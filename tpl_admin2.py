"""Admin paneli şablonları - 2. bölüm (Jinja). Emoji kullanılmaz."""

TEMPLATES = {}

TEMPLATES["admin_kyc.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import badge, pager, empty, status_tabs %}
{% block title %}Kimlik Onayları{% endblock %}
{% block heading %}Kimlik onayları{% endblock %}
{% block panel %}
{{ status_tabs('admin.kyc', status, counts) }}
<div class="notice mb">Kimlik görselleri hassas kişisel veridir. Yalnızca doğrulama için incele, kaydetme veya paylaşma. Onaylamadan önce belgenin okunaklı olduğunu, bilgilerin belgeyle uyuştuğunu ve selfie'deki kişinin belge sahibi olduğunu doğrula.</div>
{% if items %}
{% for it in items %}{% set r = it.r %}
<div class="card kyc-card">
  <div class="spread mb">
    <div>
      <h3 style="margin:0">{{ r.full_name }}</h3>
      <span class="muted small">Başvuru #{{ r.id }} &middot; <a href="{{ url_for('admin.user', uid=r.user_id) }}">{{ r.username }}</a> &middot; {{ r.email }} &middot; {{ r.created_at|dt }}</span>
    </div>
    <div class="row">{{ badge(r.status) }}<span class="badge b-muted">{{ 'Ehliyet' if r.doc_type == 'ehliyet' else 'Kimlik kartı' }}</span></div>
  </div>

  {% if it.flags or it.same_name or it.prev_rejects %}
  <ul class="flag-list">
    {% for f in it.flags %}<li>{{ f }}</li>{% endfor %}
    {% if it.same_name %}<li>Aynı ad soyadla başka hesap(lar) başvurmuş: {{ it.same_name|join(', ') }}</li>{% endif %}
    {% if it.prev_rejects %}<li>Bu kullanıcının daha önce reddedilmiş {{ it.prev_rejects }} kimlik başvurusu var.</li>{% endif %}
  </ul>
  {% endif %}

  <div class="two-col" style="display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.4fr);gap:18px">
    <dl class="kv" style="align-content:start">
      <dt>Ad soyad</dt><dd>{{ r.full_name }}</dd>
      <dt>Kimlik no</dt><dd class="mono">{{ r.id_number }}</dd>
      <dt>Doğum tarihi</dt><dd>{{ r.birth_date }}</dd>
      <dt>Telefon</dt><dd>{{ r.phone or '-' }}</dd>
      <dt>Hesap açılışı</dt><dd>{{ r.user_created|dt }}</dd>
      {% if r.reviewed_at %}<dt>İnceleme</dt><dd>{{ r.reviewed_at|dt }}</dd>{% endif %}
      {% if r.checklist %}<dt>Kontroller</dt><dd>{{ r.checklist.replace('doc', 'belge').replace('data', 'bilgi').replace('face', 'yüz').replace(',', ', ') }}</dd>{% endif %}
    </dl>
    <div class="kyc-imgs">
      <a href="{{ url_for('admin.kyc_file', kid=r.id, which='on') }}" data-zoom><img src="{{ url_for('admin.kyc_file', kid=r.id, which='on') }}" alt="Ön yüz" loading="lazy"><small>Ön yüz</small></a>
      <a href="{{ url_for('admin.kyc_file', kid=r.id, which='arka') }}" data-zoom><img src="{{ url_for('admin.kyc_file', kid=r.id, which='arka') }}" alt="Arka yüz" loading="lazy"><small>Arka yüz</small></a>
      <a href="{{ url_for('admin.kyc_file', kid=r.id, which='selfie') }}" data-zoom><img src="{{ url_for('admin.kyc_file', kid=r.id, which='selfie') }}" alt="Selfie" loading="lazy"><small>Belgeyle selfie</small></a>
    </div>
  </div>

  {% if r.status == 'pending' %}
  <form method="post" action="{{ url_for('admin.kyc_action', kid=r.id) }}" class="mt">
    {{ csrf_field() }}
    <div class="checks">
      <label class="check"><input type="checkbox" name="chk_doc" value="1"> <span>Belge gerçek görünüyor, okunaklı ve süresi geçmemiş</span></label>
      <label class="check"><input type="checkbox" name="chk_data" value="1"> <span>Ad soyad, kimlik no ve doğum tarihi belgeyle uyuşuyor</span></label>
      <label class="check"><input type="checkbox" name="chk_face" value="1"> <span>Selfie'deki kişi belge sahibiyle eşleşiyor ve belge selfie'de net görünüyor</span></label>
    </div>
    <div class="form-row">
      <div class="field"><label for="reason{{ r.id }}">Ret nedeni (reddederken)</label>
        <select id="reason{{ r.id }}" name="reason"><option value="">Seçiniz</option>{% for x in reasons %}<option value="{{ x }}">{{ x }}</option>{% endfor %}</select></div>
      <div class="field"><label for="note{{ r.id }}">Not (kullanıcıya gösterilir)</label><input type="text" id="note{{ r.id }}" name="note" maxlength="300"></div>
    </div>
    <div class="row">
      <button class="btn btn-ok" name="action" value="approve" type="submit" data-confirm="Kimlik onaylansın mı?">Onayla</button>
      <button class="btn btn-danger" name="action" value="reject" type="submit" data-confirm="Kimlik başvurusu reddedilsin mi?">Reddet</button>
    </div>
  </form>
  {% elif r.admin_note %}<p class="muted small mt"><b>Not:</b> {{ r.admin_note }}</p>{% endif %}
</div>
{% endfor %}
{{ pager(page) }}
{% else %}<div class="card">{{ empty('Bu durumda kimlik başvurusu yok') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["admin_tickets.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import pager, empty %}
{% block title %}Destek Talepleri{% endblock %}
{% block heading %}Destek talepleri{% endblock %}
{% block panel %}
<div class="tabs">
  {% for key, label in [('open', 'Açık'), ('answered', 'Yanıtlanan'), ('closed', 'Kapalı'), ('all', 'Tümü')] %}
  <a class="{{ 'on' if status == key }}" href="{{ url_for('admin.tickets', durum=key) }}">{{ label }}{% if key != 'all' %} <span class="cnt">{{ counts[key] }}</span>{% endif %}</a>
  {% endfor %}
</div>
<form class="filters" method="get" action="{{ url_for('admin.tickets') }}">
  <input type="hidden" name="durum" value="{{ status }}">
  <div class="field grow"><label for="q">Ara</label><input type="search" id="q" name="q" value="{{ text }}" placeholder="Konu, kullanıcı adı veya talep no"></div>
  <div class="field"><label for="oncelik">Öncelik</label><select id="oncelik" name="oncelik"><option value="">Hepsi</option>{% for k in ['normal', 'high', 'urgent'] %}<option value="{{ k }}" {{ 'selected' if prio == k }}>{{ k|plabel }}</option>{% endfor %}</select></div>
  <div class="field"><button class="btn" type="submit">Filtrele</button></div>
</form>
{% if page.rows %}
<div class="table-wrap"><table>
  <tr><th>No</th><th>Konu</th><th>Kullanıcı</th><th>Kategori</th><th>Öncelik</th><th>Durum</th><th>Son yanıt</th><th>Güncelleme</th><th></th></tr>
  {% for t in page.rows %}<tr>
    <td>#{{ t.id }}</td>
    <td><a href="{{ url_for('admin.ticket', tid=t.id) }}"><b>{{ t.subject[:60] }}</b></a></td>
    <td><a href="{{ url_for('admin.user', uid=t.user_id) }}">{{ t.username }}</a></td>
    <td>{{ t.category|tcat }}</td>
    <td><span class="badge b-{{ t.priority|pclass }}">{{ t.priority|plabel }}</span></td>
    <td><span class="badge b-{{ t.status|tclass }}">{{ t.status|tlabel }}</span></td>
    <td class="muted small">{{ 'Yönetim' if t.last_reply_by == 'staff' else 'Kullanıcı' }}</td>
    <td class="nowrap">{{ t.updated_at|dt }}</td>
    <td class="actions"><a class="btn btn-sm" href="{{ url_for('admin.ticket', tid=t.id) }}">Aç</a></td>
  </tr>{% endfor %}
</table></div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Bu filtreyle talep bulunamadı') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["admin_ticket.html"] = r"""
{% extends "admin_base.html" %}
{% block title %}Talep #{{ t.id }}{% endblock %}
{% block heading %}Talep #{{ t.id }}{% endblock %}
{% block panel %}
<div class="spread mb">
  <div>
    <h2 style="margin:0">{{ t.subject }}</h2>
    <span class="muted small"><a href="{{ url_for('admin.user', uid=t.user_id) }}">{{ t.username }}</a> &middot; {{ t.email }} &middot; {{ t.category|tcat }} &middot; {{ t.created_at|dt }}
      {% if order %} &middot; Sipariş #{{ order.id }} ({{ order.listing_title[:40] }}, {{ order.total|money }}){% endif %}</span>
  </div>
  <div class="row"><span class="badge b-{{ t.priority|pclass }}">{{ t.priority|plabel }}</span><span class="badge b-{{ t.status|tclass }}">{{ t.status|tlabel }}</span></div>
</div>

{% for m in msgs %}
<div class="tmsg {{ 'internal' if m.is_internal else ('staff' if m.author == 'staff') }}">
  <div class="meta"><b>{{ 'İç not (kullanıcı göremez)' if m.is_internal else ('Destek ekibi' if m.author == 'staff' else t.username) }}</b><span>{{ m.created_at|dt }}</span></div>
  <div class="pre">{{ m.body }}</div>
</div>
{% endfor %}

<div class="grid g2">
  <div class="card">
    <h3 class="mt0">Kullanıcıya yanıt ver</h3>
    <form method="post" action="{{ url_for('admin.ticket', tid=t.id) }}">
      {{ csrf_field() }}<input type="hidden" name="action" value="reply">
      <div class="field"><textarea id="reply-body" name="message" required maxlength="3000" aria-label="Yanıt"></textarea>
        <div class="quick">
          <button type="button" data-fill="Merhaba, talebini aldık ve inceliyoruz. En kısa sürede dönüş yapacağız." data-target="#reply-body">İnceleniyor</button>
          <button type="button" data-fill="Merhaba, sorunu çözebilmemiz için sipariş numaranı ve varsa ekran görüntüsünü paylaşabilir misin?" data-target="#reply-body">Bilgi iste</button>
          <button type="button" data-fill="Merhaba, bakiye yüklemen kontrol edildi ve hesabına eklendi. İyi alışverişler dileriz." data-target="#reply-body">Yükleme onaylandı</button>
          <button type="button" data-fill="Merhaba, sorunun çözüldüğünü düşünüyoruz. Başka bir sorun olursa aynı talep üzerinden yazabilirsin." data-target="#reply-body">Çözüldü</button>
        </div></div>
      <label class="check field"><input type="checkbox" name="close" value="1"> <span>Yanıtladıktan sonra talebi kapat</span></label>
      <button class="btn" type="submit">Yanıtı Gönder</button>
    </form>
  </div>
  <div class="card">
    <h3 class="mt0">İç not</h3>
    <form method="post" action="{{ url_for('admin.ticket', tid=t.id) }}">
      {{ csrf_field() }}<input type="hidden" name="action" value="note">
      <div class="field"><textarea name="message" required maxlength="3000" aria-label="İç not" placeholder="Yalnızca yöneticiler görür"></textarea></div>
      <button class="btn btn-line" type="submit">Not Ekle</button>
    </form>
    <hr style="border:0;border-top:1px solid var(--line);margin:16px 0">
    <div class="row">
      <form method="post" action="{{ url_for('admin.ticket', tid=t.id) }}" class="mini-form" style="justify-content:flex-start">{{ csrf_field() }}<input type="hidden" name="action" value="status">
        <select name="status" aria-label="Durum">{% for k in ['open', 'answered', 'closed'] %}<option value="{{ k }}" {{ 'selected' if t.status == k }}>{{ k|tlabel }}</option>{% endfor %}</select>
        <button class="btn btn-sm" type="submit">Durumu değiştir</button></form>
      <form method="post" action="{{ url_for('admin.ticket', tid=t.id) }}" class="mini-form" style="justify-content:flex-start">{{ csrf_field() }}<input type="hidden" name="action" value="priority">
        <select name="priority" aria-label="Öncelik">{% for k in ['normal', 'high', 'urgent'] %}<option value="{{ k }}" {{ 'selected' if t.priority == k }}>{{ k|plabel }}</option>{% endfor %}</select>
        <button class="btn btn-sm" type="submit">Önceliği değiştir</button></form>
    </div>
  </div>
</div>
<p class="mt"><a href="{{ url_for('admin.tickets') }}">Talep listesine dön</a></p>
{% endblock %}
"""

TEMPLATES["admin_chats.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import pager, empty %}
{% block title %}Sohbet Denetimi{% endblock %}
{% block heading %}Sohbet denetimi{% endblock %}
{% block panel %}
<div class="notice mb">Bir sohbeti açtığında bu erişim yönetici günlüğüne kaydedilir. Sohbetleri yalnızca şikayet, dolandırıcılık şüphesi veya destek talebi gibi gerekçelerle incele.</div>
<form class="filters" method="get" action="{{ url_for('admin.chats') }}">
  <div class="field grow"><label for="q">Ara</label><input type="search" id="q" name="q" value="{{ text }}" placeholder="Alıcı, satıcı veya ilan"></div>
  <div class="field"><button class="btn" type="submit">Ara</button></div>
</form>
{% if page.rows %}
<div class="table-wrap"><table>
  <tr><th>No</th><th>İlan</th><th>Alıcı</th><th>Satıcı</th><th class="right">Mesaj</th><th>Son mesaj</th><th>Durum</th><th></th></tr>
  {% for c in page.rows %}<tr>
    <td>#{{ c.id }}</td><td>{{ c.listing_title[:44] }}</td><td>{{ c.buyer_name }}</td><td>{{ c.seller_name }}{{ pkg_marks(c.seller_id) }}</td>
    <td class="right">{{ c.n }}</td><td class="nowrap">{{ c.last_message_at|dt }}</td>
    <td>{% if c.is_locked %}<span class="badge b-bad">Kilitli</span>{% else %}<span class="badge b-ok">Açık</span>{% endif %}</td>
    <td class="actions"><a class="btn btn-sm" href="{{ url_for('admin.chat', cid=c.id) }}">İncele</a></td>
  </tr>{% endfor %}
</table></div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Sohbet bulunamadı') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["admin_chat.html"] = r"""
{% extends "admin_base.html" %}
{% block title %}Sohbet #{{ conv.id }}{% endblock %}
{% block heading %}Sohbet #{{ conv.id }}{% endblock %}
{% block panel %}
<div class="spread mb">
  <div>
    <b>{{ conv.listing_title }}</b><br>
    <span class="muted small">Alıcı: <a href="{{ url_for('admin.user', uid=conv.buyer_id) }}">{{ conv.buyer_name }}</a> &middot; Satıcı: <a href="{{ url_for('admin.user', uid=conv.seller_id) }}">{{ conv.seller_name }}</a>{{ pkg_marks(conv.seller_id) }} &middot; Başlangıç: {{ conv.created_at|dt }}</span>
  </div>
  <form method="post" action="{{ url_for('admin.chat', cid=conv.id) }}" data-confirm="{{ 'Sohbetin kilidi açılsın mı?' if conv.is_locked else 'Sohbet kilitlensin mi? Taraflar yeni mesaj gönderemez.' }}">{{ csrf_field() }}
    <button class="btn {{ 'btn-ok' if conv.is_locked else 'btn-danger' }}" type="submit">{{ 'Kilidi aç' if conv.is_locked else 'Sohbeti kilitle' }}</button></form>
</div>
<div class="card chat" style="height:auto;max-height:70vh">
  <div class="chat-log" style="max-height:60vh;overflow:auto">
    {% for m in msgs %}<div class="msg {{ 'me' if m.sender_id == conv.seller_id }}"><b class="small">{{ m.username }}</b><br>{{ m.body }}<time>{{ m.created_at|dt }}</time></div>
    {% else %}<p class="muted center">Bu sohbette mesaj yok.</p>{% endfor %}
  </div>
</div>
<p class="mt"><a href="{{ url_for('admin.chats') }}">Sohbet listesine dön</a></p>
{% endblock %}
"""

TEMPLATES["admin_reviews.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import pager, empty, stars %}
{% block title %}Yorumlar{% endblock %}
{% block heading %}Yorumlar{% endblock %}
{% block panel %}
<div class="tabs">
  {% for key, label in [('', 'Tümü'), ('low', 'Düşük puanlılar'), ('hidden', 'Gizlenenler')] %}
  <a class="{{ 'on' if flt == key }}" href="{{ url_for('admin.reviews', durum=key) if key else url_for('admin.reviews') }}">{{ label }}</a>
  {% endfor %}
</div>
{% if page.rows %}
<div class="grid" style="gap:12px">
  {% for r in page.rows %}
  <div class="card review">
    <div class="spread">
      <div class="row">{{ stars(r.rating) }}<b>{{ r.rating }}/5</b>{% if r.is_hidden %}<span class="badge b-bad">Gizli</span>{% endif %}</div>
      <span class="muted small">{{ r.created_at|dt }}</span>
    </div>
    <div class="muted small mt">Alıcı <a href="{{ url_for('admin.user', uid=r.buyer_id) }}">{{ r.buyer_name }}</a> &rarr; satıcı <a href="{{ url_for('admin.user', uid=r.seller_id) }}">{{ r.seller_name }}</a>{{ pkg_marks(r.seller_id) }} &middot; {{ r.listing_title[:50] }} &middot; {% if r.order_id %}Sipariş #{{ r.order_id }}{% else %}Demo yorum{% endif %}</div>
    {% if r.comment %}<div class="pre mt">{{ r.comment }}</div>{% else %}<p class="muted mt">Yorum yazılmamış, yalnızca puan verilmiş.</p>{% endif %}
    {% if r.seller_reply %}<div class="reply mt"><b class="small">Satıcı yanıtı:</b><div class="pre">{{ r.seller_reply }}</div></div>{% endif %}
    <form method="post" action="{{ url_for('admin.review_action', rid=r.id) }}" class="mt">{{ csrf_field() }}
      {% if r.is_hidden %}<button class="btn btn-ok btn-sm" name="action" value="show" type="submit">Yeniden yayınla</button>
      {% else %}<button class="btn btn-danger btn-sm" name="action" value="hide" type="submit" data-confirm="Yorum gizlensin mi? Puan hesaplarından da çıkar.">Gizle</button>{% endif %}
    </form>
  </div>
  {% endfor %}
</div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Yorum bulunamadı') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["admin_categories.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import empty, ic with context %}
{% block title %}Kategoriler{% endblock %}
{% block heading %}Kategoriler{% endblock %}
{% block panel %}
<div class="notice mb">Komisyon alanını boş bırakırsan genel oran (%{{ global_rate }}) uygulanır. <b>Günün oyunu</b> işaretli kategoriler ana sayfadaki poster bölümünde görünür; görsel yüklemezsen sitenin hazır kategori banner'ı (yoksa genel banner) kullanılır; yüklediğin görsel varsayılanın yerine geçer, kaldırırsan varsayılana dönülür.</div>
<div class="card mb">
  <h3 class="mt0">Toplu afiş yükle</h3>
  <p class="muted small">Görselleri kategori adıyla kaydet ve hepsini birden seç: <span class="mono">discord.jpg</span>, <span class="mono">steam.png</span>, <span class="mono">valorant.webp</span> gibi. Dikey (3:4) görseller en iyi sonucu verir; otomatik kırpılır. Yalnızca kullanım hakkına sahip olduğun görselleri yükle.</p>
  <form method="post" enctype="multipart/form-data" action="{{ url_for('admin.category_posters') }}" class="row" style="align-items:center">
    {{ csrf_field() }}
    <input type="file" name="posters" accept="image/jpeg,image/png,image/webp" multiple required aria-label="Afişler" style="flex:1;min-width:220px">
    <button class="btn" type="submit">Yükle</button>
  </form>
</div>
<div class="card mb">
  <h3 class="mt0">Yeni kategori</h3>
  <form method="post" action="{{ url_for('admin.categories') }}" class="row" style="align-items:flex-end">
    {{ csrf_field() }}<input type="hidden" name="action" value="add">
    <div class="field" style="margin:0;flex:1;min-width:180px"><label for="n-name">Ad</label><input type="text" id="n-name" name="name" required minlength="2" maxlength="40"></div>
    <div class="field" style="margin:0;width:180px"><label for="n-grp">Grup</label><input type="text" id="n-grp" name="grp" maxlength="40" list="grp-list" placeholder="PC &amp; Konsol"></div>
    <div class="field" style="margin:0;width:70px"><label for="n-color">Renk</label><input type="color" id="n-color" name="color" value="#7c5cff"></div>
    <div class="field" style="margin:0;width:110px"><label for="n-rate">Komisyon %</label><input type="text" inputmode="decimal" id="n-rate" name="rate" placeholder="Genel"></div>
    <div class="field" style="margin:0;width:80px"><label for="n-order">Sıra</label><input type="number" id="n-order" name="sort_order" value="0"></div>
    <label class="check" style="margin:0 0 10px"><input type="checkbox" name="is_daily" value="1"> Günün oyunu</label>
    <button class="btn" type="submit">Ekle</button>
  </form>
  <datalist id="grp-list"><option value="PC &amp; Konsol"><option value="Mobil"><option value="Uygulama &amp; Abonelik"><option value="Hediye Kartları"></datalist>
</div>
{% if cats %}
<div class="table-wrap"><table>
  <tr><th>Ad ve açıklama</th><th>Grup</th><th>Renk</th><th>Komisyon %</th><th>Sıra</th><th>Günün oyunu</th><th>Aktif</th><th>Poster</th><th class="right">İlan</th><th></th></tr>
  {% for c in cats %}<tr>
    <form method="post" enctype="multipart/form-data" action="{{ url_for('admin.categories') }}" id="cf{{ c.id }}">{{ csrf_field() }}<input type="hidden" name="action" value="edit"><input type="hidden" name="id" value="{{ c.id }}"></form>
    <td style="min-width:220px"><input form="cf{{ c.id }}" type="text" name="name" value="{{ c.name }}" required minlength="2" maxlength="40" aria-label="Ad"><input form="cf{{ c.id }}" type="text" name="tagline" value="{{ c.tagline }}" maxlength="90" placeholder="Kısa açıklama" aria-label="Açıklama" style="margin-top:6px"></td>
    <td><input form="cf{{ c.id }}" type="text" name="grp" value="{{ c.grp }}" maxlength="40" list="grp-list" style="width:150px" aria-label="Grup"></td>
    <td><input form="cf{{ c.id }}" type="color" name="color" value="{{ c.color or '#7c5cff' }}" style="width:56px" aria-label="Renk"></td>
    <td><input form="cf{{ c.id }}" type="text" inputmode="decimal" name="rate" value="{{ c.commission_rate if c.commission_rate is not none else '' }}" placeholder="Genel" style="width:90px" aria-label="Komisyon"></td>
    <td><input form="cf{{ c.id }}" type="number" name="sort_order" value="{{ c.sort_order }}" style="width:70px" aria-label="Sıra"></td>
    <td><input form="cf{{ c.id }}" type="checkbox" name="is_daily" value="1" {{ 'checked' if c.is_daily }} aria-label="Günün oyunu"></td>
    <td><input form="cf{{ c.id }}" type="checkbox" name="is_active" value="1" {{ 'checked' if c.is_active }} aria-label="Aktif"></td>
    <td style="min-width:170px">{% if c.image %}<img class="thumb" style="width:38px;height:50px;display:inline-block;vertical-align:middle" src="{{ url_for('media_cover', name=c.image) }}" alt=""> <label class="check small" style="display:inline-flex"><input form="cf{{ c.id }}" type="checkbox" name="remove_poster" value="1"> kaldır</label>
      {% else %}<img class="thumb" style="width:38px;height:50px;display:inline-block;vertical-align:middle" src="{{ category_banner_url(c, 'card') }}" alt=""> <span class="small muted">Varsayılan banner kullanılıyor</span>{% endif %}
      <input form="cf{{ c.id }}" type="file" name="poster" accept="image/jpeg,image/png,image/webp" aria-label="Poster" style="margin-top:6px;padding:4px"></td>
    <td class="right">{{ c.n }}</td>
    <td class="actions"><div class="mini-form">
      <button form="cf{{ c.id }}" class="btn btn-sm" type="submit">Kaydet</button>
      <form method="post" action="{{ url_for('admin.categories') }}" data-confirm="Kategori silinsin mi?">{{ csrf_field() }}<input type="hidden" name="action" value="delete"><input type="hidden" name="id" value="{{ c.id }}"><button class="btn btn-danger btn-sm" type="submit">Sil</button></form>
    </div></td>
  </tr>{% endfor %}
</table></div>
{% else %}<div class="card">{{ empty('Kategori yok') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["admin_commission.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import bars, empty %}
{% block title %}Komisyon Raporu{% endblock %}
{% block heading %}Komisyon raporu{% endblock %}
{% block panel %}
<div class="spread mb">
  <p class="muted" style="margin:0">Genel komisyon: <b>%{{ global_rate }}</b> &middot; Çekim kesintisi: <b>%{{ fee_rate }}</b> &middot; Öncelik: satıcıya özel, kategori, genel.</p>
  <a class="btn btn-line" href="{{ url_for('admin.commission_csv') }}">CSV indir</a>
</div>
<div class="grid g4 mb">
  <div class="stat"><div class="k">Sipariş</div><div class="v">{{ totals.orders }}</div></div>
  <div class="stat"><div class="k">Toplam ciro</div><div class="v">{{ totals.gmv|money }}</div></div>
  <div class="stat good"><div class="k">Satış komisyonu</div><div class="v">{{ totals.fee|money }}</div></div>
  <div class="stat"><div class="k">Çekim kesintileri</div><div class="v">{{ totals.wd_fee|money }}</div><div class="s">Kupon maliyeti {{ totals.discount|money }} &middot; Doping geliri {{ totals.doping|money }}</div></div>
</div>
<div class="card mb"><h3 class="mt0">Günlük komisyon (son 14 gün)</h3>{{ bars(chart, true) }}</div>
<div class="grid g2">
  <div class="card">
    <h3 class="mt0">Kategoriye göre</h3>
    <div class="table-wrap"><table>
      <tr><th>Kategori</th><th>Oran</th><th class="right">Sipariş</th><th class="right">Ciro</th><th class="right">Komisyon</th></tr>
      {% for c in by_cat %}<tr><td>{{ c.name }}</td><td>{{ ('%' ~ c.commission_rate) if c.commission_rate is not none else 'Genel' }}</td><td class="right">{{ c.orders }}</td><td class="right nowrap">{{ c.gmv|money }}</td><td class="right nowrap">{{ c.fee|money }}</td></tr>{% endfor %}
    </table></div>
  </div>
  <div class="card">
    <h3 class="mt0">En çok komisyon getiren satıcılar</h3>
    {% if by_seller %}<div class="table-wrap"><table>
      <tr><th>Satıcı</th><th>Oran</th><th class="right">Sipariş</th><th class="right">Ciro</th><th class="right">Komisyon</th></tr>
      {% for s in by_seller %}<tr><td><a href="{{ url_for('admin.user', uid=s.id) }}">{{ s.username }}</a>{{ pkg_marks(s.id) }}</td><td>{{ ('%' ~ s.commission_rate) if s.commission_rate is not none else 'Genel' }}</td><td class="right">{{ s.orders }}</td><td class="right nowrap">{{ s.gmv|money }}</td><td class="right nowrap">{{ s.fee|money }}</td></tr>{% endfor %}
    </table></div>{% else %}{{ empty('Henüz satış yok') }}{% endif %}
  </div>
</div>
<div class="card mt">
  <h3 class="mt0">Özel oranlı satıcılar</h3>
  {% if custom %}<div class="row">{% for u in custom %}<a class="chip" href="{{ url_for('admin.user', uid=u.id) }}">{{ u.username }}{{ pkg_marks(u.id) }} &middot; %{{ u.commission_rate }}</a>{% endfor %}</div>
  {% else %}<p class="muted">Özel oran tanımlı satıcı yok. Oranı, satıcının kullanıcı sayfasından belirleyebilirsin.</p>{% endif %}
</div>
{% endblock %}
"""

TEMPLATES["admin_payments.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import empty, ic with context %}
{% block title %}Ödeme Yöntemleri{% endblock %}
{% block heading %}Ödeme yöntemleri{% endblock %}
{% block panel %}
<div class="grid g4 mb">
  <div class="stat good"><div class="k">Onaylanan yükleme</div><div class="v">{{ totals.ok_sum|money }}</div><div class="s">{{ totals.ok_n or 0 }} işlem</div></div>
  <div class="stat warn"><div class="k">Bekleyen yükleme</div><div class="v">{{ totals.pend_sum|money }}</div><div class="s"><a href="{{ url_for('admin.deposits', durum='pending') }}">{{ totals.pend_n or 0 }} talep - incele</a></div></div>
  <div class="stat"><div class="k">Aktif yöntem</div><div class="v">{{ methods|selectattr('is_active')|list|length }}</div><div class="s">{{ methods|length }} yöntemden</div></div>
  <div class="stat"><div class="k">Ödeme linkleri</div><div class="v"><a href="{{ url_for('admin.admin_paylinks') }}" style="font-size:1rem">Yönet</a></div><div class="s">Hazır ödeme sayfası bağlantıları</div></div>
</div>
<div class="notice warn mb">Hazır gelen yöntemler pasif durumdadır ve içindeki bilgiler örnektir. Kendi IBAN veya cüzdan bilgilerini girip yöntemi aktifleştirmeden kullanıcılar bakiye yükleyemez.</div>

<div class="card mb">
  <h3 class="mt0">Hazır şablondan ekle</h3>
  <p class="muted small mt0">Şablon pasif olarak eklenir; ödeme bilgilerini düzenleyip aktifleştirmen yeterli.</p>
  <form method="post" action="{{ url_for('admin.payments') }}" class="row">
    {{ csrf_field() }}<input type="hidden" name="action" value="add_template">
    <select name="template" aria-label="Şablon" style="width:auto;min-width:260px">{% for tp in templates %}<option value="{{ tp[0] }}">{{ tp[1] }}</option>{% endfor %}</select>
    <button class="btn" type="submit">{{ ic('plus') }}Şablonu ekle</button>
  </form>
</div>

<details class="card mb pm-new"><summary><b>{{ ic('plus') }} Özel yöntem ekle</b></summary>
  <form method="post" action="{{ url_for('admin.payments') }}" class="mt">
    {{ csrf_field() }}<input type="hidden" name="action" value="add">
    <div class="form-row">
      <div class="field"><label for="n-name">Ad</label><input type="text" id="n-name" name="name" required maxlength="60" placeholder="Örn. Banka havalesi / EFT"></div>
      <div class="field"><label for="n-kind">Tür</label><select id="n-kind" name="kind">{% for k, v in kinds.items() %}<option value="{{ k }}">{{ v }}</option>{% endfor %}</select></div>
    </div>
    <div class="field"><label for="n-details">Ödeme bilgileri (her satır "Etiket: değer" olursa kullanıcıda kopyala düğmesi çıkar)</label><textarea id="n-details" name="details" required maxlength="600" placeholder="Banka: ...&#10;Hesap sahibi: ...&#10;IBAN: TR00 ..."></textarea></div>
    <div class="field"><label for="n-inst">Kullanıcıya talimat</label><textarea id="n-inst" name="instructions" maxlength="600" placeholder="Örn. Açıklama kısmına kullanıcı adını yaz."></textarea></div>
    <div class="form-row">
      <div class="field"><label for="n-min">Minimum tutar (TL)</label><input type="text" inputmode="decimal" id="n-min" name="min_amount" value="0"></div>
      <div class="field"><label for="n-max">Maksimum tutar (TL, boş = sınırsız)</label><input type="text" inputmode="decimal" id="n-max" name="max_amount" value=""></div>
      <div class="field"><label for="n-bonus">Yükleme bonusu (%)</label><input type="text" inputmode="decimal" id="n-bonus" name="bonus_percent" value="0"></div>
      <div class="field"><label for="n-eta">Tahmini süre</label><input type="text" id="n-eta" name="eta" maxlength="40" placeholder="5-30 dk"></div>
    </div>
    <div class="form-row">
      <div class="field"><label for="n-badge">Rozet (isteğe bağlı)</label><input type="text" id="n-badge" name="badge" maxlength="24" placeholder="Önerilen"></div>
      <div class="field"><label for="n-icon">Simge</label><select id="n-icon" name="icon">{% for i in icons %}<option value="{{ i }}">{{ i }}</option>{% endfor %}</select></div>
      <div class="field"><label for="n-color">Renk</label><input type="color" id="n-color" name="color" value="#7c5cff"></div>
      <div class="field"><label for="n-ord">Sıra</label><input type="number" id="n-ord" name="sort_order" value="0"></div>
    </div>
    <label class="check field"><input type="checkbox" name="is_active" value="1"> <span>Hemen aktif olsun</span></label>
    <button class="btn" type="submit">Ekle</button>
  </form>
</details>

{% for m in methods %}{% set st = stats.get(m.id) %}
<div class="card mb pm-admin" style="--c:{{ m.color or '#7c5cff' }}">
  <div class="spread mb">
    <div class="row"><span class="pm-ico">{{ ic(m.icon or 'wallet') }}</span><div><h3 style="margin:0">{{ m.name }}{% if m.badge %} <span class="badge b-info">{{ m.badge }}</span>{% endif %}</h3>
      <div class="small muted">{% if st %}{{ st.ok_n or 0 }} onaylı ({{ st.ok_sum|money }}){% if st.pend_n %} &middot; <b>{{ st.pend_n }} bekleyen</b>{% endif %}{% else %}Henüz yükleme yok{% endif %}</div></div></div>
    <div class="row">
      <span class="badge b-{{ 'ok' if m.is_active else 'muted' }}">{{ 'Aktif' if m.is_active else 'Pasif' }}</span>
      <form method="post" action="{{ url_for('admin.payments') }}">{{ csrf_field() }}<input type="hidden" name="action" value="toggle"><input type="hidden" name="id" value="{{ m.id }}"><button class="btn btn-ghost btn-sm" type="submit">{{ 'Pasife al' if m.is_active else 'Aktifleştir' }}</button></form>
    </div>
  </div>
  <form method="post" action="{{ url_for('admin.payments') }}">
    {{ csrf_field() }}<input type="hidden" name="action" value="edit"><input type="hidden" name="id" value="{{ m.id }}">
    <div class="form-row">
      <div class="field"><label for="name{{ m.id }}">Ad</label><input type="text" id="name{{ m.id }}" name="name" value="{{ m.name }}" required maxlength="60"></div>
      <div class="field"><label for="kind{{ m.id }}">Tür</label><select id="kind{{ m.id }}" name="kind">{% for k, v in kinds.items() %}<option value="{{ k }}" {{ 'selected' if m.kind == k }}>{{ v }}</option>{% endfor %}</select></div>
    </div>
    <div class="field"><label for="det{{ m.id }}">Ödeme bilgileri</label><textarea id="det{{ m.id }}" name="details" required maxlength="600">{{ m.details }}</textarea></div>
    <div class="field"><label for="ins{{ m.id }}">Kullanıcıya talimat</label><textarea id="ins{{ m.id }}" name="instructions" maxlength="600">{{ m.instructions }}</textarea></div>
    <div class="form-row">
      <div class="field"><label for="min{{ m.id }}">Minimum tutar (TL)</label><input type="text" inputmode="decimal" id="min{{ m.id }}" name="min_amount" value="{{ m.min_amount|plain }}"></div>
      <div class="field"><label for="max{{ m.id }}">Maksimum tutar (TL, boş = sınırsız)</label><input type="text" inputmode="decimal" id="max{{ m.id }}" name="max_amount" value="{{ m.max_amount|plain if m.max_amount else '' }}"></div>
      <div class="field"><label for="bon{{ m.id }}">Yükleme bonusu (%)</label><input type="text" inputmode="decimal" id="bon{{ m.id }}" name="bonus_percent" value="{{ '%g'|format(m.bonus_percent) }}"></div>
      <div class="field"><label for="eta{{ m.id }}">Tahmini süre</label><input type="text" id="eta{{ m.id }}" name="eta" value="{{ m.eta }}" maxlength="40" placeholder="5-30 dk"></div>
    </div>
    <div class="form-row">
      <div class="field"><label for="bdg{{ m.id }}">Rozet</label><input type="text" id="bdg{{ m.id }}" name="badge" value="{{ m.badge }}" maxlength="24"></div>
      <div class="field"><label for="ico{{ m.id }}">Simge</label><select id="ico{{ m.id }}" name="icon">{% for i in icons %}<option value="{{ i }}" {{ 'selected' if (m.icon or '') == i }}>{{ i }}</option>{% endfor %}</select></div>
      <div class="field"><label for="clr{{ m.id }}">Renk</label><input type="color" id="clr{{ m.id }}" name="color" value="{{ m.color or '#7c5cff' }}"></div>
      <div class="field"><label for="ord{{ m.id }}">Sıra</label><input type="number" id="ord{{ m.id }}" name="sort_order" value="{{ m.sort_order }}"></div>
    </div>
    <label class="check field"><input type="checkbox" name="is_active" value="1" {{ 'checked' if m.is_active }}> <span>Aktif (kullanıcılara gösterilir)</span></label>
    <div class="row"><button class="btn" type="submit">Kaydet</button></div>
  </form>
  <form method="post" action="{{ url_for('admin.payments') }}" class="mt" data-confirm="Bu yöntem silinsin mi?">{{ csrf_field() }}<input type="hidden" name="action" value="delete"><input type="hidden" name="id" value="{{ m.id }}"><button class="link-btn link-danger" type="submit">Yöntemi sil</button></form>
</div>
{% else %}<div class="card">{{ empty('Ödeme yöntemi yok', 'Yukarıdan hazır bir şablon ekleyebilirsin.') }}</div>{% endfor %}
{% endblock %}
"""

TEMPLATES["admin_integration.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import empty %}
{% block title %}Entegrasyon ve API{% endblock %}
{% block heading %}Entegrasyon ve API{% endblock %}
{% block panel %}
<div class="grid g3 mb">
  <div class="stat"><div class="k">Aktif API anahtarı</div><div class="v">{{ stats.keys }}</div></div>
  <div class="stat"><div class="k">Otomatik onaylanan yükleme</div><div class="v">{{ stats.auto_deposits }}</div></div>
  <div class="stat"><div class="k">Son API kullanımı</div><div class="v" style="font-size:1.05rem">{{ stats.last_api_use|dt if stats.last_api_use else '-' }}</div></div>
</div>

<div class="card doc mb">
  <h3 class="mt0">Ödeme bildirimi (webhook)</h3>
  <p class="muted">Bir ödeme sağlayıcısı veya kendi ödeme servisin, başarılı ödemeyi bu adrese bildirdiğinde bekleyen bakiye yükleme talebi otomatik onaylanır ve bakiye eklenir. Kullanıcı önce sitede yükleme talebi oluşturur; talebin numarası <code class="inline">deposit_id</code> olarak gönderilir.</p>
  <p>Durum: {% if secret_set %}<span class="badge b-ok">Gizli anahtar tanımlı</span> <span class="mono muted">{{ secret_hint }}</span>{% else %}<span class="badge b-bad">PAYMENT_WEBHOOK_SECRET tanımlı değil, webhook kapalı</span>{% endif %}</p>
  <p>Adres: <code class="inline">POST {{ base }}/api/webhook/odeme</code></p>
  <p class="muted">Gizli anahtar <code class="inline">.env</code> dosyasındaki <code class="inline">PAYMENT_WEBHOOK_SECRET</code> değeridir; buradan değiştirilemez ve sayfada tam olarak gösterilmez. İmza, ham istek gövdesinin HMAC-SHA256 özetidir (onaltılık) ve <code class="inline">X-Signature</code> başlığıyla gönderilir.</p>
<pre>body='{"deposit_id": 12, "amount": "250.00", "status": "success", "transaction_id": "TX-98765"}'
sig=$(printf '%s' "$body" | openssl dgst -sha256 -hmac "$PAYMENT_WEBHOOK_SECRET" | awk '{print $2}')

curl -X POST {{ base }}/api/webhook/odeme \
  -H "Content-Type: application/json" \
  -H "X-Signature: $sig" \
  -d "$body"</pre>
  <ul class="muted">
    <li><code class="inline">status</code>: <code class="inline">success</code> talebi onaylar, <code class="inline">failed</code> reddeder.</li>
    <li><code class="inline">amount</code> talep edilen tutarla birebir eşleşmelidir; eşleşmezse istek reddedilir.</li>
    <li><code class="inline">transaction_id</code> benzersizdir; aynı bildirim tekrar gelirse ikinci kez bakiye eklenmez.</li>
  </ul>
</div>

<div class="card doc mb">
  <h3 class="mt0">Satıcı API'si</h3>
  <p class="muted">Satıcılar kendi panellerinden anahtar oluşturur ve stok ile ilan durumunu otomatik yönetir. Tüm uçlar <code class="inline">Authorization: Bearer &lt;anahtar&gt;</code> ister; dakikada 120 istek sınırı vardır.</p>
  <ul class="muted">
    <li><code class="inline">GET {{ base }}/api/v1/me</code> profil, bakiye ve satış özeti</li>
    <li><code class="inline">GET {{ base }}/api/v1/listings</code> ilanlar</li>
    <li><code class="inline">POST {{ base }}/api/v1/listings/&lt;id&gt;/stock</code> stoğa kod ekler (<code class="inline">{"codes": [...]}</code>)</li>
    <li><code class="inline">POST {{ base }}/api/v1/listings/&lt;id&gt;/status</code> ilanı yayına alır veya duraklatır</li>
    <li><code class="inline">GET {{ base }}/api/v1/orders</code> satışlar ve komisyon bilgisi</li>
  </ul>
</div>

<div class="card">
  <h3 class="mt0">Tüm API anahtarları</h3>
  {% if keys %}<div class="table-wrap"><table>
    <tr><th>Ad</th><th>Sahip</th><th>Anahtar</th><th>Son kullanım</th><th>Oluşturma</th><th>Durum</th><th></th></tr>
    {% for k in keys %}<tr>
      <td>{{ k.name }}</td><td><a href="{{ url_for('admin.user', uid=k.user_id) }}">{{ k.username }}</a></td><td class="mono">{{ k.key_prefix }}...</td>
      <td class="nowrap">{{ k.last_used_at|dt if k.last_used_at else '-' }}</td><td class="nowrap">{{ k.created_at|dt }}</td>
      <td><span class="badge b-{{ 'ok' if k.is_active else 'bad' }}">{{ 'Aktif' if k.is_active else 'İptal' }}</span></td>
      <td class="actions">{% if k.is_active %}<form method="post" action="{{ url_for('admin.api_key_revoke', kid=k.id) }}" data-confirm="Bu anahtar iptal edilsin mi?">{{ csrf_field() }}<button class="btn btn-danger btn-sm" type="submit">İptal et</button></form>{% endif %}</td>
    </tr>{% endfor %}
  </table></div>{% else %}{{ empty('Henüz API anahtarı oluşturulmadı') }}{% endif %}
</div>
{% endblock %}
"""

TEMPLATES["admin_settings.html"] = r"""
{% extends "admin_base.html" %}
{% macro chk(key, label) %}<label class="check field"><input type="checkbox" name="{{ key }}" value="1" {{ 'checked' if (request.form.get(key) if request.method == 'POST' else cfg[key] == '1') }}> <span>{{ label }}</span></label>{% endmacro %}
{% macro val(key) %}{{ request.form.get(key, cfg[key]) }}{% endmacro %}
{% block title %}Site Ayarları{% endblock %}
{% block heading %}Site ayarları{% endblock %}
{% block panel %}
<form method="post" action="{{ url_for('admin.site_settings') }}" class="grid" style="gap:16px;max-width:900px">
  {{ csrf_field() }}
  <div class="card">
    <h3 class="mt0">Genel</h3>
    <div class="form-row">
      <div class="field"><label for="site_name">Site adı</label><input type="text" id="site_name" name="site_name" value="{{ val('site_name') }}" required maxlength="30"></div>
      <div class="field"><label for="support_email">Destek e-postası</label><input type="email" id="support_email" name="support_email" value="{{ val('support_email') }}" maxlength="120"></div>
    </div>
    <div class="field"><label for="site_tagline">Slogan</label><input type="text" id="site_tagline" name="site_tagline" value="{{ val('site_tagline') }}" maxlength="120"></div>
    <div class="field"><label for="meta_description">Arama motoru açıklaması (meta description)</label><input type="text" id="meta_description" name="meta_description" value="{{ val('meta_description') }}" maxlength="200"></div>
    <div class="field"><label for="announcement">Duyuru çubuğu (sitenin üstünde görünür, boşsa gizlenir)</label><input type="text" id="announcement" name="announcement" value="{{ val('announcement') }}" maxlength="300"></div>
    <div class="form-row">
      <div class="field"><label for="support_hours">Destek saatleri</label><input type="text" id="support_hours" name="support_hours" value="{{ val('support_hours') }}" maxlength="60"></div>
      <div class="field"><label for="hero_seconds">Slider geçiş süresi (sn)</label><input type="number" id="hero_seconds" name="hero_seconds" min="3" max="20" value="{{ val('hero_seconds') }}" required></div>
    </div>
  </div>

  <div class="card">
    <h3 class="mt0">Emanet</h3>
    <div class="form-row">
      <div class="field"><label for="escrow_days">Otomatik aktarım süresi (gün)</label><input type="number" id="escrow_days" name="escrow_days" min="0" max="30" value="{{ val('escrow_days') }}" required><div class="hint">Alıcı onaylamazsa tutar bu süre sonunda satıcıya geçer. 0: sipariş anında geçer.</div></div>
    </div>
  </div>

  <div class="card">
    <h3 class="mt0">Sosyal medya</h3>
    <div class="form-row">
      <div class="field"><label for="social_discord">Discord davet bağlantısı</label><input type="url" id="social_discord" name="social_discord" value="{{ val('social_discord') }}" maxlength="200" placeholder="https://discord.gg/..."></div>
      <div class="field"><label for="social_telegram">Telegram bağlantısı</label><input type="url" id="social_telegram" name="social_telegram" value="{{ val('social_telegram') }}" maxlength="200" placeholder="https://t.me/..."></div>
    </div>
    <div class="field"><label for="social_instagram">Instagram bağlantısı</label><input type="url" id="social_instagram" name="social_instagram" value="{{ val('social_instagram') }}" maxlength="200" placeholder="https://instagram.com/..."></div>
    <div class="hint">Doldurulan bağlantılar site altbilgisinde simge olarak görünür.</div>
  </div>

  <div class="card">
    <h3 class="mt0">Komisyon ve limitler</h3>
    <div class="form-row">
      <div class="field"><label for="commission_percent">Genel satış komisyonu (%)</label><input type="text" inputmode="decimal" id="commission_percent" name="commission_percent" value="{{ val('commission_percent') }}" required><div class="hint">Kategori veya satıcıya özel oran tanımlıysa o geçerlidir.</div></div>
      <div class="field"><label for="withdraw_fee_percent">Çekim kesintisi (%)</label><input type="text" inputmode="decimal" id="withdraw_fee_percent" name="withdraw_fee_percent" value="{{ val('withdraw_fee_percent') }}" required></div>
    </div>
    <div class="form-row">
      <div class="field"><label for="min_deposit">Minimum yükleme (TL)</label><input type="text" inputmode="decimal" id="min_deposit" name="min_deposit" value="{{ val('min_deposit') }}" required></div>
      <div class="field"><label for="min_withdraw">Minimum çekim (TL)</label><input type="text" inputmode="decimal" id="min_withdraw" name="min_withdraw" value="{{ val('min_withdraw') }}" required></div>
    </div>
    <div class="field"><label for="max_qty_per_order">Sipariş başına maksimum adet</label><input type="number" id="max_qty_per_order" name="max_qty_per_order" min="1" max="100" value="{{ val('max_qty_per_order') }}" required></div>
  </div>

  <div class="card">
    <h3 class="mt0">Mağaza değişiklik ücretleri</h3>
    <div class="form-row">
      <div class="field"><label for="fee_store_name">Mağaza adı değişikliği (TL)</label><input type="text" inputmode="decimal" id="fee_store_name" name="fee_store_name" value="{{ val('fee_store_name') }}" required></div>
      <div class="field"><label for="fee_store_slug">Mağaza adresi değişikliği (TL)</label><input type="text" inputmode="decimal" id="fee_store_slug" name="fee_store_slug" value="{{ val('fee_store_slug') }}" required></div>
    </div>
    <div class="hint">Satıcının bakiyesinden düşülür. İlk belirleme ücretsizdir; yalnızca sonraki değişiklikler ücretlidir. 0 yazarsan ücret kalkar. Yönetici değişiklikleri ücretsizdir.</div>
  </div>

  <div class="card">
    <h3 class="mt0">Güvenilir satıcı rozeti</h3>
    <div class="form-row">
      <div class="field"><label for="trusted_min_sales">Asgari satış adedi</label><input type="number" id="trusted_min_sales" name="trusted_min_sales" min="1" value="{{ val('trusted_min_sales') }}" required></div>
      <div class="field"><label for="trusted_min_rating">Asgari ortalama puan (1-5)</label><input type="text" inputmode="decimal" id="trusted_min_rating" name="trusted_min_rating" value="{{ val('trusted_min_rating') }}" required></div>
    </div>
    <div class="hint">Rozet ayrıca en az 5 yorum ve onaylı kimlik ister. Yönetici, kullanıcı sayfasından rozetleri elle de verebilir.</div>
  </div>

  <div class="card">
    <h3 class="mt0">Kurallar ve vitrin</h3>
    {{ chk('require_seller_approval', 'Satıcı olmak için başvuru ve yönetici onayı gereksin') }}
    {{ chk('withdraw_only_earnings', 'Yalnızca satış kazancı çekilebilsin (yüklenen bakiye çekilemesin)') }}
    {{ chk('require_cover', 'İlanlarda kapak görseli zorunlu olsun') }}
    {{ chk('allow_registration', 'Yeni üyelik açık olsun') }}
    {{ chk('require_seller_2fa', 'Satıcı paneline girmek için iki adımlı doğrulama (2FA) zorunlu olsun') }}
    {{ chk('home_ticker', 'Ana sayfada canlı satış / yeni ilan bandını göster') }}
  </div>

  <div class="card" style="border-color:rgba(251,191,36,.4)">
    <h3 class="mt0">Bakım modu</h3>
    {{ chk('maintenance_mode', 'Siteyi bakıma al (yönetici hariç kimse giremez, ziyaretçiler bakım sayfasını görür)') }}
  </div>
  <div><button class="btn" type="submit">Ayarları kaydet</button></div>
</form>
{% endblock %}
"""

TEMPLATES["admin_transactions.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import pager, empty %}
{% block title %}İşlem Defteri{% endblock %}
{% block heading %}İşlem defteri{% endblock %}
{% block panel %}
<form class="filters" method="get" action="{{ url_for('admin.transactions') }}">
  <div class="field grow"><label for="q">Kullanıcı</label><input type="search" id="q" name="q" value="{{ text }}" placeholder="Kullanıcı adı"></div>
  <div class="field"><label for="tur">Tür</label><select id="tur" name="tur"><option value="">Hepsi</option>
    {% for k in ['deposit', 'purchase', 'sale', 'refund', 'withdraw', 'withdraw_refund', 'bonus', 'admin', 'package', 'store_fee', 'doping'] %}<option value="{{ k }}" {{ 'selected' if kind == k }}>{{ k|kindlabel }}</option>{% endfor %}</select></div>
  <div class="field"><button class="btn" type="submit">Filtrele</button></div>
</form>
{% if page.rows %}
<div class="table-wrap"><table>
  <tr><th>No</th><th>Tarih</th><th>Kullanıcı</th><th>Tür</th><th>Açıklama</th><th class="right">Tutar</th><th class="right">Bakiye</th></tr>
  {% for t in page.rows %}<tr>
    <td>#{{ t.id }}</td><td class="nowrap">{{ t.created_at|dt }}</td>
    <td><a href="{{ url_for('admin.user', uid=t.user_id) }}">{{ t.username }}</a></td>
    <td>{{ t.kind|kindlabel }}</td><td>{{ t.description }}</td>
    <td class="right nowrap"><b class="{{ 'pos' if t.amount > 0 }}">{{ '+' if t.amount > 0 }}{{ t.amount|money }}</b></td>
    <td class="right nowrap muted">{{ t.balance_after|money }}</td>
  </tr>{% endfor %}
</table></div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('İşlem bulunamadı') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["admin_log.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import pager, empty %}
{% block title %}Yönetici Günlüğü{% endblock %}
{% block heading %}Yönetici günlüğü{% endblock %}
{% block panel %}
{% if page.rows %}
<div class="table-wrap"><table>
  <tr><th>No</th><th>Tarih</th><th>İşlem</th><th>Ayrıntı</th><th>IP</th></tr>
  {% for l in page.rows %}<tr><td>#{{ l.id }}</td><td class="nowrap">{{ l.created_at|dt }}</td><td><b>{{ l.action }}</b></td><td>{{ l.detail }}</td><td class="log-ip">{{ l.ip }}</td></tr>{% endfor %}
</table></div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Kayıt yok') }}</div>{% endif %}
{% endblock %}
"""
