"""Checks on the generated food data, run by the build scripts and by CI.

    python3 tools/datacheck.py          # checks foods.js, restaurants.js and sw.js

Problems stop a build. Warnings are printed for a person to review.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MAX_PER100 = 100      # label basis: nothing is more than 100 g carbs per 100 g
MAX_PORTION = 1000    # g or ml in one preset portion
MAX_SERVING = 500     # g carbs in one restaurant item
# Groups where a zero figure is unusual enough to need a person to look at it.
STARCHY = {"Bread", "Cereal", "Rice & pasta", "Potatoes", "Cakes & biscuits"}


def slug(s):
    """Same as BolusCore.slug in core.js."""
    s = "".join(c for c in unicodedata.normalize("NFD", str(s)) if not 0x300 <= ord(c) <= 0x36F).lower()
    return re.sub(r"[^a-z0-9]+", "-", s.replace("&", " and ")).strip("-")


def curated_id(name, code):
    return "f" + code if code else "k-" + slug(name)


def chain_id(chain, item):
    return "r-" + slug(chain) + "--" + slug(item)


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def check_foods(data, warn=None):
    problems = []
    groups = data.get("groups") or []
    names, ids, codes = set(), set(), set()
    for i, f in enumerate(data.get("curated", [])):
        where = f"curated {i} ({f[0] if f else '?'})"
        if len(f) not in (6, 7):
            problems.append(f"{where}: expected 6 or 7 fields, found {len(f)}")
            continue
        name, group, per100, unit, portions, code = f[:6]
        if not name or name in names:
            problems.append(f"{where}: name is empty or repeated")
        names.add(name)
        fid = curated_id(name, code)
        if fid in ids:
            problems.append(f"{where}: ID {fid} is repeated")
        ids.add(fid)
        if code:
            codes.add(code)
        if group not in groups:
            problems.append(f"{where}: group {group!r} is not in the group list")
        if not is_num(per100) or not 0 <= per100 <= MAX_PER100:
            problems.append(f"{where}: carbs per 100 {per100!r} is outside 0 to {MAX_PER100}")
        if unit not in ("g", "ml"):
            problems.append(f"{where}: unit {unit!r} is not g or ml")
        for p in portions:
            if len(p) != 2 or not p[0] or not is_num(p[1]) or not 0 < p[1] <= MAX_PORTION:
                problems.append(f"{where}: portion {p!r} needs a name and a weight from 1 to {MAX_PORTION}")
    seen = set()
    for f in data.get("cofid", []):
        code, name, gi, per100, flags = f
        where = f"CoFID {code}"
        if code in seen:
            problems.append(f"{where}: code is repeated")
        seen.add(code)
        if not name:
            problems.append(f"{where}: name is empty")
        if not isinstance(gi, int) or not 0 <= gi < len(groups):
            problems.append(f"{where}: group index {gi!r} is out of range")
        elif warn is not None and per100 == 0 and groups[gi] in STARCHY:
            warn.append(f"{where} {name}: 0 g carbs in {groups[gi]}")
        if not is_num(per100) or not 0 <= per100 <= MAX_PER100:
            problems.append(f"{where}: carbs per 100 {per100!r} is outside 0 to {MAX_PER100}")
    return problems


def check_chains(chains):
    problems = []
    seen_chains, ids = set(), set()
    for c in chains:
        chain = c.get("chain")
        if not chain or chain in seen_chains:
            problems.append(f"chain {chain!r}: name is empty or repeated")
        seen_chains.add(chain)
        for k in ("source", "url", "date"):
            if not c.get(k):
                problems.append(f"{chain}: {k} is missing")
        for section, name, carbs in c.get("items", []):
            where = f"{chain} · {name}"
            if not section or not name:
                problems.append(f"{where}: section or name is empty")
            rid = chain_id(chain, name)
            if rid in ids:
                problems.append(f"{where}: ID {rid} is repeated")
            ids.add(rid)
            if not is_num(carbs) or not 0 <= carbs <= MAX_SERVING:
                problems.append(f"{where}: carbs {carbs!r} is outside 0 to {MAX_SERVING}")
    return problems


def load_js(path, var):
    text = Path(path).read_text(encoding="utf-8")
    m = re.search(r"window\." + var + r" = (.*);\s*$", text, re.S)
    if not m:
        raise ValueError(f"{path}: window.{var} not found")
    return json.loads(m.group(1))


def main():
    import stamp_sw  # noqa: E402  (same folder)

    warn = []
    problems = check_foods(load_js(ROOT / "foods.js", "BOLUS_FOODS"), warn)
    problems += check_chains(load_js(ROOT / "restaurants.js", "BOLUS_CHAINS"))
    if not stamp_sw.is_current():
        problems.append("sw.js: cache name is out of date. Run python3 tools/stamp_sw.py")
    for w in warn:
        print("review:", w)
    for p in problems:
        print("problem:", p)
    print(f"{len(problems)} problems, {len(warn)} to review")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
