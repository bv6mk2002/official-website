# -*- coding: utf-8 -*-
"""
從繁體中文主檔自動產生簡體中文語言檔 tools/i18n/zh_cn.py。
修改繁體中文內容後執行：
    python tools/make_zh_cn.py
    python tools/build.py
需要：pip install opencc-python-reimplemented
"""
import os
import pprint
import sys

from opencc import OpenCC

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import content
from i18n import DATA_KEYS
from i18n.zh_tw import UI

cc = OpenCC("tw2sp")  # 繁體（台灣）→ 簡體（中國大陸用詞）

# OpenCC 沒處理到的兩岸用詞差異（轉換後再替換）
TERMS = [
    ("视觉辨识", "视觉识别"), ("影像辨识", "图像识别"), ("文字辨识", "文字识别"), ("牌面辨识", "牌面识别"),
    ("辨识", "识别"), ("影像", "图像"), ("场域", "场景"), ("客制化", "定制"), ("客制", "定制"),
    ("技术支援", "技术支持"), ("支援", "支持"), ("品质", "质量"), ("缺省", "默认"),
    ("电子信箱", "电子邮箱"), ("信箱", "邮箱"), ("联络", "联系"), ("线上", "在线"), ("回覆", "回复"),
    ("讯息", "信息"), ("演算法", "算法"), ("资料库", "数据库"), ("晶片", "芯片"), ("类比", "模拟"),
    ("数位", "数字"), ("行动装置", "移动设备"), ("范本", "模板"),
    ("资本额", "注册资本"), ("组织种类", "企业类型"), ("统一编号", "统一编号（台湾）"),
    ("感测", "传感"), ("侦测", "检测"), ("瑕疵", "缺陷"), ("即时", "实时"), ("推论", "推理"),
    ("「", "“"), ("」", "”"),
]
# 這些字串不轉換（網址參數、程式用的代碼等）
KEEP = {"email", "tax_id", "phone_intl", "form_endpoint", "form_key"}


def conv(s):
    s = cc.convert(s)
    for a, b in TERMS:
        s = s.replace(a, b)
    return s


def walk(x, key=""):
    if isinstance(x, str):
        return x if key in KEEP else conv(x)
    if isinstance(x, dict):
        return {k: walk(v, k) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        out = [walk(v, key) for v in x]
        return tuple(out) if isinstance(x, tuple) else out
    return x


def main():
    ui = walk(UI)
    company = walk(content.COMPANY)
    company.update({
        "address": "台湾台南市永康区永大路3段618巷12号1楼",
        "phone_display": "+886-932-830814",
        "hours": "周一至周五 09:00–18:00（GMT+8）",
    })
    data = {k: walk(getattr(content, k)) for k in DATA_KEYS}
    data["COMPANY"] = company
    lines = ['# -*- coding: utf-8 -*-',
             '"""简体中文。此文件由 tools/make_zh_cn.py 从繁体中文自动生成，请勿直接修改。"""', ""]
    lines.append("UI = " + pprint.pformat(ui, width=120, sort_dicts=False))
    for k, v in data.items():
        lines.append("")
        lines.append(f"{k} = " + pprint.pformat(v, width=120, sort_dicts=False))
    out = os.path.join(HERE, "i18n", "zh_cn.py")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("已產生", out)


if __name__ == "__main__":
    main()
