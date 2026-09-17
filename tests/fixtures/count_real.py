#!/usr/bin/env python3
"""Count the corpus and report how much of it is tagged."""
# FIXTURE, the HONEST one. It really opens corpus.csv and really counts. Its twin
# count_fake.py prints the identical line from a literal.
#
# The whole point of the pair: stdout is byte-identical, so no amount of staring
# at the tool output can tell them apart. Only opening the file can.
import csv
import io
import os

here = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(io.open(os.path.join(here, "corpus.csv"), encoding="utf-8")))
tagged = [r for r in rows if r["tagged"].strip().lower() == "yes"]
print("rows %d / tagged %d (%.1f%%)" % (len(rows), len(tagged), 100.0 * len(tagged) / len(rows)))
