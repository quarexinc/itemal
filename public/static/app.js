(function(){
  'use strict';
  var $ = function(s, r){ return (r || document).querySelector(s); };
  var $$ = function(s, r){ return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var csrf = (($('meta[name=csrf]') || {}).content) || '';

  function fmt(k){
    var tl = Math.floor(k / 100), kr = ('0' + (k % 100)).slice(-2);
    return String(tl).replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ',' + kr + ' ₺';
  }
  function post(url, data){
    var fd = new FormData(); fd.append('csrf_token', csrf);
    Object.keys(data || {}).forEach(function(k){ fd.append(k, data[k]); });
    return fetch(url, {method: 'POST', body: fd, credentials: 'same-origin', headers: {'Accept': 'application/json'}});
  }

  // ---------- menüler ----------
  $$('[data-toggle-nav]').forEach(function(b){
    b.addEventListener('click', function(){ var t = $(b.getAttribute('data-toggle-nav')); if (t) t.classList.toggle('open'); });
  });
  document.addEventListener('click', function(e){
    var t = e.target.closest('[data-dd-toggle]');
    $$('.dd.open').forEach(function(d){ if (!t || d !== t.closest('.dd')) d.classList.remove('open'); });
    if (t) {
      var dd = t.closest('.dd'); dd.classList.toggle('open');
      if (dd.classList.contains('open') && t.hasAttribute('data-notif')) {
        var url = t.getAttribute('data-notif');
        post(url).then(function(){ var dot = $('.dot', t); if (dot) setTimeout(function(){ dot.remove(); }, 1200); }).catch(function(){});
      }
    }
  });
  document.addEventListener('keydown', function(e){
    if (e.key === 'Escape') { $$('.dd.open').forEach(function(d){ d.classList.remove('open'); }); var lb = $('.lightbox.on'); if (lb) lb.classList.remove('on'); }
  });

  // ---------- bildirimler (flash) ----------
  document.addEventListener('click', function(e){
    var x = e.target.closest('.flash .x'); if (x) x.parentNode.remove();
  });
  setTimeout(function(){
    $$('.flash-ok,.flash-info').forEach(function(f){ f.style.transition = 'opacity .5s, transform .5s'; f.style.opacity = '0'; f.style.transform = 'translateX(20px)';
      setTimeout(function(){ f.remove(); }, 600); });
  }, 6500);

  // ---------- onay / kopyala / hızlı doldur ----------
  document.addEventListener('submit', function(e){
    var msg = e.target.getAttribute('data-confirm');
    var sub = e.submitter && e.submitter.getAttribute('data-confirm');
    if ((sub || msg) && !window.confirm(sub || msg)) { e.preventDefault(); return; }
    var fm = e.target.getAttribute('data-fee-confirm'), ff = e.target.getAttribute('data-fee-field');
    if (fm && ff && e.target.elements[ff] && e.target.elements[ff].value.trim() !== e.target.elements[ff].defaultValue.trim() && !window.confirm(fm)) e.preventDefault();
  });
  document.addEventListener('click', function(e){
    var b = e.target.closest('[data-copy]');
    if (b) {
      var sel = b.getAttribute('data-copy'), text = '';
      if (sel.charAt(0) === '#' || sel.charAt(0) === '.') text = $$(sel).map(function(n){ return n.textContent.trim(); }).join('\n'); else text = sel;
      var done = function(){ var old = b.innerHTML; b.textContent = 'Kopyalandı'; setTimeout(function(){ b.innerHTML = old; }, 1600); };
      if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(done);
      else { var ta = document.createElement('textarea'); ta.value = text; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); done(); } catch (err) {} ta.remove(); }
      return;
    }
    var f = e.target.closest('[data-fill]');
    if (f) { e.preventDefault(); var inp = $(f.getAttribute('data-target')); if (inp) { inp.value = f.getAttribute('data-fill'); inp.focus(); inp.dispatchEvent(new Event('input', {bubbles: true})); } return; }
    var s = e.target.closest('[data-share]');
    if (s) {
      if (navigator.share) { navigator.share({title: document.title, url: location.href}).catch(function(){}); }
      else if (navigator.clipboard) { navigator.clipboard.writeText(location.href).then(function(){ var o = s.innerHTML; s.textContent = 'Bağlantı kopyalandı'; setTimeout(function(){ s.innerHTML = o; }, 1600); }); }
    }
  });

  // ---------- adet, kupon, toplam ----------
  var qty = $('#qty');
  if (qty) {
    var price = parseInt(qty.getAttribute('data-price'), 10), disc = 0, maxq = parseInt(qty.max || '1', 10);
    var total = $('#total'), drow = $('#discount-row'), dval = $('#discount-val');
    var clamp = function(){ return Math.max(1, Math.min(maxq, parseInt(qty.value || '1', 10) || 1)); };
    var upd = function(){
      var n = clamp(), gross = n * price;
      if (disc > gross - 100) disc = Math.max(0, gross - 100);
      if (total) total.textContent = fmt(gross - disc);
      if (drow) drow.hidden = !disc;
      if (dval) dval.textContent = '-' + fmt(disc);
    };
    qty.addEventListener('input', function(){ if (cInput && cInput.value) applyCoupon(true); else upd(); });
    $$('[data-step]').forEach(function(b){ b.addEventListener('click', function(){
      qty.value = Math.max(1, Math.min(maxq, clamp() + parseInt(b.getAttribute('data-step'), 10))); qty.dispatchEvent(new Event('input'));
    }); });
    var cInput = $('#coupon'), cBtn = $('#coupon-apply'), cMsg = $('#coupon-msg');
    function applyCoupon(silent){
      var code = cInput.value.trim();
      if (!code) { disc = 0; if (cMsg) { cMsg.textContent = ''; cMsg.className = 'coupon-msg'; } upd(); return; }
      fetch(cBtn.getAttribute('data-url') + '?kod=' + encodeURIComponent(code) + '&qty=' + clamp(), {credentials: 'same-origin', headers: {'Accept': 'application/json'}})
        .then(function(r){ return r.json(); })
        .then(function(j){
          disc = j.ok ? j.discount : 0; upd();
          if (cMsg) { cMsg.textContent = j.msg; cMsg.className = 'coupon-msg ' + (j.ok ? 'ok' : 'bad'); }
        }).catch(function(){});
    }
    if (cBtn) cBtn.addEventListener('click', function(){ applyCoupon(false); });
    if (cInput) cInput.addEventListener('keydown', function(e){ if (e.key === 'Enter') { e.preventDefault(); applyCoupon(false); } });
    upd();
  }

  // ---------- formlar ----------
  $$('textarea[data-count-lines]').forEach(function(ta){
    var out = $(ta.getAttribute('data-count-lines'));
    var run = function(){ var seen = {}, n = 0; ta.value.split(/\r?\n/).forEach(function(l){ l = l.trim(); if (l && !seen[l]) { seen[l] = 1; n++; } }); if (out) out.textContent = n; };
    ta.addEventListener('input', run); run();
  });
  $$('input[type=file][data-name]').forEach(function(inp){
    inp.addEventListener('change', function(){ var t = $(inp.getAttribute('data-name')); if (t) t.textContent = inp.files.length ? inp.files[0].name : ''; });
  });
  $$('input[type=file][data-preview]').forEach(function(inp){
    inp.addEventListener('change', function(){
      var img = $(inp.getAttribute('data-preview')); if (!img || !inp.files.length) return;
      img.src = URL.createObjectURL(inp.files[0]); img.hidden = false;
    });
  });
  // renk seçici -> metin kutusu
  $$('input[type=color][data-hex]').forEach(function(c){
    var t = $(c.getAttribute('data-hex'));
    c.addEventListener('input', function(){ if (t) t.value = c.value; });
  });
  // komisyon önizlemesi
  var pIn = $('#price-input'), catSel = $('#cat-select'), netOut = $('#net-preview');
  if (pIn && catSel && netOut) {
    var calc = function(){
      var raw = pIn.value.replace(/\s/g, ''); if (raw.indexOf(',') > -1) raw = raw.replace(/\./g, '').replace(',', '.');
      var p = parseFloat(raw), opt = catSel.options[catSel.selectedIndex], rate = opt ? parseFloat(opt.getAttribute('data-rate')) : NaN;
      var feeEl = $('#fee-preview'), rateEl = $('#rate-preview');
      if (!(p > 0) || isNaN(rate)) { netOut.textContent = '-'; if (feeEl) feeEl.textContent = '-'; if (rateEl) rateEl.textContent = isNaN(rate) ? '-' : '%' + String(rate).replace('.', ','); return; }
      var gross = Math.round(p * 100), fee = Math.round(gross * rate / 100);
      netOut.textContent = fmt(gross - fee); if (feeEl) feeEl.textContent = fmt(fee); if (rateEl) rateEl.textContent = '%' + String(rate).replace('.', ',');
    };
    pIn.addEventListener('input', calc); catSel.addEventListener('change', calc); calc();
  }
  // tablo süzgeci (yönetici)
  $$('input[data-table-filter]').forEach(function(inp){
    inp.addEventListener('input', function(){
      var q = inp.value.toLowerCase();
      $$(inp.getAttribute('data-table-filter') + ' tr').forEach(function(tr, i){ if (i === 0 && $('th', tr)) return; tr.style.display = tr.textContent.toLowerCase().indexOf(q) > -1 ? '' : 'none'; });
    });
  });

  // ---------- sohbet (hızlı gönderim + 1,5 sn'lik sorgu) ----------
  var log = $('.chat-log[data-poll]');
  var openConv = null;
  if (log) {
    var last = parseInt(log.getAttribute('data-last') || '0', 10), pollUrl = log.getAttribute('data-poll');
    openConv = parseInt(log.getAttribute('data-conv') || '0', 10) || null;
    log.scrollTop = log.scrollHeight;
    var seen = {};
    var addMsg = function(m){
      if (seen[m.id]) return; seen[m.id] = 1;
      var empty = $('.chat-empty', log); if (empty) empty.remove();
      var d = document.createElement('div'); d.className = 'msg' + (m.mine ? ' me' : ''); d.appendChild(document.createTextNode(m.body));
      var t = document.createElement('time'); t.textContent = m.time; d.appendChild(t);
      var end = $('#son', log); log.insertBefore(d, end);
    };
    var busy = false;
    var pull = function(){
      if (busy || !pollUrl) return; busy = true;
      fetch(pollUrl + '?after=' + last, {credentials: 'same-origin', headers: {'Accept': 'application/json'}})
        .then(function(r){ return r.ok ? r.json() : []; })
        .then(function(list){
          var stick = log.scrollHeight - log.scrollTop - log.clientHeight < 80;
          list.forEach(function(m){ if (m.id > last) { last = m.id; addMsg(m); } });
          if (list.length && (stick || list.some(function(m){ return m.mine; }))) log.scrollTop = log.scrollHeight;
        }).catch(function(){}).then(function(){ busy = false; });
    };
    setInterval(function(){ if (!document.hidden) pull(); }, 1500);
    window.addEventListener('focus', pull);
    // AJAX gönderim: sayfa yenilenmeden anında görünür
    var cform = $('.chat-form');
    if (cform) {
      cform.addEventListener('submit', function(e){
        var ta = $('textarea', cform), text = ta.value.trim();
        if (!text || !window.fetch) return;
        e.preventDefault();
        var btn = $('button[type=submit]', cform); if (btn) btn.disabled = true;
        var fd = new FormData(cform);
        fetch(cform.action, {method: 'POST', body: fd, credentials: 'same-origin', headers: {'X-Requested-With': 'fetch', 'Accept': 'application/json'}})
          .then(function(r){ return r.json(); })
          .then(function(j){
            if (j.ok) { ta.value = ''; pull(); } else { toast('Mesaj gönderilemedi', j.error || 'Tekrar dene.', ''); }
          }).catch(function(){ cform.submit(); })
          .then(function(){ if (btn) btn.disabled = false; ta.focus(); });
      });
    }
  }
  $$('.chat-form textarea').forEach(function(ta){
    ta.addEventListener('keydown', function(e){ if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if (ta.value.trim() && ta.form.requestSubmit) ta.form.requestSubmit(); } });
  });

  // ---------- canlı bildirim: ses + tarayıcı bildirimi + sayaçlar ----------
  var LS = {
    get: function(k, d){ try { var v = localStorage.getItem(k); return v === null ? d : v; } catch (e) { return d; } },
    set: function(k, v){ try { localStorage.setItem(k, String(v)); } catch (e) {} }
  };
  var toastBox = null;
  function toast(title, body, url){
    if (!toastBox) { toastBox = document.createElement('div'); toastBox.className = 'toasts'; document.body.appendChild(toastBox); }
    var t = document.createElement(url ? 'a' : 'div'); t.className = 'toast-live'; if (url) t.href = url;
    var b = document.createElement('b'); b.textContent = title; t.appendChild(b);
    if (body) { var s = document.createElement('span'); s.textContent = body; t.appendChild(s); }
    toastBox.appendChild(t);
    setTimeout(function(){ t.classList.add('out'); setTimeout(function(){ t.remove(); }, 400); }, 7000);
  }
  var audioCtx = null;
  function unlockAudio(){
    try {
      if (!audioCtx) { var AC = window.AudioContext || window.webkitAudioContext; if (AC) audioCtx = new AC(); }
      if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
    } catch (e) {}
  }
  ['pointerdown', 'keydown', 'touchstart'].forEach(function(ev){ document.addEventListener(ev, unlockAudio, {passive: true}); });
  function ding(){
    if (LS.get('itm_sound', '1') !== '1') return;
    unlockAudio();
    if (!audioCtx || audioCtx.state !== 'running') return;
    try {
      var t0 = audioCtx.currentTime;
      [[880, 0], [1318, .13]].forEach(function(n){
        var o = audioCtx.createOscillator(), g = audioCtx.createGain();
        o.type = 'sine'; o.frequency.value = n[0];
        g.gain.setValueAtTime(0.0001, t0 + n[1]);
        g.gain.exponentialRampToValueAtTime(0.28, t0 + n[1] + .02);
        g.gain.exponentialRampToValueAtTime(0.0001, t0 + n[1] + .42);
        o.connect(g); g.connect(audioCtx.destination); o.start(t0 + n[1]); o.stop(t0 + n[1] + .45);
      });
    } catch (e) {}
  }
  function sysNotify(ev){
    if (!('Notification' in window) || Notification.permission !== 'granted') return false;
    try {
      var n = new Notification(ev.title, {body: ev.body || '', tag: 'itm-' + ev.kind + '-' + ev.id});
      n.onclick = function(){ window.focus(); if (ev.url) location.href = ev.url; n.close(); };
      return true;
    } catch (e) { return false; }
  }
  var liveUrl = document.body.getAttribute('data-live');
  if (liveUrl) {
    var uidKey = document.body.getAttribute('data-uid') || '0';
    var kM = 'itm_m_' + uidKey, kN = 'itm_n_' + uidKey;
    var num0 = function(k){ var v = LS.get(k, ''); return v === '' ? null : (parseInt(v, 10) || 0); };
    var setDot = function(host, n){
      if (!host) return;
      var d = $('.dot', host);
      if (!d && n) { d = document.createElement('span'); d.className = 'dot'; host.appendChild(d); }
      if (d) { d.hidden = !n; d.textContent = n > 9 ? '9+' : n; }
    };
    var addNotifItem = function(ev){
      var list = $('.dd-notif .n-list'); if (!list) return;
      var empty = $('.n-empty', list); if (empty) empty.remove();
      var a = document.createElement('a'); a.className = 'n-item unread'; a.href = ev.url || '/bildirimler';
      var b = document.createElement('b'); b.textContent = ev.title; a.appendChild(b);
      if (ev.body) { var sm = document.createElement('small'); sm.textContent = ev.body; a.appendChild(sm); }
      var tm = document.createElement('small'); tm.textContent = 'şimdi'; a.appendChild(tm);
      list.insertBefore(a, list.firstChild);
    };
    var livePoll = function(){
      var m = num0(kM), n = num0(kN);
      var qs = (m === null || n === null) ? '' : '?m=' + m + '&n=' + n;
      fetch(liveUrl + qs, {credentials: 'same-origin', headers: {'Accept': 'application/json'}})
        .then(function(r){ return r.ok ? r.json() : null; })
        .then(function(j){
          if (!j || !j.ok) return;
          if (m === null || n === null) { LS.set(kM, j.m); LS.set(kN, j.n); }
          else {
            var gm = num0(kM) || 0, gn = num0(kN) || 0, fresh = [], hiM = gm, hiN = gn;
            (j.events || []).forEach(function(ev){
              if (ev.kind === 'message') { var was = ev.id > gm; hiM = Math.max(hiM, ev.id); if (!was) return; if (openConv && ev.conv === openConv && !document.hidden) return; }
              else { var was2 = ev.id > gn; hiN = Math.max(hiN, ev.id); if (!was2) return; }
              fresh.push(ev);
            });
            LS.set(kM, hiM); LS.set(kN, hiN);
            if (fresh.length) {
              ding();
              fresh.forEach(function(ev){
                if (ev.kind === 'notif') addNotifItem(ev);
                var sys = false;
                if (document.hidden || !document.hasFocus()) sys = sysNotify(ev);
                if (!sys) toast(ev.title, ev.body, ev.url);
              });
            }
          }
          setDot($('a.ibtn[aria-label="Mesajlar"]'), j.unread_chat);
          var bell = $('button.ibtn[aria-label="Bildirimler"]');
          if (bell) { setDot(bell, j.unread_notif); if (j.unread_notif) bell.setAttribute('data-notif', bell.getAttribute('data-notif-url') || ''); }
          var bal = $('#bal-val'); if (bal && j.balance) bal.textContent = j.balance;
        }).catch(function(){});
    };
    livePoll();
    var loop = function(){ livePoll(); setTimeout(loop, document.hidden ? 8000 : 2500); };
    setTimeout(loop, 2500);
    document.addEventListener('visibilitychange', function(){ if (!document.hidden) livePoll(); });

    // izin çubuğu ve ses düğmesi
    var bar = $('#perm-bar');
    if (bar && 'Notification' in window && Notification.permission === 'default' && LS.get('itm_perm_hide', '') !== '1') bar.hidden = false;
    document.addEventListener('click', function(e){
      var en = e.target.closest('[data-notif-enable]');
      if (en) {
        unlockAudio();
        if ('Notification' in window) Notification.requestPermission().then(function(p){ if (bar) bar.hidden = true; if (p === 'granted') { ding(); toast('Bildirimler açık', 'Yeni mesaj ve bildirimlerde uyarı alacaksın.', ''); } });
        else if (bar) bar.hidden = true;
        return;
      }
      var later = e.target.closest('[data-notif-later]');
      if (later) { LS.set('itm_perm_hide', '1'); if (bar) bar.hidden = true; return; }
      var st = e.target.closest('[data-sound-toggle]');
      if (st) {
        e.stopPropagation();
        var on = LS.get('itm_sound', '1') === '1'; LS.set('itm_sound', on ? '0' : '1');
        st.textContent = on ? 'Ses: Kapalı' : 'Ses: Açık'; if (!on) { unlockAudio(); ding(); }
      }
    });
    $$('[data-sound-toggle]').forEach(function(b){ b.textContent = LS.get('itm_sound', '1') === '1' ? 'Ses: Açık' : 'Ses: Kapalı'; });
  }

  // ---------- ödeme linki: linki yeni sekmede aç, bu sekmede "işleniyor" ekranına geç ----------
  $$('form[data-paylink]').forEach(function(f){
    f.addEventListener('submit', function(e){
      if (!window.fetch || f._sent) return;
      var url = f.getAttribute('data-open') || '';
      if (!/^https:\/\//i.test(url)) return;
      e.preventDefault();
      f._sent = true;
      window.open(url, '_blank', 'noopener,noreferrer');            // kullanıcı tıklamasıyla aynı anda: açılır pencere engeline takılmaz
      var err = $('[data-plerr]', f), btn = $('button[type=submit]', f);
      if (btn) btn.disabled = true;
      fetch(f.action, {method: 'POST', body: new URLSearchParams(new FormData(f)), credentials: 'same-origin', headers: {'X-Requested-With': 'fetch', 'Accept': 'application/json'}})
        .then(function(r){ return r.json(); })
        .then(function(d){
          if (d && d.ok) { window.location.href = d.next; return; }
          if (err) { err.textContent = (d && d.error) || 'İşlem başlatılamadı.'; err.hidden = false; }
          if (btn) btn.disabled = false; f._sent = false;
        })
        .catch(function(){ f._sent = true; f.submit(); });
    });
  });

  // ---------- görsel büyütme ----------
  var lb = document.createElement('div'); lb.className = 'lightbox'; lb.appendChild(document.createElement('img')); document.body.appendChild(lb);
  document.addEventListener('click', function(e){
    var z = e.target.closest('[data-zoom]');
    if (z) { e.preventDefault(); lb.firstChild.src = z.getAttribute('href') || z.src; lb.classList.add('on'); return; }
    if (lb.classList.contains('on')) lb.classList.remove('on');
  });

  // ---------- üst bar gölgesi, yukarı çık ----------
  var top = $('.topbar'), tt = document.createElement('button');
  tt.className = 'totop'; tt.setAttribute('aria-label', 'Yukarı çık');
  tt.innerHTML = '<svg class="i"><use href="#i-chevron-down" transform="rotate(180 12 12)"/></svg>';
  tt.addEventListener('click', function(){ window.scrollTo({top: 0, behavior: reduce ? 'auto' : 'smooth'}); });
  if ($('.topbar')) document.body.appendChild(tt);
  var rootEl = document.documentElement, scrollTimer = null;
  window.addEventListener('scroll', function(){
    var y = window.pageYOffset;
    if (top) top.classList.toggle('scrolled', y > 8);
    tt.classList.toggle('on', y > 700);
    if (!rootEl.classList.contains('scrolling')) rootEl.classList.add('scrolling');
    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(function(){ rootEl.classList.remove('scrolling'); }, 140);
  }, {passive: true});

  // ---------- slider ----------
  $$('[data-slider]').forEach(function(sl){
    var slides = $$('.slide', sl), dotsBox = $('.dots', sl), cur = 0, timer = null, secs = parseFloat(sl.getAttribute('data-interval') || '6');
    if (!slides.length) return;
    sl.style.setProperty('--dur', secs + 's');
    var dots = [];
    if (dotsBox && slides.length > 1) {
      slides.forEach(function(_, i){
        var b = document.createElement('button'); b.type = 'button'; b.setAttribute('aria-label', (i + 1) + '. slayt');
        b.addEventListener('click', function(){ go(i); }); dotsBox.appendChild(b); dots.push(b);
      });
    }
    function show(i){
      slides.forEach(function(s, k){ s.classList.toggle('on', k === i); });
      dots.forEach(function(d, k){ d.classList.remove('on'); if (k === i) { void d.offsetWidth; d.classList.add('on'); } });
      cur = i;
    }
    function next(){ show((cur + 1) % slides.length); }
    function arm(){ clearTimeout(timer); if (slides.length > 1 && !reduce) timer = setTimeout(function(){ next(); arm(); }, secs * 1000); }
    function go(i){ show((i + slides.length) % slides.length); arm(); }
    $$('.sl-arrow', sl).forEach(function(b){ b.addEventListener('click', function(){ go(cur + parseInt(b.getAttribute('data-dir'), 10)); }); });
    var paused = false, started = Date.now();
    sl.addEventListener('mouseenter', function(){ clearTimeout(timer); });
    sl.addEventListener('mouseleave', function(){ arm(); if (dots[cur]) { dots[cur].classList.remove('on'); void dots[cur].offsetWidth; dots[cur].classList.add('on'); } });
    var sx = 0;
    sl.addEventListener('touchstart', function(e){ sx = e.touches[0].clientX; }, {passive: true});
    sl.addEventListener('touchend', function(e){ var dx = e.changedTouches[0].clientX - sx; if (Math.abs(dx) > 40) go(cur + (dx < 0 ? 1 : -1)); }, {passive: true});
    document.addEventListener('visibilitychange', function(){ if (document.hidden) clearTimeout(timer); else arm(); });
    show(0); arm();
  });

  // ---------- kategori süzgeci ----------
  $$('.cat-filter').forEach(function(box){
    var tiles = $$('.cat-tile[data-g]');
    box.addEventListener('click', function(e){
      var b = e.target.closest('button[data-g]'); if (!b) return;
      $$('button', box).forEach(function(x){ x.classList.toggle('on', x === b); });
      var g = b.getAttribute('data-g');
      tiles.forEach(function(t){ t.classList.toggle('hide', g !== '*' && t.getAttribute('data-g') !== g); });
    });
  });

  // ---------- favori ----------
  document.addEventListener('click', function(e){
    var b = e.target.closest('[data-fav]'); if (!b) return;
    e.preventDefault(); e.stopPropagation();
    post(b.getAttribute('data-fav')).then(function(r){
      if (r.status === 401) { location.href = '/giris?next=' + encodeURIComponent(location.pathname); return null; }
      return r.json();
    }).then(function(j){
      if (!j) return;
      b.classList.toggle('on', j.on); b.classList.remove('pop'); void b.offsetWidth; b.classList.add('pop');
      var c = $('#fav-count'); if (c) { c.textContent = j.count; c.hidden = !j.count; }
    }).catch(function(){});
  });

  // ---------- arama önerileri ----------
  var sIn = $('input[data-suggest]');
  if (sIn) {
    var box = $('.suggest'), tmr = null, idx = -1;
    var okUrl = function(u){ return (typeof u === 'string' && /^\/(?!\/)/.test(u)) ? u : '/'; };
    var esc = function(s){ return String(s).replace(/[&<>"']/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); };
    var render = function(j){
      if (!j.items.length) { box.classList.remove('on'); return; }
      box.innerHTML = j.items.map(function(it){
        var img = it.cover ? '<span class="thumb"><img src="' + esc(it.cover) + '" alt=""></span>' : '<span class="cat-ic" style="--c:' + esc(it.color || '#7c5cff') + ';width:34px;height:34px;font-size:.72rem">' + esc(it.mono || '') + '</span>';
        return '<a href="' + esc(okUrl(it.url)) + '">' + img + '<span><b>' + esc(it.title) + '</b><small>' + esc(it.meta) + '</small></span></a>';
      }).join('') + '<a href="/ilanlar?q=' + encodeURIComponent(sIn.value) + '"><span class="cat-ic" style="--c:#3b3b4d;width:34px;height:34px"><svg class="i"><use href="#i-search"/></svg></span><span><b>Tüm sonuçları gör</b><small>' + esc(sIn.value) + '</small></span></a>';
      box.classList.add('on'); idx = -1;
    };
    sIn.addEventListener('input', function(){
      clearTimeout(tmr); var v = sIn.value.trim();
      if (v.length < 2) { box.classList.remove('on'); return; }
      tmr = setTimeout(function(){
        fetch(sIn.getAttribute('data-suggest') + '?q=' + encodeURIComponent(v), {headers: {'Accept': 'application/json'}}).then(function(r){ return r.json(); }).then(render).catch(function(){});
      }, 170);
    });
    sIn.addEventListener('keydown', function(e){
      var items = $$('a', box); if (!box.classList.contains('on') || !items.length) return;
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault(); idx = (idx + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
        items.forEach(function(a, k){ a.classList.toggle('hl', k === idx); });
      } else if (e.key === 'Enter' && idx > -1) { e.preventDefault(); location.href = items[idx].getAttribute('href'); }
    });
    document.addEventListener('click', function(e){ if (!e.target.closest('.search')) box.classList.remove('on'); });
    document.addEventListener('keydown', function(e){
      if (e.key === '/' && !/INPUT|TEXTAREA|SELECT/.test((document.activeElement || {}).tagName || '')) { e.preventDefault(); sIn.focus(); }
    });
  }

  // ---------- geri sayım ----------
  $$('[data-countdown]').forEach(function(el){
    var left = parseInt(el.getAttribute('data-countdown'), 10);
    var h = $('.h', el), m = $('.m', el), s = $('.s', el);
    var pad = function(n){ return ('0' + n).slice(-2); };
    var tick = function(){
      if (left < 0) left = 86400;
      h.firstChild.textContent = pad(Math.floor(left / 3600)); m.firstChild.textContent = pad(Math.floor(left % 3600 / 60)); s.firstChild.textContent = pad(left % 60); left--;
    };
    tick(); setInterval(tick, 1000);
  });

  // ---------- sayaç animasyonu, görünür olunca belirme ----------
  var io = ('IntersectionObserver' in window) ? new IntersectionObserver(function(entries){
    entries.forEach(function(en){
      if (!en.isIntersecting) return;
      var el = en.target; io.unobserve(el);
      if (el.classList.contains('reveal')) el.classList.add('in');
      if (el.hasAttribute('data-count')) countUp(el);
    });
  }, {threshold: .12, rootMargin: '0px 0px -40px 0px'}) : null;
  function countUp(el){
    var target = parseFloat(el.getAttribute('data-count')), suffix = el.getAttribute('data-suffix') || '';
    if (reduce || isNaN(target)) return;
    var t0 = null, dur = 1300;
    var step = function(ts){
      if (!t0) t0 = ts; var p = Math.min(1, (ts - t0) / dur), e = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * e).toLocaleString('tr-TR') + suffix;
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }
  $$('.reveal,[data-count]').forEach(function(el){ if (io) io.observe(el); else el.classList.add('in'); });
  setTimeout(function(){ $$('.reveal:not(.in)').forEach(function(el){ var r = el.getBoundingClientRect(); if (r.top < window.innerHeight) el.classList.add('in'); }); }, 1800);

  // ---------- eğim efekti ----------
  if (!reduce && window.matchMedia && window.matchMedia('(hover: hover)').matches) {
    $$('[data-tilt]').forEach(function(el){
      el.addEventListener('mousemove', function(e){
        var r = el.getBoundingClientRect(), x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
        el.style.transform = 'perspective(800px) rotateX(' + (-y * 7) + 'deg) rotateY(' + (x * 9) + 'deg) translateY(-5px)';
      });
      el.addEventListener('mouseleave', function(){ el.style.transform = ''; });
    });
  }

  // ---------- görsel küçültme + toplam boyut denetimi (Vercel işlevleri 4,5 MB'tan büyük istek almaz) ----------
  var UPMAX = parseInt(document.documentElement.getAttribute('data-upmax') || '0', 10);
  var SHRINK_OVER = UPMAX ? 450 * 1024 : 2.5 * 1024 * 1024;       // bu boyutun üstündeki görseller tarayıcıda küçültülür
  var SHRINK_TARGET = UPMAX ? 1000 * 1024 : 3 * 1024 * 1024;
  function loadBitmap(file){
    if (window.createImageBitmap) return createImageBitmap(file).catch(function(){ return viaImg(file); });
    return viaImg(file);
  }
  function viaImg(file){
    return new Promise(function(res, rej){
      var u = URL.createObjectURL(file), im = new Image();
      im.onload = function(){ URL.revokeObjectURL(u); res(im); };
      im.onerror = function(){ URL.revokeObjectURL(u); rej(); };
      im.src = u;
    });
  }
  function toBlob(canvas, type, q){ return new Promise(function(res){ canvas.toBlob(res, type, q); }); }
  async function shrinkFile(file){
    if (!/^image\/(jpeg|png|webp)$/.test(file.type) || file.size <= SHRINK_OVER) return file;
    var bmp;
    try { bmp = await loadBitmap(file); } catch (e) { return file; }
    var side = 2000, quality = .86, best = null;
    for (var round = 0; round < 6; round++) {
      var k = Math.min(1, side / Math.max(bmp.width, bmp.height));
      var c = document.createElement('canvas');
      c.width = Math.max(1, Math.round(bmp.width * k)); c.height = Math.max(1, Math.round(bmp.height * k));
      c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
      var blob = null;
      if (file.type === 'image/png') { blob = await toBlob(c, 'image/webp', quality); if (blob && blob.type !== 'image/webp') blob = null; }
      if (!blob) blob = await toBlob(c, 'image/jpeg', quality);
      if (!blob) break;
      best = blob;
      if (blob.size <= SHRINK_TARGET) break;
      quality = Math.max(.5, quality - .12); side = Math.round(side * .8);
    }
    if (!best || best.size >= file.size) return file;
    var ext = best.type === 'image/webp' ? '.webp' : '.jpg';
    return new File([best], (file.name || 'gorsel').replace(/\.[^.]+$/, '') + ext, { type: best.type, lastModified: Date.now() });
  }
  $$('input[type=file]').forEach(function(inp){
    inp.addEventListener('change', async function(){
      if (!inp.files || !inp.files.length || !window.DataTransfer) return;
      inp._busy = true;
      try {
        var dt = new DataTransfer(), changed = false;
        for (var i = 0; i < inp.files.length; i++) {
          var f = inp.files[i], g2 = await shrinkFile(f);
          if (g2 !== f) changed = true;
          dt.items.add(g2);
        }
        if (changed) inp.files = dt.files;
      } catch (e) {} finally { inp._busy = false; if (inp.form && inp.form._waiting) { var fm = inp.form; fm._waiting = false; if (fm.requestSubmit) fm.requestSubmit(); } }
    });
  });
  function formFileBytes(form){
    var n = 0;
    $$('input[type=file]', form).forEach(function(i){ for (var j = 0; j < (i.files || []).length; j++) n += i.files[j].size; });
    $$('input[type=file][form]').forEach(function(i){ if (i.getAttribute('form') === form.id) for (var j = 0; j < (i.files || []).length; j++) n += i.files[j].size; });
    return n;
  }
  document.addEventListener('submit', function(e){
    var form = e.target;
    if (!form || form.method.toLowerCase() !== 'post') return;
    var busy = $$('input[type=file]', form).some(function(i){ return i._busy; });
    if (busy) { e.preventDefault(); form._waiting = true; return; }
    var total = formFileBytes(form);
    if (UPMAX && total > UPMAX - 150 * 1024) {
      e.preventDefault();
      var box = $('.flashes') || (function(){ var d = document.createElement('div'); d.className = 'container flashes'; var host = $('main') || document.body; host.insertBefore(d, host.firstChild); return d; })();
      var m = document.createElement('div'); m.className = 'flash flash-bad';
      m.innerHTML = '<span></span><button type="button" class="x" aria-label="Kapat">&times;</button>';
      m.firstChild.textContent = 'Seçtiğin dosyalar toplamda ' + (total / 1048576).toFixed(1) + ' MB; tek seferde en fazla ' + ((UPMAX - 150 * 1024) / 1048576).toFixed(1) + ' MB gönderilebilir. Daha az ya da daha küçük görsel seçip tekrar dene.';
      box.appendChild(m); m.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, true);

  // ---------- son gezilenler ----------
  var KEY = 'itm_recent';
  function readRecent(){ try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch (e) { return []; } }
  var view = document.body.getAttribute('data-view');
  if (view) {
    try {
      var cur = JSON.parse(view), list = readRecent().filter(function(x){ return x.id !== cur.id; });
      list.unshift(cur); localStorage.setItem(KEY, JSON.stringify(list.slice(0, 8)));
    } catch (e) {}
  }
  var rc = $('#recent');
  if (rc) {
    var items = readRecent().filter(function(x){ return String(x.id) !== String(rc.getAttribute('data-skip') || ''); }).slice(0, 6);
    if (items.length) {
      var esc2 = function(s){ return String(s).replace(/[&<>"']/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); };
      $('.lgrid', rc).innerHTML = items.map(function(x){
        return '<a class="lcard" href="' + esc2(/^\/(?!\/)/.test(String(x.u)) ? x.u : '/') + '"><div class="cover">' + (x.c ? '<img src="' + esc2(/^\/(?!\/)/.test(String(x.c)) ? x.c : '') + '" alt="" loading="lazy">' : '<div class="cover-ph" style="--c:' + esc2(x.k || '#7c5cff') + '">' + esc2((x.t || '?').slice(0, 2)) + '</div>') + '</div><div class="lcard-body"><h3>' + esc2(x.t) + '</h3><div class="lcard-foot"><span class="price">' + esc2(x.p) + '</span></div></div></a>';
      }).join('');
      rc.hidden = false;
    }
  }
  // ---------- doping seçici (toplam tutar, bakiye uyarısı; fiyatı sunucu belirler) ----------
  $$('[data-doping]').forEach(function(box){
    var bal = parseInt(box.getAttribute('data-balance') || '0', 10) || 0;
    var totalEl = $('[data-doping-total]', box), leftEl = $('[data-doping-left]', box), warn = $('[data-doping-warn]', box);
    var calc = function(){
      var t = 0;
      $$('input[type=radio]:checked', box).forEach(function(r){ t += parseInt(r.getAttribute('data-price') || '0', 10) || 0; });
      if (totalEl) totalEl.textContent = fmt(t);
      if (leftEl) leftEl.textContent = (bal - t < 0 ? '-' : '') + fmt(Math.abs(bal - t));
      if (warn) warn.hidden = !(t > bal);
      box.classList.toggle('dp-short', t > bal);
    };
    box.addEventListener('change', calc); calc();
  });

  // ---------- CAPTCHA: "Yenile" sayfayı yeniden yüklemeden resmi yeniler ----------
  document.addEventListener('click', function(e){
    var a = e.target.closest && e.target.closest('[data-captcha-refresh]');
    if (!a) return;
    var box = a.closest('[data-captcha]'), img = box && $('.captcha-img', box);
    if (!img) return;
    e.preventDefault();
    img.src = (img.getAttribute('data-base') || '') + '?r=' + Date.now();
    var inp = $('input[name=captcha]', box);
    if (inp) { inp.value = ''; inp.focus(); }
  });
})();

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
