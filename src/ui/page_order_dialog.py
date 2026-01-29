#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ページ順序入替ダイアログ
"""

from typing import List, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from core.pdf_info import PDFInfo


class PageOrderDialog(QDialog):
    """ページ順序入替ダイアログ"""

    def __init__(self, pdf_info: PDFInfo, parent=None):
        super().__init__(parent)
        self.pdf_info = pdf_info
        # 既存のページ順序があればそれを使用
        if pdf_info.page_order is not None:
            self.page_order: List[int] = pdf_info.page_order.copy()
        else:
            self.page_order: List[int] = list(range(pdf_info.page_count))

        self.setWindowTitle(f"ページ順序 - {pdf_info.filename}")
        self.setMinimumSize(500, 600)
        self.resize(550, 700)
        self._setup_ui()
        self._load_pages()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 説明
        info_label = QLabel("ドラッグ&ドロップまたはボタンでページ順序を変更できます")
        info_label.setStyleSheet("color: #666666;")
        layout.addWidget(info_label)

        # メインエリア
        main_layout = QHBoxLayout()

        # ページリスト
        self.page_list = QListWidget()
        self.page_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.page_list.setDefaultDropAction(Qt.MoveAction)
        self.page_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.page_list.setIconSize(Qt.QSize(80, 100))
        self.page_list.setSpacing(4)
        self.page_list.model().rowsMoved.connect(self._on_rows_moved)
        main_layout.addWidget(self.page_list)

        # 操作ボタン
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_up = QPushButton("▲ 上へ")
        self.btn_up.clicked.connect(self._move_up)
        btn_layout.addWidget(self.btn_up)

        self.btn_down = QPushButton("▼ 下へ")
        self.btn_down.clicked.connect(self._move_down)
        btn_layout.addWidget(self.btn_down)

        btn_layout.addSpacing(20)

        self.btn_top = QPushButton("⏫ 先頭へ")
        self.btn_top.clicked.connect(self._move_to_top)
        btn_layout.addWidget(self.btn_top)

        self.btn_bottom = QPushButton("⏬ 末尾へ")
        self.btn_bottom.clicked.connect(self._move_to_bottom)
        btn_layout.addWidget(self.btn_bottom)

        btn_layout.addSpacing(20)

        self.btn_reverse = QPushButton("🔄 逆順")
        self.btn_reverse.clicked.connect(self._reverse_order)
        btn_layout.addWidget(self.btn_reverse)

        self.btn_reset = QPushButton("↩ リセット")
        self.btn_reset.clicked.connect(self._reset_order)
        btn_layout.addWidget(self.btn_reset)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        layout.addLayout(main_layout)

        # ダイアログボタン
        dialog_btn_layout = QHBoxLayout()
        dialog_btn_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        dialog_btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("適用")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        dialog_btn_layout.addWidget(ok_btn)

        layout.addLayout(dialog_btn_layout)

    def _load_pages(self):
        """ページを読み込み"""
        self.page_list.clear()

        for i, page_idx in enumerate(self.page_order):
            item = QListWidgetItem()

            # サムネイル取得
            pixmap = self.pdf_info.get_thumbnail(page_idx, 80)
            if pixmap:
                from PySide6.QtGui import QIcon
                icon = QIcon(pixmap)
                item.setIcon(icon)

            # ラベル
            rotation = self.pdf_info.page_rotations.get(page_idx, 0)
            label = f"ページ {page_idx + 1}"
            if rotation:
                label += f" (🔄{rotation}°)"
            item.setText(label)

            item.setData(Qt.UserRole, page_idx)
            self.page_list.addItem(item)

    def _on_rows_moved(self):
        """ドラッグ&ドロップで行が移動された"""
        self._update_order_from_list()

    def _update_order_from_list(self):
        """リストから順序を更新"""
        self.page_order = []
        for i in range(self.page_list.count()):
            item = self.page_list.item(i)
            self.page_order.append(item.data(Qt.UserRole))

    def _get_selected_row(self) -> int:
        """選択行を取得"""
        items = self.page_list.selectedItems()
        if items:
            return self.page_list.row(items[0])
        return -1

    def _move_up(self):
        """上へ移動"""
        row = self._get_selected_row()
        if row > 0:
            self.page_order[row], self.page_order[row - 1] = \
                self.page_order[row - 1], self.page_order[row]
            self._load_pages()
            self.page_list.setCurrentRow(row - 1)

    def _move_down(self):
        """下へ移動"""
        row = self._get_selected_row()
        if row >= 0 and row < len(self.page_order) - 1:
            self.page_order[row], self.page_order[row + 1] = \
                self.page_order[row + 1], self.page_order[row]
            self._load_pages()
            self.page_list.setCurrentRow(row + 1)

    def _move_to_top(self):
        """先頭へ移動"""
        row = self._get_selected_row()
        if row > 0:
            page = self.page_order.pop(row)
            self.page_order.insert(0, page)
            self._load_pages()
            self.page_list.setCurrentRow(0)

    def _move_to_bottom(self):
        """末尾へ移動"""
        row = self._get_selected_row()
        if row >= 0 and row < len(self.page_order) - 1:
            page = self.page_order.pop(row)
            self.page_order.append(page)
            self._load_pages()
            self.page_list.setCurrentRow(len(self.page_order) - 1)

    def _reverse_order(self):
        """逆順にする"""
        self.page_order.reverse()
        self._load_pages()

    def _reset_order(self):
        """リセット"""
        self.page_order = list(range(self.pdf_info.page_count))
        self._load_pages()

    def get_page_order(self) -> List[int]:
        """ページ順序を取得"""
        return self.page_order
