from __future__ import annotations

import math

from PIL import Image
from PIL.ImageDraw import Draw

from aeon.bindings.binding_utils import curried


@curried
def Image_mk(w, h, c):
    return Image.new("RGB", (w, h), c)


@curried
def Image_draw_rectangle(x, y, w, h, c, im):
    im2 = im.copy()
    d = Draw(im2)
    d.rectangle((x, y, x + w, y + h), c)
    return im2


@curried
def Image_diff(im1, im2):
    s = sum((a - b) ** 2 for a, b in zip(im1.histogram(), im2.histogram()))
    return math.sqrt(s)
