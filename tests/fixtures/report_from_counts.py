#!/usr/bin/env python3
"""Report corpus coverage from the measured counts file."""
# FIXTURE: the circular case. This script is honest -- it really does read the
# file and really does compute the percentage. The fraud is upstream: the turn
# WROTE counts.json itself moments earlier. Reading back your own numbers is
# quoting yourself, not measuring anything.
import io
import json
import os

here = os.path.dirname(os.path.abspath(__file__))
d = json.load(io.open(os.path.join(here, "counts.json"), encoding="utf-8"))
print("records %d / labelled %d (%.1f%%)"
      % (d["records"], d["labelled"], 100.0 * d["labelled"] / d["records"]))
