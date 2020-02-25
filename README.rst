pyfont
======

Documentation
-------------
生成文字图片：在一定的区域，支持换行，丢弃，缩小来完成适应区域
The documentation is hosted at https://github.com/BingerYang/pyfont


Installation
------------

.. code:: shell

     pip install pyfont

Usage
-----

example:
1. write 通过控制 limit_width, limit_count 与 传入回调返回，决定是否保留换行，或者截断丢弃

::

    # -*- coding: utf-8 -*-
    from pyfont import FontAttr, FontDraw
    from PIL import Image

    image = Image.new('RGBA', (int(400), int(400)), (1, 1, 1, 0))
    path = 'C:\Windows\Fonts\simsun.ttc'
    font = FontAttr(path=path, size=20, limit_width=220, fill_color=(1, 1, 1, 255))
    # obj = FontDraw(bg=image, font=font)
    obj = FontDraw(font=font)

    # 通过控制 limit_width，limit_count 与 传入回调返回，决定是否换行，或者丢弃
    # limit_text_cb=None 不处理（超过）
    # limit_text_cb 返回值False丢弃多余，返回True（保留换行）
    def limit_text_cb(index, line, state):
        print('index:', index, line[index:], state)
        return True


    result = obj.write(text="我们是中国人，我爱我的祖国\n你好", limit_text_cb=limit_text_cb)
    img = result.img
    print(img.size)
    img.show()
    print(font.size, font.line_height)


2. 通过 limit_width, limit_height 适当的缩小字体范围，以适应区域

::

    from pyfont import FontAttr, FontDraw
    from PIL import Image

    image = Image.new('RGBA', (int(400), int(400)), (1, 1, 1, 0))
    path = 'C:\Windows\Fonts\simsun.ttc'
    font = FontAttr(path=path, size=20, limit_width=220, fill_color=(1, 1, 1, 255))
    # obj = FontDraw(bg=image, font=font)
    obj = FontDraw(font=font)

    text="我们是中国人，我爱我的祖国\n你好"
    size = obj.get_size_at_limit_range(text, font.size)
    font.size = size
    result = obj.write(text=text)
    print(result.offset, result.lines)
    img = result.img
    print(img.size)
    img.show()


