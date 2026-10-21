// 八麟光電科技 — 官網互動
(function () {
  var body = document.body;

  // ---------------------------------------------------------------
  // 自動語系：依訪客瀏覽器語言
  //   - 第一次打開中文首頁 → 自動轉到對應語言首頁
  //   - 其他頁面 → 頂端顯示「本頁有 ○○ 語版」提示
  //   - 訪客手動切換語言或關掉提示後記住選擇，不再干擾
  //   - 搜尋引擎爬蟲不處理，避免影響收錄
  // ---------------------------------------------------------------
  (function autoLang() {
    var KEY = 'balin-lang';
    var store = {
      get: function () { try { return localStorage.getItem(KEY); } catch (e) { return null; } },
      set: function (v) { try { localStorage.setItem(KEY, v); } catch (e) {} }
    };
    // 語言切換選單裡的連結（相對路徑，指向「本頁」的各語言版本）
    var links = {};
    var current = null;
    document.querySelectorAll('.lang-dd .dd-menu a[hreflang]').forEach(function (a) {
      links[a.getAttribute('hreflang')] = a;
      if (a.hasAttribute('aria-current')) current = a.getAttribute('hreflang');
      // 訪客手動選語言 → 記住
      a.addEventListener('click', function () { store.set(a.getAttribute('hreflang')); });
    });
    if (!current || /bot|crawl|spider|slurp|baidu|yandex|duckduck|facebookexternalhit|lighthouse|headless/i.test(navigator.userAgent)) return;

    function detect() {
      var list = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || ''];
      for (var i = 0; i < list.length; i++) {
        var l = (list[i] || '').toLowerCase();
        if (l.indexOf('zh') === 0) return /hant|tw|hk|mo/.test(l) ? 'zh-TW' : 'zh-CN';
        if (l.indexOf('ja') === 0) return 'ja';
        if (l.indexOf('de') === 0) return 'de';
        if (l.indexOf('ru') === 0) return 'ru';
        if (l.indexOf('en') === 0) return 'en';
      }
      return 'en';  // 其他語言的訪客先看英文
    }
    var target = store.get() || detect();
    if (target === current || !links[target]) return;

    // 中文首頁（網站入口）→ 直接轉到對應語言首頁
    var path = location.pathname.replace(/\/index\.html$/, '/');
    if (current === 'zh-TW' && path === '/' && !location.hash) {
      store.set(target);
      location.replace(links[target].href.replace(/index\.html$/, ''));
      return;
    }

    // 其他頁面 → 用訪客的語言顯示切換提示
    var MSG = {
      'zh-TW': ['本頁提供繁體中文版。', '切換為繁體中文'],
      'zh-CN': ['本页提供简体中文版。', '切换为简体中文'],
      'en': ['This page is also available in English.', 'View in English'],
      'ja': ['このページは日本語でもご覧いただけます。', '日本語で見る'],
      'de': ['Diese Seite gibt es auch auf Deutsch.', 'Auf Deutsch lesen'],
      'ru': ['Эта страница доступна на русском языке.', 'Читать на русском']
    };
    var m = MSG[target];
    var bar = document.createElement('div');
    bar.className = 'lang-bar';
    bar.setAttribute('lang', links[target].getAttribute('lang') || target);
    bar.innerHTML = '<div class="wrap"><span></span><a class="btn btn-primary btn-sm"></a>' +
                    '<button type="button" aria-label="×">×</button></div>';
    bar.querySelector('span').textContent = m[0];
    var go = bar.querySelector('a');
    go.textContent = m[1];
    go.href = links[target].href;
    go.addEventListener('click', function () { store.set(target); });
    bar.querySelector('button').addEventListener('click', function () {
      store.set(current);  // 關掉提示 = 選擇留在目前語言
      bar.remove();
    });
    body.insertBefore(bar, body.firstChild);
  })();

  // 手機選單
  var toggle = document.querySelector('.menu-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var open = body.classList.toggle('nav-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // 下拉選單（觸控與鍵盤）
  document.querySelectorAll('.dd > button').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var dd = btn.parentElement;
      var open = dd.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  });
  document.addEventListener('click', function (e) {
    document.querySelectorAll('.dd.open').forEach(function (dd) {
      if (!dd.contains(e.target) && window.innerWidth > 1080) dd.classList.remove('open');
    });
  });

  // 捲動淡入
  var items = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add('in'); });
  }

  // 相簿點擊放大
  var links = document.querySelectorAll('a[data-lightbox]');
  if (links.length && window.HTMLDialogElement) {
    var dlg = document.createElement('dialog');
    dlg.className = 'lightbox';
    dlg.innerHTML = '<button type="button">×</button><img alt=""><p></p>';
    dlg.querySelector('button').setAttribute('aria-label', body.dataset.close || 'Close');
    document.body.appendChild(dlg);
    dlg.querySelector('button').addEventListener('click', function () { dlg.close(); });
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
    links.forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        var cap = a.parentElement.querySelector('figcaption');
        dlg.querySelector('img').src = a.href;
        dlg.querySelector('img').alt = a.querySelector('img').alt;
        dlg.querySelector('p').textContent = cap ? cap.textContent : '';
        dlg.showModal();
      });
    });
  }

  // 聯絡表單：從網址帶入諮詢主題（contact.html?subject=support&ref=產品型錄）
  // 介面文字由頁面的 data-* 屬性提供，各語言版本共用這支程式
  var form = document.getElementById('contact-form');
  if (!form) return;
  var params = new URLSearchParams(location.search);
  var subj = params.get('subject');
  if (subj) {
    var sel = form.querySelector('[name="諮詢主題"]');
    var opt = Array.prototype.find.call(sel.options, function (o) { return o.dataset.k === subj || o.value === subj; });
    if (opt) sel.value = opt.value;
    var ref = params.get('ref');
    if (ref) form.querySelector('[name="需求說明"]').value = form.dataset.ref + ref + '\n\n';
  }

  var status = form.querySelector('.form-status');
  var btn = form.querySelector('button[type="submit"]');
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (!form.reportValidity()) return;
    var data = {};
    new FormData(form).forEach(function (v, k) { data[k] = v; });
    if (data.botcheck) return;  // 機器人陷阱欄位被勾選就不送
    // 信件主旨一律中文；外語版加註訪客使用的語言
    var lang = data['網站語言'];
    var subject = '官網諮詢：' + (data['諮詢主題'] || '') + (lang && lang !== '繁體中文' ? '（' + lang + '）' : '');
    // Web3Forms 會把中文「欄位名稱」解成亂碼（內容正常），所以只用英文欄位名稱，
    // 並把所有資料整理成一段有中文標籤的內文放進 message
    var message = [
      '姓名：' + (data['姓名'] || ''),
      '公司：' + (data['公司'] || ''),
      '電子信箱：' + (data.email || ''),
      '聯絡電話：' + (data['電話'] || ''),
      '諮詢主題：' + (data['諮詢主題'] || ''),
      '網站語言：' + (lang || ''),
      '',
      '需求說明：',
      data['需求說明'] || ''
    ].join('\n');
    btn.disabled = true; btn.textContent = form.dataset.sending;
    status.hidden = true;
    // 用 FormData 送出（瀏覽器的「簡單請求」，不需 CORS 預檢）
    var body = new FormData();
    body.append('access_key', data.access_key);
    body.append('subject', subject);
    body.append('from_name', data.from_name || '八麟光電官網');
    body.append('name', data['姓名'] || '');
    body.append('email', data.email || '');  // Web3Forms 會設為回覆對象，直接按「回覆」即可回信給客戶
    body.append('message', message);
    fetch(form.action, {
      method: 'POST',
      headers: { Accept: 'application/json' },
      body: body
    }).then(function (r) {
      // 失敗時服務也會回 JSON 說明原因，所以不論狀態碼都讀內容
      return r.json().catch(function () { return {}; }).then(function (res) {
        if (!r.ok || String(res.success) !== 'true') throw new Error(res.message || ('HTTP ' + r.status));
      });
    }).then(function () {
      form.reset();
      status.className = 'form-status ok';
      status.textContent = form.dataset.ok;
    }).catch(function (err) {
      if (window.console) console.warn('contact form:', err && err.message);
      status.className = 'form-status err';
      var mail = '<a href="mailto:' + form.dataset.email + '">' + form.dataset.email + '</a>';
      status.innerHTML = form.dataset.err.replace('{email}', mail).replace('{phone}', form.dataset.phone);
    }).finally(function () {
      status.hidden = false;
      btn.disabled = false; btn.textContent = form.dataset.submit;
    });
  });
})();
