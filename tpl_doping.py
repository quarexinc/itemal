"""Doping (ilan öne çıkarma) şablonları (Jinja). Emoji kullanılmaz."""

TEMPLATES = {}

TEMPLATES["_doping.html"] = r"""
{% macro doping_picker(kinds, sel, balance, key) %}
<fieldset class="doping" data-doping data-balance="{{ balance }}">
  <legend>Doping (isteğe bağlı)</legend>
  <p class="muted small dp-lead">İlanını öne çıkar: vitrinlerde ve ana sayfa reklam panosunda göster. Tutar yayınlama anında bakiyenden düşer; bakiye yetmezse ilan oluşturulmaz.</p>
  <input type="hidden" name="req_key" value="{{ key }}">
  {% for k in kinds %}
  <div class="dp-kind">
    <div class="dp-h"><b>{{ k.label }}</b><span class="muted small">{{ k.desc }}</span></div>
    {% if k.options %}
    <div class="dp-opts" role="radiogroup" aria-label="{{ k.label }} süresi">
      <label class="dp-opt"><input type="radio" name="doping_{{ k.key }}" value="" data-price="0" {{ 'checked' if not sel[k.key] }}><span><b>Yok</b><small>Doping alma</small></span></label>
      {% for o in k.options %}<label class="dp-opt"><input type="radio" name="doping_{{ k.key }}" value="{{ o.hours }}" data-price="{{ o.price }}" {{ 'checked' if sel[k.key] == o.hours }}><span><b>{{ o.label }}</b><small>{{ o.price|money }}</small></span></label>{% endfor %}
    </div>
    {% else %}<div class="muted small">Bu doping türü şu an satışta değil.</div>{% endif %}
  </div>
  {% endfor %}
  <div class="dp-sum">
    <div><small>Toplam doping tutarı</small><b data-doping-total>0,00 ₺</b></div>
    <div><small>Mevcut bakiyen</small><b>{{ balance|money }}</b></div>
    <div><small>Sonra kalan</small><b data-doping-left>{{ balance|money }}</b></div>
  </div>
  <div class="notice warn dp-warn" data-doping-warn hidden>Bakiyen bu doping tutarına yetmiyor. <a href="{{ url_for('balance') }}">Bakiye yükle</a> ya da seçimini küçült; yetersiz bakiyede ilan oluşturulmaz.</div>
</fieldset>
{% endmacro %}
"""

TEMPLATES["seller_doping.html"] = r"""
{% extends "seller_base.html" %}
{% from "_macros.html" import badge, empty, ic with context %}
{% block title %}Doping{% endblock %}
{% block panel %}
<div class="page-h"><h1>Doping</h1><a class="btn btn-ghost btn-sm" href="{{ url_for('seller.listings') }}">İlanlarım</a></div>
<div class="notice">Dopingle ilanını vitrinlerde ve ana sayfa reklam panosunda öne çıkar. Ödeme bakiyenden yapılır; aynı türü süresi dolmadan tekrar alırsan süre mevcut bitişin üzerine eklenir.</div>

<div class="grid g4 mb">
  <div class="stat"><div class="k">Bakiyen</div><div class="v">{{ me.balance|money }}</div><div class="s"><a href="{{ url_for('balance') }}">Bakiye yükle</a></div></div>
  <div class="stat"><div class="k">Aktif doping</div><div class="v">{{ active|length }}</div><div class="s">ilan + tür sayısı</div></div>
  <div class="stat"><div class="k">Toplam harcama</div><div class="v">{{ total_spent|money }}</div></div>
  <div class="stat {{ 'hot' if banner_used >= banner_max }}"><div class="k">Reklam panosu</div><div class="v">{{ banner_used }} / {{ banner_max }}</div><div class="s">{% if banner_used >= banner_max and banner_first_end %}En erken {{ banner_first_end|dt }} boşalır{% else %}dolu pano sayısı{% endif %}</div></div>
</div>

<div class="card mb">
  <div class="card-h"><h3>Doping türleri ve fiyatlar</h3></div>
  <div class="dp-price-grid">
    {% for k in kinds %}
    <div class="dp-price">
      <b>{{ k.label }}</b>
      <p class="muted small">{{ k.desc }}</p>
      <ul>{% for o in k.options %}<li><span>{{ o.label }}</span><b>{{ o.price|money }}</b></li>{% endfor %}</ul>
    </div>
    {% endfor %}
  </div>
</div>

<div class="card mb">
  <div class="card-h"><h3>Aktif dopinglerim</h3></div>
  {% if active %}
  <div class="table-wrap"><table>
    <tr><th>İlan</th><th>Doping</th><th>Durum</th><th>Bitiş</th><th></th></tr>
    {% for a in active %}<tr>
      <td><a href="{{ url_for('listing_detail', lid=a.listing_id) }}"><b>{{ a.title[:52] }}</b></a></td>
      <td><span class="dp-tag dp-{{ a.kind }}">{{ ic('flame') }}{{ a.label }}</span></td>
      <td>{% if a.live %}<span class="badge b-ok">Yayında</span>{% else %}<span class="badge b-muted">Sırada</span>{% endif %}{% if a.status != 'active' %} <span class="badge b-warn" title="İlan yayında olmadığı için doping gösterilmiyor">İlan {{ a.status|slabel|lower }}</span>{% endif %}</td>
      <td class="nowrap">{{ a.ends_at|dt }}<div class="muted small">{{ a.ends_at|ago }}</div></td>
      <td class="actions">{% if a.status == 'active' %}<a class="btn btn-line btn-sm" href="{{ url_for('seller.doping_buy', lid=a.listing_id) }}">Süre ekle</a>{% endif %}</td>
    </tr>{% endfor %}
  </table></div>
  {% else %}{{ empty('Aktif dopingin yok', 'Aşağıdan bir ilan seçip doping satın alabilirsin.') }}{% endif %}
</div>

<div class="card mb">
  <div class="card-h"><h3>İlan seç</h3></div>
  {% if listings %}
  <div class="table-wrap"><table>
    <tr><th>İlan</th><th class="right">Stok</th><th>Durum</th><th>Doping</th><th></th></tr>
    {% for l in listings %}<tr>
      <td><div class="row" style="flex-wrap:nowrap"><div class="thumb">{% if l.cover %}<img src="{{ cover_url(l.cover, true) }}" alt="">{% endif %}</div><div><a href="{{ url_for('listing_detail', lid=l.id) }}"><b>{{ l.title[:52] }}</b></a><div class="muted small">{{ l.cat_name }}</div></div></div></td>
      <td class="right"><span class="badge b-{{ 'bad' if l.stock == 0 else ('warn' if l.stock < 5 else 'ok') }}">{{ 'Tükendi' if l.stock == 0 else l.stock }}</span></td>
      <td>{{ badge(l.status) }}</td>
      <td>{% if l.dp %}<div class="dp-tags">{% for d in l.dp %}<span class="dp-tag dp-{{ d.kind }}" title="Bitiş {{ d.ends_at|dt }}">{{ ic('flame') }}{{ d.label }}</span>{% endfor %}</div>{% else %}<span class="muted small">Yok</span>{% endif %}</td>
      <td class="actions">{% if l.status == 'active' and l.stock > 0 %}<a class="btn btn-dp btn-sm" href="{{ url_for('seller.doping_buy', lid=l.id) }}">{{ ic('flame') }}Doping al</a>{% else %}<span class="muted small">{{ 'Stok ekle' if l.status == 'active' else 'Yayında değil' }}</span>{% endif %}</td>
    </tr>{% endfor %}
  </table></div>
  {% else %}{{ empty('Henüz ilanın yok', 'Doping almak için önce bir ilan yayınla.') }}<div class="mt"><a class="btn" href="{{ url_for('seller.listing_new') }}">Yeni ilan</a></div>{% endif %}
</div>

{% if history %}
<div class="card">
  <div class="card-h"><h3>Son satın almalar</h3></div>
  <div class="table-wrap"><table>
    <tr><th>Tarih</th><th>İlan</th><th>Doping</th><th>Süre</th><th class="right">Tutar</th></tr>
    {% for h in history %}<tr>
      <td class="nowrap">{{ h.created_at|dt }}</td>
      <td>{{ h.title[:48] }}</td>
      <td>{{ h.label }}</td>
      <td>{{ h.hours_label }}</td>
      <td class="right nowrap">{{ h.price|money }}</td>
    </tr>{% endfor %}
  </table></div>
</div>
{% endif %}
{% endblock %}
"""

TEMPLATES["seller_doping_buy.html"] = r"""
{% extends "seller_base.html" %}
{% from "_macros.html" import ic with context %}
{% from "_doping.html" import doping_picker with context %}
{% block title %}Doping al{% endblock %}
{% block panel %}
<div class="page-h"><h1>Doping al</h1><a class="btn btn-ghost btn-sm" href="{{ url_for('seller.doping') }}">Doping özeti</a></div>
<div class="card mb">
  <div class="row" style="flex-wrap:nowrap">
    <div class="thumb">{% if item.cover %}<img src="{{ cover_url(item.cover, true) }}" alt="">{% endif %}</div>
    <div><a href="{{ url_for('listing_detail', lid=item.id) }}"><b>{{ item.title }}</b></a>
      <div class="muted small">İlan #{{ item.id }} &middot; {{ item.price|money }}</div>
      {% if active_dp %}<div class="dp-tags mt">{% for d in active_dp %}<span class="dp-tag dp-{{ d.kind }}">{{ ic('flame') }}{{ d.label }} <small>bitiş {{ d.ends_at|dt }}</small></span>{% endfor %}</div>{% endif %}
    </div>
  </div>
</div>
{% if blocked %}
<div class="notice warn">{{ blocked }}</div>
<a class="btn btn-ghost" href="{{ url_for('seller.listings') }}">İlanlarıma dön</a>
{% else %}
<div class="card">
  <form method="post" action="{{ url_for('seller.doping_buy', lid=item.id) }}">
    {{ csrf_field() }}
    {{ doping_picker(doping, dsel, balance, dkey) }}
    {% if active_dp %}<div class="hint mb">Süresi devam eden bir dopingi yeniden seçersen, yeni süre mevcut bitişin üzerine eklenir.</div>{% endif %}
    <button class="btn" type="submit">{{ ic('flame') }} Satın al</button>
    <a class="btn btn-ghost" href="{{ url_for('seller.doping') }}">Vazgeç</a>
  </form>
</div>
{% endif %}
{% endblock %}
"""

TEMPLATES["admin_doping.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import empty, ic with context %}
{% block title %}Doping{% endblock %}
{% block heading %}Doping{% endblock %}
{% block panel %}
<div class="notice">Doping, satıcıların ilanlarını bakiyeleriyle öne çıkarmasını sağlar. Gelir platformundur (satıcı komisyonu değildir) ve <a href="{{ url_for('admin.commission') }}">komisyon raporunda</a> ayrıca gösterilir. Fiyat değişikliği yalnızca sonraki satın almalara uygulanır.</div>

<div class="grid g4 mb">
  <div class="stat good"><div class="k">Toplam doping geliri</div><div class="v">{{ totals.revenue|money }}</div><div class="s">{{ totals.n }} satın alma</div></div>
  <div class="stat"><div class="k">Son 7 gün</div><div class="v">{{ totals.week|money }}</div></div>
  <div class="stat"><div class="k">Son 30 gün</div><div class="v">{{ totals.month|money }}</div></div>
  <div class="stat {{ 'hot' if banner_used >= banner_max }}"><div class="k">Reklam panosu</div><div class="v">{{ banner_used }} / {{ banner_max }}</div><div class="s">{% if banner_used >= banner_max and banner_first_end %}En erken {{ banner_first_end|dt }} boşalır{% else %}aktif reklam / kapasite{% endif %}</div></div>
</div>

<div class="card mb">
  <div class="card-h"><h3>Türlere göre</h3></div>
  <div class="table-wrap"><table>
    <tr><th>Doping</th><th class="right">Aktif ilan</th><th class="right">Satın alma</th><th class="right">Gelir</th></tr>
    {% for k in by_kind %}<tr><td>{{ k.label }}</td><td class="right">{{ k.active }}</td><td class="right">{{ k.n }}</td><td class="right nowrap">{{ k.revenue|money }}</td></tr>{% endfor %}
  </table></div>
</div>

<div class="card mb">
  <div class="card-h"><h3>Fiyatlar</h3></div>
  <form method="post" action="{{ url_for('admin.doping') }}">
    {{ csrf_field() }}<input type="hidden" name="action" value="prices">
    <div class="table-wrap"><table>
      <tr><th>Doping</th><th>Süre</th><th>Fiyat (TL)</th><th>Satışta</th></tr>
      {% for p in prices %}<tr>
        <td>{{ p.kind_label }}</td><td>{{ p.hours_label }}</td>
        <td><input type="text" inputmode="decimal" name="price_{{ p.id }}" value="{{ p.price|plain }}" style="max-width:130px" aria-label="{{ p.kind_label }} {{ p.hours_label }} fiyatı" required></td>
        <td><label class="check"><input type="checkbox" name="active_{{ p.id }}" value="1" {{ 'checked' if p.is_active }}> Aktif</label></td>
      </tr>{% endfor %}
    </table></div>
    <div class="mt"><button class="btn" type="submit">Fiyatları kaydet</button></div>
  </form>
</div>

<div class="card mb">
  <div class="card-h"><h3>Reklam panosu kapasitesi</h3></div>
  <form method="post" action="{{ url_for('admin.doping') }}" class="filters">
    {{ csrf_field() }}<input type="hidden" name="action" value="settings">
    <div class="field"><label for="dmb">Aynı anda en fazla reklam banner'ı</label><input type="number" id="dmb" name="doping_max_banners" value="{{ banner_max }}" min="0" max="50" required style="max-width:140px"><div class="hint">Dolunca yeni reklam banner'ı satın alınamaz (süre uzatma serbesttir). Şu an {{ banner_used }} aktif.</div></div>
    <div class="field"><button class="btn" type="submit">Kaydet</button></div>
  </form>
</div>

<div class="card">
  <div class="card-h"><h3>Son satışlar</h3><a class="small" href="{{ url_for('admin.banners') }}">Bannerlar</a></div>
  {% if recent %}
  <div class="table-wrap"><table>
    <tr><th>Tarih</th><th>Satıcı</th><th>İlan</th><th>Doping</th><th>Süre</th><th class="right">Tutar</th><th>Bitiş</th></tr>
    {% for r in recent %}<tr>
      <td class="nowrap">{{ r.created_at|dt }}</td>
      <td><a href="{{ url_for('admin.user', uid=r.seller_id) }}">{{ r.username }}</a></td>
      <td><a href="{{ url_for('listing_detail', lid=r.listing_id) }}">{{ r.title[:40] }}</a></td>
      <td>{{ r.label }}</td><td>{{ r.hours_label }}</td>
      <td class="right nowrap">{{ r.price|money }}</td>
      <td class="nowrap small">{{ r.ends_at|dt }} {% if r.live %}<span class="badge b-ok">Yayında</span>{% endif %}</td>
    </tr>{% endfor %}
  </table></div>
  {% else %}{{ empty('Henüz doping satışı yok') }}{% endif %}
</div>
{% endblock %}
"""
