"""Build the reading_channels.channel_id backfill map (read-only).

Run right before the channel_id migration, against the live table:

    GW_DATA_DB_URL=<read-only url> uv run python scripts/channel_id_backfill_map.py

TLAYOUTS_DIR names the tlayouts checkout (default: the sibling `tlayouts`),
which must have `main` and `jm/spruce` fetched.

channel_id for a data/derived/synth row is the layout Id for the row's
(terminal asset, name, unit), taken from the first layer that declares it:

  1. tlayouts jm/spruce output  (the 013 layouts about to publish)
  2. tlayouts main output       (the layouts the House0 boxes run now)
  3. journal layout.lite history, the newest layout that declares the pair

A pseudo row gets NULL. Where one channel_id would span two units, the rows
in the unit the top layer does not declare get NULL (a scale conflict).
Writes alembic/versions/channel_id_backfill.csv (row id, channel_id, source)
and prints the tally, every disagreement between layers, and the conflicts.
"""
import csv
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict

import psycopg

TLAYOUTS = os.environ.get("TLAYOUTS_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tlayouts"))
LAYERS = [
    ("tlayouts jm/spruce", "jm/spruce", [
        "output/beech/hardware-layout.generated.json",
        "output/maple/hardware-layout.generated.json",
        "output/oak/gw.house0.layout.json",
        "output/spruce/gw.nolan.layout.json",
    ]),
    ("tlayouts main", "main", [
        "output/beech/hardware-layout.json",
        "output/fir/hardware-layout.json",
        "output/maple/hardware-layout.json",
        "output/oak/hardware-layout.json",
    ]),
]
HISTORY_SQL = """
with l as (
  select from_alias, payload, created_at from gridworks.messages where message_type_name='layout.lite'
)
select from_alias, c->>'Id', c->>'Name', c->>%(unitkey)s, max(l.created_at)
from l, jsonb_array_elements(coalesce(l.payload->%(arr)s, '[]'::jsonb)) c
group by 1,2,3,4
"""
ARRAYS = (("DataChannels", "TelemetryName"), ("DerivedChannels", "OutputUnit"), ("SynthChannels", "TelemetryName"))


def tlayouts_layer(ref: str, paths: list[str]) -> dict[tuple, str]:
    m: dict[tuple, str] = {}
    for p in paths:
        d = json.loads(subprocess.check_output(["git", "-C", TLAYOUTS, "show", f"{ref}:{p}"]))
        for arr, unitkey in ARRAYS:
            for c in d.get(arr) or []:
                key = (c["TerminalAssetAlias"], c["Name"], c.get(unitkey) or "Unknown")
                m[key] = c["Id"]
    return m


def journal_layer(cur) -> dict[tuple, str]:
    newest: dict[tuple, tuple] = {}
    for arr, unitkey in ARRAYS:
        cur.execute(HISTORY_SQL, {"arr": arr, "unitkey": unitkey})
        for from_alias, cid, name, unit, t in cur.fetchall():
            key = (from_alias.rsplit(".", 1)[0] + ".ta", name, unit or "Unknown")
            if key not in newest or t > newest[key][1]:
                newest[key] = (cid, t)
    return {k: v[0] for k, v in newest.items()}


def main() -> None:
    with psycopg.connect(os.environ["GW_DATA_DB_URL"]) as conn, conn.cursor() as cur:
        cur.execute("select id, name, terminal_asset_alias, unit, channel_type, deactivated_date from gridworks.reading_channels order by terminal_asset_alias, name, deactivated_date nulls last")
        rows = cur.fetchall()
        layers = [(label, tlayouts_layer(ref, paths)) for label, ref, paths in LAYERS]
        layers.append(("journal history", journal_layer(cur)))
    print(f"rows={len(rows)} " + " ".join(f"{l}={len(m)}" for l, m in layers), file=sys.stderr)

    print("== disagreements between layers (same asset, name, unit; different Id)")
    keys = set().union(*(m.keys() for _, m in layers))
    n = 0
    for key in sorted(keys):
        ids = [(l, m[key]) for l, m in layers if key in m]
        if len({i for _, i in ids}) > 1:
            n += 1
            print(" ", *key, " | ".join(f"{l}={i[:8]}" for l, i in ids))
    print(f"  ({n})")

    def lookup(key):
        for label, m in layers:
            if key in m:
                return m[key], label
        return None, None

    out = []
    tally: Counter = Counter()
    by_chan: dict[tuple, set[str]] = defaultdict(set)
    for rid, name, ta, unit, ctype, deact in rows:
        rid = str(rid)
        if ctype == "gjk.pseudo":
            out.append((rid, ta, name, unit, None, "pseudo", deact))
            continue
        chan, src = lookup((ta, name, unit))
        if chan is None:
            out.append((rid, ta, name, unit, None, "UNMAPPED", deact))
            continue
        by_chan[(ta, chan)].add(unit)
        out.append((rid, ta, name, unit, chan, src, deact))

    # scale conflicts: one channel_id, two units -> keep the unit the top layer declares
    conflicts = {k: u for k, u in by_chan.items() if len(u) > 1}
    print(f"== scale conflicts ({len(conflicts)}); the unit not declared first gets NULL")
    keep: dict[tuple, str] = {}
    for (ta, chan), units in sorted(conflicts.items()):
        declared = [(l, k[2]) for l, m in layers for k, v in m.items() if k[0] == ta and v == chan]
        keep[(ta, chan)] = declared[0][1]
        print(f"  {ta} {chan} units={sorted(units)} keep={declared[0][1]} ({declared[0][0]})")
    final = []
    for rid, ta, name, unit, chan, src, deact in out:
        if chan is not None and (ta, chan) in keep and keep[(ta, chan)] != unit:
            chan, src = None, "scale-conflict NULL"
        tally[src] += 1
        tally["id == channel_id" if chan == rid else ("id != channel_id" if chan else "NULL")] += 1
        final.append((rid, ta, name, unit, chan, src, deact.isoformat() if deact else ""))

    print("== tally")
    for k, v in sorted(tally.items()):
        print(f"{v:6d}  {k}")
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "alembic", "versions", "channel_id_backfill.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "terminal_asset_alias", "name", "unit", "channel_id", "source", "deactivated_date"])
        w.writerows(final)
    print("== wrote", path)
    print("== channel_ids with several names (renames)")
    names: dict[tuple, set[str]] = defaultdict(set)
    for rid, ta, name, unit, chan, src, _ in final:
        if chan:
            names[(ta, chan)].add(name)
    for (ta, chan), ns in sorted(names.items()):
        if len(ns) > 1:
            print(f"  {ta.split('.')[-2]} {chan[:8]} {sorted(ns)}")


main()
