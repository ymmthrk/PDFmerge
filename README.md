# PDFmerge

ローカルで動作する安全なPDF結合ツール

## 概要

PDFmergeは、複数のPDFファイルを1つに結合するWindowsデスクトップアプリケーションです。完全にローカルで動作し、外部サーバーへのファイルアップロードを一切行わないため、機密文書を安全に扱えます。

## 主な機能

| 機能 | 説明 |
|------|------|
| PDF結合 | 複数のPDFを1つのファイルに統合 |
| ファイル順序操作 | ドラッグ&ドロップで直感的に並び替え |
| ページ回転 | 90°/180°/270°回転、リセット機能 |
| ページ順序入替 | ファイル内のページ順序を変更 |
| ページ抽出 | 特定ページのみを結合対象に指定 |
| サムネイルプレビュー | 全ページをスクロール表示で確認 |
| 結合プレビュー | 保存前に結合結果を確認 |

## 動作環境

- Windows 10 / 11
- 追加ランタイム不要（単一exeで動作）

## インストール

1. `dist/PDFmerge.exe` をダウンロード
2. 任意のフォルダに配置
3. ダブルクリックで起動

※インストーラーは不要です

## 使い方

### 基本操作

1. **ファイル追加**: ドラッグ&ドロップまたは「ファイルを選択」ボタン
2. **順序変更**: リスト内でドラッグ、または「上へ」「下へ」ボタン
3. **結合実行**: 「結合して保存」ボタンで保存先を指定

### ページ操作

| ボタン | 機能 |
|--------|------|
| 🔄 回転 | 選択ファイルのページを回転 |
| 📄 ページ順序 | ファイル内のページ順序を変更 |
| ✂ ページ抽出 | 特定ページのみを使用 |

### プレビュー

- **サムネイルパネル**: 右側に選択ファイルの全ページを表示
- **プレビューボタン**: 結合後のPDFを保存前に確認

## ビルド方法

### 必要環境

- Python 3.11以上
- pip

### メイン版（PySide6）ビルド

```batch
cd C:\PDFmerge
pip install -r requirements.txt
build.bat
```

出力: `dist\PDFmerge.exe`（約70MB）

### 軽量版（tkinter）ビルド

```batch
cd C:\PDFmerge
pip install -r requirements_tk.txt
build_tk.bat
```

出力: `dist\PDFmerge_tk.exe`（約26MB）

## 技術スタック

| 要素 | 技術 |
|------|------|
| 言語 | Python 3.11+ |
| GUI | PySide6 |
| PDF処理 | pikepdf, PyMuPDF |
| 配布 | PyInstaller |

## ファイル構成

```
PDFmerge/
├── src/                    # メイン版ソースコード
│   ├── main.py
│   ├── version.py          # バージョン情報
│   ├── core/               # コアロジック
│   │   ├── pdf_info.py
│   │   └── pdf_merger.py
│   └── ui/                 # UI コンポーネント
│       ├── main_window.py
│       ├── rotation_dialog.py
│       ├── page_order_dialog.py
│       ├── page_extract_dialog.py
│       └── preview_window.py
├── src_tk/                 # 軽量版ソースコード
├── docs/                   # ドキュメント
│   ├── requirements.md
│   └── SCOPE_PROGRESS.md
├── mockups/                # UIモックアップ
├── build.spec              # PyInstaller設定（メイン版）
├── build_tk.spec           # PyInstaller設定（軽量版）
├── version_info.txt        # Windowsバージョン情報
└── requirements.txt        # 依存パッケージ
```

## バージョン

現在のバージョン: **1.0.0**

バージョン情報は以下で確認できます：
- ウィンドウタイトル
- Aboutダイアログ
- exeファイルのプロパティ

## ライセンス

Copyright (c) 2025 BlueLamp

## セキュリティ

- 外部ネットワーク通信を一切行いません
- ユーザーが選択したファイルのみにアクセスします
- 一時ファイルは処理完了後に削除されます
