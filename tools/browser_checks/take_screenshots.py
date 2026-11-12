"""Three screenshots for Asad: after a Run, collapsed cards, a long answer opened by double-click."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

csv_path, out = sys.argv[1], Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
AREA = '[data-testid="stLayoutWrapper"]:has(> .st-key-query_area)'


def settle(page):
    page.wait_for_timeout(1200)
    page.wait_for_selector('[data-testid="stStatusWidget"]', state="detached", timeout=120000)
    page.wait_for_timeout(600)


def card(page, name):
    return page.locator('[class*="st-key-card_"]').filter(has=page.locator(f'strong:text-is("{name}")')).first


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge")
    page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5)
    page.goto("http://localhost:8599")
    page.wait_for_selector('[data-testid="stFileUploaderDropzoneInput"]', state="attached", timeout=60000)
    settle(page)
    page.locator('.st-key-top_bar [data-testid="stFileUploaderDropzoneInput"]').set_input_files(csv_path)
    settle(page)
    for q in ["Mentions a person getting hit by a car or other vehicle (near misses count)",
              "Mentions buses being late or not coming",
              "Mentions feeling unsafe walking at night"]:
        box = page.get_by_label("New query")
        box.fill(q)
        box.press("Enter")
        settle(page)
        page.locator(".st-key-add_query [data-testid=stBaseButton-primary]").first.click()
        settle(page)

    card(page, "person_getting_hit").get_by_role("button", name="Run", exact=True).click()
    page.wait_for_timeout(3000)
    settle(page)
    card(page, "buses_being_late").get_by_role("button", name="Test (20 rows)").click()
    page.wait_for_timeout(3000)
    settle(page)
    card(page, "person_getting_hit").get_by_text("Results: rows needing attention first").click()
    settle(page)
    page.evaluate("(a) => document.querySelector(a).scrollTop = 0", AREA)
    page.wait_for_timeout(500)
    page.screenshot(path=out / "1_after_run.png")

    # Collapse the first and third card; the second shows its test result.
    for name in ("person_getting_hit", "feeling_unsafe_walking"):
        card(page, name).locator('[class*="st-key-toggle_"] button').first.dispatch_event("click")
        settle(page)
    page.evaluate("(a) => document.querySelector(a).scrollTop = 0", AREA)
    page.wait_for_timeout(500)
    page.screenshot(path=out / "2_collapsed_cards.png")

    # Sidebar: scroll the list to row 22 (a very long answer) and double-click it.
    grid = page.locator('[data-testid="stSidebar"] [data-testid="stDataFrame"]').first
    gb = grid.bounding_box()
    page.mouse.move(gb["x"] + gb["width"] * 0.6, gb["y"] + gb["height"] * 0.5)
    page.mouse.wheel(0, 21 * 80)
    page.wait_for_timeout(1000)
    page.mouse.dblclick(gb["x"] + gb["width"] * 0.6, gb["y"] + 80)
    page.wait_for_timeout(1200)
    page.screenshot(path=out / "3_full_answer.png")
    browser.close()
print("saved to", out)
