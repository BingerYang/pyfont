# -*- coding: utf-8 -*- 
# @Time     : 2019-11-08 10:08
# @Author   : binger

from .draw_by_html import EffectFont
from .draw_by_html import FontDrawByHtml
from . import FontDraw, FontAttr
from PIL import Image, ImageDraw, ImageFont


class FontFactory(object):
    def __init__(self, effect_font, render_by_mixed=False):
        """
        :param render_by_mixed: False 只有浏览器生成，
        :param fill_type:
        """
        assert isinstance(effect_font, EffectFont)
        self.render_by_mixed = render_by_mixed
        self._effect_font = effect_font
        self.font_draw = None

    def is_effected(self):
        return any([self._effect_font.gradient_enable, self._effect_font.shadow_enable, self._effect_font.stroke_enable,
                    self._effect_font.weight != 'normal'])

    def get_line_size(self, size, text):
        if not self.font_draw:
            self.font_draw = FontDraw(self._effect_font.base)
        return self.font_draw.get_line_size(text, size=size)

    def get_max_canvas_size(self, text):
        if not self.font_draw:
            self.font_draw = FontDraw(self._effect_font.base)
        return self.font_draw.max_canvas_size(text, is_truncated=True)

    def get_size_at_limit_range(self, text, size, char_spacing_par=0.1):
        if not self.font_draw:
            self.font_draw = FontDraw(self._effect_font.base)
        return self.font_draw.get_size_at_limit_range(text, size, char_spacing_par=char_spacing_par)

    def get_text_size_at_width(self, size, text, width, spacing=4):
        effect_font = ImageFont.truetype(font=self._effect_font.base.path, size=size)
        len_text = len(text)

        line = text
        remain = ''

        temp_width = 0
        for n in range(len_text):
            temp_width += effect_font.getsize(text[n])[0]
            if temp_width > width:
                line = text[:n - 1]
                remain = text[n - 1:]
                break
            temp_width += spacing

        return line, remain

    def render_to_rng(self):
        if self.render_by_mixed and not self.is_effected():
            limit_text_cb = lambda *args, **kwargs: True
            if not self.font_draw:
                self.font_draw = FontDraw(self._effect_font.base)
            resp = self.font_draw.write(self._effect_font.text, limit_text_cb=limit_text_cb)
            img = resp.img
        else:
            img = FontDrawByHtml.render_to_image(self._effect_font)
        return img


if __name__ == '__main__':
    font = EffectFont()
    path = '../simkai.ttf'
    import os

    print(os.path.abspath(path))
    font.set_text_base(size=100, path=path)
    font.base.clear_margin = True
    # font.shadow((80, 31, 191, 0.3), sigma=8, x=0, y=6)
    # font.gradient([("#da7eeb", 0), ("#9070d8", 0.5)], angle="center", type="radial")
    # font.fill_color = "#da7eeb"
    font.fill_color = (1, 1, 1, 255)
    # font.stroke("#4e1269", 1)
    font.text = '实例\n中国\n实例'
    obj = FontFactory(font, render_by_mixed=True)
    img = obj.render_to_rng()
    print(img.size)
    img.save("11.png")
