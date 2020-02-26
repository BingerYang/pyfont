# -*- coding: utf-8 -*- 
# @Time     : 2019-11-01 10:02
# @Author   : binger

from .html_to_image import html2image
from jinja2 import Template
from . import FontAttr, FontDraw
import os


class Color(object):
    def __init__(self, color):
        """
        支持：数组形式的 rgba 与 rgb 表示，和 "#000000" 表示
        :param color:
        """
        self.color = color

    def __str__(self):
        if isinstance(self.color, (tuple, list)):
            if len(self.color) == 3:
                return "rgb{}".format(repr(tuple(self.color)))
            else:
                return "rgba{}".format(repr(tuple(self.color)))
        elif isinstance(self.color, Color):
            obj = self.color
            self.color = obj.color
            return obj.__str__()
        else:
            return self.color


class EffectFont(object):
    def __init__(self):
        self.base = None
        self.shadow_extend_offset = None

        self.stroke_enable = False  # 描边功能渲染使用启用
        self.stroke_width = 1  # 描边画笔的宽
        self.stroke_color = None  # 描边颜色

        self.shadow_enable = False  # 阴影功能开启
        self.shadow_x = self.shadow_y = 0  # 阴影的偏移量
        self.shadow_sigma = 0.0  # 阴影的模糊度
        self.shadow_color = ""  # 阴影的颜色

        self.gradient_enable = False  # 渐变功能是否启动
        self._fill_color = ""  # 字体前景色填充色
        self.fill_type = "color"

        self.text_content = None  # 文字内容（换行时是 <br/>）
        self.text_shadow = None  # 阴影时文字内容（换行时<A>）
        self._text = None
        self.limit_width = None  # 达到宽度自动换行
        self.is_auto_wrap = False  # 是否开启自动宽度限制换行
        self.weight = 'normal'

    def set_text_base(self, size, path, line_height=None, line_spacing_par=0.1, char_spacing=None, char_spacing_par=0.1,
                      variable_spacing=True, limit_height=None, limit_width=None, limit_count=None, align="left",
                      limit_line=None, line_sep='\n', fill_color=None, weight="normal"):

        _vars = vars().copy()
        _vars.pop("self")
        weight = _vars.pop('weight')
        _vars["path"] = os.path.abspath(_vars["path"])
        self.base = FontAttr(**_vars)
        self.weight = weight
        return True

    def shadow(self, color, sigma=0.0, x=0, y=0):
        self.shadow_enable = True
        self.shadow_x = x
        self.shadow_y = y
        self.shadow_sigma = sigma
        self.shadow_color = color
        self.shadow_extend_offset = (x, y)
        return True

    def gradient(self, color_pos_list, angle, type="linear"):
        """

        :param color_pos_list: [("#da7eeb", 0), ("#9070d8", 0.99)]
        :param type:  "linear" or "radial"
        :param angle:  角度90或者偏移量 1px, 2px 或者 center
        :return:
        """
        if type == "linear":
            angle = "{angle}deg".format(angle=angle)
        else:

            angle = "{}px, {}px".format(*angle[:2]) if isinstance(angle, (
                tuple, list)) else angle
            angle = "circle farthest-corner at {}".format(angle)
        color_change = ", ".join(["{} {}%".format(resp[0], 100 * resp[1]) for resp in color_pos_list])
        content = """{type}-gradient({angle} , {color_change});
        """.format(
            type=type, angle=angle, color_change=color_change
        )
        self._fill_color = content
        self.gradient_enable = True
        return True

    @property
    def fill_color(self):
        return self._fill_color

    @fill_color.setter
    def fill_color(self, color):
        assert isinstance(color, tuple)
        self.base.fill_color = color
        self._fill_color = Color(color)
        self.gradient_enable = False
        return True

    def stroke(self, color, width):
        self.stroke_enable = True
        self.stroke_width = width
        self.stroke_color = color
        return True

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
        txt_list = self._text.split("\n")
        self.text_content = "<br/>".join(txt_list)
        self.text_shadow = "\A".join(txt_list)


class FontDrawByHtml(object):
    def __init__(self):
        self._html = None
        self._request_size = None
        self._extend_offset = None  # 阴影引起的区域多偏移
        self.selector_element = "a"

        self._tpl = Template(self.init_template())

    @property
    def html(self):
        return self._html

    @classmethod
    def init_template(cls):
        return """
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
</head>
<style>
    body {
        margin: 0;
        position: relative;
    }

    @font-face {
        font-family: custom_font;
        src: url("{{ font.base.path }}");
    }

    #text {
        position: absolute;
        left: 0;
        top: 0;
        font-size: {{ font.base.size }}px;
        /**
            字号
        */
        line-height: {{font.base.line_height}}px;
        letter-spacing: {{font.base.char_spacing}}px;
        text-align: {{font.base.align}};
        font-family: custom_font;
        /**
            字体
        */
        font-weight: {{ font.weight }};
        /**
            当没有渐变时 不用background-image,把颜色填在 -webkit-text-fill-color:;
            当有渐变时 设置 -webkit-text-fill-color:transparent;
        */
        {%- if font.gradient_enable -%}
            -webkit-text-fill-color: transparent;

            /*-webkit-text-fill-color: #7b759a;*/
            /**
                不用渐变时的颜色
            */
            background-image: {{ font.fill_color}};
            /**
                radial-gradient：中心渐变（线性渐变会给另一个background-image）
                circle: 渐变形状为圆形（和设计师确认过不会换）;
                farthest-corner: 以离中心点最远的角的距离为 100% （和设计师确认过不会换）;
                center: 渐变中心 可以替换为偏移量 1px 1px（x轴偏移量 y轴偏移量） （和设计师讨论过可能支持设置9个点）;
                #da7eeb 0%: 颜色和百分比  在 0%（中心点） 位置的颜色为 #da7eeb;
                #9070d8 99%： 颜色和百分比 在 99%（中心点距离最远角的百分之99的地方） 位置的颜色为 #9070d8;
                颜色和百分比可以添加多对；
            */
            /*background-image: linear-gradient(0deg , #bd8749 0%, #efdfac 69%);*/
            /**
                linear-gradient: 线性渐变;
                90deg: 渐变角度;
                #f6d365 0%: 颜色和百分比 可以多对
            */
        {%- else -%}
            -webkit-text-fill-color: {{font.fill_color}};
        {%- endif -%}

        {%- if font.stroke_enable -%}
            -webkit-text-stroke: {{font.stroke_width}}px {{font.stroke_color}};
            /**
                内描边Ï
                1px: 描边1像素宽;
                #4e1269: 描边的颜色;
            */
        {%- endif -%}
        -webkit-background-clip: text;
        position: absolute;
        left: 0;
        top: 0;
        {%- if font.base.limit_width -%}
            limit_width: {{ font.base.limit_width }}px;
            word-break: bread-all;
        {%- endif -%}
        white-space: pre-wrap;
    }
    {%- if font.shadow_enable -%}
    #text::before {

        text-shadow: {{font.shadow_x}}px {{font.shadow_y}}px {{font.shadow_sigma}}px {{font.shadow_color}};
        /**
            阴影
            0px:x轴偏移量;
            10px: y轴偏移量;
            12px: 模糊;
            rgba(80, 31, 191, 0.3): rgba(前三个数值表示颜色,透明度);
        */
        color: transparent;
        display: inline;
        content: "{{ font.text_shadow }}";
        position: absolute;
        left: 0;
        top: 0;
        line-height: {{font.base.line_height}}px;
        letter-spacing: {{font.base.char_spacing}}px;
        text-align: {{font.base.align}};
        z-index: -1;
        {%- if font.base.limit_width -%}
            limit_width: {{ font.base.limit_width }}px;
            word-break: bread-all;
        {%- endif -%}
        white-space: pre-wrap;
    }
    {%- endif -%}
</style>
<body>
<a id="text">{{ font.text_content }}</a>
</body>
</html> 
        """

    def save(self, filename):
        if self._html:
            with open(filename, "w") as fw:
                fw.write(self._html)

    def to_image(self):
        from tempfile import NamedTemporaryFile

        with NamedTemporaryFile(mode="w", suffix=".html") as fw:
            fw.write(self._html)
            fw.seek(0)
            img = html2image("file://{}".format(fw.name), size=self._request_size,
                             extend_offset=self._extend_offset,
                             selector_element=self.selector_element)
            return img

    def build(self, font):
        assert isinstance(font, EffectFont)
        msg = self._html = self._tpl.render(font=font)

        if font.shadow_enable:
            self._extend_offset = font.shadow_extend_offset
        return msg

    @classmethod
    def render_to_image(cls, font, request_area_size=(800, 800)):
        obj = cls()
        obj._request_size = request_area_size
        obj.build(font)

        return obj.to_image()
