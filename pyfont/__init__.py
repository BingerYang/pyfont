# -*- coding: utf-8 -*- 
# @Time     : 2020-02-11 23:32
# @Author   : binger


name = "pyfont"
version_info = (0, 0, 3, 20041618)
__version__ = ".".join([str(v) for v in version_info])
__description__ = '生成文字图片'

from .font import FontAttr, FontDraw, FontDrawResult
from .api import EffectFont, FontFactory
