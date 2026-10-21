# -*- coding: utf-8 -*-
"""
八麟光電科技官網 — 多語言靜態網站產生器
用法（在 site 資料夾執行）：python tools/build.py

內容：
  tools/content.py        繁體中文內容（主檔）
  tools/i18n/zh_tw.py     繁體中文介面文字
  tools/i18n/en.py ...    各語言翻譯（只需寫文字，其餘沿用主檔）
  tools/i18n/zh_cn.py     簡體中文，由 tools/make_zh_cn.py 從繁體自動轉換
樣式在 assets/css/style.css。
"""
import html
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
import i18n
import photos

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = date.today().isoformat()
import hashlib
# CSS／JS 的版本號取自檔案內容，檔案一改就換號，避免訪客瀏覽器用到舊的快取
VER = hashlib.sha1(b"".join(open(os.path.join(ROOT, "assets", x), "rb").read()
                            for x in ("css/style.css", "js/main.js"))).hexdigest()[:8]
CREDITS = json.load(open(os.path.join(ROOT, "tools", "credits.json"), encoding="utf-8"))
SITE_URL = i18n.SITE_URL
PAGES = []  # 給 sitemap 用
PH = {}     # 照片庫（build 時載入）
e = html.escape

# 聯絡表單主旨：代碼 → 寄給公司的中文主旨（不論訪客語言，信件主旨一律為中文）
SUBJECTS = [("product", "產品諮詢"), ("custom", "客製化開發"), ("support", "技術支援"),
            ("dealer", "代理經銷合作"), ("other", "其他")]

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
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
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


def img(R, name, alt, lazy=True):
    w, h = img_size(name)
    load = ' loading="lazy" decoding="async"' if lazy else ' fetchpriority="high"'
    return f'<img src="{R}assets/img/{name}.webp" alt="{e(alt)}" width="{w}" height="{h}"{load}>'


def tags(items):
    return '<ul class="tags">' + "".join(f"<li>{e(t)}</li>" for t in items) + "</ul>"


def photo(slug, key, default):
    """照片庫有對應照片就用照片庫的，否則用預設圖。"""
    return PH.get(slug, {}).get(key) or default


# ---------------------------------------------------------------------------
# 頁面環境
# ---------------------------------------------------------------------------
class Page:
    """一個語言中的一個頁面。R = 到網站根目錄，H = 到該語言首頁目錄。"""

    def __init__(self, L, path):
        self.L, self.path = L, path
        self.full = L.prefix + path
        self.R = "../" * self.full.count("/")
        self.H = self.R + L.prefix
        self.D = L.data
        self.C = L.data.COMPANY

    def t(self, key, **kw):
        return self.L.t(key, **kw)

    def url(self, path):
        return self.H + path

    def contact(self, subject, ref=""):
        q = f"contact.html?subject={subject}"
        if ref:
            q += "&amp;ref=" + e(ref)
        return self.H + q


def gallery(P, slug, title, lead=""):
    items = PH.get(slug, {}).get("gallery", [])
    if not items:
        return ""
    show_cap = P.L.code.startswith("zh")  # 照片說明取自中文檔名，只在中文版顯示
    figs = "".join(
        f'<figure class="reveal"><a href="{P.R}assets/img/{i}.webp" data-lightbox>{img(P.R, i, (c if show_cap else "") or title)}</a>'
        f'{f"<figcaption>{e(c)}</figcaption>" if c and show_cap else ""}</figure>' for i, c in items)
    lead_html = f'<p>{lead}</p>' if lead else ""
    return f'<div class="gallery-head"><h2>{title}</h2>{lead_html}</div><div class="gallery">{figs}</div>'


def section_gallery(P, slug, title, lead="", cls=""):
    g = gallery(P, slug, title, lead)
    return f'<section class="{cls}"><div class="wrap">{g}</div></section>' if g else ""


# ---------------------------------------------------------------------------
# 版型
# ---------------------------------------------------------------------------
NAV = [("about", "about.html"), ("services", None), ("applications", "applications.html"),
       ("demos", "demos.html"), ("insights", "insights/"), ("support", "support.html")]


def lang_switch(P):
    L = P.L
    cur = ' aria-current="true"'
    links = "".join(
        f'<a href="{P.R}{o.prefix}{P.path}" lang="{o.html_lang}" hreflang="{o.hreflang}"'
        f'{cur if o is L else ""}><b>{o.label}</b></a>' for o in i18n.LANGS)
    return (f'<div class="dd lang-dd"><button type="button" aria-expanded="false" aria-label="{P.t("lang_label")}">'
            f'{icon("globe", 18)}<span>{L.short}</span></button><div class="dd-menu">{links}</div></div>')


def header(P, active):
    S = P.D.SERVICES
    items = []
    for key, href in NAV:
        label = P.t("nav_" + key)
        if key == "services":
            menu = "".join(
                f'<a href="{P.url("services/" + s["slug"] + ".html")}">{icon(s["icon"], 20)}<span><b>{e(s["name"])}</b><small>{e(s["summary"])}</small></span></a>'
                for s in S)
            cls = "dd active" if active == key else "dd"
            items.append(f'<div class="{cls}"><button type="button" aria-expanded="false">{label}</button>'
                         f'<div class="dd-menu">{menu}<a class="all" href="{P.url("services/")}">{P.t("all_services")} →</a></div></div>')
        else:
            cur = ' aria-current="page"' if active == key else ""
            items.append(f'<a href="{P.url(href)}"{cur}>{label}</a>')
    cur = ' aria-current="page"' if active == "contact" else ""
    return f'''<a class="skip" href="#main">{P.t("skip")}</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{P.url("index.html")}" aria-label="{e(P.C["name"])}">
      <img src="{P.R}assets/img/logo.svg" alt="" width="42" height="42">
      <span class="brand-name"><b>{P.C["brand"]}</b><small>{P.C["brand_sub"]}</small></span>
    </a>
    <button class="menu-toggle" type="button" aria-label="{P.t("menu")}" aria-expanded="false"><span></span></button>
    <nav class="nav" aria-label="{P.t("menu")}">
      {"".join(items)}
      {lang_switch(P)}
      <a class="btn btn-primary btn-sm" href="{P.url("contact.html")}"{cur}>{P.t("nav_contact")}</a>
    </nav>
  </div>
</header>'''


def footer(P):
    C = P.C
    svc = "".join(f'<li><a href="{P.url("services/" + s["slug"] + ".html")}">{e(s["name"])}</a></li>' for s in P.D.SERVICES)
    links = "".join(f'<li><a href="{P.url(h)}">{P.t("nav_" + k)}</a></li>' for k, h in
                    [("about", "about.html"), ("applications", "applications.html"), ("demos", "demos.html"),
                     ("insights", "insights/"), ("support", "support.html"), ("contact", "contact.html")])
    langs = " · ".join(f'<a href="{P.R}{o.prefix}{P.path}" lang="{o.html_lang}">{o.label}</a>' for o in i18n.LANGS)
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div class="foot-grid">
      <div class="foot-brand">
        <a class="brand" href="{P.url("index.html")}"><img src="{P.R}assets/img/logo.svg" alt="" width="42" height="42" loading="lazy">
          <span class="brand-name"><b>{C["name"]}</b><small>{C["en_short"]}</small></span></a>
        <p>{P.t("footer_about")}</p>
      </div>
      <div><h4>{P.t("nav_services")}</h4><ul>{svc}</ul></div>
      <div><h4>{P.t("quick_links")}</h4><ul>{links}</ul></div>
      <div><h4>{P.t("contact_info")}</h4><ul>
        <li>{C["address"]}</li>
        <li>{P.t("tel")}<a href="tel:{C["phone_intl"]}">{C["phone_display"]}</a></li>
        <li>{P.t("mail")}<a href="mailto:{C["email"]}">{C["email"]}</a></li>
        <li>{C["hours"]}</li>
      </ul></div>
    </div>
    <div class="foot-langs">{icon("globe", 16)} {langs}</div>
    <div class="foot-bottom">
      <span>© {date.today().year} {C["name"]}　{P.t("tax_id")} {C["tax_id"]}</span>
      <span><a href="{P.url("credits.html")}">{P.t("credits_title")}</a></span>
    </div>
  </div>
</footer>'''


def cta_band(P, title=None, text=None):
    return f'''<section class="cta-wrap"><div class="wrap"><div class="cta-box reveal">
  <div><h2>{title or P.t("cta_title")}</h2><p>{text or P.t("cta_text")}</p></div>
  <div class="actions"><a class="btn btn-primary" href="{P.url("contact.html")}">{P.t("cta_btn")}</a>
  <a class="btn btn-ghost" href="tel:{P.C["phone_intl"]}">{icon("phone", 18)} {P.C["phone_display"]}</a></div>
</div></div></section>'''


def page_hero(P, title, text, crumbs, bg=None, eyebrow=None):
    def crumb(t, h):
        return f'<a href="{P.url(h)}">{e(t)}</a>' if h else e(t)
    trail = f'<a href="{P.url("index.html")}">{P.t("home")}</a>' + "".join(f"<span>/</span>{crumb(t, h)}" for t, h in crumbs)
    style = (f' style="background-image:linear-gradient(100deg,rgba(6,20,35,.95) 35%,rgba(6,20,35,.62)),'
             f'url({P.R}assets/img/{bg}.webp)"') if bg else ""
    eb = f'<span class="eyebrow">{e(eyebrow)}</span>' if eyebrow else ""
    return f'''<section class="page-hero"{style}><div class="wrap">
  <nav class="crumbs" aria-label="{P.t("breadcrumb")}">{trail}</nav>
  {eb}<h1>{title}</h1><p>{text}</p>
</div></section>'''


def breadcrumb_ld(P, crumbs):
    base = SITE_URL + "/" + P.L.prefix
    items = [{"@type": "ListItem", "position": 1, "name": P.t("home"), "item": base}]
    for i, (t, h) in enumerate(crumbs, 2):
        items.append({"@type": "ListItem", "position": i, "name": t, "item": base + (h or P.path)})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


def org_ld(P):
    C = P.C
    return {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "@id": SITE_URL + "/#org",
        "name": C["name"],
        "alternateName": [C["en"], "八麟光電科技有限公司"],
        "url": SITE_URL + "/" + P.L.prefix,
        "logo": SITE_URL + "/assets/img/logo.svg",
        "image": SITE_URL + "/assets/img/og.png",
        "description": P.t("org_desc"),
        "telephone": C["phone_intl"],
        "email": C["email"],
        "taxID": C["tax_id"],
        "foundingDate": "2009-05",
        "address": {"@type": "PostalAddress", "streetAddress": "永大路3段618巷12號1樓", "addressLocality": "永康區",
                    "addressRegion": "臺南市", "addressCountry": "TW"},
        "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
                                       "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                                       "opens": "09:00", "closes": "18:00"}],
        "areaServed": "Worldwide",
        "knowsAbout": ["Embedded systems", "AI vision", "LoRa", "RF antenna design", "Industrial automation", "OEM/ODM", "STM32", "ESP32"],
    }


def render(P, *, title, desc, body, active=None, ld=None, og_img="og.png", og_type="website", priority="0.7", in_sitemap=True):
    L, C = P.L, P.C
    canonical = SITE_URL + "/" + (P.full[:-10] if P.full.endswith("index.html") else P.full)
    full_title = title if C["short"] in title or "Balin" in title else f"{title}｜{C['name']}"
    path_url = P.path[:-10] if P.path.endswith("index.html") else P.path
    alts = "".join(f'<link rel="alternate" hreflang="{o.hreflang}" href="{SITE_URL}/{o.prefix}{path_url}">\n' for o in i18n.LANGS)
    alts += f'<link rel="alternate" hreflang="x-default" href="{SITE_URL}/{i18n.DEFAULT.prefix}{path_url}">\n'
    lds = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    doc = f'''<!DOCTYPE html>
<html lang="{L.html_lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
{alts}<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{e(C["name"])}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE_URL}/assets/img/{og_img}">
<meta property="og:locale" content="{L.og_locale}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#061423">
<link rel="icon" href="{P.R}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{P.R}assets/img/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&display=swap">
<link rel="stylesheet" href="{P.R}assets/css/style.css?v={VER}">
{lds}
</head>
<body data-close="{P.t("close")}">
{header(P, active)}
<main id="main">
{body}
</main>
{footer(P)}
<script src="{P.R}assets/js/main.js?v={VER}" defer></script>
</body>
</html>
'''
    out = os.path.join(ROOT, P.full)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(doc)
    if in_sitemap:
        PAGES.append((canonical, priority))


# ---------------------------------------------------------------------------
# 元件
# ---------------------------------------------------------------------------
def same(a, b):
    return a.replace(" ", "").lower() == b.replace(" ", "").lower()


def svc_card(P, s):
    eyebrow = "" if same(s["en"], s["name"]) else f'<span class="card-en">{e(s["en"])}</span>'
    return f'''<a class="card reveal" href="{P.url("services/" + s["slug"] + ".html")}">
  <div class="media">{img(P.R, photo(s["slug"], "cover", s["card"]), s["name"])}</div>
  <span class="icon-badge">{icon(s["icon"])}</span>
  <div class="body">{eyebrow}<h3>{e(s["name"])}</h3>
  <p>{e(s["summary"])}</p>{tags(s["tags"][:5])}<span class="more arrow">{P.t("learn_more")} </span></div>
</a>'''


def article_card(P, a):
    return f'''<a class="card reveal" href="{P.url("insights/" + a["slug"] + ".html")}">
  <div class="media">{img(P.R, a["img"], a["title"])}</div>
  <div class="body"><div class="post-meta"><span class="pill">{e(a["tag"])}</span><time datetime="{a["date"]}">{a["date"].replace("-", ".")}</time></div>
  <h3>{e(a["title"])}</h3><p>{e(a["excerpt"])}</p><span class="more arrow">{P.t("read_more")} </span></div>
</a>'''


def demo_card(P, d):
    return f'''<a class="card demo-card reveal" href="{P.R}{d["href"]}" target="_blank" rel="noopener">
  <div class="media">{img(P.R, d["img"], d["title"])}</div>
  <div class="body"><span class="live"><span class="pulse"></span>LIVE DEMO</span><h3>{e(d["title"])}</h3>
  <p>{e(d["desc"])}</p>{tags(d["tags"])}<span class="more">{P.t("open_demo")} ↗</span></div>
</a>'''


def process_list(P):
    return "".join(f'<li><b>{loc}</b>{"" if same(en, loc) else f"<small>{en.upper()}</small>"}<p>{d}</p></li>'
                   for en, loc, d in P.D.PROCESS)


# ---------------------------------------------------------------------------
# 頁面
# ---------------------------------------------------------------------------
def build_home(L):
    P = Page(L, "index.html")
    D, C, t = P.D, P.C, P.t
    years = date.today().year - C["founded_year"]
    apps = "".join(f'''<a class="card reveal" href="{P.url("applications.html")}#{a["id"]}"><div class="media">{img(P.R, a["img"], a["title"])}</div>
  <div class="body"><h3>{e(a["title"])}</h3><p>{e(a["challenge"])}</p><span class="more arrow">{t("see_solution")} </span></div></a>''' for a in D.APPLICATIONS[:3])
    redirect = ""
    if L is i18n.BASE:
        redirect = '''<script>
// 舊版網址（#about、#products…）自動導向新頁面
(function(){var m={about:"about.html",products:"services/",support:"support.html",news:"insights/",contact:"contact.html"};var h=location.hash.slice(1);if(m[h])location.replace(m[h]);})();
</script>'''
    body = f'''
<section class="hero">
  <div class="wrap">
    <div>
      <span class="eyebrow">{C["tagline"]} · SINCE {C["founded_year"]}</span>
      <h1>{t("hero_h1_a")}<br><em>{t("hero_h1_b")}</em></h1>
      <p class="lead">{t("hero_lead")}</p>
      <div class="cta">
        <a class="btn btn-primary" href="{P.url("contact.html")}">{t("hero_cta")}</a>
        <a class="btn btn-ghost" href="#capabilities">{t("hero_cta2")}</a>
      </div>
      <ul class="chips">{"".join(f"<li>{e(x)}</li>" for x in t("hero_chips").split("|"))}</ul>
    </div>
    <div class="hero-visual">
      <div class="photo">{img(P.R, photo("home", "hero", "hero"), t("hero_img_alt"), lazy=False)}</div>
      <div class="hero-card"><span class="pulse"></span><span><b>{t("hero_card_value", years=years)}</b>{t("hero_card_label")}</span></div>
    </div>
  </div>
</section>

<section class="stats" aria-label="{t("stats_label")}"><div class="wrap"><ul>
  <li><b>{C["founded_year"]}</b><span>{t("stat1")}</span></li>
  <li><b>{years}<small>{t("stat2_unit")}</small></b><span>{t("stat2")}</span></li>
  <li><b>6<small>{t("stat3_unit")}</small></b><span>{t("stat3")}</span></li>
  <li><b>7<small>{t("stat4_unit")}</small></b><span>{t("stat4")}</span></li>
</ul></div></section>

<section id="capabilities"><div class="wrap">
  <div class="sec-head split"><div><span class="eyebrow">Core Capabilities</span><h2>{t("caps_title")}</h2>
  <p>{t("caps_text")}</p></div>
  <a class="btn btn-line" href="{P.url("services/")}">{t("all_services")} →</a></div>
  <div class="grid g3">{"".join(svc_card(P, s) for s in D.SERVICES)}</div>
</div></section>

<section class="dark"><div class="wrap">
  <div class="sec-head center"><span class="eyebrow">R&amp;D Process</span><h2>{t("process_title")}</h2>
  <p>{t("process_text")}</p></div>
  <ol class="process">{process_list(P)}</ol>
</div></section>

<section><div class="wrap split">
  <div class="photo reveal">{img(P.R, "about-solder", t("why_img_alt"))}</div>
  <div class="reveal">
    <span class="eyebrow">Why Balin</span><h2>{t("why_title")}</h2>
    <p class="lead-lg">{t("why_text")}</p>
    <ul class="checks two">{"".join(f"<li>{e(w)}</li>" for w in D.WHY)}</ul>
    <a class="btn btn-primary" href="{P.url("about.html")}">{t("why_btn")}</a>
  </div>
</div></section>

{section_gallery(P, "home", t("gallery_home"))}
<section class="soft"><div class="wrap">
  <div class="sec-head split"><div><span class="eyebrow">Applications</span><h2>{t("nav_applications")}</h2>
  <p>{t("apps_text")}</p></div>
  <a class="btn btn-line" href="{P.url("applications.html")}">{t("all_apps")} →</a></div>
  <div class="grid g3">{apps}</div>
</div></section>

<section class="dark"><div class="wrap">
  <div class="sec-head split"><div><span class="eyebrow">Tech Showcase</span><h2>{t("demos_title")}</h2>
  <p>{t("demos_text")}</p></div>
  <a class="btn btn-ghost" href="{P.url("demos.html")}">{t("demos_more")} →</a></div>
  <div class="grid g3">{"".join(demo_card(P, d) for d in D.DEMOS)}</div>
</div></section>

<section><div class="wrap">
  <div class="sec-head split"><div><span class="eyebrow">Insights</span><h2>{t("nav_insights")}</h2>
  <p>{t("insights_text")}</p></div>
  <a class="btn btn-line" href="{P.url("insights/")}">{t("all_articles")} →</a></div>
  <div class="grid g3">{"".join(article_card(P, a) for a in D.ARTICLES[:3])}</div>
</div></section>

{cta_band(P)}
{redirect}'''
    render(P, title=t("home_title"), desc=t("home_desc"), body=body, active="home",
           ld=[org_ld(P), {"@context": "https://schema.org", "@type": "WebSite", "name": C["name"], "url": SITE_URL + "/" + L.prefix, "inLanguage": L.html_lang}],
           priority="1.0")


def build_about(L):
    P = Page(L, "about.html")
    D, C, t = P.D, P.C, P.t
    crumbs = [(t("nav_about"), None)]
    rows = [("row_name", C["name"]), ("row_en", C["en"]), ("row_tax", C["tax_id"]), ("row_owner", C["owner"]),
            ("row_founded", C["founded"]), ("row_type", C["type"]), ("row_capital", C["capital"]), ("row_address", C["address"])]
    own_cover = bool(PH.get("about", {}).get("cover"))
    values = "".join(f'<div class="card reveal"><div class="body"><span class="icon-badge" style="position:static">{icon(ic)}</span><h3>{ti}</h3><p>{d}</p></div></div>' for ic, ti, d in D.VALUES)
    techs = "".join(f'<li><a href="{P.url("services/" + s["slug"] + ".html")}" style="color:#fff">{e(s["name"])}</a>　<span style="color:#9DB1C8">{e(s["summary"])}</span></li>' for s in D.SERVICES)
    body = f'''{page_hero(P, t("about_h1"), t("about_lead"), crumbs, bg=photo("about", "cover", "about-lab"), eyebrow="About Us")}
<section><div class="wrap split">
  <div class="reveal">
    <span class="eyebrow">Company Profile</span><h2>{t("profile_title")}</h2>
    <p class="lead-lg">{t("profile_p1", year=C["founded_year"])}</p>
    <p>{t("profile_p2")}</p>
    <p>{t("profile_p3")}</p>
  </div>
  <div class="photo reveal">{img(P.R, photo("about", "cover", "about-lab"), t("about_img_own") if own_cover else t("about_img_stock"))}</div>
</div></section>

<section class="soft"><div class="wrap">
  <div class="sec-head center"><span class="eyebrow">Core Values</span><h2>{t("values_title")}</h2></div>
  <div class="grid g3">{values}</div>
</div></section>

<section><div class="wrap split">
  <div class="reveal"><span class="eyebrow">Milestones</span><h2>{t("timeline_title")}</h2>
    <ol class="timeline">{"".join(f"<li><b>{y}</b><p>{e(x)}</p></li>" for y, x in D.TIMELINE)}</ol>
  </div>
  <div class="reveal"><span class="eyebrow">Company Info</span><h2>{t("info_title")}</h2>
    <table class="info">{"".join(f"<tr><th>{t(k)}</th><td>{e(v)}</td></tr>" for k, v in rows)}</table>
  </div>
</div></section>

{section_gallery(P, "about", t("gallery_about"), t("gallery_about_lead"), "soft")}
<section class="dark"><div class="wrap split">
  <div class="photo reveal">{img(P.R, "support", t("tech_img_alt"))}</div>
  <div class="reveal"><span class="eyebrow">What We Do</span><h2>{t("tech_title")}</h2>
    <p>{t("tech_text")}</p>
    <ul class="checks">{techs}</ul>
  </div>
</div></section>
{cta_band(P)}'''
    render(P, title=t("nav_about"), desc=t("about_desc", year=C["founded_year"]), body=body, active="about",
           ld=[breadcrumb_ld(P, crumbs)], priority="0.8")


def build_services(L):
    P = Page(L, "services/index.html")
    D, t = P.D, P.t
    crumbs = [(t("nav_services"), None)]
    body = f'''{page_hero(P, t("nav_services"), t("services_lead"), crumbs, bg="hero2", eyebrow="Products & Services")}
<section><div class="wrap"><div class="grid g3">{"".join(svc_card(P, s) for s in D.SERVICES)}</div></div></section>
<section class="dark"><div class="wrap">
  <div class="sec-head center"><span class="eyebrow">R&amp;D Process</span><h2>{t("process_title")}</h2></div>
  <ol class="process">{process_list(P)}</ol>
</div></section>
{cta_band(P, t("services_cta_title"), t("services_cta_text"))}'''
    render(P, title=t("nav_services"), desc=t("services_desc"), body=body, active="services",
           ld=[breadcrumb_ld(P, crumbs)], priority="0.9")

    for s in D.SERVICES:
        P = Page(L, f"services/{s['slug']}.html")
        crumbs = [(t("nav_services"), "services/"), (s["name"], None)]
        cur = ' aria-current="page"'
        others = "".join(f'<a href="{o["slug"]}.html"{cur if o is s else ""}>{e(o["name"])}<span>→</span></a>' for o in D.SERVICES)
        products = "".join(f'''<div class="product reveal">{img(P.R, photo(s["slug"], f"p{n}", p["img"]), p["name"])}
  <div><h3>{e(p["name"])}</h3>{tags(p["tags"])}<p>{e(p["desc"])}</p>
  <a class="btn btn-line btn-sm" href="{P.contact("product", p["name"])}">{t("ask_solution")}</a></div></div>''' for n, p in enumerate(s["products"], 1))
        related = [a for a in D.ARTICLES if a["service"] == s["slug"]]
        rel_html = ""
        if related:
            rel_html = f'<h2 style="margin-top:56px">{t("related_articles")}</h2><div class="grid g2">{"".join(article_card(P, a) for a in related)}</div>'
        apps = "".join(f'<a class="card reveal" href="{P.url("applications.html")}#{a["id"]}"><div class="body"><h3>{e(a["title"])}</h3><p>{e(a["challenge"])}</p><span class="more arrow">{t("see_solution")} </span></div></a>'
                       for a in D.APPLICATIONS if s["slug"] in a["tech"])
        body = f'''{page_hero(P, s["name"], s["summary"], crumbs, bg=photo(s["slug"], "cover", s["hero"]),
                          eyebrow="Products & Services" if same(s["en"], s["name"]) else s["en"])}
<section><div class="wrap svc-layout">
  <div>
    <p class="lead-lg reveal">{e(s["intro"])}</p>
    {tags(s["tags"])}
    <h2 style="margin-top:48px">{t("capabilities")}</h2>
    <ul class="checks two reveal">{"".join(f"<li>{e(c)}</li>" for c in s["capabilities"])}</ul>
    <h2 style="margin-top:56px">{t("solutions")}</h2>
    {products}
    <h2 style="margin-top:56px">{t("nav_applications")}</h2>
    <div class="grid g2">{apps}</div>
    <p class="muted" style="margin-top:16px">{t("other_apps")}{t("list_sep").join(s["apps"])}{t("period")}</p>
    {gallery(P, s["slug"], t("gallery_service"), t("gallery_service_lead"))}
    {rel_html}
  </div>
  <aside class="svc-aside">
    <div class="aside-box aside-cta"><h3>{t("aside_title", name=e(s["name"]))}</h3><p>{t("aside_text")}</p>
      <a class="btn" href="{P.contact("custom", s["name"])}">{t("cta_btn")}</a></div>
    <div class="aside-box"><h3>{t("all_services_short")}</h3><nav>{others}</nav></div>
  </aside>
</div></section>
{cta_band(P)}'''
        render(P, title=s["name"] if same(s["en"], s["name"]) else f"{s['name']}｜{s['en']}",
               desc=t("service_desc", name=s["name"], summary=s["summary"]), body=body, active="services",
               ld=[breadcrumb_ld(P, crumbs),
                   {"@context": "https://schema.org", "@type": "Service", "name": s["name"], "serviceType": s["en"],
                    "provider": {"@id": SITE_URL + "/#org"}, "areaServed": "Worldwide", "description": s["intro"]}],
               priority="0.8")


def build_applications(L):
    P = Page(L, "applications.html")
    D, t = P.D, P.t
    SVC = {s["slug"]: s for s in D.SERVICES}
    crumbs = [(t("nav_applications"), None)]
    rows = []
    for a in D.APPLICATIONS:
        techs = "".join(f'<li><a href="{P.url("services/" + x + ".html")}">{e(SVC[x]["name"])}</a></li>' for x in a["tech"])
        demo = f'<a class="btn btn-line btn-sm" href="{P.R}{a["demo"]}" target="_blank" rel="noopener">{t("open_related_demo")} ↗</a>' if a["demo"] else ""
        rows.append(f'''<article class="scenario reveal" id="{a["id"]}">
  <div class="photo">{img(P.R, a["img"], a["title"])}</div>
  <div><h2>{e(a["title"])}</h2>
  <dl><dt>{t("challenge")}</dt><dd>{e(a["challenge"])}</dd><dt>{t("solution")}</dt><dd>{e(a["solution"])}</dd></dl>
  <ul class="tags">{techs}</ul>
  <div style="display:flex;gap:10px;flex-wrap:wrap"><a class="btn btn-primary btn-sm" href="{P.contact("custom", a["title"])}">{t("discuss")}</a>{demo}</div></div>
</article>''')
    body = f'''{page_hero(P, t("nav_applications"), t("apps_lead"), crumbs, bg="p10", eyebrow="Applications")}
<section><div class="wrap">
  <p class="note" style="margin-bottom:32px">{t("apps_note")}</p>
  {"".join(rows)}
</div></section>
{cta_band(P, t("apps_cta_title"), t("apps_cta_text"))}'''
    render(P, title=t("nav_applications"), desc=t("apps_desc"), body=body, active="applications",
           ld=[breadcrumb_ld(P, crumbs)], priority="0.8")


def build_demos(L):
    P = Page(L, "demos.html")
    D, t = P.D, P.t
    crumbs = [(t("nav_demos"), None)]
    arch = "".join(f"<li><b>{k}</b>{v}</li>" for k, v in (x.split("|", 1) for x in t("arch_items").split("\n")))
    body = f'''{page_hero(P, t("demos_title"), t("demos_text"), crumbs, bg="demo-aiot", eyebrow="Tech Showcase")}
<section class="dark"><div class="wrap">
  <div class="grid g3">{"".join(demo_card(P, d) for d in D.DEMOS)}</div>
  <p class="note" style="color:#7F96B0;margin-top:24px">{t("demos_note")}</p>
</div></section>
<section><div class="wrap split">
  <div class="reveal"><span class="eyebrow">Architecture</span><h2>{t("arch_title")}</h2>
  <ul class="checks">{arch}</ul>
  <a class="btn btn-primary" href="{P.url("applications.html")}#monitoring">{t("arch_btn")}</a></div>
  <div class="photo reveal">{img(P.R, "demo-boiler", t("demo_boiler_alt"))}</div>
</div></section>
{cta_band(P, t("demos_cta_title"), t("demos_cta_text"))}'''
    render(P, title=t("demos_title"), desc=t("demos_desc"), body=body, active="demos",
           ld=[breadcrumb_ld(P, crumbs)], priority="0.7")


def expand_imgs(R, body):
    def rep(m):
        name, cap = (m.group(1).split("|") + [""])[:2]
        return f'<figure>{img(R, name, cap)}<figcaption>{e(cap)}</figcaption></figure>'
    return re.sub(r"\{img:([^}]+)\}", rep, body)


def build_insights(L):
    P = Page(L, "insights/index.html")
    D, t = P.D, P.t
    crumbs = [(t("nav_insights"), None)]
    note = f'<p class="note" style="margin-bottom:24px">{t("insights_note")}</p>' if t("insights_note") else ""
    body = f'''{page_hero(P, t("nav_insights"), t("insights_lead"), crumbs, bg="hero", eyebrow="Insights")}
<section><div class="wrap">{note}<div class="grid g3">{"".join(article_card(P, a) for a in D.ARTICLES)}</div></div></section>
{cta_band(P, t("insights_cta_title"), t("insights_cta_text"))}'''
    render(P, title=t("nav_insights"), desc=t("insights_desc"), body=body, active="insights",
           ld=[breadcrumb_ld(P, crumbs)], priority="0.7")

    SVC = {s["slug"]: s for s in D.SERVICES}
    for a in D.ARTICLES:
        P = Page(L, f"insights/{a['slug']}.html")
        crumbs = [(t("nav_insights"), "insights/"), (a["title"], None)]
        toc = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', a["body"])
        toc_html = (f'<nav class="toc" aria-label="{t("toc")}"><b>{t("toc")}</b><ol>' + "".join(
            f'<li><a href="#{i}">{x}</a></li>' for i, x in toc) + "</ol></nav>") if toc else ""
        s = SVC[a["service"]]
        more = [x for x in D.ARTICLES if x is not a][:3]
        body = f'''<section class="page-hero"><div class="wrap">
  <nav class="crumbs" aria-label="{t("breadcrumb")}"><a href="{P.url("index.html")}">{t("home")}</a><span>/</span><a href="./">{t("nav_insights")}</a></nav>
  <div class="post-meta" style="color:#9DB1C8"><span class="pill">{e(a["tag"])}</span><time datetime="{a["date"]}">{a["date"].replace("-", ".")}</time><span>{t("author")}</span></div>
  <h1>{e(a["title"])}</h1><p>{e(a["excerpt"])}</p>
</div></section>
<section><div class="wrap">
  <article class="article">
    <figure style="margin-top:0">{img(P.R, a["img"], a["title"], lazy=False)}<figcaption>{t("illustrative")}</figcaption></figure>
    {toc_html}
    {expand_imgs(P.R, a["body"])}
    <hr style="border:0;border-top:1px solid var(--line);margin:48px 0 24px">
    <p class="muted">{t("article_disclaimer")}<a href="{P.url("services/" + s["slug"] + ".html")}">{e(s["name"])}</a></p>
  </article>
</div></section>
<section class="soft"><div class="wrap"><div class="sec-head"><h2>{t("further_reading")}</h2></div>
<div class="grid g3">{"".join(article_card(P, x) for x in more)}</div></div></section>
{cta_band(P)}'''
        render(P, title=a["title"], desc=a["excerpt"], body=body, active="insights", og_type="article",
               og_img=f'{a["img"]}.webp',
               ld=[breadcrumb_ld(P, crumbs),
                   {"@context": "https://schema.org", "@type": "TechArticle", "headline": a["title"], "description": a["excerpt"],
                    "datePublished": a["date"], "inLanguage": L.html_lang, "image": f'{SITE_URL}/assets/img/{a["img"]}.webp',
                    "author": {"@type": "Organization", "name": P.C["name"]}, "publisher": {"@id": SITE_URL + "/#org"}}],
               priority="0.6")


def build_support(L):
    P = Page(L, "support.html")
    D, t = P.D, P.t
    crumbs = [(t("nav_support"), None)]
    steps = "".join(f'<div class="card reveal"><div class="body"><span class="card-en">STEP {i:02d}</span><h3>{x}</h3><p>{d}</p></div></div>'
                    for i, (x, d) in enumerate(D.SUPPORT_STEPS, 1))
    models = "".join(f'''<div class="card reveal"><div class="body"><span class="icon-badge" style="position:static">{icon(ic)}</span>
  <h3>{x}</h3><p>{d}</p><ul class="checks">{"".join(f"<li>{y}</li>" for y in pts)}</ul></div></div>'''
                     for (x, d, pts), ic in zip(D.MODELS, ["users", "tool", "factory"]))
    docs = "".join(f'''<div class="card reveal"><div class="body"><span class="icon-badge" style="position:static">{icon("doc")}</span>
  <h3>{x}</h3><p>{d}</p><a class="more arrow" href="{P.contact("support", x)}">{t("request_doc")} </a></div></div>''' for x, d in D.DOCS)
    faqs = "".join(f"<details><summary>{e(q)}</summary><div><p>{e(a)}</p></div></details>" for q, a in D.FAQS)
    body = f'''{page_hero(P, t("nav_support"), t("support_lead"), crumbs, bg="support", eyebrow="Support")}
<section><div class="wrap">
  <div class="sec-head"><span class="eyebrow">Service Flow</span><h2>{t("flow_title")}</h2></div>
  <div class="grid g4">{steps}</div>
</div></section>
<section class="soft"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">Engagement</span><h2>{t("models_title")}</h2><p>{t("models_text")}</p></div>
  <div class="grid g3">{models}</div>
</div></section>
<section><div class="wrap">
  <div class="sec-head"><span class="eyebrow">Documents</span><h2>{t("docs_title")}</h2><p>{t("docs_text")}</p></div>
  <div class="grid g4">{docs}</div>
</div></section>
<section class="soft"><div class="wrap">
  <div class="sec-head center"><span class="eyebrow">FAQ</span><h2>{t("faq_title")}</h2></div>
  <div class="faq">{faqs}</div>
</div></section>
{cta_band(P, t("support_cta_title"), t("support_cta_text"))}'''
    render(P, title=t("nav_support"), desc=t("support_desc"), body=body, active="support", priority="0.7",
           ld=[breadcrumb_ld(P, crumbs),
               {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                   {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in D.FAQS]}])


def build_contact(L):
    P = Page(L, "contact.html")
    C, t = P.C, P.t
    crumbs = [(t("nav_contact"), None)]
    q = e(i18n.BASE.data.COMPANY["address"])  # 地圖一律用中文地址查詢，定位最準
    opts = "".join(f'<option value="{v}" data-k="{k}">{t("subj_" + k)}</option>' for k, v in SUBJECTS)
    note = f'<p class="lang-note">{t("contact_lang_note")}</p>' if t("contact_lang_note") else ""
    body = f'''{page_hero(P, t("nav_contact"), t("contact_lead"), crumbs, eyebrow="Contact")}
<section><div class="wrap contact-grid">
  <div>
    <h2>{t("contact_info")}</h2>
    <ul class="contact-list">
      <li><span class="icon-badge">{icon("phone")}</span><div><small>{t("label_phone")}</small><a href="tel:{C["phone_intl"]}">{C["phone_display"]}</a></div></li>
      <li><span class="icon-badge">{icon("mail")}</span><div><small>{t("label_email")}</small><a href="mailto:{C["email"]}">{C["email"]}</a></div></li>
      <li><span class="icon-badge">{icon("map")}</span><div><small>{t("label_address")}</small><span>{C["address"]}</span></div></li>
      <li><span class="icon-badge">{icon("clock")}</span><div><small>{t("label_hours")}</small><span>{C["hours"]}</span></div></li>
    </ul>
    <div class="map"><iframe title="{t("map_title")}" loading="lazy" referrerpolicy="no-referrer-when-downgrade"
      src="https://www.google.com/maps?q={q}&amp;output=embed&amp;hl={L.map_hl}"></iframe></div>
    <p style="margin-top:12px"><a href="https://www.google.com/maps/dir/?api=1&amp;destination={q}" target="_blank" rel="noopener">{t("map_route")} ↗</a></p>
  </div>
  <div class="form-card">
    <h2>{t("form_title")}</h2>
    <p class="muted">{t("form_lead")}</p>
    {note}
    <form id="contact-form" action="{C["form_endpoint"]}" method="post" novalidate
      data-email="{C["email"]}" data-phone="{C["phone_display"]}" data-sending="{t("form_sending")}"
      data-submit="{t("form_submit")}" data-ok="{e(t("form_ok"))}" data-err="{e(t("form_err"))}" data-ref="{e(t("form_ref"))}">
      <div class="form-grid">
        <div><label for="f-name">{t("f_name")} <span class="req">*</span></label><input id="f-name" name="姓名" required autocomplete="name"></div>
        <div><label for="f-company">{t("f_company")}</label><input id="f-company" name="公司" autocomplete="organization"></div>
        <div><label for="f-email">{t("f_email")} <span class="req">*</span></label><input id="f-email" name="email" type="email" required autocomplete="email"></div>
        <div><label for="f-phone">{t("f_phone")}</label><input id="f-phone" name="電話" type="tel" autocomplete="tel"></div>
        <div class="full"><label for="f-subject">{t("f_subject")}</label><select id="f-subject" name="諮詢主題">{opts}</select></div>
        <div class="full"><label for="f-msg">{t("f_msg")} <span class="req">*</span></label><textarea id="f-msg" name="需求說明" required placeholder="{e(t("f_msg_ph"))}"></textarea></div>
        <input type="hidden" name="access_key" value="{C["form_key"]}">
        <input type="hidden" name="from_name" value="八麟光電官網">
        <input type="hidden" name="網站語言" value="{L.label}">
        <input class="hp" type="checkbox" name="botcheck" tabindex="-1" autocomplete="off" aria-hidden="true">
        <div class="full"><button class="btn btn-primary" type="submit">{t("form_submit")}</button>
        <p class="form-note">{t("form_privacy")}</p>
        <div class="form-status" role="status" hidden></div></div>
      </div>
    </form>
  </div>
</div></section>'''
    render(P, title=t("nav_contact"), desc=t("contact_desc", phone=C["phone_display"], address=C["address"]), body=body,
           active="contact", ld=[breadcrumb_ld(P, crumbs), org_ld(P)], priority="0.8")


def used_images():
    used = set()
    for dp, _, fs in os.walk(ROOT):
        if ".git" in dp or "tools" in dp:
            continue
        for f in fs:
            if f.endswith(".html") and f != "credits.html":
                used.update(re.findall(r'assets/img/([\w-]+)\.webp', open(os.path.join(dp, f), encoding="utf-8").read()))
    return used


def build_credits(L, used):
    P = Page(L, "credits.html")
    t = P.t
    rows = "".join(
        f'<tr><td><img src="{P.R}assets/img/{k}.webp" alt="" width="96" loading="lazy" style="border-radius:6px"></td>'
        f'<td><a href="{e(v["page"])}" target="_blank" rel="noopener">{e(v["title"].replace("File:", ""))}</a></td>'
        f'<td>{e(html.unescape(v["artist"])) or "—"}</td><td>{e(v["license"])}</td></tr>'
        for k, v in CREDITS.items() if k in used)
    body = f'''{page_hero(P, t("credits_title"), t("credits_lead"), [(t("credits_title"), None)])}
<section><div class="wrap">
  <p>{t("credits_text")}</p>
  <div class="table-scroll article" style="max-width:none"><table class="credits"><tr><th>{t("cr_preview")}</th><th>{t("cr_file")}</th><th>{t("cr_author")}</th><th>{t("cr_license")}</th></tr>{rows}</table></div>
</div></section>'''
    render(P, title=t("credits_title"), desc=t("credits_lead"), body=body, priority="0.2")


def build_404():
    """404 頁可能出現在任何路徑下，所以用根目錄絕對路徑，並同時列出各語言。"""
    L = i18n.BASE
    P = Page(L, "404.html")
    blocks = "".join(f'<p lang="{o.html_lang}" style="margin:0 0 6px">{o.t("nf_text")} <a href="/{o.prefix}" style="color:#6CC8FF">{o.t("nf_home")} →</a></p>'
                     for o in i18n.LANGS)
    body = f'''<section class="page-hero" style="min-height:60vh;display:grid;align-items:center"><div class="wrap">
  <span class="eyebrow">404</span><h1>{L.t("nf_title")} · Page not found</h1>
  <div style="margin-top:20px">{blocks}</div>
</div></section>'''
    render(P, title=L.t("nf_title"), desc=L.t("nf_title"), body=body, in_sitemap=False)
    p = os.path.join(ROOT, "404.html")
    s = open(p, encoding="utf-8").read()
    s = re.sub(r'(href|src)="(?!https?:|/|#|mailto:|tel:)', r'\1="/', s)
    s = re.sub(r'href="/((?:[a-z-]+/)?)404\.html"', r'href="/\1"', s)  # 語言切換改指向各語言首頁
    open(p, "w", encoding="utf-8", newline="\n").write(s)


def build_meta_files():
    urls = "".join(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod><priority>{p}</priority></url>\n" for u, p in PAGES)
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8", newline="\n").write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8", newline="\n").write(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")


if __name__ == "__main__":
    PH.update(photos.load())
    for L in i18n.LANGS:
        n = len(PAGES)
        build_home(L)
        build_about(L)
        build_services(L)
        build_applications(L)
        build_demos(L)
        build_insights(L)
        build_support(L)
        build_contact(L)
        print(f"   {L.label:<8} /{L.prefix:<7} {len(PAGES) - n} 頁")
    build_404()
    used = used_images()
    for L in i18n.LANGS:
        build_credits(L, used)  # 最後產生，只列出實際使用中的圖片
    build_meta_files()
    missing = i18n.report_missing()
    print(f"完成，共 {len(PAGES)} 頁列入 sitemap。{missing}")
