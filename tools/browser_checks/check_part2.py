"""End-to-end check of the Part 2 add-ons in Edge, with PASS/FAIL per check."""
import csv
import re
import sys
from pathlib import Path

import pandas as pd
from playwright.sync_api import sync_playwright

csv_path, out = sys.argv[1], Path(sys.argv[2])
out.mkdir(exist_ok=True)
AREA = '[data-testid="stLayoutWrapper"]:has(> .st-key-query_area)'
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))


def settle(page):
    page.wait_for_timeout(1200)
    page.wait_for_selector('[data-testid="stStatusWidget"]', state="detached", timeout=120000)
    page.wait_for_timeout(500)


def text(page, selector):
    return " ".join(page.locator(selector).all_inner_texts())


def card(page, name):
    return page.locator('[class*="st-key-card_"]').filter(has=page.locator(f'strong:text-is("{name}")')).first


def pick_column(page, column):
    page.locator('.st-key-top_bar [data-testid="stSelectbox"]').click()
    page.get_by_role("option", name=re.compile(rf"^{column}")).click()
    settle(page)


def add_llm(page, query):
    page.get_by_role("tab", name="New LLM Query").click()
    box = page.get_by_label("New query", exact=True)
    box.fill(query)
    box.press("Enter")
    settle(page)
    page.locator(".st-key-add_query [data-testid=stBaseButton-primary]").first.click()
    settle(page)


def add_keyword(page, words):
    page.get_by_role("tab", name="New Keyword Query").click()
    page.wait_for_timeout(400)
    box = page.get_by_label("Keywords", exact=True)
    box.fill(words)
    box.press("Enter")
    settle(page)
    page.locator(".st-key-add_keyword_query [data-testid=stBaseButton-primary]").first.click()
    settle(page)


data = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge")
    page = browser.new_page(viewport={"width": 1600, "height": 900}, accept_downloads=True)
    page.goto("http://localhost:8599")
    page.wait_for_selector('[data-testid="stFileUploaderDropzoneInput"]', state="attached", timeout=60000)
    settle(page)
    page.locator('.st-key-top_bar [data-testid="stFileUploaderDropzoneInput"]').set_input_files(csv_path)
    settle(page)
    check("tabs present", page.get_by_role("tab", name="New LLM Query").count() == 1
          and page.get_by_role("tab", name="New Keyword Query").count() == 1)

    # LLM + keyword query on transportation_open
    add_llm(page, "Mentions a person getting hit by a car or other vehicle (near misses count)")
    add_keyword(page, "car, truck, bus")
    kw = card(page, "car_truck_bus")
    check("keyword card has tag and free estimate", "Keyword" in kw.inner_text() and "Free: keyword match" in kw.inner_text())
    card(page, "person_getting_hit").get_by_role("button", name="Run", exact=True).click()
    page.wait_for_timeout(2500)
    settle(page)
    card(page, "car_truck_bus").get_by_role("button", name="Run", exact=True).click()
    settle(page)
    kw_text = card(page, "car_truck_bus").inner_text()
    pattern = re.compile(r"(?<!\w)(?:truck|car|bus)(?!\w)", re.IGNORECASE)
    expected = sum(1 for t in data["transportation_open"] if t.strip() and pattern.search(t))
    check("keyword matches = regex count", f"{expected} of 220 matched" in kw_text, f"expected {expected}")
    check("keyword run is free", "Free keyword match" in kw_text)
    check("match count in card header", f"car_truck_bus: {expected} matches" in kw_text)

    # Sidebar: the keyword query's rows, matches highlighted (no filter buttons by default)
    card(page, "car_truck_bus").locator('[class*="st-key-sidebar_"] button').first.dispatch_event("click")
    settle(page)
    side = text(page, '[data-testid="stSidebar"]')
    check("sidebar shows the query's rows", "rows of car_truck_bus" in side, side[:80])
    check("sidebar highlight only (no filter buttons)",
          page.locator('[data-testid="stSidebar"]').get_by_role("radio").count() == 0)
    check("sidebar count", f"212 shown · {expected} of 212 rows matched" in side, side[:160])
    page.screenshot(path=out / "p2_1_keyword_sidebar.png")
    page.locator('[data-testid="stSidebar"] .st-key-sidebar_clear button').first.click()
    settle(page)
    check("sidebar back to all answers", "212 answers" in text(page, '[data-testid="stSidebar"]'))

    # Second column with its own query
    pick_column(page, "safety_open")
    check("other column starts empty", page.locator('[class*="st-key-card_"]').count() == 0)
    add_keyword(page, "night, dark")
    card(page, "night_dark").get_by_role("button", name="Run", exact=True).click()
    settle(page)
    pick_column(page, "transportation_open")
    titles = page.locator('[class*="st-key-card_"] strong').all_inner_texts()
    check("first column's cards restored", "person_getting_hit" in titles and "car_truck_bus" in titles, str(titles))
    picker = page.locator('.st-key-top_bar [data-testid="stSelectbox"] input').first.input_value()
    page.locator('.st-key-top_bar [data-testid="stSelectbox"]').click()
    options = page.get_by_role("option").all_inner_texts()
    page.keyboard.press("Escape")
    check("picker shows query counts", any("safety_open · 1 query" in o for o in options)
          and any("transportation_open · 2 queries" in o for o in options), str(options))

    # Download: each column's queries right after it
    with page.expect_download() as info:
        page.locator(".st-key-bottom_bar").get_by_role("button", name="Download CSV").click()
    f = out / info.value.suggested_filename
    info.value.save_as(f)
    with open(f, encoding="utf-8-sig", newline="") as fh:
        header = next(csv.reader(fh))
    want = ["respondent_id", "neighborhood", "transportation_open",
            "person_getting_hit", "person_getting_hit_conf", "person_getting_hit_note",
            "car_truck_bus", "car_truck_bus_conf", "car_truck_bus_note",
            "housing_open", "safety_open", "night_dark", "night_dark_conf", "night_dark_note"]
    check("download column order", header == want, str(header))

    # Provider switch: Claude without a key
    page.locator(".st-key-session_info [data-testid=stPopover] button").first.click()
    page.wait_for_timeout(500)
    page.locator('[data-testid="stPopoverBody"]').get_by_text(re.compile("^Claude")).click()
    settle(page)
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    top = text(page, ".st-key-top_bar")
    check("key status follows provider", "No Claude key" in top, top[:120])
    check("Claude key warning", "Claude API key missing" in text(page, ".st-key-query_area"))
    llm_run = card(page, "person_getting_hit").get_by_role("button", name="Run", exact=True)
    kw_run = card(page, "car_truck_bus").get_by_role("button", name="Run", exact=True)
    check("LLM run disabled, keyword run enabled", llm_run.is_disabled() and kw_run.is_enabled())
    page.screenshot(path=out / "p2_2_claude_no_key.png")

    for w, h in ((1100, 800), (760, 700)):
        page.set_viewport_size({"width": w, "height": h})
        page.wait_for_timeout(800)
        page.screenshot(path=out / f"p2_resize_{w}.png")
    browser.close()

print(f"\n{sum(results)}/{len(results)} checks passed")
