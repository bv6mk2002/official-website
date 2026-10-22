// 八麟光電科技 — 工程計算工具（LoRa 鏈路預算、電池續航）
// 介面文字都在 HTML 裡（由 build.py 依語言產生），這支程式只負責計算與填數字
(function () {
  var lang = document.documentElement.lang || 'en';
  function $(id) { return document.getElementById(id); }
  function v(id) { var x = parseFloat($(id).value); return isFinite(x) ? x : 0; }
  function fmt(x, d) {
    if (!isFinite(x)) return '–';
    return new Intl.NumberFormat(lang, { maximumFractionDigits: d, minimumFractionDigits: d }).format(x);
  }
  function set(id, text) { $(id).value = text; $(id).textContent = text; }
  function ask(box, text) {
    var a = box.querySelector('.calc-ask');
    a.href = a.getAttribute('href').split('&')[0] + '&ref=' + encodeURIComponent(box.dataset.ref + (/^(zh|ja)/.test(lang) ? '：' : ': ') + text);
  }

  // -------------------------------------------------------------
  // LoRa
  // -------------------------------------------------------------
  var SNR = { 7: -7.5, 8: -10, 9: -12.5, 10: -15, 11: -17.5, 12: -20 };  // 各 SF 解調所需 SNR（Semtech）
  var toa = 0;

  function lora() {
    var sf = v('l-sf'), bw = v('l-bw') * 1000, cr = v('l-cr'), f = v('l-freq'), pl = Math.round(v('l-payload'));
    var sens = -174 + 10 * Math.log10(bw) + v('l-nf') + SNR[sf];
    var budget = v('l-ptx') + v('l-gtx') + v('l-grx') - v('l-loss') - sens;
    var maxPl = budget - v('l-margin');
    // 對數距離路徑損耗：PL(d) = FSPL(1 m) + 10·n·log10(d)
    var n = v('l-env');
    var fspl1m = 20 * Math.log10(f) - 27.55;
    var d = Math.pow(10, (maxPl - fspl1m) / (10 * n));  // 公尺

    // 空中時間（Semtech SX127x，前導碼 8、顯式標頭、CRC 開）
    var tsym = Math.pow(2, sf) / bw * 1000;  // ms
    var de = tsym > 16 ? 1 : 0;
    var nPay = 8 + Math.max(Math.ceil((8 * pl - 4 * sf + 28 + 16) / (4 * (sf - 2 * de))) * (cr + 4), 0);
    toa = (8 + 4.25) * tsym + nPay * tsym;
    var rate = sf * bw / Math.pow(2, sf) * 4 / (4 + cr);

    set('o-sens', fmt(sens, 1));
    set('o-budget', fmt(budget, 1));
    set('o-pl', fmt(maxPl, 1));
    set('o-dist', d >= 1000 ? fmt(d / 1000, d >= 10000 ? 0 : 1) + ' km' : fmt(d, 0) + ' m');
    set('o-toa', fmt(toa, 1));
    set('o-rate', fmt(rate, 0));
    set('o-duty', fmt(Math.floor(36000 / toa), 0));
    $('o-far').hidden = d < 30000;
    ask($('lora'), 'SF' + sf + ' / ' + bw / 1000 + ' kHz / CR 4/' + (cr + 4) + ' / ' + f + ' MHz / ' +
      v('l-ptx') + ' dBm / ' + pl + ' bytes → ' + fmt(budget, 1) + ' dB, ' + $('o-dist').textContent + ', ' + fmt(toa, 1) + ' ms');
  }

  // -------------------------------------------------------------
  // 電池續航
  // -------------------------------------------------------------
  function battery() {
    var box = $('battery');
    var period = Math.max(v('b-interval') * 60, 0.001);           // 秒
    var tAct = Math.max(v('b-active-t'), 0), tTx = Math.max(v('b-tx-t'), 0) / 1000;
    var tSleep = Math.max(period - tAct - tTx, 0);
    var qSleep = v('b-sleep') / 1000 * tSleep;                     // mA·s
    var qAct = v('b-active-i') * tAct, qTx = v('b-tx-i') * tTx;
    var q = qSleep + qAct + qTx;
    var avg = q / period;                                          // mA
    var daily = avg * 24;                                          // mAh／天
    var cap = v('b-cap');
    var usable = cap * Math.min(v('b-usable'), 100) / 100;
    var days = usable / (daily + cap * v('b-sd') / 100 / 365);     // 自放電依額定容量計

    set('o-avg', fmt(avg, avg < 0.1 ? 4 : avg < 10 ? 3 : 1));
    set('o-daily', fmt(daily, daily < 10 ? 2 : 1));
    var life = !isFinite(days) ? '–' : days >= 365 ? fmt(days / 365, 1) + ' ' + box.dataset.years : fmt(days, 0) + ' ' + box.dataset.days;
    set('o-life', life);
    var parts = { sleep: qSleep, active: qAct, tx: qTx };
    Object.keys(parts).forEach(function (k) {
      var p = q > 0 ? parts[k] / q * 100 : 0;
      box.querySelector('.share-bar .s-' + k).style.width = p + '%';
      set('o-share-' + k, fmt(p, p < 10 ? 1 : 0) + '%');
    });
    ask(box, fmt(cap, 0) + ' mAh × ' + v('b-usable') + '% / ' + v('b-interval') + ' min / ' + v('b-sleep') + ' µA · ' +
      v('b-active-i') + ' mA × ' + v('b-active-t') + ' s · ' + v('b-tx-i') + ' mA × ' + v('b-tx-t') + ' ms → ' + $('o-avg').textContent + ' mA, ' + life);
  }

  document.querySelectorAll('#lora input, #lora select').forEach(function (el) { el.addEventListener('input', lora); });
  document.querySelectorAll('#battery input').forEach(function (el) { el.addEventListener('input', battery); });
  $('b-use-toa').addEventListener('click', function () {
    $('b-tx-t').value = Math.round(toa * 10) / 10;
    battery();
  });
  lora();
  battery();
})();
