"""Satıcı paneli şablonları (Jinja). Emoji kullanılmaz."""

TEMPLATES = {}

TEMPLATES["seller_base.html"] = r"""
{% extends "base.html" %}
{% from "_macros.html" import avatar, ic with context %}
{% block body_class %} class="app"{% endblock %}
{% block site_header %}{% endblock %}
{% block site_footer %}{% endblock %}
{% block content %}
{% set ep = request.endpoint or '' %}
<div class="shell">
  <aside class="s-side" id="s-side">
    <a class="brand" href="{{ url_for('index') }}"><img class="brand-mark" src="{{ url_for('static', filename='logo.svg') }}" width="32" height="32" alt="">{{ site_name }}</a>
    <div class="who">{{ avatar(me.username, me.avatar, 'sm') }}<div><b>{{ me.store_name or me.username }}{{ pkg_marks(me.id) }}</b><small>@{{ me.username }}</small></div></div>
    <nav>
      <div class="sep">Yönetim</div>
      <a class="{{ 'on' if ep == 'seller.dashboard' }}" href="{{ url_for('seller.dashboard') }}">{{ ic('chart') }}Genel bakış</a>
      <a class="{{ 'on' if ep in ['seller.listings', 'seller.listing_edit', 'seller.stock'] }}" href="{{ url_for('seller.listings') }}">{{ ic('tag') }}İlanlarım{% if s_nav.lowstock %}<span class="cnt warn" title="Stoğu azalan ilan">{{ s_nav.lowstock }}</span>{% endif %}</a>
      <a class="{{ 'on' if ep == 'seller.listing_new' }}" href="{{ url_for('seller.listing_new') }}">{{ ic('plus') }}Yeni ilan</a>
      <a class="{{ 'on' if ep in ['seller.doping', 'seller.doping_buy'] }}" href="{{ url_for('seller.doping') }}">{{ ic('flame') }}Doping</a>
      <a class="{{ 'on' if ep == 'seller.sales' }}" href="{{ url_for('seller.sales') }}">{{ ic('receipt') }}Satışlarım</a>
      <a class="{{ 'on' if ep == 'seller.earnings' }}" href="{{ url_for('seller.earnings') }}">{{ ic('wallet') }}Kazançlarım{% if s_nav.held %}<span class="cnt" title="Emanetteki sipariş">{{ s_nav.held }}</span>{% endif %}</a>
      <a class="{{ 'on' if ep == 'seller.reviews' }}" href="{{ url_for('seller.reviews') }}">{{ ic('star') }}Yorumlar{% if s_nav.unreplied %}<span class="cnt" title="Yanıt bekleyen yorum">{{ s_nav.unreplied }}</span>{% endif %}</a>
      <a class="{{ 'on' if ep == 'seller.commission' }}" href="{{ url_for('seller.commission') }}">{{ ic('percent') }}Komisyon</a>
      <a class="{{ 'on' if ep in ['seller.packages', 'seller.package_buy'] }}" href="{{ url_for('seller.packages') }}">{{ ic('award') }}Paketler</a>
      <div class="sep">Mağaza</div>
      <a class="{{ 'on' if ep == 'seller.store' }}" href="{{ url_for('seller.store') }}">{{ ic('store') }}Mağaza profili</a>
      <a class="{{ 'on' if ep == 'seller.showcase' }}" href="{{ url_for('seller.showcase') }}">{{ ic('image') }}Vitrin ve adres</a>
      <a class="{{ 'on' if ep == 'seller.customers' }}" href="{{ url_for('seller.customers') }}">{{ ic('users') }}Müşterilerim</a>
      <a class="{{ 'on' if ep == 'seller.followers' }}" href="{{ url_for('seller.followers') }}">{{ ic('heart') }}Takipçilerim</a>
      <a class="{{ 'on' if ep == 'seller.giveaways' }}" href="{{ url_for('seller.giveaways') }}">{{ ic('gift') }}Çekilişlerim</a>
      <a class="{{ 'on' if ep == 'seller.api_keys' }}" href="{{ url_for('seller.api_keys') }}">{{ ic('code') }}API erişimi</a>
      <a href="{{ url_for('storefront', username=me.username) }}" target="_blank" rel="noopener">{{ ic('external') }}Herkese açık sayfa</a>
      <div class="sep">Hesap</div>
      <a href="{{ url_for('withdraw') }}">{{ ic('wallet') }}Para çek</a>
      <a href="{{ url_for('inbox') }}">{{ ic('message') }}Mesajlar{% if unread_chat %}<span class="cnt">{{ unread_chat }}</span>{% endif %}</a>
      <a href="{{ url_for('tickets') }}">{{ ic('life-buoy') }}Destek{% if answered_tickets %}<span class="cnt">{{ answered_tickets }}</span>{% endif %}</a>
      <a href="{{ url_for('account') }}">{{ ic('user') }}Alıcı hesabım</a>
      <a href="{{ url_for('index') }}">{{ ic('home') }}Siteye dön</a>
    </nav>
  </aside>
  <div class="s-main">
    <div class="s-top">
      <div class="row">
        <button class="ibtn a-toggle" type="button" data-toggle-nav="#s-side" aria-label="Menü">{{ ic('menu') }}</button>
        <span class="tag-seller">SATICI PANELİ</span>
      </div>
      <div class="row">
        <a class="chip" href="{{ url_for('withdraw') }}" title="Bakiyen">{{ ic('wallet') }}{{ me.balance|money }}</a>
        <a class="ibtn" href="{{ url_for('site.notifications') }}" aria-label="Bildirimler">{{ ic('bell') }}{% if notif_unread %}<span class="dot">{{ notif_unread if notif_unread < 10 else '9+' }}</span>{% endif %}</a>
        <a class="btn btn-sm" href="{{ url_for('seller.listing_new') }}">{{ ic('plus') }}Yeni ilan</a>
      </div>
    </div>
    {% block panel %}{% endblock %}
  </div>
</div>
{% endblock %}
"""

TEMPLATES["seller_dashboard.html"] = r"""
{% extends "seller_base.html" %}
{% from "_macros.html" import bars, badge, badge_list, rating_line, empty, ic, spark with context %}
{% macro trend(v) %}{% if v is not none %}<span class="trend {{ 'up' if v >= 0 else 'down' }}">{{ '+' if v >= 0 }}%{{ v }}</span>{% endif %}{% endmacro %}
{% block title %}Satıcı Paneli{% endblock %}
{% block panel %}
{% set series = chart|map(attribute='value')|list %}
{% set checks = [
  ('Telefon numarası', me.phone, url_for('profile')),
  ('Profil fotoğrafı / logo', me.avatar, url_for('seller.store')),
  ('Mağaza açıklaması', (me.store_desc or '')|length > 10, url_for('seller.store')),
  ('En az 3 aktif ilan', counts.active >= 3, url_for('seller.listing_new')),
  ('Yanıtsız yorum yok', unreplied == 0, url_for('seller.reviews', durum='yanitsiz'))] %}
{% set done = checks|selectattr(1)|list|length %}

<div class="page-h">
  <div><div class="crumb">{{ greeting }}</div><h1>{{ me.store_name or me.username }}{{ pkg_marks(me.id) }}</h1></div>
  <div class="row"><a class="btn" href="{{ url_for('seller.listing_new') }}">{{ ic('plus') }}Yeni ilan</a><a class="btn btn-ghost btn-sm" href="{{ url_for('seller.sales_csv') }}">{{ ic('download') }}Satışları indir</a></div>
</div>
{% if badges %}<div class="mb">{{ badge_list(badges) }}</div>{% endif %}
{% set mypk = my_packages() %}
<div class="card pk-mini mb">
  <div class="spread">
    <div class="row"><b>{{ ic('award') }} Paketlerim</b>
      {% for a in mypk %}<span class="pk-chip" style="--c:{{ a.color }}"><b>{{ a.name }}</b><em>{% if a.permanent %}Kalıcı{% else %}{{ a.until|dt(false) }}{% endif %}</em></span>{% else %}<span class="muted small">Aktif paketin yok. Mavi tik ve diğer paketlerle mağazanı öne çıkar.</span>{% endfor %}
    </div>
    <a class="btn btn-ghost btn-sm" href="{{ url_for('seller.packages') }}">{{ 'Paketleri yönet' if mypk else 'Paketlere göz at' }}</a>
  </div>
</div>

{% if vacation %}<div class="notice warn mb">Mağazan tatil modunda; yeni sipariş alınmıyor. <a href="{{ url_for('seller.showcase') }}">Tatili yönet</a></div>{% endif %}
{% if goal %}
<div class="card goal-card mb">
  <div class="spread"><b>Aylık hedef</b><a class="small" href="{{ url_for('seller.showcase') }}">Hedefi düzenle</a></div>
  <div class="meter"><i style="width:{{ goal.pct }}%"></i></div>
  <div class="spread small"><span>{{ goal.got|money }} / {{ goal.goal|money }}</span><span class="{{ 'pos' if goal.done else 'muted' }}">{% if goal.done %}Hedef tamamlandı{% else %}%{{ goal.pct }} &middot; {{ goal.left|money }} kaldı &middot; {{ goal.days_left }} gün{% endif %}</span></div>
</div>
{% endif %}
{% if attention %}
<div class="card attn mb">
  <div class="card-h"><h3>Dikkat gerektirenler</h3><span class="chip">{{ attention|length }}</span></div>
  {% for lvl, text, link, cta in attention %}
  <div class="attn-row {{ lvl }}"><i aria-hidden="true"></i><span>{{ text }}</span><a class="btn btn-ghost btn-sm" href="{{ link }}">{{ cta }}</a></div>
  {% endfor %}
</div>
{% else %}
<div class="notice ok mb">Her şey yolunda: bekleyen bir işin yok.</div>
{% endif %}

<div class="kpis mb">
  <div class="kpi"><div class="k">{{ ic('calendar') }}Bugün</div><div class="v">{{ periods.today_net|money }}</div><div class="s">{{ periods.today_qty }} adet satış {{ trend(trends.today) }}</div></div>
  <div class="kpi"><div class="k">{{ ic('activity') }}Son 7 gün</div><div class="v">{{ periods.week_net|money }}</div><div class="s">{{ periods.week_qty }} adet satış {{ trend(trends.week) }}</div></div>
  <div class="kpi"><div class="k">{{ ic('trend') }}Son 30 gün</div><div class="v">{{ periods.month_net|money }}</div><div class="s">{{ periods.month_qty }} adet satış {{ trend(trends.month) }}</div>{{ spark(series) }}</div>
  <div class="kpi"><div class="k">{{ ic('wallet') }}Çekilebilir</div><div class="v ok">{{ withdrawable|money }}</div><div class="s">{% if pending_wd %}Bekleyen çekim {{ pending_wd|money }}{% else %}<a href="{{ url_for('withdraw') }}">Para çek</a>{% endif %}</div></div>
</div>
<div class="small muted mb" style="margin-top:-8px">Yüzdeler bir önceki dönemle karşılaştırmadır (dün, önceki 7 gün, önceki 30 gün).</div>

<div class="grid g-main mb">
  <div class="card">
    <div class="card-h"><h3>Net kazanç</h3>
      <div class="row"><span class="small muted">{{ series|sum|money }} toplam</span>
        <div class="seg">{% for d in (7, 14, 30) %}<a class="{{ 'on' if days == d }}" href="{{ url_for('seller.dashboard', gun=d) }}">{{ d }} gün</a>{% endfor %}</div></div></div>
    {{ bars(chart, true) }}
  </div>
  <div class="stack">
    <div class="card">
      <div class="card-h"><h3>Bakiye özeti</h3><a class="small" href="{{ url_for('seller.earnings') }}">Kazançlarım</a></div>
      <div class="sum-row"><span>Çekilebilir</span><b class="pos">{{ withdrawable|money }}</b></div>
      <div class="sum-row"><span>Emanette bekleyen ({{ held.n }})</span><b>{{ held.s|money }}</b></div>
      <div class="sum-row"><span>Bekleyen çekim</span><b>{{ pending_wd|money }}</b></div>
      <div class="sum-row"><span>Toplam net kazanç</span><b>{{ totals.net|money }}</b></div>
      <a class="btn btn-sm mt" href="{{ url_for('withdraw') }}">Para çek</a>
    </div>
    <div class="card">
      <div class="card-h"><h3>Mağaza sağlığı</h3><span class="small muted">{{ done }} / {{ checks|length }}</span></div>
      <div class="meter mb"><i style="width:{{ (done * 100 / checks|length)|round|int }}%"></i></div>
      <div class="checklist">
        {% for label, ok, link in checks %}
        <a class="cl-row {{ 'ok' if ok }}" href="{{ link }}">{{ ic('check-circle' if ok else 'clock') }}<span>{{ label }}</span></a>
        {% endfor %}
      </div>
    </div>
  </div>
</div>

<div class="kpis c3 mb">
  <div class="kpi"><div class="k">{{ ic('package') }}Toplam satış</div><div class="v">{{ totals.sold }}</div><div class="s">{{ totals.orders }} sipariş</div></div>
  <div class="kpi"><div class="k">{{ ic('chart') }}Brüt ciro</div><div class="v">{{ totals.gross|money }}</div><div class="s">Net {{ totals.net|money }}</div></div>
  <div class="kpi"><div class="k">{{ ic('percent') }}Komisyon</div><div class="v">{{ totals.fee|money }}</div><div class="s">Genel %{{ global_rate }}{% if personal_rate is not none %} / sana özel %{{ personal_rate }}{% endif %}</div></div>
  <div class="kpi"><div class="k">{{ ic('tag') }}Aktif ilan</div><div class="v">{{ counts.active }}</div><div class="s">{{ counts.paused }} duraklatıldı &middot; {{ stock_total }} kod stokta</div></div>
  <div class="kpi"><div class="k">{{ ic('eye') }}Görüntülenme</div><div class="v">{{ counts.views }}</div><div class="s">{% if counts.views %}Dönüşüm %{{ (stats.sold * 100 / counts.views)|round(1)|string|replace('.', ',') if stats.sold is defined else '-' }}{% endif %}</div></div>
  <div class="kpi"><div class="k">{{ ic('star') }}Puan</div><div class="v">{{ stats.rating if stats.reviews else '-' }}</div><div class="s">{{ stats.reviews }} yorum</div></div>
</div>

<div class="two-col mb">
  <div class="card">
    <div class="card-h"><h3>Stoğu azalanlar</h3><a class="small" href="{{ url_for('seller.listings', sirala='stok') }}">İlanlarım</a></div>
    {% if low_stock %}<div class="table-wrap"><table>
      <tr><th>İlan</th><th class="right">Stok</th><th></th></tr>
      {% for l in low_stock %}<tr><td>{{ l.title[:44] }}</td><td class="right"><span class="badge b-{{ 'bad' if l.stock == 0 else 'warn' }}">{{ 'Tükendi' if l.stock == 0 else l.stock }}</span></td><td class="actions"><a class="btn btn-sm" href="{{ url_for('seller.stock', lid=l.id) }}">Kod ekle</a></td></tr>{% endfor %}
    </table></div>{% else %}{{ empty('Stok durumun iyi', 'Tüm ilanlarında en az 5 kod var.') }}{% endif %}
  </div>
  <div class="card">
    <div class="card-h"><h3>En çok kazandıranlar</h3></div>
    {% if top %}<div class="top-list">
      {% for t in top %}<div class="top-row"><div class="top-t"><span>{{ t.listing_title[:42] }}</span><b>{{ t.net|money }}</b></div>
        <div class="meter"><i style="width:{{ (t.net * 100 / top_max)|round|int }}%"></i></div><div class="small muted">{{ t.qty }} adet</div></div>{% endfor %}
    </div>{% else %}{{ empty('Henüz satış yok') }}{% endif %}
  </div>
</div>

<div class="card">
  <div class="card-h"><h3>Son satışlar</h3><a class="small" href="{{ url_for('seller.sales') }}">Tüm satışlar</a></div>
  {% if recent %}<div class="table-wrap"><table>
    <tr><th>No</th><th>Tarih</th><th>İlan</th><th>Alıcı</th><th class="right">Adet</th><th class="right">Toplam</th><th class="right">Net</th><th>Durum</th></tr>
    {% for o in recent %}<tr><td><a href="{{ url_for('order_detail', oid=o.id) }}">#{{ o.id }}</a></td><td class="nowrap">{{ o.created_at|dt }}</td><td>{{ o.listing_title[:36] }}</td><td>{{ o.buyer_name|mask }}</td><td class="right">{{ o.quantity }}</td><td class="right nowrap">{{ o.total|money }}</td><td class="right nowrap pos">{{ o.seller_earning|money }}</td><td>{{ badge(o.escrow_status) }}</td></tr>{% endfor %}
  </table></div>{% else %}{{ empty('Henüz satışın yok', 'İlanlarını görsel ve açıklamayla zenginleştirmek satışları artırır.') }}{% endif %}
</div>
{% endblock %}
"""

TEMPLATES["seller_listings.html"] = r"""
{% extends "seller_base.html" %}
{% from "_macros.html" import badge, pager, empty, rating_line, ic with context %}
{% block title %}İlanlarım{% endblock %}
{% block panel %}
<div class="page-h"><h1>İlanlarım</h1><a class="btn" href="{{ url_for('seller.listing_new') }}">Yeni İlan</a></div>
<div class="grid g4 mb">
  <div class="stat"><div class="k">Toplam ilan</div><div class="v">{{ counts.n }}</div><div class="s">{{ counts.active }} yayında</div></div>
  <div class="stat"><div class="k">Stoktaki kod</div><div class="v">{{ counts.stock_sum }}</div>{% if counts.soldout %}<div class="s neg">{{ counts.soldout }} ilan tükendi</div>{% endif %}</div>
  <div class="stat"><div class="k">Toplam satış</div><div class="v">{{ counts.sales }}</div></div>
  <div class="stat"><div class="k">Görüntülenme</div><div class="v">{{ counts.views }}</div>{% if counts.views %}<div class="s">Dönüşüm %{{ (counts.sales * 100 / counts.views)|round(1)|string|replace('.', ',') }}</div>{% endif %}</div>
</div>
<div class="tabs">
  {% for key, label, n in [('', 'Hepsi', counts.n), ('active', 'Yayında', counts.active), ('paused', 'Duraklatılan', counts.paused), ('soldout', 'Stoksuz', counts.soldout), ('blocked', 'Engelli', counts.blocked)] %}
  <a class="{{ 'on' if status == key }}" href="{{ url_for('seller.listings', durum=key or None, sirala=sort if sort != 'yeni' else None, q=text or None) }}">{{ label }} <span class="cnt">{{ n }}</span></a>
  {% endfor %}
</div>
<form class="filters" method="get" action="{{ url_for('seller.listings') }}">
  {% if status %}<input type="hidden" name="durum" value="{{ status }}">{% endif %}
  <div class="field grow"><label for="q">Ara</label><input type="search" id="q" name="q" value="{{ text }}" placeholder="İlan başlığı"></div>
  <div class="field"><label for="sirala">Sırala</label><select id="sirala" name="sirala">{% for k, v in sorts.items() %}<option value="{{ k }}" {{ 'selected' if sort == k }}>{{ v[0] }}</option>{% endfor %}</select></div>
  <div class="field"><button class="btn" type="submit">Uygula</button></div>
</form>
{% if page.rows %}
<form id="bulkform" method="post" action="{{ url_for('seller.bulk') }}" data-bulk>
  {{ csrf_field() }}
  <div class="bulk-bar">
    <b data-bulk-count>0 ilan seçili</b>
    <select name="action" aria-label="Toplu işlem" onchange="document.getElementById('bulk-pct').hidden = this.value !== 'price'">
      <option value="pause">Duraklat</option><option value="activate">Yayına al</option><option value="price">Fiyatı yüzde ile değiştir</option><option value="delete">Sil</option>
    </select>
    <input type="text" id="bulk-pct" name="pct" placeholder="% (örn. 10 ya da -5)" size="14" hidden inputmode="decimal">
    <button class="btn btn-sm" type="submit">Uygula</button>
  </div>
<div class="table-wrap"><table>
  <tr><th class="chk"><input type="checkbox" data-check-all='input[name="ids"]' aria-label="Hepsini seç"></th><th>İlan</th><th class="right">Fiyat</th><th class="right">Stok</th><th class="right">Satış</th><th class="right">Görüntülenme</th><th>Puan</th><th>Durum</th><th></th></tr>
  {% for l in page.rows %}<tr>
    <td class="chk"><input type="checkbox" name="ids" value="{{ l.id }}" aria-label="İlanı seç"></td>
    <td><div class="row" style="flex-wrap:nowrap"><div class="thumb">{% if l.cover %}<img src="{{ cover_url(l.cover, true) }}" alt="">{% endif %}</div><div><a href="{{ url_for('listing_detail', lid=l.id) }}"><b>{{ l.title[:52] }}</b></a><div class="muted small">{{ l.cat_name }}</div>{% if l.dp %}<div class="dp-tags">{% for d in l.dp %}<span class="dp-tag dp-{{ d.kind }}" title="{{ d.label }} - bitiş {{ d.ends_at|dt }}">{{ ic('flame') }}{{ d.label }} <small>{{ d.ends_at|dt }}</small></span>{% endfor %}</div>{% endif %}</div></div></td>
    <td class="right nowrap">{{ l.price|money }}</td>
    <td class="right"><span class="badge b-{{ 'bad' if l.stock == 0 else ('warn' if l.stock < 5 else 'ok') }}">{{ 'Tükendi' if l.stock == 0 else l.stock }}</span></td>
    <td class="right">{{ l.sales_count }}</td>
    <td class="right">{{ l.views }}{% if l.views %}<div class="muted small">%{{ (l.sales_count * 100 / l.views)|round(1)|string|replace('.', ',') }} dönüşüm</div>{% endif %}</td>
    <td>{{ rating_line(rating_of(l), l.rating_count) }}</td>
    <td>{{ badge(l.status) }}</td>
    <td class="actions">
      <div class="mini-form">
        <a class="btn {{ '' if l.stock < 5 else 'btn-ghost' }} btn-sm" href="{{ url_for('seller.stock', lid=l.id) }}">{{ 'Kod ekle' if l.stock < 5 else 'Stok' }}</a>
        {% if l.status == 'active' %}<a class="btn btn-dp btn-sm" href="{{ url_for('seller.doping_buy', lid=l.id) }}">{{ ic('flame') }}Doping al</a>{% endif %}
        <a class="btn btn-ghost btn-sm" href="{{ url_for('seller.listing_edit', lid=l.id) }}">Düzenle</a>
        {% if l.status != 'blocked' %}<form method="post" action="{{ url_for('seller.listing_status', lid=l.id) }}">{{ csrf_field() }}<button class="btn btn-line btn-sm" type="submit">{{ 'Duraklat' if l.status == 'active' else 'Yayınla' }}</button></form>{% endif %}
        <button class="btn btn-ghost btn-sm" type="submit" formaction="{{ url_for('seller.listing_copy', lid=l.id) }}" formnovalidate title="İlanı stoksuz, duraklatılmış olarak kopyala">Kopyala</button>
        <button class="btn btn-danger btn-sm" type="submit" formaction="{{ url_for('seller.listing_delete', lid=l.id) }}" formnovalidate onclick="return confirm('Bu ilan silinsin mi? Geçmiş siparişler korunur.')">Sil</button>
      </div>
    </td>
  </tr>{% endfor %}
</table></div></form>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Bu filtreyle ilan yok' if (status or text) else 'Henüz ilanın yok', 'Kapak görseli, net açıklama ve doğru fiyatla ilk ilanını oluştur.' if not (status or text) else 'Filtreyi değiştirmeyi dene.') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["seller_listing_form.html"] = r"""
{% extends "seller_base.html" %}
{% from "_macros.html" import ic with context %}
{% from "_doping.html" import doping_picker with context %}
{% block title %}{{ 'İlanı Düzenle' if item else 'Yeni İlan' }}{% endblock %}
{% block panel %}
<div class="page-h"><h1>{{ 'İlanı düzenle' if item else 'Yeni ilan' }}</h1><a class="btn btn-ghost btn-sm" href="{{ url_for('seller.listings') }}">İlanlarım</a></div>
<div class="card">
  <form method="post" enctype="multipart/form-data" action="{{ url_for('seller.listing_edit', lid=item.id) if item else url_for('seller.listing_new') }}">
    {{ csrf_field() }}
    <div class="field"><label for="title">İlan başlığı</label><input type="text" id="title" name="title" value="{{ form.title }}" required minlength="5" maxlength="90" placeholder="Örn. Steam 250 TL Cüzdan Kodu - Anında Teslim"></div>
    <div class="form-row">
      <div class="field"><label for="cat-select">Kategori</label>
        <select id="cat-select" name="category_id" required>{% for c in cats %}<option value="{{ c.id }}" data-rate="{{ rates[c.id][0] }}" {{ 'selected' if form.category_id|string == c.id|string }}>{{ c.name }}</option>{% endfor %}</select></div>
      <div class="field"><label for="price-input">Fiyat (TL)</label><input type="text" inputmode="decimal" id="price-input" name="price" value="{{ form.price }}" required placeholder="250,00"></div>
    </div>
    <div class="field"><label for="old_price">Eski fiyat (isteğe bağlı)</label><input type="text" inputmode="decimal" id="old_price" name="old_price" value="{{ form.old_price }}" placeholder="300,00"><div class="hint">Doldurursan kartta üstü çizili gösterilir ve indirim yüzdesi hesaplanır. Güncel fiyattan yüksek olmalı.</div></div>
    <div class="calc mb">
      <div><small>Komisyon oranın</small><b id="rate-preview">-</b></div>
      <div><small>Satış başına kesinti</small><b id="fee-preview">-</b></div>
      <div><small>Eline geçecek net tutar</small><b id="net-preview">-</b></div>
    </div>
    <div class="field"><label for="phone">Telefon numaran</label><input type="tel" id="phone" name="phone" value="{{ form.phone if form.phone is defined else me.phone }}" required maxlength="20" placeholder="+90 5xx xxx xx xx"><div class="hint">Yalnızca yönetim ekibi görür; alıcılara gösterilmez.</div></div>
    <div class="field"><label for="description">Açıklama</label><textarea id="description" name="description" required minlength="20" maxlength="2000" style="min-height:150px" placeholder="Kodun ne olduğunu, hangi bölge/hesap için geçerli olduğunu ve nasıl kullanılacağını anlat.">{{ form.description }}</textarea><div class="hint">En az 20 karakter. Ayrıntılı açıklama daha çok güven ve satış getirir.</div></div>
    <div class="field"><label for="cover">Kapak görseli {% if cfg.require_cover == '1' and not (item and item.cover) %}(zorunlu){% endif %}</label>
      <input type="file" id="cover" name="cover" accept="image/jpeg,image/png,image/webp" data-preview="#cover-preview" {{ 'required' if cfg.require_cover == '1' and not (item and item.cover) }}>
      <div class="hint">JPG, PNG veya WEBP; en fazla 6 MB, en az 320 piksel. 16:10 oranında yatay görseller en iyi görünür.</div>
      <img id="cover-preview" class="preview-img" alt="Kapak önizleme" {% if item and item.cover %}src="{{ cover_url(item.cover) }}"{% else %}hidden{% endif %}></div>
    {% if not item %}
    <div class="field"><label for="codes">E-pin kodları (her satıra bir kod)</label><textarea id="codes" name="codes" required style="min-height:150px" class="mono" data-count-lines="#code-count">{{ form.codes }}</textarea><div class="hint"><span id="code-count">0</span> benzersiz kod algılandı. Tekrar eden satırlar otomatik atlanır.</div></div>
    {% endif %}
    {% if not item %}{{ doping_picker(doping, dsel, me.balance, dkey) }}{% endif %}
    <button class="btn" type="submit">{{ 'Değişiklikleri Kaydet' if item else 'İlanı Yayınla' }}</button>
    {% if item %}<a class="btn btn-ghost" href="{{ url_for('seller.stock', lid=item.id) }}">Stok yönetimi</a><a class="btn btn-ghost" href="{{ url_for('seller.doping_buy', lid=item.id) }}">{{ ic('flame') }} Doping al</a>{% endif %}
  </form>
</div>
{% endblock %}
"""

TEMPLATES["seller_stock.html"] = r"""
{% extends "seller_base.html" %}
{% from "_macros.html" import pager, empty %}
{% block title %}Stok - {{ l.title }}{% endblock %}
{% block panel %}
<div class="page-h"><div><h1>Stok yönetimi</h1><span class="muted">{{ l.title }}</span></div><a class="btn btn-ghost btn-sm" href="{{ url_for('seller.listings') }}">İlanlarım</a></div>
<div class="grid g3 mb">
  <div class="stat good"><div class="k">Satışa hazır kod</div><div class="v">{{ counts.available }}</div></div>
  <div class="stat"><div class="k">Satılan kod</div><div class="v">{{ counts.sold }}</div></div>
  <div class="stat"><div class="k">Fiyat</div><div class="v">{{ l.price|money }}</div></div>
</div>
<div class="card mb">
  <h3 class="mt0">Kod ekle</h3>
  <form method="post" action="{{ url_for('seller.stock', lid=l.id) }}">
    {{ csrf_field() }}
    <div class="field"><textarea name="codes" required class="mono" style="min-height:140px" placeholder="Her satıra bir kod" data-count-lines="#code-count"></textarea><div class="hint"><span id="code-count">0</span> benzersiz kod algılandı. Aynı ilanda zaten olan kodlar atlanır.</div></div>
    <button class="btn" type="submit">Stoğa Ekle</button>
  </form>
</div>
<div class="card">
  <h3 class="mt0">Satılmamış kodlar</h3>
  {% if page.rows %}<div class="table-wrap"><table>
    <tr><th>Kod</th><th>Eklenme</th><th></th></tr>
    {% for c in page.rows %}<tr><td class="mono">{{ c.code }}</td><td class="nowrap muted">{{ c.created_at|dt }}</td>
      <td class="actions"><form method="post" action="{{ url_for('seller.stock_delete', lid=l.id, cid=c.id) }}" data-confirm="Bu kod silinsin mi?">{{ csrf_field() }}<button class="btn btn-danger btn-sm" type="submit">Sil</button></form></td></tr>{% endfor %}
  </table></div>{{ pager(page) }}{% else %}{{ empty('Stokta kod yok', 'Yukarıdan kod ekleyerek ilanı yeniden satışa hazırla.') }}{% endif %}
</div>
{% endblock %}
"""

TEMPLATES["seller_sales.html"] = r"""
{% extends "seller_base.html" %}
{% from "_macros.html" import badge, pager, empty %}
{% block title %}Satışlarım{% endblock %}
{% block panel %}
<div class="page-h"><h1>Satışlarım</h1><a class="btn btn-ghost btn-sm" href="{{ url_for('seller.sales_csv', **f.to_dict()) }}">CSV olarak indir</a></div>
<form class="filters" method="get" action="{{ url_for('seller.sales') }}">
  <div class="field grow"><label for="q">Sipariş no veya alıcı</label><input type="search" id="q" name="q" value="{{ f.get('q', '') }}"></div>
  <div class="field"><label for="ilan">İlan</label><select id="ilan" name="ilan"><option value="">Hepsi</option>{% for x in my_listings %}<option value="{{ x.id }}" {{ 'selected' if f.get('ilan', '') == x.id|string }}>{{ x.title[:40] }}</option>{% endfor %}</select></div>
  <div class="field"><label for="durum">Durum</label><select id="durum" name="durum"><option value="">Hepsi</option>{% for k, v in [('held', 'Emanette'), ('released', 'Tamamlandı'), ('disputed', 'İtiraz var'), ('refunded', 'İade edildi')] %}<option value="{{ k }}" {{ 'selected' if f.get('durum', '') == k }}>{{ v }} ({{ status_counts.get(k, 0) }})</option>{% endfor %}</select></div>
  <div class="field"><label for="baslangic">Başlangıç</label><input type="date" id="baslangic" name="baslangic" value="{{ f.get('baslangic', '') }}"></div>
  <div class="field"><label for="bitis">Bitiş</label><input type="date" id="bitis" name="bitis" value="{{ f.get('bitis', '') }}"></div>
  <div class="field"><button class="btn" type="submit">Filtrele</button></div>
</form>
<div class="grid g4 mb">
  <div class="stat"><div class="k">Adet</div><div class="v">{{ sums.qty }}</div></div>
  <div class="stat"><div class="k">Brüt</div><div class="v">{{ sums.gross|money }}</div></div>
  <div class="stat"><div class="k">Komisyon</div><div class="v">{{ sums.fee|money }}</div></div>
  <div class="stat good"><div class="k">Net kazanç</div><div class="v">{{ sums.net|money }}</div></div>
</div>
{% if page.rows %}
<div class="table-wrap"><table>
  <tr><th>No</th><th>Tarih</th><th>İlan</th><th>Alıcı</th><th class="right">Adet</th><th class="right">Toplam</th><th class="right">Komisyon</th><th class="right">Net</th><th>Durum</th></tr>
  {% for o in page.rows %}<tr><td><a href="{{ url_for('order_detail', oid=o.id) }}">#{{ o.id }}</a></td><td class="nowrap">{{ o.created_at|dt }}</td><td>{{ o.listing_title[:40] }}</td><td>{{ o.buyer_name }}</td><td class="right">{{ o.quantity }}</td><td class="right nowrap">{{ o.total|money }}</td><td class="right nowrap muted">{{ o.commission|money }} (%{{ o.commission_rate }})</td><td class="right nowrap pos">{{ o.seller_earning|money }}</td><td>{{ badge(o.escrow_status) }}</td></tr>{% endfor %}
</table></div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Bu filtreyle eşleşen satış yok') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["seller_commission.html"] = r"""
{% extends "seller_base.html" %}
{% block title %}Komisyon{% endblock %}
{% block panel %}
<div class="page-h"><h1>Komisyon ve kesintiler</h1></div>
<div class="grid g3 mb">
  <div class="stat"><div class="k">Bugüne kadar ödenen komisyon</div><div class="v">{{ totals.fee|money }}</div></div>
  <div class="stat"><div class="k">Brüt ciro</div><div class="v">{{ totals.gross|money }}</div></div>
  <div class="stat"><div class="k">Para çekme kesintisi</div><div class="v">%{{ fee_rate }}</div><div class="s">Çekim tutarı üzerinden</div></div>
</div>
<div class="card mb">
  <h3 class="mt0">Kategorilere göre komisyon oranların</h3>
  <p class="muted">Bir satışta uygulanan oran sipariş anında sabitlenir ve sonradan değişmez. Öncelik sırası: sana özel oran, kategori oranı, genel oran.</p>
  <div class="table-wrap"><table>
    <tr><th>Kategori</th><th class="right">Oran</th><th>Kaynak</th><th class="right">100 TL'lik satışta net</th></tr>
    {% for r in rows %}<tr><td>{{ r.cat.name }}</td><td class="right"><b>%{{ r.rate }}</b></td><td class="muted">{{ r.source }}</td><td class="right nowrap">{{ (10000 - (10000 * r.rate / 100)|round|int)|money }}</td></tr>{% endfor %}
  </table></div>
</div>
<div class="card">
  <h3 class="mt0">Nasıl hesaplanır?</h3>
  <p class="muted mt0">Komisyon = satış tutarı x oran. Satıcı kazancı = satış tutarı - komisyon; anında bakiyene eklenir. Alıcıdan ek ücret alınmaz. Oranlarla ilgili özel bir talebin varsa <a href="{{ url_for('ticket_new') }}">destek talebi</a> açabilirsin.</p>
</div>
{% endblock %}
"""

TEMPLATES["seller_reviews.html"] = r"""
{% extends "seller_base.html" %}
{% from "_macros.html" import pager, empty, stars, rating_line %}
{% block title %}Yorumlar{% endblock %}
{% block panel %}
<div class="page-h"><h1>Müşteri yorumları</h1>{{ rating_line(stats.rating, stats.reviews) }}</div>
<div class="tabs">
  <a class="{{ 'on' if not only_open }}" href="{{ url_for('seller.reviews') }}">Tümü</a>
  <a class="{{ 'on' if only_open }}" href="{{ url_for('seller.reviews', durum='yanitsiz') }}">Yanıt bekleyenler</a>
</div>
{% if page.rows %}
<div class="card">
  {% for r in page.rows %}
  <div class="review">
    <div class="who">{{ stars(r.rating, true) }}<b>{{ r.buyer_name|mask }}</b><span class="muted small">{{ r.listing_title[:50] }} &middot; {{ r.created_at|dt }}</span></div>
    <div class="pre">{{ r.comment or 'Yorum yazılmadı.' }}</div>
    {% if r.seller_reply %}<div class="reply"><b>Yanıtın:</b> {{ r.seller_reply }}</div>{% endif %}
    <form method="post" action="{{ url_for('seller.review_reply', rid=r.id) }}" class="mt">
      {{ csrf_field() }}
      <div class="row" style="flex-wrap:nowrap"><input type="text" name="reply" maxlength="300" placeholder="{{ 'Yanıtı güncelle' if r.seller_reply else 'Yoruma yanıt yaz' }}" required><button class="btn btn-ghost btn-sm" type="submit">Yanıtla</button></div>
    </form>
  </div>
  {% endfor %}
</div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Henüz yorum yok', 'Alıcılar siparişlerinin ardından yorum bırakabilir.') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["seller_api.html"] = r"""
{% extends "seller_base.html" %}
{% from "_macros.html" import empty %}
{% block title %}API Erişimi{% endblock %}
{% block panel %}
{% set base = request.host_url.rstrip('/') %}
<div class="page-h"><h1>API erişimi</h1></div>

{% if new_key %}
<div class="card mb">
  <h3 class="mt0">Yeni anahtarın oluşturuldu</h3>
  <p class="muted">Bu anahtarı yalnızca <b>şimdi</b> görebilirsin. Güvenli bir yere kaydet; kaybedersen iptal edip yenisini oluşturman gerekir.</p>
  <div class="keybox mono" id="newkey">{{ new_key }}</div>
  <div class="row mt"><button type="button" class="btn btn-sm" data-copy="#newkey">Anahtarı kopyala</button></div>
</div>
{% endif %}

<div class="card mb">
  <h3 class="mt0">API anahtarların</h3>
  {% if keys %}<div class="table-wrap"><table>
    <tr><th>Ad</th><th>Anahtar</th><th>Son kullanım</th><th>Oluşturma</th><th>Durum</th><th></th></tr>
    {% for k in keys %}<tr><td>{{ k.name }}</td><td class="mono">{{ k.key_prefix }}...</td><td class="nowrap">{{ k.last_used_at|dt if k.last_used_at else '-' }}</td><td class="nowrap">{{ k.created_at|dt }}</td>
      <td><span class="badge b-{{ 'ok' if k.is_active else 'bad' }}">{{ 'Aktif' if k.is_active else 'İptal' }}</span></td>
      <td class="actions">{% if k.is_active %}<form method="post" action="{{ url_for('seller.api_keys') }}" data-confirm="Bu anahtar iptal edilsin mi? Bunu kullanan tüm araçlar çalışmayı durdurur.">{{ csrf_field() }}<input type="hidden" name="action" value="revoke"><input type="hidden" name="id" value="{{ k.id }}"><button class="btn btn-danger btn-sm" type="submit">İptal et</button></form>{% endif %}</td></tr>{% endfor %}
  </table></div>{% else %}{{ empty('Henüz API anahtarın yok') }}{% endif %}
  <form method="post" action="{{ url_for('seller.api_keys') }}" class="row mt">
    {{ csrf_field() }}<input type="hidden" name="action" value="create">
    <div class="field" style="flex:1;min-width:220px;margin:0"><label for="name">Yeni anahtar adı</label><input type="text" id="name" name="name" maxlength="40" required placeholder="Örn. Stok botu"></div>
    <button class="btn" type="submit">Anahtar Oluştur</button>
  </form>
</div>

<div class="card doc">
  <h3 class="mt0">Kullanım</h3>
  <p class="muted">Tüm isteklerde <code class="inline">Authorization: Bearer &lt;anahtar&gt;</code> başlığı gerekir. Dakikada en fazla 120 istek gönderebilirsin. Yanıtlar JSON'dur.</p>
  <h3>Profil ve bakiye</h3>
<pre>curl {{ base }}/api/v1/me \
  -H "Authorization: Bearer itm_..."</pre>
  <h3>İlanlarını listele</h3>
<pre>curl {{ base }}/api/v1/listings \
  -H "Authorization: Bearer itm_..."</pre>
  <h3>Stoğa kod ekle</h3>
<pre>curl -X POST {{ base }}/api/v1/listings/12/stock \
  -H "Authorization: Bearer itm_..." \
  -H "Content-Type: application/json" \
  -d '{"codes": ["ABCD-1234", "EFGH-5678"]}'</pre>
  <h3>İlanı duraklat / yayınla</h3>
<pre>curl -X POST {{ base }}/api/v1/listings/12/status \
  -H "Authorization: Bearer itm_..." \
  -H "Content-Type: application/json" \
  -d '{"status": "paused"}'</pre>
  <h3>Satışları çek</h3>
<pre>curl "{{ base }}/api/v1/orders?after_id=0&amp;limit=50" \
  -H "Authorization: Bearer itm_..."</pre>
  <p class="muted small">Satış yanıtlarında alıcıya teslim edilen kodlar yer almaz.</p>
</div>
{% endblock %}
"""

TEMPLATES["seller_store.html"] = r"""
{% extends "seller_base.html" %}
{% from "_macros.html" import avatar, badge_list %}
{% block title %}Mağazam{% endblock %}
{% block panel %}
<div class="page-h"><h1>Mağaza profilim</h1><a class="btn btn-ghost btn-sm" href="{{ url_for('storefront', username=me.username) }}">Herkese açık sayfa</a></div>
<div class="card mb">
  <div class="spread"><div><b>Mağaza adresin:</b> <span class="mono">{{ store_url(me) }}</span></div><div class="row"><button type="button" class="btn btn-ghost btn-sm" data-copy="{{ store_url(me) }}">Kopyala</button><a class="btn btn-sm" href="{{ url_for('seller.showcase') }}">Adresi ve vitrini düzenle</a></div></div>
</div>
<div class="card mb">
  <div class="store-head">
    {{ avatar(me.username, me.avatar, 'lg') }}
    <div style="flex:1;min-width:240px">
      <h2 style="margin-bottom:.2em">{{ me.store_name or me.username }}{{ pkg_marks(me.id) }}</h2>
      {{ badge_list(badges) }}
    </div>
  </div>
  <hr>
  <form method="post" action="{{ url_for('seller.store') }}" enctype="multipart/form-data" class="row">
    {{ csrf_field() }}<input type="hidden" name="action" value="avatar">
    <div class="field" style="flex:1;min-width:240px;margin:0"><label for="avatar">Mağaza profil fotoğrafı / logo</label><input type="file" id="avatar" name="avatar" accept="image/jpeg,image/png,image/webp" required></div>
    <button class="btn btn-sm" type="submit">Yükle</button>
  </form>
  {% if me.avatar %}<form method="post" action="{{ url_for('seller.store') }}" class="mt">{{ csrf_field() }}<input type="hidden" name="action" value="avatar_remove"><button class="link-btn link-danger" type="submit">Fotoğrafı kaldır</button></form>{% endif %}
</div>
<div class="card mb">
  <h3 class="mt0">Mağaza kapak görseli</h3>
  <p class="muted small">Mağaza sayfanın üstünde görünür. Geniş (4:1) bir görsel kullan; otomatik kırpılır.</p>
  {% if me.store_banner %}<img class="store-banner-prev" src="{{ url_for('media_cover', name=me.store_banner) }}" alt="">{% endif %}
  <form method="post" action="{{ url_for('seller.store') }}" enctype="multipart/form-data" class="row">
    {{ csrf_field() }}<input type="hidden" name="action" value="banner">
    <div class="field" style="flex:1;min-width:240px;margin:0"><input type="file" name="banner" accept="image/jpeg,image/png,image/webp" required aria-label="Kapak görseli"></div>
    <button class="btn btn-sm" type="submit">Yükle</button>
  </form>
  {% if me.store_banner %}<form method="post" action="{{ url_for('seller.store') }}" class="mt">{{ csrf_field() }}<input type="hidden" name="action" value="banner_remove"><button class="link-btn link-danger" type="submit">Kapak görselini kaldır</button></form>{% endif %}
</div>
<div class="card mb">
  <form method="post" action="{{ url_for('seller.store') }}"{% if name_fee %} data-fee-field="store_name" data-fee-confirm="Mağaza adını değiştirmek {{ name_fee|money }} tutarında ücretlidir ve bakiyenden düşülür. Onaylıyor musun?"{% endif %}>
    {{ csrf_field() }}<input type="hidden" name="action" value="store">
    <div class="field"><label for="store_name">Mağaza adı</label><input type="text" id="store_name" name="store_name" value="{{ me.store_name }}" required minlength="3" maxlength="40">{% if name_fee %}<div class="hint fee-note">Mağaza adını değiştirmek <b>{{ name_fee|money }}</b> ücretlidir ve bakiyenden düşülür. Açıklamayı değiştirmek ücretsizdir.</div>{% endif %}</div>
    <div class="field"><label for="store_desc">Mağaza açıklaması</label><textarea id="store_desc" name="store_desc" maxlength="500">{{ me.store_desc }}</textarea></div>
    <button class="btn" type="submit">Kaydet</button>
  </form>
</div>
<div class="card">
  <h3 class="mt0">Rozetler nasıl kazanılır?</h3>
  <ul class="muted">
    <li><b>Onaylı Satıcı</b>: satıcı başvurun onaylanınca otomatik verilir. <b>Kimliği Doğrulandı</b>: ilk para çekiminde kimlik bilgilerin onaylanınca eklenir.</li>
    <li><b>Güvenilir Satıcı</b>: en az {{ cfg.trusted_min_sales }} satış, en az 5 yorum ve {{ cfg.trusted_min_rating }} ve üzeri ortalama puan ile otomatik kazanılır.</li>
    <li><b>Mağaza Üyesi</b> ve <b>Yıldız Satıcı</b>: yönetim tarafından verilir.</li>
  </ul>
</div>
{% endblock %}
"""

TEMPLATES["seller_earnings.html"] = r"""
{% extends "seller_base.html" %}
{% from "_macros.html" import badge, empty, ic with context %}
{% block title %}Kazançlarım{% endblock %}
{% block panel %}
<div class="page-h"><h1>Kazançlarım</h1><a class="btn" href="{{ url_for('withdraw') }}">Para çek</a></div>
<div class="grid g4 mb">
  <div class="stat good"><div class="k">Çekilebilir</div><div class="v">{{ withdrawable|money }}</div><div class="s">Minimum çekim {{ min_w|money }}</div></div>
  <div class="stat"><div class="k">Emanette bekleyen</div><div class="v">{{ held.s|money }}</div><div class="s">{{ held.n }} sipariş</div></div>
  <div class="stat"><div class="k">Bekleyen çekim</div><div class="v">{{ wd.pending|money }}</div></div>
  <div class="stat"><div class="k">Toplam çekilen (net)</div><div class="v">{{ wd.paid|money }}</div><div class="s">Toplam net kazanç {{ lifetime|money }}</div></div>
</div>
{% if not kyc_ok %}<div class="notice warn">Para çekebilmek için kimlik doğrulaması gerekir. <a href="{{ url_for('kyc', devam='cekim') }}">Kimliğini doğrula</a></div>{% endif %}

<div class="card mb">
  <div class="card-h"><h3>Emanetteki siparişler</h3><span class="small muted">Alıcı onaylayınca ya da süre dolunca bakiyene geçer</span></div>
  {% if held_rows %}<div class="table-wrap"><table>
    <tr><th>No</th><th>Sipariş tarihi</th><th>İlan</th><th>Alıcı</th><th class="right">Net</th><th>Otomatik aktarım</th><th>Durum</th></tr>
    {% for o in held_rows %}<tr><td><a href="{{ url_for('order_detail', oid=o.id) }}">#{{ o.id }}</a></td><td class="nowrap">{{ o.created_at|dt }}</td><td>{{ o.listing_title[:38] }}</td><td>{{ o.buyer_name|mask }}</td><td class="right nowrap pos">{{ o.seller_earning|money }}</td><td class="nowrap">{{ o.release_at|dt if o.release_at else '-' }}</td><td>{{ badge(o.escrow_status) }}</td></tr>{% endfor %}
  </table></div>{% else %}{{ empty('Emanette bekleyen sipariş yok', 'Satışların alıcı onayından sonra hemen bakiyene geçer.') }}{% endif %}
</div>

<div class="card">
  <div class="card-h"><h3>Çekim geçmişi</h3><span class="small muted">İşlem kesintisi %{{ fee_rate }}</span></div>
  {% if history %}<div class="table-wrap"><table>
    <tr><th>No</th><th>Tarih</th><th>Yöntem</th><th class="right">Tutar</th><th class="right">Kesinti</th><th class="right">Ödenecek</th><th>Durum</th><th>Not</th></tr>
    {% for w in history %}<tr><td>#{{ w.id }}</td><td class="nowrap">{{ w.created_at|dt }}</td><td>{{ w.method }}</td><td class="right nowrap">{{ w.amount|money }}</td><td class="right nowrap muted">{{ w.fee|money }}</td><td class="right nowrap">{{ w.net|money }}</td><td>{{ badge(w.status) }}</td><td class="muted small">{{ w.admin_note }}</td></tr>{% endfor %}
  </table></div>{% else %}{{ empty('Henüz çekim talebin yok') }}{% endif %}
</div>
{% endblock %}
"""
