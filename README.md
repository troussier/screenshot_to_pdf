# screenshot_to_pdf

URLリストのスクリーンショットをまとめて1つのPDFに出力するツールです。

---

## セットアップ（初回のみ）

### 1. 仮想環境を作成する

スクリプトを置いたフォルダで実行します。

```bash
cd /path/to/screenshot_to_pdf
python3 -m venv venv
```

### 2. 仮想環境を有効化する

```bash
source venv/bin/activate
```

ターミナルの先頭に `(venv)` と表示されれば有効化されています。

### 3. ライブラリをインストールする

```bash
pip install playwright Pillow
playwright install chromium
```

---

## 毎回の使い方

### 1. 仮想環境を有効化する

```bash
cd /path/to/screenshot_to_pdf
source venv/bin/activate
```

### 2. urls.txt を編集する

設定とURLを記述します（詳細は後述）。

### 3. スクリプトを実行する

```bash
python screenshot_to_pdf.py
```

URLファイルを指定することもできます。

```bash
python screenshot_to_pdf.py sanflare_urls.txt
```

---

## urls.txt の書き方

`#` から始まる行はコメントとして無視されます。
`@` から始まる行が設定、それ以外がURLです。

```
# ============================================================
# 設定
# ============================================================

@width 1280
@basic-auth user:password
@scroll-wait 300
@wait-after-load 1000
@output 確認_20260324.pdf
@user-agent Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15

# ============================================================
# URL
# ============================================================

https://example.com
https://staging.example.com/page
```

### 設定一覧

| 設定キー | 説明 | デフォルト |
|---|---|---|
| `@width` | ブラウザ幅（px） | `1280` |
| `@basic-auth` | 共通のBasic認証（`user:password` 形式） | なし |
| `@scroll-wait` | スクロール間の待機時間（ms）。アニメーションが重い場合は増やす | `300` |
| `@wait-after-load` | ページ読み込み後の追加待機時間（ms） | `1000` |
| `@output` | 出力PDFファイル名。省略すると `screenshots_YYYYMMDD_HHMMSS.pdf` になる | なし |
| `@user-agent` | User-Agent文字列。スマホ表示の確認などに使う | デフォルト |

### Basic認証について

`@basic-auth` で全URLに共通の認証情報を適用できます。
一部のURLだけ別の認証情報が必要な場合は、そのURLだけ `user:password@ホスト名` 形式で記述するとURL個別の設定が優先されます。

```
@basic-auth common_user:common_pass

https://staging.example.com/page1
https://staging.example.com/page2

# このURLだけ別の認証情報を使う
https://other_user:other_pass@other.example.com/page
```

### スマホ表示を確認したい場合

`@user-agent` にスマートフォンのUser-Agent文字列を指定します。
`@width` も合わせて変更するとより正確です。

```
@width 390
@user-agent Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15
```

---

## 注意事項

- タイムアウトは30秒です。重いページはスキップされ、警告が表示されます
- ログイン必須ページ（セッション認証など）は撮影できません
- PDFは各URLが1ページになり、ページの高さはスクロール量に応じて自動調整されます
- 出力PDFは2倍解像度（Retina相当）で撮影しているためファイルサイズが大きくなることがあります

---

## フォルダを移動したい場合

`venv` フォルダは絶対パスで構成されているため、フォルダを移動すると壊れます。
移動後は `venv` を削除して作り直してください。

```bash
cd /移動先/screenshot_to_pdf
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install playwright Pillow
playwright install chromium
```

スクリプト本体（`screenshot_to_pdf.py`）と `urls.txt` はそのまま使えます。
