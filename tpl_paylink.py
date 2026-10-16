"""Ödeme linki şablonları (yönetim sayfası + kullanıcının "ödemen işleniyor" ekranı). Emoji kullanılmaz."""

TEMPLATES = {}

TEMPLATES["admin_paylinks.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import empty, ic %}
{% block title %}Ödeme Linkleri{% endblock %}
{% block heading %}Ödeme linkleri{% endblock %}
{% block panel %}
<div class="notice mb">Kullanıcılar Bakiye Yükle sayfasında bu linkleri görür. Linke basan kullanıcı ödeme sayfasına gider, sitede "ödemen işleniyor" ekranı açılır. Ödemeyi kontrol edip
  <a href="{{ url_for('admin.deposits') }}">Bakiye yüklemeleri</a> sayfasından onaylayınca fiyat kadar tutar bakiyesine eklenir.</div>

<div class="card mb">
  <h2>{{ 'Ödeme linkini düzenle' if edit else 'Yeni ödeme linki' }}</h2>
  <form method="post" action="{{ url_for('admin.admin_paylinks') }}">
    {{ csrf_field() }}{% if edit %}<input type="hidden" name="id" value="{{ edit.id }}">{% endif %}
    <div class="form-row">
      <div class="field"><label for="pl_title">Başlık</label><input type="text" id="pl_title" name="title" value="{{ form.title }}" required minlength="3" maxlength="80" placeholder="100 TL Bakiye"></div>
      <div class="field"><label for="pl_amount">Fiyat (TL)</label><input type="text" inputmode="decimal" id="pl_amount" name="amount" value="{{ form.amount }}" required placeholder="100,00"><div class="hint">Ödeme onaylanınca kullanıcının bakiyesine eklenecek tutar.</div></div>
    </div>
    <div class="field"><label for="pl_url">Ödeme linki</label><input type="url" id="pl_url" name="url" value="{{ form.url }}" required maxlength="500" placeholder="https://..."><div class="hint">Yalnızca https:// ile başlayan adresler kabul edilir.</div></div>
    <div class="field"><label for="pl_desc">Açıklama (isteğe bağlı)</label><input type="text" id="pl_desc" name="description" value="{{ form.description }}" maxlength="200"></div>
    <div class="form-row">
      <div class="field"><label for="pl_sort">Sıra</label><input type="number" id="pl_sort" name="sort_order" value="{{ form.sort_order }}"></div>
      <div class="field"><label class="check"><input type="checkbox" name="is_active" value="1" {{ 'checked' if form.is_active }}> Aktif (kullanıcılar görür)</label></div>
    </div>
    <button class="btn" type="submit">{{ 'Kaydet' if edit else 'Ekle' }}</button>
    {% if edit %}<a class="btn btn-ghost" href="{{ url_for('admin.admin_paylinks') }}">Vazgeç</a>{% endif %}
  </form>
</div>

{% if rows %}
<div class="table-wrap"><table>
  <tr><th>Başlık</th><th>Link</th><th class="right">Fiyat</th><th>Durum</th><th class="right">Bekleyen / Onaylı</th><th></th></tr>
  {% for p in rows %}<tr>
    <td><b>{{ p.title }}</b>{% if p.description %}<div class="muted small">{{ p.description }}</div>{% endif %}</td>
    <td class="small" style="max-width:280px;overflow-wrap:anywhere"><a href="{{ p.url }}" target="_blank" rel="noopener noreferrer nofollow">{{ p.url }}</a></td>
    <td class="right nowrap"><b>{{ p.amount|money }}</b></td>
    <td>{% if p.is_active %}<span class="badge b-ok">Aktif</span>{% else %}<span class="badge b-muted">Pasif</span>{% endif %}</td>
    <td class="right">{{ p.pending_n }} / {{ p.approved_n }}</td>
    <td class="actions">
      <a class="btn btn-ghost btn-sm" href="{{ url_for('admin.admin_paylinks', duzenle=p.id) }}">Düzenle</a>
      <form method="post" action="{{ url_for('admin.admin_paylink_toggle', lid=p.id) }}" style="display:inline">{{ csrf_field() }}<button class="btn btn-ghost btn-sm" type="submit">{{ 'Kapat' if p.is_active else 'Aç' }}</button></form>
      <form method="post" action="{{ url_for('admin.admin_paylink_delete', lid=p.id) }}" style="display:inline" data-confirm="Ödeme linki silinsin mi? Geçmiş yüklemeler korunur.">{{ csrf_field() }}<button class="btn btn-danger btn-sm" type="submit">Sil</button></form>
    </td>
  </tr>{% endfor %}
</table></div>
{% else %}<div class="card">{{ empty('Henüz ödeme linki yok') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["pay_wait.html"] = r"""
{% extends "account_base.html" %}
{% from "_macros.html" import badge, ic with context %}
{% block title %}Ödeme Durumu{% endblock %}
{% block head_extra %}{% if d.status == 'pending' %}<meta http-equiv="refresh" content="10">{% endif %}{% endblock %}
{% block panel %}
<div class="page-h"><h1>Ödeme durumu</h1><span class="chip">Bakiyen: {{ balance_now|money }}</span></div>

<div class="card cp-state mb">
  {% if d.status == 'pending' %}
    <div class="cp-spin" aria-hidden="true"></div>
    <h2>Ödemen işleniyor</h2>
    <p class="muted">Ödeme sayfasında işlemi tamamla. Ödemen yönetim tarafından kontrol edilince <b>{{ d.amount|money }}</b> bakiyene eklenecek. Bu sayfa kendiliğinden yenilenir, kapatabilirsin; sonuç bildirim olarak da gelir.</p>
    {% if d.link_url %}<p><a class="btn" href="{{ d.link_url }}" target="_blank" rel="noopener noreferrer nofollow">Ödeme sayfasını aç</a></p>{% endif %}
  {% elif d.status == 'approved' %}
    <div class="cp-done ok">{{ ic('check') }}</div>
    <div class="pay-plus">{{ d.amount|smoney }}</div>
    <h2>Bakiyeniz onaylandı</h2>
    <p class="muted">Ödemen onaylandı, tutar hesabına eklendi. Güncel bakiyen: <b>{{ balance_now|money }}</b></p>
    <p><a class="btn" href="{{ url_for('listings') }}">Alışverişe başla</a></p>
  {% else %}
    <div class="cp-done bad">{{ ic('x') }}</div>
    <h2>Talep sonuçlanmadı</h2>
    <p class="muted">{{ d.admin_note or 'Bu ödeme talebi onaylanmadı.' }} Ödemeyi yaptıysan destek talebi açabilirsin.</p>
    <p><a class="btn btn-ghost" href="{{ url_for('balance') }}">Bakiye Yükle'ye dön</a> <a class="btn btn-ghost" href="{{ url_for('ticket_new') }}">Destek talebi</a></p>
  {% endif %}
  <dl class="kv mt">
    <dt>Talep no</dt><dd>#{{ d.id }}</dd>
    <dt>Ödeme</dt><dd>{{ d.method_name }}</dd>
    <dt>Tutar</dt><dd>{{ d.amount|money }}</dd>
    <dt>Durum</dt><dd>{{ badge(d.status) }}</dd>
    <dt>Tarih</dt><dd>{{ d.created_at|dt }}</dd>
  </dl>
</div>

{% if d.status == 'pending' %}
<div class="card mb">
  <h3>Onayı hızlandır</h3>
  <p class="muted small">Ödemeyi yaptıktan sonra ödeme numarasını, dekont numarasını veya ödemede kullandığın ad soyadı yaz; yönetim ödemeni daha çabuk eşleştirir.</p>
  <form method="post" action="{{ url_for('paylink.info', did=d.id) }}">
    {{ csrf_field() }}
    <div class="field"><label for="pw_ref">Ödeme / dekont no veya ad soyad</label><input type="text" id="pw_ref" name="reference" value="{{ d.reference }}" required minlength="3" maxlength="120"></div>
    <div class="field"><label for="pw_note">Not (isteğe bağlı)</label><input type="text" id="pw_note" name="note" value="{{ d.note }}" maxlength="300"></div>
    <button class="btn" type="submit">Bilgiyi Gönder</button>
  </form>
</div>
<form method="post" action="{{ url_for('paylink.cancel', did=d.id) }}" data-confirm="Ödemeyi yapmadıysan talebi iptal et. Ödeme yaptıysan iptal etme. Devam edilsin mi?">
  {{ csrf_field() }}<button class="btn btn-ghost btn-sm" type="submit">Talebi iptal et</button>
</form>
{% endif %}
{% endblock %}
"""
