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
    dlg.innerHTML = '<button type="button" aria-label="關閉">×</button><img alt=""><p></p>';
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

  // 聯絡表單：從網址帶入諮詢主題（contact.html?subject=技術文件索取）
  var form = document.getElementById('contact-form');
  if (!form) return;
  var params = new URLSearchParams(location.search);
  var subj = params.get('subject');
  if (subj) {
    var sel = form.querySelector('[name="諮詢主題"]');
    var opt = Array.prototype.find.call(sel.options, function (o) { return o.value === subj; });
    if (opt) sel.value = subj;
    var ref = params.get('ref');
    if (ref) form.querySelector('[name="需求說明"]').value = '我想索取／了解：' + ref + '\n\n';
  }

  var status = form.querySelector('.form-status');
  var btn = form.querySelector('button[type="submit"]');
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (!form.reportValidity()) return;
    var data = {};
    new FormData(form).forEach(function (v, k) { data[k] = v; });
    if (data._honey) return;
    data._subject = '官網諮詢：' + (data['諮詢主題'] || '');
    btn.disabled = true; btn.textContent = '送出中…';
    status.hidden = true;
    fetch(form.action, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(data)
    }).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      form.reset();
      status.className = 'form-status ok';
      status.textContent = '感謝您的來信！我們已收到訊息，將於 1 個工作天內與您聯繫。';
    }).catch(function () {
      status.className = 'form-status err';
      status.innerHTML = '送出失敗，可能是網路問題。請直接來信 <a href="mailto:' + form.dataset.email + '">' + form.dataset.email + '</a> 或致電 ' + form.dataset.phone + '。';
    }).finally(function () {
      status.hidden = false;
      btn.disabled = false; btn.textContent = '送出諮詢';
    });
  });
})();
