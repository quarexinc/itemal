"""Genel site şablonları (Jinja). Emoji kullanılmaz; ikonlar SVG sprite'ından gelir."""

TEMPLATES = {}

TEMPLATES["base.html"] = r"""
{%- from "_macros.html" import ic with context -%}
<!doctype html>
<html lang="tr" data-upmax="{{ upload_max }}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block title %}Ana Sayfa{% endblock %} | {{ site_name }}</title>
<meta name="description" content="{% block desc %}{{ cfg.meta_description or cfg.site_tagline }}{% endblock %}">
<meta name="theme-color" content="#0a0a0f">
<meta name="csrf" content="{{ csrf_token() }}">
<link rel="icon" type="image/svg+xml" href="{{ url_for('static', filename='favicon.svg') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
<script src="{{ url_for('static', filename='boot.js') }}"></script>
<script src="{{ url_for('static', filename='app.js') }}" defer></script>
{% block head_extra %}{% endblock %}
</head>
<body{% block body_class %}{% endblock %}{% block body_attr %}{% endblock %}{% if me %} data-live="{{ url_for('trust.live') }}" data-uid="{{ me.id }}"{% endif %}>
{% include "_sprite.html" %}
{% if cfg.announcement %}<div class="announce">{{ cfg.announcement }}</div>{% endif %}
{% block site_header %}
<header class="topbar" id="topbar">
  <div class="container topbar-in">
    <a class="brand" href="{{ url_for('index') }}"><img class="brand-mark" src="{{ url_for('static', filename='logo.svg') }}" width="32" height="32" alt="">{{ site_name }}</a>
    <nav class="nav" aria-label="Ana menü">
      <a href="{{ url_for('listings') }}" class="{{ 'on' if request.endpoint == 'listings' }}">İlanlar</a>
      <a href="{{ url_for('site.categories') }}" class="{{ 'on' if request.endpoint == 'site.categories' }}">Kategoriler</a>
      <a href="{{ url_for('site.sellers') }}" class="{{ 'on' if request.endpoint == 'site.sellers' }}">Mağazalar</a>
      <a href="{{ url_for('community.giveaways') }}" class="{{ 'on' if request.endpoint in ('community.giveaways', 'community.giveaway_view') }}">Çekilişler</a>
      <a href="{{ url_for('faq') }}" class="{{ 'on' if request.endpoint == 'faq' }}">Nasıl Çalışır</a>
      {% if me %}<a href="{{ url_for('tickets') }}" class="{{ 'on' if request.endpoint and request.endpoint.startswith('ticket') }}">Destek{% if answered_tickets %} <span class="dot-count">{{ answered_tickets }}</span>{% endif %}</a>{% endif %}
    </nav>
    <div class="search">
      <form action="{{ url_for('listings') }}" method="get" role="search">
        {{ ic('search') }}
        <input type="search" name="q" data-suggest="{{ url_for('site.search_suggest') }}" autocomplete="off" placeholder="Oyun, kart veya abonelik ara" value="{{ request.args.get('q', '') if request.endpoint == 'listings' }}" maxlength="60" aria-label="Ara">
        <kbd>/</kbd>
      </form>
      <div class="suggest" role="listbox"></div>
    </div>
    <div class="top-right">
      {% if me %}
        <a class="chip" href="{{ url_for('balance') }}" title="Bakiye yükle">{{ ic('wallet') }}<span id="bal-val">{{ me.balance|money }}</span></a>
        <a class="ibtn" href="{{ url_for('site.favorites') }}" title="Favorilerim" aria-label="Favorilerim">{{ ic('heart') }}<span class="dot" id="fav-count" {% if not fav_total %}hidden{% endif %}>{{ fav_total }}</span></a>
        <a class="ibtn" href="{{ url_for('inbox') }}" title="Mesajlar" aria-label="Mesajlar">{{ ic('message') }}{% if unread_chat %}<span class="dot">{{ unread_chat }}</span>{% endif %}</a>
        <div class="dd">
          <button class="ibtn" type="button" data-dd-toggle data-notif-url="{{ url_for('site.notif_read') }}" {% if notif_unread %}data-notif="{{ url_for('site.notif_read') }}"{% endif %} aria-label="Bildirimler">{{ ic('bell') }}{% if notif_unread %}<span class="dot">{{ notif_unread if notif_unread < 10 else '9+' }}</span>{% endif %}</button>
          <div class="dd-menu dd-notif">
            <div class="n-head"><span>Bildirimler</span><span class="row" style="gap:10px"><button type="button" class="link-btn" data-sound-toggle>Ses: Açık</button><a class="small" href="{{ url_for('site.notifications') }}">Tümü</a></span></div>
            <div class="n-list">
              {% for n in notif_recent %}
              <a class="n-item {{ 'unread' if not n.is_read }}" href="{{ url_for('site.notif_view', nid=n.id) }}"><b>{{ n.title }}</b>{% if n.body %}<small>{{ n.body }}</small>{% endif %}<small>{{ n.created_at|ago }}</small></a>
              {% else %}<div class="n-empty">Yeni bildirimin yok.</div>{% endfor %}
            </div>
          </div>
        </div>
        <div class="dd">
          <button class="ibtn" type="button" data-dd-toggle aria-label="Hesap menüsü">{{ ic('user') }}</button>
          <div class="dd-menu">
            <div class="dd-head"><b>{{ me.username }}</b>{{ pkg_marks(me.id) }}<small>{{ me.balance|money }} bakiye</small></div>
            <a href="{{ url_for('account') }}">{{ ic('home') }}Hesabım</a>
            <a href="{{ url_for('orders') }}">{{ ic('receipt') }}Siparişlerim</a>
            <a href="{{ url_for('balance') }}">{{ ic('wallet') }}Bakiye yükle</a>
            <a href="{{ url_for('site.favorites') }}">{{ ic('heart') }}Favorilerim</a>
            <a href="{{ url_for('community.following') }}">{{ ic('users') }}Takip ettiklerim</a>
            <a href="{{ url_for('profile') }}">{{ ic('settings') }}Profil ayarları</a>
            {% if can_sell %}<hr><a href="{{ url_for('seller.dashboard') }}">{{ ic('store') }}Satıcı paneli</a>{% endif %}
            {% if is_admin %}<a href="{{ url_for('admin.dashboard') }}">{{ ic('shield') }}Yönetim paneli</a>{% endif %}
            <hr>
            <form method="post" action="{{ url_for('logout') }}">{{ csrf_field() }}<button class="dd-item" type="submit">{{ ic('logout') }}Çıkış yap</button></form>
          </div>
        </div>
      {% else %}
        <a class="btn btn-ghost btn-sm" href="{{ url_for('login') }}">Giriş</a>
        <a class="btn btn-sm" href="{{ url_for('register') }}">Kayıt Ol</a>
        {% if is_admin %}<a class="chip" href="{{ url_for('admin.dashboard') }}">{{ ic('shield') }}Yönetim</a>{% endif %}
      {% endif %}
      <button class="ibtn nav-toggle" type="button" data-toggle-nav="#topbar" aria-label="Menü">{{ ic('menu') }}</button>
    </div>
  </div>
  <div class="catbar">
    <div class="catbar-in">
      <a class="all" href="{{ url_for('listings') }}">Tüm ilanlar</a>
      {% for c in nav_categories[:16] %}<a href="{{ url_for('listings', kategori=c.slug) }}" style="--c:{{ c.color or '#7c5cff' }}">{{ c.name }}</a>{% endfor %}
      <a class="all" href="{{ url_for('site.categories') }}">Tümü {{ ic('chevron-right') }}</a>
    </div>
  </div>
</header>
{% endblock %}

{% with msgs = get_flashed_messages(with_categories=true) %}
{% if msgs %}<div class="container flashes">{% for c, m in msgs %}<div class="flash flash-{{ c }}"><span>{{ m }}</span><button type="button" class="x" aria-label="Kapat">&times;</button></div>{% endfor %}</div>{% endif %}
{% endwith %}

{% if me %}<div class="perm-bar" id="perm-bar" hidden><span>Yeni mesaj ve bildirimleri sesli uyarıyla, sekme kapalıyken bile görmek ister misin?</span><div class="row"><button type="button" class="btn btn-sm" data-notif-enable>Bildirimleri aç</button><button type="button" class="btn btn-ghost btn-sm" data-notif-later>Sonra</button></div></div>{% endif %}
<main>{% block content %}{% endblock %}</main>

{% block site_footer %}
<footer class="footer">
  <div class="container">
    <div class="footer-in">
      <div>
        <a class="brand" href="{{ url_for('index') }}"><img class="brand-mark" src="{{ url_for('static', filename='logo.svg') }}" width="32" height="32" alt="">{{ site_name }}</a>
        <p class="mt small">{{ cfg.site_tagline }}. Kodlar satın alma anında hesabına teslim edilir; ödeme, sen onaylayana kadar emanette tutulur.</p>
        <div class="socials">
          {% if cfg.social_discord %}<a href="{{ cfg.social_discord }}" target="_blank" rel="noopener nofollow" aria-label="Discord">{{ ic('message') }}</a>{% endif %}
          {% if cfg.social_telegram %}<a href="{{ cfg.social_telegram }}" target="_blank" rel="noopener nofollow" aria-label="Telegram">{{ ic('send') }}</a>{% endif %}
          {% if cfg.social_instagram %}<a href="{{ cfg.social_instagram }}" target="_blank" rel="noopener nofollow" aria-label="Instagram">{{ ic('image') }}</a>{% endif %}
          <a href="mailto:{{ cfg.support_email }}" aria-label="E-posta">{{ ic('mail') }}</a>
        </div>
      </div>
      <div>
        <h4>Pazaryeri</h4>
        <ul>
          <li><a href="{{ url_for('listings') }}">Tüm ilanlar</a></li>
          <li><a href="{{ url_for('site.categories') }}">Kategoriler</a></li>
          <li><a href="{{ url_for('site.sellers') }}">Mağazalar</a></li>
          <li><a href="{{ url_for('seller_apply') }}">Satıcı ol</a></li>
          <li><a href="{{ url_for('faq') }}">Nasıl çalışır</a></li>
        </ul>
      </div>
      <div>
        <h4>Popüler kategoriler</h4>
        <ul>{% for c in nav_categories[:5] %}<li><a href="{{ url_for('listings', kategori=c.slug) }}">{{ c.name }}</a></li>{% endfor %}</ul>
      </div>
      <div>
        <h4>Destek</h4>
        <ul>
          <li><a href="{{ url_for('tickets') }}">Destek talebi oluştur</a></li>
          <li><a href="mailto:{{ cfg.support_email }}">{{ cfg.support_email }}</a></li>
          {% if cfg.support_hours %}<li>{{ cfg.support_hours }}</li>{% endif %}
        </ul>
      </div>
    </div>
    {% if pay_methods() %}<div class="pay-strip" aria-label="Kabul edilen ödeme yöntemleri"><span class="pay-lbl">Bakiye yükleme yöntemleri</span>{% for m in pay_methods() %}<a class="pay-chip" href="{{ url_for('balance', yontem=m.id) }}" style="--c:{{ m.color or '#7c5cff' }}">{{ ic(pay_icon(m.icon, m.kind)) }}{{ m.name }}</a>{% endfor %}</div>{% endif %}
    <div class="copy"><span>&copy; {{ year }} {{ site_name }}. Tüm hakları saklıdır.</span><span>Tüm fiyatlar Türk Lirası cinsindendir.</span></div>
  </div>
</footer>
{% endblock %}
</body>
</html>
"""

TEMPLATES["_macros.html"] = r"""
{% macro ic(name, cls='') %}<svg class="i {{ cls }}" aria-hidden="true"><use href="#i-{{ name }}"/></svg>{% endmacro %}

{% macro spark(values, w=120, h=28) %}
{%- set mx = values|max if values else 0 -%}
{%- set n = values|length -%}
{%- if n > 1 -%}
<svg class="spark" viewBox="0 0 {{ w }} {{ h }}" preserveAspectRatio="none" aria-hidden="true">
  {%- set ns = namespace(pts=[]) -%}
  {%- for v in values -%}
    {%- set x = (loop.index0 * w / (n - 1))|round(1) -%}
    {%- set y = (h - 3 - ((v / mx * (h - 6)) if mx else 0))|round(1) -%}
    {%- set ns.pts = ns.pts + [x ~ ',' ~ y] -%}
  {%- endfor -%}
  <path d="M0,{{ h }} L{{ ns.pts|join(' L') }} L{{ w }},{{ h }} Z"/>
  <polyline points="{{ ns.pts|join(' ') }}"/>
</svg>
{%- endif -%}
{% endmacro %}

{% macro badge(status) %}<span class="badge b-{{ status|sclass }}">{{ status|slabel }}</span>{% endmacro %}

{% macro stars(rating, small=false) %}<span class="stars{{ ' sm' if small }}" style="--v: {{ rating }}" role="img" aria-label="5 üzerinden {{ rating }}"></span>{% endmacro %}

{% macro rating_line(rating, count) %}
{% if count %}<span class="rate-line">{{ stars(rating, true) }}<b>{{ rating }}</b><span>({{ count }})</span></span>{% else %}<span class="rate-line">Henüz yorum yok</span>{% endif %}
{% endmacro %}

{% macro avatar(name, img, size='') %}<span class="avatar {{ size }}">{% if img %}<img src="{{ avatar_url(img) }}" alt="">{% else %}{{ (name or '?')[:1]|upper }}{% endif %}</span>{% endmacro %}

{% macro report_box(kind, action, label) %}
<details class="report-box"><summary>{{ ic('flag') }} {{ label }}</summary>
  <form method="post" action="{{ action }}">
    {{ csrf_field() }}
    <div class="field"><label>Neden</label><select name="reason" required><option value="">Seç</option>{% for r in REASONS[kind] %}<option>{{ r }}</option>{% endfor %}</select></div>
    <div class="field"><label>Ayrıntı</label><textarea name="detail" maxlength="600" placeholder="Ne olduğunu kısaca anlat"></textarea></div>
    <button class="btn btn-danger btn-sm" type="submit">Bildir</button>
  </form>
</details>
{% endmacro %}

{% macro badge_list(items) %}{% if items %}<div class="badges">{% for b in items %}<span class="bd {{ b.cls }}" title="{{ b.desc }}">{{ b.label }}</span>{% endfor %}</div>{% endif %}{% endmacro %}

{% macro cover(l, small=true) %}<div class="cover" style="--c:{{ l.cat_color or '#7c5cff' }}">{% if l.cover %}<img src="{{ cover_url(l.cover, small) }}" alt="{{ l.title }}" loading="lazy">{% else %}<div class="cover-ph">{{ l.cat_name|mono }}</div>{% endif %}</div>{% endmacro %}

{% macro fav_btn(lid) %}<button type="button" class="fav {{ 'on' if lid in fav_ids }}" data-fav="{{ url_for('site.favorite_toggle', lid=lid) }}" aria-label="Favorilere ekle / çıkar"><svg class="i" aria-hidden="true"><use href="#i-heart"/></svg></button>{% endmacro %}

{% macro listing_card(l) %}
<article class="lcard" style="--c:{{ l.cat_color or '#7c5cff' }}">
  <div class="cover">
    {% if l.cover %}<img src="{{ cover_url(l.cover, true) }}" alt="" loading="lazy">{% else %}<div class="cover-ph">{{ l.cat_name|mono }}</div>{% endif %}
    <span class="tag-l">{{ l.cat_name }}</span>
    {% if l.vitrin %}<span class="tag-v" title="Öne çıkarılan ilan">{{ ic('flame') }}Vitrin</span>{% endif %}
    {{ fav_btn(l.id) }}
    {% if l.old_price and l.old_price > l.price %}<span class="tag-b disc">-%{{ ((l.old_price - l.price) * 100 // l.old_price) }}</span>{% endif %}
  </div>
  <div class="lcard-body">
    <h3><a href="{{ url_for('listing_detail', lid=l.id) }}">{{ l.title }}</a></h3>
    <div class="lcard-meta"><span class="nm">{{ l.seller_display }}</span>{{ pkg_marks(l) }}{% if l.seller_kyc == 'approved' %}<span class="vf" title="Kimliği doğrulanmış satıcı">{{ ic('shield-check') }}</span>{% endif %}{{ rating_line(rating_of(l), l.rating_count) }}</div>
    <div class="lcard-foot">
      <div>{% if l.old_price and l.old_price > l.price %}<span class="price-old">{{ l.old_price|money }}</span>{% endif %}<span class="price">{{ l.price|money }}</span></div>
      {% if l.stock > 5 %}<span class="stock">Stokta</span>{% elif l.stock > 0 %}<span class="stock low">Son {{ l.stock }}</span>{% else %}<span class="stock out">Tükendi</span>{% endif %}
    </div>
  </div>
</article>
{% endmacro %}

{% macro strip(b) %}
<a class="strip-ad" href="{{ url_for('site.banner_go', bid=b.id) }}" style="--c1:{{ b.color1 }};--c2:{{ b.color2 }}">
  {% if b.image %}<img class="bg" src="{{ url_for('media_cover', name=b.image) }}" alt="">{% endif %}
  <div><b>{{ b.title }}</b>{% if b.subtitle %}<span class="sub">{{ b.subtitle }}</span>{% endif %}</div>
  {% if b.cta_text %}<span class="go">{{ b.cta_text }} {{ ic('arrow-right') }}</span>{% endif %}
</a>
{% endmacro %}

{% macro empty(text, hint='') %}<div class="empty"><strong>{{ text }}</strong>{% if hint %}<div class="small mt">{{ hint }}</div>{% endif %}</div>{% endmacro %}

{% macro pager(page) %}
{% if page.pages > 1 %}
<nav class="pager" aria-label="Sayfalar">
  {% if page.page > 1 %}<a href="{{ page_url(page.page - 1) }}">Önceki</a>{% endif %}
  {% for n in range(1, page.pages + 1) %}
    {% if n == page.page %}<span class="on">{{ n }}</span>
    {% elif n <= 1 or n > page.pages - 1 or (n - page.page)|abs <= 2 %}<a href="{{ page_url(n) }}">{{ n }}</a>
    {% elif (n - page.page)|abs == 3 %}<span>...</span>{% endif %}
  {% endfor %}
  {% if page.page < page.pages %}<a href="{{ page_url(page.page + 1) }}">Sonraki</a>{% endif %}
</nav>
{% endif %}
{% endmacro %}

{% macro status_tabs(endpoint, status, counts) %}
<div class="tabs">
{% for key, label in [('pending', 'Bekleyen'), ('approved', 'Onaylanan'), ('rejected', 'Reddedilen'), ('all', 'Tümü')] %}
  <a class="{{ 'on' if status == key }}" href="{{ url_for(endpoint, durum=key) }}">{{ label }}{% if key != 'all' %} <span class="cnt">{{ counts[key] }}</span>{% endif %}</a>
{% endfor %}
</div>
{% endmacro %}

{% macro bars(series, is_money=false) %}
<div class="bars">
{% for b in series %}
  <div class="bar" title="{{ b.label }}: {{ b.value|money if is_money else b.value }}">
    <div class="bar-track"><span class="bar-fill" style="height: {{ b.pct }}%"></span></div>
    <em>{{ b.label }}</em>
  </div>
{% endfor %}
</div>
{% endmacro %}
"""

TEMPLATES["index.html"] = r"""
{% extends "base.html" %}
{% from "_macros.html" import listing_card, strip, empty, ic, avatar, badge_list, stars with context %}
{% block title %}Güvenli E-pin Pazaryeri{% endblock %}
{% block content %}

<section class="hero-wrap">
  <div class="container">
    <div class="slider" data-slider data-interval="{{ cfg.hero_seconds or 6 }}">
      {% for b in hero %}
      <div class="slide{{ ' ad' if b.is_ad }}" style="--c1:{{ b.color1 }};--c2:{{ b.color2 }}">
        <span class="shape a"></span><span class="shape b"></span><span class="shape c"></span>
        {% if b.image %}<img class="slide-img" src="{{ url_for('media_cover', name=b.image) }}" alt="">{% endif %}
        <div class="slide-body">
          <span class="kicker{{ ' kicker-ad' if b.is_ad }}">{{ ic('bolt') }} {{ 'Reklam' if b.is_ad else 'Kampanya' }}</span>
          <h2>{{ b.title }}</h2>
          {% if b.subtitle %}<p>{{ b.subtitle }}</p>{% endif %}
          {% if b.cta_text %}<a class="btn btn-lg" href="{{ url_for('site.banner_go', bid=b.id) }}">{{ b.cta_text }} {{ ic('arrow-right') }}</a>{% endif %}
        </div>
      </div>
      {% else %}
      <div class="slide" style="--c1:#5b3fd6;--c2:#1b1140">
        <span class="shape a"></span><span class="shape b"></span><span class="shape c"></span>
        <div class="slide-body">
          <span class="kicker">{{ ic('bolt') }} {{ site_name }}</span>
          <h2>Oyun ve dijital kodlar, anında teslim.</h2>
          <p>{{ cfg.site_tagline }}.</p>
          <a class="btn btn-lg" href="{{ url_for('listings') }}">İlanlara göz at {{ ic('arrow-right') }}</a>
        </div>
      </div>
      {% endfor %}
      <div class="dots"></div>
      <button class="sl-arrow sl-prev" type="button" data-dir="-1" aria-label="Önceki">{{ ic('chevron-left') }}</button>
      <button class="sl-arrow sl-next" type="button" data-dir="1" aria-label="Sonraki">{{ ic('chevron-right') }}</button>
    </div>

    <div class="trust">
      <div><span class="ti">{{ ic('bolt') }}</span><span><b>Anında teslimat</b><small>Kod ödeme anında hesabında</small></span></div>
      <div><span class="ti">{{ ic('shield-check') }}</span><span><b>Emanet korumalı</b><small>Onaylayana kadar bloke</small></span></div>
      <div><span class="ti">{{ ic('lock') }}</span><span><b>Güvenli bakiye</b><small>Tüm işlemler kayıt altında</small></span></div>
      <div><span class="ti">{{ ic('life-buoy') }}</span><span><b>Canlı destek</b><small>{{ cfg.support_hours or 'Her gün' }}</small></span></div>
    </div>
  </div>
</section>

{% if ticker %}
<div class="ticker mt" aria-label="Canlı akış">
  <div class="ticker-track">
    {% for rep in range(2) %}{% for t in ticker %}
    <span class="ticker-item"><span class="live"></span>
      {% if t.kind == 'sale' %}<b>{{ t.who|mask }}</b> satın aldı: {{ t.text }}{% if t.qty > 1 %} x{{ t.qty }}{% endif %}
      {% else %}<b>{{ t.who }}</b>{{ pkg_marks(t.uid) }} yeni ilan ekledi: {{ t.text }}{% endif %}
      <span class="dim">{{ t.at|ago }}</span></span>
    {% endfor %}{% endfor %}
  </div>
</div>
{% endif %}

<section class="section reveal">
  <div class="container">
    <div class="section-h">
      <div><h2>{{ ic('flame') }} Günün oyunları</h2><p>En çok tercih edilen oyun ve platformlar, tek tıkla ilanlara git.</p></div>
      <div class="deal-head"><span class="small muted">Gün sonuna</span>
        <div class="countdown" data-countdown="{{ left }}"><span class="h">00<small>sa</small></span><span class="m">00<small>dk</small></span><span class="s">00<small>sn</small></span></div>
      </div>
    </div>
    <div class="posters">
      {% for c in daily[:8] %}
      <a class="poster reveal" data-tilt style="--c:{{ c.color or '#7c5cff' }};--d:{{ loop.index0 }}" href="{{ url_for('listings', kategori=c.slug) }}">
        <img src="{{ category_banner_url(c, 'card') }}" alt="{{ c.name }}" loading="lazy" width="720" height="960">
        <span class="poster-tag">{{ ic('flame') }} Günün seçimi</span>
        <div class="poster-body"><b>{{ c.name }}</b><small>{% if c.n %}{{ c.n }} ilan &middot; {{ c.min_price|money }}'den başlayan{% else %}{{ c.tagline or 'Yakında' }}{% endif %}</small></div>
      </a>
      {% endfor %}
    </div>
  </div>
</section>

{% if strips|length > 0 %}<section class="container reveal">{{ strip(strips[0]) }}</section>{% endif %}

<section class="section reveal">
  <div class="container">
    <div class="section-h">
      <div><h2>{{ ic('grid') }} Kategoriler</h2><p>{{ categories|length }} kategoride oyun kodu, hediye kartı ve abonelik.</p></div>
      <a class="more" href="{{ url_for('site.categories') }}">Tümünü gör {{ ic('arrow-right') }}</a>
    </div>
    <div class="cat-filter">
      <button type="button" class="on" data-g="*">Tümü</button>
      {% for g in groups %}<button type="button" data-g="{{ g }}">{{ g }}</button>{% endfor %}
    </div>
    <div class="cat-grid">
      {% for c in categories %}
      <a class="cat-tile" data-g="{{ c.grp }}" style="--c:{{ c.color or '#7c5cff' }}" href="{{ url_for('listings', kategori=c.slug) }}">
        <span class="cat-ic cat-ic-img"><img src="{{ category_banner_url(c, 'card') }}" alt="" loading="lazy"></span>
        <span><b>{{ c.name }}</b><small>{{ c.n }} ilan</small></span>
      </a>
      {% endfor %}
    </div>
  </div>
</section>

{% if deals %}
<section class="section reveal">
  <div class="container">
    <div class="section-h">
      <div><h2>{{ ic('percent') }} Fırsat ürünleri</h2><p>Sınırlı süreli indirimler.</p></div>
      <a class="more" href="{{ url_for('listings', sirala='ucuz') }}">Daha fazla {{ ic('arrow-right') }}</a>
    </div>
    <div class="lgrid">{% for l in deals %}{{ listing_card(l) }}{% endfor %}</div>
  </div>
</section>
{% endif %}

{% if featured %}
<section class="section reveal">
  <div class="container">
    <div class="section-h"><div><h2>{{ ic('crown') }} Öne çıkan ilanlar</h2><p>Editörlerin ve alıcıların seçtikleri.</p></div></div>
    <div class="lgrid">{% for l in featured %}{{ listing_card(l) }}{% endfor %}</div>
  </div>
</section>
{% endif %}

{% if strips|length > 1 %}<section class="container reveal">{{ strip(strips[1]) }}</section>{% endif %}

<section class="section reveal">
  <div class="container">
    <div class="section-h"><div><h2>{{ ic('clock') }} Yeni eklenenler</h2><p>Satıcıların az önce yayınladığı ilanlar.</p></div><a class="more" href="{{ url_for('listings') }}">Tüm ilanlar {{ ic('arrow-right') }}</a></div>
    {% if latest %}<div class="lgrid">{% for l in latest %}{{ listing_card(l) }}{% endfor %}</div>
    {% else %}<div class="card">{{ empty('Henüz ilan yok', 'İlk ilanı vermek için satıcı başvurusu yap.') }}</div>{% endif %}
  </div>
</section>

{% if popular %}
<section class="section reveal">
  <div class="container">
    <div class="section-h"><div><h2>{{ ic('trend') }} Çok satanlar</h2><p>Bu hafta en çok tercih edilenler.</p></div></div>
    <div class="lgrid">{% for l in popular %}{{ listing_card(l) }}{% endfor %}</div>
  </div>
</section>
{% endif %}

{% for b in strips[2:] %}<section class="container reveal mt">{{ strip(b) }}</section>{% endfor %}

{% if seller_cards %}
<section class="section reveal">
  <div class="container">
    <div class="section-h"><div><h2>{{ ic('store') }} Öne çıkan satıcılar</h2><p>Satış ve puanlarına göre en güvenilir mağazalar.</p></div><a class="more" href="{{ url_for('site.sellers') }}">Tüm mağazalar {{ ic('arrow-right') }}</a></div>
    <div class="sellers">
      {% for sc in seller_cards %}{% set s = sc.u %}
      <a class="seller-card{{ ' pk-gold' if s.pk_rank == 1 }}{{ ' pk-diamond' if s.pk_rank == 2 }}" href="{{ url_for('storefront', username=s.username) }}">
        {{ avatar(s.username, s.avatar) }}
        <div>
          <b>{{ s.store_name or s.username }}{{ pkg_marks(s.id) }}</b>
          <div class="small muted">{% if s.rc %}<span class="pos">{{ '%.1f'|format(s.avg) }}</span> puan &middot; {% endif %}{{ s.sold }} satış &middot; {{ s.n_listings }} ilan</div>
          {{ badge_list(sc.badges) }}
        </div>
      </a>
      {% endfor %}
    </div>
  </div>
</section>
{% endif %}

{% if reviews %}
<section class="section reveal">
  <div class="container">
    <div class="section-h"><div><h2>{{ ic('star') }} Alıcı yorumları</h2><p>Alıcıların bıraktığı son değerlendirmeler.</p></div></div>
    <div class="revs">
      {% for r in reviews %}
      <a class="rev-card" href="{{ url_for('listing_detail', lid=r.lid) }}">
        {{ stars(r.rating, true) }}
        <p>{{ r.comment }}</p>
        <div class="small muted"><b>{{ r.buyer_name|mask }}</b> &middot; {{ r.listing_title }}</div>
      </a>
      {% endfor %}
    </div>
  </div>
</section>
{% endif %}

<section class="section reveal">
  <div class="container">
    <div class="stat-band">
      <div><b data-count="{{ stats.sold }}">{{ stats.sold }}</b><span>teslim edilen kod</span></div>
      <div><b data-count="{{ stats.listings }}">{{ stats.listings }}</b><span>aktif ilan</span></div>
      <div><b data-count="{{ stats.sellers }}">{{ stats.sellers }}</b><span>satıcı</span></div>
      <div><b data-count="{{ stats.users }}">{{ stats.users }}</b><span>üye</span></div>
    </div>
  </div>
</section>

<section class="section reveal">
  <div class="container">
    <div class="section-h"><div><h2>Nasıl çalışır?</h2></div><a class="more" href="{{ url_for('faq') }}">Ayrıntılar {{ ic('arrow-right') }}</a></div>
    <div class="steps">
      <div class="step"><h3>Bakiye yükle</h3><p>Aktif ödeme yöntemlerinden birini seç, bildirimini gönder.</p></div>
      <div class="step"><h3>İlanı seç</h3><p>Kategori, fiyat ve satıcı puanına göre karşılaştır.</p></div>
      <div class="step"><h3>Satın al</h3><p>Kodlar ödeme anında sipariş sayfanda görünür.</p></div>
      <div class="step"><h3>Değerlendir</h3><p>Satıcıya puan ver, sorun olursa destek talebi aç.</p></div>
    </div>
    {% if not can_sell %}
    <div class="cta-band mt">
      <div><h3>Sen de satmaya başla</h3><p>Kimliğini doğrula, ilan ver, kazancını çek. Komisyon oranı ilan verirken net kazancınla birlikte görünür.</p></div>
      <a class="btn btn-lg" href="{{ url_for('seller_apply') }}">Satıcı ol {{ ic('arrow-right') }}</a>
    </div>
    {% endif %}
  </div>
</section>
{% endblock %}
"""

TEMPLATES["listings.html"] = r"""
{% extends "base.html" %}
{% from "_macros.html" import listing_card, pager, empty, ic with context %}
{% set cur = (nav_categories|selectattr('slug', 'equalto', cat)|first) if cat else none %}
{% block title %}{{ cur.name if cur else 'İlanlar' }}{% endblock %}
{% block content %}
<div class="container section">
  {% if cur %}
  {% if cur.image %}
  <div class="cat-hero" style="--c:{{ cur.color or '#7c5cff' }}">
    <img class="hero-img" src="{{ category_banner_url(cur, 'wide') }}" alt="">
    <span class="cat-ic">{{ cur.name|mono }}</span>
    <div><h1>{{ cur.name }}</h1><p>{{ cur.tagline }}</p></div>
    <span class="badge b-muted">{{ page.total }} ilan</span>
  </div>
  {% else %}
  <div class="cat-banner" style="--c:{{ cur.color or '#7c5cff' }}">
    <picture>
      <source media="(max-width:640px)" srcset="{{ category_banner_url(cur, 'mobile') }}">
      <img src="{{ category_banner_url(cur, 'wide') }}" alt="{{ cur.name }}" width="1600" height="480" fetchpriority="high">
    </picture>
    <h1 class="sr-only">{{ cur.name }}</h1>
    <span class="cat-banner-count">{{ page.total }} ilan</span>
  </div>
  {% endif %}
  {% else %}
  <div class="page-h"><h1>Tüm ilanlar</h1><span class="muted">{{ page.total }} sonuç</span></div>
  {% endif %}

  <div class="chips">
    <a class="chip-c {{ 'on' if not cat }}" href="{{ url_for('listings', q=text or none, sirala=sort if sort != 'yeni' else none) }}">Hepsi</a>
    {% for c in nav_categories[:14] %}<a class="chip-c {{ 'on' if c.slug == cat }}" style="--c:{{ c.color or '#7c5cff' }}" href="{{ url_for('listings', kategori=c.slug, q=text or none) }}">{{ c.name }}</a>{% endfor %}
  </div>

  <form class="card filters" method="get" action="{{ url_for('listings') }}">
    <div class="field grow"><label for="q">Ara</label><input type="search" id="q" name="q" value="{{ text }}" placeholder="İlan başlığı veya açıklama" maxlength="60"></div>
    <div class="field"><label for="kategori">Kategori</label>
      <select id="kategori" name="kategori"><option value="">Tümü</option>{% for c in nav_categories %}<option value="{{ c.slug }}" {{ 'selected' if c.slug == cat }}>{{ c.name }}</option>{% endfor %}</select></div>
    <div class="field"><label for="min">En az (TL)</label><input type="text" inputmode="decimal" id="min" name="min" value="{{ pmin }}" placeholder="0"></div>
    <div class="field"><label for="max">En çok (TL)</label><input type="text" inputmode="decimal" id="max" name="max" value="{{ pmax }}" placeholder="10.000"></div>
    <div class="field"><label for="puan">Puan</label>
      <select id="puan" name="puan"><option value="">Hepsi</option>{% for n in (5, 4, 3) %}<option value="{{ n }}" {{ 'selected' if min_rating == n }}>{{ n }} ve üzeri</option>{% endfor %}</select></div>
    <div class="field"><label for="sirala">Sırala</label>
      <select id="sirala" name="sirala">
        {% for k, v in [('yeni', 'En yeni'), ('onerilen', 'Önerilen'), ('populer', 'En çok satan'), ('puan', 'En yüksek puan'), ('ucuz', 'Fiyat: artan'), ('pahali', 'Fiyat: azalan')] %}<option value="{{ k }}" {{ 'selected' if sort == k }}>{{ v }}</option>{% endfor %}
      </select></div>
    <label class="check field"><input type="checkbox" name="stok" value="1" {{ 'checked' if only_stock }}> Sadece stokta olanlar</label>
    <div class="field"><button class="btn" type="submit">{{ ic('filter') }} Filtrele</button></div>
  </form>
  {% if vitrin_cat %}
  <section class="vitrin" aria-label="Kategori vitrini">
    <div class="vitrin-h"><h2>{{ ic('flame') }} Kategori vitrini</h2><span class="muted small">{{ cur.name if cur }} kategorisinde öne çıkanlar</span></div>
    <div class="lgrid">{% for l in vitrin_cat %}{{ listing_card(l) }}{% endfor %}</div>
  </section>
  {% endif %}
  {% if vitrin_market %}
  <section class="vitrin" aria-label="Vitrin">
    <div class="vitrin-h"><h2>{{ ic('flame') }} Vitrin</h2><span class="muted small">Öne çıkan ilanlar</span></div>
    <div class="lgrid">{% for l in vitrin_market %}{{ listing_card(l) }}{% endfor %}</div>
  </section>
  {% endif %}
  {% if (vitrin_cat or vitrin_market) and page.rows %}<div class="vitrin-sep"><span>Tüm ilanlar</span></div>{% endif %}
  {% if page.rows %}<div class="lgrid">{% for l in page.rows %}{{ listing_card(l) }}{% endfor %}</div>{{ pager(page) }}
  {% else %}<div class="card">{{ empty('Aramana uygun ilan bulunamadı', 'Filtreleri değiştirmeyi dene ya da başka bir kategoriye göz at.') }}</div>{% endif %}
</div>
{% endblock %}
"""

TEMPLATES["listing.html"] = r"""
{% extends "base.html" %}
{% from "_macros.html" import cover, stars, rating_line, badge_list, avatar, listing_card, fav_btn, report_box, ic with context %}
{% block title %}{{ l.title }}{% endblock %}
{% block desc %}{{ (l.description or l.title)[:150] }}{% endblock %}
{% block body_attr %}{% if visible %} data-view='{{ {"id": l.id, "t": l.title, "p": l.price|money, "u": url_for("listing_detail", lid=l.id), "c": cover_url(l.cover, true), "k": l.cat_color or "#7c5cff"}|tojson }}'{% endif %}{% endblock %}
{% block content %}
<div class="container">
  <div class="crumbs"><a href="{{ url_for('index') }}">Ana sayfa</a><span class="sepx">/</span><a href="{{ url_for('listings', kategori=l.cat_slug) }}">{{ l.cat_name }}</a><span class="sepx">/</span><span>{{ l.title }}</span></div>
  {% if not visible %}<div class="notice warn">Bu ilan şu an herkese açık değil ({{ l.status|slabel }}). Yalnızca sen ve yönetim görebilir.</div>{% endif %}
  <div class="detail">
    <div>
      <div class="gallery" style="--c:{{ l.cat_color or '#7c5cff' }}">
        <div class="cover wide">{% if l.cover %}<img src="{{ cover_url(l.cover) }}" alt="{{ l.title }}">{% else %}<div class="cover-ph">{{ l.cat_name|mono }}</div>{% endif %}
          <span class="tag-l">{{ l.cat_name }}</span>
          {% if l.old_price and l.old_price > l.price %}<span class="tag-b disc">-%{{ ((l.old_price - l.price) * 100 // l.old_price) }}</span>{% endif %}
        </div>
      </div>
      <div class="card mt">
        <div class="row mb"><span class="badge b-muted">{{ l.cat_name }}</span>{% if l.is_featured %}<span class="badge b-warn">Öne çıkan</span>{% endif %}{{ rating_line(rating_of(l), l.rating_count) }}<span class="muted small">{{ l.sales_count }} satış</span><span class="muted small">{{ fav_count }} favori</span></div>
        <h1>{{ l.title }}</h1>
        <h3 class="mt">Açıklama</h3>
        <div class="pre">{{ l.description or 'Satıcı açıklama eklememiş.' }}</div>
        <hr>
        <div class="notice">Teslimat anında yapılır: ödemeden sonra kodlar sipariş sayfanda görünür. Tutar, sen siparişi onaylayana kadar emanette kalır.</div>
      </div>
      <div class="card mt">
        <div class="card-h"><h2>Yorumlar</h2>{{ rating_line(rating_of(l), l.rating_count) }}</div>
        {% for r in reviews %}
        <div class="review">
          <div class="who">{{ stars(r.rating, true) }}<b>{{ r.buyer_name|mask }}</b><span class="muted small">{{ r.created_at|dt(false) }}</span></div>
          <div class="pre">{{ r.comment or 'Yorum yazılmadı.' }}</div>
          {% if r.seller_reply %}<div class="reply"><b>Satıcı yanıtı:</b> {{ r.seller_reply }}</div>{% endif %}
        </div>
        {% else %}<p class="muted">Bu ilan için henüz yorum yok. Yorumlar yalnızca gerçek satın alımların ardından yazılabilir.</p>{% endfor %}
      </div>
    </div>

    <aside>
      <div class="card buybox">
        <div class="spread">
          <div>{% if l.old_price and l.old_price > l.price %}<span class="price-old">{{ l.old_price|money }}</span>{% endif %}<strong class="price">{{ l.price|money }}</strong></div>
          {% if l.stock > 5 %}<span class="stock">Stokta {{ l.stock }}</span>{% elif l.stock > 0 %}<span class="stock low">Son {{ l.stock }} adet</span>{% else %}<span class="stock out">Tükendi</span>{% endif %}
        </div>
        <hr>
        {% if seller_vacation and not is_owner %}<div class="vac-note">{{ ic('clock') }}<span>Bu mağaza şu an tatilde; yeni sipariş almıyor.</span></div>{% endif %}
        {% if is_owner %}
          <p class="muted">Bu senin ilanın.</p>
          <div class="row"><a class="btn btn-sm" href="{{ url_for('seller.listing_edit', lid=l.id) }}">Düzenle</a><a class="btn btn-ghost btn-sm" href="{{ url_for('seller.stock', lid=l.id) }}">Stok</a></div>
        {% elif not visible %}
          <button class="btn btn-block" disabled>Satışta değil</button>
        {% elif me %}
          {% if l.stock > 0 %}
          <form method="post" action="{{ url_for('buy', lid=l.id) }}" data-confirm="Satın alma onaylansın mı? Tutar bakiyenden düşülür.">
            {{ csrf_field() }}
            <label for="qty">Adet</label>
            <div class="stepper"><button type="button" data-step="-1" aria-label="Azalt">-</button><input type="number" id="qty" name="qty" min="1" max="{{ max_qty }}" value="1" data-price="{{ l.price }}"><button type="button" data-step="1" aria-label="Artır">+</button></div>
            <div class="coupon-row">
              <label for="coupon">Kupon kodu</label>
              <div class="input-btn"><input type="text" id="coupon" name="coupon" maxlength="40" placeholder="Varsa kodu gir" autocomplete="off"><button class="btn btn-ghost" type="button" id="coupon-apply" data-url="{{ url_for('site.coupon_check', lid=l.id) }}">Uygula</button></div>
              <div class="coupon-msg" id="coupon-msg"></div>
            </div>
            <div class="total-row" id="discount-row" hidden><span>İndirim</span><strong class="pos" id="discount-val">-</strong></div>
            <div class="total-row"><span>Toplam</span><strong id="total">{{ l.price|money }}</strong></div>
            <button class="btn btn-block btn-lg shine" type="submit" {{ 'disabled' if seller_vacation }}>{{ ic('cart') }} {{ 'Mağaza tatilde' if seller_vacation else 'Satın Al' }}</button>
          </form>
          <p class="small muted mt">Bakiyen: <b>{{ me.balance|money }}</b>{% if me.balance < l.price %} &middot; <a href="{{ url_for('balance', tutar=((l.price - me.balance) / 100)|round(0, 'ceil')|int) }}">Bakiye yükle</a>{% endif %}</p>
          {% if me.balance < l.price %}<div class="topup-hint">{{ ic('wallet') }}<span>Bu ilan için <b>{{ (l.price - me.balance)|money }}</b> eksik. {% if pay_methods() %}Havale, Papara ve kripto ile yükleyebilirsin.{% else %}Bakiye yükleyip tekrar dene.{% endif %}</span></div>{% endif %}
          {% else %}<button class="btn btn-block" disabled>Stok tükendi</button>{% endif %}
          <form method="post" action="{{ url_for('chat_start', lid=l.id) }}" class="mt">{{ csrf_field() }}<button class="btn btn-line btn-block" type="submit">{{ ic('message') }} Satıcıya mesaj yaz</button></form>
        {% else %}
          <a class="btn btn-block btn-lg" href="{{ url_for('login', next=request.path) }}">Satın almak için giriş yap</a>
          <p class="small muted mt center">Hesabın yok mu? <a href="{{ url_for('register') }}">Kayıt ol</a></p>
        {% endif %}
        <div class="share-row">
          <button type="button" class="btn btn-ghost btn-sm {{ 'on' if l.id in fav_ids }}" data-fav="{{ url_for('site.favorite_toggle', lid=l.id) }}" style="flex:1">{{ ic('heart') }} Favori</button>
          <button type="button" class="btn btn-ghost btn-sm" data-share style="flex:1">{{ ic('share') }} Paylaş</button>
        </div>
        {% if me and not is_owner %}{{ report_box('listing', url_for('trust.report_listing', lid=l.id), 'İlanı bildir') }}{% endif %}
        <ul class="perks">
          <li>{{ ic('bolt') }}<span>Kod ödeme anında teslim edilir</span></li>
          <li>{{ ic('shield-check') }}<span>Ödeme, sen onaylayana kadar emanette</span></li>
          <li>{{ ic('life-buoy') }}<span>Sorun olursa destek talebi aç</span></li>
        </ul>
      </div>

      <div class="card mt">
        <div class="seller-box">
          {{ avatar(seller.username, seller.avatar, 'lg') }}
          <div>
            <a href="{{ url_for('storefront', username=seller.username) }}"><b>{{ l.seller_display }}</b></a>{{ pkg_marks(l) }}
            <div class="muted small">@{{ seller.username }}</div>
            {{ rating_line(seller_stats.rating, seller_stats.reviews) }}
          </div>
        </div>
        <div class="mt">{{ badge_list(seller_badges) }}</div>
        <dl class="kv mt">
          <dt>Toplam satış</dt><dd>{{ seller_stats.sold }} adet</dd>
          <dt>Üyelik</dt><dd>{{ seller.created_at|dt(false) }}</dd>
        </dl>
        <div class="row mt"><a class="btn btn-ghost" style="flex:1" href="{{ url_for('storefront', username=seller.username) }}">Mağazayı gör</a>{% if not me or me.id != seller.id %}<form class="inline-form" method="post" action="{{ url_for('community.follow_toggle', sid=seller.id) }}">{{ csrf_field() }}<button class="btn btn-line" type="submit">{{ ic('users') }}Takip et</button></form>{% endif %}</div>
      </div>
    </aside>
  </div>

  {% if others %}
  <div class="section"><div class="section-h"><h2>Bu satıcının diğer ilanları</h2></div><div class="lgrid">{% for r in others %}{{ listing_card(r) }}{% endfor %}</div></div>
  {% endif %}
  {% if related %}
  <div class="section"><div class="section-h"><h2>Benzer ilanlar</h2></div><div class="lgrid">{% for r in related %}{{ listing_card(r) }}{% endfor %}</div></div>
  {% endif %}
  <div class="section" id="recent" data-skip="{{ l.id }}" hidden><div class="section-h"><h2>Son gezdiklerin</h2></div><div class="lgrid"></div></div>
</div>
{% endblock %}
"""

TEMPLATES["storefront.html"] = r"""
{% extends "base.html" %}
{% from "_macros.html" import listing_card, pager, empty, avatar, badge_list, rating_line, stars, report_box, ic with context %}
{% from "_community.html" import follow_btn, gw_card with context %}
{% block title %}{{ seller.store_name or seller.username }}{% endblock %}
{% block content %}
<div class="container section{{ ' store-themed' if theme_css }}"{% if theme_css %} style="{{ theme_css }}"{% endif %}>
  {% if vacation %}<div class="store-vac">{{ ic('clock') }}<span>Bu mağaza şu an tatilde{% if vacation_until %} ({{ vacation_until|dt(false) }} tarihine kadar){% endif %}. İlanlar görüntülenebilir ancak yeni sipariş alınmıyor.</span></div>{% endif %}
  {% if seller.store_notice %}<div class="store-notice">{{ ic('megaphone') }}<span>{{ seller.store_notice }}</span></div>{% endif %}
  {% set pk = pkg_tier(seller.id) %}
  <div class="card store-card{{ ' has-banner' if seller.store_banner }}{{ ' pk-' ~ pk if pk }}">
    {% if seller.store_banner %}<div class="store-banner"><img src="{{ url_for('media_cover', name=seller.store_banner) }}" alt=""></div>{% endif %}
    <div class="store-head">
      {{ avatar(seller.username, seller.avatar, 'lg') }}
      <div class="grow-1">
        <h1 class="mb0">{{ seller.store_name or seller.username }}{{ pkg_marks(seller.id) }}</h1>
        <div class="muted small mb">@{{ seller.username }} &middot; {{ seller.created_at|dt(false) }} tarihinden beri üye</div>
        {{ badge_list(badges) }}
        {% if seller.store_desc %}<p class="mt pre">{{ seller.store_desc }}</p>{% endif %}
        {% if socials %}<div class="store-links">{% for s in socials %}<a href="{{ s.url }}" target="_blank" rel="nofollow noopener noreferrer ugc">{{ ic(s.icon) }}{{ s.label }}</a>{% endfor %}</div>{% endif %}
        <div class="store-links"><a href="#" data-copy="{{ store_link }}" onclick="return false">{{ ic('copy') }}Mağaza adresini kopyala</a></div>
        {% if me and me.id != seller.id %}{{ report_box('user', url_for('trust.report_user', username=seller.username), 'Kullanıcıyı bildir') }}{% endif %}
      </div>
      <div class="store-side">
        {% if not me or me.id != seller.id %}{{ follow_btn(seller.id, i_follow, followers) }}{% endif %}
        <div class="grid g2 store-stats">
          <div class="stat good"><div class="k">Başarılı işlem</div><div class="v">{{ ok_orders }}</div><div class="s">{% if ok_rate is not none %}%{{ ok_rate }} başarı oranı{% else %}Tamamlanan sipariş{% endif %}</div></div>
          <div class="stat"><div class="k">Puan</div><div class="v">{{ stats.rating if stats.reviews else '-' }}</div><div class="s">{{ stats.reviews }} yorum</div></div>
          <div class="stat"><div class="k">İlan</div><div class="v">{{ page.total }}</div></div>
          <div class="stat"><div class="k">Takipçi</div><div class="v">{{ followers }}</div></div>
        </div>
      </div>
    </div>
  </div>

  {% if store_gws %}<div class="section-h mt"><h2>{{ ic('gift') }} Çekilişler</h2></div><div class="gw-grid">{% for gw in store_gws %}{{ gw_card(gw, false, gw_left(gw.ends_at)) }}{% endfor %}</div>{% endif %}
  <div class="section-h mt"><h2>İlanlar</h2></div>
  {% if page.rows %}<div class="lgrid">{% for l in page.rows %}{{ listing_card(l) }}{% endfor %}</div>{{ pager(page) }}
  {% else %}<div class="card">{{ empty('Bu mağazanın aktif ilanı yok') }}</div>{% endif %}

  <div class="card mt">
    <div class="card-h"><h2>Son yorumlar</h2>{{ rating_line(stats.rating, stats.reviews) }}</div>
    {% for r in reviews %}
    <div class="review">
      <div class="who">{{ stars(r.rating, true) }}<b>{{ r.buyer_name|mask }}</b><span class="muted small">{{ r.listing_title }} &middot; {{ r.created_at|dt(false) }}</span></div>
      <div class="pre">{{ r.comment or 'Yorum yazılmadı.' }}</div>
      {% if r.seller_reply %}<div class="reply"><b>Satıcı yanıtı:</b> {{ r.seller_reply }}</div>{% endif %}
    </div>
    {% else %}<p class="muted">Henüz yorum yok.</p>{% endfor %}
  </div>

  <div class="card mt" id="yorumlar">
    <div class="card-h"><h2>Mağaza yorumları</h2><span class="muted small">{{ scomments|length }} yorum</span></div>
    {% if me and me.id != seller.id and can_comment %}
    <form method="post" action="{{ url_for('trust.seller_comment', username=seller.username) }}" class="mb">
      {{ csrf_field() }}
      <div class="field"><label for="body">{{ 'Yorumunu güncelle' if my_comment else 'Bu satıcı hakkında ne düşünüyorsun?' }}</label><textarea id="body" name="body" required minlength="5" maxlength="500" style="min-height:80px" placeholder="Deneyimini kısaca yaz">{{ my_comment.body if my_comment }}</textarea></div>
      <button class="btn btn-sm" type="submit">{{ 'Güncelle' if my_comment else 'Yorum Yaz' }}</button>
    </form>
    {% elif not me %}<p class="muted"><a href="{{ url_for('login', next=request.path) }}">Giriş yap</a>; mağazadan alışveriş yaptıysan yorum bırakabilirsin.</p>
    {% elif me.id != seller.id %}<p class="muted small mb">Mağaza yorumunu yalnızca bu satıcıdan alışveriş yapmış alıcılar yazabilir.</p>{% endif %}
    {% for c in scomments %}
    <div class="review">
      <div class="who"><b>{{ c.author_name|mask }}</b>{{ pkg_marks(c.author_id) }}<span class="muted small">{{ c.created_at|dt(false) }}</span>
        {% if me and me.id == c.author_id %}<form class="inline-form" method="post" action="{{ url_for('trust.seller_comment_delete', cid=c.id) }}" data-confirm="Yorumun silinsin mi?">{{ csrf_field() }}<button class="link-btn" type="submit">Sil</button></form>{% endif %}</div>
      <div class="pre">{{ c.body }}</div>
    </div>
    {% else %}<p class="muted">Henüz mağaza yorumu yok.</p>{% endfor %}
  </div>
</div>
{% endblock %}
"""

TEMPLATES["login.html"] = r"""
{% extends "base.html" %}
{% from "_macros.html" import ic with context %}
{% block title %}Giriş Yap{% endblock %}
{% block content %}
<div class="container">
  <div class="auth-wrap">
    <div class="auth-art">
      <div><a class="brand" href="{{ url_for('index') }}"><img class="brand-mark" src="{{ url_for('static', filename='logo.svg') }}" width="32" height="32" alt="">{{ site_name }}</a></div>
      <div>
        <h2>Tekrar hoş geldin.</h2>
        <ul>
          <li>{{ ic('bolt') }}<span>Kodlar ödeme anında hesabında</span></li>
          <li>{{ ic('shield-check') }}<span>Ödeme, sen onaylayana kadar emanette</span></li>
          <li>{{ ic('heart') }}<span>Favorilerin ve siparişlerin seni bekliyor</span></li>
        </ul>
      </div>
    </div>
    <div class="auth-form">
      <h1>Giriş yap</h1>
      <p class="muted">Hesabına erişmek için bilgilerini gir.</p>
      <form method="post" action="{{ url_for('login') }}">
        {{ csrf_field() }}{{ form_guard('login') }}
        {% if next %}<input type="hidden" name="next" value="{{ next }}">{% endif %}
        <div class="field"><label for="ident">Kullanıcı adı veya e-posta</label><input type="text" id="ident" name="ident" required autofocus autocomplete="username"></div>
        <div class="field"><label for="password">Şifre</label><input type="password" id="password" name="password" required autocomplete="current-password"></div>
        {% if show_captcha %}{{ captcha_block('login') }}{% endif %}
        <label class="check field"><input type="checkbox" name="remember" value="1"> Beni hatırla</label>
        <button class="btn btn-block btn-lg" type="submit">Giriş Yap</button>
      </form>
      <p class="center muted mt">Hesabın yok mu? <a href="{{ url_for('register') }}">Kayıt ol</a></p>
    </div>
  </div>
</div>
{% endblock %}
"""

TEMPLATES["register.html"] = r"""
{% extends "base.html" %}
{% from "_macros.html" import ic with context %}
{% block title %}Kayıt Ol{% endblock %}
{% block content %}
<div class="container">
  <div class="auth-wrap">
    <div class="auth-art">
      <div><a class="brand" href="{{ url_for('index') }}"><img class="brand-mark" src="{{ url_for('static', filename='logo.svg') }}" width="32" height="32" alt="">{{ site_name }}</a></div>
      <div>
        <h2>Dakikalar içinde alışverişe başla.</h2>
        <ul>
          <li>{{ ic('gift') }}<span>Discord, Steam, Roblox ve 35'ten fazla kategori</span></li>
          <li>{{ ic('bell') }}<span>Sipariş ve destek bildirimleri</span></li>
          <li>{{ ic('store') }}<span>İstersen satıcı olup kazanmaya başla</span></li>
        </ul>
      </div>
    </div>
    <div class="auth-form">
      <h1>Hesap oluştur</h1>
      <p class="muted">Ücretsiz üye ol.</p>
      <form method="post" action="{{ url_for('register') }}">
        {{ csrf_field() }}{{ form_guard('register') }}
        <div class="field"><label for="username">Kullanıcı adı</label><input type="text" id="username" name="username" value="{{ form.username }}" required minlength="3" maxlength="20" autocomplete="username"><div class="hint">3-20 karakter; harf, rakam ve alt çizgi.</div></div>
        <div class="field"><label for="email">E-posta</label><input type="email" id="email" name="email" value="{{ form.email }}" required autocomplete="email"></div>
        <div class="form-row">
          <div class="field"><label for="password">Şifre</label><input type="password" id="password" name="password" required minlength="8" autocomplete="new-password"></div>
          <div class="field"><label for="password2">Şifre tekrar</label><input type="password" id="password2" name="password2" required minlength="8" autocomplete="new-password"></div>
        </div>
        <div class="hint" style="margin:-6px 0 14px">En az 8 karakter. Kullanıcı adını ve e-postanın ilk kısmını içeren ya da kolay tahmin edilen şifreler kabul edilmez.</div>
        {{ captcha_block('register') }}
        <label class="check field"><input type="checkbox" name="agree" value="1" required> <span><a href="{{ url_for('faq') }}">Kullanım koşullarını</a> okudum ve kabul ediyorum.</span></label>
        <button class="btn btn-block btn-lg" type="submit">Kayıt Ol</button>
      </form>
      <p class="center muted mt">Zaten üye misin? <a href="{{ url_for('login') }}">Giriş yap</a></p>
    </div>
  </div>
</div>
{% endblock %}
"""

TEMPLATES["faq.html"] = r"""
{% extends "base.html" %}
{% block title %}Nasıl Çalışır{% endblock %}
{% block content %}
<div class="container section doc" style="max-width:860px">
  <h1>Nasıl çalışır ve kullanım koşulları</h1>
  <div class="card mb">
    <h3 class="mt0">Satın alma</h3>
    <p class="muted">Bakiye yükle, ilan seç, satın al. Kodlar ödeme anında sipariş sayfanda görünür. Teslim edilen dijital kodlar kullanıldığı için genel kural olarak iade edilmez; kodun çalışmaması gibi sorunlarda destek talebi aç. Kupon kodun varsa satın alma ekranında uygulayabilirsin.</p>
    <h3>Satıcı olmak</h3>
    <p class="muted">Satıcı başvurusu yap. Onaylanınca ilan verebilir, stok yükleyebilir ve satış raporlarını görebilirsin.</p>
    <h3>Emanet</h3>
    <p class="muted">Ödemen satıcıya hemen geçmez. Kodları kontrol edip siparişi onayladığında tutar satıcıya aktarılır. Onay vermezsen belirlenen süre sonunda otomatik aktarılır; sorun varsa aynı sayfadan bildirim yapabilirsin.</p>
    <h3>Komisyon</h3>
    <p class="muted">Satıcılardan satış başına komisyon alınır (genel oran {{ cfg.commission_percent }}%; kategoriye veya satıcıya özel oran uygulanabilir). Alıcıdan ek ücret alınmaz. Oranı ilan verirken net kazancınla birlikte görürsün.</p>
    <h3>Para çekme</h3>
    <p class="muted">{% if cfg.withdraw_only_earnings == '1' %}Yalnızca satış kazançları çekilebilir; yüklenen bakiye alışveriş içindir.{% endif %} Çekimlerde %{{ cfg.withdraw_fee_percent }} işlem kesintisi uygulanır, minimum tutar {{ cfg.min_withdraw }} TL'dir.</p>
  </div>
  <div class="card mb">
    <h3 class="mt0">Güvenlik kuralları</h3>
    <p class="muted">Ödemeyi ve teslimatı platform dışına taşımayın; platform dışı anlaşmalarda koruma sağlanamaz. Sahte veya daha önce kullanılmış kod satmak hesabın kalıcı olarak kapatılmasına yol açar.</p>
    <p class="muted"><b>Mesajlaşma:</b> Alıcı-satıcı yazışmaları ve destek talepleri, dolandırıcılığı önlemek ve uyuşmazlıkları çözmek amacıyla yönetim ekibi tarafından görüntülenebilir. Şifre, banka kartı bilgisi veya kimlik numarası paylaşmayın.</p>
  </div>
  <div class="card faq">
    <h3 class="mt0">Sıkça sorulan sorular</h3>
    <details><summary>Kodum çalışmadı, ne yapmalıyım?</summary><p>Sipariş sayfasından satıcıya mesaj yaz; çözülmezse Destek bölümünden sipariş numaranla talep aç.</p></details>
    <details><summary>Bakiyem ne zaman yüklenir?</summary><p>Yükleme bildirimin kontrol edildikten sonra bakiyene eklenir. Süre yöntemine göre değişir.</p></details>
    <details><summary>Rozetler ne anlama geliyor?</summary><p><b>Kimliği Doğrulandı:</b> ödeme öncesi kimlik doğrulaması tamamlandı. <b>Onaylı Satıcı:</b> satıcı başvurusu onaylandı. <b>Güvenilir Satıcı:</b> yüksek satış adedi ve yüksek müşteri puanı. <b>Mağaza Üyesi:</b> kurumsal mağaza üyeliği. <b>Yıldız Satıcı:</b> yönetim tarafından seçilen üstün performans.</p></details>
    <details><summary>Kupon nasıl kullanılır?</summary><p>İlan sayfasında satın alma kutusundaki kupon alanına kodu yazıp Uygula'ya bas. İndirim toplam tutardan düşer; kupon kategori, minimum tutar ve kullanım sınırı gibi koşullara bağlı olabilir.</p></details>
    <details><summary>Destek talebim ne zaman yanıtlanır?</summary><p>Talepler sıraya alınır; ödeme ve şikayet konuları önceliklidir. Yanıt geldiğinde bildirim alırsın.</p></details>
  </div>
</div>
{% endblock %}
"""

TEMPLATES["error.html"] = r"""
{% extends "base.html" %}
{% block title %}{{ title }}{% endblock %}
{% block content %}
<div class="container section center" style="max-width:560px">
  <div class="card">
    <div class="err-code">{{ code }}</div>
    <h1 style="font-size:1.6rem">{{ title }}</h1>
    <p class="muted">{{ message }}</p>
    <a class="btn" href="{{ url_for('index') }}">Ana sayfaya dön</a>
  </div>
</div>
{% endblock %}
"""

TEMPLATES["favorites.html"] = r"""
{% extends "base.html" %}
{% from "_macros.html" import listing_card, pager, empty, ic with context %}
{% block title %}Favorilerim{% endblock %}
{% block content %}
<div class="container section">
  <div class="page-h"><h1>{{ ic('heart') }} Favorilerim</h1><span class="muted">{{ page.total }} ilan</span></div>
  {% if page.rows %}<div class="lgrid">{% for l in page.rows %}{{ listing_card(l) }}{% endfor %}</div>{{ pager(page) }}
  {% else %}<div class="card">{{ empty('Henüz favorin yok', 'İlan kartlarındaki kalp simgesine dokunarak ilanları buraya ekleyebilirsin.') }}<div class="center"><a class="btn" href="{{ url_for('listings') }}">İlanlara göz at</a></div></div>{% endif %}
</div>
{% endblock %}
"""

TEMPLATES["notifications.html"] = r"""
{% extends "base.html" %}
{% from "_macros.html" import pager, empty, ic with context %}
{% block title %}Bildirimler{% endblock %}
{% block content %}
<div class="container section" style="max-width:860px">
  <div class="page-h"><h1>{{ ic('bell') }} Bildirimler</h1><div class="row">
    {% if unread %}<form method="post" action="{{ url_for('site.notif_read_all') }}">{{ csrf_field() }}<button class="btn btn-ghost btn-sm" type="submit">Tümünü okundu say ({{ unread }})</button></form>{% endif %}
    <button type="button" class="btn btn-ghost btn-sm" data-notif-enable>Tarayıcı bildirimini aç</button><button type="button" class="btn btn-ghost btn-sm" data-sound-toggle>Ses: Açık</button></div></div>
  <div class="tabs">
    <a class="{{ 'on' if not flt }}" href="{{ url_for('site.notifications') }}">Hepsi</a>
    <a class="{{ 'on' if flt == 'okunmamis' }}" href="{{ url_for('site.notifications', durum='okunmamis') }}">Okunmamış</a>
    {% for k, v in kinds.items() %}<a class="{{ 'on' if flt == k }}" href="{{ url_for('site.notifications', durum=k) }}">{{ v }}</a>{% endfor %}
  </div>
  <div class="card tight">
    {% for n in items %}
    <a class="notif-row {{ 'unread' if not n.is_read }} nk-{{ n.kind }}" href="{{ url_for('site.notif_view', nid=n.id) }}">
      <span class="ti">{{ ic('check-circle' if n.kind == 'ok' else ('alert' if n.kind in ('bad', 'warn') else 'bell')) }}</span>
      <span class="grow-1"><b>{{ n.title }}</b>{% if n.body %}<span class="muted small d-block notif-snip">{{ n.body }}</span>{% endif %}</span>
      <span class="nk-tag nk-{{ n.kind }}">{{ kinds[n.kind] }}</span>
      <span class="dim small nowrap">{{ n.created_at|ago }}</span>
    </a>
    {% else %}{{ empty('Bildirimin yok', 'Sipariş, destek ve hesap hareketleri burada görünür.') }}{% endfor %}
  </div>
  {{ pager(page) }}
</div>
{% endblock %}
"""

TEMPLATES["notification_view.html"] = r"""
{% extends "base.html" %}
{% from "_macros.html" import ic, badge with context %}
{% block title %}{{ n.title }}{% endblock %}
{% block content %}
<div class="container section" style="max-width:760px">
  <div class="crumbs"><a href="{{ url_for('site.notifications') }}">Bildirimler</a> <span>/</span> <span>Ayrıntı</span></div>
  <div class="card notif-detail nk-{{ kind }}">
    <div class="nd-head">
      <span class="nd-ico">{{ ic('check-circle' if kind == 'ok' else ('alert' if kind in ('bad', 'warn') else 'bell')) }}</span>
      <div>
        <span class="nk-tag nk-{{ kind }}">{{ label }}</span>
        <h1>{{ n.title }}</h1>
        <div class="muted small">{{ n.created_at|dt }} &middot; {{ n.created_at|ago }}</div>
      </div>
    </div>
    {% if n.body %}<div class="nd-body pre">{{ n.body }}</div>{% endif %}
    {% if order %}
    <div class="nd-order">
      <div class="spread"><b>Sipariş #{{ order.id }}</b>{{ badge(order.escrow_status) }}</div>
      <dl class="kv">
        <dt>İlan</dt><dd>{{ order.listing_title }}</dd>
        <dt>Adet</dt><dd>{{ order.quantity }}</dd>
        <dt>Toplam</dt><dd><b>{{ order.total|money }}</b></dd>
        <dt>Alıcı / satıcı</dt><dd>{{ order.buyer_name }} / {{ order.seller_name }}</dd>
        <dt>Tarih</dt><dd>{{ order.created_at|dt }}</dd>
      </dl>
    </div>
    {% endif %}
    <div class="row mt">
      {% if n.link %}<a class="btn" href="{{ n.link }}">İlgili sayfaya git {{ ic('arrow-right') }}</a>{% endif %}
      <a class="btn btn-ghost" href="{{ url_for('site.notifications') }}">Tüm bildirimler</a>
      <form method="post" action="{{ url_for('site.notif_delete', nid=n.id) }}" data-confirm="Bu bildirim silinsin mi?">{{ csrf_field() }}<button class="btn btn-line" type="submit">Sil</button></form>
    </div>
  </div>
  <div class="spread mt">
    {% if next_n %}<a class="btn btn-ghost btn-sm" href="{{ url_for('site.notif_view', nid=next_n.id) }}">{{ ic('chevron-left') }}Önceki</a>{% else %}<span></span>{% endif %}
    {% if prev_n %}<a class="btn btn-ghost btn-sm" href="{{ url_for('site.notif_view', nid=prev_n.id) }}">Sonraki{{ ic('chevron-right') }}</a>{% endif %}
  </div>
</div>
{% endblock %}
"""


TEMPLATES["sellers.html"] = r"""
{% extends "base.html" %}
{% from "_macros.html" import ic, avatar, badge_list, empty with context %}
{% block title %}Mağazalar{% endblock %}
{% block content %}
<div class="container section">
  <div class="page-h"><h1>Mağazalar</h1><span class="muted">{{ cards|length }} mağaza</span></div>
  <form class="mb" method="get" action="{{ url_for('site.sellers') }}" style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
    <input type="search" name="q" value="{{ text }}" placeholder="Mağaza ara" maxlength="40" style="flex:1;min-width:200px" aria-label="Mağaza ara">
    <select name="sirala" aria-label="Sırala" style="width:auto;min-width:180px">
      {% for k, v in sorts.items() %}<option value="{{ k }}" {{ 'selected' if k == sort }}>{{ v[0] }}</option>{% endfor %}
    </select>
    <button class="btn" type="submit">Ara</button>
  </form>
  {% if cards %}
  <div class="sellers">
    {% for sc in cards %}{% set s = sc.u %}
    <a class="seller-card{{ ' pk-featured' if s.pk_featured }}{{ ' pk-gold' if s.pk_rank == 1 }}{{ ' pk-diamond' if s.pk_rank == 2 }}" href="{{ url_for('storefront', username=s.username) }}">
      {{ avatar(s.username, s.avatar) }}
      <div>
        <b>{{ s.store_name or s.username }}{{ pkg_marks(s.id) }}</b>{% if s.pk_featured %}<span class="pk-flag">{{ ic('flame') }}Öne çıkan</span>{% endif %}
        <div class="small muted">{% if s.rc %}<span class="pos">{{ '%.1f'|format(s.avg) }}</span> puan ({{ s.rc }}) &middot; {% endif %}{{ s.sold }} satış &middot; {{ s.n_listings }} ilan</div>
        {{ badge_list(sc.badges) }}
      </div>
    </a>
    {% endfor %}
  </div>
  {% else %}{{ empty('Mağaza bulunamadı', 'Farklı bir arama dene.') }}{% endif %}
</div>
{% endblock %}
"""

TEMPLATES["categories.html"] = r"""
{% extends "base.html" %}
{% from "_macros.html" import ic with context %}
{% block title %}Kategoriler{% endblock %}
{% block content %}
<div class="container section">
  <div class="page-h"><h1>Kategoriler</h1><span class="muted">{{ cats|length }} kategori</span></div>
  {% for g in groups %}
  <div class="section-t mt" style="margin-top:26px">{{ g }}</div>
  <div class="cat-ban-grid">
    {% for c in cats if c.grp == g %}
    <a class="cat-ban" style="--c:{{ c.color or '#7c5cff' }}" href="{{ url_for('listings', kategori=c.slug) }}">
      <span class="cat-ban-art"><img src="{{ category_banner_url(c, 'mobile') }}" alt="{{ c.name }}" loading="lazy" width="640" height="400">{% if c.image %}<span class="cat-ban-name">{{ c.name }}</span>{% endif %}</span>
      <span class="cat-ban-foot"><span>İlanlara git</span><em>{{ c.n }} ilan</em></span>
    </a>
    {% endfor %}
  </div>
  {% endfor %}
  {% set other = cats|rejectattr('grp', 'in', groups)|list %}
  {% if other %}
  <div class="section-t mt">Diğer</div>
  <div class="cat-ban-grid">
    {% for c in other %}
    <a class="cat-ban" style="--c:{{ c.color or '#7c5cff' }}" href="{{ url_for('listings', kategori=c.slug) }}">
      <span class="cat-ban-art"><img src="{{ category_banner_url(c, 'mobile') }}" alt="{{ c.name }}" loading="lazy" width="640" height="400">{% if c.image %}<span class="cat-ban-name">{{ c.name }}</span>{% endif %}</span>
      <span class="cat-ban-foot"><span>İlanlara git</span><em>{{ c.n }} ilan</em></span>
    </a>
    {% endfor %}
  </div>
  {% endif %}
</div>
{% endblock %}
"""

TEMPLATES["maintenance.html"] = r"""
<!doctype html>
<html lang="tr" data-upmax="{{ upload_max }}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bakımdayız | {{ site_name }}</title>
<link rel="icon" type="image/svg+xml" href="{{ url_for('static', filename='favicon.svg') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
<main class="maint">
  <div class="maint-card">
    <img class="brand-mark maint-mark" src="{{ url_for('static', filename='logo.svg') }}" width="32" height="32" alt="">
    <h1>Kısa bir bakımdayız</h1>
    <p class="muted">{{ site_name }} şu an güncelleniyor. Kısa süre içinde geri döneceğiz; ödeme ve siparişlerin güvende.</p>
    <p class="small dim">{{ cfg.support_email }}</p>
  </div>
</main>
</body>
</html>
"""
