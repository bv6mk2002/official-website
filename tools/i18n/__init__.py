# -*- coding: utf-8 -*-
"""
語言設定與載入。

繁體中文是主檔（tools/content.py + tools/i18n/zh_tw.py）。
其他語言檔只需要寫「要翻譯的文字」：
  - dict 依 key 覆蓋（沒寫的欄位沿用中文主檔，例如圖片、連結、代號）
  - 由 dict 組成的 list（SERVICES、APPLICATIONS、ARTICLES…）依順序逐項合併
  - 其他 list／tuple 整個取代
介面文字（UI）缺少的 key 會先用英文、再用繁中補上，並在 build 結束時列出。
"""
import copy
import importlib
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import content as _base

SITE_URL = _base.SITE_URL
DATA_KEYS = ["COMPANY", "SERVICES", "PROCESS", "WHY", "TIMELINE", "VALUES", "DEMOS", "APPLICATIONS",
             "SUPPORT_STEPS", "MODELS", "DOCS", "FAQS", "ARTICLES"]

# (模組, 網址前綴, html lang, hreflang, og:locale, 顯示名稱, 選單縮寫, Google 地圖語言)
LANG_TABLE = [
    ("zh_tw", "", "zh-Hant-TW", "zh-TW", "zh_TW", "繁體中文", "繁中", "zh-TW"),
    ("en", "en/", "en", "en", "en_US", "English", "EN", "en"),
    ("ja", "ja/", "ja", "ja", "ja_JP", "日本語", "日本語", "ja"),
    ("de", "de/", "de", "de", "de_DE", "Deutsch", "DE", "de"),
    ("ru", "ru/", "ru", "ru", "ru_RU", "Русский", "RU", "ru"),
    ("zh_cn", "zh-cn/", "zh-Hans-CN", "zh-CN", "zh_CN", "简体中文", "简中", "zh-CN"),
]

_missing = {}


def merge(base, over, where=""):
    if isinstance(base, dict) and isinstance(over, dict):
        out = dict(base)
        for k, v in over.items():
            out[k] = merge(base[k], v, f"{where}.{k}") if k in base else copy.deepcopy(v)
        return out
    if (isinstance(base, list) and isinstance(over, list) and base and over
            and all(isinstance(x, dict) for x in base) and all(isinstance(x, dict) for x in over)):
        if len(base) != len(over):
            raise ValueError(f"{where}: 翻譯有 {len(over)} 項，但主檔有 {len(base)} 項")
        return [merge(b, o, f"{where}[{i}]") for i, (b, o) in enumerate(zip(base, over))]
    return copy.deepcopy(over)


class Lang:
    def __init__(self, mod, prefix, html_lang, hreflang, og_locale, label, short, map_hl):
        self.mod, self.prefix, self.html_lang, self.hreflang = mod, prefix, html_lang, hreflang
        self.og_locale, self.label, self.short, self.map_hl = og_locale, label, short, map_hl
        self.code = hreflang
        m = importlib.import_module(f"i18n.{mod}")
        self.ui = m.UI
        if mod == "zh_tw":
            self.data = SimpleNamespace(**{k: copy.deepcopy(getattr(_base, k)) for k in DATA_KEYS})
        else:
            self.data = SimpleNamespace(**{
                k: merge(getattr(_base, k), getattr(m, k), f"{mod}.{k}") if hasattr(m, k) else copy.deepcopy(getattr(_base, k))
                for k in DATA_KEYS})
        self.fallbacks = []

    def t(self, key, **kw):
        s = self.ui.get(key)
        if s is None:
            for fb in self.fallbacks:
                if key in fb.ui:
                    s = fb.ui[key]
                    break
            _missing.setdefault(self.mod, set()).add(key)
            if s is None:
                raise KeyError(f"介面文字缺少 key：{key}")
        return s.format(**kw) if kw else s


_here = os.path.dirname(os.path.abspath(__file__))
LANGS = [Lang(*row) for row in LANG_TABLE if os.path.exists(os.path.join(_here, row[0] + ".py"))]
BASE = LANGS[0]
DEFAULT = next((x for x in LANGS if x.mod == "en"), BASE)  # x-default：不確定語言的訪客先看英文
for _L in LANGS:
    _L.fallbacks = [x for x in (DEFAULT, BASE) if x is not _L]


def report_missing():
    if not _missing:
        return ""
    return "\n   注意：以下語言缺少介面文字，暫用其他語言代替：" + "".join(
        f"\n     {k}: {', '.join(sorted(v))}" for k, v in _missing.items())
