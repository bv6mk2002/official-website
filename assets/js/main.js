// 八麟光電科技 — 官網互動
(function () {
  var body = document.body;

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
    delete data.botcheck;
    // 信件主旨一律中文；外語版加註訪客使用的語言
    var lang = data['網站語言'];
    data.subject = '官網諮詢：' + (data['諮詢主題'] || '') + (lang && lang !== '繁體中文' ? '（' + lang + '）' : '');
    btn.disabled = true; btn.textContent = form.dataset.sending;
    status.hidden = true;
    // 用 FormData 送出（瀏覽器的「簡單請求」，不需 CORS 預檢）
    var body = new FormData();
    Object.keys(data).forEach(function (k) { body.append(k, data[k]); });
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
