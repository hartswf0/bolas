#!/usr/bin/env python3
"""Photograph the first screen of every version for the album: assets/cards/<id>.jpg.
Needs Playwright with Chromium (pip install playwright && playwright install chromium) and Pillow.
Run from anywhere: python3 registry/cards.py [version-id ...]"""
import asyncio, io, json, os, sys
from PIL import Image
from playwright.async_api import async_playwright
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(root, 'registry/registry.js'), encoding='utf-8').read()
reg = json.loads(src[src.index('{'):src.rindex('}') + 1])
only = set(sys.argv[1:])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for v in reg['versions']:
            if only and v['id'] not in only: continue
            pg = await b.new_page(viewport={'width': 1120, 'height': 700})
            await pg.goto('file://' + os.path.join(root, v['play']))
            await pg.wait_for_timeout(3500)
            png = await pg.screenshot()
            im = Image.open(io.BytesIO(png)).convert('RGB').resize((560, 350), Image.LANCZOS)
            out = os.path.join(root, 'assets/cards', v['id'] + '.jpg')
            im.save(out, quality=74, optimize=True)
            print(v['id'], os.path.getsize(out), 'bytes')
            await pg.close()
        await b.close()
asyncio.run(main())
