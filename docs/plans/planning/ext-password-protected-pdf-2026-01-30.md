# 機能拡張計画: パスワード保護PDF対応（入力） 2026-01-30

## 1. 拡張概要

パスワードで保護されたPDFファイルを読み込み、結合処理に含められるようにする機能。ファイル追加時にパスワード入力ダイアログを表示し、正しいパスワードを入力することでファイルを追加できる。結合後はパスワードなしのPDFとして出力される。

## 2. 詳細仕様

### 2.1 現状と課題

**現在の実装:**
- `pdf_info.py` の `_load_info()` で `pikepdf.PasswordError` をキャッチしている
- エラーメッセージ「パスワードで保護されています」を設定し、`is_valid=False` としている
- パスワード保護PDFは追加できない状態

**課題:**
- 業務で使用するPDFにはパスワード保護されたものも多く、結合できないと利便性が低下
- requirements.md で「高」優先度として記載されている機能

### 2.2 拡張内容

**動作フロー:**
1. ファイル追加時（D&D / ファイル選択直後）
2. パスワード保護PDFを検出
3. パスワード入力ダイアログを表示（ファイル名明示）
4. パスワード入力 → 正しければ追加、間違いなら再入力（回数制限なし、キャンセルで中止）
5. 複数ファイル同時追加時は1ファイルずつ順番にダイアログ表示

**パスワード管理:**
- セッション中はPDFInfoオブジェクト内にパスワードを保持
- 結合時にパスワードを使用してPDFを開き、パスワードなしのPDFとして出力

**UI仕様:**
- パスワード入力ダイアログ
  - ファイル名を明示表示
  - 伏せ字入力欄 + 表示/非表示切り替えボタン
  - OK / キャンセルボタン
- ファイルリスト表示
  - パスワード保護PDFは🔒アイコンで区別

## 3. ディレクトリ構造

```
src/
├── core/
│   ├── pdf_info.py          # 変更: パスワード対応
│   └── pdf_merger.py        # 変更: パスワード付きPDF結合対応
└── ui/
    ├── main_window.py       # 変更: パスワードダイアログ呼び出し、🔒表示
    ├── password_dialog.py   # 新規: パスワード入力ダイアログ
    └── preview_window.py    # 変更: パスワード付きPDFプレビュー対応
```

## 4. 技術的影響分析

### 4.1 影響範囲

- **フロントエンド（UI）**: main_window.py, preview_window.py, password_dialog.py（新規）
- **バックエンド（Core）**: pdf_info.py, pdf_merger.py
- **データモデル**: PDFInfoクラスに `password` 属性と `is_encrypted` フラグを追加

### 4.2 変更が必要なファイル

```
- src/core/pdf_info.py: パスワード対応の_load_info()、password属性追加、is_encryptedフラグ追加、get_thumbnail()でパスワード使用
- src/core/pdf_merger.py: pikepdf.open()にパスワード指定
- src/ui/main_window.py: _add_files()でパスワードダイアログ呼び出し、_refresh_table()で🔒表示
- src/ui/password_dialog.py: 新規作成（パスワード入力ダイアログ）
- src/ui/preview_window.py: _create_preview_pdf()でパスワード指定
```

### 4.3 変更不要なファイル

```
- src/ui/rotation_dialog.py: PDFInfoを使用するがパスワードは解決済み
- src/ui/page_order_dialog.py: PDFInfoを使用するがパスワードは解決済み
- src/ui/page_extract_dialog.py: PDFInfoを使用するがパスワードは解決済み
```

## 5. タスクリスト

```
- [ ] **T1**: PDFInfoクラスにパスワード対応を追加
  - password属性追加
  - is_encryptedフラグ追加
  - _load_info()でパスワード受け取り対応
  - get_thumbnail()でパスワード使用（PyMuPDF対応）

- [ ] **T2**: パスワード入力ダイアログ(PasswordDialog)を新規作成
  - ファイル名表示
  - 伏せ字入力欄
  - 表示/非表示切り替えボタン
  - OK/キャンセルボタン

- [ ] **T3**: MainWindowの_add_files()にパスワード入力フローを追加
  - パスワード保護PDF検出時にPasswordDialogを表示
  - 正しいパスワードでPDFInfo再作成
  - 間違いなら再入力（キャンセルで中止）
  - 複数ファイル時は1ファイルずつ処理

- [ ] **T4**: MainWindowの_refresh_table()に🔒アイコン表示を追加
  - is_encrypted=Trueの場合、ファイル名の前に🔒を表示

- [ ] **T5**: PDFMergerWorkerでパスワード付きPDFを開く処理を追加
  - pikepdf.open()にpassword引数を追加

- [ ] **T6**: PreviewWindowでパスワード付きPDFを開く処理を追加
  - _create_preview_pdf()でpikepdf.open()とfitz.open()にパスワード指定

- [ ] **T7**: 動作テスト
  - パスワード保護PDFの追加
  - パスワード間違い → 再入力
  - 複数ファイル同時追加
  - 結合処理
  - プレビュー機能
```

## 6. テスト計画

| テストケース | 期待結果 |
|-------------|---------|
| パスワード保護PDF単体追加 | ダイアログ表示 → 正しいパスワードで追加成功 |
| パスワード間違い | エラー表示 → 再入力ダイアログ |
| キャンセル | ファイル追加されない |
| 複数ファイル同時追加（一部パスワード保護） | 通常PDFは即追加、保護PDFは1つずつダイアログ表示 |
| 🔒アイコン表示 | パスワード保護PDFのファイル名に🔒が表示される |
| 結合処理 | パスワードなしのPDFとして出力される |
| プレビュー | パスワード保護PDFを含む結合プレビューが表示される |
| サムネイル表示 | パスワード保護PDFのサムネイルが正常に表示される |

## 7. SCOPE_PROGRESSへの統合

```markdown
### 追加機能

| 番号 | タスク | 実装 | テスト |
|------|--------|------|--------|
| 3.22 | パスワード保護PDF対応（入力） | [ ] | [ ] |
  - 参照: [/docs/plans/planning/ext-password-protected-pdf-2026-01-30.md]
  - 内容: パスワード保護されたPDFファイルの読み込み対応
```

## 8. 備考

**技術的注意点:**
- pikepdf: `pikepdf.open(filepath, password=password)` でパスワード付きPDFを開ける
- PyMuPDF (fitz): `fitz.open(filepath, password=password)` でパスワード付きPDFを開ける
- パスワードなしで保存: `pdf.save(output_path)` とすればパスワードなしで出力される

**セキュリティ考慮:**
- パスワードはメモリ上にのみ保持（ファイルに保存しない）
- アプリケーション終了時にパスワードは破棄される
