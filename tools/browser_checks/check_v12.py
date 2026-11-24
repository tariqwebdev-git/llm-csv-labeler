"""v1.2.0 check in Edge: two-column cards on wide windows, one column on narrow ones,
slim cards (test results start collapsed), and the sidebar's "No match yet" view.
Keyword queries only, so it costs nothing. PASS/FAIL per check."""
import re
import sys
from pathlib import Path

import pandas as pd
from playwright.sync_api import sync_playwright

csv_path, out = sys.argv[1], Path(sys.argv[2])
out.mkdir(exist_ok=True)
AREA = '[data-testid="stLayoutWrapper"]:has(> .st-key-query_area)'
CARDS = '[class*="st-key-card_"]'
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))


def settle(page):
    page.wait_for_timeout(1200)
    page.wait_for_selector('[data-testid="stStatusWidget"]', state="detached", timeout=120000)
    page.wait_for_timeout(500)


def card(page, name):
    return page.locator(CARDS).filter(has=page.locator(f'strong:text-is("{name}")')).first


def add_keyword(page, words):
    page.get_by_role("tab", name="New Keyword Query").click()
    page.wait_for_timeout(400)
    box = page.get_by_label("Keywords", exact=True)
    box.fill(words)
    box.press("Enter")
    settle(page)
    page.locator(".st-key-add_keyword_query [data-testid=stBaseButton-primary]").first.click()
    settle(page)


def card_boxes(page):
    return [page.locator(CARDS).nth(i).bounding_box() for i in range(page.locator(CARDS).count())]


def no_match_count(page):
    label = page.locator('[data-testid="stSidebar"]').get_by_text(re.compile(r"No match yet \(\d+\)")).first
    return int(re.search(r"\((\d+)\)", label.inner_text()).group(1))


def layout(page):
    return page.evaluate(f"""() => {{
        const area = document.querySelector('{AREA}');
        return {{area_scroll: area.scrollTop, area_max: area.scrollHeight - area.clientHeight,
                 page_scroll: document.scrollingElement.scrollTop}};
    }}""")


data = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
answers = sum(1 for t in data["transportation_open"] if t.strip())
with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge")
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto("http://localhost:8599")
    page.wait_for_selector('[data-testid="stFileUploaderDropzoneInput"]', state="attached", timeout=60000)
    settle(page)
    page.locator('.st-key-top_bar [data-testid="stFileUploaderDropzoneInput"]').set_input_files(csv_path)
    settle(page)

    check("no match yet starts with every answer", no_match_count(page) == answers, f"{answers} answers")
    for words in ("car", "bus, train", "truck*", "bike, bicycle"):
        add_keyword(page, words)

    boxes = card_boxes(page)
    check("1920 px: cards in two columns", len(boxes) == 4 and boxes[0]["y"] == boxes[1]["y"]
          and boxes[1]["x"] > boxes[0]["x"] + boxes[0]["width"] - 1, str([(round(b["x"]), round(b["y"])) for b in boxes]))

    card(page, "car").get_by_role("button", name="Run", exact=True).click()
    settle(page)
    car = card(page, "car").inner_text()
    matched = int(re.search(r"(\d+) of 220 matched", car).group(1))
    check("one-line stats after a run", "free keyword match" in car and "Notes:" not in car)
    check("estimate hidden after the first run", "Free: keyword match, no API" not in car)
    check("no match yet drops after a run", no_match_count(page) == answers - matched,
          f"{no_match_count(page)} = {answers} - {matched}")

    card(page, "bus_train").get_by_role("button", name="Test (20 rows)", exact=True).click()
    settle(page)
    test_expander = card(page, "bus_train").locator('[data-testid="stExpander"] details').first
    check("test results start collapsed", test_expander.get_attribute("open") is None)

    page.locator('[data-testid="stSidebar"]').get_by_text(re.compile(r"No match yet \(\d+\)")).first.click()
    settle(page)
    sidebar = page.locator('[data-testid="stSidebar"]').inner_text()
    check("no match yet list shown", f"{answers - matched} answers" in sidebar and "none of this column's queries" in sidebar)
    page.screenshot(path=str(out / "v12_wide_two_columns.png"))

    area = page.locator(AREA)
    area.hover()
    page.mouse.wheel(0, 3000)
    page.wait_for_timeout(600)
    after = layout(page)
    check("only the query area scrolls (wide)", after["page_scroll"] == 0, str(after))

    page.set_viewport_size({"width": 1100, "height": 800})
    page.wait_for_timeout(1500)
    boxes = card_boxes(page)
    check("1100 px: one column", len({round(b["x"]) for b in boxes}) == 1, str([round(b["x"]) for b in boxes]))
    page.screenshot(path=str(out / "v12_narrow_one_column.png"))

    browser.close()

print(f"{sum(results)}/{len(results)} checks passed")
