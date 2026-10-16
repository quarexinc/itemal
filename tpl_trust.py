"""Güven modülleri şablonları: şikayet ve mağaza yorumu yönetimi."""

TEMPLATES = {}

TEMPLATES["admin_complaints.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import pager, empty, badge with context %}
{% block title %}Şikayetler{% endblock %}
{% block heading %}Şikayetler{% endblock %}
{% block panel %}
<div class="tabs">
  {% for key, label in [('open', 'Açık'), ('resolved', 'Çözüldü'), ('dismissed', 'Reddedildi'), ('all', 'Tümü')] %}
  <a class="{{ 'on' if status == key }}" href="{{ url_for('admin.complaints', durum=key, tur=kind) }}">{{ label }}{% if key != 'all' and counts.get(key) %} ({{ counts.get(key) }}){% endif %}</a>
  {% endfor %}
</div>
<div class="row mb">
  {% for key, label in [('', 'Tüm türler'), ('listing', 'İlan'), ('user', 'Kullanıcı'), ('order', 'Sipariş itirazı')] %}
  <a class="btn btn-sm {{ 'btn-line' if kind != key else '' }}" href="{{ url_for('admin.complaints', durum=status, tur=key) }}">{{ label }}</a>
  {% endfor %}
</div>
{% if page.rows %}
<div class="grid" style="gap:12px">
  {% for r in page.rows %}
  <div class="card">
    <div class="spread">
      <div class="row">
        <span class="badge b-muted">{{ {'listing': 'İlan', 'user': 'Kullanıcı', 'order': 'Sipariş'}[r.kind] }}</span>
        {{ badge(r.status) }}
        <b>{{ r.reason }}</b>
      </div>
      <span class="muted small">#{{ r.id }} &middot; {{ r.created_at|dt }}</span>
    </div>
    <div class="muted small mt">
      Bildiren: <a href="{{ url_for('admin.user', uid=r.reporter_id) }}">{{ r.reporter_name }}</a> &rarr;
      {% if r.kind == 'listing' %}<a href="{{ url_for('listing_detail', lid=r.target_id) }}" target="_blank" rel="noopener">{{ r.listing_title or ('İlan #' ~ r.target_id) }}</a> ({{ (r.listing_status or '-')|slabel }})
      {% elif r.kind == 'user' %}<a href="{{ url_for('admin.user', uid=r.target_id) }}">{{ r.target_name }}</a>{% if r.target_banned %} <span class="badge b-bad">Askıda</span>{% endif %}
      {% else %}Sipariş <a href="{{ url_for('admin.orders', q=r.target_id) }}">#{{ r.target_id }}</a> &middot; {{ (r.order_title or '')[:40] }} &middot; {{ (r.order_total or 0)|money }} &middot; {{ (r.order_escrow or '-')|slabel }}{% endif %}
    </div>
    {% if r.detail %}<div class="pre mt">{{ r.detail }}</div>{% endif %}
    {% if r.status == 'open' %}
    <form method="post" action="{{ url_for('admin.complaint_action', rid=r.id) }}" class="mt">
      {{ csrf_field() }}
      <div class="field"><input type="text" name="note" maxlength="300" placeholder="Not / bildirene gidecek yanıt (isteğe bağlı)"></div>
      <div class="row">
        <button class="btn btn-ok btn-sm" name="action" value="resolve" type="submit">Çözüldü</button>
        <button class="btn btn-ghost btn-sm" name="action" value="dismiss" type="submit">İşlem gerektirmiyor</button>
        {% if r.kind == 'listing' %}<button class="btn btn-danger btn-sm" name="action" value="block_listing" type="submit" data-confirm="İlan engellensin mi?">İlanı engelle</button>{% endif %}
        {% if r.kind == 'user' %}<button class="btn btn-danger btn-sm" name="action" value="ban_user" type="submit" data-confirm="Hesap askıya alınsın mı?">Hesabı askıya al</button>{% endif %}
        {% if r.kind == 'order' %}
          <button class="btn btn-ok btn-sm" name="action" value="release_order" type="submit" data-confirm="Tutar satıcıya aktarılsın mı?">Satıcıya aktar</button>
          <button class="btn btn-danger btn-sm" name="action" value="refund_order" type="submit" data-confirm="Tutar alıcıya iade edilsin mi?">Alıcıya iade et</button>
        {% endif %}
      </div>
    </form>
    {% elif r.admin_note %}<p class="muted small mt">Not: {{ r.admin_note }}</p>{% endif %}
  </div>
  {% endfor %}
</div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Bildirim yok', 'Bu filtrede şikayet bulunmuyor.') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["admin_scomments.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import pager, empty %}
{% block title %}Mağaza Yorumları{% endblock %}
{% block heading %}Mağaza yorumları{% endblock %}
{% block panel %}
{% if page.rows %}
<div class="grid" style="gap:12px">
  {% for c in page.rows %}
  <div class="card">
    <div class="spread"><div class="muted small"><a href="{{ url_for('admin.user', uid=c.author_id) }}">{{ c.author_name }}</a>{{ pkg_marks(c.author_id) }} &rarr; <a href="{{ url_for('admin.user', uid=c.seller_id) }}">{{ c.seller_name }}</a>{{ pkg_marks(c.seller_id) }}{% if c.is_hidden %} <span class="badge b-bad">Gizli</span>{% endif %}</div><span class="muted small">{{ c.created_at|dt }}</span></div>
    <div class="pre mt">{{ c.body }}</div>
    <form method="post" action="{{ url_for('admin.seller_comment_action', cid=c.id) }}" class="mt row">{{ csrf_field() }}
      {% if c.is_hidden %}<button class="btn btn-ok btn-sm" name="action" value="show" type="submit">Yeniden yayınla</button>{% else %}<button class="btn btn-ghost btn-sm" name="action" value="hide" type="submit">Gizle</button>{% endif %}
      <button class="btn btn-danger btn-sm" name="action" value="delete" type="submit" data-confirm="Yorum kalıcı olarak silinsin mi?">Sil</button>
    </form>
  </div>
  {% endfor %}
</div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Mağaza yorumu yok') }}</div>{% endif %}
{% endblock %}
"""
