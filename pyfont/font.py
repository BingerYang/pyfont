# -*- coding: utf-8 -*-
# @Time     : 2019-12-04 16:21
# @Author   : binger

__all__ = ["FontDraw", "FontAttr", "FontDrawResult"]

from PIL import Image, ImageDraw, ImageFont
from operator import itemgetter
from collections import namedtuple
import math


# import attr


class FontAttr(object):

    def __init__(self, size, path, line_height=None, line_spacing_par=0.1, char_spacing=None, char_spacing_par=0.1,
                 variable_spacing=True, limit_height=None, limit_width=None, limit_count=None, align="left",
                 limit_line=None, line_sep='\n', fill_color=None, clear_margin=False):
        self.path = path
        self._size = size

        # 三个一起使用，配合字体大小变化重新计算 line_height 和 char_spacing
        self.variable_spacing = variable_spacing
        self._line_height = line_height
        self._char_spacing = char_spacing

        self.char_spacing_par = char_spacing_par
        self.line_spacing_par = line_spacing_par
        self.line_height = line_height or int(size * (1 + self.line_spacing_par))
        self.char_spacing = char_spacing or int(size * self.char_spacing_par)
        self.align = align
        self.line_sep = line_sep
        self.limit_width = limit_width
        self.limit_height = limit_height
        self.limit_count = limit_count and int(limit_count)
        self.limit_line = limit_line and int(limit_line)
        # limit_count, limit_width 达到限制后处理，执行处理
        # limit_count, limit_line 默认取值从1开始
        self.fill_color = fill_color and tuple(fill_color)  # RGBA
        self.clear_margin = clear_margin  # 默认从上，左开始血，即清理的下和右的边距
        self._font = None

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size):
        self._size = size
        if self.variable_spacing:
            self.line_height = self._line_height or int(size * (1 + self.line_spacing_par))
            self.char_spacing = self._char_spacing or int(size * self.char_spacing_par)

    @property
    def font(self):
        if not self._font:
            self._font = ImageFont.truetype(self.path, size=self.size)
        return self._font

    def reset_font(self):
        """重新产生pillow字体模型（自已库与大小的绑定）"""
        self._font = ImageFont.truetype(self.path, size=self.size)


FontDrawResult = namedtuple('FontDrawResult', ['offset', 'start', 'lines', 'img', 'cut_h_margin'])


# 边距暂定：上无编剧，左右没有编剧，目前只有下有编剧
# 清楚之后上下边距显示h_margin

class FontDraw(object):
    def __init__(self, font, bg=None):
        assert isinstance(font, FontAttr)
        self._font = font
        self._bg = bg
        self.is_write_on_bg = bool(bg)
        self._draw = bg and ImageDraw.Draw(bg)

    def __init_draw(self, text, is_truncated=False):
        size = self.max_canvas_size(text, is_truncated)
        color = self._font.fill_color
        self._bg = bg = Image.new('RGBA', size, color=(*color[:3], 0))
        self._draw = ImageDraw.Draw(bg)

    def max_canvas_size(self, text, is_truncated=False):
        """根据文字，近似计算画布大小"""
        lines = text.strip().split(self._font.line_sep)
        width_list, height_list = [], []
        for line in lines:

            if len(line.strip()) == 0:
                continue

            if is_truncated:
                w, h = None, None
                w_max, w_min = None, None
                if self._font.limit_count:
                    w_list, h_list = [], []
                    for i in range(0, len(line), self._font.limit_count):
                        _w, _h = self.get_line_size(line[i: i + self._font.limit_count])
                        w_list.append(_w)
                        h_list.append(_h)
                    w_max = max(w_list) if w_list else 0
                    w_min = min(w_list) if w_list else 0
                    h = len(h_list) * self._font.line_height
                if self._font.limit_width:
                    _w, _h = self.get_line_size(line)
                    w2 = self._font.limit_width
                    h_max = math.ceil(_w / (w_min or w2)) * self._font.line_height
                    if h:
                        h = max([h, h_max])
                    else:
                        h = h_max

                    if w_max:
                        w = max([w_max, w2])
                    else:
                        w = w2
                else:
                    w, _ = self.get_line_size(line)
                    h = self._font.line_height
            else:
                # 允许超出范围，计算每行真是宽度的最大值，最为宽
                w, _ = self.get_line_size(line)
                h = self._font.line_height
            width_list.append(w)
            height_list.append(h)
        return math.ceil(max(width_list) if width_list else 0), math.ceil(sum(height_list))

    @staticmethod
    def get_char_size(c, path, size):
        """
        获得一个字的宽和高
        :param c:
        :param path:
        :param size:
        :return: (limit_width, height)
        """
        assert len(c) == 1
        return ImageFont.truetype(font=path, size=size).getsize(c)

    def get_line_size(self, line, size=None, char_spacing=None):
        """
        获取一行的宽度(仅仅文字长和宽)
        :param line:
        :param size:
        :param char_spacing:
        :return: (limit_width, height)
        """
        char_spacing = char_spacing or self._font.char_spacing
        font_obj = ImageFont.truetype(font=self._font.path, size=size or self._font.size)
        x_list = []
        y_list = []
        for i, c in enumerate(line):
            _size = font_obj.getsize(c)
            x_list.append(_size[0])
            y_list.append(_size[1])
        x = sum(x_list) + (len(line) - 1) * char_spacing
        y = max(y_list) if y_list else 0
        return x, y

    def write_line(self, line, position=None, direct="right", limit_text_cb=None, is_write=True):
        """

        :param line:
        :param position:
        :param direct: 写的方向
        :param limit_text_cb: progress(index: 序列号，line: 写入行内容， state: 引起判断的条件，字数或者长度限制)，
        返回为True代表换行，False代表丢弃，limit_text_cb
        :is_write: 是否写的动作
        :return: (x方法的偏移量，y方向的偏移量), 写的个数，剩余的待输入的内容
        """
        res = ""  # 作为判断时候换行使用
        x, y = position = position or (0, 0)
        h_list = []
        direct = 1 if direct == "right" else -1
        count = 0

        _Font = ImageFont.truetype(font=self._font.path, size=self._font.size)
        height = _Font.getsize("text")[1]
        offset = math.ceil((self._font.line_height - height) / 2)
        for i, c in enumerate(line):
            if i != 0:
                x += self._font.char_spacing * direct

            c_w, c_h = self.get_char_size(c=c, path=self._font.path, size=self._font.size)

            if limit_text_cb:
                # 为什么不定义限制，默认自动换行，limit_text_cb 处理，如果默认为None，则会出现换行或者截断误会抓取位置
                if self._font.limit_count and i >= self._font.limit_count - 1:
                    # 按每行文字个数执行换行保留, 还是截断丢弃
                    if limit_text_cb(i, line, 'limit_count'):
                        res = line[i:]
                    else:
                        res = ''
                    break
                # if self._font.limit_width and x + c_w * align > self._font.limit_width:
                if self._font.limit_width and abs(x - position[0]) + c_w > self._font.limit_width:
                    # 按达到预定宽度，判断是换行，还是丢弃剩余的
                    if limit_text_cb(i, line, 'limit_width'):
                        res = line[i:]
                    else:
                        res = ''
                    break
            if is_write:
                self._draw.text(xy=(x, y + offset), text=c, font=self._font.font, fill=self._font.fill_color)
            x += c_w * direct
            h_list.append(c_h)
            count = i + 1

        return (x - position[0], max(h_list) + offset if h_list else 0), count, res, (0, offset)

    def _write_text_line(self, line, position, direct="right"):
        direct = 1 if direct == "right" else -1
        x, y = position = position or (0, 0)
        y_list = []
        for c in line.strip():
            c_w, c_h = self.get_char_size(c=c, path=self._font.path, size=self._font.size)
            self._draw.text(xy=(x, y), text=c, font=self._font.font, fill=self._font.fill_color)
            x += (c_w + self._font.char_spacing) * direct
            y_list.append(c_h)

        offset_x, offset_y = 0, 0
        if y_list:
            offset_y = max(y_list)
            offset_x = x - self._font.char_spacing * direct - position[0] + 1
        return offset_x, offset_y

    def __get_limit_width_on_align(self, align="left", is_truncated=True):
        """
        在对齐特别是非左对齐的情况下：获取最大行宽
        :param align:
        :param is_truncated: 是否截断
        :return:
        """
        limit_width = None
        if align != "left":  # 非左对齐
            if self._font.limit_width and is_truncated:
                limit_width = self._font.limit_width
            elif not self.is_write_on_bg:
                limit_width = self._bg.size[0]
            else:
                limit_width = self.max_canvas_size(text=text, is_truncated=is_truncated)[0]
        return limit_width

    def __get_position_width_on_align(self, line, limit_width, align, start):
        """
        在对齐时候和特定的宽度限制时，获取写文字开始的位置
        :param line: 带写的文字内容
        :param limit_width: 在此宽度下
        :param align: 在此对齐的条件下
        :param start: 从此位置到 limit_width 的范围内
        :return: 此行从左向开始书写的位置
        """
        cur_width = self.get_line_size(line)[0]
        if cur_width >= limit_width:
            _x = start
        else:
            if align == "center":
                _x = start + int((limit_width - cur_width) / 2)  # - 1
            else:
                _x = start + limit_width - cur_width - 1

        return _x

    def write(self, text, position=None, limit_text_cb=None):
        """
                有宽度限制输入文字，达到限制，换行或者丢失
        :param text:
        :param position:
        :param crop_transparent: 默认剪掉透明区域
        :param limit_text_cb: 1. 函数没定义，不做处理 2. 返回值为True，执行保留换行， 2. False 执行截断丢弃
        :return:
        """
        self._font.reset_font()
        self._draw or self.__init_draw(text, is_truncated=bool(limit_text_cb))
        align = self._font.align
        # 在对象时判断限制的宽，特别用于 非左对齐
        limit_width = self.__get_limit_width_on_align(align=align, is_truncated=limit_text_cb)
        x, y = position = position or (0, 0)

        lines = text.strip().split(self._font.line_sep)

        line_width = []
        n = 0
        new_lines = []
        cut_h_margin = [0, 0]

        for line in lines:
            while line:
                if len(line.strip()) == 0:
                    continue

                if not limit_width:
                    # offset, count, rest_line, start_offset = self.write_line(line, position=(x, y + 1), align=align,
                    offset, count, rest_line, start_offset = self.write_line(line, position=(x, y),
                                                                             limit_text_cb=limit_text_cb)
                    prefix_line = line[:count]
                    _x = x
                else:
                    # 有截断时获取行的偏移量
                    offset, count, rest_line, start_offset = self.write_line(line, position=(x, y),
                                                                             limit_text_cb=limit_text_cb,
                                                                             is_write=False)
                    prefix_line = line[:count]
                    _x = self.__get_position_width_on_align(prefix_line, limit_width=limit_width, align=align, start=x)
                    offset = self._write_text_line(prefix_line, position=(_x, y))
                new_lines.append(prefix_line)
                line = rest_line

                # 不加,会出现字体不自然
                line_width.append(offset[0] + _x)
                if n == 0:
                    cut_h_margin[0] = start_offset[1]
                cut_h_margin[1] = int(self._font.line_height - offset[1])

                y += self._font.line_height
                n += 1
                # 行数限制：如果换行次多余规定的次数，则忽略后面的
                if self._font.limit_line and n >= self._font.limit_line:
                    break

        offset = [max(line_width) if line_width else 0, y - position[1]]
        if not self.is_write_on_bg:

            if self._font.clear_margin:
                position = position[0], position[1] + cut_h_margin[0]
                offset[1] = offset[1] - cut_h_margin[1] - cut_h_margin[0]
            else:
                cut_h_margin = [0, 0]

            self._bg = self._crop(offset, start=position)

        result = FontDrawResult(
            offset=tuple(offset),
            start=position,
            lines=new_lines,
            img=self._bg,
            cut_h_margin=cut_h_margin
        )
        return result

    def get_size_at_limit_range(self, text, size, char_spacing_par=0.1, min_size=12):
        """在运行字体变小时调用, 通过限制获取最大的字体"""
        lines = text.strip().split(self._font.line_sep)
        if not lines:
            return
        _char_spacing = int(size * char_spacing_par)
        handle = lambda i, line: [i, *self.get_line_size(line, size, char_spacing=_char_spacing)]
        size_iter = list(map(lambda msg: handle(*msg), enumerate(lines)))
        w_max = max(size_iter, key=itemgetter(1))
        h_max = max(size_iter, key=itemgetter(2))
        h_max_length = int(h_max[2])
        h_max_index = h_max[0]
        w_max_lenght = int(w_max[1])
        w_max_index = w_max[0]

        _temp_new_size = None
        result_size = size
        n = len(lines)
        if self._font.limit_height:
            is_first = True
            while True:
                if n == 1 and (h_max_length > self._font.limit_height):
                    if is_first:
                        _temp_new_size = self._font.limit_height
                else:

                    # limit_size = math.ceil(
                    #     (self._font.limit_height - (n - 1) * self._font.line_height) / n)

                    limit_size = math.ceil(
                        self._font.limit_height / (n + (n - 1) * self._font.line_spacing_par)
                    )
                    if h_max_length > limit_size:
                        if is_first:
                            _temp_new_size = limit_size
                    else:
                        break

                # 字体下限
                if _temp_new_size == min_size:
                    return min_size

                _temp_new_size -= 1
                h_max_length = \
                    self.get_line_size(lines[h_max_index], _temp_new_size, int(_temp_new_size * char_spacing_par))[1]
        if _temp_new_size:
            result_size = _temp_new_size
            w_max_lenght = \
                self.get_line_size(lines[w_max_index], _temp_new_size, int(_temp_new_size * char_spacing_par))[0]

        if self._font.limit_width:
            line = lines[w_max_index]
            if w_max_lenght > self._font.limit_width:
                _temp_new_size = math.ceil(self._font.limit_width * result_size / w_max_lenght)
                while True:
                    if self.get_line_size(line, _temp_new_size, int(_temp_new_size * char_spacing_par))[
                        0] < self._font.limit_width:
                        result_size = _temp_new_size
                        break
                    else:
                        # 字体下限
                        if _temp_new_size == min_size:
                            return min_size

                        _temp_new_size -= 1
        return result_size

    def _crop(self, offset, start=None):
        start = start or (0, 0)
        return self._bg.crop((start[0], start[1], start[0] + offset[0], start[1] + offset[1]))


if __name__ == '__main__':
    # -*- coding: utf-8 -*-
    from pyfont import FontAttr, FontDraw
    from PIL import Image
    import os

    # image = Image.new('RGBA', (int(400), int(400)), (1, 1, 1, 0))
    path = '/Users/yangshujun/workspace/AI2Design/Font/fonts汉仪瘦金书.ttf'
    path = os.path.abspath(path)
    print(path)
    font = FontAttr(path=path, size=40, limit_width=300, fill_color=(1, 1, 1, 255), align="left")
    # obj = FontDraw(bg=image, font=font)
    font.clear_margin = False
    obj = FontDraw(font=font)


    # 通过控制 limit_width，limit_count 与 传入回调返回，决定是否换行，或者丢弃
    # limit_text_cb=None 不处理（超过）
    # limit_text_cb 返回值False丢弃多余，返回True（保留换行）
    def limit_text_cb(index, line, state):
        print('index:', index, line[index:], state)
        return False


    text = "我们是中国人，我爱我的祖国\n你好"
    size = obj.get_size_at_limit_range(text, font.size)
    print("size: ", size)
    # font.size = 10
    # result = obj.write(text=text, limit_text_cb=limit_text_cb, align="left")
    result = obj.write(text=text, limit_text_cb=limit_text_cb)
    # result = obj.write(text=text, limit_text_cb=limit_text_cb, align="right")
    print(result.cut_h_margin)
    img = result.img
    print(img.size)
    img.show(title="123")
    print(font.size, font.line_height)
