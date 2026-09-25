# 八麟光電官網

https://www.balinedge.com.tw — GitHub Pages 靜態網站（repo：`bv6mk2002/official-website`）

## 修改內容

所有頁面由 `tools/build.py` 產生，**不要直接改 HTML**，改完會被覆蓋。

1. 修改內容：編輯 `tools/content.py`（公司資料、服務項目、應用場域、FAQ、技術專欄文章）
2. 重新產生頁面（需要 Python 3 與 Pillow）：

   ```
   python tools/build.py
   ```

3. 本機預覽：`python -m http.server 8000`，開啟 http://localhost:8000
4. 確認無誤後 commit 並 push，GitHub Pages 約 1 分鐘內更新

## 結構

| 路徑 | 說明 |
|---|---|
| `index.html`、`about.html`… | 產生出來的頁面 |
| `services/` | 六大服務頁 |
| `insights/` | 技術專欄文章 |
| `en/` | 英文簡介頁 |
| `assets/css/style.css` | 全站樣式 |
| `assets/js/main.js` | 選單、表單等互動 |
| `assets/img/` | 圖片（WebP）、標誌、分享預覽圖 |
| `*dashboard.html` | 即時監測展示（獨立頁面，不由 build.py 產生） |
| `tools/credits.json` | 開放授權圖片的來源與授權資訊 |

## 新增技術文章

在 `tools/content.py` 的 `ARTICLES` 加一筆，圖片放到 `assets/img/`（WebP 格式），再執行 `build.py`。
使用 Wikimedia Commons 等開放授權圖片時，請一併加入 `tools/credits.json`，會自動列在「圖片來源與授權」頁。

## 表單

聯絡表單透過 formsubmit.co 寄到公司信箱。第一次有人送出表單時，formsubmit 會寄一封啟用信，點擊連結後才會開始轉寄。
