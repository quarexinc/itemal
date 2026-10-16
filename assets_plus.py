"""Mağaza+ için ek CSS ve JS (style.css / app.js sonuna eklenir)."""

CSS = r"""
/* ---- Mağaza+ ---- */
.slug-box{display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:12px 14px;border:1px dashed var(--line-2);border-radius:12px;background:var(--bg-2)}
.slug-link{flex:1;min-width:200px;font-size:1.05rem;overflow-wrap:anywhere}
.slug-link b{color:var(--p-2)}
.pre-addon{display:inline-flex;align-items:center;padding:0 12px;border:1px solid var(--line-2);border-right:0;border-radius:10px 0 0 10px;background:var(--card-2);color:var(--muted);font-size:.9rem;white-space:nowrap}
.slug-field .input-btn input{border-radius:0 10px 10px 0}
.theme-sws{display:flex;gap:10px;flex-wrap:wrap}
.theme-sw{position:relative;display:flex;align-items:center;gap:8px;padding:8px 12px;border:1px solid var(--line-2);border-radius:999px;cursor:pointer;background:var(--card);font-size:.86rem;transition:border-color .15s}
.theme-sw input{position:absolute;opacity:0;pointer-events:none}
.theme-sw i{width:16px;height:16px;border-radius:50%;display:block;box-shadow:0 0 0 2px rgba(255,255,255,.12) inset}
.theme-sw:has(input:checked){border-color:var(--p-2);background:var(--p-soft)}
.theme-sw:has(input:focus-visible){outline:2px solid var(--p-2);outline-offset:2px}
.goal-bar .meter{height:10px;margin-bottom:8px}
.goal-card{display:grid;gap:10px}
.goal-card .meter{height:10px}
.store-notice{display:flex;gap:10px;align-items:center;padding:11px 16px;border-radius:12px;border:1px solid var(--p-soft);background:var(--p-soft);color:#fff;margin-bottom:14px;font-weight:500}
.store-vac{display:flex;gap:10px;align-items:center;padding:12px 16px;border-radius:12px;border:1px solid rgba(251,191,36,.4);background:rgba(251,191,36,.08);color:#fde68a;margin-bottom:14px}
.store-links{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.store-links a{display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:999px;border:1px solid var(--line-2);background:var(--card-2);font-size:.85rem;color:#fff}
.store-links a:hover{border-color:var(--p-2);color:#fff}
.store-links svg{width:15px;height:15px}
.store-themed .btn:not(.btn-ghost):not(.btn-line):not(.btn-danger){background:var(--grad)}
.bulk-bar{display:none;gap:10px;align-items:center;flex-wrap:wrap;padding:10px 14px;border:1px solid var(--p-soft);background:var(--p-soft);border-radius:12px;margin-bottom:12px;position:sticky;top:8px;z-index:5;backdrop-filter:blur(6px)}
.bulk-bar.on{display:flex}
.bulk-bar select,.bulk-bar input[type=text]{width:auto;padding:6px 10px}
td.chk,th.chk{width:34px;padding-right:0}
.vac-note{display:flex;gap:8px;align-items:center;color:#fde68a;font-size:.88rem;margin:0 0 10px}
.feed-row{display:flex;gap:12px;align-items:flex-start;padding:11px 4px;border-bottom:1px solid var(--line)}
.feed-row:last-child{border-bottom:0}
.feed-main{flex:1;min-width:0;overflow-wrap:anywhere}
.feed-dot{width:10px;height:10px;border-radius:50%;margin-top:7px;flex:none;background:var(--p-2)}
.feed-dot.k-siparis{background:#34d399}.feed-dot.k-kayit{background:#60a5fa}.feed-dot.k-para{background:#fbbf24}.feed-dot.k-destek{background:#f87171}.feed-dot.k-ilan{background:#a99aff}
"""

JS = r"""
(function(){
  document.addEventListener('change', function(e){
    var all = e.target.closest('[data-check-all]');
    var scope = document;
    if (all) {
      var boxes = scope.querySelectorAll(all.getAttribute('data-check-all'));
      for (var i = 0; i < boxes.length; i++) boxes[i].checked = all.checked;
    }
    var bar = document.querySelector('.bulk-bar');
    if (bar) {
      var n = document.querySelectorAll('input[name="ids"]:checked').length;
      bar.classList.toggle('on', n > 0);
      var c = bar.querySelector('[data-bulk-count]');
      if (c) c.textContent = n + ' ilan seçili';
    }
  });
  document.addEventListener('submit', function(e){
    var f = e.target.closest('form[data-bulk]');
    if (!f) return;
    var act = f.querySelector('[name="action"]');
    if (act && act.value === 'delete' && !window.confirm('Seçili ilanlar silinsin mi? Geçmiş siparişler korunur.')) e.preventDefault();
  });
})();
"""

CSS += r"""
/* ---- Bildirim detayı ---- */
.nk-tag{display:inline-flex;align-items:center;padding:2px 10px;border-radius:999px;font-size:.72rem;font-weight:700;border:1px solid;white-space:nowrap;letter-spacing:.01em}
.nk-tag.nk-ok{color:#6ee7b7;border-color:rgba(52,211,153,.45);background:rgba(52,211,153,.1)}
.nk-tag.nk-bad{color:#fca5a5;border-color:rgba(248,113,113,.45);background:rgba(248,113,113,.1)}
.nk-tag.nk-warn{color:#fcd34d;border-color:rgba(251,191,36,.45);background:rgba(251,191,36,.1)}
.nk-tag.nk-info{color:#a5b4fc;border-color:rgba(129,140,248,.4);background:rgba(129,140,248,.1)}
.notif-row.nk-ok .ti{background:rgba(52,211,153,.14);color:#34d399}
.notif-row.nk-bad .ti{background:rgba(248,113,113,.14);color:#f87171}
.notif-row.nk-warn .ti{background:rgba(251,191,36,.14);color:#fbbf24}
.notif-snip{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.notif-detail{padding:26px;border-top:3px solid var(--p)}
.notif-detail.nk-ok{border-top-color:#34d399}.notif-detail.nk-bad{border-top-color:#f87171}.notif-detail.nk-warn{border-top-color:#fbbf24}
.nd-head{display:flex;gap:16px;align-items:flex-start;margin-bottom:18px}
.nd-head h1{font-size:1.5rem;margin:8px 0 4px}
.nd-ico{display:grid;place-items:center;width:52px;height:52px;border-radius:15px;flex:none;background:var(--p-soft);color:var(--p-2)}
.nd-ico svg{width:26px;height:26px}
.notif-detail.nk-ok .nd-ico{background:rgba(52,211,153,.14);color:#34d399}
.notif-detail.nk-bad .nd-ico{background:rgba(248,113,113,.14);color:#f87171}
.notif-detail.nk-warn .nd-ico{background:rgba(251,191,36,.14);color:#fbbf24}
.nd-body{padding:16px 18px;border-radius:12px;background:var(--bg-2);border:1px solid var(--line);font-size:1.02rem;line-height:1.7;overflow-wrap:anywhere}
.nd-order{margin-top:16px;padding:14px 16px;border-radius:12px;border:1px solid var(--line);background:var(--card-2)}
"""

CSS += r"""
/* ---- Takip ve çekiliş ---- */
.follow-form .btn{gap:8px}
.follow-count{font-style:normal;font-size:.78rem;padding:1px 8px;border-radius:999px;background:rgba(255,255,255,.16)}
.chip-s{display:inline-flex;align-items:center;padding:2px 10px;border-radius:999px;font-size:.72rem;font-weight:600;border:1px solid var(--line-2);background:var(--card-2);color:var(--muted)}
.chip-s.ok{color:#6ee7b7;border-color:rgba(52,211,153,.4);background:rgba(52,211,153,.1)}
.gw-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(270px,100%),1fr));gap:16px}
.gw-card{display:flex;flex-direction:column;gap:6px;padding:18px;border-radius:16px;border:1px solid var(--line);background:linear-gradient(160deg,var(--card),var(--card-2));color:var(--text);transition:.25s var(--ease)}
.gw-card:hover{border-color:var(--p-2);color:var(--text);box-shadow:0 18px 40px -24px var(--p)}
.gw-card h3{margin:6px 0 0;font-size:1.05rem}
.gw-top{display:flex;gap:12px;align-items:center}
.gw-ico{display:grid;place-items:center;width:44px;height:44px;border-radius:13px;background:var(--grad);color:#fff;flex:none}
.gw-ico.lg{width:60px;height:60px;border-radius:18px}
.gw-ico svg{width:22px;height:22px}.gw-ico.lg svg{width:30px;height:30px}
.gw-prize small,.gw-prize-box small{display:block;color:var(--dim);font-size:.72rem;text-transform:uppercase;letter-spacing:.08em}
.gw-prize b{font-size:1rem}
.gw-meta{display:flex;gap:12px;flex-wrap:wrap;color:var(--muted);font-size:.82rem;margin-top:4px}
.gw-meta span{display:inline-flex;align-items:center;gap:5px}.gw-meta svg{width:14px;height:14px}
.gw-tags{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}
.gw-hero{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;padding:22px 24px;border-radius:18px;border:1px solid var(--p-soft);background:linear-gradient(120deg,rgba(124,92,255,.18),rgba(244,114,182,.08))}
.gw-detail{padding:26px}
.gw-head{display:flex;gap:16px;align-items:flex-start;margin-bottom:16px}
.gw-head h1{font-size:1.6rem;margin:8px 0 6px}
.gw-prize-box{padding:16px 18px;border-radius:14px;margin-bottom:16px;background:linear-gradient(120deg,var(--p-soft),rgba(244,114,182,.1));border:1px solid var(--p-soft)}
.gw-prize-box b{font-size:1.35rem}
.gw-rules{list-style:none;padding:0;margin:0 0 18px;display:grid;gap:8px;color:#d6d6e2}
.gw-rules li{display:flex;gap:9px;align-items:flex-start;font-size:.92rem}.gw-rules svg{width:17px;height:17px;color:#34d399;flex:none;margin-top:3px}
"""

JS += r"""
(function(){
  document.addEventListener('submit', function(e){
    var f = e.target.closest('form[data-follow]');
    if (!f || !window.fetch) return;
    e.preventDefault();
    var fd = new FormData(f);
    fetch(f.action, {method: 'POST', body: fd, credentials: 'same-origin', headers: {'X-Requested-With': 'fetch', 'Accept': 'application/json'}})
      .then(function(r){ return r.json(); })
      .then(function(j){
        if (!j || !j.ok) { f.submit(); return; }
        var b = f.querySelector('[data-follow-btn]');
        f.querySelector('[data-follow-label]').textContent = j.following ? 'Takip ediliyor' : 'Takip et';
        f.querySelector('[data-follow-count]').textContent = j.count;
        if (b) b.classList.toggle('btn-line', !!j.following);
      }).catch(function(){ f.submit(); });
  });
})();
"""

CSS += r"""
.store-side{display:grid;gap:10px;min-width:300px}
.store-side .follow-form .btn{width:100%}
@media (max-width:760px){.store-side{min-width:0;width:100%}}
"""

CSS += r"""
/* ---------- Elmas paket: premium görünüm ---------- */
.theme-sw.locked{opacity:.5;cursor:not-allowed}
.theme-sw.locked i{filter:grayscale(.6)}
.pk-card.hot{isolation:isolate;border:0;padding:24px 22px 22px;background:linear-gradient(170deg,rgba(34,211,238,.10),rgba(124,92,255,.14) 45%,rgba(15,16,26,.0) 80%),var(--card);
  box-shadow:0 28px 60px -30px rgba(99,120,255,.75),0 0 40px -18px rgba(34,211,238,.5)}
.pk-card.hot:before{content:"";position:absolute;inset:-70%;z-index:-2;pointer-events:none;
  background:conic-gradient(from 0deg,#22d3ee,#5b8cff,#a78bfa,#f0abfc,#5b8cff,#22d3ee);animation:pk-spin 9s linear infinite;will-change:transform}
.pk-card.hot:after{content:"";position:absolute;inset:1.5px;z-index:-1;border-radius:15px;pointer-events:none;
  background:radial-gradient(260px 160px at 0 0,rgba(34,211,238,.16),transparent 70%),radial-gradient(240px 160px at 100% 100%,rgba(167,139,250,.16),transparent 70%),var(--card)}
.pk-card.hot .pk-ico{width:60px;height:60px;border-radius:17px;border:1px solid rgba(147,197,253,.45);
  background:radial-gradient(circle at 30% 25%,rgba(255,255,255,.22),transparent 55%),linear-gradient(145deg,rgba(34,211,238,.22),rgba(124,92,255,.3));
  box-shadow:0 10px 26px -10px rgba(99,140,255,.9),inset 0 0 0 1px rgba(255,255,255,.08)}
.pk-card.hot .pk-ico img{width:40px;height:40px;filter:drop-shadow(0 3px 8px rgba(80,140,255,.65));animation:pk-float 4.5s ease-in-out infinite}
.pk-card.hot .pk-top h3{font-size:1.25rem;background:linear-gradient(90deg,#e6f9ff,#a9c4ff 55%,#d8c4ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.pk-card.hot .pk-price b{background:linear-gradient(90deg,#fff,#b9d3ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.pk-card.hot .pk-feats li{color:#e6e8f5}
.pk-card.hot .pk-feats .i{color:#7dd3fc}
.pk-card.hot .pk-ribbon{right:20px;padding:4px 12px 5px;background:linear-gradient(90deg,#22d3ee,#5b8cff 50%,#a78bfa);box-shadow:0 8px 18px -8px rgba(91,140,255,.95)}
.pk-card.hot .btn.shine{background:linear-gradient(90deg,#22b8e6,#5b7cff 55%,#8f6bff);box-shadow:0 12px 26px -12px rgba(91,124,255,.9)}
.pk-perks{display:flex;flex-wrap:wrap;gap:6px;margin-top:-2px}
.pk-perks span{display:inline-flex;align-items:center;gap:5px;font-size:.72rem;font-weight:700;padding:3px 10px;border-radius:999px;color:#bfe6ff;background:rgba(56,189,248,.1);border:1px solid rgba(125,211,252,.35)}
.pk-perks .i{width:.95em;height:.95em}
@keyframes pk-spin{to{transform:rotate(360deg)}}
@keyframes pk-float{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}
/* elmas mağaza: mağaza kartı ve satıcı kartı */
.store-card.pk-diamond:before{background:linear-gradient(90deg,#22d3ee,#5b8cff,#a78bfa,#f0abfc,#22d3ee,#5b8cff);background-size:200% 100%;animation:pk-bar 6s linear infinite}
.store-card.pk-diamond:not(.has-banner){background:radial-gradient(520px 200px at 0 0,rgba(34,211,238,.13),transparent 70%),radial-gradient(520px 220px at 100% 0,rgba(167,139,250,.14),transparent 70%),var(--card)}
.seller-card.pk-diamond{position:relative;border-color:rgba(125,185,255,.6);box-shadow:0 18px 40px -26px rgba(99,140,255,.8)}
.vtier-diamond{filter:drop-shadow(0 0 4px rgba(96,165,250,.7))}
@keyframes pk-bar{to{background-position:200% 0}}
@media (prefers-reduced-motion:reduce){.pk-card.hot:before,.pk-card.hot .pk-ico img,.store-card.pk-diamond:before{animation:none}}
"""

CSS += r"""
/* kaydırırken fare altındaki kartların hover durumu titremesin (kaydırma sırasında etkileşim kapatılır) */
html.scrolling main{pointer-events:none}
.lcard,.seller-card,.cat-ban,.gw-card,.pk-card{contain:layout style}
"""

CSS += r"""
.fee-note{color:#fbbf24;font-size:.86rem;margin:6px 0 0}
.fee-note b{color:#fde68a}
"""

CSS += r"""
/* ---------- ödeme yöntemleri ---------- */
.pm-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(250px,100%),1fr));gap:12px}
.pm-card{--c:#7c5cff;position:relative;display:flex;align-items:center;gap:12px;padding:14px;border:1px solid var(--line-2);border-radius:14px;background:var(--card);cursor:pointer;margin:0;font-weight:400;transition:border-color .2s,background .2s,box-shadow .2s}
.pm-card input{position:absolute;opacity:0;pointer-events:none}
.pm-card:hover{border-color:color-mix(in srgb,var(--c) 55%,transparent)}
.pm-card.on,.pm-card:has(input:checked){border-color:var(--c);background:color-mix(in srgb,var(--c) 11%,var(--card));box-shadow:0 0 0 1px var(--c) inset}
.pm-card:has(input:focus-visible){outline:2px solid var(--p-2);outline-offset:2px}
.pm-ico{flex:none;display:grid;place-items:center;width:42px;height:42px;border-radius:12px;color:var(--c,#7c5cff);background:color-mix(in srgb,var(--c,#7c5cff) 14%,var(--card-2));border:1px solid color-mix(in srgb,var(--c,#7c5cff) 32%,transparent)}
.pm-ico .i{width:20px;height:20px}
.pm-body{display:grid;gap:2px;min-width:0}
.pm-body b{font-size:.96rem;color:#fff}
.pm-body small{color:var(--muted);font-size:.78rem}
.pm-tag{position:absolute;top:-9px;right:12px;font-size:.66rem;font-weight:800;letter-spacing:.04em;text-transform:uppercase;padding:2px 8px;border-radius:999px;color:#bbf7d0;background:color-mix(in srgb,#22c55e 20%,var(--card));border:1px solid rgba(34,197,94,.45)}
.pm-tag.bonus{color:#fde68a;background:color-mix(in srgb,#f5b301 20%,var(--card));border-color:rgba(245,179,1,.5)}
.pm-lines{display:grid;gap:8px}
.pm-line{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:9px 12px;border-radius:10px;background:var(--card-2);border:1px solid var(--line)}
.pm-k{color:var(--muted);font-size:.8rem;min-width:110px}
.pm-v{flex:1;min-width:0;word-break:break-all;font-size:.92rem;color:#fff}
.pm-v.plain{font-family:inherit;color:var(--text)}
.pm-note{display:flex;gap:9px;align-items:flex-start;margin-top:12px;padding:10px 12px;border-radius:10px;font-size:.88rem;color:#bfe3ff;background:rgba(56,189,248,.08);border:1px solid rgba(56,189,248,.28)}
.pm-note .i{flex:none;margin-top:.15em}
.pm-sum{display:grid;gap:6px;margin:6px 0 12px;padding:12px 14px;border-radius:12px;background:var(--card-2);border:1px solid var(--line-2);max-width:420px}
.pm-sum>div{display:flex;justify-content:space-between;gap:12px;font-size:.92rem}
.pm-sum .bonus-row b{color:#fde68a}
.pm-sum .tot{border-top:1px solid var(--line);padding-top:7px;font-weight:700}
.pm-limit{margin-bottom:12px}
.pm-limit.bad{color:var(--bad)}
.pm-admin{border-color:color-mix(in srgb,var(--c) 26%,var(--line))}
.pm-admin .pm-ico{width:40px;height:40px}
.pm-new summary{cursor:pointer;list-style:none}
.pm-new summary::-webkit-details-marker{display:none}
.pay-strip{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:22px 0 4px;padding-top:18px;border-top:1px solid var(--line)}
.pay-lbl{color:var(--dim);font-size:.74rem;text-transform:uppercase;letter-spacing:.08em;font-weight:600;margin-right:4px}
.pay-chip{--c:#7c5cff;display:inline-flex;align-items:center;gap:7px;padding:5px 12px;border-radius:999px;font-size:.82rem;color:var(--text);background:color-mix(in srgb,var(--c) 10%,var(--card-2));border:1px solid color-mix(in srgb,var(--c) 30%,transparent)}
.pay-chip .i{color:var(--c);width:1.05em;height:1.05em}
.pay-chip:hover{color:#fff;border-color:var(--c)}
.topup-hint{display:flex;gap:9px;align-items:flex-start;margin-top:10px;padding:9px 12px;border-radius:10px;font-size:.84rem;color:#fde68a;background:rgba(245,179,1,.08);border:1px solid rgba(245,179,1,.3)}
.topup-hint .i{flex:none;margin-top:.15em}
"""

JS += r"""
/* bakiye yükleme sayfası: yöntem seçimi, bilgi paneli, bonus ve sınır özeti */
(function(){
  var form = document.getElementById('depform');
  if (form) {
    var radios = [].slice.call(form.querySelectorAll('input[name=method_id]'));
    var amt = document.getElementById('amount'), sum = document.getElementById('pm-sum'), lim = document.getElementById('pm-limit');
    var money = function(k){ return (k / 100).toLocaleString('tr-TR', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' ₺'; };
    var parse = function(s){ s = (s || '').replace(/\./g, '').replace(',', '.'); var v = parseFloat(s); return isNaN(v) ? null : Math.round(v * 100); };
    var update = function(){
      var sel = radios.filter(function(r){ return r.checked; })[0];
      if (!sel) return;
      radios.forEach(function(r){ r.closest('.pm-card').classList.toggle('on', r.checked); });
      [].slice.call(form.querySelectorAll('.pm-detail')).forEach(function(d){ d.hidden = d.getAttribute('data-pm') !== sel.value; });
      var min = parseInt(sel.getAttribute('data-min'), 10) || 0, max = parseInt(sel.getAttribute('data-max'), 10) || 0, pct = parseFloat(sel.getAttribute('data-bonus')) || 0;
      var v = parse(amt.value);
      lim.className = 'pm-limit small muted';
      lim.textContent = 'Bu yöntemde tutar ' + money(min) + (max ? ' - ' + money(max) : ' ve üzeri') + ' olmalı.';
      if (v === null || v <= 0) { sum.hidden = true; return; }
      if (v < min || (max && v > max)) { lim.className = 'pm-limit small bad'; }
      var bonus = Math.round(v * pct / 100);
      sum.hidden = false;
      document.getElementById('pm-s-amt').textContent = money(v);
      var br = sum.querySelector('.bonus-row'); br.hidden = !bonus;
      document.getElementById('pm-s-bonus').textContent = '+ ' + money(bonus);
      document.getElementById('pm-s-tot').textContent = money(v + bonus);
    };
    radios.forEach(function(r){ r.addEventListener('change', update); });
    amt.addEventListener('input', update);
    document.addEventListener('click', function(e){ if (e.target.closest('[data-fill]')) setTimeout(update, 0); });
    update();
  }
  /* para çekme: önceki hesabı otomatik doldur */
  var wm = document.getElementById('method'), wi = document.getElementById('account_info');
  if (wm && wi && wm.getAttribute('data-last')) {
    var last = {}; try { last = JSON.parse(wm.getAttribute('data-last')); } catch (e) {}
    var fill = function(){ if (!wi.value || wi.getAttribute('data-auto') === '1') { wi.value = last[wm.value] || ''; wi.setAttribute('data-auto', '1'); } };
    wi.addEventListener('input', function(){ wi.setAttribute('data-auto', '0'); });
    wm.addEventListener('change', fill); fill();
  }
})();
"""

CSS += r"""
/* ---------- mobil uyum (telefon) ---------- */
html{-webkit-text-size-adjust:100%;text-size-adjust:100%}
body{overflow-x:clip}
img,video,svg{max-width:100%}
.table-wrap,.tbl-wrap{max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}
@media (max-width:760px){
  .container{padding-left:14px;padding-right:14px}
  .topbar-in{gap:8px}
  .top-right{gap:2px;min-width:0}
  .ibtn{width:36px;height:38px}
  .chip{padding:6px 10px;font-size:.82rem;gap:5px}
  .brand{min-width:0}
  .dd-menu{max-width:calc(100vw - 20px)}
}
@media (max-width:520px){
  .brand{font-size:0;gap:0}
  .brand .brand-mark{width:34px;height:34px}
  .footer .brand{font-size:1.15rem;gap:10px}
  .top-right .ibtn[aria-label="Favorilerim"]{display:none}
}
@media (max-width:360px){
  .chip{padding:5px 8px;font-size:.78rem}
  .chip .i{display:none}
  .ibtn{width:34px}
  .btn-sm{padding-left:10px;padding-right:10px}
}
/* dokunmatik: yeterince büyük hedefler, girişlerde iOS yakınlaştırmasını engelle */
@media (pointer:coarse){
  input:not([type=checkbox]):not([type=radio]):not([type=range]),select,textarea{font-size:16px}
  .footer a,.catbar a,.dd-menu a,.dd-menu button.dd-item,.n-item,.chip-c{min-height:40px;display:flex;align-items:center}
  .footer-in ul li a,.footer-links a{padding-top:6px;padding-bottom:6px}
}
"""

CSS += r"""
code,.mono,pre{overflow-wrap:anywhere}
pre{white-space:pre-wrap}
.grow-1,.pk-top>div,.card{min-width:0}
@media (max-width:760px){
  .pk-top{flex-wrap:wrap}
  .pk-edit{padding:14px}
  .spread{flex-wrap:wrap;gap:10px}
}
"""

CSS += r"""
/* mobil: mağaza başlığı dikey düzen, dokunma hedefleri, bildirim menüsü */
@media (max-width:560px){
  .store-head{flex-direction:column;align-items:flex-start;gap:14px}
  .store-head>.grow-1{width:100%;flex:1 1 auto}
  .store-head h1{font-size:1.5rem;line-height:1.2}
  .store-card.has-banner .store-head{padding:14px 16px 18px}
  .store-card.has-banner .store-head .avatar{margin-top:-46px}
  .store-side{width:100%}
  .store-links a{min-height:40px}
  .dd-menu.dd-notif{position:fixed;left:8px;right:8px;top:64px;width:auto;max-width:none}
  .n-list{max-height:60vh;overflow:auto}
}
@media (pointer:coarse){
  .btn,button.btn,.chip,.tab,.nav a{min-height:40px}
  input,select,textarea{font-size:16px}
}
"""

CSS += r"""
/* bildirim menusu: .dd-menu a (flex, tam genislik) kuralini bildirim bag
   lantilarinda gecersiz kil */
.dd-menu .n-item{display:block;width:auto;padding:11px 14px;border-radius:0}
.dd-menu .n-head a{display:inline;width:auto;padding:0;border-radius:0}
.dd-menu .n-head button.link-btn{display:inline;width:auto;padding:0}
"""
