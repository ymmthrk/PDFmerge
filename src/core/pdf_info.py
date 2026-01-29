#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF情報クラス
"""

from pathlib import Path
from typing import Optional, List, Dict

import pikepdf
import fitz  # PyMuPDF
from PySide6.QtGui import QPixmap, QImage


class PDFInfo:
    """PDFファイルの情報を保持するクラス"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = Path(filepath).name
        self.file_size = 0
        self.page_count = 0
        self.is_valid = False
        self.error_message: Optional[str] = None
        self.page_rotations: Dict[int, int] = {}  # {page_index: rotation_degrees}
        self.page_order: Optional[List[int]] = None  # カスタムページ順序（Noneは元の順序）
        self.selected_pages: Optional[List[int]] = None  # 抽出するページ（Noneは全ページ）

        self._load_info()

    def _load_info(self):
        """PDFの情報を読み込む"""
        try:
            path = Path(self.filepath)
            if not path.exists():
                self.error_message = "ファイルが見つかりません"
                return

            self.file_size = path.stat().st_size

            # pikepdfでPDFを開いて情報を取得
            with pikepdf.open(self.filepath) as pdf:
                self.page_count = len(pdf.pages)
                self.is_valid = True

        except pikepdf.PasswordError:
            self.error_message = "パスワードで保護されています"
        except pikepdf.PdfError as e:
            self.error_message = f"PDFを読み込めません: {str(e)}"
        except Exception as e:
            self.error_message = f"エラー: {str(e)}"

    @property
    def size_str(self) -> str:
        """ファイルサイズを人間が読みやすい形式で返す"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"

    def __repr__(self) -> str:
        return f"PDFInfo(filename={self.filename}, pages={self.page_count})"

    def get_thumbnail(self, page_num: int = 0, width: int = 150) -> Optional[QPixmap]:
        """指定ページのサムネイルを生成"""
        try:
            doc = fitz.open(self.filepath)
            if page_num >= len(doc):
                page_num = 0

            page = doc[page_num]

            # 回転を適用
            rotation = self.page_rotations.get(page_num, 0)

            # スケール計算
            zoom = width / page.rect.width
            matrix = fitz.Matrix(zoom, zoom)

            if rotation:
                matrix = matrix.prerotate(rotation)

            pix = page.get_pixmap(matrix=matrix)

            # QPixmapに変換
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(img)

            doc.close()
            return pixmap
        except Exception as e:
            return None

    def set_rotation(self, page_indices: List[int], degrees: int):
        """指定ページの回転を設定"""
        for idx in page_indices:
            if 0 <= idx < self.page_count:
                current = self.page_rotations.get(idx, 0)
                new_rotation = (current + degrees) % 360
                self.page_rotations[idx] = new_rotation

    def set_all_pages_rotation(self, degrees: int):
        """全ページの回転を設定"""
        self.set_rotation(list(range(self.page_count)), degrees)

    def get_page_thumbnail(self, page_num: int, width: int = 100) -> Optional[QPixmap]:
        """個別ページのサムネイルを取得（回転適用済み）"""
        return self.get_thumbnail(page_num, width)
