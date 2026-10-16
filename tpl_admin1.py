"""Admin paneli şablonları - 1. bölüm (Jinja). Emoji kullanılmaz."""

TEMPLATES = {}

TEMPLATES["admin_base.html"] = r"""
{% extends "base.html" %}
{% from "_macros.html" import ic with context %}
{% block body_class %} class="app"{% endblock %}
{% block head_extra %}<meta name="robots" content="noindex, nofollow">{% endblock %}
{% block site_header %}{% endblock %}
{% block site_footer %}{% endblock %}
{% block title %}{% block heading %}Pano{% endblock %}{% endblock %}
{% block content %}
{% set ep = request.endpoint or '' %}
<div class="admin-shell">
  <aside class="a-side" id="aside">
    <a class="brand" href="{{ url_for('admin.dashboard') }}"><img class="brand-mark" src="{{ url_for('static', filename='logo.svg') }}" width="32" height="32" alt="">{{ site_name }} <span class="tag-admin">ADMIN</span></a>
    <div class="sep">Genel</div>
    <a class="{{ 'on' if ep == 'admin.dashboard' }}" href="{{ url_for('admin.dashboard') }}">{{ ic('grid') }}<span>Pano</span></a>
    <a class="{{ 'on' if ep == 'admin.reports' }}" href="{{ url_for('admin.reports') }}">{{ ic('chart') }}<span>Raporlar</span></a>
    <a class="{{ 'on' if ep == 'admin.finance' }}" href="{{ url_for('admin.finance') }}">{{ ic('wallet') }}<span>Finans ve kasa</span></a>
    <a class="{{ 'on' if ep == 'admin.feed' }}" href="{{ url_for('admin.feed') }}">{{ ic('history') }}<span>Canlı akış</span></a>
    <div class="sep">Onay bekleyenler</div>
    <a class="{{ 'on' if ep == 'admin.deposits' }}" href="{{ url_for('admin.deposits') }}">{{ ic('download') }}<span>Bakiye yüklemeleri</span>{% if pending.deposits %}<span class="cnt">{{ pending.deposits }}</span>{% endif %}</a>
    <a class="{{ 'on' if ep == 'admin.admin_paylinks' }}" href="{{ url_for('admin.admin_paylinks') }}">{{ ic('link') }}<span>Ödeme linkleri</span></a>
    <a class="{{ 'on' if ep == 'admin.complaints' }}" href="{{ url_for('admin.complaints') }}">{{ ic('flag') }}<span>Şikayetler</span>{% if pending.reports %}<span class="cnt">{{ pending.reports }}</span>{% endif %}</a>
    <a class="{{ 'on' if ep == 'admin.withdrawals' }}" href="{{ url_for('admin.withdrawals') }}">{{ ic('upload') }}<span>Çekim talepleri</span>{% if pending.withdrawals %}<span class="cnt">{{ pending.withdrawals }}</span>{% endif %}</a>
    <a class="{{ 'on' if ep == 'admin.kyc' }}" href="{{ url_for('admin.kyc') }}">{{ ic('id-card') }}<span>Kimlik onayları</span>{% if pending.kyc %}<span class="cnt">{{ pending.kyc }}</span>{% endif %}</a>
    <a class="{{ 'on' if ep == 'admin.sellers' }}" href="{{ url_for('admin.sellers') }}">{{ ic('store') }}<span>Satıcı başvuruları</span>{% if pending.sellers %}<span class="cnt">{{ pending.sellers }}</span>{% endif %}</a>
    <a class="{{ 'on' if ep in ['admin.tickets', 'admin.ticket'] }}" href="{{ url_for('admin.tickets') }}">{{ ic('life-buoy') }}<span>Destek talepleri</span>{% if pending.tickets %}<span class="cnt">{{ pending.tickets }}</span>{% endif %}</a>
    <div class="sep">Yönetim</div>
    <a class="{{ 'on' if ep in ['admin.users', 'admin.user', 'admin.user_new'] }}" href="{{ url_for('admin.users') }}">{{ ic('users') }}<span>Kullanıcılar</span></a>
    <a class="{{ 'on' if ep == 'admin.stores' }}" href="{{ url_for('admin.stores') }}">{{ ic('store') }}<span>Mağazalar</span></a>
    <a class="{{ 'on' if ep in ['admin.listings', 'admin.listing_new', 'admin.listing_edit'] }}" href="{{ url_for('admin.listings') }}">{{ ic('tag') }}<span>İlanlar</span></a>
    <a class="{{ 'on' if ep == 'admin.orders' }}" href="{{ url_for('admin.orders') }}">{{ ic('receipt') }}<span>Siparişler</span></a>
    <a class="{{ 'on' if ep == 'admin.reviews' }}" href="{{ url_for('admin.reviews') }}">{{ ic('star') }}<span>Yorumlar</span></a>
    <a class="{{ 'on' if ep == 'admin.seller_comments' }}" href="{{ url_for('admin.seller_comments') }}">{{ ic('message') }}<span>Mağaza yorumları</span></a>
    <a class="{{ 'on' if ep in ['admin.chats', 'admin.chat'] }}" href="{{ url_for('admin.chats') }}">{{ ic('message') }}<span>Sohbet denetimi</span></a>
    <a class="{{ 'on' if ep == 'admin.transactions' }}" href="{{ url_for('admin.transactions') }}">{{ ic('database') }}<span>İşlem defteri</span></a>
    <div class="sep">Vitrin ve pazarlama</div>
    <a class="{{ 'on' if ep in ['admin.banners', 'admin.banner_edit'] }}" href="{{ url_for('admin.banners') }}">{{ ic('image') }}<span>Bannerlar</span></a>
    <a class="{{ 'on' if ep == 'admin.doping' }}" href="{{ url_for('admin.doping') }}">{{ ic('flame') }}<span>Doping</span></a>
    <a class="{{ 'on' if ep == 'admin.giveaways_admin' }}" href="{{ url_for('admin.giveaways_admin') }}">{{ ic('gift') }}<span>Çekilişler</span></a>
    <a class="{{ 'on' if ep == 'admin.coupons' }}" href="{{ url_for('admin.coupons') }}">{{ ic('ticket') }}<span>Kuponlar</span></a>
    <a class="{{ 'on' if ep == 'admin.packages' }}" href="{{ url_for('admin.packages') }}">{{ ic('award') }}<span>Paketler</span></a>
    <a class="{{ 'on' if ep == 'admin.categories' }}" href="{{ url_for('admin.categories') }}">{{ ic('layers') }}<span>Kategoriler</span></a>
    <a class="{{ 'on' if ep == 'admin.broadcast' }}" href="{{ url_for('admin.broadcast') }}">{{ ic('megaphone') }}<span>Duyuru gönder</span></a>
    <div class="sep">Sistem</div>
    <a class="{{ 'on' if ep == 'admin.commission' }}" href="{{ url_for('admin.commission') }}">{{ ic('percent') }}<span>Komisyon raporu</span></a>
    <a class="{{ 'on' if ep == 'admin.payments' }}" href="{{ url_for('admin.payments') }}">{{ ic('credit-card') }}<span>Ödeme yöntemleri</span></a>
    <a class="{{ 'on' if ep == 'admin.integration' }}" href="{{ url_for('admin.integration') }}">{{ ic('code') }}<span>Entegrasyon ve API</span></a>
    <a class="{{ 'on' if ep == 'admin.site_settings' }}" href="{{ url_for('admin.site_settings') }}">{{ ic('settings') }}<span>Site ayarları</span></a>
    <a class="{{ 'on' if ep == 'admin.system' }}" href="{{ url_for('admin.system') }}">{{ ic('server') }}<span>Sistem ve araçlar</span></a>
    <a class="{{ 'on' if ep in ['admin.security_page', 'admin.setup'] }}" href="{{ url_for('admin.security_page') }}">{{ ic('shield-check') }}<span>Güvenlik</span></a>
    <a class="{{ 'on' if ep == 'admin.log' }}" href="{{ url_for('admin.log') }}">{{ ic('history') }}<span>Yönetici günlüğü</span></a>
  </aside>
  <div class="a-main">
    <div class="a-top">
      <div class="row">
        <button type="button" class="ibtn a-toggle" data-toggle-nav="#aside" aria-label="Menü">{{ ic('menu') }}</button>
        <h1>{{ self.heading() }}</h1>
      </div>
      <div class="gsearch"><form action="{{ url_for('admin.search') }}" method="get" role="search">{{ ic('search') }}<input type="search" name="q" placeholder="Kullanıcı, ilan, sipariş, talep ara" maxlength="60" aria-label="Yönetim araması"></form></div>
      <div class="row">
        <a class="btn btn-ghost btn-sm" href="{{ url_for('index') }}" target="_blank" rel="noopener">{{ ic('external') }}Siteyi gör</a>
        <form class="inline-form" method="post" action="{{ url_for('admin.logout') }}">{{ csrf_field() }}<button class="btn btn-line btn-sm" type="submit">{{ ic('logout') }}Çıkış</button></form>
      </div>
    </div>
    {% if admsec %}
      {% if admsec.alert %}<div class="notice bad"><b>Yeni cihazdan yönetici girişi:</b> {{ admsec.alert.at|dt }} &middot; {{ admsec.alert.why }} &middot; {{ admsec.alert.ip }} &middot; {{ admsec.alert.browser }}. Bu sen değilsen şifreni hemen değiştir ve giriş geçmişini incele.
        <div class="row" style="margin-top:8px"><a class="btn btn-line btn-sm" href="{{ url_for('admin.security_page') }}">Giriş geçmişi</a><form class="inline-form" method="post" action="{{ url_for('admin.security_dismiss') }}">{{ csrf_field() }}<button class="btn btn-ghost btn-sm" type="submit">Bendim, uyarıyı kapat</button></form></div></div>{% endif %}
      {% if admsec.tfa_warn %}<div class="notice warn">İki adımlı doğrulama kapalı. Yönetici hesabını korumak için <a href="{{ url_for('admin.security_page') }}">Güvenlik</a> sayfasından etkinleştir.</div>{% endif %}
    {% endif %}
    {% block panel %}{% endblock %}
  </div>
</div>
{% endblock %}
"""

TEMPLATES["admin_authbase.html"] = r"""
<!doctype html>
<html lang="tr" data-upmax="{{ upload_max }}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{% block title %}{% block heading %}Yönetici{% endblock %}{% endblock %} | {{ site_name }}</title>
<link rel="icon" type="image/svg+xml" href="{{ url_for('static', filename='favicon.svg') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
<script src="{{ url_for('static', filename='boot.js') }}"></script>
<script src="{{ url_for('static', filename='app.js') }}" defer></script>
</head>
<body class="app">
{% include "_sprite.html" %}
<div class="a-login{% block wrap_class %}{% endblock %}">
  <div class="center mb"><a class="brand" href="{{ url_for('index') }}" style="justify-content:center"><img class="brand-mark" src="{{ url_for('static', filename='logo.svg') }}" width="32" height="32" alt="">{{ site_name }}</a></div>
  {% with msgs = get_flashed_messages(with_categories=true) %}
  {% if msgs %}<div class="container flashes">{% for c, m in msgs %}<div class="flash flash-{{ c }}"><span>{{ m }}</span><button type="button" class="x" aria-label="Kapat">&times;</button></div>{% endfor %}</div>{% endif %}
  {% endwith %}
  <div class="card">
    <div class="spread mb"><h1 style="font-size:1.25rem;margin:0">{{ self.heading() }}</h1><span class="tag-admin">ADMIN</span></div>
    {% block panel %}{% endblock %}
  </div>
</div>
</body>
</html>
"""

TEMPLATES["admin_login.html"] = r"""
{% extends "admin_authbase.html" %}
{% block heading %}Yönetici girişi{% endblock %}
{% block panel %}
<form method="post" action="{{ url_for('admin.login') }}" autocomplete="off">
  {{ csrf_field() }}
  <input type="hidden" name="ft" value="{{ ft }}">
  {% if nxt %}<input type="hidden" name="next" value="{{ nxt }}">{% endif %}
  <div class="hp-field" aria-hidden="true"><label for="website">Web sitesi</label><input type="text" id="website" name="website" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px;width:1px;height:1px"></div>
  <div class="field"><label for="username">Kullanıcı adı</label><input type="text" id="username" name="username" required autofocus autocomplete="username"></div>
  <div class="field"><label for="password">Şifre</label><input type="password" id="password" name="password" required autocomplete="current-password"></div>
  {% if captcha %}{{ captcha_block('admin') }}{% endif %}
  <button class="btn btn-block" type="submit">Giriş yap</button>
</form>
{% endblock %}
"""

TEMPLATES["admin_dashboard.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import bars, badge, empty, ic, spark with context %}
{% macro delta(cur, prev) %}{% if prev %}{% set p = ((cur - prev) * 100 / prev)|round|int %}<span class="delta {{ 'up' if p > 0 else ('down' if p < 0 else 'flat') }}">{{ '+' if p > 0 }}{{ p }}%</span>{% elif cur %}<span class="delta up">yeni</span>{% endif %}{% endmacro %}
{% block heading %}Pano{% endblock %}
{% block panel %}
{% if demo_loaded %}<div class="notice warn">Demo veri yüklü. Vitrin dolu görünür ama ilanlar satın alınamaz. Canlıya çıkmadan önce <a href="{{ url_for('admin.system') }}">Sistem ve araçlar</a> sayfasından sil.</div>{% endif %}

<div class="todo mb">
  <a class="todo-i {{ 'hot' if pending.deposits }}" href="{{ url_for('admin.deposits') }}">{{ ic('download') }}<b>{{ pending.deposits }}</b><span>Bekleyen yükleme</span></a>
  <a class="todo-i {{ 'hot' if pending.withdrawals }}" href="{{ url_for('admin.withdrawals') }}">{{ ic('upload') }}<b>{{ pending.withdrawals }}</b><span>Bekleyen çekim</span></a>
  <a class="todo-i {{ 'hot' if pending.kyc }}" href="{{ url_for('admin.kyc') }}">{{ ic('id-card') }}<b>{{ pending.kyc }}</b><span>Kimlik onayı</span></a>
  <a class="todo-i {{ 'hot' if pending.sellers }}" href="{{ url_for('admin.sellers') }}">{{ ic('store') }}<b>{{ pending.sellers }}</b><span>Satıcı başvurusu</span></a>
  <a class="todo-i {{ 'hot' if pending.tickets }}" href="{{ url_for('admin.tickets') }}">{{ ic('life-buoy') }}<b>{{ pending.tickets }}</b><span>Açık destek</span></a>
  <a class="todo-i {{ 'warn' if out_of_stock }}" href="{{ url_for('admin.listings', durum='active') }}">{{ ic('package') }}<b>{{ out_of_stock }}</b><span>Stoğu biten ilan</span></a>
</div>

<div class="kpis mb">
  <div class="kpi"><div class="k">{{ ic('chart') }}Toplam ciro (GMV)</div><div class="v">{{ stats.gmv|money }}</div><div class="s">{{ stats.orders }} sipariş &middot; 7 gün {{ delta(week.gmv, week.prev_gmv) }}</div>{{ spark(chart_gmv|map(attribute='value')|list) }}</div>
  <div class="kpi"><div class="k">{{ ic('percent') }}Komisyon geliri</div><div class="v ok">{{ stats.commission|money }}</div><div class="s">+ {{ stats.wd_fees|money }} çekim kesintisi &middot; + {{ stats.doping|money }} doping</div></div>
  <div class="kpi"><div class="k">{{ ic('wallet') }}Kullanıcı bakiyeleri</div><div class="v warn">{{ stats.liabilities|money }}</div><div class="s">Platformun yükümlülüğü</div></div>
  <div class="kpi"><div class="k">{{ ic('download') }}Onaylı yüklemeler</div><div class="v">{{ stats.deposited|money }}</div><div class="s">Ödenen çekim {{ stats.paid_out|money }}</div>{{ spark(chart_dep|map(attribute='value')|list) }}</div>
</div>
<div class="kpis mb">
  <div class="kpi"><div class="k">{{ ic('users') }}Kullanıcı</div><div class="v">{{ stats.users }}</div><div class="s">Bugün +{{ stats.new_today }} &middot; 7 gün {{ delta(week.users, week.prev_users) }} &middot; {{ stats.banned }} engelli</div></div>
  <div class="kpi"><div class="k">{{ ic('store') }}Satıcı</div><div class="v">{{ stats.sellers }}</div></div>
  <div class="kpi"><div class="k">{{ ic('tag') }}Aktif ilan</div><div class="v">{{ stats.listings }}</div><div class="s">{{ stats.stock_codes }} kod stokta</div></div>
  <div class="kpi"><div class="k">{{ ic('life-buoy') }}Destek / yorum</div><div class="v">{{ stats.open_tickets }} / {{ stats.reviews }}</div><div class="s">açık talep / yayındaki yorum</div></div>
  <div class="kpi"><div class="k">{{ ic('ticket') }}Kupon / banner</div><div class="v">{{ week.coupons }} / {{ week.banners }}</div><div class="s">İndirim maliyeti {{ week.discounts|money }}</div></div>
</div>

<div class="two-col mb">
  <div class="card"><div class="card-h"><h3>Ciro, son 14 gün</h3><a class="small" href="{{ url_for('admin.reports') }}">Raporlar</a></div>{{ bars(chart_gmv, true) }}</div>
  <div class="card"><div class="card-h"><h3>Yeni üye, son 14 gün</h3></div>{{ bars(chart_users) }}</div>
</div>

<div class="two-col mb">
  <div class="card">
    <div class="card-h"><h3>Kategori performansı</h3><span class="small muted">Son 30 gün</span></div>
    {% if top_cats %}{% set peak = top_cats[0].gmv or 1 %}
      {% for c in top_cats %}<div class="hbar"><span>{{ c.name }}</span><div class="meter"><i style="width:{{ (c.gmv * 100 / peak)|round|int }}%;background:{{ c.color or '#7c5cff' }}"></i></div><b>{{ c.gmv|money }}</b></div>{% endfor %}
    {% else %}{{ empty('Henüz satış yok') }}{% endif %}
  </div>
  <div class="card">
    <div class="card-h"><h3>Açık destek talepleri</h3><a class="small" href="{{ url_for('admin.tickets') }}">Tümü</a></div>
    {% if recent_tickets %}<div class="table-wrap"><table>
      <tr><th>No</th><th>Konu</th><th>Kullanıcı</th><th>Öncelik</th></tr>
      {% for t in recent_tickets %}<tr><td><a href="{{ url_for('admin.ticket', tid=t.id) }}">#{{ t.id }}</a></td><td>{{ t.subject[:34] }}{% if t.last_reply_by == 'user' %} <span class="badge b-warn">Yanıt bekliyor</span>{% endif %}</td><td>{{ t.username }}</td><td><span class="badge b-{{ t.priority|pclass }}">{{ t.priority|plabel }}</span></td></tr>{% endfor %}
    </table></div>{% else %}{{ empty('Açık talep yok') }}{% endif %}
  </div>
</div>

<div class="two-col mb">
  <div class="card">
    <div class="card-h"><h3>Son siparişler</h3><a class="small" href="{{ url_for('admin.orders') }}">Tümü</a></div>
    {% if recent_orders %}<div class="table-wrap"><table>
      <tr><th>No</th><th>İlan</th><th>Alıcı</th><th class="right">Tutar</th></tr>
      {% for o in recent_orders %}<tr><td>#{{ o.id }}</td><td>{{ o.listing_title[:30] }}<div class="muted small">{{ o.seller_name }}{{ pkg_marks(o.seller_id) }}</div></td><td>{{ o.buyer_name }}</td><td class="right nowrap">{{ o.total|money }}</td></tr>{% endfor %}
    </table></div>{% else %}{{ empty('Henüz sipariş yok') }}{% endif %}
  </div>
  <div class="card">
    <div class="card-h"><h3>Yeni üyeler</h3><div class="row"><a class="small" href="{{ url_for('admin.user_new') }}">Üye oluştur</a><a class="small" href="{{ url_for('admin.users') }}">Tümü</a></div></div>
    <div class="table-wrap"><table>
      <tr><th>Kullanıcı</th><th>Kimlik</th><th>Kayıt</th></tr>
      {% for u in recent_users %}<tr><td><a href="{{ url_for('admin.user', uid=u.id) }}">{{ u.username }}</a>{{ pkg_marks(u.id) }}<div class="muted small trunc">{{ u.email }}</div></td><td>{{ badge(u.kyc_status) }}</td><td class="nowrap">{{ u.created_at|ago }}</td></tr>{% endfor %}
    </table></div>
  </div>
</div>

<div class="card">
  <div class="card-h"><h3>Son yönetici işlemleri</h3><a class="small" href="{{ url_for('admin.log') }}">Günlük</a></div>
  {% if recent_log %}<div class="table-wrap"><table>
    {% for l in recent_log %}<tr><td><b>{{ l.action }}</b><div class="muted small">{{ l.detail[:90] }}</div></td><td class="nowrap muted small right">{{ l.created_at|dt }}</td></tr>{% endfor %}
  </table></div>{% else %}{{ empty('Kayıt yok') }}{% endif %}
</div>
{% endblock %}
"""

TEMPLATES["admin_users.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import badge, pager, empty %}
{% block title %}Kullanıcılar{% endblock %}
{% block heading %}Kullanıcılar{% endblock %}
{% block panel %}
<div class="spread mb">
  <form class="filters" style="margin:0;flex:1" method="get" action="{{ url_for('admin.users') }}">
    <div class="field grow"><label for="q">Ara</label><input type="search" id="q" name="q" value="{{ text }}" placeholder="Kullanıcı adı, e-posta veya ID"></div>
    <div class="field"><label for="filtre">Filtre</label><select id="filtre" name="filtre"><option value="">Hepsi</option>
      {% for k, v in [('seller', 'Satıcılar'), ('banned', 'Engelliler'), ('pending', 'Kimlik: beklemede'), ('approved', 'Kimlik: onaylı'), ('rejected', 'Kimlik: reddedilmiş'), ('none', 'Kimlik: yok')] %}<option value="{{ k }}" {{ 'selected' if flt == k }}>{{ v }}</option>{% endfor %}</select></div>
    <div class="field"><button class="btn" type="submit">Filtrele</button></div>
  </form>
  <a class="btn" href="{{ url_for('admin.user_new') }}">Üye Oluştur</a>
</div>
{% if page.rows %}
<div class="table-wrap"><table>
  <tr><th>ID</th><th>Kullanıcı</th><th>Roller</th><th>Kimlik</th><th class="right">Bakiye</th><th class="right">Alış / Satış</th><th>Kayıt</th><th></th></tr>
  {% for u in page.rows %}<tr>
    <td>#{{ u.id }}</td>
    <td><a href="{{ url_for('admin.user', uid=u.id) }}"><b>{{ u.username }}</b></a>{{ pkg_marks(u.id) }}<div class="muted small">{{ u.email }}</div></td>
    <td>{% if u.is_seller %}<span class="badge b-ok">Satıcı</span>{% endif %} {% if u.is_banned %}<span class="badge b-bad">Engelli</span>{% endif %}</td>
    <td>{{ badge(u.kyc_status) }}</td>
    <td class="right nowrap">{{ u.balance|money }}</td>
    <td class="right">{{ u.buys }} / {{ u.sold }}</td>
    <td class="nowrap">{{ u.created_at|dt(false) }}</td>
    <td class="actions"><a class="btn btn-ghost btn-sm" href="{{ url_for('admin.user', uid=u.id) }}#bakiye">Bakiye ekle</a> <a class="btn btn-ghost btn-sm" href="{{ url_for('admin.user', uid=u.id) }}">Yönet</a></td>
  </tr>{% endfor %}
</table></div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Kullanıcı bulunamadı') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["admin_user_new.html"] = r"""
{% extends "admin_base.html" %}
{% block title %}Üye Oluştur{% endblock %}
{% block heading %}Üye oluştur{% endblock %}
{% block panel %}
<div class="card" style="max-width:760px">
  <p class="muted mt0">Yönetici olarak yeni bir hesap açarsın. Şifreyi boş bırakırsan güçlü bir geçici şifre üretilir ve yalnızca bir kez gösterilir.</p>
  <form method="post" action="{{ url_for('admin.user_new') }}">
    {{ csrf_field() }}
    <div class="form-row">
      <div class="field"><label for="username">Kullanıcı adı</label><input type="text" id="username" name="username" value="{{ form.username }}" required minlength="3" maxlength="20"></div>
      <div class="field"><label for="email">E-posta</label><input type="email" id="email" name="email" value="{{ form.email }}" required></div>
    </div>
    <div class="form-row">
      <div class="field"><label for="password">Şifre (boşsa otomatik)</label><input type="text" id="password" name="password" autocomplete="off" minlength="8" maxlength="128"></div>
      <div class="field"><label for="balance">Açılış bakiyesi (TL, isteğe bağlı)</label><input type="text" inputmode="decimal" id="balance" name="balance" value="{{ form.balance }}" placeholder="0"></div>
    </div>
    <label class="check field"><input type="checkbox" name="kyc_ok" value="1" {{ 'checked' if form.kyc_ok }}> <span>Kimlik doğrulaması onaylı say <span class="muted">(yalnızca belgeyi kendin doğruladıysan)</span></span></label>
    <label class="check field"><input type="checkbox" name="is_seller" value="1" {{ 'checked' if form.is_seller }}> <span>Satıcı olarak oluştur</span></label>
    <div class="field"><label for="store_name">Mağaza adı (satıcıysa)</label><input type="text" id="store_name" name="store_name" value="{{ form.store_name }}" maxlength="40"></div>
    <button class="btn" type="submit">Üyeyi Oluştur</button> <a class="btn btn-ghost" href="{{ url_for('admin.users') }}">Vazgeç</a>
  </form>
</div>
{% endblock %}
"""

TEMPLATES["admin_user.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import badge, avatar, badge_list, rating_line, empty, ic with context %}
{% block title %}{{ u.username }}{% endblock %}
{% block heading %}Kullanıcı: {{ u.username }}{% endblock %}
{% block panel %}
<div class="card mb">
  <div class="store-head">
    {{ avatar(u.username, u.avatar, 'lg') }}
    <div style="flex:1;min-width:260px">
      <h2 style="margin-bottom:.2em">{{ u.store_name or u.username }}{{ pkg_marks(u.id) }} <span class="muted small">#{{ u.id }}</span></h2>
      <div class="muted small mb">{{ u.email }}{% if u.phone %} &middot; {{ u.phone }}{% endif %} &middot; Kayıt: {{ u.created_at|dt }} &middot; Son giriş: {{ u.last_login|dt if u.last_login else '-' }}</div>
      <div class="row mb">{% if u.is_seller %}<span class="badge b-ok">Satıcı</span>{% endif %}{% if u.is_banned %}<span class="badge b-bad">Engelli</span>{% endif %}<span class="badge b-{{ u.kyc_status|sclass }}">Kimlik: {{ u.kyc_status|slabel }}</span>{% if u.is_seller %}{{ rating_line(seller_stats.rating, seller_stats.reviews) }}{% endif %}</div>
      {{ badge_list(badges) }}
      <a class="btn btn-sm" href="#bakiye">Bakiye ekle</a>
    </div>
    <div class="right"><div class="muted small">Bakiye</div><div style="font-size:1.8rem;font-weight:800">{{ u.balance|money }}</div><div class="muted small">Çekilebilir: {{ withdrawable|money }}</div></div>
  </div>
</div>

<div class="grid g4 mb">
  <div class="stat"><div class="k">Alışlar</div><div class="v">{{ stats.buys }}</div><div class="s">{{ stats.spent|money }}</div></div>
  <div class="stat"><div class="k">Satışlar</div><div class="v">{{ stats.sold }}</div><div class="s">Net {{ stats.earned|money }} &middot; komisyon {{ stats.fees|money }}</div></div>
  <div class="stat"><div class="k">Yükleme / Çekim</div><div class="v" style="font-size:1.2rem">{{ stats.deposited|money }}</div><div class="s">Çekilen: {{ stats.withdrawn|money }}</div></div>
  <div class="stat"><div class="k">İlan / Talep / API</div><div class="v">{{ stats.listings }} / {{ stats.tickets }} / {{ stats.api_keys }}</div></div>
</div>

<div class="two-col mb">
  <div class="card">
    <h3 class="mt0">Hesap işlemleri</h3>
    <div class="row mb">
      {% if u.is_banned %}
      <form method="post" action="{{ url_for('admin.user_action', uid=u.id) }}">{{ csrf_field() }}<input type="hidden" name="action" value="unban"><button class="btn btn-ok btn-sm" type="submit">Engeli kaldır</button></form>
      {% else %}
      <form method="post" action="{{ url_for('admin.user_action', uid=u.id) }}" class="mini-form" data-confirm="Kullanıcı engellensin mi? İlanları yayından kalkar.">{{ csrf_field() }}<input type="hidden" name="action" value="ban"><input type="text" name="reason" placeholder="Gerekçe" maxlength="200"><button class="btn btn-danger btn-sm" type="submit">Engelle</button></form>
      {% endif %}
      {% if u.is_seller %}
      <form method="post" action="{{ url_for('admin.user_action', uid=u.id) }}" data-confirm="Satıcı yetkisi alınsın mı? Aktif ilanlar duraklatılır.">{{ csrf_field() }}<input type="hidden" name="action" value="seller_off"><button class="btn btn-line btn-sm" type="submit">Satıcı yetkisini al</button></form>
      {% else %}
      <form method="post" action="{{ url_for('admin.user_action', uid=u.id) }}">{{ csrf_field() }}<input type="hidden" name="action" value="seller_on"><button class="btn btn-ghost btn-sm" type="submit">Satıcı yap</button></form>
      {% endif %}
      <form method="post" action="{{ url_for('admin.user_action', uid=u.id) }}" data-confirm="Yeni geçici şifre üretilsin mi? Mevcut şifre geçersiz olur.">{{ csrf_field() }}<input type="hidden" name="action" value="reset_pw"><button class="btn btn-line btn-sm" type="submit">Şifre sıfırla</button></form>
      <form method="post" action="{{ url_for('admin.user_action', uid=u.id) }}" data-confirm="Kimlik durumu sıfırlansın mı?">{{ csrf_field() }}<input type="hidden" name="action" value="kyc_reset"><button class="btn btn-line btn-sm" type="submit">Kimliği sıfırla</button></form>
      {% if u.avatar %}<form method="post" action="{{ url_for('admin.user_action', uid=u.id) }}" data-confirm="Profil fotoğrafı kaldırılsın mı?">{{ csrf_field() }}<input type="hidden" name="action" value="avatar_remove"><button class="btn btn-line btn-sm" type="submit">Fotoğrafı kaldır</button></form>{% endif %}
    </div>
    <hr>
    <h3 id="bakiye">Bakiye ekle / düzenle</h3>
    <form method="post" action="{{ url_for('admin.user_action', uid=u.id) }}" data-confirm="Bakiye işlemi uygulansın mı?">
      {{ csrf_field() }}<input type="hidden" name="action" value="balance">
      <div class="form-row">
        <div class="field"><label>İşlem</label><select name="type"><option value="add">Bakiye ekle (çekilemez)</option><option value="bonus">Kazanç ekle (çekilebilir)</option><option value="sub">Bakiye düş</option></select></div>
        <div class="field"><label>Tutar (TL)</label><input type="text" inputmode="decimal" name="amount" required></div>
      </div>
      <div class="field"><label>Gerekçe</label><input type="text" name="reason" required maxlength="200"></div>
      <button class="btn btn-sm" type="submit">Uygula</button>
    </form>
  </div>
  <div class="card">
    <h3 class="mt0">Komisyon ve rozetler</h3>
    <form method="post" action="{{ url_for('admin.user_action', uid=u.id) }}" class="mb">
      {{ csrf_field() }}<input type="hidden" name="action" value="commission">
      <div class="field"><label>Satıcıya özel komisyon oranı (%)</label>
        <div class="row" style="flex-wrap:nowrap"><input type="text" inputmode="decimal" name="rate" value="{{ u.commission_rate if u.commission_rate is not none else '' }}" placeholder="Boş: kategori/genel oran (genel %{{ eff_rate }})"><button class="btn btn-sm" type="submit">Kaydet</button></div>
        <div class="hint">Doluysa bu satıcı için kategori ve genel orandan önce uygulanır (0-50).</div></div>
    </form>
    <hr>
    <h3>Elle verilen rozetler</h3>
    <div class="grid" style="gap:8px">
      {% for key in manual_badges %}
      <div class="spread"><span class="bd {{ BADGES[key][1] }}" title="{{ BADGES[key][2] }}">{{ BADGES[key][0] }}</span>
        <form method="post" action="{{ url_for('admin.user_action', uid=u.id) }}">{{ csrf_field() }}<input type="hidden" name="badge" value="{{ key }}">
          {% if key in manual %}<input type="hidden" name="action" value="badge_remove"><button class="btn btn-line btn-sm" type="submit">Kaldır</button>
          {% else %}<input type="hidden" name="action" value="badge_add"><button class="btn btn-ghost btn-sm" type="submit">Ver</button>{% endif %}</form></div>
      {% endfor %}
    </div>
    <p class="muted small mt">"Kimliği Doğrulandı" ve "Onaylı Satıcı" otomatik verilir; "Güvenilir Satıcı" performansa göre otomatik ya da elle verilebilir.</p>
  </div>
</div>

<div class="two-col mb">
  <div class="card">
    <h3 class="mt0">Kimlik başvurusu</h3>
    {% if kyc %}<dl class="kv">
      <dt>Durum</dt><dd>{{ badge(kyc.status) }}</dd><dt>Ad soyad</dt><dd>{{ kyc.full_name }}</dd><dt>T.C. no</dt><dd class="mono">{{ kyc.id_number }}</dd><dt>Doğum tarihi</dt><dd>{{ kyc.birth_date }}</dd><dt>Tarih</dt><dd>{{ kyc.created_at|dt }}</dd>{% if kyc.admin_note %}<dt>Not</dt><dd>{{ kyc.admin_note }}</dd>{% endif %}
    </dl><a class="btn btn-ghost btn-sm mt" href="{{ url_for('admin.kyc', durum='all') }}">Kimlik listesi</a>{% else %}<p class="muted">Başvuru yok.</p>{% endif %}
  </div>
  <div class="card">
    <h3 class="mt0">Satıcı başvurusu</h3>
    {% if application %}<dl class="kv"><dt>Durum</dt><dd>{{ badge(application.status) }}</dd><dt>Mağaza adı</dt><dd>{{ application.store_name }}</dd><dt>Tarih</dt><dd>{{ application.created_at|dt }}</dd></dl>{% else %}<p class="muted">Başvuru yok.</p>{% endif %}
  </div>
</div>

<div class="two-col mb">
  <div class="card">
    <h3 class="mt0">Yönetici notu</h3>
    <form method="post" action="{{ url_for('admin.user_action', uid=u.id) }}">
      {{ csrf_field() }}<input type="hidden" name="action" value="note">
      <div class="field"><textarea name="admin_note" maxlength="1000" placeholder="Yalnızca yöneticiler görür" style="min-height:90px">{{ u.admin_note }}</textarea></div>
      <button class="btn btn-sm" type="submit">Notu kaydet</button>
    </form>
    <hr>
    <h3>Bildirim gönder</h3>
    <form method="post" action="{{ url_for('admin.user_action', uid=u.id) }}">
      {{ csrf_field() }}<input type="hidden" name="action" value="notify">
      <div class="field"><input type="text" name="title" maxlength="100" placeholder="Başlık" required></div>
      <div class="field"><input type="text" name="body" maxlength="280" placeholder="Metin (isteğe bağlı)"></div>
      <button class="btn btn-ghost btn-sm" type="submit">Gönder</button>
    </form>
  </div>
  <div class="card">
    <h3 class="mt0">Güvenlik ve IP kayıtları</h3>
    <dl class="kv"><dt>Kayıt IP</dt><dd class="mono small">{{ u.reg_ip or '-' }}</dd><dt>Son IP</dt><dd class="mono small">{{ u.last_ip or '-' }}</dd></dl>
    {% if same_ip %}<div class="notice warn mt">Aynı IP'yi kullanan diğer hesaplar:
      {% for o in same_ip %}<a href="{{ url_for('admin.user', uid=o.id) }}">{{ o.username }}</a>{% if o.is_banned %} (engelli){% endif %}{{ ', ' if not loop.last }}{% endfor %}</div>{% endif %}
    {% if events %}<div class="table-wrap mt"><table>
      <tr><th>Giriş</th><th>IP</th><th>Tarayıcı</th></tr>
      {% for e in events %}<tr><td class="nowrap small">{{ e.created_at|ago }}</td><td class="mono small">{{ e.ip }}</td><td class="small muted">{{ e.agent[:38] }}</td></tr>{% endfor %}
    </table></div>{% else %}<p class="muted small mt">Giriş kaydı yok.</p>{% endif %}
  </div>
</div>

<div class="card mb">
  <div class="card-h"><h3>Son hareketler</h3></div>
  {% if txs %}<div class="table-wrap"><table>
    <tr><th>Tarih</th><th>Tür</th><th>Açıklama</th><th class="right">Tutar</th><th class="right">Bakiye</th></tr>
    {% for t in txs %}<tr><td class="nowrap">{{ t.created_at|dt }}</td><td>{{ t.kind|kindlabel }}</td><td class="muted">{{ t.description }}</td><td class="right nowrap {{ 'pos' if t.amount > 0 else 'neg' }}">{{ t.amount|smoney }}</td><td class="right nowrap">{{ t.balance_after|money }}</td></tr>{% endfor %}
  </table></div>{% else %}{{ empty('Hareket yok') }}{% endif %}
</div>

<div class="two-col">
  <div class="card">
    <div class="card-h"><h3>Son siparişler</h3></div>
    {% if orders %}<div class="table-wrap"><table>
      <tr><th>No</th><th>İlan</th><th>Rol</th><th class="right">Tutar</th></tr>
      {% for o in orders %}<tr><td>#{{ o.id }}</td><td>{{ o.listing_title[:34] }}</td><td>{{ 'Alıcı' if o.buyer_id == u.id else 'Satıcı' }}</td><td class="right nowrap">{{ o.total|money }}</td></tr>{% endfor %}
    </table></div>{% else %}{{ empty('Sipariş yok') }}{% endif %}
  </div>
  <div class="card">
    <div class="card-h"><h3>İlanları</h3></div>
    {% if lst %}<div class="table-wrap"><table>
      <tr><th>İlan</th><th class="right">Stok</th><th>Durum</th><th></th></tr>
      {% for l in lst %}<tr><td>{{ l.title[:34] }}</td><td class="right">{{ l.stock }}</td><td>{{ badge(l.status) }}</td><td class="actions"><a class="btn btn-ghost btn-sm" href="{{ url_for('admin.listing_edit', lid=l.id) }}">Düzenle</a></td></tr>{% endfor %}
    </table></div>{% else %}{{ empty('İlan yok') }}{% endif %}
  </div>
</div>
{% endblock %}
"""

TEMPLATES["admin_listings.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import badge, pager, empty, rating_line %}
{% block title %}İlanlar{% endblock %}
{% block heading %}İlanlar{% endblock %}
{% block panel %}
<div class="spread mb">
  <form class="filters" style="margin:0;flex:1" method="get" action="{{ url_for('admin.listings') }}">
    <div class="field grow"><label for="q">Ara</label><input type="search" id="q" name="q" value="{{ text }}" placeholder="Başlık veya satıcı"></div>
    <div class="field"><label for="durum">Durum</label><select id="durum" name="durum"><option value="">Hepsi</option>
      {% for k, v in [('active', 'Yayında'), ('paused', 'Duraklatıldı'), ('blocked', 'Engelli'), ('removed', 'Silinmiş'), ('featured', 'Öne çıkanlar')] %}<option value="{{ k }}" {{ 'selected' if status == k }}>{{ v }}</option>{% endfor %}</select></div>
    <div class="field"><button class="btn" type="submit">Filtrele</button></div>
  </form>
  <a class="btn" href="{{ url_for('admin.listing_new') }}">İlan Oluştur</a>
</div>
{% if page.rows %}
<div class="table-wrap"><table>
  <tr><th>ID</th><th>İlan</th><th>Satıcı</th><th class="right">Fiyat</th><th class="right">Stok</th><th class="right">Satış</th><th>Puan</th><th>Durum</th><th></th></tr>
  {% for l in page.rows %}<tr>
    <td>#{{ l.id }}</td>
    <td><div class="row" style="flex-wrap:nowrap"><div class="thumb">{% if l.cover %}<img src="{{ cover_url(l.cover, true) }}" alt="">{% endif %}</div><div><a href="{{ url_for('listing_detail', lid=l.id) }}"><b>{{ l.title[:44] }}</b></a> {% if l.is_featured %}<span class="badge b-warn">Öne çıkan</span>{% endif %}{% if l.is_deal %} <span class="badge b-info">Fırsat</span>{% endif %}{% if l.is_demo %} <span class="badge b-muted">Demo</span>{% endif %}<div class="muted small">{{ l.cat_name }}</div></div></div></td>
    <td><a href="{{ url_for('admin.user', uid=l.seller_id) }}">{{ l.seller_name }}</a>{{ pkg_marks(l.seller_id) }}</td>
    <td class="right nowrap">{% if l.old_price %}<span class="price-old">{{ l.old_price|money }}</span>{% endif %}{{ l.price|money }}</td><td class="right">{{ l.stock }}</td><td class="right">{{ l.sales_count }}</td>
    <td>{{ rating_line(rating_of(l), l.rating_count) }}</td>
    <td>{{ badge(l.status) }}</td>
    <td class="actions"><div class="mini-form">
      <a class="btn btn-ghost btn-sm" href="{{ url_for('admin.listing_edit', lid=l.id) }}">Düzenle</a>
      <form method="post" action="{{ url_for('admin.listing_feature', lid=l.id) }}">{{ csrf_field() }}<button class="btn btn-line btn-sm" type="submit">{{ 'Öne çıkarmayı kaldır' if l.is_featured else 'Öne çıkar' }}</button></form>
      <form method="post" action="{{ url_for('admin.listing_deal', lid=l.id) }}">{{ csrf_field() }}<button class="btn btn-line btn-sm" type="submit" title="{{ 'Fırsat listesinden çıkar' if l.is_deal else 'Fırsat ürünlerine ekle (eski fiyat gerekir)' }}">{{ 'Fırsattan çıkar' if l.is_deal else 'Fırsata ekle' }}</button></form>
      <form method="post" action="{{ url_for('admin.listing_status', lid=l.id) }}">{{ csrf_field() }}
        <select name="status" style="width:auto;padding:5px 8px">{% for k, v in [('active', 'Yayınla'), ('paused', 'Duraklat'), ('blocked', 'Engelle'), ('removed', 'Kaldır')] %}<option value="{{ k }}" {{ 'selected' if l.status == k }}>{{ v }}</option>{% endfor %}</select>
        <button class="btn btn-sm" type="submit">Uygula</button></form>
    </div></td>
  </tr>{% endfor %}
</table></div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('İlan bulunamadı') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["admin_listing_form.html"] = r"""
{% extends "admin_base.html" %}
{% block title %}{{ 'İlanı Düzenle' if item else 'İlan Oluştur' }}{% endblock %}
{% block heading %}{{ 'İlanı düzenle #' ~ item.id if item else 'İlan oluştur' }}{% endblock %}
{% block panel %}
<div class="card" style="max-width:860px">
  <form method="post" enctype="multipart/form-data" action="{{ url_for('admin.listing_edit', lid=item.id) if item else url_for('admin.listing_new') }}">
    {{ csrf_field() }}
    {% if item %}
      <p class="muted mt0">Satıcı: <a href="{{ url_for('admin.user', uid=item.seller_id) }}">{{ item.seller_name }}</a>{{ pkg_marks(item.seller_id) }} &middot; Durum: {{ item.status|slabel }} &middot; Mevcut stok: {{ item.stock }}</p>
    {% else %}
      <div class="field"><label for="seller">Satıcı (kullanıcı adı)</label><input type="text" id="seller" name="seller" list="seller-list" value="{{ form.seller }}" required maxlength="30" autocomplete="off">
        <datalist id="seller-list">{% for s in sellers %}<option value="{{ s.username }}">{% endfor %}</datalist>
        <div class="hint">İlan bu kullanıcının adına oluşturulur; satışlardan onun hesabına kazanç yazılır.</div></div>
      <label class="check field"><input type="checkbox" name="make_seller" value="1" {{ 'checked' if form.make_seller }}> <span>Kullanıcı satıcı değilse onu satıcı yap</span></label>
    {% endif %}
    <div class="field"><label for="title">Başlık</label><input type="text" id="title" name="title" value="{{ form.title }}" required minlength="5" maxlength="90"></div>
    <div class="form-row">
      <div class="field"><label for="category_id">Kategori</label><select id="category_id" name="category_id" required>{% for c in cats %}<option value="{{ c.id }}" {{ 'selected' if form.category_id|string == c.id|string }}>{{ c.name }}</option>{% endfor %}</select></div>
      <div class="field"><label for="price">Fiyat (TL)</label><input type="text" inputmode="decimal" id="price" name="price" value="{{ form.price }}" required></div>
    </div>
    <div class="field"><label for="old_price">Eski fiyat (TL, isteğe bağlı)</label><input type="text" inputmode="decimal" id="old_price" name="old_price" value="{{ form.old_price }}"><div class="hint">Doluysa kartta üstü çizili gösterilir; Fırsata ekle için gereklidir.</div></div>
    <div class="field"><label for="description">Açıklama</label><textarea id="description" name="description" required minlength="20" maxlength="2000" style="min-height:140px">{{ form.description }}</textarea></div>
    <div class="field"><label for="cover">Kapak görseli</label><input type="file" id="cover" name="cover" accept="image/jpeg,image/png,image/webp" data-preview="#cover-preview">
      <img id="cover-preview" class="preview-img" alt="Kapak önizleme" {% if item and item.cover %}src="{{ cover_url(item.cover) }}"{% else %}hidden{% endif %}></div>
    <div class="field"><label for="codes">{{ 'Eklenecek yeni kodlar (isteğe bağlı, her satıra bir kod)' if item else 'E-pin kodları (her satıra bir kod)' }}</label>
      <textarea id="codes" name="codes" class="mono" style="min-height:140px" data-count-lines="#code-count" {{ 'required' if not item }}>{{ form.codes }}</textarea>
      <div class="hint"><span id="code-count">0</span> benzersiz kod algılandı.</div></div>
    <button class="btn" type="submit">{{ 'Kaydet' if item else 'İlanı Oluştur' }}</button> <a class="btn btn-ghost" href="{{ url_for('admin.listings') }}">Vazgeç</a>
  </form>
</div>
{% endblock %}
"""

TEMPLATES["admin_orders.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import pager, empty %}
{% block title %}Siparişler{% endblock %}
{% block heading %}Siparişler{% endblock %}
{% block panel %}
<form class="filters" method="get" action="{{ url_for('admin.orders') }}">
  <div class="field grow"><label for="q">Ara</label><input type="search" id="q" name="q" value="{{ text }}" placeholder="Sipariş no, alıcı, satıcı veya ilan"></div>
  <div class="field"><button class="btn" type="submit">Ara</button></div>
</form>
<div class="grid g3 mb">
  <div class="stat"><div class="k">Adet</div><div class="v">{{ sums.qty }}</div></div>
  <div class="stat"><div class="k">Ciro</div><div class="v">{{ sums.gross|money }}</div></div>
  <div class="stat good"><div class="k">Komisyon</div><div class="v">{{ sums.fee|money }}</div></div>
</div>
{% if page.rows %}
<div class="table-wrap"><table>
  <tr><th>No</th><th>Tarih</th><th>İlan</th><th>Alıcı</th><th>Satıcı</th><th class="right">Adet</th><th class="right">Toplam</th><th class="right">Komisyon</th><th>Emanet</th></tr>
  {% for o in page.rows %}<tr><td>#{{ o.id }}</td><td class="nowrap">{{ o.created_at|dt }}</td><td>{{ o.listing_title[:40] }}</td><td>{{ o.buyer_name }}</td><td>{{ o.seller_name }}{{ pkg_marks(o.seller_id) }}</td><td class="right">{{ o.quantity }}</td><td class="right nowrap">{{ o.total|money }}</td><td class="right nowrap">{{ o.commission|money }} <span class="muted small">(%{{ o.commission_rate }})</span></td>
    <td><span class="badge b-{{ o.escrow_status|sclass }}">{{ o.escrow_status|slabel }}</span>
      {% if o.escrow_status in ('held', 'disputed') %}<form method="post" action="{{ url_for('admin.escrow_action', oid=o.id) }}" class="mt row">{{ csrf_field() }}
        <button class="btn btn-ok btn-sm" name="action" value="release" type="submit" data-confirm="Tutar satıcıya aktarılsın mı?">Aktar</button>
        <button class="btn btn-danger btn-sm" name="action" value="refund" type="submit" data-confirm="Tutar alıcıya iade edilsin mi?">İade</button></form>{% endif %}</td></tr>{% endfor %}
</table></div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Sipariş bulunamadı') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["admin_deposits.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import badge, pager, empty, status_tabs %}
{% block title %}Bakiye Yüklemeleri{% endblock %}
{% block heading %}Bakiye yüklemeleri{% endblock %}
{% block panel %}
{{ status_tabs('admin.deposits', status, counts) }}
{% if page.rows %}
<div class="table-wrap"><table>
  <tr><th>No</th><th>Tarih</th><th>Kullanıcı</th><th>Yöntem</th><th class="right">Tutar</th><th>Referans</th><th>Durum</th><th>İşlem</th></tr>
  {% for d in page.rows %}<tr>
    <td>#{{ d.id }}</td><td class="nowrap">{{ d.created_at|dt }}</td>
    <td><a href="{{ url_for('admin.user', uid=d.user_id) }}">{{ d.username }}</a></td>
    <td>{{ d.method_name }}</td><td class="right nowrap"><b>{{ d.amount|money }}</b>{% if d.bonus %}<div class="small pos">+ {{ d.bonus|money }} bonus</div>{% endif %}</td>
    <td>{{ d.reference }}{% if d.note %}<div class="muted small">{{ d.note }}</div>{% endif %}</td>
    <td>{{ badge(d.status) }}{% if d.auto %} <span class="badge b-muted">Otomatik</span>{% endif %}{% if d.admin_note %}<div class="muted small">{{ d.admin_note }}</div>{% endif %}</td>
    <td class="actions">{% if d.status == 'pending' %}
      <form method="post" action="{{ url_for('admin.deposit_action', did=d.id) }}" class="mini-form">{{ csrf_field() }}
        <input type="text" name="note" placeholder="Not (isteğe bağlı)" maxlength="300">
        <button class="btn btn-ok btn-sm" name="action" value="approve" type="submit" data-confirm="{{ (d.amount + d.bonus)|money }} bakiyeye eklensin mi?{{ ' (bonus dahil)' if d.bonus }}">Onayla</button>
        <button class="btn btn-danger btn-sm" name="action" value="reject" type="submit" data-confirm="Talep reddedilsin mi?">Reddet</button>
      </form>{% endif %}</td>
  </tr>{% endfor %}
</table></div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Bu durumda yükleme talebi yok') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["admin_withdrawals.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import badge, pager, empty, status_tabs %}
{% block title %}Çekim Talepleri{% endblock %}
{% block heading %}Çekim talepleri{% endblock %}
{% block panel %}
{{ status_tabs('admin.withdrawals', status, counts) }}
{% if page.rows %}
<div class="table-wrap"><table>
  <tr><th>No</th><th>Tarih</th><th>Kullanıcı</th><th class="right">Tutar</th><th class="right">Kesinti</th><th class="right">Ödenecek</th><th>Hesap bilgisi</th><th>Durum</th><th>İşlem</th></tr>
  {% for w in page.rows %}<tr>
    <td>#{{ w.id }}</td><td class="nowrap">{{ w.created_at|dt }}</td>
    <td><a href="{{ url_for('admin.user', uid=w.user_id) }}">{{ w.username }}</a><div class="muted small">Kimlik adı: {{ w.kyc_name or '-' }}</div></td>
    <td class="right nowrap">{{ w.amount|money }}</td><td class="right nowrap muted">{{ w.fee|money }}</td><td class="right nowrap"><b>{{ w.net|money }}</b></td>
    <td><b>{{ w.method }}</b><div class="mono small pre">{{ w.account_info }}</div></td>
    <td>{{ badge(w.status) }}{% if w.admin_note %}<div class="muted small">{{ w.admin_note }}</div>{% endif %}</td>
    <td class="actions">{% if w.status == 'pending' %}
      <form method="post" action="{{ url_for('admin.withdrawal_action', wid=w.id) }}" class="mini-form">{{ csrf_field() }}
        <input type="text" name="note" placeholder="Not / dekont no" maxlength="300">
        <button class="btn btn-ok btn-sm" name="action" value="approve" type="submit" data-confirm="Ödemeyi yaptığını onaylıyor musun? Kullanıcıya {{ w.net|money }} ödenecek.">Onayla</button>
        <button class="btn btn-danger btn-sm" name="action" value="reject" type="submit" data-confirm="Talep reddedilip tutar iade edilsin mi?">Reddet</button>
      </form>{% endif %}</td>
  </tr>{% endfor %}
</table></div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Bu durumda çekim talebi yok') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["admin_sellers.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import badge, pager, empty, status_tabs %}
{% block title %}Satıcı Başvuruları{% endblock %}
{% block heading %}Satıcı başvuruları{% endblock %}
{% block panel %}
{{ status_tabs('admin.sellers', status, counts) }}
{% if page.rows %}
<div class="grid" style="gap:14px">
  {% for a in page.rows %}
  <div class="card">
    <div class="spread mb">
      <div><h3 style="margin:0">{{ a.store_name }}</h3><span class="muted small">Başvuran: <a href="{{ url_for('admin.user', uid=a.user_id) }}">{{ a.username }}</a> &middot; {{ a.email }} &middot; {{ a.created_at|dt }}</span></div>
      <div class="row">{{ badge(a.status) }}<span class="badge b-{{ a.kyc_status|sclass }}">Kimlik: {{ a.kyc_status|slabel }}</span></div>
    </div>
    <div class="pre">{{ a.description }}</div>
    {% if a.experience %}<p class="muted small mt"><b>Deneyim:</b> {{ a.experience }}</p>{% endif %}
    {% if a.admin_note %}<p class="muted small"><b>Yönetici notu:</b> {{ a.admin_note }}</p>{% endif %}
    {% if a.status == 'pending' %}
    <form method="post" action="{{ url_for('admin.seller_action', aid=a.id) }}" class="mini-form mt" style="justify-content:flex-start">{{ csrf_field() }}
      <input type="text" name="note" placeholder="Not (reddederken kullanıcıya gösterilir)" maxlength="300" style="width:280px">
      <button class="btn btn-ok btn-sm" name="action" value="approve" type="submit" data-confirm="Başvuru onaylansın mı?">Onayla</button>
      <button class="btn btn-danger btn-sm" name="action" value="reject" type="submit" data-confirm="Başvuru reddedilsin mi?">Reddet</button>
    </form>{% endif %}
  </div>
  {% endfor %}
</div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Bu durumda başvuru yok') }}</div>{% endif %}
{% endblock %}
"""
