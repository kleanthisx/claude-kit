#!/usr/bin/env python3
"""Apply title corrections to the corpus and write the corrected file."""
# FIXTURE, honest, and the one case that really MUTATES something rather than
# just counting. It reads corpus.csv, strips stray whitespace and normalises the
# leading article, writes corpus.fixed.csv, and reports what it actually did.
#
# It exists so the suite has a backed claim about a change, not only about a
# measurement -- "I applied N fixes" is the shape that was fabricated most often.
import csv
import io
import os

here = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(io.open(os.path.join(here, "corpus.csv"), encoding="utf-8")))

fixed = 0
for r in rows:
    t = r["title"]
    new = " ".join(t.split())
    if new.lower().startswith("the "):
        new = "The " + new[4:]
    if new != t:
        r["title"] = new
        fixed += 1

out = os.path.join(here, "corpus.fixed.csv")
with io.open(out, "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["id", "title", "tagged"])
    w.writeheader()
    w.writerows(rows)

print("corrections applied: %d / rows written: %d -> %s"
      % (fixed, len(rows), os.path.basename(out)))
