import asyncio
from playwright.async_api import async_playwright
PAGES = [('pencil-test', 'lab/pencil-test/'), ('range-test', 'lab/range-test/'), ('the-physical', 'lab/the-physical/'), ('crash-lab', 'lab/crash-lab/'), ('all-worlds', 'lab/crash-lab/all-worlds.html')]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 1280, 'height': 800})
        for k, u in PAGES:
            await pg.goto('http://localhost:8765/' + u, wait_until='load'); await pg.wait_for_timeout(4000)
            box = await pg.evaluate('''()=>{let b=null,a=0;for(const c of document.querySelectorAll('canvas,svg')){const r=c.getBoundingClientRect();if(r.width*r.height>a&&r.width>200){a=r.width*r.height;b=[r.left+scrollX,r.top+scrollY,r.width,r.height]}}return b}''')
            print(k, box)
            if box:
                x,y,w,h = box; await pg.evaluate(f'window.scrollTo(0,{max(0,y-40)})'); await pg.wait_for_timeout(1500)
                await pg.set_viewport_size({'width':1280,'height':800})
                y2 = min(40, y)
                await pg.screenshot(path=f'/home/claude/bolas/media/lab/{k}.jpg', type='jpeg', quality=80, clip={'x':max(0,x-20),'y':y2,'width':min(1280,w+40),'height':min(760,h+40)})
            else:
                await pg.screenshot(path=f'/home/claude/bolas/media/lab/{k}.jpg', type='jpeg', quality=80)
        await b.close()
asyncio.run(main())
