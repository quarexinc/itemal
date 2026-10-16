"""Mağaza paketleri şablonları (Jinja): satıcı paket sayfası ve yönetim paket sayfası. Emoji kullanılmaz."""

TEMPLATES = {}

TEMPLATES['seller_packages.html'] = r"""
{% extends "seller_base.html" %}
{% from "_macros.html" import ic, empty with context %}
{% block title %}Paketler{% endblock %}
{% block panel %}
<div class="page-h">
  <div><div class="crumb">Mağaza</div><h1>Mağaza paketleri</h1></div>
  <div class="row">
    <span class="chip" title="Kullanılabilir bakiye">{{ ic('wallet') }}Bakiye: <b>{{ balance|money }}</b></span>
    <a class="btn btn-ghost btn-sm" href="{{ url_for('balance') }}">{{ ic('plus') }}Bakiye yükle</a>
  </div>
</div>
<p class="muted pk-lead">Paketler bakiyenden satın alınır ve satın aldığın anda etkinleşir. Mavi tik mağaza adının yanında ilan kartlarında, ilan sayfasında, mağaza sayfanda, yorumlarda ve sohbetlerde görünür. Süreli paketleri tekrar alırsan süre uzar.</p>

{% if active_list %}
<div class="card pk-active mb">
  <div class="card-h"><h3>{{ ic('check-circle') }} Aktif paketlerin</h3><span class="chip">{{ active_list|length }}</span></div>
  <div class="row">
    {% for a in active_list %}<span class="pk-chip" style="--c:{{ a.color }}"><b>{{ a.name }}</b><em>{% if a.permanent %}Kalıcı{% else %}{{ a.until|dt(false) }} tarihine kadar{% endif %}</em></span>{% endfor %}
  </div>
</div>
{% endif %}

<div class="pk-grid">
  {% for c in cards %}{% set p = c.p %}
  <article class="pk-card{{ ' owned' if c.owned }}{{ ' hot' if p.tier == 'diamond' }}{{ ' tier-gold' if p.tier == 'gold' }}" style="--c:{{ c.color }}" id="paket-{{ p.id }}">
    {% if p.tier == 'diamond' %}<span class="pk-ribbon">En kapsamlı</span>{% endif %}
    <div class="pk-top">
      <span class="pk-ico">{{ c.icon }}</span>
      <div><h3>{{ p.name }}</h3><p class="muted small">{{ p.tagline }}</p></div>
    </div>
    {% if p.tier == 'diamond' %}<div class="pk-perks"><span>{{ ic('gem') }}Elmas rozet</span><span>{{ ic('gift') }}{{ p.giveaway_slots }} ek çekiliş</span><span>{{ ic('palette') }}Tüm temalar</span><span>{{ ic('life-buoy') }}Öncelikli destek</span></div>{% endif %}
    <div class="pk-price"><b>{{ p.price|money }}</b><span>{% if p.duration_days %}/ {{ p.duration_days }} gün{% else %}tek seferlik{% endif %}</span></div>
    <ul class="pk-feats">
      {% for f in c.features %}<li>{{ ic('check') }}<span>{{ f }}</span></li>{% endfor %}
    </ul>
    {% if p.description %}<p class="pk-desc small muted">{{ p.description }}</p>{% endif %}
    <div class="pk-foot">
      {% if c.owned %}<div class="pk-own">{{ ic('check-circle') }}<span>Aktif - {% if c.owned.permanent %}kalıcı{% else %}bitiş {{ c.owned.until|dt(false) }}{% endif %}</span></div>{% endif %}
      {% if c.locked %}
        <button class="btn btn-ghost btn-block" type="button" disabled>Kalıcı olarak sahipsin</button>
      {% elif not c.can_afford %}
        <a class="btn btn-line btn-block" href="{{ url_for('balance') }}">{{ ic('wallet') }}Bakiye yükle ({{ c.missing|money }} eksik)</a>
      {% else %}
        <form method="post" action="{{ url_for('seller.package_buy', pid=p.id) }}" data-confirm="{{ p.name }} paketi için {{ p.price|money }} bakiyenden düşülecek. Onaylıyor musun?">
          {{ csrf_field() }}
          <button class="btn btn-block{{ ' shine' if p.tier == 'diamond' }}" type="submit">{% if c.owned %}Süreyi uzat{% else %}Satın al{% endif %} - {{ p.price|money }}</button>
        </form>
      {% endif %}
    </div>
  </article>
  {% else %}
  <div class="card">{{ empty('Şu anda satışta paket yok') }}</div>
  {% endfor %}
</div>

<div class="card mt">
  <div class="card-h"><h3>Paket geçmişin</h3></div>
  {% if history %}
  <div class="table-wrap"><table>
    <tr><th>Tarih</th><th>Paket</th><th class="right">Tutar</th><th>Başlangıç</th><th>Bitiş</th><th>Durum</th></tr>
    {% for h in history %}<tr>
      <td class="nowrap">{{ h.created_at|dt }}</td><td><b>{{ h.name }}</b>{% if h.source == 'admin' %} <span class="muted small">(yönetici verdi)</span>{% endif %}</td>
      <td class="right nowrap">{{ h.price|money }}</td><td class="nowrap">{{ h.starts_at|dt(false) }}</td><td class="nowrap">{% if h.ends_at %}{{ h.ends_at|dt(false) }}{% else %}Kalıcı{% endif %}</td>
      <td>{% if h.state == 'active' %}<span class="badge b-ok">Aktif</span>{% elif h.state == 'queued' %}<span class="badge b-info">Sırada</span>{% elif h.state == 'cancelled' %}<span class="badge b-bad">İptal</span>{% else %}<span class="badge b-muted">Bitti</span>{% endif %}</td>
    </tr>{% endfor %}
  </table></div>
  {% else %}{{ empty('Henüz paket almadın', 'Yukarıdan bir paket seçerek mağazanı öne çıkarabilirsin.') }}{% endif %}
</div>
{% endblock %}
"""

TEMPLATES['admin_packages.html'] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import empty, ic, pager with context %}
{% block heading %}Mağaza paketleri{% endblock %}
{% block panel %}
<div class="grid g4 mb">
  <div class="stat good"><div class="k">Toplam gelir</div><div class="v">{{ totals.revenue|money }}</div><div class="s">{{ totals.sales }} paket satışı</div></div>
  <div class="stat"><div class="k">Etkin paketli mağaza</div><div class="v">{{ totals.holders }}</div><div class="s">{{ totals.active }} etkin paket</div></div>
  <div class="stat"><div class="k">Satın alınan</div><div class="v">{{ totals.sales }}</div></div>
  <div class="stat"><div class="k">Yönetici verdi</div><div class="v">{{ totals.granted }}</div></div>
</div>

<div class="pk-admin-grid mb">
  {% for x in pkgs %}{% set p = x.p %}
  <form class="card pk-edit{{ '' if p.is_active else ' off' }}" id="paket-{{ p.id }}" style="--c:{{ x.color }}" method="post" action="{{ url_for('admin.package_edit', pid=p.id) }}">
    {{ csrf_field() }}
    <div class="pk-top">
      <span class="pk-ico">{{ x.icon }}</span>
      <div class="grow-1"><h3>{{ p.name }} <span class="muted small mono">{{ p.code }}</span></h3>
        <div class="small muted">{{ x.sales }} satış &middot; {{ x.revenue|money }} gelir &middot; {{ x.active_users }} etkin</div></div>
      <span class="badge b-{{ 'ok' if p.is_active else 'muted' }}">{{ 'Satışta' if p.is_active else 'Pasif' }}</span>
    </div>
    <div class="pk-chips">{% for f in x.features %}<span>{{ f }}</span>{% endfor %}</div>
    <div class="form-row">
      <div class="field"><label for="name{{ p.id }}">Ad</label><input type="text" id="name{{ p.id }}" name="name" value="{{ p.name }}" required maxlength="80"></div>
      <div class="field"><label for="tag{{ p.id }}">Kısa açıklama</label><input type="text" id="tag{{ p.id }}" name="tagline" value="{{ p.tagline }}" maxlength="160"></div>
    </div>
    <div class="field"><label for="desc{{ p.id }}">Açıklama</label><textarea id="desc{{ p.id }}" name="description" maxlength="1000" style="min-height:70px">{{ p.description }}</textarea></div>
    <div class="form-row">
      <div class="field"><label for="price{{ p.id }}">Fiyat (TL)</label><input type="text" inputmode="decimal" id="price{{ p.id }}" name="price" value="{{ x.price_plain }}" required></div>
      <div class="field"><label for="dur{{ p.id }}">Süre (gün, 0 = kalıcı)</label><input type="number" id="dur{{ p.id }}" name="duration_days" min="0" max="3650" value="{{ p.duration_days }}" required></div>
    </div>
    <div class="form-row">
      {% if p.commission_discount > 0 %}<div class="field"><label for="disc{{ p.id }}">Komisyon indirimi (puan)</label><input type="text" inputmode="decimal" id="disc{{ p.id }}" name="commission_discount" value="{{ x.disc_plain }}"></div>{% endif %}
      {% if p.giveaway_slots > 0 %}<div class="field"><label for="gs{{ p.id }}">Ek çekiliş hakkı</label><input type="number" id="gs{{ p.id }}" name="giveaway_slots" min="0" max="50" value="{{ p.giveaway_slots }}"></div>{% endif %}
      <div class="field"><label for="sort{{ p.id }}">Sıra</label><input type="number" id="sort{{ p.id }}" name="sort_order" value="{{ p.sort_order }}"></div>
    </div>
    <div class="spread">
      <label class="check"><input type="checkbox" name="is_active" value="1" {{ 'checked' if p.is_active }}> Satışta (aktif)</label>
      <button class="btn btn-sm" type="submit">Kaydet</button>
    </div>
  </form>
  {% endfor %}
</div>

<div class="card mb" id="ver">
  <h3 class="mt0">Satıcıya elle paket ver</h3>
  <p class="muted small mt0">Ücretsiz tanımlanır (bakiye değişmez). Kullanıcıda aynı paket varsa süre uzar; kalıcı paket zaten varsa reddedilir.</p>
  <form method="post" action="{{ url_for('admin.package_grant') }}">
    {{ csrf_field() }}
    <div class="form-row">
      <div class="field"><label for="g_user">Kullanıcı adı</label><input type="text" id="g_user" name="username" required maxlength="40" placeholder="satici_adi"></div>
      <div class="field"><label for="g_pkg">Paket</label><select id="g_pkg" name="package_id" required>{% for x in pkgs %}<option value="{{ x.p.id }}">{{ x.p.name }} ({{ x.p.duration_days ~ ' gün' if x.p.duration_days else 'kalıcı' }})</option>{% endfor %}</select></div>
    </div>
    <div class="field" style="max-width:320px"><label for="g_days">Gün sayısı (isteğe bağlı)</label><input type="number" id="g_days" name="days" min="1" max="3650" placeholder="Paketin süresi"><div class="hint">Boş bırakırsan paketin kendi süresi uygulanır. Kalıcı paketlerde yok sayılır.</div></div>
    <button class="btn" type="submit">{{ ic('plus') }}Paketi ver</button>
  </form>
</div>

<div class="card-h"><h3>Satış ve tanımlamalar</h3>
  <form method="get" action="{{ url_for('admin.packages') }}" class="row">
    <select name="paket" aria-label="Paket" style="width:auto"><option value="0">Tüm paketler</option>{% for x in pkgs %}<option value="{{ x.p.id }}" {{ 'selected' if filter == x.p.id }}>{{ x.p.name }}</option>{% endfor %}</select><button class="btn btn-ghost btn-sm" type="submit">Filtrele</button>
  </form>
</div>
{% if page.rows %}
<div class="table-wrap"><table>
  <tr><th>No</th><th>Tarih</th><th>Mağaza</th><th>Paket</th><th class="right">Tutar</th><th>Kaynak</th><th>Başlangıç</th><th>Bitiş</th><th>Durum</th><th></th></tr>
  {% for r in page.rows %}<tr>
    <td>#{{ r.id }}</td><td class="nowrap">{{ r.created_at|dt }}</td>
    <td><a href="{{ url_for('admin.user', uid=r.user_id) }}">{{ r.store }}</a>{{ pkg_marks(r.user_id) }}<div class="muted small">@{{ r.username }}</div></td>
    <td><b>{{ r.package_name }}</b></td><td class="right nowrap">{{ r.price|money }}</td>
    <td>{{ 'Yönetici' if r.source == 'admin' else 'Satın alma' }}</td>
    <td class="nowrap">{{ r.starts_at|dt }}</td><td class="nowrap">{% if r.ends_at %}{{ r.ends_at|dt }}{% else %}Kalıcı{% endif %}</td>
    <td>{% if r.state == 'active' %}<span class="badge b-ok">Aktif</span>{% elif r.state == 'queued' %}<span class="badge b-info">Sırada</span>{% elif r.state == 'cancelled' %}<span class="badge b-bad">İptal</span>{% else %}<span class="badge b-muted">Bitti</span>{% endif %}</td>
    <td class="actions">{% if r.state in ['active', 'queued'] %}<form method="post" action="{{ url_for('admin.package_revoke') }}" data-confirm="{{ r.package_name }} paketi {{ r.username }} kullanıcısından kaldırılsın mı? (Ücret iade edilmez.)">{{ csrf_field() }}<input type="hidden" name="user_id" value="{{ r.user_id }}"><input type="hidden" name="package_id" value="{{ r.package_id }}"><button class="btn btn-danger btn-sm" type="submit">Kaldır</button></form>{% endif %}</td>
  </tr>{% endfor %}
</table></div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Henüz paket satışı yok', 'Satıcılar paketleri panelindeki Paketler sayfasından satın alır.') }}</div>{% endif %}
{% endblock %}
"""
