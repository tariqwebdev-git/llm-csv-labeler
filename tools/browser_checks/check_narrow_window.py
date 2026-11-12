"""Reproduce Tariq's screenshot: ~1000px window, sidebar dragged very wide. Screenshot several sizes."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

csv_path, out = sys.argv[1], Path(sys.argv[2])
out.mkdir(exist_ok=True)


def settle(page):
    page.wait_for_timeout(1500)
    page.wait_for_selector('[data-testid="stStatusWidget"]', state="detached", timeout=120000)
    page.wait_for_timeout(500)


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge")
    page = browser.new_page(viewport={"width": 1000, "height": 840})
    page.goto("http://localhost:8599")
    page.wait_for_selector('[data-testid="stFileUploaderDropzoneInput"]', state="attached", timeout=60000)
    settle(page)
    page.locator('.st-key-top_bar [data-testid="stFileUploaderDropzoneInput"]').set_input_files(csv_path)
    settle(page)
    for text in ["Mentions a person getting hit by a car or other vehicle (near misses count)",
                 "Mentions buses being late or not coming"]:
        box = page.get_by_label("New query")
        box.fill(text)
        box.press("Enter")
        settle(page)
        page.locator(".st-key-add_query [data-testid=stBaseButton-primary]").first.click()
        settle(page)
    # Drag the sidebar edge far to the right, like in the screenshot.
    side = page.locator('[data-testid="stSidebar"]').bounding_box()
    edge_x = side["x"] + side["width"] - 1
    page.mouse.move(edge_x, 400)
    page.mouse.down()
    page.mouse.move(edge_x + 300, 400, steps=10)
    page.mouse.up()
    page.wait_for_timeout(800)
    print("sidebar width:", page.locator('[data-testid="stSidebar"]').bounding_box()["width"])
    page.screenshot(path=out / "n_1000_wide_sidebar.png")
    for w, h in ((800, 700), (1366, 768), (1920, 1000)):
        page.set_viewport_size({"width": w, "height": h})
        page.wait_for_timeout(1000)
        page.screenshot(path=out / f"n_{w}.png")
    browser.close()
