#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDFmerge - PDF結合ツール (tkinter版)
ローカルで動作する安全なPDF結合アプリケーション
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import List, Optional
import threading

# tkinterdnd2のインポート（D&D機能用）
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

import pikepdf


class PDFInfo:
    """PDFファイル情報"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = Path(filepath).name
        self.file_size = 0
        self.page_count = 0
        self.is_valid = False
        self.error_message: Optional[str] = None
        self._load_info()

    def _load_info(self):
        try:
            path = Path(self.filepath)
            if not path.exists():
                self.error_message = "ファイルが見つかりません"
                return

            self.file_size = path.stat().st_size

            with pikepdf.open(self.filepath) as pdf:
                self.page_count = len(pdf.pages)
                self.is_valid = True

        except pikepdf.PasswordError:
            self.error_message = "パスワードで保護されています"
        except pikepdf.PdfError as e:
            self.error_message = f"PDFを読み込めません"
        except Exception as e:
            self.error_message = f"エラー: {str(e)}"

    @property
    def size_str(self) -> str:
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"


class PDFMergeApp:
    """PDF結合アプリケーション"""

    def __init__(self):
        # D&D対応のルートウィンドウ
        if DND_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()

        self.root.title("PDFmerge")
        self.root.geometry("800x700")
        self.root.minsize(600, 550)

        self.pdf_list: List[PDFInfo] = []
        self.merge_cancelled = False

        self._setup_styles()
        self._setup_ui()
        self._update_button_states()
        self._update_status_bar()

    def _setup_styles(self):
        """スタイル設定"""
        style = ttk.Style()
        style.theme_use('clam')

        # ボタンスタイル
        style.configure('TButton', padding=6)
        style.configure('Merge.TButton', padding=(20, 10), font=('', 10, 'bold'))

    def _setup_ui(self):
        """UI構築"""
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ドロップエリア
        self._create_drop_area(main_frame)

        # ファイルリストヘッダー
        header_label = ttk.Label(main_frame, text="ファイルリスト:", font=('', 10, 'bold'))
        header_label.pack(anchor=tk.W, pady=(10, 5))

        # ファイルリスト
        self._create_file_list(main_frame)

        # 操作ボタン
        self._create_control_buttons(main_frame)

        # 区切り線
        separator = ttk.Separator(main_frame, orient=tk.HORIZONTAL)
        separator.pack(fill=tk.X, pady=10)

        # 結合ボタン
        self._create_merge_button(main_frame)

        # ステータスバー
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var,
                               relief=tk.SUNKEN, anchor=tk.W, padding=(10, 5))
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _create_drop_area(self, parent):
        """ドロップエリア作成"""
        drop_frame = tk.Frame(parent, bg='#f0f8ff', relief=tk.GROOVE, bd=2)
        drop_frame.pack(fill=tk.X, pady=(0, 10))

        inner_frame = tk.Frame(drop_frame, bg='#f0f8ff', padx=20, pady=20)
        inner_frame.pack(fill=tk.X)

        icon_label = tk.Label(inner_frame, text="📄", font=('', 32), bg='#f0f8ff')
        icon_label.pack()

        if DND_AVAILABLE:
            text = "ここにファイルをドラッグ&ドロップ\nまたは"
        else:
            text = "tkinterdnd2未インストール\nボタンからファイルを選択してください"

        text_label = tk.Label(inner_frame, text=text, bg='#f0f8ff', fg='#666666')
        text_label.pack(pady=(5, 10))

        select_btn = ttk.Button(inner_frame, text="ファイルを選択", command=self._on_select_files)
        select_btn.pack()

        # D&D設定
        if DND_AVAILABLE:
            drop_frame.drop_target_register(DND_FILES)
            drop_frame.dnd_bind('<<Drop>>', self._on_drop)

            for widget in [drop_frame, inner_frame, icon_label, text_label]:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind('<<Drop>>', self._on_drop)

    def _create_file_list(self, parent):
        """ファイルリスト作成"""
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview
        columns = ('#', 'filename', 'size', 'pages')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)

        self.tree.heading('#', text='#')
        self.tree.heading('filename', text='ファイル名')
        self.tree.heading('size', text='サイズ')
        self.tree.heading('pages', text='ページ')

        self.tree.column('#', width=40, anchor=tk.CENTER)
        self.tree.column('filename', width=400)
        self.tree.column('size', width=80, anchor=tk.E)
        self.tree.column('pages', width=60, anchor=tk.CENTER)

        # スクロールバー
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 選択変更時のイベント
        self.tree.bind('<<TreeviewSelect>>', lambda e: self._update_button_states())

    def _create_control_buttons(self, parent):
        """操作ボタン作成"""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self.btn_up = ttk.Button(btn_frame, text="▲ 上へ", command=self._on_move_up, width=10)
        self.btn_up.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_down = ttk.Button(btn_frame, text="▼ 下へ", command=self._on_move_down, width=10)
        self.btn_down.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_delete = ttk.Button(btn_frame, text="削除", command=self._on_delete, width=10)
        self.btn_delete.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_clear = ttk.Button(btn_frame, text="クリア", command=self._on_clear, width=10)
        self.btn_clear.pack(side=tk.LEFT)

    def _create_merge_button(self, parent):
        """結合ボタン作成"""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(5, 10))

        self.btn_merge = ttk.Button(
            btn_frame,
            text="    結合して保存    ",
            command=self._on_merge
        )
        self.btn_merge.pack(side=tk.RIGHT, ipady=10)

    def _on_drop(self, event):
        """ファイルドロップ時"""
        files = self.root.tk.splitlist(event.data)
        self._add_files(list(files))

    def _on_select_files(self):
        """ファイル選択ダイアログ"""
        files = filedialog.askopenfilenames(
            title="PDFファイルを選択",
            filetypes=[("PDFファイル", "*.pdf"), ("すべてのファイル", "*.*")]
        )
        if files:
            self._add_files(list(files))

    def _add_files(self, file_paths: List[str]):
        """ファイル追加"""
        added = 0
        errors = []

        for path in file_paths:
            # PDF以外をスキップ
            if not path.lower().endswith('.pdf'):
                errors.append(f"{Path(path).name}: PDFファイルではありません")
                continue

            # 重複チェック
            if any(pdf.filepath == path for pdf in self.pdf_list):
                messagebox.showwarning("警告", f"'{Path(path).name}' は既に追加されています。")
                continue

            # PDF情報取得
            pdf_info = PDFInfo(path)
            if pdf_info.is_valid:
                self.pdf_list.append(pdf_info)
                added += 1
            else:
                errors.append(f"{pdf_info.filename}: {pdf_info.error_message}")

        if errors:
            messagebox.showwarning("エラー",
                "以下のファイルを追加できませんでした:\n\n" + "\n".join(errors))

        if added > 0:
            self._refresh_tree()
            self._update_button_states()
            self._update_status_bar()

    def _refresh_tree(self):
        """リスト更新"""
        self.tree.delete(*self.tree.get_children())
        for i, pdf in enumerate(self.pdf_list):
            self.tree.insert('', tk.END, values=(i + 1, pdf.filename, pdf.size_str, pdf.page_count))

    def _get_selected_index(self) -> Optional[int]:
        """選択インデックス取得"""
        selection = self.tree.selection()
        if not selection:
            return None
        item = selection[0]
        return self.tree.index(item)

    def _on_move_up(self):
        """上へ移動"""
        idx = self._get_selected_index()
        if idx is None or idx == 0:
            return

        self.pdf_list[idx], self.pdf_list[idx - 1] = self.pdf_list[idx - 1], self.pdf_list[idx]
        self._refresh_tree()

        # 選択を維持
        children = self.tree.get_children()
        self.tree.selection_set(children[idx - 1])
        self._update_button_states()

    def _on_move_down(self):
        """下へ移動"""
        idx = self._get_selected_index()
        if idx is None or idx >= len(self.pdf_list) - 1:
            return

        self.pdf_list[idx], self.pdf_list[idx + 1] = self.pdf_list[idx + 1], self.pdf_list[idx]
        self._refresh_tree()

        # 選択を維持
        children = self.tree.get_children()
        self.tree.selection_set(children[idx + 1])
        self._update_button_states()

    def _on_delete(self):
        """削除"""
        idx = self._get_selected_index()
        if idx is None:
            return

        del self.pdf_list[idx]
        self._refresh_tree()
        self._update_button_states()
        self._update_status_bar()

    def _on_clear(self):
        """全クリア"""
        if not self.pdf_list:
            return

        if messagebox.askyesno("確認", "すべてのファイルを削除しますか？"):
            self.pdf_list.clear()
            self._refresh_tree()
            self._update_button_states()
            self._update_status_bar()

    def _on_merge(self):
        """結合実行"""
        if len(self.pdf_list) < 2:
            messagebox.showinfo("情報", "2つ以上のPDFファイルを追加してください。")
            return

        output_path = filedialog.asksaveasfilename(
            title="保存先を選択",
            defaultextension=".pdf",
            filetypes=[("PDFファイル", "*.pdf")]
        )

        if not output_path:
            return

        # プログレスダイアログ
        self._show_progress_dialog(output_path)

    def _show_progress_dialog(self, output_path: str):
        """プログレスダイアログ表示"""
        self.merge_cancelled = False

        progress_win = tk.Toplevel(self.root)
        progress_win.title("結合中")
        progress_win.geometry("300x120")
        progress_win.resizable(False, False)
        progress_win.transient(self.root)
        progress_win.grab_set()

        ttk.Label(progress_win, text="PDFを結合しています...").pack(pady=(20, 10))

        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_win, variable=progress_var, maximum=100, length=250)
        progress_bar.pack(pady=5)

        def cancel():
            self.merge_cancelled = True

        cancel_btn = ttk.Button(progress_win, text="キャンセル", command=cancel)
        cancel_btn.pack(pady=10)

        # バックグラウンドで結合
        def merge_thread():
            try:
                output_pdf = pikepdf.Pdf.new()
                total_files = len(self.pdf_list)
                total_pages = 0

                for i, pdf_info in enumerate(self.pdf_list):
                    if self.merge_cancelled:
                        progress_win.destroy()
                        return

                    progress_var.set((i / total_files) * 100)
                    progress_win.update()

                    with pikepdf.open(pdf_info.filepath) as pdf:
                        for page in pdf.pages:
                            if self.merge_cancelled:
                                progress_win.destroy()
                                return
                            output_pdf.pages.append(page)
                            total_pages += 1

                progress_var.set(95)
                progress_win.update()

                output_pdf.save(output_path)
                progress_var.set(100)

                progress_win.destroy()

                messagebox.showinfo("完了",
                    f"PDFの結合が完了しました。\n\n"
                    f"ファイル数: {len(self.pdf_list)}\n"
                    f"総ページ数: {total_pages}\n"
                    f"保存先: {output_path}")

                self._update_status_bar(f"結合完了: {total_pages}ページ")

            except Exception as e:
                progress_win.destroy()
                messagebox.showerror("エラー", f"PDF結合中にエラーが発生しました:\n\n{str(e)}")

        thread = threading.Thread(target=merge_thread, daemon=True)
        thread.start()

    def _update_button_states(self):
        """ボタン状態更新"""
        has_files = len(self.pdf_list) > 0
        idx = self._get_selected_index()
        has_selection = idx is not None

        state_up = tk.NORMAL if has_selection and idx > 0 else tk.DISABLED
        state_down = tk.NORMAL if has_selection and idx < len(self.pdf_list) - 1 else tk.DISABLED
        state_delete = tk.NORMAL if has_selection else tk.DISABLED
        state_clear = tk.NORMAL if has_files else tk.DISABLED
        state_merge = tk.NORMAL if len(self.pdf_list) >= 2 else tk.DISABLED

        self.btn_up.config(state=state_up)
        self.btn_down.config(state=state_down)
        self.btn_delete.config(state=state_delete)
        self.btn_clear.config(state=state_clear)
        self.btn_merge.config(state=state_merge)

    def _update_status_bar(self, message: Optional[str] = None):
        """ステータスバー更新"""
        if message:
            self.status_var.set(message)
        elif not self.pdf_list:
            self.status_var.set("ファイルを追加してください")
        else:
            total_pages = sum(pdf.page_count for pdf in self.pdf_list)
            self.status_var.set(f"{len(self.pdf_list)} ファイル / 合計 {total_pages} ページ")

    def run(self):
        """アプリ実行"""
        self.root.mainloop()


def main():
    app = PDFMergeApp()
    app.run()


if __name__ == "__main__":
    main()
