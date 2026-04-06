#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
画像→PDF変換モジュール

画像ファイルをA4サイズのPDFに変換する。
画像はアスペクト比を維持したままA4ページ中央に配置される。
"""

import tempfile
import atexit
from pathlib import Path
from typing import List, Set

import fitz  # PyMuPDF

# A4サイズ（ポイント単位: 72DPI）
A4_WIDTH = 595.276
A4_HEIGHT = 841.890

# 余白（ポイント単位）
MARGIN = 36  # 約12.7mm

# 対応する画像拡張子
SUPPORTED_IMAGE_EXTENSIONS: Set[str] = {
    ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif", ".webp",
}


def is_supported_image(filepath: str) -> bool:
    """対応する画像ファイルかどうかを判定する"""
    return Path(filepath).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS


def get_image_filter_string() -> str:
    """ファイルダイアログ用の画像フィルタ文字列を返す"""
    extensions = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_IMAGE_EXTENSIONS))
    return f"画像ファイル ({extensions})"


class ImageConverter:
    """画像→PDF変換を管理するクラス

    変換で生成された一時PDFファイルを追跡し、
    cleanup()呼び出し時またはプロセス終了時に削除する。
    """

    def __init__(self):
        self._temp_files: List[Path] = []
        atexit.register(self.cleanup)

    def convert_to_pdf(self, image_path: str) -> str:
        """画像ファイルをA4サイズのPDFに変換する

        Args:
            image_path: 変換元の画像ファイルパス

        Returns:
            生成された一時PDFファイルのパス

        Raises:
            ValueError: 画像ファイルを開けない場合
            FileNotFoundError: ファイルが存在しない場合
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {image_path}")

        # 一時ファイルを作成（拡張子.pdfで自動削除されないようにdelete=False）
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".pdf",
            prefix=f"pdfmerge_img_{path.stem}_",
            delete=False,
        )
        temp_path = Path(temp_file.name)
        temp_file.close()

        try:
            self._convert(image_path, str(temp_path))
            self._temp_files.append(temp_path)
            return str(temp_path)
        except Exception:
            # 変換失敗時は一時ファイルを削除
            temp_path.unlink(missing_ok=True)
            raise

    def _convert(self, image_path: str, output_path: str):
        """画像をA4 PDFに変換する実処理

        画像はアスペクト比を維持し、A4ページの余白内に収まるよう
        スケーリングされ、ページ中央に配置される。
        """
        doc = fitz.open()

        try:
            # A4ページを追加
            page = doc.new_page(width=A4_WIDTH, height=A4_HEIGHT)

            # 画像の元サイズを取得
            img_doc = fitz.open(image_path)
            if len(img_doc) == 0:
                raise ValueError(f"画像を読み込めません: {image_path}")

            # fitz.openで画像を開くと1ページのドキュメントになる
            img_page = img_doc[0]
            img_width = img_page.rect.width
            img_height = img_page.rect.height
            img_doc.close()

            # 配置可能な領域
            available_width = A4_WIDTH - (MARGIN * 2)
            available_height = A4_HEIGHT - (MARGIN * 2)

            # アスペクト比を維持したスケーリング
            scale_x = available_width / img_width
            scale_y = available_height / img_height
            scale = min(scale_x, scale_y)

            # 実際の描画サイズ
            draw_width = img_width * scale
            draw_height = img_height * scale

            # 中央配置のオフセット計算
            x_offset = (A4_WIDTH - draw_width) / 2
            y_offset = (A4_HEIGHT - draw_height) / 2

            # 画像をページに挿入
            rect = fitz.Rect(x_offset, y_offset,
                             x_offset + draw_width, y_offset + draw_height)
            page.insert_image(rect, filename=image_path)

            doc.save(output_path)
        finally:
            doc.close()

    def cleanup(self):
        """一時PDFファイルをすべて削除する"""
        for temp_path in self._temp_files:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
        self._temp_files.clear()
