#!/usr/bin/env python3
"""Rebuild registry/library.js from the "library" list in registry/registry.js.
The index copies prompt text from library.js so copying works offline and on file://."""
import json, os, re
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(root, 'registry/registry.js'), encoding='utf-8').read()
data = json.loads(src[src.index('{'):src.rindex('}') + 1])
text = {}
for item in data['library']:
    with open(os.path.join(root, item['file']), encoding='utf-8') as f:
        text[item['key']] = f.read().strip()
out = 'window.CRANK_TEXT = ' + json.dumps(text, ensure_ascii=False, indent=1).replace('</', '<\\/') + ';\n'
open(os.path.join(root, 'registry/library.js'), 'w', encoding='utf-8').write(out)
print('library.js:', len(text), 'texts,', len(out), 'bytes')
