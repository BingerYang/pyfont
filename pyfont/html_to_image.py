# -*- coding: utf-8 -*- 
# @Time     : 2019-10-09 14:42
# @Author   : binger

from pyppeteer import launch
import asyncio
from PIL import Image
from io import BytesIO
import os

__advocate_loop = asyncio.new_event_loop()

executablePath = "chromium/chrome"
options = dict(handleSIGINT=False,
               handleSIGTERM=False,
               handleSIGHUP=False,
               autoClose=False,
               args=['--no-sandbox', '--disable-setuid-sandbox'])
if os.path.exists(executablePath):
    options["executablePath"] = executablePath


async def to_buffer(page_path, size, extend_offset=None, selector_element=None):
    browser = await launch(options)
    page = await browser.newPage()
    try:
        await page.setViewport(viewport={"width": size[0], "height": size[1]})
        # await page.setJavaScriptEnabled(enabled=False)
        await page.goto(page_path)
        # await page.screenshot({'path': _OUTFILE, 'fullPage': True, 'omitBackground': "transparency"})
        element = selector_element and await page.querySelector(selector_element)

        if element:
            box = await element.boundingBox()
            if extend_offset:
                box["width"] += extend_offset[0]
                box["height"] += extend_offset[1]
            buffer = await element.screenshot(
                {'type': 'png', 'omitBackground': "transparency", "clip": box})
            # {'type': 'png', 'fullPage': True, 'omitBackground': "transparency", "clip": box})
        else:
            buffer = await page.screenshot({'type': 'png', 'fullPage': True, 'omitBackground': "transparency"})
    finally:
        await page.close()
    return buffer


async def to_image(page_path, size, extend_offset=None, selector_element=None):
    buffer = await to_buffer(page_path, size, extend_offset, selector_element)
    image = Image.open(BytesIO(buffer))
    return image


import threading


def mutex_self_lock(cls):
    def decorator(*args, **kwargs):
        if decorator.mutex.acquire():
            result = None
            try:
                result = cls(*args, **kwargs)
            except:
                pass
            finally:
                decorator.mutex.release()
                return result

    decorator.mutex = threading.Lock()
    return decorator


# @mutex_self_lock
def html2image(page_path, size, extend_offset=None, selector_element=None):
    asyncio.set_event_loop(__advocate_loop)
    return __advocate_loop.run_until_complete(to_image(page_path, size, extend_offset, selector_element))
