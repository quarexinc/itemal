"""Topluluk şablonları: satıcı takibi ve çekilişler. Emoji kullanılmaz."""

TEMPLATES = {}

TEMPLATES["_community.html"] = r"""
{% from "_macros.html" import ic with context %}
{% macro follow_btn(seller_id, following, count, small=false) %}
<form class="inline-form follow-form" method="post" action="{{ url_for('community.follow_toggle', sid=seller_id) }}" data-follow>
  {{ csrf_field() }}
  <button class="btn {{ 'btn-line' if following else '' }} {{ 'btn-sm' if small }}" type="submit" data-follow-btn>{{ ic('users') }}<span data-follow-label>{{ 'Takip ediliyor' if following else 'Takip et' }}</span><em class="follow-count" data-follow-count>{{ count }}</em></button>
</form>
{% endmacro %}

{% macro gw_card(gw, entered=false, left='') %}
<a class="gw-card" href="{{ url_for('community.giveaway_view', gid=gw.id) }}">
  <div class="gw-top"><span class="gw-ico">{{ ic('gift') }}</span><div class="gw-prize"><small>Ödül</small><b>{{ gw.prize }}</b></div></div>
  <h3>{{ gw.title }}</h3>
  <div class="muted small">{{ gw.store_name or gw.seller_name }}</div>
  <div class="gw-meta">
    <span>{{ ic('users') }}{{ gw.entry_count }} katılımcı</span>
    <span>{{ ic('trophy') }}{{ gw.winners }} kazanan</span>
    {% if gw.status == 'open' %}<span>{{ ic('clock') }}{{ left }}</span>{% endif %}
  </div>
  <div class="gw-tags">
    {% if gw.need_follow %}<span class="chip-s">Takip şartı</span>{% endif %}
    {% if gw.need_purchase %}<span class="chip-s">Alışveriş şartı</span>{% endif %}
    {% if entered %}<span class="chip-s ok">Katıldın</span>{% endif %}
    {% if gw.status == 'drawn' %}<span class="chip-s">Sonuçlandı</span>{% endif %}
  </div>
</a>
{% endmacro %}
"""

TEMPLATES["giveaways.html"] = r"""
{% extends "base.html" %}
{% from "_macros.html" import empty, ic with context %}
{% from "_community.html" import gw_card with context %}
{% block title %}Çekilişler{% endblock %}
{% block content %}
<div class="container section">
  <div class="cat-hero gw-hero">
    <div><h1 class="mb0">{{ ic('gift') }} Çekilişler</h1><p class="muted mb0">Mağazaların düzenlediği çekilişlere katıl; kazananlar kura ile belirlenir.</p></div>
    {% if can_sell %}<a class="btn" href="{{ url_for('seller.giveaways') }}">Çekiliş düzenle</a>{% endif %}
  </div>
  <div class="section-h mt"><h2>Devam eden çekilişler</h2></div>
  {% if open_rows %}<div class="gw-grid">{% for gw in open_rows %}{{ gw_card(gw, gw.id in mine, remaining(gw.ends_at)) }}{% endfor %}</div>
  {% else %}<div class="card">{{ empty('Şu an açık çekiliş yok', 'Takip ettiğin mağazalar çekiliş başlattığında burada ve bildirimlerinde görünür.') }}</div>{% endif %}
  {% if done %}
  <div class="section-h mt"><h2>Son sonuçlanan çekilişler</h2></div>
  <div class="gw-grid">{% for gw in done %}{{ gw_card(gw, gw.id in mine) }}{% endfor %}</div>
  {% endif %}
</div>
{% endblock %}
"""

TEMPLATES["giveaway_view.html"] = r"""
{% extends "base.html" %}
{% from "_macros.html" import avatar, ic with context %}
{% block title %}{{ gw.title }}{% endblock %}
{% block content %}
<div class="container section" style="max-width:860px">
  <div class="crumbs"><a href="{{ url_for('community.giveaways') }}">Çekilişler</a> <span>/</span> <span>{{ gw.title }}</span></div>
  <div class="card gw-detail">
    <div class="gw-head">
      <span class="gw-ico lg">{{ ic('gift') }}</span>
      <div class="grow-1">
        <span class="badge b-{{ status[1] }}">{{ status[0] }}</span>
        <h1>{{ gw.title }}</h1>
        <a class="row small" href="{{ url_for('storefront', username=gw.seller_name) }}">{{ avatar(gw.seller_name, gw.seller_avatar, 'sm') }}<b>{{ gw.store_name or gw.seller_name }}</b>{{ pkg_marks(gw.seller_id) }}</a>
      </div>
    </div>
    <div class="gw-prize-box"><small>Ödül</small><b>{{ gw.prize }}</b></div>
    {% if gw.description %}<p class="pre">{{ gw.description }}</p>{% endif %}
    <div class="grid g3 mb">
      <div class="stat"><div class="k">Katılımcı</div><div class="v">{{ gw.entry_count }}</div></div>
      <div class="stat"><div class="k">Kazanan sayısı</div><div class="v">{{ gw.winners }}</div></div>
      <div class="stat"><div class="k">{{ 'Kalan süre' if gw.status == 'open' else 'Bitiş' }}</div><div class="v" style="font-size:1.15rem">{{ left if gw.status == 'open' else (gw.drawn_at or gw.ends_at)|dt }}</div></div>
    </div>
    <ul class="gw-rules">
      <li>{{ ic('check-circle') }}Kazananlar kura ile, sistem tarafından rastgele belirlenir.</li>
      {% if gw.need_follow %}<li>{{ ic('check-circle') }}Katılmak için mağazayı takip etmek gerekir.</li>{% endif %}
      {% if gw.need_purchase %}<li>{{ ic('check-circle') }}Yalnızca bu mağazadan alışveriş yapmış üyeler katılabilir.</li>{% endif %}
      <li>{{ ic('check-circle') }}Bitiş: {{ gw.ends_at|dt }}. Kazananlara bildirim gönderilir; ödül satıcı tarafından teslim edilir.</li>
    </ul>

    {% if gw.status == 'drawn' %}
      <h3>Kazananlar</h3>
      {% if winners %}<div class="row">{% for w in winners %}<span class="chip">{{ ic('trophy') }}{{ w.username|mask }}{% if me and me.id == w.id %} (sen){% endif %}</span>{% endfor %}</div>
      {% else %}<p class="muted">Bu çekilişe uygun katılım olmadı.</p>{% endif %}
      {% if won %}<div class="notice ok mt">Tebrikler, çekilişi kazandın. Ödülünü almak için satıcıyla mesajlaşabilirsin.</div>{% endif %}
    {% elif gw.status == 'cancelled' %}
      <div class="notice bad">Bu çekiliş iptal edildi.</div>
    {% elif is_owner %}
      <div class="notice">Bu senin çekilişin. Yönetmek için <a href="{{ url_for('seller.giveaways') }}">Çekilişlerim</a> sayfasına git.</div>
    {% elif entered %}
      <div class="notice ok">Bu çekilişe katıldın. Bol şans!</div>
      <form method="post" action="{{ url_for('community.giveaway_leave', gid=gw.id) }}" data-confirm="Çekilişten ayrılmak istiyor musun?">{{ csrf_field() }}<button class="btn btn-line btn-sm" type="submit">Katılımı geri çek</button></form>
    {% elif not me %}
      <a class="btn btn-lg" href="{{ url_for('login', next=request.path) }}">Katılmak için giriş yap</a>
    {% elif ok %}
      <form method="post" action="{{ url_for('community.giveaway_join', gid=gw.id) }}" class="row">
        {{ csrf_field() }}
        {% if gw.need_follow and not follows %}<input type="hidden" name="follow" value="1">{% endif %}
        <button class="btn btn-lg shine" type="submit">{{ ic('gift') }}{{ 'Takip et ve katıl' if gw.need_follow and not follows else 'Çekilişe katıl' }}</button>
      </form>
    {% else %}
      <div class="notice warn">{{ why }}</div>
    {% endif %}
  </div>
</div>
{% endblock %}
"""

TEMPLATES["following.html"] = r"""
{% extends "base.html" %}
{% from "_macros.html" import avatar, empty, listing_card, ic with context %}
{% block title %}Takip ettiklerim{% endblock %}
{% block content %}
<div class="container section">
  <div class="page-h"><h1>{{ ic('users') }} Takip ettiklerim</h1><a class="btn btn-ghost btn-sm" href="{{ url_for('site.sellers') }}">Mağazalara göz at</a></div>
  {% if rows %}
  <div class="grid g3 mb">
    {% for s in rows %}
    <a class="seller-card" href="{{ url_for('storefront', username=s.username) }}">
      {{ avatar(s.username, s.avatar, 'lg') }}
      <div><b>{{ s.store_name or s.username }}{{ pkg_marks(s.id) }}</b><div class="muted small">{{ s.listings }} ilan &middot; {{ s.since|dt(false) }} tarihinden beri</div>{% if s.gws %}<span class="chip-s ok">{{ s.gws }} açık çekiliş</span>{% endif %}</div>
    </a>
    {% endfor %}
  </div>
  {% if fresh %}<div class="section-h"><h2>Takip ettiklerinden yeni ilanlar</h2></div><div class="lgrid">{% for l in fresh %}{{ listing_card(l) }}{% endfor %}</div>{% endif %}
  {% else %}<div class="card">{{ empty('Henüz kimseyi takip etmiyorsun', 'Mağaza sayfasındaki Takip et düğmesiyle yeni ilan ve çekilişlerden haberdar ol.') }}</div>{% endif %}
</div>
{% endblock %}
"""

TEMPLATES["seller_followers.html"] = r"""
{% extends "seller_base.html" %}
{% from "_macros.html" import pager, empty, avatar %}
{% block title %}Takipçilerim{% endblock %}
{% block panel %}
<div class="page-h"><h1>Takipçilerim</h1></div>
<div class="grid g3 mb">
  <div class="stat"><div class="k">Takipçi</div><div class="v">{{ total }}</div></div>
  <div class="stat good"><div class="k">Son 7 gün</div><div class="v">+{{ week }}</div></div>
  <div class="stat"><div class="k">Alışveriş yapmış takipçi</div><div class="v">{{ buyers }}</div><div class="s">{% if total %}%{{ (buyers * 100 / total)|round|int }}{% endif %}</div></div>
</div>
<p class="muted">Takipçilerin yeni çekilişlerinden haberdar edilir ve yeni ilanlarında bildirim alır. Daha fazla takipçi için mağaza adresini paylaş ve çekiliş düzenle.</p>
{% if page.rows %}
<div class="table-wrap"><table>
  <tr><th>Kullanıcı</th><th>Takip tarihi</th><th class="right">Sipariş</th></tr>
  {% for f in page.rows %}<tr><td><div class="row" style="flex-wrap:nowrap">{{ avatar(f.username, f.avatar, 'sm') }}<b>{{ f.username }}</b></div></td><td class="nowrap">{{ f.since|dt }}</td><td class="right">{{ f.orders }}</td></tr>{% endfor %}
</table></div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Henüz takipçin yok', 'Mağaza adresini paylaşarak ve çekiliş düzenleyerek takipçi kazan.') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["seller_giveaways.html"] = r"""
{% extends "seller_base.html" %}
{% from "_macros.html" import empty, ic with context %}
{% block title %}Çekilişlerim{% endblock %}
{% block panel %}
<div class="page-h"><h1>Çekilişlerim</h1><a class="btn btn-ghost btn-sm" href="{{ url_for('community.giveaways') }}" target="_blank" rel="noopener">{{ ic('external') }}Herkese açık sayfa</a></div>
<div class="grid g3 mb">
  <div class="stat"><div class="k">Açık çekiliş</div><div class="v">{{ open_n }} / {{ slots }}</div><div class="s">Çekiliş paketiyle hakkın artar</div></div>
  <div class="stat"><div class="k">Takipçi</div><div class="v">{{ followers }}</div><div class="s">Yeni çekilişte bildirim alırlar</div></div>
  <div class="stat"><div class="k">Toplam çekiliş</div><div class="v">{{ rows|length }}</div></div>
</div>
{% if not enabled %}<div class="notice warn">Çekiliş özelliği şu an yönetim tarafından kapatıldı.</div>
{% else %}
<div class="card mb">
  <h3 class="mt0">Yeni çekiliş başlat</h3>
  <form method="post" action="{{ url_for('seller.giveaway_new') }}">
    {{ csrf_field() }}
    <div class="grid g2">
      <div class="field"><label for="title">Çekiliş başlığı</label><input type="text" id="title" name="title" required minlength="5" maxlength="80" placeholder="Örnek: 100 TL Steam kartı çekilişi"></div>
      <div class="field"><label for="prize">Ödül</label><input type="text" id="prize" name="prize" required minlength="3" maxlength="120" placeholder="Örnek: 100 TL Steam hediye kartı"></div>
    </div>
    <div class="field"><label for="description">Açıklama (isteğe bağlı)</label><textarea id="description" name="description" maxlength="600" style="min-height:80px" placeholder="Katılım koşulları, ödülün nasıl teslim edileceği vb."></textarea></div>
    <div class="grid g2">
      <div class="field"><label for="winners">Kazanan sayısı</label><input type="number" id="winners" name="winners" min="1" max="10" value="1"></div>
      <div class="field"><label for="hours">Süre</label><select id="hours" name="hours">{% for h, label in durations.items() %}<option value="{{ h }}" {{ 'selected' if h == 168 }}>{{ label }}</option>{% endfor %}</select></div>
    </div>
    <label class="check field"><input type="checkbox" name="need_follow" value="1" checked> Katılmak için mağazamı takip etmek gereksin</label>
    <label class="check field"><input type="checkbox" name="need_purchase" value="1"> Yalnızca mağazamdan alışveriş yapanlar katılabilsin</label>
    <button class="btn" type="submit" {{ 'disabled' if open_n >= slots }}>Çekilişi yayınla</button>
    {% if open_n >= slots %}<span class="muted small"> Açık çekiliş sınırına ulaştın.</span>{% endif %}
  </form>
</div>
{% endif %}
{% if rows %}
<div class="table-wrap"><table>
  <tr><th>Çekiliş</th><th>Ödül</th><th class="right">Katılımcı</th><th class="right">Kazanan</th><th>Durum</th><th></th></tr>
  {% for gw in rows %}<tr>
    <td><a href="{{ url_for('community.giveaway_view', gid=gw.id) }}"><b>{{ gw.title[:50] }}</b></a><div class="muted small">{% if gw.status == 'open' %}Kalan: {{ remaining(gw.ends_at) }}{% else %}{{ (gw.drawn_at or gw.ends_at)|dt }}{% endif %}</div></td>
    <td>{{ gw.prize[:40] }}</td><td class="right">{{ gw.entry_count }}</td><td class="right">{{ gw.winners }}</td>
    <td><span class="badge b-{{ status[gw.status][1] }}">{{ status[gw.status][0] }}</span></td>
    <td class="actions">{% if gw.status == 'open' %}<div class="mini-form">
      <form method="post" action="{{ url_for('seller.giveaway_draw', gid=gw.id) }}" data-confirm="Kura şimdi çekilsin mi? Çekiliş hemen sonuçlanır.">{{ csrf_field() }}<button class="btn btn-sm" type="submit">Kurayı çek</button></form>
      <form method="post" action="{{ url_for('seller.giveaway_cancel', gid=gw.id) }}" data-confirm="Çekiliş iptal edilsin mi?">{{ csrf_field() }}<button class="btn btn-danger btn-sm" type="submit">İptal</button></form>
    </div>{% endif %}</td>
  </tr>{% endfor %}
</table></div>
{% else %}<div class="card">{{ empty('Henüz çekiliş açmadın', 'Çekilişler mağazana takipçi ve ziyaretçi kazandırır.') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["admin_giveaways.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import pager, empty %}
{% block title %}Çekilişler{% endblock %}
{% block heading %}Çekilişler{% endblock %}
{% block panel %}
<div class="grid g4 mb">
  <div class="stat"><div class="k">Toplam çekiliş</div><div class="v">{{ kpi.n }}</div></div>
  <div class="stat good"><div class="k">Açık</div><div class="v">{{ kpi.open_n }}</div></div>
  <div class="stat"><div class="k">Toplam katılım</div><div class="v">{{ kpi.entries }}</div></div>
  <div class="stat"><div class="k">Özellik</div><div class="v" style="font-size:1.1rem">{{ 'Açık' if enabled else 'Kapalı' }}</div>
    <form method="post" action="{{ url_for('admin.giveaway_setting') }}" class="mt">{{ csrf_field() }}<input type="hidden" name="enabled" value="{{ '0' if enabled else '1' }}"><button class="btn btn-line btn-sm" type="submit">{{ 'Kapat' if enabled else 'Aç' }}</button></form></div>
</div>
<div class="tabs">
  <a class="{{ 'on' if not flt }}" href="{{ url_for('admin.giveaways_admin') }}">Hepsi</a>
  {% for k, v in status.items() %}<a class="{{ 'on' if flt == k }}" href="{{ url_for('admin.giveaways_admin', durum=k) }}">{{ v[0] }}</a>{% endfor %}
</div>
{% if page.rows %}
<div class="table-wrap"><table>
  <tr><th>Çekiliş</th><th>Satıcı</th><th>Ödül</th><th class="right">Katılım</th><th>Bitiş</th><th>Durum</th><th></th></tr>
  {% for gw in page.rows %}<tr>
    <td><a href="{{ url_for('community.giveaway_view', gid=gw.id) }}" target="_blank" rel="noopener"><b>{{ gw.title[:46] }}</b></a><div class="muted small">#{{ gw.id }}{% if gw.need_follow %} &middot; takip şartı{% endif %}{% if gw.need_purchase %} &middot; alışveriş şartı{% endif %}</div></td>
    <td><a href="{{ url_for('admin.user', uid=gw.seller_id) }}">{{ gw.store_name or gw.seller_name }}</a></td>
    <td>{{ gw.prize[:40] }}</td><td class="right">{{ gw.entry_count }}</td><td class="nowrap">{{ gw.ends_at|dt }}</td>
    <td><span class="badge b-{{ status[gw.status][1] }}">{{ status[gw.status][0] }}</span></td>
    <td class="actions">{% if gw.status == 'open' %}<form method="post" action="{{ url_for('admin.giveaway_cancel_admin', gid=gw.id) }}" data-confirm="Çekiliş iptal edilsin mi?">{{ csrf_field() }}<button class="btn btn-danger btn-sm" type="submit">İptal et</button></form>{% endif %}</td>
  </tr>{% endfor %}
</table></div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Çekiliş yok') }}</div>{% endif %}
{% endblock %}
"""
