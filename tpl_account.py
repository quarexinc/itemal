"""Kullanıcı hesabı şablonları (Jinja). Emoji kullanılmaz."""

TEMPLATES = {}

TEMPLATES["account_base.html"] = r"""
{% extends "base.html" %}
{% from "_macros.html" import avatar, ic with context %}
{% block content %}
{% set ep = request.endpoint or '' %}
<div class="container layout">
  <aside class="side">
    <div class="side-user">{{ avatar(me.username, me.avatar) }}<div><b>{{ me.username }}{{ pkg_marks(me.id) }}</b><small>{{ me.email }}</small></div></div>
    <nav>
      <a class="{{ 'on' if ep == 'account' }}" href="{{ url_for('account') }}">{{ ic('home') }}Genel Bakış</a>
      <a class="{{ 'on' if ep == 'balance' }}" href="{{ url_for('balance') }}">{{ ic('download') }}Bakiye Yükle</a>
      <a class="{{ 'on' if ep == 'withdraw' }}" href="{{ url_for('withdraw') }}">{{ ic('upload') }}Para Çek</a>
      <a class="{{ 'on' if ep in ['orders', 'order_detail'] }}" href="{{ url_for('orders') }}">{{ ic('receipt') }}Siparişlerim</a>
      <a class="{{ 'on' if ep == 'site.favorites' }}" href="{{ url_for('site.favorites') }}">{{ ic('heart') }}Favorilerim</a>
      <a class="{{ 'on' if ep == 'transactions' }}" href="{{ url_for('transactions') }}">{{ ic('history') }}Hesap Hareketleri</a>
      <a class="{{ 'on' if ep in ['inbox', 'chat'] }}" href="{{ url_for('inbox') }}">{{ ic('message') }}Mesajlar{% if unread_chat %} <span class="dot-count">{{ unread_chat }}</span>{% endif %}</a>
      <a class="{{ 'on' if ep == 'site.notifications' }}" href="{{ url_for('site.notifications') }}">{{ ic('bell') }}Bildirimler{% if notif_unread %} <span class="dot-count">{{ notif_unread }}</span>{% endif %}</a>
      <a class="{{ 'on' if ep in ['tickets', 'ticket_new', 'ticket_view'] }}" href="{{ url_for('tickets') }}">{{ ic('life-buoy') }}Destek Talepleri{% if answered_tickets %} <span class="dot-count">{{ answered_tickets }}</span>{% endif %}</a>
      <div class="sep">Hesap</div>
      {% if can_sell %}<a href="{{ url_for('seller.dashboard') }}">{{ ic('store') }}Satıcı Paneli</a>{% else %}<a class="{{ 'on' if ep == 'seller_apply' }}" href="{{ url_for('seller_apply') }}">{{ ic('store') }}Satıcı Ol</a>{% endif %}
      <a class="{{ 'on' if ep == 'profile' }}" href="{{ url_for('profile') }}">{{ ic('settings') }}Profil ve Güvenlik</a>
    </nav>
  </aside>
  <section>{% block panel %}{% endblock %}</section>
</div>
{% endblock %}
"""

TEMPLATES["account.html"] = r"""
{% extends "account_base.html" %}
{% from "_macros.html" import badge, empty %}
{% block title %}Hesabım{% endblock %}
{% block panel %}
<div class="balance-hero mb">
  <div><small>Kullanılabilir bakiye</small><div class="amt">{{ me.balance|money }}</div></div>
  <div class="row"><a class="btn" href="{{ url_for('balance') }}">Bakiye Yükle</a><a class="btn" href="{{ url_for('withdraw') }}">Para Çek</a></div>
</div>


<div class="grid g4 mb">
  <div class="stat"><div class="k">Siparişlerim</div><div class="v">{{ stats.orders }}</div></div>
  <div class="stat"><div class="k">Toplam harcama</div><div class="v">{{ stats.spent|money }}</div></div>
  <div class="stat"><div class="k">Bekleyen yükleme</div><div class="v">{{ stats.pending_deposits }}</div></div>
  <div class="stat"><div class="k">Bekleyen çekim</div><div class="v">{{ stats.pending_withdrawals }}</div></div>
</div>

<div class="two-col">
  <div class="card">
    <div class="card-h"><h3>Son siparişler</h3><a href="{{ url_for('orders') }}">Tümü</a></div>
    {% if recent_orders %}<div class="table-wrap"><table>
      <tr><th>No</th><th>İlan</th><th class="right">Tutar</th></tr>
      {% for o in recent_orders %}<tr><td><a href="{{ url_for('order_detail', oid=o.id) }}">#{{ o.id }}</a></td><td>{{ o.listing_title }}</td><td class="right nowrap">{{ o.total|money }}</td></tr>{% endfor %}
    </table></div>{% else %}{{ empty('Henüz siparişin yok') }}{% endif %}
  </div>
  <div class="card">
    <div class="card-h"><h3>Son hareketler</h3><a href="{{ url_for('transactions') }}">Tümü</a></div>
    {% if recent_tx %}<div class="table-wrap"><table>
      <tr><th>Tür</th><th class="right">Tutar</th></tr>
      {% for t in recent_tx %}<tr><td>{{ t.kind|kindlabel }}<div class="muted small">{{ t.created_at|dt }}</div></td><td class="right nowrap {{ 'pos' if t.amount > 0 else 'neg' }}">{{ t.amount|smoney }}</td></tr>{% endfor %}
    </table></div>{% else %}{{ empty('Henüz hareket yok') }}{% endif %}
  </div>
</div>
{% endblock %}
"""

TEMPLATES["balance.html"] = r"""
{% extends "account_base.html" %}
{% from "_macros.html" import badge, empty, ic with context %}
{% block title %}Bakiye Yükle{% endblock %}
{% block panel %}
<div class="page-h"><h1>Bakiye yükle</h1><span class="chip">Bakiyen: {{ me.balance|money }}</span></div>

{% if pay_links %}
<div class="card mb card-method">
  <div class="card-h"><h2>Ödeme linkiyle yükle</h2></div>
  <p class="muted">Bir tutar seç ve <b>Öde</b> düğmesine bas. Ödeme sayfası yeni sekmede açılır; bu sayfada ödemenin durumunu görürsün. Ödemen kontrol edilince tutar bakiyene eklenir.</p>
  <div class="grid g3">
    {% for p in pay_links %}
    <form class="card flat paylink" method="post" action="{{ url_for('paylink.start', lid=p.id) }}" data-paylink data-open="{{ p.url }}">
      {{ csrf_field() }}
      <div class="muted small">{{ p.title }}</div>
      <div class="stat-v" style="font-size:1.6rem;font-weight:800;margin:6px 0">{{ p.amount|money }}</div>
      {% if p.description %}<p class="muted small">{{ p.description }}</p>{% endif %}
      <button class="btn" type="submit">Öde</button>
      <div class="notice bad small mt" data-plerr hidden></div>
    </form>
    {% endfor %}
  </div>
</div>
{% endif %}

{% if not methods %}
{% if not pay_links %}<div class="notice warn">Şu anda aktif bir yükleme yöntemi yok. Lütfen daha sonra tekrar dene ya da <a href="{{ url_for('ticket_new') }}">destek talebi</a> oluştur.</div>{% endif %}
{% else %}
<form method="post" action="{{ url_for('balance') }}" class="pm-form mb" id="depform" data-min-default="{{ min_deposit }}">
  {{ csrf_field() }}
  <div class="card">
    <div class="card-h"><h2>1. Yükleme yöntemini seç</h2><span class="muted small">{{ methods|length }} yöntem</span></div>
    <div class="pm-grid" role="radiogroup" aria-label="Yükleme yöntemi">
      {% for m in methods %}{% set mn = [m.min_amount, min_deposit]|max %}
      <label class="pm-card{{ ' on' if m.id == pre_method }}" style="--c:{{ m.color or '#7c5cff' }}">
        <input type="radio" name="method_id" value="{{ m.id }}" {{ 'checked' if m.id == pre_method }} required
          data-min="{{ mn }}" data-max="{{ m.max_amount }}" data-bonus="{{ m.bonus_percent }}">
        <span class="pm-ico">{{ ic(pm_clean_icon(m.icon, m.kind)) }}</span>
        <span class="pm-body">
          <b>{{ m.name }}</b>
          <small>{% if m.eta %}{{ m.eta }} &middot; {% endif %}Min. {{ mn|money }}{% if m.max_amount %} &middot; Maks. {{ m.max_amount|money }}{% endif %}</small>
        </span>
        {% if m.bonus_percent %}<span class="pm-tag bonus">%{{ '%g'|format(m.bonus_percent) }} bonus</span>{% elif m.badge %}<span class="pm-tag">{{ m.badge }}</span>{% endif %}
      </label>
      {% endfor %}
    </div>
  </div>

  <div class="card mt">
    <div class="card-h"><h2>2. Ödeme bilgileri</h2><span class="muted small">Ödemeyi bu bilgilere gönder</span></div>
    {% for m in methods %}
    <div class="pm-detail" data-pm="{{ m.id }}" {{ 'hidden' if m.id != pre_method }}>
      <div class="pm-lines" id="pm{{ m.id }}">
        {% for line in m.details.split('\n') if line.strip() %}{% set parts = line.split(':', 1) %}
        <div class="pm-line">
          {% if parts|length > 1 and parts[1].strip() %}<span class="pm-k">{{ parts[0] }}</span><code class="pm-v">{{ parts[1].strip() }}</code>
          <button type="button" class="btn btn-ghost btn-sm" data-copy="{{ parts[1].strip() }}">{{ ic('copy') }}Kopyala</button>
          {% else %}<span class="pm-v plain">{{ line }}</span>{% endif %}
        </div>
        {% endfor %}
      </div>
      <div class="row mt"><button type="button" class="btn btn-ghost btn-sm" data-copy="#pm{{ m.id }}">{{ ic('copy') }}Tüm bilgileri kopyala</button></div>
      {% if m.instructions %}<div class="pm-note">{{ ic('info') }}<span>{{ m.instructions }}</span></div>{% endif %}
    </div>
    {% endfor %}
  </div>

  <div class="card mt">
    <div class="card-h"><h2>3. Ödeme bildirimi</h2></div>
    <p class="muted">Ödemeyi gönderdikten sonra tutarı ve dekont bilgisini yaz. Kontrol edilince tutar bakiyene eklenir.</p>
    <div class="form-row">
      <div class="field"><label for="amount">Gönderdiğin tutar (TL)</label><input type="text" inputmode="decimal" id="amount" name="amount" required placeholder="250,00" value="{{ pre_amount|plain if pre_amount }}">
        <div class="quick">{% for v in (50, 100, 250, 500, 1000) %}<button type="button" data-fill="{{ v }}" data-target="#amount">{{ v }} TL</button>{% endfor %}</div></div>
      <div class="field"><label for="reference">Dekont / işlem no veya gönderen adı</label><input type="text" id="reference" name="reference" required maxlength="120"></div>
    </div>
    <div class="field"><label for="note">Not (isteğe bağlı)</label><input type="text" id="note" name="note" maxlength="300"></div>
    <div class="pm-sum" id="pm-sum" hidden>
      <div><span>Gönderilecek</span><b id="pm-s-amt">-</b></div>
      <div class="bonus-row" hidden><span>Yükleme bonusu</span><b id="pm-s-bonus">-</b></div>
      <div class="tot"><span>Bakiyene eklenecek</span><b id="pm-s-tot">-</b></div>
    </div>
    <div class="pm-limit small muted" id="pm-limit"></div>
    <button class="btn" type="submit">{{ ic('send') }}Bildirimi gönder</button>
  </div>
</form>
{% endif %}

<div class="card">
  <h2>Yükleme geçmişi</h2>
  {% if history %}<div class="table-wrap"><table>
    <tr><th>No</th><th>Tarih</th><th>Yöntem</th><th class="right">Tutar</th><th>Durum</th><th>Not</th></tr>
    {% for d in history %}<tr><td>#{{ d.id }}</td><td>{{ d.created_at|dt }}</td><td>{{ d.method_name }}</td><td class="right nowrap {{ 'pos' if d.status == 'approved' }}">{{ d.amount|smoney if d.status == 'approved' else d.amount|money }}</td><td>{{ badge(d.status) }}</td><td class="muted small">{{ d.admin_note }}{% if d.link_id or d.link_url %} <a href="{{ url_for('paylink.wait', did=d.id) }}">Durum</a>{% endif %}</td></tr>{% endfor %}
  </table></div>{% else %}{{ empty('Henüz yükleme bildirimin yok') }}{% endif %}
</div>
{% endblock %}
"""

TEMPLATES["withdraw.html"] = r"""
{% extends "account_base.html" %}
{% from "_macros.html" import badge, empty %}
{% block title %}Para Çek{% endblock %}
{% block panel %}
<div class="page-h"><h1>Para çek</h1></div>
<div class="grid g3 mb">
  <div class="stat good"><div class="k">Çekilebilir tutar</div><div class="v">{{ available|money }}</div><div class="s">Toplam bakiye: {{ me.balance|money }}</div></div>
  <div class="stat"><div class="k">Minimum çekim</div><div class="v">{{ min_w|money }}</div></div>
  <div class="stat"><div class="k">İşlem kesintisi</div><div class="v">%{{ fee_rate }}</div></div>
</div>
{% if earnings_only %}<div class="notice">Güvenlik gereği yalnızca <b>satış kazançların</b> çekilebilir. Yüklediğin bakiye site içi alışveriş içindir.</div>{% endif %}

<div class="card mb">
  <form method="post" action="{{ url_for('withdraw') }}" data-confirm="Çekim talebi oluşturulsun mu? Tutar bakiyenden hemen düşülür.">
    {{ csrf_field() }}
    <div class="form-row">
      <div class="field"><label for="method">Yöntem</label><select id="method" name="method" data-last='{{ last_accounts|tojson }}'>{% for m in methods %}<option>{{ m }}</option>{% endfor %}</select></div>
      <div class="field"><label for="amount">Tutar (TL)</label><input type="text" inputmode="decimal" id="amount" name="amount" required placeholder="{{ min_w|plain }}">
        <div class="quick"><button type="button" data-fill="{{ available|plain }}" data-target="#amount">Tümü</button></div></div>
    </div>
    <div class="field"><label for="account_info">IBAN / Papara no / cüzdan adresi</label><textarea id="account_info" name="account_info" required maxlength="300" style="min-height:80px"></textarea>
      <div class="hint">Hesap sahibi adı, kimlik doğrulamandaki adla aynı olmalıdır. Önceki çekimlerindeki hesap otomatik doldurulur.</div></div>
    <button class="btn" type="submit">Çekim Talebi Oluştur</button>
  </form>
</div>

<div class="card">
  <h2>Çekim geçmişi</h2>
  {% if history %}<div class="table-wrap"><table>
    <tr><th>No</th><th>Tarih</th><th>Yöntem</th><th class="right">Tutar</th><th class="right">Kesinti</th><th class="right">Net</th><th>Durum</th></tr>
    {% for w in history %}<tr><td>#{{ w.id }}</td><td>{{ w.created_at|dt }}</td><td>{{ w.method }}</td><td class="right nowrap">{{ w.amount|money }}</td><td class="right nowrap">{{ w.fee|money }}</td><td class="right nowrap">{{ w.net|money }}</td><td>{{ badge(w.status) }}{% if w.admin_note %}<div class="muted small">{{ w.admin_note }}</div>{% endif %}</td></tr>{% endfor %}
  </table></div>{% else %}{{ empty('Henüz çekim talebin yok') }}{% endif %}
</div>
{% endblock %}
"""

TEMPLATES["orders.html"] = r"""
{% extends "account_base.html" %}
{% from "_macros.html" import pager, empty %}
{% block title %}Siparişlerim{% endblock %}
{% block panel %}
<div class="page-h"><h1>Siparişlerim</h1></div>
{% if page.rows %}
<div class="table-wrap"><table>
  <tr><th>No</th><th>Tarih</th><th>İlan</th><th>Satıcı</th><th class="right">Adet</th><th class="right">Tutar</th><th>Durum</th><th></th></tr>
  {% for o in page.rows %}<tr>
    <td><a href="{{ url_for('order_detail', oid=o.id) }}">#{{ o.id }}</a></td><td>{{ o.created_at|dt }}</td><td><a href="{{ url_for('listing_detail', lid=o.listing_id) }}">{{ o.listing_title }}</a></td>
    <td><a href="{{ url_for('storefront', username=o.seller_name) }}">{{ o.seller_name }}</a>{{ pkg_marks(o.seller_id) }}</td><td class="right">{{ o.quantity }}</td><td class="right nowrap">{{ o.total|money }}</td>
    <td><span class="badge b-{{ o.escrow_status|sclass }}">{{ o.escrow_status|slabel }}</span></td>
    <td class="actions"><a class="btn btn-ghost btn-sm" href="{{ url_for('order_detail', oid=o.id) }}">{{ 'Onayla' if o.escrow_status == 'held' else 'Detay' }}</a></td>
  </tr>{% endfor %}
</table></div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Henüz sipariş vermedin', 'İlanlara göz atarak ilk alışverişini yapabilirsin.') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["order.html"] = r"""
{% extends "account_base.html" %}
{% from "_macros.html" import stars %}
{% block title %}Sipariş #{{ o.id }}{% endblock %}
{% block panel %}
<div class="page-h"><h1>Sipariş #{{ o.id }}</h1><a class="btn btn-ghost btn-sm" href="{{ url_for('orders') if is_buyer else url_for('seller.sales') }}">Geri dön</a></div>

<div class="card mb">
  <dl class="kv">
    <dt>İlan</dt><dd><a href="{{ url_for('listing_detail', lid=o.listing_id) }}">{{ o.listing_title }}</a></dd>
    <dt>Tarih</dt><dd>{{ o.created_at|dt }}</dd>
    <dt>{{ 'Satıcı' if is_buyer else 'Alıcı' }}</dt><dd>{{ o.seller_name if is_buyer else o.buyer_name }}{% if is_buyer %}{{ pkg_marks(o.seller_id) }}{% endif %}</dd>
    <dt>Adet x birim fiyat</dt><dd>{{ o.quantity }} x {{ o.unit_price|money }}</dd>
    <dt>Toplam</dt><dd>{{ o.total|money }}</dd>
    {% if is_buyer and o.discount %}<dt>Kupon{% if o.coupon_code %} ({{ o.coupon_code }}){% endif %}</dt><dd class="pos">-{{ o.discount|money }}</dd><dt>Ödenen</dt><dd>{{ (o.total - o.discount)|money }}</dd>{% endif %}
    {% if not is_buyer %}<dt>Komisyon (%{{ o.commission_rate }})</dt><dd>{{ o.commission|money }}</dd><dt>Net kazancın</dt><dd>{{ o.seller_earning|money }}</dd>{% endif %}
  </dl>
</div>

<div class="card mb escrow-{{ o.escrow_status }}">
  <div class="card-h"><h2>Ödeme durumu</h2><span class="badge b-{{ o.escrow_status|sclass }}">{{ o.escrow_status|slabel }}</span></div>
  {% if o.escrow_status == 'held' %}
    {% if is_buyer %}
    <p class="muted">Ödemen emanette; satıcıya henüz aktarılmadı. Kodları kontrol edip çalıştığından emin olunca siparişi onayla. Onay vermezsen tutar <b>{{ o.release_at|dt }}</b> tarihinde otomatik aktarılır.</p>
    <div class="row">
      <form method="post" action="{{ url_for('trust.order_confirm', oid=o.id) }}" data-confirm="Kodlar sorunsuz çalıştı, ödeme satıcıya aktarılsın mı?">{{ csrf_field() }}<button class="btn" type="submit">Siparişi onayla</button></form>
      <details class="report-box inline"><summary>Sorun var</summary>
        <form method="post" action="{{ url_for('trust.order_dispute', oid=o.id) }}">{{ csrf_field() }}
          <div class="field"><label>Sorun nedir?</label><select name="reason" required><option value="">Seç</option>{% for r in REASONS['order'] %}<option>{{ r }}</option>{% endfor %}</select></div>
          <div class="field"><label>Ayrıntı</label><textarea name="detail" maxlength="600"></textarea></div>
          <button class="btn btn-danger btn-sm" type="submit">İtiraz et</button>
        </form>
      </details>
    </div>
    {% else %}
    <p class="muted">{{ o.seller_earning|money }} alıcı onayı bekliyor. Alıcı onaylayınca ya da <b>{{ o.release_at|dt }}</b> tarihinde bakiyene geçecek.</p>
    {% endif %}
  {% elif o.escrow_status == 'disputed' %}
    <p class="muted">Bu sipariş için itiraz açıldı. Yönetim ekibi inceliyor; tutar sonuçlanana kadar bloke kalır.</p>
  {% elif o.escrow_status == 'refunded' %}
    <p class="muted">Sipariş iade edildi.</p>
  {% else %}
    <p class="muted">{{ 'Siparişi onayladın; ödeme satıcıya aktarıldı.' if is_buyer and o.confirmed_at else 'Ödeme tamamlandı.' }}</p>
  {% endif %}
</div>

{% if is_buyer %}
<div class="card mb">
  <div class="card-h"><h2>Kodların</h2>{% if codes|length > 1 %}<button type="button" class="btn btn-ghost btn-sm" data-copy=".code-val">Hepsini kopyala</button>{% endif %}</div>
  {% for c in codes %}
  <div class="codebox"><code class="code-val" id="code{{ loop.index }}">{{ c.code }}</code><button type="button" class="btn btn-ghost btn-sm" data-copy="#code{{ loop.index }}">Kopyala</button></div>
  {% endfor %}
  <p class="muted small mt">Kodları başkalarıyla paylaşma. Bu sayfaya istediğin zaman Siparişlerim bölümünden ulaşabilirsin.</p>
</div>

<div class="card mb">
  <div class="card-h"><h2>Değerlendirme</h2></div>
  {% if review %}
    <div class="review">
      <div class="who">{{ stars(review.rating) }}<span class="muted small">{{ review.created_at|dt }}</span>{% if review.is_hidden %}<span class="badge b-bad">Yönetim tarafından gizlendi</span>{% endif %}</div>
      <div class="pre">{{ review.comment or 'Yorum yazmadın.' }}</div>
      {% if review.seller_reply %}<div class="reply"><b>Satıcı yanıtı:</b> {{ review.seller_reply }}</div>{% endif %}
    </div>
  {% else %}
    <p class="muted">Siparişinden memnun kaldın mı? Puanın diğer alıcılara yardımcı olur.</p>
    <form method="post" action="{{ url_for('review_create', oid=o.id) }}">
      {{ csrf_field() }}
      <div class="field"><label for="rating">Puan</label>
        <select id="rating" name="rating" required><option value="">Seç</option><option value="5">5 - Mükemmel</option><option value="4">4 - İyi</option><option value="3">3 - Orta</option><option value="2">2 - Kötü</option><option value="1">1 - Çok kötü</option></select></div>
      <div class="field"><label for="comment">Yorumun (isteğe bağlı)</label><textarea id="comment" name="comment" maxlength="500" placeholder="Teslimat hızı, satıcı iletişimi ..."></textarea></div>
      <button class="btn" type="submit">Değerlendirmeyi Gönder</button>
    </form>
  {% endif %}
</div>

<div class="row">
  <form method="post" action="{{ url_for('chat_start', lid=o.listing_id) }}">{{ csrf_field() }}<button class="btn btn-line" type="submit">Satıcıya mesaj yaz</button></form>
  <a class="btn btn-line" href="{{ url_for('ticket_new', siparis=o.id) }}">Bu sipariş için destek talebi aç</a>
</div>
{% else %}
<div class="notice">Kodlar alıcıya teslim edildi; güvenlik nedeniyle burada gösterilmez.</div>
{% endif %}
{% endblock %}
"""

TEMPLATES["transactions.html"] = r"""
{% extends "account_base.html" %}
{% from "_macros.html" import pager, empty %}
{% block title %}Hesap Hareketleri{% endblock %}
{% block panel %}
<div class="page-h"><h1>Hesap hareketleri</h1><span class="chip">Bakiye: {{ me.balance|money }}</span></div>
{% if page.rows %}
<div class="table-wrap"><table>
  <tr><th>Tarih</th><th>Tür</th><th>Açıklama</th><th class="right">Tutar</th><th class="right">Bakiye</th></tr>
  {% for t in page.rows %}<tr><td class="nowrap">{{ t.created_at|dt }}</td><td>{{ t.kind|kindlabel }}</td><td class="muted">{{ t.description }}</td><td class="right nowrap {{ 'pos' if t.amount > 0 else 'neg' }}">{{ t.amount|smoney }}</td><td class="right nowrap">{{ t.balance_after|money }}</td></tr>{% endfor %}
</table></div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Henüz hareket yok') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["kyc.html"] = r"""
{% extends "account_base.html" %}
{% block title %}Kimlik Doğrulama{% endblock %}
{% block panel %}
<div class="page-h"><h1>Kimlik doğrulama</h1><span class="badge b-{{ me.kyc_status|sclass }}">{{ me.kyc_status|slabel }}</span></div>

<p class="muted mb">Ödemenin doğru kişiye yapılabilmesi için bilgilerini bir kez doğruluyoruz. Onaylanınca çekim talebini oluşturabilirsin.</p>
{% if me.kyc_status == 'approved' %}
<div class="notice ok">Bilgilerin doğrulandı. <a href="{{ url_for('withdraw') }}">Çekim sayfasına dön</a>.</div>
{% elif me.kyc_status == 'pending' %}
<div class="notice">Başvurun inceleniyor. Sonuç hesabına yansıyacak; genellikle kısa sürede tamamlanır.</div>
{% else %}
{% if last and last.status == 'rejected' %}<div class="notice bad"><b>Önceki başvurun reddedildi:</b> {{ last.admin_note or 'Bilgiler doğrulanamadı.' }}<br>Aşağıdaki bilgilerle yeniden başvurabilirsin.</div>{% endif %}
<div class="card mb">
  <h3 class="mt0">Görsel kalitesi için ipuçları</h3>
  <ul class="muted">
    <li>Kimliğin tamamı çerçevede, dört köşesi görünür olsun.</li>
    <li>Işık yeterli, yansıma ve parlama olmasın; yazılar net okunsun.</li>
    <li>Selfie'de yüzün ve kimlik aynı karede, kimlik üzerindeki yazılar okunabilir olsun.</li>
    <li>Düzenlenmiş, ekran görüntüsü veya kopya görseller reddedilir. Görseller yalnızca doğrulama için kullanılır ve konum bilgisi silinerek saklanır.</li>
  </ul>
</div>
<div class="card">
  <form method="post" action="{{ url_for('kyc') }}" enctype="multipart/form-data">
    {{ csrf_field() }}
    <div class="form-row">
      <div class="field"><label for="doc_type">Belge türü</label><select id="doc_type" name="doc_type"><option value="kimlik">T.C. kimlik kartı</option><option value="ehliyet">Sürücü belgesi</option></select></div>
      <div class="field"><label for="full_name">Ad soyad (belgedeki gibi)</label><input type="text" id="full_name" name="full_name" required maxlength="80" autocomplete="name"></div>
    </div>
    <div class="form-row">
      <div class="field"><label for="id_number">T.C. kimlik numarası</label><input type="text" id="id_number" name="id_number" required inputmode="numeric" pattern="[0-9]{11}" maxlength="11"></div>
      <div class="field"><label for="birth_date">Doğum tarihi</label><input type="date" id="birth_date" name="birth_date" required></div>
    </div>
    <div class="form-row">
      <div class="field"><label for="id_front">Belgenin ön yüzü</label><input type="file" id="id_front" name="id_front" accept="image/jpeg,image/png,image/webp" required></div>
      <div class="field"><label for="id_back">Belgenin arka yüzü</label><input type="file" id="id_back" name="id_back" accept="image/jpeg,image/png,image/webp" required></div>
    </div>
    <div class="field"><label for="selfie">Belgeyle birlikte selfie</label><input type="file" id="selfie" name="selfie" accept="image/jpeg,image/png,image/webp" required><div class="hint">JPG, PNG veya WEBP. Her görsel en fazla 8 MB, en az 300 piksel.</div></div>
    <button class="btn" type="submit">Başvuruyu Gönder</button>
  </form>
</div>
{% endif %}
{% endblock %}
"""

TEMPLATES["seller_apply.html"] = r"""
{% extends "account_base.html" %}
{% from "_macros.html" import badge %}
{% block title %}Satıcı Ol{% endblock %}
{% block panel %}
<div class="page-h"><h1>Satıcı başvurusu</h1></div>
{% if pending %}
<div class="notice">Satıcı başvurun inceleniyor. Sonuç hesabına yansıyacak.</div>
<div class="card"><dl class="kv"><dt>Mağaza adı</dt><dd>{{ last.store_name }}</dd><dt>Başvuru tarihi</dt><dd>{{ last.created_at|dt }}</dd></dl></div>
{% else %}
{% if last and last.status == 'rejected' %}<div class="notice bad"><b>Önceki başvurun reddedildi:</b> {{ last.admin_note or 'Uygun bulunmadı.' }} Bilgilerini düzeltip tekrar başvurabilirsin.</div>{% endif %}
<div class="card mb">
  <h3 class="mt0">Satıcılar için</h3>
  <ul class="muted">
    <li>Onaylanınca ilan verebilir, stok yükleyebilir, satış ve kazanç raporlarını görebilirsin.</li>
    <li>Satış başına komisyon alınır (genel oran %{{ cfg.commission_percent }}); ilan verirken net kazancını görürsün.</li>
    <li>Yorumlar ve satış adedin doğrultusunda "Güvenilir Satıcı" gibi rozetler kazanırsın.</li>
    <li>Yalnızca gerçek, kullanılmamış kodlar satılabilir; ihlal hesabın kapatılmasına yol açar.</li>
  </ul>
</div>
<div class="card">
  <form method="post" action="{{ url_for('seller_apply') }}">
    {{ csrf_field() }}
    <div class="field"><label for="store_name">Mağaza adı</label><input type="text" id="store_name" name="store_name" value="{{ form.store_name }}" required minlength="3" maxlength="40"></div>
    <div class="field"><label for="description">Mağazanı tanıt</label><textarea id="description" name="description" required minlength="20" maxlength="500">{{ form.description }}</textarea><div class="hint">Ne sattığını ve kodları nereden temin ettiğini kısaca anlat (en az 20 karakter).</div></div>
    <div class="field"><label for="experience">Deneyimin (isteğe bağlı)</label><textarea id="experience" name="experience" maxlength="500" style="min-height:80px">{{ form.experience }}</textarea></div>
    <label class="check field"><input type="checkbox" name="agree" value="1" required> <span>Satıcı kurallarını okudum; yalnızca gerçek ve kullanılmamış kodlar satacağımı kabul ediyorum.</span></label>
    <button class="btn" type="submit">Başvuruyu Gönder</button>
  </form>
</div>
{% endif %}
{% endblock %}
"""

TEMPLATES["profile.html"] = r"""
{% extends "account_base.html" %}
{% from "_macros.html" import avatar, badge_list %}
{% block title %}Profil ve Güvenlik{% endblock %}
{% block panel %}
<div class="page-h"><h1>Profil ve güvenlik</h1></div>
<div class="card mb">
  <div class="store-head">
    {{ avatar(me.username, me.avatar, 'lg') }}
    <div style="flex:1;min-width:240px">
      <h2 style="margin-bottom:.2em">{{ me.username }}{{ pkg_marks(me.id) }}</h2>
      <div class="muted small mb">{{ me.email }} &middot; Üyelik: {{ me.created_at|dt(false) }}</div>
      {{ badge_list(my_badges) }}
    </div>
  </div>
  <hr>
  <form method="post" action="{{ url_for('profile') }}" enctype="multipart/form-data" class="row">
    {{ csrf_field() }}<input type="hidden" name="action" value="avatar">
    <div class="field" style="flex:1;min-width:240px;margin:0"><label for="avatar">Profil fotoğrafı</label><input type="file" id="avatar" name="avatar" accept="image/jpeg,image/png,image/webp" required></div>
    <button class="btn btn-sm" type="submit">Yükle</button>
  </form>
  {% if me.avatar %}<form method="post" action="{{ url_for('profile') }}" class="mt">{{ csrf_field() }}<input type="hidden" name="action" value="avatar_remove"><button class="link-btn link-danger" type="submit">Fotoğrafı kaldır</button></form>{% endif %}
</div>

<div class="two-col">
  <div class="card">
    <h3 class="mt0">İletişim</h3>
    <form method="post" action="{{ url_for('profile') }}">
      {{ csrf_field() }}<input type="hidden" name="action" value="phone">
      <div class="field"><label for="phone">Telefon</label><input type="tel" id="phone" name="phone" value="{{ me.phone }}" maxlength="20" placeholder="+90 5xx xxx xx xx"></div>
      <button class="btn btn-sm" type="submit">Kaydet</button>
    </form>
  </div>
  <div class="card">
    <h3 class="mt0">Şifre değiştir</h3>
    <form method="post" action="{{ url_for('profile') }}">
      {{ csrf_field() }}<input type="hidden" name="action" value="password">
      <div class="field"><label for="current">Mevcut şifre</label><input type="password" id="current" name="current" required autocomplete="current-password"></div>
      <div class="field"><label for="new">Yeni şifre</label><input type="password" id="new" name="new" required minlength="8" autocomplete="new-password"></div>
      <div class="field"><label for="new2">Yeni şifre (tekrar)</label><input type="password" id="new2" name="new2" required minlength="8" autocomplete="new-password"></div>
      <button class="btn btn-sm" type="submit">Şifreyi Güncelle</button>
    </form>
  </div>
</div>

{% set sec = sec_summary() %}
<div class="mt" id="guvenlik">
  <div class="page-h"><h2>Güvenlik</h2></div>
  <div class="two-col">
    <div class="card">
      <h3 class="mt0">İki adımlı doğrulama</h3>
      <div class="sec-stat">
        <span class="badge {{ 'b-ok' if sec.twofa else 'b-warn' }}">{{ 'Açık' if sec.twofa else 'Kapalı' }}</span>
        {% if sec.twofa %}<span class="muted small">Kalan yedek kod: {{ sec.backups }}</span>{% endif %}
      </div>
      <p class="muted small">Girişte şifrene ek olarak doğrulama uygulamandaki (Google Authenticator, Authy vb.) 6 haneli kod istenir. Şifren çalınsa bile hesabına girilemez.{% if cfg.require_seller_2fa == '1' and not sec.twofa %} <b>Satıcı paneli için bu özellik zorunludur.</b>{% endif %}</p>
      <a class="btn btn-sm" href="{{ url_for('accsec.twofa') }}">{{ 'Yönet' if sec.twofa else 'Etkinleştir' }}</a>
    </div>
    <div class="card">
      <h3 class="mt0">Oturumlar</h3>
      <p class="muted small">Başka bir cihazda açık kalan oturumların varsa ya da hesabından şüphelendiysen tüm cihazlardan çıkış yap. Bu cihazdaki oturumun açık kalır. Şifreni değiştirdiğinde de diğer oturumlar kapanır.</p>
      <form method="post" action="{{ url_for('accsec.logout_all') }}" data-confirm="Diğer tüm cihazlardaki oturumlar kapatılsın mı?">{{ csrf_field() }}<button class="btn btn-sm btn-ghost" type="submit">Tüm cihazlardan çıkış yap</button></form>
    </div>
  </div>
  <div class="card mt">
    <h3 class="mt0">Son girişler</h3>
    {% if sec.failed_24h %}<div class="notice warn small">Son 24 saatte hesabına {{ sec.failed_24h }} başarısız giriş denemesi yapıldı. Sen yapmadıysan şifreni değiştir ve iki adımlı doğrulamayı aç.</div>{% endif %}
    {% if sec.events %}
    <div class="table-wrap"><table class="sec-table">
      <tr><th>Tarih</th><th>IP</th><th>Tarayıcı</th></tr>
      {% for e in sec.events %}<tr><td>{{ e.created_at|dt }}</td><td>{{ e.ip|maskip }}</td><td>{{ e.agent|uasum }}</td></tr>{% endfor %}
    </table></div>
    {% else %}<p class="muted small">Henüz giriş kaydı yok.</p>{% endif %}
    <p class="muted small mt">IP adresleri güvenlik için kısmen gizlenir. Tanımadığın bir giriş görürsen şifreni değiştir.</p>
  </div>
</div>
{% endblock %}
"""

TEMPLATES["profile_2fa.html"] = r"""
{% extends "account_base.html" %}
{% block title %}İki Adımlı Doğrulama{% endblock %}
{% block panel %}
<div class="page-h"><h1>İki adımlı doğrulama</h1><a class="btn btn-ghost btn-sm" href="{{ url_for('profile') }}#guvenlik">Profil ve güvenlik</a></div>
{% if codes %}
<div class="card">
  <h3 class="mt0">Yedek kodların</h3>
  <div class="notice warn">Bu kodlar yalnızca <b>bir kez</b> gösterilir. Telefonuna erişemezsen her kod bir kere giriş yapmanı sağlar. Güvenli bir yere kaydet.</div>
  <div class="backup-codes">{% for c in codes %}<code>{{ c }}</code>{% endfor %}</div>
  <a class="btn btn-sm" href="{{ url_for('profile') }}#guvenlik">Kodları kaydettim</a>
</div>
{% elif enabled %}
<div class="two-col">
  <div class="card">
    <h3 class="mt0">Yedek kodları yenile</h3>
    <p class="muted small">Kalan yedek kod: <b>{{ backups }}</b>. Yenilersen eskileri geçersiz olur.</p>
    <form method="post" action="{{ url_for('accsec.twofa') }}">
      {{ csrf_field() }}<input type="hidden" name="action" value="regen">
      <div class="field"><label for="rg_pw">Şifre</label><input type="password" id="rg_pw" name="password" required autocomplete="current-password"></div>
      <div class="field"><label for="rg_code">Doğrulama uygulamasındaki kod</label><input type="text" id="rg_code" name="code" required inputmode="numeric" maxlength="8" autocomplete="one-time-code"></div>
      <button class="btn btn-sm" type="submit">Yeni Kodlar Oluştur</button>
    </form>
  </div>
  <div class="card">
    <h3 class="mt0">İki adımlı doğrulamayı kapat</h3>
    <p class="muted small">Hesabın yalnızca şifreyle korunur. Şifre ve doğrulama kodu (ya da yedek kod) gerekir.</p>
    <form method="post" action="{{ url_for('accsec.twofa') }}" data-confirm="İki adımlı doğrulama kapatılsın mı?">
      {{ csrf_field() }}<input type="hidden" name="action" value="disable">
      <div class="field"><label for="ds_pw">Şifre</label><input type="password" id="ds_pw" name="password" required autocomplete="current-password"></div>
      <div class="field"><label for="ds_code">Kod veya yedek kod</label><input type="text" id="ds_code" name="code" required maxlength="16" autocomplete="one-time-code"></div>
      <button class="btn btn-sm btn-ghost" type="submit">Kapat</button>
    </form>
  </div>
</div>
{% else %}
<div class="card">
  <h3 class="mt0">1. Doğrulama uygulamanı bağla</h3>
  <p class="muted">Google Authenticator, Microsoft Authenticator, Authy gibi bir uygulamada yeni hesap ekle ve QR kodu okut. QR okutamazsan anahtarı elle gir.</p>
  <div class="qr-box">
    {% if qr %}<div>{{ qr }}</div>{% endif %}
    <div style="flex:1;min-width:220px">
      <div class="muted small mb">Kurulum anahtarı (zaman tabanlı, 6 hane)</div>
      <div class="qr-key">{{ secret_text }}</div>
    </div>
  </div>
  <h3>2. Kodu doğrula</h3>
  <form method="post" action="{{ url_for('accsec.twofa') }}">
    {{ csrf_field() }}<input type="hidden" name="action" value="enable">
    <div class="field" style="max-width:260px"><label for="code">Uygulamadaki 6 haneli kod</label><input class="code-input" type="text" id="code" name="code" required inputmode="numeric" maxlength="8" autocomplete="one-time-code" autofocus></div>
    <button class="btn" type="submit">Etkinleştir</button>
  </form>
</div>
{% endif %}
{% endblock %}
"""

TEMPLATES["login_2fa.html"] = r"""
{% extends "base.html" %}
{% from "_macros.html" import ic with context %}
{% block title %}İki Adımlı Doğrulama{% endblock %}
{% block content %}
<div class="container">
  <div class="auth-wrap">
    <div class="auth-art">
      <div><a class="brand" href="{{ url_for('index') }}"><span class="brand-mark">{{ site_name[:1]|upper }}</span>{{ site_name }}</a></div>
      <div>
        <h2>Bir adım daha.</h2>
        <ul>
          <li>{{ ic('shield-check') }}<span>Hesabın iki adımlı doğrulamayla korunuyor</span></li>
          <li>{{ ic('bolt') }}<span>Kod 30 saniyede bir yenilenir</span></li>
        </ul>
      </div>
    </div>
    <div class="auth-form">
      <h1>Doğrulama kodu</h1>
      <p class="muted">Doğrulama uygulamandaki 6 haneli kodu gir. Telefonuna erişemiyorsan bir yedek kod kullanabilirsin.</p>
      <form method="post" action="{{ url_for('accsec.login_2fa') }}">
        {{ csrf_field() }}
        <div class="field"><label for="code">Kod veya yedek kod</label><input class="code-input" type="text" id="code" name="code" required autofocus maxlength="16" autocomplete="one-time-code"></div>
        <button class="btn btn-block btn-lg" type="submit">Doğrula ve Giriş Yap</button>
      </form>
      <p class="center muted mt"><a href="{{ url_for('login') }}">Girişe dön</a></p>
    </div>
  </div>
</div>
{% endblock %}
"""

TEMPLATES["inbox.html"] = r"""
{% extends "account_base.html" %}
{% from "_macros.html" import avatar, empty %}
{% block title %}Mesajlar{% endblock %}
{% block panel %}
<div class="page-h"><h1>Mesajlar</h1></div>
{% if convs %}
<div class="card" style="padding:0">
  {% for it in convs %}
  <a class="conv" href="{{ url_for('chat', cid=it.c.id) }}">
    {{ avatar(it.other, it.other_avatar) }}
    <div class="grow">
      <div><b>{{ it.other }}</b>{% if it.c.buyer_id == me.id %}{{ pkg_marks(it.c.seller_id) }}{% endif %} <span class="muted small">&middot; {{ 'Satıcı' if it.c.buyer_id == me.id else 'Alıcı' }}</span></div>
      <div class="muted small ellipsis">{{ it.c.listing_title }}</div>
      <div class="ellipsis small">{% if it.last %}{{ 'Sen: ' if it.last.sender_id == me.id }}{{ it.last.body }}{% else %}<span class="muted">Henüz mesaj yok</span>{% endif %}</div>
    </div>
    <div class="right small muted nowrap">{{ it.c.last_message_at|dt }}{% if it.unread %}<div class="mt"><span class="dot-count">{{ it.unread }}</span></div>{% endif %}</div>
  </a>
  {% endfor %}
</div>
{% else %}<div class="card">{{ empty('Henüz mesajın yok', 'Bir ilan sayfasındaki "Satıcıya mesaj yaz" düğmesiyle konuşma başlatabilirsin.') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["chat.html"] = r"""
{% extends "account_base.html" %}
{% from "_macros.html" import avatar, badge_list %}
{% block title %}Mesajlar{% endblock %}
{% block panel %}
<div class="card chat">
  <div class="chat-head">
    {{ avatar(other.username, other.avatar) }}
    <div style="flex:1;min-width:200px">
      <div><b>{{ (other.store_name or other.username) if other.id == conv.seller_id else other.username }}</b>{% if other.id == conv.seller_id %}{{ pkg_marks(other.id) }}{% endif %} <span class="muted small">&middot; {{ 'Satıcı' if other.id == conv.seller_id else 'Alıcı' }}</span></div>
      <a class="small" href="{{ url_for('listing_detail', lid=conv.listing_id) }}">{{ conv.listing_title }}</a>
    </div>
    {{ badge_list(other_badges) }}
    <a class="btn btn-ghost btn-sm" href="{{ url_for('inbox') }}">Tüm mesajlar</a>
  </div>
  <div class="chat-log" data-poll="{{ url_for('chat_poll', cid=conv.id) }}" data-last="{{ last_id }}" data-conv="{{ conv.id }}">
    {% for m in msgs %}<div class="msg {{ 'me' if m.sender_id == me.id }}">{{ m.body }}<time>{{ m.created_at|dt }}</time></div>
    {% else %}<p class="muted center chat-empty">Konuşmayı başlat: ilan hakkında merak ettiğini sor.</p>{% endfor %}
    <span id="son"></span>
  </div>
  {% if conv.is_locked %}
  <div class="notice bad" style="margin:0;border-radius:0">Bu konuşma yönetim tarafından kilitlendi; yeni mesaj gönderilemez.</div>
  {% else %}
  <form class="chat-form" method="post" action="{{ url_for('chat', cid=conv.id) }}">
    {{ csrf_field() }}
    <textarea name="body" placeholder="Mesajını yaz (Enter: gönder, Shift+Enter: yeni satır)" maxlength="1000" required></textarea>
    <button class="btn" type="submit">Gönder</button>
  </form>
  {% endif %}
  <div class="chat-note">Ödemeyi ve teslimatı platform dışına taşıma; şifre veya kart bilgisi paylaşma. Mesajlar güvenlik için yönetim tarafından görüntülenebilir.</div>
</div>
{% endblock %}
"""

TEMPLATES["tickets.html"] = r"""
{% extends "account_base.html" %}
{% from "_macros.html" import pager, empty %}
{% block title %}Destek Talepleri{% endblock %}
{% block panel %}
<div class="page-h"><h1>Destek talepleri</h1><a class="btn" href="{{ url_for('ticket_new') }}">Yeni Talep</a></div>
{% if page.rows %}
<div class="table-wrap"><table>
  <tr><th>No</th><th>Konu</th><th>Kategori</th><th>Durum</th><th>Son güncelleme</th></tr>
  {% for t in page.rows %}<tr>
    <td><a href="{{ url_for('ticket_view', tid=t.id) }}">#{{ t.id }}</a></td>
    <td><a href="{{ url_for('ticket_view', tid=t.id) }}">{{ t.subject }}</a></td>
    <td>{{ t.category|tcat }}</td>
    <td><span class="badge b-{{ t.status|tclass }}">{{ t.status|tlabel }}</span></td>
    <td class="nowrap">{{ t.updated_at|dt }}</td>
  </tr>{% endfor %}
</table></div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Henüz destek talebin yok', 'Bir sorun yaşarsan yeni talep oluşturabilirsin.') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["ticket_new.html"] = r"""
{% extends "account_base.html" %}
{% block title %}Yeni Destek Talebi{% endblock %}
{% block panel %}
<div class="page-h"><h1>Yeni destek talebi</h1><a class="btn btn-ghost btn-sm" href="{{ url_for('tickets') }}">Taleplerim</a></div>
<div class="card">
  <form method="post" action="{{ url_for('ticket_new') }}">
    {{ csrf_field() }}
    <div class="form-row">
      <div class="field"><label for="category">Kategori</label>
        <select id="category" name="category" required>{% for k, v in TICKET_CATEGORIES.items() %}<option value="{{ k }}" {{ 'selected' if form.category == k }}>{{ v }}</option>{% endfor %}</select></div>
      <div class="field"><label for="order_id">İlgili sipariş (isteğe bağlı)</label>
        <select id="order_id" name="order_id"><option value="">Yok</option>{% for o in my_orders %}<option value="{{ o.id }}" {{ 'selected' if (form.order_id|string == o.id|string) or (not form and preset_order == o.id) }}>#{{ o.id }} - {{ o.listing_title[:40] }}</option>{% endfor %}</select></div>
    </div>
    <div class="field"><label for="subject">Konu</label><input type="text" id="subject" name="subject" value="{{ form.subject }}" required minlength="5" maxlength="100"></div>
    <div class="field"><label for="message">Sorunun</label><textarea id="message" name="message" required minlength="10" maxlength="3000" style="min-height:160px" placeholder="Ne oldu? Ne zaman oldu? Sipariş veya işlem numarasını yazmayı unutma.">{{ form.message }}</textarea></div>
    {% if need_captcha %}<div class="notice small">Kısa sürede çok sayıda talep oluşturdun; devam etmek için güvenlik doğrulamasını tamamla.</div>{{ captcha_block('ticket') }}{% endif %}
    <div class="notice small">Şifreni, kart bilgilerini veya kodları bu forma yazma. Destek ekibi bu bilgileri asla istemez.</div>
    <button class="btn" type="submit">Talebi Gönder</button>
  </form>
</div>
{% endblock %}
"""

TEMPLATES["ticket.html"] = r"""
{% extends "account_base.html" %}
{% block title %}Talep #{{ t.id }}{% endblock %}
{% block panel %}
<div class="page-h">
  <div><h1>#{{ t.id }} {{ t.subject }}</h1><span class="muted small">{{ t.category|tcat }} &middot; {{ t.created_at|dt }}{% if t.order_id %} &middot; <a href="{{ url_for('order_detail', oid=t.order_id) }}">Sipariş #{{ t.order_id }}</a>{% endif %}</span></div>
  <span class="badge b-{{ t.status|tclass }}">{{ t.status|tlabel }}</span>
</div>
{% for m in msgs %}
<div class="tmsg {{ 'staff' if m.author == 'staff' }}">
  <div class="meta"><b>{{ 'Destek Ekibi' if m.author == 'staff' else 'Sen' }}</b><span>{{ m.created_at|dt }}</span></div>
  <div class="pre">{{ m.body }}</div>
</div>
{% endfor %}
{% if t.status == 'closed' %}
<div class="notice">Bu talep kapatıldı. Sorun devam ediyorsa aşağıdan yazarak yeniden açabilirsin.</div>
{% endif %}
<div class="card">
  <form method="post" action="{{ url_for('ticket_view', tid=t.id) }}">
    {{ csrf_field() }}
    <div class="field"><label for="message">{{ 'Yeniden aç ve yanıt yaz' if t.status == 'closed' else 'Yanıtın' }}</label><textarea id="message" name="message" required maxlength="3000"></textarea></div>
    <div class="row"><button class="btn" type="submit">Gönder</button></div>
  </form>
  {% if t.status != 'closed' %}
  <form method="post" action="{{ url_for('ticket_view', tid=t.id) }}" class="mt" data-confirm="Talep kapatılsın mı?">{{ csrf_field() }}<input type="hidden" name="action" value="close"><button class="link-btn" type="submit">Sorunum çözüldü, talebi kapat</button></form>
  {% endif %}
</div>
{% endblock %}
"""
