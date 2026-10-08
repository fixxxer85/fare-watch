"""Fetch cheapest business-class fares for each route in watchlist.json
and append a snapshot to data/prices.json. Uses the unofficial `fli` library
(pip package name: flights)."""
import json, os, time, datetime as dt, urllib.request
from pathlib import Path
from fli.models import (Airport, FlightSearchFilters, FlightSegment, MaxStops,
                        PassengerInfo, SeatType, SortBy, TripType)
from fli.search import SearchFlights

ROOT = Path(__file__).resolve().parent.parent
WATCH, OUT = ROOT / "watchlist.json", ROOT / "data" / "prices.json"
MAX_RUNS = 400
SEAT = {"business": SeatType.BUSINESS, "economy": SeatType.ECONOMY,
        "premium": SeatType.PREMIUM_ECONOMY, "first": SeatType.FIRST}


def wanted(leg, route):
    a = getattr(leg, "airline", None)
    code = str(getattr(a, "name", a)).upper()
    label = str(getattr(a, "value", a)).lower()
    codes = [c.upper() for c in route.get("airline_codes", [])]
    names = [n.lower() for n in route.get("airline_names", [])]
    if not codes and not names:
        return True
    return code in codes or any(n in label for n in names)


def search(route, date):
    seg = FlightSegment(
        departure_airport=[[getattr(Airport, route["from"]), 0]],
        arrival_airport=[[getattr(Airport, route["to"]), 0]],
        travel_date=date)
    filters = FlightSearchFilters(
        trip_type=TripType.ONE_WAY,
        passenger_info=PassengerInfo(adults=route.get("adults", 1)),
        flight_segments=[seg],
        seat_type=SEAT[route.get("cabin", "business")],
        stops=MaxStops.ANY, sort_by=SortBy.CHEAPEST)
    return SearchFlights().search(filters, top_n=30) or []


def best_fare(route, date):
    best = None
    for r in search(route, date):
        r = r[0] if isinstance(r, tuple) else r
        legs = getattr(r, "legs", [])
        if not legs or not all(wanted(l, route) for l in legs):
            continue
        if best is None or r.price < best["p"]:
            first = legs[0]
            dep = getattr(first, "departure_datetime", None)
            best = {"d": date, "p": round(float(r.price), 2),
                    "f": f'{getattr(first.airline, "name", "")} {getattr(first, "flight_number", "")}'.strip(),
                    "dep": dep.strftime("%H:%M") if dep else "",
                    "stops": max(len(legs) - 1, 0)}
    return best


def notify(msg):
    topic = os.environ.get("NTFY_TOPIC")
    if topic:
        urllib.request.urlopen(urllib.request.Request(
            f"https://ntfy.sh/{topic}", data=msg.encode(), method="POST"), timeout=15)


def main():
    routes = json.loads(WATCH.read_text())
    data = json.loads(OUT.read_text())
    today, now = dt.date.today(), dt.datetime.now(dt.timezone.utc)
    for route in routes:
        fares = []
        step = max(route.get("sample_every_days", 7), 1)
        for n in range(route["days_ahead_from"], route["days_ahead_to"] + 1, step):
            date = (today + dt.timedelta(days=n)).isoformat()
            try:
                fare = best_fare(route, date)
                if fare:
                    fares.append(fare)
            except Exception as e:  # keep going if one date fails
                print(f'{route["id"]} {date}: {e}')
            time.sleep(2)
        entry = data["routes"].setdefault(route["id"], {"runs": []})
        entry.update({"label": f'{route["from"]} → {route["to"]}',
                      "airline": ", ".join(route.get("airline_codes", [])) or "any airline",
                      "cabin": route.get("cabin", "business"),
                      "currency": route.get("currency_label", "")})
        prev = [min(f["p"] for f in r["fares"]) for r in entry["runs"] if r["fares"]]
        entry["runs"].append({"t": now.isoformat(timespec="minutes"), "fares": fares})
        entry["runs"] = entry["runs"][-MAX_RUNS:]
        if fares:
            low = min(fares, key=lambda f: f["p"])
            thr = route.get("alert_below", 0)
            if thr and low["p"] <= thr and (not prev or low["p"] < prev[-1]):
                notify(f'{entry["label"]} {entry["cabin"]}: {entry["currency"]} {low["p"]:.0f} on {low["d"]} ({low["f"]})')
    data["updated"] = now.isoformat(timespec="minutes")
    OUT.write_text(json.dumps(data, separators=(",", ":")))


if __name__ == "__main__":
    main()
