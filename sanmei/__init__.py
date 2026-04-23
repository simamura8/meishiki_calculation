"""
算命学 命式計算パッケージ (sanmei)

使用例:
    from sanmei.meishiki import calc_meishiki
    result = calc_meishiki("1996-10-12 12:00", "m")
"""

from .meishiki import calc_meishiki

__all__ = ["calc_meishiki"]
