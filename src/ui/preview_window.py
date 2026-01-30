#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
プレビューウィンドウ
"""

from typing import List, Optional
import tempfile
import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QSpinBox, QFileDialog, QMessageBox,
    QProgressDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

import fitz  # PyMuPDF
import pikepdf

from core.pdf_info import PDFInfo


class PreviewWindow(QDialog):
    """結合後プレビューウィンドウ"""

    def __init__(self, pdf_list: List[PDFInfo], parent=None):
        super().__init__(parent)
        self.pdf_list = pdf_list
        self.temp_pdf_path: Optional[str] = None
        self.current_page = 0
        self.total_pages = 0
        self.doc: Optional[fitz.Document] = None

        self.setWindowTitle("結合プレビュー")
        self.setMinimumSize(700, 800)
        self.resize(800, 900)

        self._setup_ui()
        self._create_preview_pdf()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ナビゲーション
        nav_layout = QHBoxLayout()

        self.prev_btn = QPushButton("◀ 前へ")
        self.prev_btn.clicked.connect(self._prev_page)
        nav_layout.addWidget(self.prev_btn)

        nav_layout.addStretch()

        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.valueChanged.connect(self._on_page_changed)
        nav_layout.addWidget(QLabel("ページ:"))
        nav_layout.addWidget(self.page_spin)

        self.page_label = QLabel("/ 0")
        nav_layout.addWidget(self.page_label)

        nav_layout.addStretch()

        self.next_btn = QPushButton("次へ ▶")
        self.next_btn.clicked.connect(self._next_page)
        nav_layout.addWidget(self.next_btn)

        layout.addLayout(nav_layout)

        # プレビューエリア
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.preview_label)

        layout.addWidget(self.scroll_area)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("閉じる")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _create_preview_pdf(self):
        """プレビュー用PDFを生成"""
        try:
            # 一時ファイル作成
            fd, self.temp_pdf_path = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)

            # PDF結合
            output_pdf = pikepdf.Pdf.new()

            for pdf_info in self.pdf_list:
                with pikepdf.open(pdf_info.filepath, password=pdf_info.password or "") as pdf:
                    # 使用するページのインデックスリストを決定
                    if pdf_info.selected_pages is not None and pdf_info.page_order is not None:
                        # 抽出対象のページを、指定された順序で並べ替え
                        page_indices = [p for p in pdf_info.page_order if p in pdf_info.selected_pages]
                    elif pdf_info.selected_pages is not None:
                        page_indices = pdf_info.selected_pages
                    elif pdf_info.page_order is not None:
                        page_indices = pdf_info.page_order
                    else:
                        page_indices = list(range(len(pdf.pages)))

                    for page_idx in page_indices:
                        if page_idx >= len(pdf.pages):
                            continue

                        page = pdf.pages[page_idx]

                        # 回転を適用
                        rotation = pdf_info.page_rotations.get(page_idx, 0)
                        if rotation:
                            current_rotation = page.get("/Rotate", 0)
                            if isinstance(current_rotation, pikepdf.Object):
                                current_rotation = int(current_rotation)
                            page["/Rotate"] = (current_rotation + rotation) % 360

                        output_pdf.pages.append(page)

            output_pdf.save(self.temp_pdf_path)

            # PyMuPDFで開く
            self.doc = fitz.open(self.temp_pdf_path)
            self.total_pages = len(self.doc)

            self.page_spin.setMaximum(self.total_pages)
            self.page_label.setText(f"/ {self.total_pages}")

            self._show_page(0)

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"プレビュー生成エラー: {str(e)}")

    def _show_page(self, page_num: int):
        """指定ページを表示"""
        if not self.doc or page_num < 0 or page_num >= self.total_pages:
            return

        self.current_page = page_num
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(page_num + 1)
        self.page_spin.blockSignals(False)

        page = self.doc[page_num]

        # 表示サイズ計算
        available_width = self.scroll_area.width() - 40
        zoom = available_width / page.rect.width
        zoom = min(zoom, 2.0)  # 最大2倍

        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)

        from PySide6.QtGui import QImage
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(img)

        self.preview_label.setPixmap(pixmap)

        # ボタン状態更新
        self.prev_btn.setEnabled(page_num > 0)
        self.next_btn.setEnabled(page_num < self.total_pages - 1)

    def _prev_page(self):
        if self.current_page > 0:
            self._show_page(self.current_page - 1)

    def _next_page(self):
        if self.current_page < self.total_pages - 1:
            self._show_page(self.current_page + 1)

    def _on_page_changed(self, value: int):
        self._show_page(value - 1)

    def _on_save(self):
        """保存"""
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存先を選択",
            "merged.pdf",
            "PDFファイル (*.pdf)"
        )

        if not output_path:
            return

        try:
            # 一時ファイルをコピー
            import shutil
            shutil.copy(self.temp_pdf_path, output_path)

            QMessageBox.information(
                self,
                "完了",
                f"PDFを保存しました。\n\n保存先: {output_path}"
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"保存エラー: {str(e)}")

    def closeEvent(self, event):
        """ウィンドウを閉じる際の処理"""
        if self.doc:
            self.doc.close()

        if self.temp_pdf_path and os.path.exists(self.temp_pdf_path):
            try:
                os.remove(self.temp_pdf_path)
            except:
                pass

        super().closeEvent(event)

    def resizeEvent(self, event):
        """リサイズ時に再描画"""
        super().resizeEvent(event)
        if self.doc:
            self._show_page(self.current_page)
