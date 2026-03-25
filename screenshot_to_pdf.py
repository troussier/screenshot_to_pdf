#!/usr/bin/env python3
"""
screenshot_to_pdf.py
URLリストのスクリーンショットをまとめて1つのPDFに出力するツール

使い方:
    python screenshot_to_pdf.py              # urls.txt を読み込む
    python screenshot_to_pdf.py my_urls.txt  # ファイルを指定

urls.txt の書き方:
    # コメント（無視される）

    # --- 設定（@で始まる行）---
    @width 1280
    @basic-auth user:password
    @scroll-wait 300
    @wait-after-load 1000
    @output 確認_20260324.pdf
    @user-agent Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)

    # --- URL ---
    https://example.com
    https://staging.example.com/page
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright
from PIL import Image
import io


# デフォルト設定
DEFAULTS = {
    "width": 1280,
    "basic-auth": None,
    "scroll-wait": 300,
    "wait-after-load": 1000,
    "output": None,
    "user-agent": None,
}


def load_file(filepath: str) -> tuple[dict, list[str]]:
    """設定とURLリストをファイルから読み込む"""
    path = Path(filepath)
    if not path.exists():
        print(f"エラー: '{filepath}' が見つかりません。")
        sys.exit(1)

    config = dict(DEFAULTS)
    urls = []

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("@"):
                parts = line[1:].split(None, 1)
                key = parts[0].lower()
                value = parts[1] if len(parts) > 1 else ""
                if key not in DEFAULTS:
                    print(f"警告: 不明な設定 '@{key}' を無視します。")
                    continue
                if key in ("width", "scroll-wait", "wait-after-load"):
                    try:
                        config[key] = int(value)
                    except ValueError:
                        print(f"警告: '@{key} {value}' は数値ではありません。デフォルト値を使います。")
                else:
                    config[key] = value if value else None
            else:
                urls.append(line)

    if not urls:
        print(f"エラー: '{filepath}' に有効なURLがありません。")
        sys.exit(1)

    return config, urls


def parse_basic_auth(url: str, default_credentials: dict | None = None) -> tuple[str, dict | None]:
    """URLからBasic認証情報を取り出す。URLに認証情報があればそちらを優先。"""
    from urllib.parse import urlparse, urlunparse
    parsed = urlparse(url)
    if parsed.username:
        credentials = {"username": parsed.username, "password": parsed.password or ""}
        clean = parsed._replace(netloc=parsed.hostname + (f":{parsed.port}" if parsed.port else ""))
        return urlunparse(clean), credentials
    return url, default_credentials


def take_screenshot(browser, url: str, config: dict, default_credentials: dict | None) -> bytes | None:
    """1URLのフルページスクリーンショットを撮影してPNGバイト列を返す（2倍解像度）"""
    try:
        print(f"  撮影中: {url}")
        clean_url, credentials = parse_basic_auth(url, default_credentials)

        context_options = {
            "viewport": {"width": config["width"], "height": 900},
            "device_scale_factor": 2,  # Retina相当の2倍解像度
        }
        if credentials:
            context_options["http_credentials"] = credentials
        if config["user-agent"]:
            context_options["user_agent"] = config["user-agent"]

        context = browser.new_context(**context_options)
        page = context.new_page()
        page.goto(clean_url, wait_until="networkidle", timeout=30000)

        # ページ読み込み後の待機
        page.wait_for_timeout(config["wait-after-load"])

        # スクロールしてフェードインアニメーションをすべて発火させる
        current = 0
        while True:
            page.evaluate(f"window.scrollTo(0, {current})")
            page.wait_for_timeout(config["scroll-wait"])
            current += 900
            page_height = page.evaluate("document.body.scrollHeight")
            if current >= page_height:
                break

        # 一番上に戻ってからスクリーンショット
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        screenshot = page.screenshot(full_page=True)
        context.close()
        return screenshot
    except Exception as e:
        print(f"  ⚠ スキップ ({url}): {e}")
        return None


def screenshots_to_pdf(screenshot_bytes_list: list[tuple[str, bytes]], output_path: str):
    """スクリーンショット（PNG bytes）のリストを高品質PDFにまとめる"""
    images = []
    for url, data in screenshot_bytes_list:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        images.append(img)

    if not images:
        print("エラー: 有効なスクリーンショットがありませんでした。")
        sys.exit(1)

    first, rest = images[0], images[1:]
    first.save(
        output_path,
        save_all=True,
        append_images=rest,
        format="PDF",
        resolution=192,  # 2倍解像度に合わせて192dpi指定
    )


def main():
    parser = argparse.ArgumentParser(description="URLリストのスクリーンショットをPDFにまとめる")
    parser.add_argument(
        "urls_file",
        nargs="?",
        default="urls.txt",
        help="URLリストファイル（デフォルト: urls.txt）",
    )
    args = parser.parse_args()

    # ファイル読み込み
    config, urls = load_file(args.urls_file)

    # Basic認証の解析
    default_credentials = None
    if config["basic-auth"]:
        if ":" not in config["basic-auth"]:
            print("エラー: @basic-auth は user:password の形式で指定してください。")
            sys.exit(1)
        user, _, passwd = config["basic-auth"].partition(":")
        default_credentials = {"username": user, "password": passwd}

    # 出力ファイル名
    output_path = config["output"] or f"screenshots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    # 設定サマリーを表示
    print(f"\n設定:")
    print(f"  ブラウザ幅       : {config['width']}px")
    print(f"  Basic認証        : {'あり' if default_credentials else 'なし'}")
    print(f"  スクロール待機   : {config['scroll-wait']}ms")
    print(f"  読み込み後待機   : {config['wait-after-load']}ms")
    print(f"  User-Agent       : {config['user-agent'] or 'デフォルト'}")
    print(f"  出力ファイル     : {output_path}")
    print(f"\n{len(urls)} 件のURLを処理します\n")

    # スクリーンショット撮影
    results: list[tuple[str, bytes]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()

        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}]", end=" ")
            shot = take_screenshot(browser, url, config, default_credentials)
            if shot:
                results.append((url, shot))
                print(f"  ✓ 完了")

        browser.close()

    # PDF生成
    print(f"\nPDF生成中...")
    screenshots_to_pdf(results, output_path)
    print(f"\n✅ 完了: {output_path}  ({len(results)}/{len(urls)} ページ)")


if __name__ == "__main__":
    main()
