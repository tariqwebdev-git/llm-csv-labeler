"""End-to-end check of every test-guide step in Edge, with PASS/FAIL per check."""
import csv
import json
import sys
from pathlib import Path

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
    page.wait_for_timeout(400)


def text(page, selector):
    return " ".join(page.locator(selector).all_inner_texts())


def card(page, name):
    return page.locator('[class*="st-key-card_"]').filter(has=page.locator(f'strong:text-is("{name}")')).first


def add_query(page, query):
    box = page.get_by_label("New query")
    box.fill(query)
    box.press("Enter")
    settle(page)
    suggested = page.locator('.st-key-top_bar input[aria-label="Column name"]').input_value()
    page.locator(".st-key-add_query [data-testid=stBaseButton-primary]").first.click()
    settle(page)
    return suggested


def boxes(page):
    return page.evaluate("""(area) => {
      const b = s => { const r = document.querySelector(s).getBoundingClientRect(); return [Math.round(r.top), Math.round(r.bottom)]; };
      const a = document.querySelector(area), m = document.querySelector('[data-testid=stMain]');
      return {top: b('.st-key-top_bar'), bottom: b('.st-key-bottom_bar'), area_scroll: a.scrollTop,
              area_max: a.scrollHeight - a.clientHeight, page_scroll: m.scrollTop};
    }""", AREA)


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge")
    page = browser.new_page(viewport={"width": 1600, "height": 900}, accept_downloads=True)
    page.goto("http://localhost:8599")
    page.wait_for_selector('[data-testid="stFileUploaderDropzoneInput"]', state="attached", timeout=60000)
    settle(page)

    # 1. Start
    check("1 no big headers", page.locator("h1").count() == 0)
    top = text(page, ".st-key-top_bar")
    check("1 key status and spend top right", "key" in top and "Spent $" in top, top[:120])

    # 2. Upload
    page.locator('.st-key-top_bar [data-testid="stFileUploaderDropzoneInput"]').set_input_files(csv_path)
    settle(page)
    picked = page.locator('.st-key-top_bar [data-testid="stSelectbox"] input').first.input_value()
    check("2 text column guessed", picked.startswith("transportation_open"), picked)
    check("2 empty-rows warning", "8 of 220 rows are empty" in text(page, ".st-key-query_area"))
    preview = page.locator('[data-testid="stExpander"]').filter(has_text="Data preview: 220 rows, 5 columns").first
    check("2 data preview collapsed", preview.count() == 1 and preview.locator("details").get_attribute("open") is None)
    side = text(page, '[data-testid="stSidebar"]')
    check("2 sidebar lists answers", "transportation_open · 212 answers" in side)

    # 3. Sidebar follows column
    page.locator('.st-key-top_bar [data-testid="stSelectbox"]').click()
    page.get_by_role("option", name="housing_open").click()
    settle(page)
    check("3 sidebar follows column", "housing_open ·" in text(page, '[data-testid="stSidebar"]'))
    page.locator('.st-key-top_bar [data-testid="stSelectbox"]').click()
    page.get_by_role("option", name="transportation_open").click()
    settle(page)
    check("3 sidebar back", "transportation_open · 212 answers" in text(page, '[data-testid="stSidebar"]'))

    # 4. Short query warning
    box = page.get_by_label("New query")
    check("4 one-line box with hint", box.evaluate("e => e.tagName") == "INPUT" and "full sentence" in (box.get_attribute("placeholder") or ""))
    box.fill("accident")
    box.press("Enter")
    settle(page)
    check("4 short query warning", "Short queries are often misread" in text(page, ".st-key-top_bar"))
    box.fill("")
    box.press("Enter")
    settle(page)

    # 5. Add 3 queries
    names = [add_query(page, q) for q in [
        "Mentions a person getting hit by a car or other vehicle (near misses count)",
        "Mentions buses being late or not coming",
        "Mentions feeling unsafe walking at night"]]
    check("5 suggested names", names == ["person_getting_hit", "buses_being_late", "feeling_unsafe_walking"], str(names))
    check("5 three cards", page.locator('[class*="st-key-card_"]').count() == 3)

    # 7. Test + cache
    c1 = card(page, "person_getting_hit")
    c1.get_by_role("button", name="Test (20 rows)").click()
    page.wait_for_timeout(2500)
    settle(page)
    t = text(page, ".st-key-query_area")
    check("7 test result", "Test on 20 rows:" in t and "matched" in t)
    c1.get_by_role("button", name="Test (20 rows)").click()
    settle(page)
    check("7 re-test from cache costs $0", "cost $0.0000" in text(page, ".st-key-query_area"))

    # 8. Edit + save
    c1.get_by_role("button", name="Edit").click()
    settle(page)
    ed = c1.locator("textarea").first
    ed.fill("Mentions a person getting hit by a truck or other vehicle (near misses count)")
    c1.get_by_role("button", name="Save").click()
    settle(page)
    check("8 edit saved", "hit by a truck" in text(page, ".st-key-query_area"))
    c1.get_by_role("button", name="Edit").click()
    settle(page)
    c1.locator("textarea").first.fill("Mentions a person getting hit by a car or other vehicle (near misses count)")
    c1.get_by_role("button", name="Save").click()
    settle(page)

    # 9. Run
    c1.get_by_role("button", name="Run", exact=True).click()
    page.wait_for_timeout(3000)
    settle(page)
    t = text(page, ".st-key-query_area")
    check("9 run box", "of 220 matched" in t and "Done" in t)
    c1.get_by_text("Results: rows needing attention first").click()
    settle(page)
    page.screenshot(path=out / "09_run.png")

    # 6. Fixed bars + scroll (with results open, lots to scroll)
    before = boxes(page)
    page.evaluate("(a) => document.querySelector(a).scrollTop = 99999", AREA)
    page.wait_for_timeout(500)
    after = boxes(page)
    check("6 bars fixed while scrolling", before["top"] == after["top"] and before["bottom"] == after["bottom"], f"{before} -> {after}")
    check("6 only query area scrolls", after["area_scroll"] > 0 and after["page_scroll"] == 0 and after["area_scroll"] >= after["area_max"] - 1)
    page.screenshot(path=out / "06_scrolled_bottom.png")
    page.evaluate("(a) => document.querySelector(a).scrollTop = 0", AREA)

    # 6b. Collapse
    c2 = card(page, "buses_being_late")
    c2.locator('[class*="st-key-toggle_"] button').first.dispatch_event("click")
    settle(page)
    check("6 card collapses", card(page, "buses_being_late").get_by_role("button", name="Run", exact=True).count() == 0)
    card(page, "buses_being_late").locator('[class*="st-key-toggle_"] button').first.dispatch_event("click")
    settle(page)
    check("6 card opens again", card(page, "buses_being_late").get_by_role("button", name="Run", exact=True).count() == 1)

    # 10. Download
    with page.expect_download() as info:
        page.locator(".st-key-bottom_bar").get_by_role("button", name="Download CSV").click()
    f = out / info.value.suggested_filename
    info.value.save_as(f)
    with open(f, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    want = ["respondent_id", "neighborhood", "transportation_open", "person_getting_hit", "person_getting_hit_conf",
            "person_getting_hit_note", "housing_open", "safety_open"]
    check("10 download column order", rows[0] == want, str(rows[0]))
    check("10 download has all rows", len(rows) == 221)

    # 11. Save, delete, load
    with page.expect_download() as info:
        page.locator(".st-key-bottom_bar").get_by_role("button", name="Save queries").click()
    saved = out / "queries.json"
    info.value.save_as(saved)
    check("11 saved 3 queries", len(json.loads(saved.read_text())["queries"]) == 3)
    c3 = card(page, "feeling_unsafe_walking")
    c3.get_by_role("button", name="Delete").click()
    settle(page)
    card(page, "feeling_unsafe_walking").get_by_role("button", name="Yes, delete").click()
    settle(page)
    check("11 delete with confirm", page.locator('[class*="st-key-card_"]').count() == 2)
    page.locator(".st-key-bottom_bar").get_by_role("button", name="Load queries").click()
    page.wait_for_timeout(800)
    page.locator('[data-testid="stPopoverBody"] [data-testid="stFileUploaderDropzoneInput"]').set_input_files(saved)
    settle(page)
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    titles = page.locator('[class*="st-key-card_"] strong').all_inner_texts()
    check("11 load adds Not run cards", page.locator('[class*="st-key-card_"]').count() == 5 and "feeling_unsafe_walking" in titles, str(titles))

    # 12. Settings + clear cache, then the test costs again
    page.locator(".st-key-session_info [data-testid=stPopover] button").first.click()
    page.wait_for_timeout(600)
    pop = text(page, '[data-testid="stPopoverBody"]')
    check("12 gear shows model", "gpt-6-luna" in pop)
    page.locator('[data-testid="stPopoverBody"]').get_by_role("button", name="Clear cache").click()
    settle(page)
    page.keyboard.press("Escape")
    card(page, "person_getting_hit").get_by_role("button", name="Test (20 rows)").click()
    page.wait_for_timeout(2500)
    settle(page)
    t = text(page, ".st-key-query_area")
    check("12 after clear cache, test costs again", "cost $0.0000" not in t.split("Test on 20 rows")[1][:80], t.split("Test on 20 rows")[1][:80])

    # Resize
    for w, h in ((1100, 800), (760, 700)):
        page.set_viewport_size({"width": w, "height": h})
        page.wait_for_timeout(800)
        b = boxes(page)
        check(f"resize {w}x{h}: bars inside window, page not scrolling",
              b["top"][0] >= 0 and b["bottom"][1] <= h and b["page_scroll"] == 0, str(b))
        page.screenshot(path=out / f"resize_{w}.png")
    browser.close()

print(f"\n{sum(results)}/{len(results)} checks passed")
