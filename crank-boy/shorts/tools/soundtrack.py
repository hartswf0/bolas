#!/usr/bin/env python3
"""python3 shorts/tools/soundtrack.py <cues.json> <seconds> <out.wav>: synthesise a short's soundtrack (see sound.py)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sound
sound.render(json.load(open(sys.argv[1])), float(sys.argv[2]), sys.argv[3])
