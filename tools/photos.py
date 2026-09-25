# -*- coding: utf-8 -*-
"""
照片庫處理：讀取「照片庫」資料夾，轉成網站用的 WebP，並決定每張照片放在哪裡。

照片庫位置：與 site 資料夾同一層的「照片庫」（Balinedge.com架構/照片庫）
每個分類資料夾內的照片：
  - 檔名開頭為「封面」 → 該頁的頁首背景與卡片圖
  - 檔名開頭為「方案1」「方案2」 → 服務頁兩個方案的圖片
  - 首頁資料夾中檔名開頭為「主視覺」 → 首頁大圖
  - 其他照片 → 依檔名排序，放進該頁的「實景照片」相簿
  - 檔名（去掉開頭的編號與底線）會成為照片說明，例如「01_LoRa閘道器實機測試.jpg」
原始照片不會上傳，只有轉檔後的 WebP 會放進網站。
"""
import hashlib
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBRARY = os.environ.get("BALIN_PHOTO_LIBRARY") or os.path.join(os.path.dirname(ROOT), "照片庫")
OUT_DIR = os.path.join(ROOT, "assets", "img", "photos")
EXTS = (".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif")

# 資料夾名稱 → 網站分類代號（名稱比對時忽略空白與大小寫）
FOLDERS = {
    "首頁": "home",
    "關於我們": "about",
    "嵌入式系統": "embedded",
    "AI視覺辨識": "ai-vision",
    "LoRa無線通訊": "lora",
    "RF天線設計": "rf-antenna",
    "工業控制": "industrial",
    "客製化ODM": "odm",
}

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF = True
except ImportError:
    HEIF = False


def _norm(s):
    return re.sub(r"\s+", "", s).lower()


def _caption(stem):
    s = re.sub(r"^(封面|主視覺|方案[12])", "", stem)
    s = re.sub(r"^[\d\s._\-－]+", "", s)
    s = s.replace("_", " ").strip(" -－")
    return s


def _convert(src, key, max_side):
    from PIL import Image, ImageOps
    h = hashlib.sha1()
    with open(src, "rb") as f:
        h.update(f.read())
    h.update(str(max_side).encode())
    name = f"{key}-{h.hexdigest()[:10]}"
    out = os.path.join(OUT_DIR, name + ".webp")
    if not os.path.exists(out):
        im = Image.open(src)
        im = ImageOps.exif_transpose(im)          # 依拍攝方向轉正
        im = im.convert("RGB")                    # 同時丟掉 EXIF（含 GPS 位置）
        im.thumbnail((max_side, max_side))
        im.save(out, "WEBP", quality=80, method=6)
    return "photos/" + name


def load():
    """回傳 {分類代號: {"cover":..., "hero":..., "p1":..., "p2":..., "gallery":[(img, caption), ...]}}"""
    result = {}
    if not os.path.isdir(LIBRARY):
        return result
    os.makedirs(OUT_DIR, exist_ok=True)
    lookup = {_norm(k): v for k, v in FOLDERS.items()}
    used = set()
    for folder in sorted(os.listdir(LIBRARY)):
        path = os.path.join(LIBRARY, folder)
        if not os.path.isdir(path):
            continue
        slug = lookup.get(_norm(folder))
        if not slug:
            print(f"   [照片庫] 略過不認得的資料夾：{folder}")
            continue
        entry = {"gallery": []}
        for fn in sorted(os.listdir(path)):
            stem, ext = os.path.splitext(fn)
            if ext.lower() not in EXTS or fn.startswith("."):
                continue
            if ext.lower() in (".heic", ".heif") and not HEIF:
                print(f"   [照片庫] 無法讀取 HEIC：{folder}/{fn}（請改存成 JPG，或安裝 pillow-heif）")
                continue
            src = os.path.join(path, fn)
            idx = len(entry["gallery"]) + sum(1 for k in ("cover", "hero", "p1", "p2") if k in entry)
            try:
                if stem.startswith("封面"):
                    entry["cover"] = _convert(src, f"{slug}-cover", 1920)
                elif stem.startswith("主視覺"):
                    entry["hero"] = _convert(src, f"{slug}-hero", 1920)
                elif stem.startswith("方案1"):
                    entry["p1"] = _convert(src, f"{slug}-p1", 1200)
                elif stem.startswith("方案2"):
                    entry["p2"] = _convert(src, f"{slug}-p2", 1200)
                else:
                    entry["gallery"].append((_convert(src, f"{slug}-{idx:02d}", 1600), _caption(stem)))
            except Exception as ex:
                print(f"   [照片庫] 無法處理 {folder}/{fn}：{ex}")
                continue
        for k, v in entry.items():
            if k == "gallery":
                used.update(i for i, _ in v)
            else:
                used.add(v)
        n = len(entry["gallery"]) + sum(1 for k in ("cover", "hero", "p1", "p2") if k in entry)
        if n:
            result[slug] = entry
            print(f"   [照片庫] {folder}：{n} 張")
    # 清掉已經從照片庫移除的舊轉檔
    for fn in os.listdir(OUT_DIR):
        if fn.endswith(".webp") and "photos/" + fn[:-5] not in used:
            os.remove(os.path.join(OUT_DIR, fn))
    return result
