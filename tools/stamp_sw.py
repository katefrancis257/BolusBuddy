"""Stamp sw.js with a cache name made from the app's files.

    python3 tools/stamp_sw.py

Run it after changing any app file or rebuilding the food data, so phones fetch the new copy.
tools/datacheck.py fails while the stamp is out of date.
"""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SW = ROOT / "sw.js"
PATTERN = re.compile(r'var CACHE = "bolusbuddy-([0-9a-f]+)";')


def files():
    names = re.search(r"var SHELL = \[(.*?)\];", SW.read_text(encoding="utf-8")).group(1)
    return [n for n in re.findall(r'"([^"]+)"', names) if n != "./"]


def stamp():
    h = hashlib.sha256()
    for name in files():
        h.update(name.encode() + b"\0" + (ROOT / name).read_bytes())
    return h.hexdigest()[:10]


def is_current():
    m = PATTERN.search(SW.read_text(encoding="utf-8"))
    return bool(m) and m.group(1) == stamp()


def main():
    text = SW.read_text(encoding="utf-8")
    new = PATTERN.sub('var CACHE = "bolusbuddy-' + stamp() + '";', text, count=1)
    SW.write_text(new, encoding="utf-8")
    print("sw.js cache:", PATTERN.search(new).group(0))


if __name__ == "__main__":
    main()
