"""Build a large synthetic CSV for stress tests (not committed; regenerate any time).

Creates:
  stress.csv      - 5,000 unique rows; matches ONLY in the last 250 rows
  stress_key.csv  - expected labels for each stress-test query

Every row is unique (so cache and de-duplication cannot reduce cost) and each
template carries flags, so the expected label for each query is known.

Run:  python sample_data/make_stress_sample.py
"""
import csv
import random
from pathlib import Path

random.seed(7)
OUT = Path(__file__).parent

TOTAL_ROWS = 5_000
MATCH_ROWS = 250          # placed at the very end of the file
LONG_ROWS = 300           # ~1,500 chars, spread through the non-match rows

# (sentence, mentions_vehicle)
COMPLAINTS = [
    ("The buses are always late and the schedule is never right.", True),
    ("Parking downtown costs too much and there are never spots.", True),
    ("Potholes on our road damaged two of my car tires.", True),
    ("The train does not stop in our town anymore.", True),
    ("Traffic on the highway is terrible at rush hour.", True),
    ("Taxis never come out to our neighborhood at night.", True),
    ("The subway escalators are always broken.", True),
    ("Gas prices make my daily car commute expensive.", True),
    ("The sidewalks are cracked and uneven.", False),
    ("I walk to work and the streetlights are often out.", False),
    ("In winter the paths are icy and nobody clears them.", False),
    ("I work from home, so I rarely travel.", False),
    ("There are no benches or shade along the main walking path.", False),
    ("The pedestrian bridge over the river is closed for repairs.", False),
]
# Neutral second sentences: no vehicles, nobody hurt.
EXTRAS = [
    "I have lived in {place} for {years} years.",
    "Honestly it has been like this since {year}.",
    'My neighbor in {place} says "nothing ever changes", and I agree.',
    "Café owners on {place} street complain too 😡, it hurts business.",
    "Please fix this soon,\nwe have asked many times.",
    "We raised it at the {place} community meeting in {year}.",
    "It is the same story every season in {place}.",
]
PLACES = ["Northside", "Riverside", "Oak Hill", "Westfield", "Eastgate", "Elm", "Maple", "Harbor", "Pine Ridge"]

CHILD_VICTIMS = ["My son", "My daughter", "A little girl on our street", "My 7-year-old nephew", "A kid from the school"]
ADULT_VICTIMS = ["My neighbor", "My husband", "An elderly man", "My coworker", "A woman at the bus stop"]
VEHICLES = ["car", "pickup truck", "delivery van", "city bus", "motorcycle", "taxi"]
BLAME_CITY = [
    "The city never fixed that crossing even after we complained.",
    "City hall ignored years of requests for a traffic light there.",
]
NO_BLAME = [
    "The driver did not even stop.",
    "Thankfully they are recovering now.",
    "It happened so fast.",
]

LONG_PARAGRAPH = (
    "Getting around {place} has become harder every year. The bus routes were cut, "
    "the remaining buses are crowded, and the timetable posted at the stop is rarely accurate. "
    "Parking near the clinic is expensive and the garage closes early. "
)


def _fill(template: str) -> str:
    return template.format(place=random.choice(PLACES), years=random.randint(1, 60),
                           year=random.randint(1990, 2026))


def _unrelated_row() -> tuple[str, dict]:
    sentence, vehicle = random.choice(COMPLAINTS)
    return f"{sentence} {_fill(random.choice(EXTRAS))}", {"no_vehicle": int(not vehicle), "long": 0}


def _long_row() -> tuple[str, dict]:
    text = " ".join(_fill(LONG_PARAGRAPH) for _ in range(6)) + _fill(random.choice(EXTRAS))
    return text, {"no_vehicle": 0, "long": 1}


def _match_row() -> tuple[str, dict]:
    child = random.random() < 0.5
    victim = random.choice(CHILD_VICTIMS if child else ADULT_VICTIMS)
    blames_city = random.random() < 0.5
    follow_up = random.choice(BLAME_CITY if blames_city else NO_BLAME)
    text = (f"{victim} was hit by a {random.choice(VEHICLES)} near {random.choice(PLACES)} "
            f"in {random.randint(2010, 2026)}. {follow_up}")
    return text, {"no_vehicle": 0, "long": 0, "child_city": int(child and blames_city)}


def _unique(make, seen: set[str]) -> tuple[str, dict]:
    while True:
        text, flags = make()
        if text not in seen:
            seen.add(text)
            return text, flags


def main() -> None:
    seen: set[str] = set()
    non_match = TOTAL_ROWS - MATCH_ROWS
    long_positions = set(random.sample(range(non_match), LONG_ROWS))

    rows = []
    for i in range(non_match):
        rows.append((*_unique(_long_row if i in long_positions else _unrelated_row, seen), 0))
    for _ in range(MATCH_ROWS):
        rows.append((*_unique(_match_row, seen), 1))

    with open(OUT / "stress.csv", "w", newline="", encoding="utf-8") as f, \
         open(OUT / "stress_key.csv", "w", newline="", encoding="utf-8") as k:
        w, kw = csv.writer(f), csv.writer(k)
        w.writerow(["respondent_id", "neighborhood", "transportation_open"])
        kw.writerow(["respondent_id", "expect_hit", "expect_no_vehicle", "expect_child_city", "is_long"])
        for n, (text, flags, hit) in enumerate(rows, start=1):
            w.writerow([n, random.choice(PLACES), text])
            kw.writerow([n, hit, flags["no_vehicle"], flags.get("child_city", 0), flags["long"]])

    print(f"Wrote {len(rows)} rows ({MATCH_ROWS} matches at the end, {LONG_ROWS} long) to {OUT / 'stress.csv'}")


if __name__ == "__main__":
    main()
