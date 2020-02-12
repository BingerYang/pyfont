# -*- coding: utf-8 -*-
# @Time     : 2019-12-04 16:21
# @Author   : binger

from PIL import Image, ImageDraw, ImageFont
from operator import itemgetter
import math


# import attr


class FontAttr(object):

    def __init__(self, size, path, line_height=None, line_spacing_par=0.1, char_spacing=None, char_spacing_par=0.1,
                 variable_spacing=True, limit_height=None, limit_width=None, align="left", line_sep='\n',
                 fill_color=None):
        self.path = path
        self._size = size
        self.variable_spacing = variable_spacing
        self.char_spacing_par = char_spacing_par
        self.line_spacing_par = line_spacing_par
        self.line_height = line_height or int(size * (1 + self.line_spacing_par))
        self.char_spacing = char_spacing or int(size * self.char_spacing_par)
        self.align = align
        self.line_sep = line_sep
        self.limit_width = limit_width
        self.limit_height = limit_height
        self.fill_color = fill_color
        self._font = None

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size):
        self._size = size
        if self.variable_spacing:
            self.line_height = int(self.size * (1 + self.line_spacing_par))
            self.char_spacing = int(self.size * self.char_spacing_par)

    @property
    def font(self):
        if not self._font:
            self._font = ImageFont.truetype(self.path, size=self.size)
        return self._font

    def reset_font(self):
        self._font = ImageFont.truetype(self.path, size=self.size)


class FontDraw(object):
    def __init__(self, bg, font):
        self._font = font
        self._bg = bg
        self._draw = ImageDraw.Draw(bg)

    def get_char_size(self, text, path, size):
        """
        获得一个字的宽和高
        :param text:
        :param size:
        :return: (width, height)
        """
        return ImageFont.truetype(font=path, size=size).getsize(text)

    def get_line_size(self, line, size=None):

        font_obj = ImageFont.truetype(font=self._font.path, size=size or self._font.size)
        x_list = []
        y_list = []
        for i, c in enumerate(line):
            _size = font_obj.getsize(c)
            x_list.append(_size[0])
            y_list.append(_size[1])
        x = sum(x_list) + (len(line) - 1) * self._font.char_spacing
        y = max(y_list) if y_list else 0
        return x, y

    def write_line(self, line, position=None, align="left", progress=None):
        res = ""  # 作为判断时候换行使用
        x, y = position = position or (0, 0)
        h_list = []
        align = 1 if align == "left" else -1
        for i, c in enumerate(line):
            if i != 0:
                x += self._font.char_spacing * align
            c_w, c_h = self.get_char_size(text=c, path=self._font.path, size=self._font.size)

            if progress and x + c_w * align > self._font.limit_width:
                res = progress(i, line) or ''
                break

            self._draw.text(xy=(x, y), text=c, font=self._font.font, fill=self._font.fill_color)
            x += c_w * align
            h_list.append(c_h)

        return (x - position[0], max(h_list) if h_list else 0), res

    def write(self, text, position=None, align='left', progress=None):
        """
        有宽度限制输入文字，达到限制，换行或者丢失
        """
        self._font.reset_font()
        x, y = position = position or (0, 0)

        lines = text.strip().split(self._font.line_sep)

        line_width = []
        n = 0
        for line in lines:
            while line:
                if len(line.strip()) == 0:
                    continue

                offset, line = self.write_line(line, position=(x, y + 1), align=align, progress=progress)
                # 不加,会出现字体不自然
                line_width.append(offset[0])
                if n == 0:
                    y += offset[1]
                else:
                    y += self._font.line_height
                n += 1

        return max(line_width) if line_width else 0, y - position[1]

    def write_by_change_size(self, text, position=None, align='left', progress=None):
        lines = text.strip().split(self._font.line_sep)
        if not lines:
            return

        handle = lambda i, line: [i, *self.get_line_size(line, self._font.size)]
        size_iter = list(map(lambda msg: handle(*msg), enumerate(lines)))
        w_max = max(size_iter, key=itemgetter(1))
        h_max = max(size_iter, key=itemgetter(2))
        h_max_size = int(h_max[2])
        h_max_index = h_max[0]
        w_max_size = int(h_max[1])
        w_max_index = w_max[0]

        new_size = None
        n = len(lines)
        if self._font.limit_height:
            is_first = True
            while True:
                if n == 1 and h_max_size > self._font.limit_height:
                    if is_first:
                        new_size = self._font.limit_height
                else:

                    # limit_size = math.ceil(
                    #     (self._font.limit_height - (n - 1) * self._font.line_height) / n)

                    limit_size = math.ceil(
                        self._font.limit_height / (n + (n - 1) * self._font.line_spacing_par)
                    )
                    if h_max_size > limit_size:
                        if is_first:
                            new_size = limit_size
                    else:
                        break
                new_size -= 1
                h_max_size = self.get_line_size(lines[h_max_index], new_size)[1]
        if new_size:
            self._font.size = new_size
            w_max_size = self.get_line_size(lines[w_max_index], new_size)[0]

        if self._font.limit_width:
            line = lines[w_max_index]
            if w_max_size > self._font.limit_width:
                new_size = math.ceil(self._font.limit_width * self._font.size / w_max_size)
                while True:
                    if self.get_line_size(line, size=new_size)[0] < self._font.limit_width:
                        self._font.size = new_size
                        break
                    else:
                        new_size -= 1
        return self.write(text, position=position, align=align, progress=progress)

    def crop(self, offset, start=None):
        start = start or (0, 0)
        return self._bg.crop((start[0], start[1], start[0] + offset[0] + 1, start[1] + offset[1] + 1))


class FontImage(object):
    def __init__(self, bg, font, size, fill=None):
        """
        :param bg:
        :param font: 字体库路径
        :param size: 字体大小
        :param fill:
        """
        self._bg = bg
        self._draw = ImageDraw.Draw(bg)
        self._font = ImageFont.truetype(font=font, size=size)
        self._fill_color = fill and tuple(fill)
        self._font_family_path = font

    def get_char_size(self, text, size):
        """
        获得一个字的宽和高
        :param text:
        :param size:
        :return: (width, height)
        """
        if size:
            _font = ImageFont.truetype(font=self._font_family_path, size=size)
        else:
            _font = self._font
        return _font.getsize(text)

    def write(self, text, line_height, char_spacing, position=None, size=None, align="left", line_sep="\n"):
        """

        :param text: 输入的文本
        :param line_height: 行高
        :param char_spacing: 字符间距
        :param position: 输入的文字
        :param size: 文字大小
        :param align: 对齐方向
        :param line_sep: 分隔符
        :return:
        """
        x, y = position = position or (0, 0)

        lines = text.strip().split(line_sep)
        line_width = []
        for i, line in enumerate(lines):
            if len(line.strip()) == 0:
                continue

            if i != 0:
                y += line_height
            offset = self.write_line(line, spacing=char_spacing, position=(x, y + 1), size=size, align=align)
            line_width.append(offset[0])
            y += offset[1]
        return max(line_width) if line_width else 0, y - position[1]

    def write_line(self, line, spacing=5, position=None, size=None, align="left"):
        x, y = position = position or (0, 0)
        h_list = []
        align = 1 if align == "left" else -1
        for i, c in enumerate(line):
            if i != 0:
                x += spacing * align
            c_w, c_h = self.get_char_size(text=c, size=size)
            self._draw.text(xy=(x, y), text=c, font=self._font, fill=self._fill_color)
            x += c_w * align
            h_list.append(c_h)

        return x - position[0], max(h_list)

    def crop(self, offset, start=None):
        start = start or (0, 0)

        return self._bg.crop((start[0], start[1], start[0] + offset[0] + 1, start[1] + offset[1] + 1))
