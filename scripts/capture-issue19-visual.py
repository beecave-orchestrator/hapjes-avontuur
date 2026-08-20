#!/usr/bin/env python3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "visual"
OUT.mkdir(parents=True, exist_ok=True)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *args):
        pass


httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
Thread(target=httpd.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{httpd.server_address[1]}/index.html"

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--no-sandbox"])

    def shot(width, height, name, setup):
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(url, wait_until="load")
        setup(page)
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT / name), full_page=True)
        page.close()

    def open_picker(page):
        page.click("#mealChip")
        page.wait_for_selector("#mealPicker.show")

    def open_plate(page):
        open_picker(page)
        page.click('[data-meal="pasta"]')
        page.click("#pickerDone")
        page.wait_for_selector("#pickerStep2:not([hidden])")

    shot(390, 844, "issue19-presets-phone.png", open_picker)
    shot(1280, 900, "issue19-presets-desktop.png", open_picker)
    shot(390, 844, "issue19-plate-phone.png", open_plate)
    shot(1280, 900, "issue19-plate-desktop.png", open_plate)
    browser.close()

httpd.shutdown()
print("wrote 4 screenshots")
