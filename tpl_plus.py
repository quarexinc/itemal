"""Mağaza+ şablonları (Jinja). Emoji kullanılmaz."""

TEMPLATES = {}

TEMPLATES["seller_showcase.html"] = r"""
{% extends "seller_base.html" %}
{% from "_macros.html" import ic with context %}
{% block title %}Vitrin ayarları{% endblock %}
{% block panel %}
<div class="page-h"><h1>Vitrin ayarları</h1><a class="btn btn-ghost btn-sm" href="{{ path }}" target="_blank" rel="noopener">{{ ic('external') }}Mağazamı gör</a></div>

<div class="card mb">
  <h3 class="mt0">Mağaza adresin</h3>
  <p class="muted small">Müşterilerine kolay bir adres ver: <b>{{ host }}/magazaadin</b>. Adresi sosyal medya, Discord ve kartvizitlerde paylaşabilirsin.</p>
  <div class="slug-box">
    <div class="slug-link"><span class="muted">{{ host }}/</span><b>{{ u.store_slug or u.username }}</b></div>
    <button type="button" class="btn btn-ghost btn-sm" data-copy="{{ link }}">{{ ic('copy') }}Kopyala</button>
    <a class="btn btn-ghost btn-sm" href="{{ url_for('seller.showcase_qr') }}" download="magaza-qr.svg">{{ ic('download') }}QR kod</a>
  </div>
  <form method="post" action="{{ url_for('seller.showcase') }}" class="row mt"{% if slug_fee %} data-fee-field="slug" data-fee-confirm="Mağaza adresini değiştirmek {{ slug_fee|money }} tutarında ücretlidir ve bakiyenden düşülür. Onaylıyor musun?"{% endif %}>
    {{ csrf_field() }}<input type="hidden" name="action" value="slug">
    <div class="field slug-field" style="flex:1;min-width:240px;margin:0"><label for="slug">Yeni adres</label>
      <div class="input-btn"><span class="pre-addon">{{ host }}/</span><input type="text" id="slug" name="slug" value="{{ u.store_slug }}" placeholder="{{ u.username|lower }}" maxlength="30" pattern="[A-Za-z0-9_\-]{3,30}" autocomplete="off" {{ 'disabled' if cool }}></div>
    </div>
    <button class="btn" type="submit" {{ 'disabled' if cool }}>Kaydet</button>
  </form>
  {% if slug_fee %}<p class="fee-note mt">Adres değişikliği <b>{{ slug_fee|money }}</b> ücretlidir ve bakiyenden düşülür (bakiyen: {{ balance|money }}). İlk belirleme ücretsizdi.</p>
  {% else %}<p class="muted small mt">İlk adres belirleme ücretsizdir; sonraki değişiklikler {{ fee_slug_amount|money }} ücretlidir.</p>{% endif %}
  {% if cool %}<p class="muted small mt">Adresi en sık 7 günde bir değiştirebilirsin. {{ cool|int }} gün sonra tekrar değiştirebilirsin.</p>
  {% else %}<p class="muted small mt">3-30 karakter; harf, rakam, tire ve alt çizgi. Boş bırakırsan kullanıcı adın kullanılır. Eski adresin 30 gün boyunca yeni adresine yönlenir.</p>{% endif %}
  <div class="grid g3 mt">
    <div class="stat"><div class="k">Mağaza ziyareti</div><div class="v">{{ u.store_views }}</div><div class="s">Tekil ziyaretçi sayısı</div></div>
    <div class="stat"><div class="k">Durum</div><div class="v" style="font-size:1.1rem">{{ 'Tatilde' if vac else 'Siparişe açık' }}</div></div>
    <div class="stat"><div class="k">Tema</div><div class="v" style="font-size:1.1rem">{{ themes[u.store_theme][0] if u.store_theme in themes else 'Mor (varsayılan)' }}</div></div>
  </div>
</div>

<div class="card mb">
  <h3 class="mt0">Görünüm ve bağlantılar</h3>
  <form method="post" action="{{ url_for('seller.showcase') }}">
    {{ csrf_field() }}<input type="hidden" name="action" value="look">
    <div class="field"><label>Mağaza tema rengi</label>
      <div class="theme-sws">
        {% for key, t in themes.items() %}{% set lock = (key not in free_themes) and not themes_open %}<label class="theme-sw{{ ' locked' if lock }}" title="{{ t[0] }}{{ ' (Premium Vitrin gerekir)' if lock }}"><input type="radio" name="theme" value="{{ key }}" {{ 'checked' if (u.store_theme or '') == key }} {{ 'disabled' if lock }}><i style="background:{{ t[1] }}"></i><span>{{ t[0] }}{% if lock %} &middot; kilitli{% endif %}</span></label>{% endfor %}
      </div>
      {% if not themes_open %}<small class="muted">Kilitli renkler için <a href="{{ url_for('seller.packages') }}">Premium Vitrin</a> ya da Elmas paketi gerekir.</small>{% endif %}
    </div>
    <div class="field"><label for="notice">Mağaza duyurusu</label><input type="text" id="notice" name="notice" value="{{ u.store_notice }}" maxlength="140" placeholder="Örnek: Hafta sonu tüm ilanlarda stok yenilendi"><small class="muted">Mağaza sayfanın en üstünde bir çubukta görünür. Boş bırakırsan gösterilmez.</small></div>
    <div class="grid g2">
      <div class="field"><label for="discord">Discord sunucusu</label><input type="text" id="discord" name="discord" value="{{ u.store_discord }}" maxlength="80" placeholder="discord.gg/davetkodu"></div>
      <div class="field"><label for="telegram">Telegram</label><input type="text" id="telegram" name="telegram" value="{{ u.store_telegram }}" maxlength="80" placeholder="@kullaniciadi"></div>
      <div class="field"><label for="instagram">Instagram</label><input type="text" id="instagram" name="instagram" value="{{ u.store_instagram }}" maxlength="80" placeholder="@kullaniciadi"></div>
      <div class="field"><label for="web">Web sitesi</label><input type="text" id="web" name="web" value="{{ u.store_web }}" maxlength="120" placeholder="https://siteadi.com"></div>
    </div>
    <button class="btn" type="submit">Kaydet</button>
  </form>
</div>

<div class="grid g2 mb">
  <div class="card">
    <h3 class="mt0">Tatil modu</h3>
    {% if vac %}
      <div class="notice warn">Mağazan tatilde{% if u.vacation_until %}: <b>{{ u.vacation_until|dt }}</b> tarihine kadar{% endif %}. Yeni sipariş alınmıyor, ilanların görünmeye devam ediyor.</div>
      <form method="post" action="{{ url_for('seller.showcase') }}">{{ csrf_field() }}<input type="hidden" name="action" value="vacation_off"><button class="btn" type="submit">Tatili bitir</button></form>
    {% else %}
      <p class="muted small">Müsait değilken siparişleri geçici olarak durdur. Alıcılar mağaza ve ilan sayfanda bilgilendirilir; ilanların silinmez ve sıralaman bozulmaz.</p>
      <form method="post" action="{{ url_for('seller.showcase') }}">
        {{ csrf_field() }}<input type="hidden" name="action" value="vacation_on">
        <div class="field"><label for="until">Bitiş tarihi (isteğe bağlı)</label><input type="date" id="until" name="until"><small class="muted">En fazla 60 gün. Boş bırakırsan sen kapatana kadar sürer.</small></div>
        <button class="btn btn-line" type="submit" data-confirm="Mağazan tatil moduna alınsın mı? Yeni sipariş alınmaz.">Tatil moduna al</button>
      </form>
    {% endif %}
  </div>
  <div class="card">
    <h3 class="mt0">Otomatik karşılama mesajı</h3>
    <p class="muted small">Bir alıcı sana ilk kez mesaj yazdığında bu metin otomatik gönderilir. Teslimat süresi, çalışma saatleri ya da sık sorulan sorular için ideal.</p>
    <form method="post" action="{{ url_for('seller.showcase') }}">
      {{ csrf_field() }}<input type="hidden" name="action" value="reply">
      <div class="field"><textarea name="auto_reply" maxlength="400" style="min-height:110px" placeholder="Merhaba, mağazamıza hoş geldin. Kodlar ödeme anında teslim edilir; sorunu buraya yazabilirsin.">{{ u.auto_reply }}</textarea></div>
      <button class="btn" type="submit">Kaydet</button>
    </form>
  </div>
</div>

<div class="card">
  <h3 class="mt0">Aylık kazanç hedefi</h3>
  <p class="muted small">Hedefini yaz, genel bakış sayfasında bu ayki ilerlemeni göster. Hedef yalnızca sana görünür.</p>
  {% if goal %}<div class="goal-bar mb"><div class="meter"><i style="width:{{ goal.pct }}%"></i></div><div class="spread small"><span>{{ goal.got|money }} / {{ goal.goal|money }}</span><b>%{{ goal.pct }}</b></div></div>{% endif %}
  <form method="post" action="{{ url_for('seller.showcase') }}" class="row">
    {{ csrf_field() }}<input type="hidden" name="action" value="goal">
    <div class="field" style="margin:0;flex:1;min-width:200px"><label for="goal">Hedef (TL, net kazanç)</label><input type="text" id="goal" name="goal" inputmode="decimal" value="{{ (u.sales_goal / 100)|int if u.sales_goal else '' }}" placeholder="Örnek: 5000"></div>
    <button class="btn" type="submit">Kaydet</button>
  </form>
</div>
{% endblock %}
"""

TEMPLATES["seller_customers.html"] = r"""
{% extends "seller_base.html" %}
{% from "_macros.html" import pager, empty, avatar %}
{% block title %}Müşterilerim{% endblock %}
{% block panel %}
<div class="page-h"><h1>Müşterilerim</h1><a class="btn btn-ghost btn-sm" href="{{ url_for('seller.customers_csv') }}">CSV olarak indir</a></div>
<div class="grid g4 mb">
  <div class="stat"><div class="k">Müşteri</div><div class="v">{{ sums.n }}</div></div>
  <div class="stat good"><div class="k">Tekrar alışveriş yapan</div><div class="v">{{ sums.repeat }}</div><div class="s">{% if sums.n %}%{{ (sums.repeat * 100 / sums.n)|round|int }} sadakat oranı{% endif %}</div></div>
  <div class="stat"><div class="k">Toplam ciro</div><div class="v">{{ sums.spent|money }}</div></div>
  <div class="stat"><div class="k">Müşteri başı</div><div class="v">{{ ((sums.spent / sums.n)|int if sums.n else 0)|money }}</div><div class="s">Ortalama harcama</div></div>
</div>
<form class="filters" method="get" action="{{ url_for('seller.customers') }}">
  <div class="field grow"><label for="q">Kullanıcı adı</label><input type="search" id="q" name="q" value="{{ text }}"></div>
  <div class="field"><label for="sirala">Sırala</label><select id="sirala" name="sirala">{% for k, v in sorts.items() %}<option value="{{ k }}" {{ 'selected' if sort == k }}>{{ v[0] }}</option>{% endfor %}</select></div>
  <div class="field"><button class="btn" type="submit">Uygula</button></div>
</form>
{% if page.rows %}
<div class="table-wrap"><table>
  <tr><th>Müşteri</th><th class="right">Sipariş</th><th class="right">Adet</th><th class="right">Toplam harcama</th><th>İlk alışveriş</th><th>Son alışveriş</th><th></th></tr>
  {% for c in page.rows %}<tr>
    <td><div class="row" style="flex-wrap:nowrap">{{ avatar(c.username, c.avatar, 'sm') }}<b>{{ c.username }}</b></div></td>
    <td class="right">{{ c.orders }}</td><td class="right">{{ c.qty }}</td><td class="right nowrap">{{ c.spent|money }}</td>
    <td class="nowrap muted">{{ c.first_at|dt(false) }}</td><td class="nowrap">{{ c.last_at|dt }}</td>
    <td>{% if c.orders >= 5 %}<span class="badge b-ok">Sadık müşteri</span>{% elif c.orders >= 2 %}<span class="badge b-info">Tekrar müşteri</span>{% else %}<span class="badge b-muted">Yeni</span>{% endif %}</td>
  </tr>{% endfor %}
</table></div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Henüz müşterin yok', 'İlk siparişten sonra alıcılar burada listelenir.') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["admin_stores.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import pager, empty, ic with context %}
{% block title %}Mağazalar{% endblock %}
{% block heading %}Mağazalar{% endblock %}
{% block panel %}
<div class="grid g4 mb">
  <div class="stat"><div class="k">Mağaza</div><div class="v">{{ kpi.n }}</div></div>
  <div class="stat"><div class="k">Özel adresli</div><div class="v">{{ kpi.custom }}</div></div>
  <div class="stat"><div class="k">Tatilde</div><div class="v">{{ kpi.vac }}</div></div>
  <div class="stat"><div class="k">Toplam mağaza ziyareti</div><div class="v">{{ kpi.views }}</div></div>
</div>
<form class="filters" method="get" action="{{ url_for('admin.stores') }}">
  <div class="field grow"><label for="q">Ara</label><input type="search" id="q" name="q" value="{{ text }}" placeholder="Kullanıcı adı, mağaza adı veya adres"></div>
  <div class="field"><label for="durum">Filtre</label><select id="durum" name="durum"><option value="">Hepsi</option>{% for k, v in [('adresli', 'Özel adresli'), ('tatil', 'Tatildeki'), ('gercek', 'Gerçek mağazalar'), ('demo', 'Örnek mağazalar')] %}<option value="{{ k }}" {{ 'selected' if flt == k }}>{{ v }}</option>{% endfor %}</select></div>
  <div class="field"><label for="sirala">Sırala</label><select id="sirala" name="sirala">{% for k, v in sorts.items() %}<option value="{{ k }}" {{ 'selected' if sort == k }}>{{ v[0] }}</option>{% endfor %}</select></div>
  <div class="field"><button class="btn" type="submit">Uygula</button></div>
</form>
{% if page.rows %}
<div class="table-wrap"><table>
  <tr><th>Mağaza</th><th>Adres</th><th class="right">İlan</th><th class="right">Satış</th><th class="right">30 gün ciro</th><th class="right">Ziyaret</th><th>Durum</th><th></th></tr>
  {% for s in page.rows %}<tr>
    <td><a href="{{ url_for('admin.user', uid=s.id) }}"><b>{{ s.store_name or s.username }}</b></a>{{ pkg_marks(s.id) }}<div class="muted small">@{{ s.username }}{% if s.is_demo %} &middot; örnek{% endif %}</div></td>
    <td class="nowrap"><a href="{{ url_for('storefront', username=s.username) }}" target="_blank" rel="noopener">/{{ s.store_slug or s.username }}</a>{% if not s.store_slug %}<div class="muted small">varsayılan</div>{% endif %}</td>
    <td class="right">{{ s.listings }}</td><td class="right">{{ s.sold }}</td><td class="right nowrap">{{ s.gmv30|money }}</td><td class="right">{{ s.store_views }}</td>
    <td>{% if s.is_banned %}<span class="badge b-bad">Yasaklı</span>{% elif s.store_vacation %}<span class="badge b-warn">Tatilde</span>{% else %}<span class="badge b-ok">Açık</span>{% endif %}</td>
    <td class="actions"><div class="mini-form">
      <form method="post" action="{{ url_for('admin.store_action', uid=s.id) }}" class="row" style="flex-wrap:nowrap">{{ csrf_field() }}<input type="hidden" name="action" value="slug"><input type="text" name="slug" value="{{ s.store_slug }}" placeholder="adres" maxlength="30" style="width:130px;padding:6px 8px" aria-label="Mağaza adresi"><button class="btn btn-line btn-sm" type="submit">Adresi ata</button></form>
      {% if s.store_vacation %}<form method="post" action="{{ url_for('admin.store_action', uid=s.id) }}">{{ csrf_field() }}<input type="hidden" name="action" value="vacation_off"><button class="btn btn-ghost btn-sm" type="submit">Tatili bitir</button></form>{% endif %}
      <form method="post" action="{{ url_for('admin.store_action', uid=s.id) }}" data-confirm="Mağaza duyurusu ve sosyal bağlantılar temizlensin mi?">{{ csrf_field() }}<input type="hidden" name="action" value="reset_notice"><button class="btn btn-ghost btn-sm" type="submit">İçeriği temizle</button></form>
    </div></td>
  </tr>{% endfor %}
</table></div>{{ pager(page) }}
{% else %}<div class="card">{{ empty('Mağaza bulunamadı') }}</div>{% endif %}
{% endblock %}
"""

TEMPLATES["admin_finance.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import bars, empty %}
{% block title %}Finans{% endblock %}
{% block heading %}Finans ve kasa{% endblock %}
{% block panel %}
<div class="spread mb">
  <div class="tabs" style="margin:0">{% for k, v in ranges.items() %}<a class="{{ 'on' if days == k }}" href="{{ url_for('admin.finance', gun=k) }}">{{ v }}</a>{% endfor %}</div>
  <a class="btn btn-line" href="{{ url_for('admin.export', what='siparisler') }}">Siparişleri indir</a>
</div>
<div class="grid g4 mb">
  <div class="stat good"><div class="k">Platform geliri</div><div class="v">{{ revenue|money }}</div><div class="s">Kupon maliyeti düşülünce {{ net_revenue|money }}</div></div>
  <div class="stat"><div class="k">Satış komisyonu</div><div class="v">{{ rev.commission|money }}</div><div class="s">{{ rev.orders }} sipariş, ciro {{ rev.gmv|money }}</div></div>
  <div class="stat"><div class="k">Doping geliri</div><div class="v">{{ rev.doping|money }}</div></div>
  <div class="stat"><div class="k">Paket geliri</div><div class="v">{{ rev.packages|money }}</div><div class="s">Çekim kesintisi {{ rev.wd_fee|money }}</div></div>
</div>
<div class="card mb"><h3 class="mt0">Günlük platform geliri</h3>{{ bars(series, true) }}</div>

<div class="grid g2 mb">
  <div class="card">
    <h3 class="mt0">Kasa durumu (tüm zamanlar)</h3>
    <dl class="kv">
      <dt>Onaylanan bakiye yüklemeleri</dt><dd class="pos">{{ cash.cash_in|money }}</dd>
      <dt>Ödenen çekimler</dt><dd class="neg">-{{ cash.cash_out|money }}</dd>
      <dt>Net nakit</dt><dd><b>{{ net_cash|money }}</b></dd>
    </dl>
    <hr>
    <h4>Kullanıcılara borç (yükümlülük)</h4>
    <dl class="kv">
      <dt>Kullanıcı bakiyeleri</dt><dd>{{ cash.balances|money }}</dd>
      <dt>Emanetteki satıcı alacakları</dt><dd>{{ cash.held|money }}</dd>
      <dt>Bekleyen çekim talepleri</dt><dd>{{ cash.pending_wd|money }}</dd>
      <dt>Toplam</dt><dd><b>{{ liabilities|money }}</b></dd>
    </dl>
    <hr>
    <dl class="kv">
      <dt>Yönetici bakiye düzeltmeleri</dt><dd>{{ cash.adjustments|money }}</dd>
      <dt>Tahmini kasa farkı</dt><dd><b class="{{ 'pos' if est_profit >= 0 else 'neg' }}">{{ est_profit|money }}</b></dd>
    </dl>
    <p class="muted small">Tahmini kasa farkı = net nakit - borçlar + yönetici düzeltmeleri. Platformun elinde kalan (komisyon, doping, paket, kesinti) tutarla örtüşmesi beklenir; büyük bir sapma, kayıt dışı bir bakiye müdahalesine işaret eder.</p>
  </div>
  <div class="card">
    <h3 class="mt0">Bekleyenler ve uyarılar</h3>
    <dl class="kv">
      <dt>Onay bekleyen yüklemeler</dt><dd>{{ cash.pending_dep|money }}</dd>
      <dt>Onay bekleyen çekimler</dt><dd>{{ cash.pending_wd|money }}</dd>
      <dt>Örnek hesaplarda biriken tutar</dt><dd class="muted">{{ cash.demo_balances|money }}</dd>
    </dl>
    {% if cash.pending_wd > net_cash and net_cash >= 0 %}<div class="notice warn">Bekleyen çekimler net nakdi aşıyor; ödemeden önce kasayı kontrol et.</div>{% endif %}
    <hr>
    <h3>İlk 8 mağaza (komisyon)</h3>
    {% if top_stores %}<div class="table-wrap"><table>
      <tr><th>Mağaza</th><th class="right">Sipariş</th><th class="right">Ciro</th><th class="right">Komisyon</th></tr>
      {% for s in top_stores %}<tr><td><a href="{{ url_for('admin.user', uid=s.id) }}">{{ s.store_name or s.username }}</a></td><td class="right">{{ s.orders }}</td><td class="right nowrap">{{ s.gmv|money }}</td><td class="right nowrap">{{ s.fee|money }}</td></tr>{% endfor %}
    </table></div>{% else %}{{ empty('Bu dönemde satış yok') }}{% endif %}
  </div>
</div>
<div class="card">
  <h3 class="mt0">Büyük hareketler (5.000 ₺ ve üzeri)</h3>
  {% if big %}<div class="table-wrap"><table>
    <tr><th>Tarih</th><th>Kullanıcı</th><th>Tür</th><th>Açıklama</th><th class="right">Tutar</th></tr>
    {% for t in big %}<tr><td class="nowrap">{{ t.created_at|dt }}</td><td><a href="{{ url_for('admin.user', uid=t.uid) }}">{{ t.username }}</a></td><td>{{ kindlabel(t.kind) }}</td><td class="muted">{{ t.description[:60] }}</td><td class="right nowrap {{ 'pos' if t.amount > 0 else 'neg' }}">{{ t.amount|money }}</td></tr>{% endfor %}
  </table></div>{% else %}{{ empty('Bu dönemde büyük hareket yok') }}{% endif %}
</div>
{% endblock %}
"""

TEMPLATES["admin_feed.html"] = r"""
{% extends "admin_base.html" %}
{% from "_macros.html" import empty, ic with context %}
{% block title %}Canlı akış{% endblock %}
{% block heading %}Canlı akış{% endblock %}
{% block panel %}
<div class="tabs">
  {% for k, v in kinds.items() %}<a class="{{ 'on' if kind == k }}" href="{{ url_for('admin.feed', tur=k or None) }}">{{ v }}</a>{% endfor %}
</div>
{% if rows %}
<div class="card feed">
  {% for r in rows %}
  <div class="feed-row">
    <i class="feed-dot k-{{ r.kind }}" aria-hidden="true"></i>
    <div class="feed-main">
      <div>{% if r.link %}<a href="{{ r.link }}">{{ r.title[:90] }}</a>{% else %}{{ r.title[:90] }}{% endif %}</div>
      <div class="muted small">{{ r.sub }}</div>
    </div>
    <div class="right nowrap">{% if r.amount %}<b>{{ r.amount|money }}</b>{% endif %}<div class="muted small">{{ r.ts|dt }}</div></div>
  </div>
  {% endfor %}
</div>
<p class="muted small mt">Son olaylar, tüm türler birleşik ve zamana göre sıralı gösterilir. Sayfayı yenileyerek güncelleyebilirsin.</p>
{% else %}<div class="card">{{ empty('Henüz olay yok') }}</div>{% endif %}
{% endblock %}
"""
