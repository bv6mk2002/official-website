# 八麟光電官網

https://www.balinedge.com.tw — GitHub Pages 靜態網站（repo：`bv6mk2002/official-website`）

## 修改內容

所有頁面由 `tools/build.py` 產生，**不要直接改 HTML**，改完會被覆蓋。

1. 修改內容：編輯 `tools/content.py`（公司資料、服務項目、應用場域、FAQ、技術專欄文章）
2. 重新產生頁面（需要 Python 3、Pillow、opencc-python-reimplemented）：

   ```
   python tools/make_zh_cn.py   # 繁體改過時，重新產生簡體中文
   python tools/build.py
   ```

3. 本機預覽：`python -m http.server 8000`，開啟 http://localhost:8000
4. 確認無誤後 commit 並 push，GitHub Pages 約 1 分鐘內更新

## 多語言

| 語言 | 網址 | 內容檔 |
|---|---|---|
| 繁體中文（主檔） | `/` | `tools/content.py`、`tools/i18n/zh_tw.py`（介面文字） |
| English | `/en/` | `tools/i18n/en.py` |
| 日本語 | `/ja/` | `tools/i18n/ja.py` |
| Deutsch | `/de/` | `tools/i18n/de.py` |
| Русский | `/ru/` | `tools/i18n/ru.py` |
| 简体中文 | `/zh-cn/` | `tools/i18n/zh_cn.py`（由 `make_zh_cn.py` 自動產生，勿手改） |

- 外語檔只寫翻譯文字；圖片、連結、代號自動沿用主檔。清單項目（服務、應用、文章…）的數量與順序必須和主檔一致。
- **修改中文內容後，記得同步修改英、日、德、俄四個檔案**，否則外語版仍是舊內容。新增文章時，四個外語檔也要各加一篇。
- 介面文字缺翻譯時，build 會用英文暫代並列出缺少的 key。
- 聯絡表單不論訪客語言，寄到公司的主旨一律是中文，並附上「網站語言」欄位。
- 新增語言：在 `tools/i18n/__init__.py` 的 `LANG_TABLE` 加一行，再新增對應的翻譯檔。

## 結構

| 路徑 | 說明 |
|---|---|
| `index.html`、`about.html`… | 產生出來的頁面 |
| `services/` | 六大服務頁 |
| `insights/` | 技術專欄文章 |
| `en/`、`ja/`、`de/`、`ru/`、`zh-cn/` | 各語言版本（結構與中文版相同） |
| `assets/css/style.css` | 全站樣式 |
| `assets/js/main.js` | 選單、表單等互動 |
| `calculators.html`、`assets/js/calc.js` | 工程工具（LoRa 鏈路預算、電池續航試算）；頁面文字在各語言檔的 `l_*`、`b_*`、`r_*` 等 key，計算在 calc.js |
| `assets/img/` | 圖片（WebP）、標誌、分享預覽圖 |
| `*dashboard.html` | 即時監測展示（獨立頁面，不由 build.py 產生） |
| `tools/credits.json` | 開放授權圖片的來源與授權資訊 |

## 照片庫

自家照片放在 site 資料夾「外面」的 `../照片庫/<分類>/`，執行 `build.py` 時會自動轉正方向、縮圖、轉成 WebP、移除 EXIF（含 GPS），
輸出到 `assets/img/photos/`，並取代對應的示意圖。原始照片不進 git。規則詳見 `../照片庫/使用說明.txt`，程式在 `tools/photos.py`。

## 新增技術文章

在 `tools/content.py` 的 `ARTICLES` 加一筆，圖片放到 `assets/img/`（WebP 格式），再執行 `build.py`。
使用 Wikimedia Commons 等開放授權圖片時，請一併加入 `tools/credits.json`，會自動列在「圖片來源與授權」頁。

## 表單

聯絡表單透過 Web3Forms（https://web3forms.com）寄到公司信箱，免費方案每月 250 封。
金鑰設定在 `tools/content.py` 的 `COMPANY["form_key"]`。
選擇「產品諮詢／客製化開發」時會顯示「專案資訊」問卷（`build.py` 的 `QUESTIONS`），答案一律以繁體中文附在信件內文最後。金鑰本來就會出現在網頁上，不是機密；
要換收件信箱，請到 web3forms.com 用新信箱重新申請金鑰並替換。
