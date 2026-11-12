"""Check that only the query area scrolls: bars stay put, the page itself never scrolls."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

csv_path, out = sys.argv[1], Path(sys.argv[2])
out.mkdir(exist_ok=True)
AREA = '[data-testid="stLayoutWrapper"]:has(> .st-key-query_area)'


def settle(page):
    page.wait_for_timeout(1500)
    page.wait_for_selector('[data-testid="stStatusWidget"]', state="detached", timeout=120000)
    page.wait_for_timeout(500)


def report(page, label):
    info = page.evaluate("""(area) => {
      const box = s => { const e = document.querySelector(s); if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.top), Math.round(r.bottom)]; };
      const a = document.querySelector(area); const main = document.querySelector('[data-testid=stMain]');
      return {top_bar: box('.st-key-top_bar'), bottom_bar: box('.st-key-bottom_bar'), area: box(area),
              area_scroll: a ? [a.scrollTop, a.scrollHeight, a.clientHeight] : null,
              page_scroll: [main.scrollTop, main.scrollHeight, main.clientHeight], win: window.innerHeight};
    }""", AREA)
    print(label, info)


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge")
    page = browser.new_page(viewport={"width": 1600, "height": 900})
    page.goto("http://localhost:8599")
    page.wait_for_selector('[data-testid="stFileUploaderDropzoneInput"]', state="attached", timeout=60000)
    settle(page)
    page.locator('.st-key-top_bar [data-testid="stFileUploaderDropzoneInput"]').set_input_files(csv_path)
    settle(page)
    for text in ["Mentions a person getting hit by a car or other vehicle (near misses count)",
                 "Mentions buses being late or not coming",
                 "Mentions feeling unsafe walking at night"]:
        box = page.get_by_label("New query")
        box.fill(text)
        box.press("Enter")
        settle(page)
        page.locator(".st-key-add_query [data-testid=stBaseButton-primary]").first.click()
        settle(page)
    page.get_by_role("button", name="Run", exact=True).first.click()
    page.wait_for_timeout(3000)
    settle(page)
    page.get_by_text("Results: rows needing attention first").click()
    settle(page)
    report(page, "after run:")
    page.screenshot(path=out / "a_after_run.png")

    page.mouse.move(1000, 500)
    for i in range(6):
        page.mouse.wheel(0, 600)
        page.wait_for_timeout(400)
        report(page, f"wheel {i}:")
    page.screenshot(path=out / "b_scrolled.png")
    page.evaluate("(area) => { const a = document.querySelector(area); a.scrollTop = a.scrollHeight; }", AREA)
    page.wait_for_timeout(500)
    report(page, "bottom:")
    page.screenshot(path=out / "c_bottom.png")

    for w, h in ((1100, 800), (760, 700)):
        page.set_viewport_size({"width": w, "height": h})
        page.wait_for_timeout(1000)
        report(page, f"{w}x{h}:")
        page.screenshot(path=out / f"d_{w}.png")
    browser.close()
