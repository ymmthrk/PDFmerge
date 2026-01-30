#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF結合処理
"""

from typing import List, TYPE_CHECKING

from PySide6.QtCore import QThread, Signal

import pikepdf

if TYPE_CHECKING:
    from core.pdf_info import PDFInfo


class PDFMergerWorker(QThread):
    """PDF結合を行うワーカースレッド"""

    progress = Signal(int)  # 進捗率 (0-100)
    finished = Signal(str, int)  # 出力パス, 総ページ数
    error = Signal(str)  # エラーメッセージ

    def __init__(self, pdf_list: List['PDFInfo'], output_path: str, parent=None):
        super().__init__(parent)
        self.pdf_list = pdf_list
        self.output_path = output_path
        self._cancelled = False

    def cancel(self):
        """処理をキャンセル"""
        self._cancelled = True

    def run(self):
        """結合処理を実行"""
        try:
            output_pdf = pikepdf.Pdf.new()
            total_files = len(self.pdf_list)
            total_pages = 0

            for i, pdf_info in enumerate(self.pdf_list):
                if self._cancelled:
                    return

                # 進捗を更新
                progress_value = int((i / total_files) * 100)
                self.progress.emit(progress_value)

                # PDFを開いてページを追加（パスワード保護の場合はパスワードを指定）
                with pikepdf.open(pdf_info.filepath, password=pdf_info.password or "") as pdf:
                    # 使用するページのインデックスリストを決定
                    if pdf_info.selected_pages is not None:
                        # 抽出ページが指定されている場合
                        page_indices = pdf_info.selected_pages
                    elif pdf_info.page_order is not None:
                        # ページ順序が指定されている場合
                        page_indices = pdf_info.page_order
                    else:
                        # デフォルト: 全ページを順番に
                        page_indices = list(range(len(pdf.pages)))

                    # ページ順序が指定されている場合は抽出ページにも適用
                    if pdf_info.selected_pages is not None and pdf_info.page_order is not None:
                        # 抽出対象のページを、指定された順序で並べ替え
                        # page_order内で、selected_pagesに含まれるもののみを抽出
                        page_indices = [p for p in pdf_info.page_order if p in pdf_info.selected_pages]

                    for page_idx in page_indices:
                        if self._cancelled:
                            return

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
                        total_pages += 1

            if self._cancelled:
                return

            # 保存
            self.progress.emit(95)
            output_pdf.save(self.output_path)
            self.progress.emit(100)

            self.finished.emit(self.output_path, total_pages)

        except pikepdf.PasswordError:
            self.error.emit("パスワードで保護されたPDFが含まれています")
        except pikepdf.PdfError as e:
            self.error.emit(f"PDF処理エラー: {str(e)}")
        except PermissionError:
            self.error.emit("保存先に書き込み権限がありません")
        except Exception as e:
            self.error.emit(f"予期しないエラー: {str(e)}")
