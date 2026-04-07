#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
メインウィンドウ
"""

from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QProgressDialog,
    QAbstractItemView, QStatusBar, QFrame, QSplitter,
    QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap

from core.pdf_info import PDFInfo
from core.pdf_merger import PDFMergerWorker
from core.image_converter import ImageConverter, is_supported_image, get_image_filter_string
from version import VERSION, APP_NAME, COPYRIGHT, DESCRIPTION


class DropArea(QFrame):
    """ドラッグ&ドロップエリア"""

    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(100)
        self.setStyleSheet("""
            DropArea {
                border: 2px dashed #0078d4;
                border-radius: 8px;
                background-color: #f8fbff;
            }
            DropArea:hover {
                background-color: #e8f4ff;
                border-color: #005a9e;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel("📄")
        icon_label.setStyleSheet("font-size: 32px; border: none;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        text_label = QLabel("ここにPDF・画像ファイルをドラッグ&ドロップ または")
        text_label.setStyleSheet("color: #666666; font-size: 12px; border: none;")
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)

        self.select_button = QPushButton("ファイルを選択")
        self.select_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        self.select_button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.select_button, alignment=Qt.AlignCenter)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                DropArea {
                    border: 2px dashed #005a9e;
                    border-radius: 8px;
                    background-color: #d0e8ff;
                }
            """)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            DropArea {
                border: 2px dashed #0078d4;
                border-radius: 8px;
                background-color: #f8fbff;
            }
            DropArea:hover {
                background-color: #e8f4ff;
                border-color: #005a9e;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("""
            DropArea {
                border: 2px dashed #0078d4;
                border-radius: 8px;
                background-color: #f8fbff;
            }
            DropArea:hover {
                background-color: #e8f4ff;
                border-color: #005a9e;
            }
        """)

        files = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                files.append(url.toLocalFile())

        if files:
            self.files_dropped.emit(files)


class ThumbnailPanel(QGroupBox):
    """サムネイルパネル（全ページスクロール表示）"""

    def __init__(self, parent=None):
        super().__init__("プレビュー", parent)
        self.setMinimumWidth(180)
        self.setMaximumWidth(220)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        self.info_label = QLabel("ファイルを選択してください")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("font-size: 11px; color: #666666;")
        layout.addWidget(self.info_label)

        # スクロールエリア
        from PySide6.QtWidgets import QScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
        """)

        # サムネイルコンテナ
        self.thumbnail_container = QWidget()
        self.thumbnail_layout = QVBoxLayout(self.thumbnail_container)
        self.thumbnail_layout.setSpacing(8)
        self.thumbnail_layout.setContentsMargins(8, 8, 8, 8)
        self.thumbnail_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.thumbnail_container)
        layout.addWidget(self.scroll_area)

        self.current_pdf = None

    def set_pdf(self, pdf_info):
        """PDFの全ページサムネイルを表示"""
        self._clear_thumbnails()
        self.current_pdf = pdf_info

        if not pdf_info:
            self.info_label.setText("ファイルを選択してください")
            return

        # 情報ラベルを更新
        info_parts = [pdf_info.filename, f"{pdf_info.page_count}ページ"]
        if pdf_info.page_rotations:
            info_parts.append(f"🔄{len(pdf_info.page_rotations)}ページ回転済")
        if pdf_info.page_order is not None:
            info_parts.append("📄順序変更あり")
        if pdf_info.selected_pages is not None:
            info_parts.append(f"✂{len(pdf_info.selected_pages)}ページ抽出")
        self.info_label.setText("\n".join(info_parts))

        # 表示するページのリストを決定
        if pdf_info.selected_pages is not None and pdf_info.page_order is not None:
            # 抽出ページを順序に従って並べ替え
            selected_set = set(pdf_info.selected_pages)
            page_indices = [p for p in pdf_info.page_order if p in selected_set]
        elif pdf_info.selected_pages is not None:
            page_indices = pdf_info.selected_pages
        elif pdf_info.page_order is not None:
            page_indices = pdf_info.page_order
        else:
            page_indices = list(range(pdf_info.page_count))

        # サムネイルを生成
        for display_idx, page_num in enumerate(page_indices):
            pixmap = pdf_info.get_thumbnail(page_num, 140)
            if pixmap:
                # ページラベル
                page_widget = QWidget()
                page_layout = QVBoxLayout(page_widget)
                page_layout.setContentsMargins(0, 0, 0, 0)
                page_layout.setSpacing(2)

                thumb_label = QLabel()
                scaled = pixmap.scaled(140, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                thumb_label.setPixmap(scaled)
                thumb_label.setAlignment(Qt.AlignCenter)
                thumb_label.setStyleSheet("""
                    QLabel {
                        background-color: white;
                        border: 1px solid #ddd;
                        padding: 2px;
                    }
                """)
                page_layout.addWidget(thumb_label)

                # ページ番号（元のページ番号と現在の位置を表示）
                rotation = pdf_info.page_rotations.get(page_num, 0)
                if pdf_info.page_order is not None or pdf_info.selected_pages is not None:
                    page_text = f"{display_idx + 1}. (元P.{page_num + 1})"
                else:
                    page_text = f"P.{page_num + 1}"
                if rotation:
                    page_text += f" 🔄{rotation}°"

                num_label = QLabel(page_text)
                num_label.setAlignment(Qt.AlignCenter)
                num_label.setStyleSheet("font-size: 10px; color: #666;")
                page_layout.addWidget(num_label)

                self.thumbnail_layout.addWidget(page_widget)

    def _clear_thumbnails(self):
        """サムネイルをクリア"""
        while self.thumbnail_layout.count():
            item = self.thumbnail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def clear(self):
        """クリア"""
        self._clear_thumbnails()
        self.current_pdf = None
        self.info_label.setText("ファイルを選択してください")


class MainWindow(QMainWindow):
    """メインウィンドウ"""

    def __init__(self):
        super().__init__()
        self.pdf_list: List[PDFInfo] = []
        self.worker: Optional[PDFMergerWorker] = None
        self.progress_dialog: Optional[QProgressDialog] = None
        self.image_converter = ImageConverter()

        self._setup_ui()
        self._connect_signals()
        self._update_button_states()

    def closeEvent(self, event):
        """ウィンドウ閉じる時に一時ファイルをクリーンアップ"""
        self.image_converter.cleanup()
        super().closeEvent(event)

    def _setup_ui(self):
        """UIを構築"""
        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)

        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # 左側：メインコンテンツ
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # ドロップエリア
        self.drop_area = DropArea()
        left_layout.addWidget(self.drop_area)

        # ファイルリストヘッダー
        list_header = QLabel("ファイルリスト:")
        list_header.setStyleSheet("font-weight: bold; font-size: 13px;")
        left_layout.addWidget(list_header)

        # ファイルリストテーブル
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(5)
        self.file_table.setHorizontalHeaderLabels(["#", "ファイル名", "サイズ", "ページ", "操作"])
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.file_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.file_table.setColumnWidth(0, 40)
        self.file_table.setColumnWidth(2, 80)
        self.file_table.setColumnWidth(3, 60)
        self.file_table.setColumnWidth(4, 50)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.file_table.setDragDropMode(QAbstractItemView.InternalMove)
        self.file_table.setDragEnabled(True)
        self.file_table.setAcceptDrops(True)
        self.file_table.verticalHeader().setVisible(False)
        self.file_table.setAlternatingRowColors(True)
        left_layout.addWidget(self.file_table)

        # 操作ボタン（1行目）
        controls_layout1 = QHBoxLayout()
        controls_layout1.setSpacing(8)

        self.btn_up = QPushButton("▲ 上へ")
        self.btn_down = QPushButton("▼ 下へ")
        self.btn_rotate = QPushButton("🔄 回転")
        self.btn_page_order = QPushButton("📄 ページ順序")
        self.btn_page_extract = QPushButton("✂ ページ抽出")
        self.btn_clear = QPushButton("クリア")

        btn_style = """
            QPushButton {
                background-color: #f5f5f5;
                border: 1px solid #cccccc;
                padding: 8px 14px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
                border-color: #999999;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                border-color: #e0e0e0;
                color: #aaaaaa;
            }
        """

        for btn in [self.btn_up, self.btn_down, self.btn_rotate, self.btn_page_order, self.btn_page_extract, self.btn_clear]:
            btn.setStyleSheet(btn_style)
            controls_layout1.addWidget(btn)

        controls_layout1.addStretch()
        left_layout.addLayout(controls_layout1)

        # 区切り線
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #e0e0e0;")
        left_layout.addWidget(separator)

        # アクションボタン
        action_layout = QHBoxLayout()

        self.btn_about = QPushButton("About")
        self.btn_about.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                border: 1px solid #cccccc;
                padding: 8px 14px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
        """)
        action_layout.addWidget(self.btn_about)

        action_layout.addStretch()

        self.btn_preview = QPushButton("プレビュー")
        self.btn_preview.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.btn_preview.setCursor(Qt.PointingHandCursor)
        action_layout.addWidget(self.btn_preview)

        self.btn_merge = QPushButton("結合して保存")
        self.btn_merge.setStyleSheet("""
            QPushButton {
                background-color: #107c10;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b5c0b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.btn_merge.setCursor(Qt.PointingHandCursor)
        action_layout.addWidget(self.btn_merge)

        left_layout.addLayout(action_layout)

        main_layout.addWidget(left_widget, stretch=1)

        # 右側：サムネイルパネル
        self.thumbnail_panel = ThumbnailPanel()
        main_layout.addWidget(self.thumbnail_panel)

        # ステータスバー
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status_bar()

    def _connect_signals(self):
        """シグナルを接続"""
        self.drop_area.select_button.clicked.connect(self._on_select_files)
        self.drop_area.files_dropped.connect(self._on_files_dropped)
        self.btn_up.clicked.connect(self._on_move_up)
        self.btn_down.clicked.connect(self._on_move_down)
        self.btn_rotate.clicked.connect(self._on_rotate)
        self.btn_page_order.clicked.connect(self._on_page_order)
        self.btn_page_extract.clicked.connect(self._on_page_extract)
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_about.clicked.connect(self._on_about)
        self.btn_preview.clicked.connect(self._on_preview)
        self.btn_merge.clicked.connect(self._on_merge)
        self.file_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.file_table.model().rowsMoved.connect(self._on_rows_moved)

    def _on_selection_changed(self):
        """選択変更時"""
        self._update_button_states()
        self._update_thumbnail()

    def _update_thumbnail(self):
        """サムネイル更新"""
        row = self.file_table.currentRow()
        if row >= 0 and row < len(self.pdf_list):
            pdf_info = self.pdf_list[row]
            self.thumbnail_panel.set_pdf(pdf_info)
        else:
            self.thumbnail_panel.clear()

    def _on_select_files(self):
        """ファイル選択ダイアログを開く"""
        image_filter = get_image_filter_string()
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "ファイルを選択",
            "",
            f"対応ファイル (*.pdf *.jpg *.jpeg *.png *.bmp *.tiff *.tif *.gif *.webp);;"
            f"PDFファイル (*.pdf);;"
            f"{image_filter};;"
            f"すべてのファイル (*.*)"
        )
        if files:
            self._add_files(files)

    def _on_files_dropped(self, files: List[str]):
        """ファイルがドロップされた"""
        self._add_files(files)

    def _add_files(self, file_paths: List[str]):
        """ファイルを追加（PDF・画像対応）"""
        added = 0
        errors = []

        for path in file_paths:
            is_pdf = path.lower().endswith('.pdf')
            is_image = is_supported_image(path)

            if not is_pdf and not is_image:
                errors.append(f"{Path(path).name}: 対応していないファイル形式です")
                continue

            if self._is_duplicate(path):
                QMessageBox.warning(
                    self,
                    "警告",
                    f"'{Path(path).name}' は既に追加されています。"
                )
                continue

            try:
                if is_image:
                    # 画像→PDF変換
                    temp_pdf_path = self.image_converter.convert_to_pdf(path)
                    pdf_info = PDFInfo(temp_pdf_path, original_image_path=path)
                else:
                    pdf_info = PDFInfo(path)

                # パスワード保護されている場合はパスワード入力を求める
                if pdf_info.needs_password:
                    pdf_info = self._handle_password_protected_pdf(path)
                    if pdf_info is None:
                        # キャンセルされた
                        continue

                if pdf_info.is_valid:
                    self.pdf_list.append(pdf_info)
                    added += 1
                else:
                    errors.append(f"{pdf_info.filename}: {pdf_info.error_message}")
            except Exception as e:
                errors.append(f"{Path(path).name}: {str(e)}")

        if errors:
            error_msg = "以下のファイルを追加できませんでした:\n\n" + "\n".join(errors)
            QMessageBox.warning(self, "エラー", error_msg)

        if added > 0:
            self._refresh_table()
            self._update_status_bar()
            self._update_button_states()

    def _is_duplicate(self, path: str) -> bool:
        """重複チェック（元画像パスも考慮）"""
        for pdf_info in self.pdf_list:
            if pdf_info.filepath == path:
                return True
            if pdf_info.original_image_path and pdf_info.original_image_path == path:
                return True
        return False

    def _handle_password_protected_pdf(self, path: str) -> Optional[PDFInfo]:
        """パスワード保護されたPDFの処理"""
        filename = Path(path).name

        while True:
            # パスワード入力ダイアログを表示
            from ui.password_dialog import PasswordDialog
            dialog = PasswordDialog(filename, self)
            if dialog.exec() != PasswordDialog.Accepted:
                # キャンセルされた
                return None

            password = dialog.get_password()
            if not password:
                continue

            # パスワードを使ってPDFを開いてみる
            pdf_info = PDFInfo(path, password=password)

            if pdf_info.is_valid:
                return pdf_info

            # パスワードが間違っている場合
            if pdf_info.needs_password:
                QMessageBox.warning(
                    self,
                    "パスワードエラー",
                    "パスワードが正しくありません。\nもう一度入力してください。"
                )
                continue
            else:
                # 他のエラー
                QMessageBox.warning(
                    self,
                    "エラー",
                    f"PDFを開けませんでした:\n{pdf_info.error_message}"
                )
                return None

    def _refresh_table(self):
        """テーブルを更新"""
        self.file_table.setRowCount(len(self.pdf_list))

        for i, pdf_info in enumerate(self.pdf_list):
            # 番号
            num_item = QTableWidgetItem(str(i + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            num_item.setFlags(num_item.flags() & ~Qt.ItemIsEditable)
            self.file_table.setItem(i, 0, num_item)

            # ファイル名（画像変換・パスワード保護・回転・順序・抽出情報付き）
            name_text = ""
            if pdf_info.original_image_path:
                name_text = "🖼 "
            elif pdf_info.is_encrypted:
                name_text = "🔒 "
            name_text += pdf_info.filename
            indicators = []
            if pdf_info.page_rotations:
                indicators.append("🔄")
            if pdf_info.page_order is not None:
                indicators.append("📄")
            if pdf_info.selected_pages is not None:
                indicators.append("✂")
            if indicators:
                name_text += " " + "".join(indicators)
            name_item = QTableWidgetItem(name_text)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            name_item.setData(Qt.UserRole, i)
            # ツールチップに詳細を表示
            if pdf_info.original_image_path:
                tooltip = f"元画像: {pdf_info.original_image_path}"
            else:
                tooltip = pdf_info.filepath
            if pdf_info.page_order is not None:
                tooltip += f"\n順序変更: {len(pdf_info.page_order)}ページ"
            if pdf_info.selected_pages is not None:
                tooltip += f"\n抽出: {len(pdf_info.selected_pages)}/{pdf_info.page_count}ページ"
            name_item.setToolTip(tooltip)
            self.file_table.setItem(i, 1, name_item)

            # サイズ
            size_item = QTableWidgetItem(pdf_info.size_str)
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)
            self.file_table.setItem(i, 2, size_item)

            # ページ数
            page_item = QTableWidgetItem(str(pdf_info.page_count))
            page_item.setTextAlignment(Qt.AlignCenter)
            page_item.setFlags(page_item.flags() & ~Qt.ItemIsEditable)
            self.file_table.setItem(i, 3, page_item)

            # 削除ボタン
            delete_btn = QPushButton("×")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background: none;
                    border: none;
                    color: #cc0000;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #ffeeee;
                }
            """)
            delete_btn.setCursor(Qt.PointingHandCursor)
            delete_btn.clicked.connect(lambda checked, idx=i: self._on_delete_row(idx))
            self.file_table.setCellWidget(i, 4, delete_btn)

    def _on_delete_row(self, index: int):
        """行を削除"""
        if 0 <= index < len(self.pdf_list):
            del self.pdf_list[index]
            self._refresh_table()
            self._update_status_bar()
            self._update_button_states()
            self.thumbnail_panel.clear()

    def _on_move_up(self):
        """選択行を上に移動"""
        row = self.file_table.currentRow()
        if row > 0:
            self.pdf_list[row], self.pdf_list[row - 1] = \
                self.pdf_list[row - 1], self.pdf_list[row]
            self._refresh_table()
            self.file_table.selectRow(row - 1)

    def _on_move_down(self):
        """選択行を下に移動"""
        row = self.file_table.currentRow()
        if row >= 0 and row < len(self.pdf_list) - 1:
            self.pdf_list[row], self.pdf_list[row + 1] = \
                self.pdf_list[row + 1], self.pdf_list[row]
            self._refresh_table()
            self.file_table.selectRow(row + 1)

    def _on_rotate(self):
        """回転ダイアログを表示"""
        row = self.file_table.currentRow()
        if row < 0 or row >= len(self.pdf_list):
            QMessageBox.information(self, "情報", "回転するファイルを選択してください。")
            return

        pdf_info = self.pdf_list[row]
        from ui.rotation_dialog import RotationDialog
        dialog = RotationDialog(pdf_info.page_count, pdf_info.page_rotations, self)

        if dialog.exec():
            pages, degrees, is_reset = dialog.get_result()
            if is_reset:
                # 回転をリセット
                for page_idx in pages:
                    if page_idx in pdf_info.page_rotations:
                        del pdf_info.page_rotations[page_idx]
                self.status_bar.showMessage(f"{len(pages)}ページの回転をリセットしました", 3000)
            else:
                pdf_info.set_rotation(pages, degrees)
                self.status_bar.showMessage(f"{len(pages)}ページを{degrees}°回転しました", 3000)
            self._refresh_table()
            self._update_thumbnail()

    def _on_page_order(self):
        """ページ順序ダイアログを表示"""
        row = self.file_table.currentRow()
        if row < 0 or row >= len(self.pdf_list):
            QMessageBox.information(self, "情報", "ページ順序を変更するファイルを選択してください。")
            return

        pdf_info = self.pdf_list[row]
        if pdf_info.page_count < 2:
            QMessageBox.information(self, "情報", "このファイルは1ページのみです。")
            return

        from ui.page_order_dialog import PageOrderDialog
        dialog = PageOrderDialog(pdf_info, self)

        if dialog.exec():
            new_order = dialog.get_page_order()
            # 元の順序と異なる場合のみ保存
            if new_order != list(range(pdf_info.page_count)):
                pdf_info.page_order = new_order
                self.status_bar.showMessage("ページ順序を変更しました", 3000)
            else:
                pdf_info.page_order = None
                self.status_bar.showMessage("ページ順序をリセットしました", 3000)
            self._refresh_table()
            self._update_thumbnail()

    def _on_page_extract(self):
        """ページ抽出ダイアログを表示"""
        row = self.file_table.currentRow()
        if row < 0 or row >= len(self.pdf_list):
            QMessageBox.information(self, "情報", "ページを抽出するファイルを選択してください。")
            return

        pdf_info = self.pdf_list[row]
        from ui.page_extract_dialog import PageExtractDialog
        dialog = PageExtractDialog(pdf_info, self)

        if dialog.exec():
            selected = dialog.get_selected_pages()
            if len(selected) == pdf_info.page_count:
                # 全ページ選択の場合はNone
                pdf_info.selected_pages = None
                self.status_bar.showMessage("全ページを使用します", 3000)
            else:
                pdf_info.selected_pages = selected
                self.status_bar.showMessage(f"{len(selected)}ページを抽出対象に設定しました", 3000)
            self._refresh_table()
            self._update_thumbnail()

    def _on_rows_moved(self):
        """ドラッグ&ドロップで行が移動された"""
        new_list = []
        for row in range(self.file_table.rowCount()):
            name_item = self.file_table.item(row, 1)
            if name_item:
                original_index = name_item.data(Qt.UserRole)
                if original_index is not None and 0 <= original_index < len(self.pdf_list):
                    new_list.append(self.pdf_list[original_index])
        self.pdf_list = new_list
        self._refresh_table()

    def _on_clear(self):
        """全ファイルをクリア"""
        if not self.pdf_list:
            return

        reply = QMessageBox.question(
            self,
            "確認",
            "すべてのファイルを削除しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.pdf_list.clear()
            self._refresh_table()
            self._update_status_bar()
            self._update_button_states()
            self.thumbnail_panel.clear()

    def _on_about(self):
        """Aboutダイアログを表示"""
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<h2>{APP_NAME}</h2>"
            f"<p>Version {VERSION}</p>"
            f"<p>{DESCRIPTION}</p>"
            f"<p>{COPYRIGHT}</p>"
            f"<hr>"
            f"<p>ローカルで動作するPDF結合ツール</p>"
            f"<p>機能: 結合・回転・ページ順序変更・ページ抽出・画像変換</p>"
        )

    def _on_preview(self):
        """プレビューウィンドウを表示"""
        if len(self.pdf_list) < 2:
            QMessageBox.information(
                self,
                "情報",
                "2つ以上のPDFファイルを追加してください。"
            )
            return

        from ui.preview_window import PreviewWindow
        preview = PreviewWindow(self.pdf_list, self)
        preview.exec()

    def _on_merge(self):
        """PDF結合を実行"""
        if len(self.pdf_list) < 2:
            QMessageBox.information(
                self,
                "情報",
                "2つ以上のPDFファイルを追加してください。"
            )
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存先を選択",
            "merged.pdf",
            "PDFファイル (*.pdf)"
        )

        if not output_path:
            return

        self.progress_dialog = QProgressDialog(
            "PDFを結合しています...",
            "キャンセル",
            0,
            100,
            self
        )
        self.progress_dialog.setWindowTitle("結合中")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)
        self.progress_dialog.canceled.connect(self._on_cancel_merge)

        # 回転情報を含めてワーカーに渡す
        self.worker = PDFMergerWorker(self.pdf_list, output_path)
        self.worker.progress.connect(self._on_merge_progress)
        self.worker.finished.connect(self._on_merge_finished)
        self.worker.error.connect(self._on_merge_error)
        self.worker.start()

    def _on_cancel_merge(self):
        """結合処理をキャンセル"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
            self.status_bar.showMessage("結合をキャンセルしました", 3000)

    def _on_merge_progress(self, value: int):
        """結合進捗を更新"""
        if self.progress_dialog:
            self.progress_dialog.setValue(value)

    def _on_merge_finished(self, output_path: str, total_pages: int):
        """結合完了"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        QMessageBox.information(
            self,
            "完了",
            f"PDFの結合が完了しました。\n\n"
            f"ファイル数: {len(self.pdf_list)}\n"
            f"総ページ数: {total_pages}\n"
            f"保存先: {output_path}"
        )
        self.status_bar.showMessage(f"結合完了: {total_pages}ページ", 5000)

    def _on_merge_error(self, error_message: str):
        """結合エラー"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        QMessageBox.critical(
            self,
            "エラー",
            f"PDF結合中にエラーが発生しました:\n\n{error_message}"
        )
        self.status_bar.showMessage("エラーが発生しました", 5000)

    def _update_button_states(self):
        """ボタンの有効/無効を更新"""
        has_files = len(self.pdf_list) > 0
        has_selection = self.file_table.currentRow() >= 0
        can_merge = len(self.pdf_list) >= 2

        self.btn_up.setEnabled(has_selection and self.file_table.currentRow() > 0)
        self.btn_down.setEnabled(
            has_selection and self.file_table.currentRow() < len(self.pdf_list) - 1
        )
        self.btn_rotate.setEnabled(has_selection)
        self.btn_page_order.setEnabled(has_selection)
        self.btn_page_extract.setEnabled(has_selection)
        self.btn_clear.setEnabled(has_files)
        self.btn_preview.setEnabled(can_merge)
        self.btn_merge.setEnabled(can_merge)

    def _update_status_bar(self):
        """ステータスバーを更新"""
        if not self.pdf_list:
            self.status_bar.showMessage("ファイルを追加してください")
        else:
            total_pages = sum(pdf.page_count for pdf in self.pdf_list)
            self.status_bar.showMessage(
                f"{len(self.pdf_list)} ファイル / 合計 {total_pages} ページ"
            )
