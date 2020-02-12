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
1. write 通过控制 limit_width 与 传入回调返回，决定是否换行，或者丢弃

::


    # -*- coding: utf-8 -*-
    from pyfont import FontAttr, FontDraw
    from PIL import Image

    image = Image.new('RGBA', (int(400), int(400)), (255, 255, 255, 0))
    font = FontAttr(size=20, limit_width=220)
    obj = FontDraw(bg=image, font=font)

    # 通过控制 limit_width 与 传入回调返回，决定是否换行，或者丢弃
    # progress=None 超过不处理
    # progress 返回值有空，丢弃多余，返回多余的 line[index:]（换行处理）
    def progress(index, line):
        print('index:', index, line[index:])
        # return line[index:]
        pass


    offset = obj.write(text="我们是中国人，我爱我的祖国\n你好", progress=progress)
    img = obj.crop(offset)
    print(img.size)
    img.show()
    print(font.size, font.line_height)


2. write_by_change_size 通过 limit_width, limit_height 适当的缩小字体范围，以适应区域

::

    from pyfont import FontAttr, FontDraw
    from PIL import Image

    image = Image.new('RGBA', (int(400), int(400)), (255, 255, 255, 0))
    font = FontAttr(size=20, limit_width=220)
    obj = FontDraw(bg=image, font=font)

    offset = obj.write_by_change_size(text="我们是中国人，我爱我的祖国\n你好")
    img = obj.crop(offset)
    img.show()
