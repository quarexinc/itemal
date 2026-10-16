"""Admin paneli şablonları - 3. bölüm: arama, banner, kupon, rapor, duyuru, sistem (Jinja). Emoji kullanılmaz."""

TEMPLATES = {}

TEMPLATES["admin_search.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import badge, empty, ic with context %}
{% block heading %}Arama{% endblock %}
{% block panel %}
<div class="page-h"><div><div class="crumb">Global arama</div><h1>"{{ text }}" için {{ total }} sonuç</h1></div></div>
{% if not text %}<div class="card">{{ empty('Bir arama terimi gir', 'Kullanıcı adı, e-posta, ID, ilan başlığı, sipariş no, destek konusu veya IP arayabilirsin.') }}</div>{% endif %}
{% if res.users %}
<div class="res-h"><h3>{{ ic('users') }} Kullanıcılar</h3></div>
<div class="table-wrap"><table>
  {% for u in res.users %}<tr><td>#{{ u.id }}</td><td><a href="{{ url_for('admin.user', uid=u.id) }}"><b>{{ u.username }}</b></a>{{ pkg_marks(u.id) }}<div class="muted small">{{ u.email }}</div></td><td>{% if u.is_seller %}<span class="badge b-ok">Satıcı</span>{% endif %} {% if u.is_banned %}<span class="badge b-bad">Engelli</span>{% endif %}</td><td class="right nowrap">{{ u.balance|money }}</td></tr>{% endfor %}
</table></div>
{% endif %}
{% if res.listings %}
<div class="res-h"><h3>{{ ic('tag') }} İlanlar</h3></div>
<div class="table-wrap"><table>
  {% for l in res.listings %}<tr><td>#{{ l.id }}</td><td><a href="{{ url_for('admin.listing_edit', lid=l.id) }}"><b>{{ l.title[:60] }}</b></a><div class="muted small">{{ l.cat_name }} &middot; {{ l.seller_name }}{{ pkg_marks(l.seller_id) }}</div></td><td>{{ badge(l.status) }}</td><td class="right nowrap">{{ l.price|money }}</td></tr>{% endfor %}
</table></div>
{% endif %}
{% if res.orders %}
<div class="res-h"><h3>{{ ic('receipt') }} Siparişler</h3></div>
<div class="table-wrap"><table>
  {% for o in res.orders %}<tr><td>#{{ o.id }}</td><td>{{ o.listing_title[:50] }}<div class="muted small">{{ o.buyer_name }} - {{ o.seller_name }}{{ pkg_marks(o.seller_id) }}</div></td><td class="nowrap muted">{{ o.created_at|dt }}</td><td class="right nowrap">{{ o.total|money }}</td></tr>{% endfor %}
</table></div>
{% endif %}
{% if res.tickets %}
<div class="res-h"><h3>{{ ic('life-buoy') }} Destek talepleri</h3></div>
<div class="table-wrap"><table>
  {% for t in res.tickets %}<tr><td><a href="{{ url_for('admin.ticket', tid=t.id) }}">#{{ t.id }}</a></td><td>{{ t.subject[:60] }}<div class="muted small">{{ t.username }}</div></td><td><span class="badge b-{{ t.status|tclass }}">{{ t.status|tlabel }}</span></td></tr>{% endfor %}
</table></div>
{% endif %}
{% if res.deposits %}
<div class="res-h"><h3>{{ ic('download') }} Yüklemeler</h3></div>
<div class="table-wrap"><table>
  {% for d in res.deposits %}<tr><td>#{{ d.id }}</td><td>{{ d.username }}<div class="muted small">{{ d.reference[:60] }}</div></td><td>{{ badge(d.status) }}</td><td class="right nowrap">{{ d.amount|money }}</td></tr>{% endfor %}
</table></div>
{% endif %}
{% if text and not total %}<div class="card">{{ empty('Sonuç bulunamadı') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["admin_banners.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import empty, ic with context %}
{% block heading %}Bannerlar{% endblock %}
{% block panel %}
{% set f = edit if edit else form %}
<div class="notice">Doping ile satın alınan reklam bannerları <b>Reklam (satın alınan)</b> etiketiyle listelenir; kapatabilir ya da silebilirsin. Süreleri ve kapasite <a href="{{ url_for('admin.doping') }}">Doping</a> sayfasından izlenir.</div>
<div class="notice">Ana sayfada <b>Slider</b> konumu büyük kayan afişleri, <b>Reklam şeridi</b> konumu bölümlerin arasındaki geniş bantları gösterir. Görsel yüklemezsen renk geçişi kullanılır. Tıklama ve gösterim sayıları otomatik izlenir.</div>

<div class="card mb">
  <div class="card-h"><h3>{{ 'Banner düzenle #' ~ edit.id if edit else 'Yeni banner' }}</h3>{% if edit %}<a class="btn btn-ghost btn-sm" href="{{ url_for('admin.banners') }}">Yeni banner ekle</a>{% endif %}</div>
  <form method="post" enctype="multipart/form-data" action="{{ url_for('admin.banner_edit', bid=edit.id) if edit else url_for('admin.banners') }}">
    {{ csrf_field() }}
    <div class="form-row">
      <div class="field"><label for="slot">Konum</label><select id="slot" name="slot"><option value="hero" {{ 'selected' if f.slot == 'hero' }}>Slider (büyük)</option><option value="strip" {{ 'selected' if f.slot == 'strip' }}>Reklam şeridi</option></select></div>
      <div class="field"><label for="title">Başlık</label><input type="text" id="title" name="title" value="{{ f.title }}" required maxlength="70"></div>
    </div>
    <div class="form-row">
      <div class="field"><label for="subtitle">Alt metin</label><input type="text" id="subtitle" name="subtitle" value="{{ f.subtitle }}" maxlength="140"></div>
      <div class="field"><label for="cta_text">Düğme yazısı</label><input type="text" id="cta_text" name="cta_text" value="{{ f.cta_text }}" maxlength="30" placeholder="Örn. Hemen incele"></div>
    </div>
    <div class="form-row">
      <div class="field"><label for="link">Bağlantı</label><input type="text" id="link" name="link" value="{{ f.link }}" maxlength="300" placeholder="/ilanlar?kategori=discord"><div class="hint">Site içi yol ya da https:// ile başlayan adres.</div></div>
      <div class="field"><label for="sort_order">Sıra</label><input type="number" id="sort_order" name="sort_order" value="{{ f.sort_order or 0 }}"></div>
    </div>
    <div class="form-row">
      <div class="field"><label for="color1">Renk 1</label><div class="row" style="flex-wrap:nowrap"><input type="color" data-hex="#color1t" value="{{ f.color1 or '#7c5cff' }}" style="width:56px"><input type="text" id="color1t" name="color1" value="{{ f.color1 or '#7c5cff' }}" maxlength="7"></div></div>
      <div class="field"><label for="color2">Renk 2</label><div class="row" style="flex-wrap:nowrap"><input type="color" data-hex="#color2t" value="{{ f.color2 or '#1b1140' }}" style="width:56px"><input type="text" id="color2t" name="color2" value="{{ f.color2 or '#1b1140' }}" maxlength="7"></div></div>
    </div>
    <div class="form-row">
      <div class="field"><label for="starts_at">Başlangıç (isteğe bağlı, Türkiye saati)</label><input type="datetime-local" id="starts_at" name="starts_at" value="{{ (f.starts_at|local_input) if edit else (f.starts_at or '') }}"></div>
      <div class="field"><label for="ends_at">Bitiş (isteğe bağlı)</label><input type="datetime-local" id="ends_at" name="ends_at" value="{{ (f.ends_at|local_input) if edit else (f.ends_at or '') }}"></div>
    </div>
    <div class="field"><label for="image">Görsel (isteğe bağlı, yatay, en az 200 px)</label><input type="file" id="image" name="image" accept="image/jpeg,image/png,image/webp" data-preview="#ban-prev">
      <img id="ban-prev" class="preview-img" alt="Önizleme" {% if edit and edit.image %}src="{{ url_for('media_cover', name=edit.image) }}"{% else %}hidden{% endif %}>
      {% if edit and edit.image %}<label class="check mt"><input type="checkbox" name="remove_image" value="1"> Mevcut görseli kaldır</label>{% endif %}</div>
    <label class="check field"><input type="checkbox" name="is_active" value="1" {{ 'checked' if (edit.is_active if edit else (f.is_active if f else true)) }}> Yayında</label>
    <button class="btn" type="submit">{{ 'Kaydet' if edit else 'Banner ekle' }}</button>
  </form>
</div>

{% if rows %}
<div class="table-wrap"><table>
  <tr><th>Önizleme</th><th>Konum</th><th>Sıra</th><th>Zaman</th><th class="right">Gösterim</th><th class="right">Tıklama</th><th class="right">Oran</th><th>Durum</th><th></th></tr>
  {% for b in rows %}<tr>
    <td><div class="ban-prev" style="--c1:{{ b.color1 }};--c2:{{ b.color2 }}">{{ b.title[:28] }}</div></td>
    <td>{{ 'Slider' if b.slot == 'hero' else 'Şerit' }}{% if b.is_ad %}<br><span class="badge b-info" title="Doping ile satın alınan reklam; ilan: #{{ b.listing_id }}">Reklam (satın alınan)</span>{% if b.listing_id %}<div class="small"><a href="{{ url_for('listing_detail', lid=b.listing_id) }}">İlan #{{ b.listing_id }}</a></div>{% endif %}{% endif %}</td><td>{{ b.sort_order }}</td>
    <td class="small muted nowrap">{% if b.starts_at or b.ends_at %}{{ b.starts_at|dt if b.starts_at else '...' }}<br>{{ b.ends_at|dt if b.ends_at else '...' }}{% else %}Sürekli{% endif %}</td>
    <td class="right">{{ b.views }}</td><td class="right">{{ b.clicks }}</td><td class="right">{{ '%.1f'|format(b.clicks * 100 / b.views) if b.views else '-' }}{% if b.views %}%{% endif %}</td>
    <td><span class="badge b-{{ 'ok' if b.is_active else 'muted' }}">{{ 'Yayında' if b.is_active else 'Kapalı' }}</span></td>
    <td class="actions"><div class="mini-form">
      <a class="btn btn-ghost btn-sm" href="{{ url_for('admin.banner_edit', bid=b.id) }}">Düzenle</a>
      <form method="post" action="{{ url_for('admin.banner_action', bid=b.id) }}">{{ csrf_field() }}<input type="hidden" name="action" value="toggle"><button class="btn btn-line btn-sm" type="submit">{{ 'Kapat' if b.is_active else 'Aç' }}</button></form>
      <form method="post" action="{{ url_for('admin.banner_action', bid=b.id) }}" data-confirm="Banner silinsin mi?">{{ csrf_field() }}<input type="hidden" name="action" value="delete"><button class="btn btn-danger btn-sm" type="submit">Sil</button></form>
    </div></td>
  </tr>{% endfor %}
</table></div>
{% else %}<div class="card">{{ empty('Banner yok', 'Yukarıdaki formla ilk bannerını ekle.') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["admin_coupons.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import empty, ic with context %}
{% block heading %}Kuponlar{% endblock %}
{% block panel %}
<div class="grid g3 mb">
  <div class="stat"><div class="k">Kupon sayısı</div><div class="v">{{ rows|length }}</div></div>
  <div class="stat"><div class="k">Toplam kullanım</div><div class="v">{{ totals.n }}</div></div>
  <div class="stat hot"><div class="k">Verilen indirim</div><div class="v">{{ totals.given|money }}</div><div class="s">Platform karşılar; satıcı kazancı etkilenmez</div></div>
</div>

<div class="card mb">
  <h3 class="mt0">Yeni kupon</h3>
  <form method="post" action="{{ url_for('admin.coupons') }}">
    {{ csrf_field() }}
    <div class="form-row">
      <div class="field"><label for="code">Kod</label><input type="text" id="code" name="code" value="{{ form.code }}" required maxlength="30" placeholder="HOSGELDIN10" style="text-transform:uppercase"></div>
      <div class="field"><label for="kind">Tür</label><select id="kind" name="kind"><option value="percent" {{ 'selected' if form.kind == 'percent' }}>Yüzde (%)</option><option value="fixed" {{ 'selected' if form.kind == 'fixed' }}>Sabit tutar (TL)</option></select></div>
    </div>
    <div class="form-row">
      <div class="field"><label for="value">Değer</label><input type="text" inputmode="decimal" id="value" name="value" value="{{ form.value }}" required placeholder="10"><div class="hint">Yüzde için 1-90, sabit için TL.</div></div>
      <div class="field"><label for="category_id">Kategori (isteğe bağlı)</label><select id="category_id" name="category_id"><option value="">Tüm kategoriler</option>{% for c in cats %}<option value="{{ c.id }}" {{ 'selected' if form.category_id|string == c.id|string }}>{{ c.name }}</option>{% endfor %}</select></div>
    </div>
    <div class="form-row">
      <div class="field"><label for="min_total">Minimum tutar (TL)</label><input type="text" inputmode="decimal" id="min_total" name="min_total" value="{{ form.min_total }}" placeholder="0"></div>
      <div class="field"><label for="max_discount">En fazla indirim (TL, yüzdelik için)</label><input type="text" inputmode="decimal" id="max_discount" name="max_discount" value="{{ form.max_discount }}" placeholder="Sınırsız"></div>
    </div>
    <div class="form-row">
      <div class="field"><label for="max_uses">Toplam kullanım hakkı (0: sınırsız)</label><input type="number" id="max_uses" name="max_uses" min="0" value="{{ form.max_uses or 0 }}"></div>
      <div class="field"><label for="per_user">Kişi başı hak (0: sınırsız)</label><input type="number" id="per_user" name="per_user" min="0" value="{{ form.per_user or 1 }}"></div>
    </div>
    <div class="form-row">
      <div class="field"><label for="starts_at">Başlangıç (isteğe bağlı)</label><input type="datetime-local" id="starts_at" name="starts_at" value="{{ form.starts_at }}"></div>
      <div class="field"><label for="expires_at">Bitiş (isteğe bağlı)</label><input type="datetime-local" id="expires_at" name="expires_at" value="{{ form.expires_at }}"></div>
    </div>
    <label class="check field"><input type="checkbox" name="is_active" value="1" checked> Aktif</label>
    <button class="btn" type="submit">Kupon oluştur</button>
  </form>
</div>

{% if rows %}
<div class="table-wrap"><table>
  <tr><th>Kod</th><th>İndirim</th><th>Koşul</th><th class="right">Kullanım</th><th class="right">Verilen</th><th>Geçerlilik</th><th>Durum</th><th></th></tr>
  {% for c in rows %}{% set dead = (c.expires_at and c.expires_at < now) or (c.max_uses and c.used_count >= c.max_uses) %}<tr>
    <td><b class="mono">{{ c.code }}</b></td>
    <td>{% if c.kind == 'percent' %}%{{ '%g'|format(c.value) }}{% if c.max_discount %} <span class="muted small">(en fazla {{ c.max_discount|money }})</span>{% endif %}{% else %}{{ c.value|int|money }}{% endif %}</td>
    <td class="small muted">{% if c.min_total %}Min. {{ c.min_total|money }}<br>{% endif %}{{ c.cat_name or 'Tüm kategoriler' }}<br>Kişi başı: {{ c.per_user or 'sınırsız' }}</td>
    <td class="right">{{ c.used_count }}{% if c.max_uses %} / {{ c.max_uses }}{% endif %}</td>
    <td class="right nowrap">{{ c.given|money }}</td>
    <td class="small muted nowrap">{% if c.starts_at %}{{ c.starts_at|dt }}<br>{% endif %}{% if c.expires_at %}{{ c.expires_at|dt }}{% else %}Süresiz{% endif %}</td>
    <td>{% if dead %}<span class="badge b-bad">Bitti</span>{% else %}<span class="badge b-{{ 'ok' if c.is_active else 'muted' }}">{{ 'Aktif' if c.is_active else 'Kapalı' }}</span>{% endif %}</td>
    <td class="actions"><div class="mini-form">
      <form method="post" action="{{ url_for('admin.coupon_action', cid=c.id) }}">{{ csrf_field() }}<input type="hidden" name="action" value="toggle"><button class="btn btn-line btn-sm" type="submit">{{ 'Kapat' if c.is_active else 'Aç' }}</button></form>
      <form method="post" action="{{ url_for('admin.coupon_action', cid=c.id) }}" data-confirm="Kupon silinsin mi?">{{ csrf_field() }}<input type="hidden" name="action" value="delete"><button class="btn btn-danger btn-sm" type="submit">Sil</button></form>
    </div></td>
  </tr>{% endfor %}
</table></div>
{% else %}<div class="card">{{ empty('Kupon yok', 'Yukarıdaki formla ilk kuponunu oluştur.') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["admin_reports.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import bars, empty, ic, spark with context %}
{% block heading %}Raporlar{% endblock %}
{% block panel %}
<div class="page-h">
  <div class="seg">{% for d, label in ranges.items() %}<a class="{{ 'on' if d == days }}" href="{{ url_for('admin.reports', gun=d) }}">{{ label }}</a>{% endfor %}</div>
  <div class="row">
    <span class="small muted">Dışa aktar (CSV):</span>
    <a class="btn btn-ghost btn-sm" href="{{ url_for('admin.export', what='siparisler') }}">Siparişler</a>
    <a class="btn btn-ghost btn-sm" href="{{ url_for('admin.export', what='kullanicilar') }}">Kullanıcılar</a>
    <a class="btn btn-ghost btn-sm" href="{{ url_for('admin.export', what='yuklemeler') }}">Yüklemeler</a>
    <a class="btn btn-ghost btn-sm" href="{{ url_for('admin.export', what='cekimler') }}">Çekimler</a>
    <a class="btn btn-ghost btn-sm" href="{{ url_for('admin.export', what='ilanlar') }}">İlanlar</a>
  </div>
</div>

<div class="kpis mb">
  <div class="kpi"><div class="k">{{ ic('chart') }}Ciro</div><div class="v">{{ kpi.gmv|money }}</div><div class="s">{{ kpi.orders }} sipariş &middot; {{ kpi.qty }} adet</div>{{ spark(chart|map(attribute='value')|list) }}</div>
  <div class="kpi"><div class="k">{{ ic('percent') }}Komisyon</div><div class="v ok">{{ kpi.fee|money }}</div><div class="s">Ort. sepet {{ (kpi.gmv / kpi.orders)|int|money if kpi.orders else '-' }}</div></div>
  <div class="kpi"><div class="k">{{ ic('ticket') }}Kupon maliyeti</div><div class="v warn">{{ kpi.discount|money }}</div><div class="s">Net komisyon {{ (kpi.fee - kpi.discount)|money }} &middot; Doping geliri {{ mi.doping|money }}</div></div>
  <div class="kpi"><div class="k">{{ ic('users') }}Alıcı / yeni üye</div><div class="v">{{ kpi.buyers }} / {{ mi.new_users }}</div><div class="s">{{ mi.new_sellers }} yeni satıcı</div></div>
  <div class="kpi"><div class="k">{{ ic('download') }}Yüklemeler</div><div class="v">{{ mi.deposits|money }}</div><div class="s">Ödenen çekim {{ mi.payouts|money }}</div></div>
</div>

<div class="two-col mb">
  <div class="card"><div class="card-h"><h3>Günlük ciro</h3><span class="small muted">Son {{ span }} gün</span></div>{{ bars(chart, true) }}</div>
  <div class="card"><div class="card-h"><h3>Günlük sipariş</h3><span class="small muted">Son {{ span }} gün</span></div>{{ bars(chart_orders) }}</div>
</div>

<div class="two-col mb">
  <div class="card">
    <div class="card-h"><h3>Kategoriler</h3></div>
    {% if by_cat %}{% set peak = by_cat[0].gmv or 1 %}
    {% for c in by_cat %}<div class="hbar"><span>{{ c.name }}</span><div class="meter"><i style="width:{{ (c.gmv * 100 / peak)|round|int }}%;background:{{ c.color or '#7c5cff' }}"></i></div><b>{{ c.gmv|money }}</b></div>{% endfor %}
    {% else %}{{ empty('Bu aralıkta satış yok') }}{% endif %}
  </div>
  <div class="card">
    <div class="card-h"><h3>Ödeme yöntemleri (yüklemeler)</h3></div>
    {% if by_method %}<div class="table-wrap"><table>
      <tr><th>Yöntem</th><th class="right">Adet</th><th class="right">Tutar</th></tr>
      {% for m in by_method %}<tr><td>{{ m.name }}</td><td class="right">{{ m.n }}</td><td class="right nowrap">{{ m.total|money }}</td></tr>{% endfor %}
    </table></div>{% else %}{{ empty('Bu aralıkta yükleme yok') }}{% endif %}
  </div>
</div>

<div class="two-col mb">
  <div class="card">
    <div class="card-h"><h3>En çok satan satıcılar</h3></div>
    {% if top_sellers %}<div class="table-wrap"><table>
      <tr><th>Satıcı</th><th class="right">Sipariş</th><th class="right">Ciro</th><th class="right">Komisyon</th></tr>
      {% for s in top_sellers %}<tr><td><a href="{{ url_for('admin.user', uid=s.id) }}">{{ s.username }}</a>{{ pkg_marks(s.id) }}</td><td class="right">{{ s.orders }}</td><td class="right nowrap">{{ s.gmv|money }}</td><td class="right nowrap">{{ s.fee|money }}</td></tr>{% endfor %}
    </table></div>{% else %}{{ empty('Veri yok') }}{% endif %}
  </div>
  <div class="card">
    <div class="card-h"><h3>En çok harcayan alıcılar</h3></div>
    {% if top_buyers %}<div class="table-wrap"><table>
      <tr><th>Alıcı</th><th class="right">Sipariş</th><th class="right">Harcama</th></tr>
      {% for s in top_buyers %}<tr><td><a href="{{ url_for('admin.user', uid=s.id) }}">{{ s.username }}</a></td><td class="right">{{ s.orders }}</td><td class="right nowrap">{{ s.spent|money }}</td></tr>{% endfor %}
    </table></div>{% else %}{{ empty('Veri yok') }}{% endif %}
  </div>
</div>

<div class="two-col">
  <div class="card">
    <div class="card-h"><h3>En çok satan ilanlar</h3></div>
    {% if top_listings %}<div class="table-wrap"><table>
      <tr><th>İlan</th><th class="right">Adet</th><th class="right">Ciro</th></tr>
      {% for l in top_listings %}<tr><td>{{ l.listing_title[:44] }}</td><td class="right">{{ l.qty }}</td><td class="right nowrap">{{ l.gmv|money }}</td></tr>{% endfor %}
    </table></div>{% else %}{{ empty('Veri yok') }}{% endif %}
  </div>
  <div class="card">
    <div class="card-h"><h3>Kupon ve banner performansı</h3></div>
    {% if coupon_rows %}<div class="table-wrap mb"><table>
      <tr><th>Kupon</th><th class="right">Kullanım</th><th class="right">İndirim</th></tr>
      {% for c in coupon_rows %}<tr><td class="mono">{{ c.code }}</td><td class="right">{{ c.n }}</td><td class="right nowrap">{{ c.given|money }}</td></tr>{% endfor %}
    </table></div>{% endif %}
    {% if banner_rows %}<div class="table-wrap"><table>
      <tr><th>Banner</th><th class="right">Gösterim</th><th class="right">Tıklama</th></tr>
      {% for b in banner_rows %}<tr><td>{{ b.title[:32] }}</td><td class="right">{{ b.views }}</td><td class="right">{{ b.clicks }}</td></tr>{% endfor %}
    </table></div>{% elif not coupon_rows %}{{ empty('Veri yok') }}{% endif %}
  </div>
</div>
{% endblock %}
"""

TEMPLATES["admin_broadcast.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import empty, ic with context %}
{% block heading %}Duyuru gönder{% endblock %}
{% block panel %}
<div class="two-col">
  <div class="card">
    <h3 class="mt0">Uygulama içi bildirim</h3>
    <p class="muted">Bildirim, kullanıcının üst menüdeki çan simgesinde ve Bildirimler sayfasında görünür.</p>
    <form method="post" action="{{ url_for('admin.broadcast') }}" data-confirm="Bildirim gönderilsin mi?">
      {{ csrf_field() }}
      <div class="field"><label for="audience">Hedef kitle</label>
        <select id="audience" name="audience">
          <option value="all" {{ 'selected' if form.audience == 'all' }}>Tüm kullanıcılar ({{ counts.everyone }})</option>
          <option value="sellers" {{ 'selected' if form.audience == 'sellers' }}>Yalnızca satıcılar ({{ counts.sellers }})</option>
          <option value="buyers" {{ 'selected' if form.audience == 'buyers' }}>Alışveriş yapmış alıcılar ({{ counts.buyers }})</option>
          <option value="user" {{ 'selected' if form.audience == 'user' }}>Tek kullanıcı</option>
        </select></div>
      <div class="field"><label for="username">Kullanıcı adı (tek kullanıcı seçtiysen)</label><input type="text" id="username" name="username" value="{{ form.username }}" maxlength="30"></div>
      <div class="field"><label for="title">Başlık</label><input type="text" id="title" name="title" value="{{ form.title }}" required maxlength="100"></div>
      <div class="field"><label for="body">Metin</label><textarea id="body" name="body" maxlength="280" style="min-height:90px">{{ form.body }}</textarea></div>
      <div class="field"><label for="link">Bağlantı (isteğe bağlı)</label><input type="text" id="link" name="link" value="{{ form.link }}" maxlength="200" placeholder="/ilanlar?kategori=discord"></div>
      <button class="btn" type="submit">{{ ic('send') }}Gönder</button>
    </form>
  </div>
  <div class="card">
    <h3 class="mt0">Son gönderimler</h3>
    {% if history %}<div class="table-wrap"><table>
      {% for h in history %}<tr><td>{{ h.detail[:80] }}</td><td class="nowrap muted small right">{{ h.created_at|dt }}</td></tr>{% endfor %}
    </table></div>{% else %}{{ empty('Henüz duyuru gönderilmedi') }}{% endif %}
    <p class="muted small mt">Sitenin en üstündeki duyuru çubuğu için <a href="{{ url_for('admin.site_settings') }}">Site ayarları</a> sayfasındaki Duyuru alanını kullan.</p>
  </div>
</div>
{% endblock %}
"""

TEMPLATES["admin_system.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import ic with context %}
{% block heading %}Sistem ve araçlar{% endblock %}
{% block panel %}
<div class="grid g4 mb">
  <div class="stat"><div class="k">Veritabanı</div><div class="v">{{ db_size }}</div></div>
  <div class="stat"><div class="k">Yüklenen görseller</div><div class="v">{{ up_size }}</div></div>
  <div class="stat"><div class="k">Kullanıcı / ilan</div><div class="v">{{ tables.users }} / {{ tables.listings }}</div></div>
  <div class="stat"><div class="k">Son yedek</div><div class="v" style="font-size:1.05rem">{{ last_backup|dt if last_backup else 'Alınmadı' }}</div></div>
</div>

<div class="two-col mb">
  <div class="card">
    <h3 class="mt0">Sağlık kontrolü</h3>
    {% for c in checks %}<div class="sys-row {{ 'ok' if c.ok else 'bad' }}">{{ ic('check-circle' if c.ok else 'alert') }}<div>{{ c.title }}{% if not c.ok %}<small>{{ c.hint }}</small>{% endif %}</div></div>{% endfor %}
  </div>
  <div class="card">
    <h3 class="mt0">Ortam</h3>
    <dl class="kv">{% for k, v in info.items() %}<dt>{{ k }}</dt><dd class="small">{{ v }}</dd>{% endfor %}</dl>
    <hr>
    <h3>Kayıt sayıları</h3>
    <dl class="kv">{% for k, v in tables.items() %}<dt>{{ k }}</dt><dd>{{ v }}</dd>{% endfor %}</dl>
  </div>
</div>

<div class="two-col">
  <div class="card">
    <h3 class="mt0">Veritabanı yedeği</h3>
    <p class="muted">Tüm veritabanının anlık kopyasını indirir. Kullanıcı bilgileri ve kimlik verileri içerir; güvenli bir yerde sakla, kimseyle paylaşma. Yüklenen görseller <code class="inline">uploads/</code> klasöründedir, onu da ayrıca yedekle.</p>
    <form method="post" action="{{ url_for('admin.backup') }}" data-confirm="Yedek indirilsin mi? Dosya kişisel veriler içerir.">{{ csrf_field() }}<button class="btn" type="submit">{{ ic('download') }}Yedeği indir</button></form>
  </div>
  <div class="card">
    <h3 class="mt0">Demo veri</h3>
    <p class="muted">Vitrini önizlemek için 30+ örnek mağaza, 60 kadar kapak görselli ilan ve örnek yorumlar ekler (mağaza başına en fazla 2 ilan, 10 yorum, 300 satış). Demo ilanlar satın alınabilir: alıcıya örnek kod teslim edilir, stok kendiliğinden yenilenir ve demo mağazaların kazancı çekilemez. Tek tıkla silinir. Bunlar önizleme içindir: canlıda gerçek alıcıdan para almadan önce satışı kapat ya da demo veriyi sil.</p>
    {% if demo_loaded %}
      <p><span class="badge b-warn">Yüklü</span> {{ demo_counts.listings }} ilan, {{ demo_counts.sellers }} mağaza, {{ demo_counts.reviews }} yorum</p>
      <p>Demo ilan satışı: <span class="badge b-{{ 'ok' if demo_sales else 'muted' }}">{{ 'Açık' if demo_sales else 'Kapalı' }}</span></p>
      <div class="row">
        <form method="post" action="{{ url_for('admin.demo_action') }}">{{ csrf_field() }}<input type="hidden" name="action" value="{{ 'sales_off' if demo_sales else 'sales_on' }}"><button class="btn btn-line" type="submit">{{ 'Demo satışını kapat' if demo_sales else 'Demo satışını aç' }}</button></form>
        <form method="post" action="{{ url_for('admin.demo_action') }}" data-confirm="Tüm demo veri silinsin mi?">{{ csrf_field() }}<input type="hidden" name="action" value="clear"><button class="btn btn-danger" type="submit">{{ ic('trash') }}Demo veriyi sil</button></form>
      </div>
    {% else %}
      <form method="post" action="{{ url_for('admin.demo_action') }}" data-confirm="Demo veri yüklensin mi? İşlem birkaç saniye sürebilir.">{{ csrf_field() }}<input type="hidden" name="action" value="load"><button class="btn" type="submit">{{ ic('plus') }}Demo veri yükle</button></form>
    {% endif %}
  </div>
</div>
{% endblock %}
"""


TEMPLATES["admin_2fa.html"] = r"""
{% extends "admin_authbase.html" %}
{% block heading %}İki adımlı doğrulama{% endblock %}
{% block panel %}
<p class="muted" style="margin-top:0">Authenticator uygulamandaki 6 haneli kodu gir. Telefonuna erişemiyorsan yedek kodlardan birini yaz.</p>
<form method="post" action="{{ url_for('admin.verify') }}" autocomplete="off">
  {{ csrf_field() }}
  <div class="field"><label for="code">Doğrulama kodu</label><input class="tf-input" type="text" id="code" name="code" required autofocus autocomplete="one-time-code" inputmode="text" maxlength="16" spellcheck="false" placeholder="000000"></div>
  <button class="btn btn-block" type="submit">Doğrula</button>
</form>
<p class="small muted" style="margin:14px 0 8px">Bu adımı yaklaşık {{ minutes_left }} dakika içinde tamamla; aksi halde yeniden giriş yapman gerekir.</p>
<form class="inline-form" method="post" action="{{ url_for('admin.logout') }}">{{ csrf_field() }}<button class="btn btn-ghost btn-sm" type="submit">Vazgeç</button></form>
{% endblock %}
"""

TEMPLATES["admin_2fa_setup.html"] = r"""
{% extends layout %}
{% from "_macros.html" import ic with context %}
{% block heading %}İki adımlı doğrulama{% if not done %} kurulumu{% endif %}{% endblock %}
{% block wrap_class %} wide{% endblock %}
{% block panel %}
{% if done %}
  <div class="notice ok">İki adımlı doğrulama etkinleştirildi.</div>
  <h3 style="margin:0 0 6px">Yedek kodların</h3>
  <p class="muted" style="margin-top:0">Telefonuna erişemezsen bu kodlarla giriş yapabilirsin. Her kod yalnızca bir kez çalışır. <b>Bu kodlar bir daha gösterilmeyecek</b>; şimdi güvenli bir yere kaydet.</p>
  <div class="code-grid" id="backup-codes">{% for c in codes %}<code>{{ c }}</code>{% endfor %}</div>
  <div class="row" style="margin-top:16px">
    <button class="btn btn-line btn-sm" type="button" data-copy="#backup-codes code">{{ ic('copy') }}Kodları kopyala</button>
    <a class="btn btn-sm" href="{{ nxt or url_for('admin.dashboard') }}">Panele geç</a>
  </div>
{% else %}
  <p class="muted" style="margin-top:0">{% if full %}Yönetici hesabına ikinci bir doğrulama adımı eklenir.{% else %}Yönetici girişi için iki adımlı doğrulama zorunlu. Devam etmek için bir kez kurman gerekiyor.{% endif %}</p>
  <div class="tf-setup">
    {% if qr %}<div class="tf-qr" role="img" aria-label="Authenticator QR kodu">{{ qr }}</div>{% endif %}
    <div>
      <ol class="tf-steps">
        <li>Telefonunda bir authenticator uygulaması aç (Google Authenticator, Microsoft Authenticator, Aegis, 1Password vb.).</li>
        <li>{% if qr %}QR kodu tara ya da{% endif %} aşağıdaki anahtarı elle gir (zaman tabanlı, 6 hane).</li>
        <li>Uygulamada görünen 6 haneli kodu aşağıya yaz.</li>
      </ol>
      <div class="tf-key" id="tf-key">{{ secret_fmt }}</div>
      <button class="btn btn-ghost btn-sm" type="button" data-copy="{{ secret }}">{{ ic('copy') }}Anahtarı kopyala</button>
    </div>
  </div>
  <form method="post" action="{{ url_for('admin.setup') }}" autocomplete="off" style="margin-top:18px">
    {{ csrf_field() }}
    {% if full %}<div class="field"><label for="password">Yönetici şifren</label><input type="password" id="password" name="password" required autocomplete="current-password"></div>{% endif %}
    <div class="field"><label for="code">Uygulamadaki 6 haneli kod</label><input class="tf-input" type="text" id="code" name="code" required {% if not full %}autofocus{% endif %} autocomplete="one-time-code" inputmode="numeric" maxlength="8" pattern="[0-9 ]*" placeholder="000000"></div>
    <button class="btn btn-block" type="submit">Doğrula ve etkinleştir</button>
  </form>
  {% if not full %}<div style="margin-top:12px"><form class="inline-form" method="post" action="{{ url_for('admin.logout') }}">{{ csrf_field() }}<button class="btn btn-ghost btn-sm" type="submit">Vazgeç</button></form></div>{% endif %}
{% endif %}
{% endblock %}
"""

TEMPLATES["admin_security.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import ic with context %}
{% block heading %}Güvenlik{% endblock %}
{% block panel %}
{% if mode == 'off' %}<div class="notice warn">Acil durum bayrağı açık (ADMIN_2FA=off): yönetici girişi iki adımlı doğrulama olmadan, yalnızca şifreyle yapılıyor. Sorun giderildikten sonra .env içinden ADMIN_2FA satırını kaldır.</div>{% endif %}
{% if new_codes %}
<div class="card mb">
  <div class="card-h"><h3>Yeni yedek kodların</h3></div>
  <p class="muted" style="margin-top:0">Eski kodların hepsi geçersiz oldu. Her kod yalnızca bir kez çalışır ve <b>bir daha gösterilmeyecek</b>.</p>
  <div class="code-grid" id="backup-codes">{% for c in new_codes %}<code>{{ c }}</code>{% endfor %}</div>
  <div class="row" style="margin-top:14px"><button class="btn btn-line btn-sm" type="button" data-copy="#backup-codes code">{{ ic('copy') }}Kodları kopyala</button></div>
</div>
{% endif %}

<div class="two-col mb">
  <div class="card">
    <div class="card-h"><h3>İki adımlı doğrulama</h3>{% if enabled %}<span class="badge b-ok">Etkin</span>{% elif mode == 'off' %}<span class="badge b-muted">Devre dışı (ADMIN_2FA=off)</span>{% else %}<span class="badge b-warn">Kurulu değil</span>{% endif %}</div>
    {% if enabled %}
      <p class="muted" style="margin-top:0">Etkinleştirilme: {{ since|dt }}. Kalan yedek kod: <b>{{ left }}</b>{% if left <= 3 %} &middot; azalıyor, yenilerini üret{% endif %}</p>
      <details class="mb"><summary>Yedek kodları yeniden üret</summary>
        <form method="post" action="{{ url_for('admin.backup_regenerate') }}" autocomplete="off" style="margin-top:10px">{{ csrf_field() }}
          <div class="field"><label for="p1">Yönetici şifren</label><input type="password" id="p1" name="password" required autocomplete="current-password"></div>
          <div class="field"><label for="c1">Güncel doğrulama kodu</label><input class="tf-input" type="text" id="c1" name="code" required inputmode="numeric" maxlength="8" autocomplete="one-time-code" placeholder="000000"></div>
          <button class="btn btn-line" type="submit">Yeni 10 kod üret</button>
        </form>
      </details>
      {% if mode == 'required' %}
        <p class="small muted">Yönetici girişi için iki adımlı doğrulama zorunlu (ADMIN_2FA=required); kapatılamaz.</p>
      {% else %}
      <details><summary>İki adımlı doğrulamayı kapat</summary>
        <form method="post" action="{{ url_for('admin.tfa_disable') }}" autocomplete="off" data-confirm="İki adımlı doğrulama kapatılsın mı? Hesabın yalnızca şifreyle korunur." style="margin-top:10px">{{ csrf_field() }}
          <div class="field"><label for="p2">Yönetici şifren</label><input type="password" id="p2" name="password" required autocomplete="current-password"></div>
          <div class="field"><label for="c2">Güncel doğrulama kodu</label><input class="tf-input" type="text" id="c2" name="code" required inputmode="numeric" maxlength="8" autocomplete="one-time-code" placeholder="000000"></div>
          <button class="btn btn-danger" type="submit">Kapat</button>
        </form>
      </details>
      {% endif %}
    {% else %}
      <p class="muted" style="margin-top:0">{% if mode == 'off' %}Acil durum bayrağı açık: ADMIN_2FA=off olduğu için giriş yalnızca şifreyle yapılıyor. Normale dönmek için .env içinde ADMIN_2FA değerini kaldır.{% else %}Giriş şifreye ek olarak telefondaki bir kodla korunur.{% endif %}</p>
      {% if mode != 'off' %}<a class="btn" href="{{ url_for('admin.setup') }}">{{ ic('shield-check') }}Etkinleştir</a>{% endif %}
    {% endif %}
  </div>

  <div class="card">
    <div class="card-h"><h3>Oturum ve erişim</h3></div>
    <div class="table-wrap"><table>
      <tr><td>Bosta kalma zaman aşımı</td><td class="right">{{ info.idle_min }} dk (kalan ~{{ info.idle_left }} dk)</td></tr>
      <tr><td>Mutlak oturum süresi</td><td class="right">{{ info.abs_hours }} saat (kalan ~{{ info.abs_left // 60 }} sa {{ info.abs_left % 60 }} dk)</td></tr>
      <tr><td>Oturum tarayıcıya bağlı</td><td class="right"><span class="badge b-ok">Evet</span></td></tr>
      <tr><td>Oturum ağa (/24) bağlı</td><td class="right">{% if info.bind_ip %}<span class="badge b-ok">Evet</span>{% else %}<span class="badge b-muted">Hayır (ADMIN_BIND_IP=1)</span>{% endif %}</td></tr>
      <tr><td>IP izin listesi</td><td class="right">{% if info.allow_count %}<span class="badge b-ok">{{ info.allow_count }} kayıt</span>{% else %}<span class="badge b-muted">Kapalı (ADMIN_ALLOWED_IPS)</span>{% endif %}</td></tr>
      <tr><td>Yönetim yolu</td><td class="right">{% if info.custom_prefix %}<span class="badge b-ok">Özel</span>{% else %}<span class="badge b-muted">Varsayılan (ADMIN_URL_PREFIX)</span>{% endif %}</td></tr>
      <tr><td>İki adımlı doğrulama modu</td><td class="right"><code>{{ info.mode }}</code></td></tr>
      <tr><td>Hatalı giriş kilidi</td><td class="right">5 hata: 15 dk, sonra 1 saat, sonra 24 saat</td></tr>
      <tr><td>Şu anki IP</td><td class="right">{{ info.your_ip }}</td></tr>
    </table></div>
  </div>
</div>

<div class="card">
  <div class="card-h"><h3>Son yönetici girişleri</h3><span class="small muted">En son 30 olay &middot; IP adresleri maskelenir</span></div>
  {% if events %}<div class="table-wrap"><table>
    <tr><th>Zaman</th><th>IP</th><th>Tarayıcı</th><th>Sonuç</th></tr>
    {% for e in events %}<tr><td class="nowrap">{{ e.at|dt }}</td><td class="nowrap">{{ e.ip }}</td><td>{{ e.browser }}</td><td><span class="badge b-{{ e.cls }}">{{ e.label }}</span>{% if e.detail %}<div class="muted small">{{ e.detail }}</div>{% endif %}</td></tr>{% endfor %}
  </table></div>{% else %}<p class="muted">Henüz kayıt yok.</p>{% endif %}
</div>
{% endblock %}
"""
