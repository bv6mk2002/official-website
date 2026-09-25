# -*- coding: utf-8 -*-
"""
八麟光電科技官網 — 靜態網站產生器
用法（在 site 資料夾執行）：python tools/build.py
內容請改 tools/content.py；樣式在 assets/css/style.css。
"""
import html
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
from content import (APPLICATIONS, ARTICLES, COMPANY as C, DEMOS, DOCS, FAQS, MODELS, PROCESS,
                     SERVICES, SITE_URL, SUPPORT_STEPS, TIMELINE, VALUES, WHY)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = date.today().isoformat()
SVC = {s["slug"]: s for s in SERVICES}
CREDITS = json.load(open(os.path.join(ROOT, "tools", "credits.json"), encoding="utf-8"))
PAGES = []  # 給 sitemap 用
e = html.escape

# ---------------------------------------------------------------------------
# 圖示
# ---------------------------------------------------------------------------
ICON_PATHS = {
    "chip": '<rect x="7" y="7" width="10" height="10" rx="1.5"/><path d="M9 2v5M15 2v5M9 17v5M15 17v5M2 9h5M2 15h5M17 9h5M17 15h5"/>',
    "eye": '<path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z"/><circle cx="12" cy="12" r="2.8"/>',
    "signal": '<path d="M5 19v-3M10 19v-7M15 19v-11M20 19V4"/>',
    "antenna": '<circle cx="12" cy="6" r="2"/><path d="M12 8v13M7.5 11a6.5 6.5 0 0 1 9 0M4.6 8.2a10.5 10.5 0 0 1 14.8 0"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.3 5.3l2.1 2.1M16.6 16.6l2.1 2.1M5.3 18.7l2.1-2.1M16.6 7.4l2.1-2.1"/>',
    "box": '<path d="M4 8l8-4 8 4-8 4-8-4z"/><path d="M4 8v8l8 4 8-4V8M12 12v8"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.8 2.8L16.5 9"/>',
    "phone": '<path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2z"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "map": '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "doc": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.5a3.5 3.5 0 0 1 0 7M18 14.5a6.5 6.5 0 0 1 3.5 5.5"/>',
    "tool": '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>',
    "factory": '<path d="M3 21V10l5 3V10l5 3V6l8 4v11z"/><path d="M7 17h2M12 17h2M17 17h2"/>',
    "external": '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
}


def icon(name, size=22):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICON_PATHS[name]}</svg>')


IMG_SIZES = {}


def img_size(name):
    if name not in IMG_SIZES:
        try:
            from PIL import Image
            IMG_SIZES[name] = Image.open(os.path.join(ROOT, "assets", "img", name + ".webp")).size
        except Exception:
            IMG_SIZES[name] = (900, 600)
    return IMG_SIZES[name]


def img(R, name, alt, lazy=True, cls=""):
    w, h = img_size(name)
    load = ' loading="lazy" decoding="async"' if lazy else ' fetchpriority="high"'
    klass = f' class="{cls}"' if cls else ""
    return f'<img src="{R}assets/img/{name}.webp" alt="{e(alt)}" width="{w}" height="{h}"{load}{klass}>'


def tags(items):
    return '<ul class="tags">' + "".join(f"<li>{e(t)}</li>" for t in items) + "</ul>"


# ---------------------------------------------------------------------------
# 版型
# ---------------------------------------------------------------------------
NAV = [
    ("about", "about.html", "關於我們"),
    ("services", None, "產品與服務"),
    ("applications", "applications.html", "應用場域"),
    ("demos", "demos.html", "即時展示"),
    ("insights", "insights/", "技術專欄"),
    ("support", "support.html", "技術支援"),
]


def header(R, active):
    items = []
    for key, href, label in NAV:
        if key == "services":
            menu = "".join(
                f'<a href="{R}services/{s["slug"]}.html">{icon(s["icon"], 20)}<span><b>{e(s["name"])}</b><small>{e(s["summary"])}</small></span></a>'
                for s in SERVICES)
            cls = "dd active" if active == key else "dd"
            items.append(f'<div class="{cls}"><button type="button" aria-expanded="false">產品與服務</button>'
                         f'<div class="dd-menu">{menu}<a class="all" href="{R}services/">查看全部產品與服務 →</a></div></div>')
        else:
            cur = ' aria-current="page"' if active == key else ""
            items.append(f'<a href="{R}{href}"{cur}>{label}</a>')
    return f'''<a class="skip" href="#main">跳到主要內容</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{R}index.html" aria-label="{C["name"]} 首頁">
      <img src="{R}assets/img/logo.svg" alt="" width="42" height="42">
      <span class="brand-name"><b>{C["short"]}科技</b><small>{C["en_short"]}</small></span>
    </a>
    <button class="menu-toggle" type="button" aria-label="開啟選單" aria-expanded="false"><span></span></button>
    <nav class="nav" aria-label="主選單">
      {"".join(items)}
      <a class="lang" href="{R}en/" lang="en">EN</a>
      <a class="btn btn-primary btn-sm" href="{R}contact.html"{' aria-current="page"' if active == "contact" else ""}>聯絡我們</a>
    </nav>
  </div>
</header>'''


def footer(R):
    svc = "".join(f'<li><a href="{R}services/{s["slug"]}.html">{e(s["name"])}</a></li>' for s in SERVICES)
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div class="foot-grid">
      <div class="foot-brand">
        <a class="brand" href="{R}index.html"><img src="{R}assets/img/logo.svg" alt="" width="42" height="42" loading="lazy">
          <span class="brand-name"><b>{C["name"]}</b><small>{C["en_short"]}</small></span></a>
        <p>{C["tagline"]} — 嵌入式系統、AI 視覺辨識、LoRa／RF 無線通訊與工業控制整合，從概念到量產一條龍完成。</p>
      </div>
      <div><h4>產品與服務</h4><ul>{svc}</ul></div>
      <div><h4>快速連結</h4><ul>
        <li><a href="{R}about.html">關於我們</a></li>
        <li><a href="{R}applications.html">應用場域</a></li>
        <li><a href="{R}demos.html">即時展示</a></li>
        <li><a href="{R}insights/">技術專欄</a></li>
        <li><a href="{R}support.html">技術支援</a></li>
        <li><a href="{R}contact.html">聯絡我們</a></li>
      </ul></div>
      <div><h4>聯絡方式</h4><ul>
        <li>{C["address"]}</li>
        <li>電話：<a href="tel:{C["phone_intl"]}">{C["phone"]}</a></li>
        <li>信箱：<a href="mailto:{C["email"]}">{C["email"]}</a></li>
        <li>{C["hours"]}</li>
      </ul></div>
    </div>
    <div class="foot-bottom">
      <span>© {date.today().year} {C["name"]} {C["en"]}　統一編號 {C["tax_id"]}</span>
      <span><a href="{R}credits.html">圖片來源與授權</a></span>
    </div>
  </div>
</footer>'''


def cta_band(R, title="準備好開始您的專案了嗎？", text="歡迎與我們的技術團隊聊聊您的需求，免費取得從概念到量產的方案建議。"):
    return f'''<section class="cta-wrap"><div class="wrap"><div class="cta-box reveal">
  <div><h2>{title}</h2><p>{text}</p></div>
  <div class="actions"><a class="btn btn-primary" href="{R}contact.html">免費諮詢</a>
  <a class="btn btn-ghost" href="tel:{C["phone_intl"]}">{icon("phone", 18)} {C["phone"]}</a></div>
</div></div></section>'''


def page_hero(R, title, text, crumbs, bg=None, eyebrow=None):
    def crumb(t, h):
        return f'<a href="{R}{h}">{e(t)}</a>' if h else e(t)
    trail = f'<a href="{R}index.html">首頁</a>' + "".join(f"<span>/</span>{crumb(t, h)}" for t, h in crumbs)
    style = (f' style="background-image:linear-gradient(100deg,rgba(6,20,35,.95) 35%,rgba(6,20,35,.62)),'
             f'url({R}assets/img/{bg}.webp)"') if bg else ""
    eb = f'<span class="eyebrow">{e(eyebrow)}</span>' if eyebrow else ""
    return f'''<section class="page-hero"{style}><div class="wrap">
  <nav class="crumbs" aria-label="麵包屑">{trail}</nav>
  {eb}<h1>{title}</h1><p>{text}</p>
</div></section>'''


def breadcrumb_ld(path, crumbs):
    items = [{"@type": "ListItem", "position": 1, "name": "首頁", "item": SITE_URL + "/"}]
    for i, (t, h) in enumerate(crumbs, 2):
        items.append({"@type": "ListItem", "position": i, "name": t, "item": SITE_URL + "/" + (h or path)})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


ORG_LD = {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "@id": SITE_URL + "/#org",
    "name": C["name"],
    "alternateName": C["en"],
    "url": SITE_URL + "/",
    "logo": SITE_URL + "/assets/img/logo.svg",
    "image": SITE_URL + "/assets/img/og.png",
    "description": "AIoT 智慧產品設計中心，專注嵌入式系統、AI 視覺辨識、LoRa／RF 無線通訊與工業控制整合，提供從概念到量產的 OEM／ODM 服務。",
    "telephone": C["phone_intl"],
    "email": C["email"],
    "taxID": C["tax_id"],
    "foundingDate": "2009-05",
    "address": {"@type": "PostalAddress", "streetAddress": "永大路3段618巷12號1樓", "addressLocality": "永康區",
                "addressRegion": "臺南市", "addressCountry": "TW"},
    "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
                                   "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                                   "opens": "09:00", "closes": "18:00"}],
    "areaServed": "TW",
    "knowsAbout": ["嵌入式系統", "AI 視覺辨識", "LoRa", "RF 天線設計", "工業控制", "OEM/ODM", "STM32", "ESP32"],
}


def render(path, *, title, desc, body, active=None, lang="zh-Hant-TW", ld=None, og_img="og.png",
           og_type="website", extra_head="", priority="0.7", in_sitemap=True):
    depth = path.count("/")
    R = "../" * depth
    canonical = SITE_URL + "/" + (path[:-10] if path.endswith("index.html") else path)
    full_title = title if C["short"] in title else f"{title}｜{C['name']}"
    lds = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    doc = f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{C["name"]}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE_URL}/assets/img/{og_img}">
<meta property="og:locale" content="{"en_US" if lang == "en" else "zh_TW"}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#061423">
<link rel="icon" href="{R}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{R}assets/img/apple-touch-icon.png">
<link rel="alternate" hreflang="zh-Hant-TW" href="{SITE_URL}/">
<link rel="alternate" hreflang="en" href="{SITE_URL}/en/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&display=swap">
<link rel="stylesheet" href="{R}assets/css/style.css?v={TODAY.replace("-", "")}">
{extra_head}{lds}
</head>
<body>
{header(R, active) if lang != "en" else header_en(R)}
<main id="main">
{body}
</main>
{footer(R) if lang != "en" else footer_en(R)}
<script src="{R}assets/js/main.js?v={TODAY.replace("-", "")}" defer></script>
</body>
</html>
'''
    doc = doc.replace("{R}", R)
    out = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(doc)
    if in_sitemap:
        PAGES.append((canonical, priority))
    print("  ", path)


def svc_card(R, s):
    return f'''<a class="card reveal" href="{R}services/{s["slug"]}.html">
  <div class="media">{img(R, s["card"], s["name"])}</div>
  <span class="icon-badge">{icon(s["icon"])}</span>
  <div class="body"><span class="card-en">{e(s["en"])}</span><h3>{e(s["name"])}</h3>
  <p>{e(s["summary"])}</p>{tags(s["tags"][:5])}<span class="more arrow">了解更多 </span></div>
</a>'''


def article_card(R, a, prefix):
    return f'''<a class="card reveal" href="{prefix}{a["slug"]}.html">
  <div class="media">{img(R, a["img"], a["title"])}</div>
  <div class="body"><div class="post-meta"><span class="pill">{e(a["tag"])}</span><time datetime="{a["date"]}">{a["date"].replace("-", ".")}</time></div>
  <h3>{e(a["title"])}</h3><p>{e(a["excerpt"])}</p><span class="more arrow">閱讀全文 </span></div>
</a>'''


def demo_card(R, d):
    return f'''<a class="card demo-card reveal" href="{R}{d["href"]}" target="_blank" rel="noopener">
  <div class="media">{img(R, d["img"], d["title"] + " 畫面")}</div>
  <div class="body"><span class="live"><span class="pulse"></span>LIVE DEMO</span><h3>{e(d["title"])}</h3>
  <p>{e(d["desc"])}</p>{tags(d["tags"])}<span class="more">開啟展示 ↗</span></div>
</a>'''


# ---------------------------------------------------------------------------
# 頁面
# ---------------------------------------------------------------------------
def build_home():
    R = ""
    years = date.today().year - C["founded_year"]
    process = "".join(f'<li><b>{zh}</b><small>{en.upper()}</small><p>{d}</p></li>' for en, zh, d in PROCESS)
    body = f'''
<section class="hero">
  <div class="wrap">
    <div>
      <span class="eyebrow">{C["tagline"]} · SINCE {C["founded_year"]}</span>
      <h1>從構想到量產，<br><em>打造可靠的智慧硬體</em></h1>
      <p class="lead">嵌入式系統、AI 視覺辨識、LoRa／RF 無線通訊與工業控制整合 —— 台南在地研發團隊，硬體、韌體、AI 到量產一條龍完成。</p>
      <div class="cta">
        <a class="btn btn-primary" href="contact.html">免費諮詢專案</a>
        <a class="btn btn-ghost" href="#capabilities">探索核心能力</a>
      </div>
      <ul class="chips"><li>STM32／ESP32</li><li>YOLO／OCR</li><li>LoRaWAN</li><li>PCB 天線</li><li>Modbus／MQTT</li><li>OEM／ODM</li></ul>
    </div>
    <div class="hero-visual">
      <div class="photo">{img(R, "hero", "電路板上的微控制器晶片特寫", lazy=False)}</div>
      <div class="hero-card"><span class="pulse"></span><span><b>{years}+ 年</b>嵌入式研發經驗</span></div>
    </div>
  </div>
</section>

<section class="stats" aria-label="公司概況"><div class="wrap"><ul>
  <li><b>{C["founded_year"]}</b><span>年成立，台南在地研發</span></li>
  <li><b>{years}<small>年+</small></b><span>嵌入式系統開發經驗</span></li>
  <li><b>6<small>大</small></b><span>核心技術領域整合</span></li>
  <li><b>7<small>階段</small></b><span>概念到量產一條龍</span></li>
</ul></div></section>

<section id="capabilities"><div class="wrap">
  <div class="sec-head split"><div><span class="eyebrow">Core Capabilities</span><h2>六大核心能力</h2>
  <p>橫跨硬體、韌體、AI 與無線通訊，一個團隊整合所有關鍵技術，減少多方協調的時間與風險。</p></div>
  <a class="btn btn-line" href="services/">查看全部服務 →</a></div>
  <div class="grid g3">{"".join(svc_card(R, s) for s in SERVICES)}</div>
</div></section>

<section class="dark"><div class="wrap">
  <div class="sec-head center"><span class="eyebrow">R&amp;D Process</span><h2>從概念到量產，一條龍完成</h2>
  <p>客戶要的不只是產品，而是完整實現構想的能力。每個階段都有明確的交付項目與驗證標準。</p></div>
  <ol class="process">{process}</ol>
</div></section>

<section><div class="wrap split">
  <div class="photo reveal">{img(R, "about-solder", "工程師在電路板上焊接表面黏著元件")}</div>
  <div class="reveal">
    <span class="eyebrow">Why Balin</span><h2>為什麼選擇八麟光電</h2>
    <p class="lead-lg">我們不只是電子設計公司，而是客戶的「智慧產品研發部門」。從第一次討論開始，就由實際動手的工程師與您溝通。</p>
    <ul class="checks two">{"".join(f"<li>{e(w)}</li>" for w in WHY)}</ul>
    <a class="btn btn-primary" href="about.html">認識我們</a>
  </div>
</div></section>

<section class="soft"><div class="wrap">
  <div class="sec-head split"><div><span class="eyebrow">Applications</span><h2>應用場域</h2>
  <p>從工廠設備監測到農場環境感測，我們把技術整合成解決現場問題的方案。</p></div>
  <a class="btn btn-line" href="applications.html">查看全部應用 →</a></div>
  <div class="grid g3">{"".join(f"""<a class="card reveal" href="applications.html#{a["id"]}"><div class="media">{img(R, a["img"], a["title"])}</div>
  <div class="body"><h3>{e(a["title"])}</h3><p>{e(a["challenge"])}</p><span class="more arrow">看解決方案 </span></div></a>""" for a in APPLICATIONS[:3])}</div>
</div></section>

<section class="dark"><div class="wrap">
  <div class="sec-head split"><div><span class="eyebrow">Tech Showcase</span><h2>AIoT 即時監測展示</h2>
  <p>實際操作我們開發的監控儀表板，體驗設備資料即時上雲後的樣子。</p></div>
  <a class="btn btn-ghost" href="demos.html">展示說明 →</a></div>
  <div class="grid g3">{"".join(demo_card(R, d) for d in DEMOS)}</div>
</div></section>

<section><div class="wrap">
  <div class="sec-head split"><div><span class="eyebrow">Insights</span><h2>技術專欄</h2>
  <p>分享我們在嵌入式、無線通訊與 AI 專案中累積的實務經驗。</p></div>
  <a class="btn btn-line" href="insights/">全部文章 →</a></div>
  <div class="grid g3">{"".join(article_card(R, a, "insights/") for a in ARTICLES[:3])}</div>
</div></section>

{cta_band(R)}
<script>
// 舊版網址（#about、#products…）自動導向新頁面
(function(){{var m={{about:"about.html",products:"services/",support:"support.html",news:"insights/",contact:"contact.html"}};var h=location.hash.slice(1);if(m[h])location.replace(m[h]);}})();
</script>'''
    render("index.html", title=f"{C['name']}｜AIoT、嵌入式系統、LoRa 無線通訊、AI 視覺辨識",
           desc="八麟光電科技 — 台南 AIoT 智慧產品設計中心，專注嵌入式系統（STM32／ESP32）、AI 視覺辨識、LoRa／RF 無線通訊與工業控制整合，提供從概念到量產的一站式 OEM／ODM 服務。",
           body=body, active="home", ld=[ORG_LD, {"@context": "https://schema.org", "@type": "WebSite", "name": C["name"], "url": SITE_URL + "/"}],
           priority="1.0")


def build_about():
    R = ""
    crumbs = [("關於我們", None)]
    rows = [("公司名稱", C["name"]), ("英文名稱", C["en"]), ("統一編號", C["tax_id"]), ("負責人", C["owner"]),
            ("設立日期", C["founded"]), ("組織種類", C["type"]), ("資本額", C["capital"]), ("公司地址", C["address"])]
    body = f'''{page_hero(R, "關於八麟光電", "AIoT 智慧產品設計中心 —— 從概念、硬體、韌體、AI 到量產，一條龍完成。", crumbs, bg="about-lab", eyebrow="About Us")}
<section><div class="wrap split">
  <div class="reveal">
    <span class="eyebrow">Company Profile</span><h2>公司簡介</h2>
    <p class="lead-lg">八麟光電科技有限公司成立於 {C["founded_year"]} 年，位於臺南市永康區，深耕嵌入式系統、AI 視覺辨識、LoRa／RF 無線通訊與工業控制整合技術。</p>
    <p>我們不只是電子設計公司，而是客戶眼中的「AIoT 智慧產品設計中心」——從概念發想、硬體設計、韌體開發、AI 演算法整合，到原型打樣、認證測試與量產交付，提供一條龍的完整支援。</p>
    <p>憑藉跨領域整合能力，我們協助客戶將創新構想快速實現為可量產的智慧產品，服務領域涵蓋工業自動化、智慧監控、智慧農業與物聯網應用。</p>
  </div>
  <div class="photo reveal">{img(R, "about-lab", "電子實驗室中的工程師與量測儀器")}</div>
</div></section>

<section class="soft"><div class="wrap">
  <div class="sec-head center"><span class="eyebrow">Core Values</span><h2>核心價值</h2></div>
  <div class="grid g3">{"".join(f'<div class="card reveal"><div class="body"><span class="icon-badge" style="position:static">{icon(ic)}</span><h3>{t}</h3><p>{d}</p></div></div>' for ic, t, d in VALUES)}</div>
</div></section>

<section><div class="wrap split">
  <div class="reveal"><span class="eyebrow">Milestones</span><h2>發展歷程</h2>
    <ol class="timeline">{"".join(f"<li><b>{y}</b><p>{e(t)}</p></li>" for y, t in TIMELINE)}</ol>
  </div>
  <div class="reveal"><span class="eyebrow">Company Info</span><h2>公司資料</h2>
    <table class="info">{"".join(f"<tr><th>{k}</th><td>{e(v)}</td></tr>" for k, v in rows)}</table>
  </div>
</div></section>

<section class="dark"><div class="wrap split">
  <div class="photo reveal">{img(R, "support", "開發中的電路板與測試設備")}</div>
  <div class="reveal"><span class="eyebrow">What We Do</span><h2>我們的技術領域</h2>
    <p>一個團隊涵蓋智慧產品開發的所有關鍵環節：</p>
    <ul class="checks">{"".join(f'<li><a href="services/{s["slug"]}.html" style="color:#fff">{e(s["name"])}</a>　<span style="color:#9DB1C8">{e(s["summary"])}</span></li>' for s in SERVICES)}</ul>
  </div>
</div></section>
{cta_band(R)}'''
    render("about.html", title="關於我們", desc=f"八麟光電科技成立於 {C['founded_year']} 年，位於臺南市永康區，深耕嵌入式系統、AI 視覺辨識、LoRa／RF 無線通訊與工業控制整合，是客戶的 AIoT 智慧產品設計中心。",
           body=body, active="about", ld=[breadcrumb_ld("about.html", crumbs)], priority="0.8")


def build_services():
    R = "../"
    crumbs = [("產品與服務", None)]
    body = f'''{page_hero(R, "產品與服務", "六大核心能力，涵蓋嵌入式系統、AI 視覺、LoRa／RF 通訊、工業控制與 ODM 量產的完整解決方案。", crumbs, bg="hero2", eyebrow="Products & Services")}
<section><div class="wrap"><div class="grid g3">{"".join(svc_card(R, s) for s in SERVICES)}</div></div></section>
<section class="dark"><div class="wrap">
  <div class="sec-head center"><span class="eyebrow">R&amp;D Process</span><h2>一條龍開發流程</h2></div>
  <ol class="process">{"".join(f'<li><b>{zh}</b><small>{en.upper()}</small><p>{d}</p></li>' for en, zh, d in PROCESS)}</ol>
</div></section>
{cta_band(R, "不確定需要哪一項服務？", "告訴我們您想解決的問題，我們會建議最合適的技術組合與合作方式。")}'''
    render("services/index.html", title="產品與服務", desc="八麟光電六大核心能力：嵌入式系統、AI 視覺辨識、LoRa 無線通訊、RF 天線設計、工業控制與客製化 ODM，提供從概念到量產的一站式服務。",
           body=body, active="services", ld=[breadcrumb_ld("services/", crumbs)], priority="0.9")

    for s in SERVICES:
        crumbs = [("產品與服務", "services/"), (s["name"], None)]
        cur = ' aria-current="page"'
        others = "".join(f'<a href="{o["slug"]}.html"{cur if o is s else ""}>{e(o["name"])}<span>→</span></a>' for o in SERVICES)
        products = "".join(f'''<div class="product reveal">{img(R, p["img"], p["name"])}
  <div><h3>{e(p["name"])}</h3>{tags(p["tags"])}<p>{e(p["desc"])}</p>
  <a class="btn btn-line btn-sm" href="../contact.html?subject=產品諮詢&amp;ref={e(p["name"])}">詢問此方案</a></div></div>''' for p in s["products"])
        related = [a for a in ARTICLES if a["service"] == s["slug"]]
        rel_html = ""
        if related:
            rel_html = f'<h2 style="margin-top:56px">相關技術文章</h2><div class="grid g2">{"".join(article_card(R, a, "../insights/") for a in related)}</div>'
        apps = [a for a in APPLICATIONS if s["slug"] in a["tech"]]
        body = f'''{page_hero(R, s["name"], s["summary"], crumbs, bg=s["hero"], eyebrow=s["en"])}
<section><div class="wrap svc-layout">
  <div>
    <p class="lead-lg reveal">{e(s["intro"])}</p>
    {tags(s["tags"])}
    <h2 style="margin-top:48px">服務能力</h2>
    <ul class="checks two reveal">{"".join(f"<li>{e(c)}</li>" for c in s["capabilities"])}</ul>
    <h2 style="margin-top:56px">方案與服務</h2>
    {products}
    <h2 style="margin-top:56px">應用場域</h2>
    <div class="grid g2">{"".join(f'<a class="card reveal" href="../applications.html#{a["id"]}"><div class="body"><h3>{e(a["title"])}</h3><p>{e(a["challenge"])}</p><span class="more arrow">看解決方案 </span></div></a>' for a in apps)}</div>
    <p class="muted" style="margin-top:16px">其他適用情境：{"、".join(s["apps"])}。</p>
    {rel_html}
  </div>
  <aside class="svc-aside">
    <div class="aside-box aside-cta"><h3>有{e(s["name"])}相關需求？</h3><p>提供需求描述，1 個工作天內由工程師回覆評估。</p>
      <a class="btn" href="../contact.html?subject=客製化開發&amp;ref={e(s["name"])}">免費諮詢</a></div>
    <div class="aside-box"><h3>所有服務</h3><nav>{others}</nav></div>
  </aside>
</div></section>
{cta_band(R)}'''
        render(f"services/{s['slug']}.html", title=f"{s['name']}｜{s['en']}",
               desc=f"{C['short']}{s['name']}服務：{s['summary']}{s['intro'][:60]}…",
               body=body, active="services", ld=[breadcrumb_ld(f"services/{s['slug']}.html", crumbs),
               {"@context": "https://schema.org", "@type": "Service", "name": s["name"], "serviceType": s["en"],
                "provider": {"@id": SITE_URL + "/#org"}, "areaServed": "TW", "description": s["intro"]}],
               priority="0.8")


def build_applications():
    R = ""
    crumbs = [("應用場域", None)]
    rows = []
    for a in APPLICATIONS:
        techs = "".join(f'<li><a href="services/{t}.html">{e(SVC[t]["name"])}</a></li>' for t in a["tech"])
        demo = f'<a class="btn btn-line btn-sm" href="{a["demo"]}" target="_blank" rel="noopener">開啟相關展示 ↗</a>' if a["demo"] else ""
        rows.append(f'''<article class="scenario reveal" id="{a["id"]}">
  <div class="photo">{img(R, a["img"], a["title"])}</div>
  <div><h2>{e(a["title"])}</h2>
  <dl><dt>現場挑戰</dt><dd>{e(a["challenge"])}</dd><dt>解決方案</dt><dd>{e(a["solution"])}</dd></dl>
  <ul class="tags">{techs}</ul>
  <div style="display:flex;gap:10px;flex-wrap:wrap"><a class="btn btn-primary btn-sm" href="contact.html?subject=客製化開發&amp;ref={e(a["title"])}">討論我的需求</a>{demo}</div></div>
</article>''')
    body = f'''{page_hero(R, "應用場域", "把嵌入式、無線通訊、AI 與工業控制技術，整合成解決現場問題的方案。", crumbs, bg="p10", eyebrow="Applications")}
<section><div class="wrap">
  <p class="note" style="margin-bottom:32px">以下為典型應用架構說明，實際方案將依您的場域條件、預算與時程規劃。</p>
  {"".join(rows)}
</div></section>
{cta_band(R, "您的場域也有類似的挑戰？", "告訴我們現場狀況，我們會提出可行的技術架構與導入建議。")}'''
    render("applications.html", title="應用場域", desc="八麟光電應用場域：設備狀態監測、智慧農業 LoRa 感測、產線 AI 瑕疵檢測、OCR 標籤辨識、無線產品天線整合與舊設備聯網改造。",
           body=body, active="applications", ld=[breadcrumb_ld("applications.html", crumbs)], priority="0.8")


def build_demos():
    R = ""
    crumbs = [("即時展示", None)]
    body = f'''{page_hero(R, "AIoT 即時監測展示", "實際操作我們開發的監控儀表板，體驗設備資料即時上雲後的樣子。", crumbs, bg="demo-aiot", eyebrow="Tech Showcase")}
<section class="dark"><div class="wrap">
  <div class="grid g3">{"".join(demo_card(R, d) for d in DEMOS)}</div>
  <p class="note" style="color:#7F96B0;margin-top:24px">展示頁面使用模擬資料。實際專案可串接您的感測器、PLC 或既有系統，並依需求客製畫面與警示規則。</p>
</div></section>
<section><div class="wrap split">
  <div class="reveal"><span class="eyebrow">Architecture</span><h2>典型系統架構</h2>
  <ul class="checks">
    <li><b>感測層：</b>溫度、壓力、振動、轉速、DI／DO 點位等感測器與 I/O 模組。</li>
    <li><b>傳輸層：</b>RS485／Modbus、CAN、LoRa 或 Wi-Fi，依距離與佈線條件選擇。</li>
    <li><b>閘道層：</b>嵌入式閘道器負責協定轉換、邊緣運算與斷線暫存。</li>
    <li><b>平台層：</b>MQTT 資料上雲、資料庫保存、即時儀表板與異常通知。</li>
  </ul>
  <a class="btn btn-primary" href="applications.html#monitoring">看設備監測方案</a></div>
  <div class="photo reveal">{img(R, "demo-boiler", "鍋爐感測儀表板畫面")}</div>
</div></section>
{cta_band(R, "想要一套自己的監控儀表板？", "從感測器、閘道器到儀表板，我們可以整套建置，也可以串接您的既有設備。")}'''
    render("demos.html", title="AIoT 即時監測展示", desc="八麟光電 AIoT 即時監測展示：感測即時儀表板、鍋爐壓力溫度監控、活塞馬達轉速振動監測，體驗設備資料即時上雲。",
           body=body, active="demos", ld=[breadcrumb_ld("demos.html", crumbs)], priority="0.7")


def expand_imgs(R, body):
    def rep(m):
        name, cap = (m.group(1).split("|") + [""])[:2]
        return f'<figure>{img(R, name, cap)}<figcaption>{e(cap)}</figcaption></figure>'
    return re.sub(r"\{img:([^}]+)\}", rep, body)


def build_insights():
    R = "../"
    crumbs = [("技術專欄", None)]
    body = f'''{page_hero(R, "技術專欄", "分享我們在嵌入式、無線通訊、RF 天線、AI 視覺與工業控制專案中累積的實務經驗。", crumbs, bg="hero", eyebrow="Insights")}
<section><div class="wrap"><div class="grid g3">{"".join(article_card(R, a, "") for a in ARTICLES)}</div></div></section>
{cta_band(R, "有技術問題想討論？", "歡迎直接與我們的工程師聯繫，一起找出最適合的解法。")}'''
    render("insights/index.html", title="技術專欄", desc="八麟光電技術專欄：LoRa 頻段與參數設計、PCB 天線匹配、ESP32 低功耗、AI 視覺瑕疵檢測、RS485／Modbus 除錯等實務文章。",
           body=body, active="insights", ld=[breadcrumb_ld("insights/", crumbs)], priority="0.7")

    for a in ARTICLES:
        crumbs = [("技術專欄", "insights/"), (a["title"], None)]
        toc = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', a["body"])
        toc_html = '<nav class="toc" aria-label="文章目錄"><b>本文目錄</b><ol>' + "".join(
            f'<li><a href="#{i}">{t}</a></li>' for i, t in toc) + "</ol></nav>" if toc else ""
        s = SVC[a["service"]]
        more = [x for x in ARTICLES if x is not a][:3]
        body = f'''<section class="page-hero"><div class="wrap">
  <nav class="crumbs" aria-label="麵包屑"><a href="../index.html">首頁</a><span>/</span><a href="./">技術專欄</a></nav>
  <div class="post-meta" style="color:#9DB1C8"><span class="pill">{e(a["tag"])}</span><time datetime="{a["date"]}">{a["date"].replace("-", ".")}</time><span>八麟光電研發團隊</span></div>
  <h1>{e(a["title"])}</h1><p>{e(a["excerpt"])}</p>
</div></section>
<section><div class="wrap">
  <article class="article">
    <figure style="margin-top:0">{img(R, a["img"], a["title"], lazy=False)}<figcaption>示意圖</figcaption></figure>
    {toc_html}
    {expand_imgs(R, a["body"])}
    <hr style="border:0;border-top:1px solid var(--line);margin:48px 0 24px">
    <p class="muted">本文由八麟光電研發團隊整理，內容為一般性技術說明；實際設計請依產品條件與最新法規評估。相關服務：<a href="../services/{s["slug"]}.html">{e(s["name"])}</a></p>
  </article>
</div></section>
<section class="soft"><div class="wrap"><div class="sec-head"><h2>延伸閱讀</h2></div>
<div class="grid g3">{"".join(article_card(R, x, "") for x in more)}</div></div></section>
{cta_band(R)}'''
        render(f"insights/{a['slug']}.html", title=a["title"], desc=a["excerpt"], body=body, active="insights", og_type="article",
               og_img=f'{a["img"]}.webp',
               ld=[breadcrumb_ld(f"insights/{a['slug']}.html", crumbs),
                   {"@context": "https://schema.org", "@type": "TechArticle", "headline": a["title"], "description": a["excerpt"],
                    "datePublished": a["date"], "inLanguage": "zh-Hant-TW", "image": f'{SITE_URL}/assets/img/{a["img"]}.webp',
                    "author": {"@type": "Organization", "name": C["name"]}, "publisher": {"@id": SITE_URL + "/#org"}}],
               priority="0.6")


def build_support():
    R = ""
    crumbs = [("技術支援", None)]
    steps = "".join(f'<div class="card reveal"><div class="body"><span class="card-en">STEP {i:02d}</span><h3>{t}</h3><p>{d}</p></div></div>'
                    for i, (t, d) in enumerate(SUPPORT_STEPS, 1))
    models = "".join(f'''<div class="card reveal"><div class="body"><span class="icon-badge" style="position:static">{icon(ic)}</span>
  <h3>{t}</h3><p>{d}</p><ul class="checks">{"".join(f"<li>{x}</li>" for x in pts)}</ul></div></div>'''
                     for (t, d, pts), ic in zip(MODELS, ["users", "tool", "factory"]))
    docs = "".join(f'''<div class="card reveal"><div class="body"><span class="icon-badge" style="position:static">{icon("doc")}</span>
  <h3>{t}</h3><p>{d}</p><a class="more arrow" href="contact.html?subject=技術支援&amp;ref={e(t)}">填表索取 </a></div></div>''' for t, d in DOCS)
    faqs = "".join(f"<details><summary>{e(q)}</summary><div><p>{e(a)}</p></div></details>" for q, a in FAQS)
    body = f'''{page_hero(R, "技術支援", "從需求諮詢到量產，全程提供專業技術協助。", crumbs, bg="support", eyebrow="Support")}
<section><div class="wrap">
  <div class="sec-head"><span class="eyebrow">Service Flow</span><h2>服務流程</h2></div>
  <div class="grid g4">{steps}</div>
</div></section>
<section class="soft"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">Engagement</span><h2>合作模式</h2><p>依您的團隊與專案階段，選擇最合適的合作方式。</p></div>
  <div class="grid g3">{models}</div>
</div></section>
<section><div class="wrap">
  <div class="sec-head"><span class="eyebrow">Documents</span><h2>技術文件索取</h2><p>為確保您取得對應版本的最新資料，技術文件採填表索取，由專人寄送。</p></div>
  <div class="grid g4">{docs}</div>
</div></section>
<section class="soft"><div class="wrap">
  <div class="sec-head center"><span class="eyebrow">FAQ</span><h2>常見問題</h2></div>
  <div class="faq">{faqs}</div>
</div></section>
{cta_band(R, "找不到您要的答案？", "直接與工程師聯繫，我們會在 1 個工作天內回覆。")}'''
    render("support.html", title="技術支援", desc="八麟光電技術支援：服務流程、合作模式（技術顧問、委託設計、ODM 量產）、技術文件索取與常見問題。",
           body=body, active="support", priority="0.7",
           ld=[breadcrumb_ld("support.html", crumbs),
               {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                   {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQS]}])


def build_contact():
    R = ""
    crumbs = [("聯絡我們", None)]
    q = html.escape(C["address"])
    subjects = ["產品諮詢", "客製化開發", "技術支援", "代理經銷合作", "其他"]
    body = f'''{page_hero(R, "聯絡我們", "歡迎洽詢產品規格、合作方案或技術支援需求，我們將於 1 個工作天內回覆。", crumbs, eyebrow="Contact")}
<section><div class="wrap contact-grid">
  <div>
    <h2>聯絡資訊</h2>
    <ul class="contact-list">
      <li><span class="icon-badge">{icon("phone")}</span><div><small>聯絡電話</small><a href="tel:{C["phone_intl"]}">{C["phone"]}</a></div></li>
      <li><span class="icon-badge">{icon("mail")}</span><div><small>電子信箱</small><a href="mailto:{C["email"]}">{C["email"]}</a></div></li>
      <li><span class="icon-badge">{icon("map")}</span><div><small>公司地址</small><span>{C["address"]}</span></div></li>
      <li><span class="icon-badge">{icon("clock")}</span><div><small>服務時間</small><span>{C["hours"]}</span></div></li>
    </ul>
    <div class="map"><iframe title="八麟光電位置地圖" loading="lazy" referrerpolicy="no-referrer-when-downgrade"
      src="https://www.google.com/maps?q={q}&amp;output=embed"></iframe></div>
    <p style="margin-top:12px"><a href="https://www.google.com/maps/dir/?api=1&amp;destination={q}" target="_blank" rel="noopener">在 Google 地圖規劃路線 ↗</a></p>
  </div>
  <div class="form-card">
    <h2>線上諮詢表單</h2>
    <p class="muted">請盡量描述您的應用情境、預計數量與時程，方便我們提供更準確的建議。</p>
    <form id="contact-form" action="{C["form_endpoint"]}" method="post" data-email="{C["email"]}" data-phone="{C["phone"]}" novalidate>
      <div class="form-grid">
        <div><label for="f-name">姓名 <span class="req">*</span></label><input id="f-name" name="姓名" required autocomplete="name"></div>
        <div><label for="f-company">公司名稱</label><input id="f-company" name="公司" autocomplete="organization"></div>
        <div><label for="f-email">電子信箱 <span class="req">*</span></label><input id="f-email" name="email" type="email" required autocomplete="email"></div>
        <div><label for="f-phone">聯絡電話</label><input id="f-phone" name="電話" type="tel" autocomplete="tel"></div>
        <div class="full"><label for="f-subject">諮詢主題</label><select id="f-subject" name="諮詢主題">{"".join(f"<option>{x}</option>" for x in subjects)}</select></div>
        <div class="full"><label for="f-msg">需求說明 <span class="req">*</span></label><textarea id="f-msg" name="需求說明" required placeholder="例如：想開發一款 LoRa 溫濕度感測器，電池供電，預計數量 500 台，希望 6 個月內量產。"></textarea></div>
        <input class="hp" type="text" name="_honey" tabindex="-1" autocomplete="off" aria-hidden="true">
        <div class="full"><button class="btn btn-primary" type="submit">送出諮詢</button>
        <p class="form-note">送出即表示您同意我們使用上述資料回覆您的諮詢，資料不會提供給第三方。</p>
        <div class="form-status" role="status" hidden></div></div>
      </div>
    </form>
  </div>
</div></section>'''
    render("contact.html", title="聯絡我們", desc=f"聯絡八麟光電科技：電話 {C['phone']}，地址 {C['address']}。線上填寫需求，1 個工作天內由工程師回覆。",
           body=body, active="contact", ld=[breadcrumb_ld("contact.html", crumbs), ORG_LD], priority="0.8")


def build_credits():
    R = ""
    rows = "".join(
        f'<tr><td><img src="assets/img/{k}.webp" alt="" width="96" loading="lazy" style="border-radius:6px"></td>'
        f'<td><a href="{e(v["page"])}" target="_blank" rel="noopener">{e(v["title"].replace("File:", ""))}</a></td>'
        f'<td>{e(html.unescape(v["artist"])) or "—"}</td><td>{e(v["license"])}</td></tr>'
        for k, v in CREDITS.items())
    body = f'''{page_hero(R, "圖片來源與授權", "本網站部分照片來自 Wikimedia Commons，依各自的開放授權條款使用。", [("圖片來源與授權", None)])}
<section><div class="wrap">
  <p>以下照片為示意用途，版權屬原作者所有，依所列授權（CC0、公有領域、CC BY、CC BY-SA）使用，部分照片經裁切與壓縮。點選標題可查看原始檔案與完整授權。即時展示畫面、網站標誌與插圖為八麟光電所有。</p>
  <div class="table-scroll article" style="max-width:none"><table class="credits"><tr><th>預覽</th><th>原始檔案</th><th>作者</th><th>授權</th></tr>{rows}</table></div>
</div></section>'''
    render("credits.html", title="圖片來源與授權", desc="八麟光電官網使用之開放授權圖片來源與授權說明。", body=body, priority="0.2")


def build_404():
    body = '''<section class="page-hero" style="min-height:60vh;display:grid;align-items:center"><div class="wrap">
  <span class="eyebrow">404</span><h1>找不到這個頁面</h1><p>頁面可能已移動或網址有誤。您可以回到首頁，或直接與我們聯繫。</p>
  <p style="margin-top:28px;display:flex;gap:12px;flex-wrap:wrap"><a class="btn btn-primary" href="/">回到首頁</a><a class="btn btn-ghost" href="/contact.html">聯絡我們</a></p>
</div></section>'''
    # 404 頁可能出現在任何路徑下，所以用根目錄絕對路徑
    render("404.html", title="找不到頁面", desc="找不到頁面", body=body, in_sitemap=False)
    p = os.path.join(ROOT, "404.html")
    s = open(p, encoding="utf-8").read()
    s = re.sub(r'(href|src)="(?!https?:|/|#|mailto:|tel:)', r'\1="/', s)
    open(p, "w", encoding="utf-8", newline="\n").write(s)


# ---------------------------------------------------------------------------
# English
# ---------------------------------------------------------------------------
EN_SERVICES = {
    "embedded": "Circuit design, PCB layout and firmware on STM32, ESP32, PIC, MSP430 and ARM Linux, including RTOS, low-power design and OTA updates.",
    "ai-vision": "Camera and lighting design, YOLO object detection, OpenCV and OCR, deployed on edge devices and integrated with PLCs.",
    "lora": "SX12xx RF design, point-to-point and LoRaWAN networks for AS923 / US915 / EU868 / CN470, gateways and MQTT cloud integration.",
    "rf-antenna": "Custom PCB, IFA, meander, patch and spring antennas, matching networks tuned with a vector network analyzer.",
    "industrial": "RS485 / Modbus RTU & TCP, CAN, PLC integration, multi-channel I/O and real-time dashboards over MQTT.",
    "odm": "PCB layout, prototyping, pilot runs and mass production, plus test fixtures and certification (NCC / CE / FCC) support.",
}


def header_en(R):
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap">
  <a class="brand" href="{R}en/"><img src="{R}assets/img/logo.svg" alt="" width="42" height="42">
  <span class="brand-name"><b>BALIN</b><small>OPTOELECTRONICS</small></span></a>
  <button class="menu-toggle" type="button" aria-label="Menu" aria-expanded="false"><span></span></button>
  <nav class="nav" aria-label="Main">
    <a href="#capabilities">Capabilities</a><a href="#process">Process</a><a href="#demos">Demos</a><a href="#about">About</a>
    <a class="lang" href="{R}index.html" lang="zh-Hant">中文</a>
    <a class="btn btn-primary btn-sm" href="#contact">Contact Us</a>
  </nav>
</div></header>'''


def footer_en(R):
    return f'''<footer class="site-footer"><div class="wrap">
  <div class="foot-bottom" style="margin-top:0;border-top:0;padding-top:0">
    <span>© {date.today().year} {C["en"]} · Tax ID {C["tax_id"]} · {C["address_en"]}</span>
    <span><a href="{R}credits.html">Image credits</a></span>
  </div>
</div></footer>'''


def build_en():
    R = "../"
    years = date.today().year - C["founded_year"]
    cards = "".join(f'''<div class="card reveal"><div class="media">{img(R, s["card"], s["en"])}</div>
  <span class="icon-badge">{icon(s["icon"])}</span><div class="body"><h3>{s["en"]}</h3><p>{EN_SERVICES[s["slug"]]}</p></div></div>''' for s in SERVICES)
    body = f'''
<section class="hero"><div class="wrap">
  <div><span class="eyebrow">AIoT Product Design House · Since {C["founded_year"]}</span>
    <h1>From concept to mass production — <em>smart hardware, done right.</em></h1>
    <p class="lead">Balin Optoelectronics is an engineering design house in Tainan, Taiwan. We build embedded systems, AI vision, LoRa / RF wireless and industrial automation products for OEM and ODM customers.</p>
    <div class="cta"><a class="btn btn-primary" href="#contact">Talk to an engineer</a><a class="btn btn-ghost" href="#capabilities">Our capabilities</a></div>
    <ul class="chips"><li>STM32 / ESP32</li><li>YOLO / OCR</li><li>LoRaWAN</li><li>PCB Antenna</li><li>Modbus / MQTT</li><li>OEM / ODM</li></ul>
  </div>
  <div class="hero-visual"><div class="photo">{img(R, "hero", "Microcontroller on a circuit board", lazy=False)}</div>
    <div class="hero-card"><span class="pulse"></span><span><b>{years}+ years</b>of embedded engineering</span></div></div>
</div></section>
<section id="capabilities"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">Core Capabilities</span><h2>Six disciplines, one team</h2>
  <p>Hardware, firmware, AI and RF under one roof — fewer hand-offs, faster iterations and lower project risk.</p></div>
  <div class="grid g3">{cards}</div>
</div></section>
<section class="dark" id="process"><div class="wrap">
  <div class="sec-head center"><span class="eyebrow">R&amp;D Process</span><h2>One-stop development</h2></div>
  <ol class="process">{"".join(f"<li><b>{en}</b></li>" for en, zh, d in PROCESS)}</ol>
</div></section>
<section id="demos"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">Live Demos</span><h2>Real-time IoT dashboards</h2><p>Try the monitoring dashboards we built (simulated data, Chinese UI).</p></div>
  <div class="grid g3">{"".join(f'<a class="card reveal" href="{R}{d["href"]}" target="_blank" rel="noopener"><div class="media">{img(R, d["img"], "Dashboard screenshot")}</div><div class="body"><h3>{t}</h3><span class="more">Open demo ↗</span></div></a>' for d, t in zip(DEMOS, ["IoT Sensor Dashboard", "Boiler Monitoring", "Rotating Equipment Monitoring"]))}</div>
</div></section>
<section class="soft" id="about"><div class="wrap split">
  <div class="reveal"><span class="eyebrow">About</span><h2>Company profile</h2>
    <table class="info">
      <tr><th>Company</th><td>{C["en"]}</td></tr><tr><th>Founded</th><td>May {C["founded_year"]}</td></tr>
      <tr><th>Tax ID</th><td>{C["tax_id"]}</td></tr><tr><th>Location</th><td>{C["address_en"]}</td></tr>
      <tr><th>Languages</th><td>Mandarin Chinese, English</td></tr>
    </table></div>
  <div class="photo reveal">{img(R, "about-solder", "Soldering SMD components")}</div>
</div></section>
<section id="contact" class="cta-wrap"><div class="wrap"><div class="cta-box">
  <div><h2>Let's build your next product</h2><p>Email <a href="mailto:{C["email"]}" style="color:#fff;text-decoration:underline">{C["email"]}</a> or call <a href="tel:{C["phone_intl"]}" style="color:#fff">{C["phone_intl"]}</a>. We reply within one business day.</p></div>
  <div class="actions"><a class="btn btn-primary" href="mailto:{C["email"]}?subject=Project%20inquiry">Email us</a></div>
</div></div></section>'''
    render("en/index.html", title="Balin Optoelectronics | Embedded, AI Vision, LoRa & RF Design House in Taiwan",
           desc="Balin Optoelectronics is an AIoT product design house in Tainan, Taiwan: embedded systems (STM32/ESP32), AI vision, LoRa/RF wireless, antenna design, industrial automation and OEM/ODM manufacturing.",
           body=body, lang="en", ld=[ORG_LD], priority="0.6")


# ---------------------------------------------------------------------------
def build_meta_files():
    urls = "".join(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod><priority>{p}</priority></url>\n" for u, p in PAGES)
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8", newline="\n").write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8", newline="\n").write(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    print("   sitemap.xml, robots.txt")


if __name__ == "__main__":
    print("產生頁面：")
    build_home()
    build_about()
    build_services()
    build_applications()
    build_demos()
    build_insights()
    build_support()
    build_contact()
    build_credits()
    build_404()
    build_en()
    build_meta_files()
    print(f"完成，共 {len(PAGES)} 頁列入 sitemap。")
