# itemal - e-pin pazaryeri

Flask ile yazılmış, kullanıcıdan kullanıcıya e-pin / dijital kod pazaryeri. Koyu, animasyonlu modern arayüz (kategori başına renk), emojisiz.
HTML şablonları ve CSS/JS dosyaları uygulama her başladığında **otomatik üretilir** (`templates/` ve `static/`).
Metin tabanlı statik dosyalar (`assets*.py`: CSS, JS, `logo.svg`, `favicon.svg`) ve ikili kaynaklar (`static_src/`: kategori banner'ları `static_src/kategori/*.webp`) aynı adımda `public/static/` altına yazılır/kopyalanır; `python manage.py build` ve Vercel paketlemesi bu klasörü de içermelidir. Banner'lar `tools/make_category_banners.py` ile üretilmiştir (belge amaçlı, Pillow gerekir). Kategoriye görsel yüklenmemişse `/static/kategori/<slug>.webp` (yoksa `genel.webp`) kullanılır (`catbanner.py`, Jinja: `category_banner_url(kategori, 'wide'|'mobile'|'card')`).

## Kurulum

```bash
pip install -r requirements.txt
python app.py
```

Site: http://127.0.0.1:5000  -  Yönetici paneli: http://127.0.0.1:5000/admin/giris (`ADMIN_URL_PREFIX` tanımlıysa o yolun altında)

Yönetici kullanıcı adı ve şifresi `.env` dosyasındadır (`ADMIN_USERNAME`, `ADMIN_PASSWORD`).

**Yönetici girişi güvenliği:** varsayılan olarak giriş iki adımlıdır. İlk girişte (kullanıcı adı + parola doğruysa) zorunlu kurulum sayfası açılır: authenticator uygulamasıyla QR kodu tara, 6 haneli kodu gir, 10 yedek kodu kaydet. Sonraki girişlerde `/admin/dogrula` sayfasında kod (ya da bir yedek kod) istenir. Panelde **Güvenlik** sayfası: yedek kodları yenileme, 2FA kapatma (`optional` modda), son giriş geçmişi ve oturum ayarları. 5 hatalı girişte IP kilitlenir (15 dk, 1 saat, 24 saat), 2 hatadan sonra CAPTCHA zorunlu olur.
- **Telefon ve yedek kodlar kaybolursa:** sunucuda `python manage.py admin-2fa-reset` (2FA kaydını siler; sonraki girişte yeniden kurulum istenir).
- **Acil durum bayrağı:** `.env` içine `ADMIN_2FA=off` yaz, uygulamayı yeniden başlat, sorunu çöz, satırı kaldır.
- **Önerilen canlı ayarlar:** `ADMIN_2FA=required`, sabit IP/VPN varsa `ADMIN_ALLOWED_IPS`, tahmin edilmesi zor bir `ADMIN_URL_PREFIX`, `ADMIN_PASSWORD_HASH` (`python manage.py hash-admin`). Ayrıntı: `docs/SECURITY.md`.
Kullanıcı, ilan, sipariş vb. tüm veriler `data/epin.db` (SQLite) dosyasında tutulur. Yüklenen kimlik görselleri `uploads/kyc/`, kapak ve profil görselleri `uploads/` altındadır.

`.env` dosyasını başkalarıyla paylaşma. Canlıya çıkmadan önce `ADMIN_PASSWORD`, `SECRET_KEY` ve `PAYMENT_WEBHOOK_SECRET` değerlerini değiştir.

| Değişken | Açıklama |
| --- | --- |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | Yönetici girişi |
| `ADMIN_2FA` | Yönetici iki adımlı doğrulama (TOTP): `required` (varsayılan, ilk girişte zorunlu kurulum) / `optional` / `off` (yalnızca acil durum) |
| `ADMIN_ALLOWED_IPS` | İsteğe bağlı: virgülle IP/CIDR. Tanımlıysa izin dışındaki IP'ler `/admin/*` için 404 alır |
| `ADMIN_URL_PREFIX` | İsteğe bağlı yönetim yolu (varsayılan `/admin`), örn. `/yonetim-x7` |
| `ADMIN_BIND_IP` | `1`: yönetici oturumu istemcinin /24 ağına bağlanır |
| `ADMIN_FAIL_DELAY` | Başarısız yönetici girişinde en az bekleme, saniye (varsayılan `0.6`) |
| `SECRET_KEY` | Oturum imzası (uzun ve rastgele olmalı) |
| `PAYMENT_WEBHOOK_SECRET` | Ödeme bildirimi imza anahtarı |
| `DATABASE_PATH` | SQLite dosya yolu (varsayılan `data/epin.db`) |
| `REGENERATE_TEMPLATES` | `1`: her açılışta şablonları yeniden yaz. Şablonları elle düzenlemek istersen `0` yap |
| `AUTO_DEMO` | `1` (varsayılan): veritabanında hiç ilan yoksa açılışta demo mağaza/ilan/yorum yüklenir (arka planda ~15 sn sürer, site hemen açılır). Canlıda `0` yap |
| `COOKIE_SECURE` | HTTPS arkasında `1` yap |
| `HOST`, `PORT`, `DEBUG` | Sunucu ayarları |

## Vercel'e yayinlama

Proje Vercel'de calisacak sekilde hazirdir: `app.py` (Flask giris noktasi, Vercel otomatik algilar), `vercel.json` (bolge ve gunluk cron), `.python-version`, `requirements.txt`.
`templates/` ve `public/static/` depoda hazir bulunur (Vercel'de dosya sistemi salt okunurdur). Kodda sablon/CSS/JS degistirirsen gondermeden once `python manage.py build` calistir.

1. Veritabani: Turso hesabi ac (turso.tech), `turso db create itemal`, `turso db show itemal --url`, `turso db tokens create itemal`. Yerel SQLite Vercel'de kalici degildir; gorseller de `media` tablosunda saklanir.
2. Vercel'de bu depoyu iceri aktar (Framework: Other). Build komutu gerekmez.
3. Environment Variables: `ADMIN_USERNAME`, `ADMIN_PASSWORD` (ya da `ADMIN_PASSWORD_HASH`), `SECRET_KEY`, `PAYMENT_WEBHOOK_SECRET`, `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`, `CRON_SECRET`. Istege bagli: `ADMIN_2FA`, `ADMIN_URL_PREFIX`, `ADMIN_ALLOWED_IPS`, `AUTO_DEMO=0`.
4. Deploy et. Ilk istekte sema Turso'ya otomatik kurulur (`python manage.py init-db` ile onceden de kurulabilir). Yonetim paneli: `/admin/giris`.
5. Gunluk is (`/cron/gunluk`, emanet serbest birakma ve temizlik) `vercel.json` ile her gun 03:00 UTC calisir.

Notlar: Vercel islevleri en fazla 4,5 MB govde kabul eder (yuklemeler buna gore sinirlanir); arka plan is parcacigi yoktur, demo veri yonetim panelinden (Sistem > Demo veri) yuklenir. Turso taklidi ile yerelde denemek icin `tools/fake_turso.py`.

## Özellikler

**Alıcı / genel**
- Kayıt, giriş, profil, şifre değiştirme, profil fotoğrafı
- Hesap güvenliği: giriş/kayıtta kendi sunucumuzda üretilen CAPTCHA (kayıtta her zaman, girişte 3 hatalı denemeden sonra), honeypot ve form zaman damgası, kademeli IP kilidi, yeni cihaz bildirimi, son girişler, "tüm cihazlardan çıkış", isteğe bağlı iki adımlı doğrulama (TOTP + yedek kodlar; satıcılar için yönetici ayarıyla zorunlu yapılabilir). Ayrıntı: `docs/SECURITY.md`
- İlan listesi: arama, kategori, fiyat, stok, puan filtreleri ve sıralama
- İlan sayfası: kapak görseli, açıklama, satıcı rozetleri, yorumlar, benzer ilanlar
- Bakiye yükleme talebi (yönetici onaylı) ve ödeme bildirimi ile otomatik onay
- Anında teslim: satın alınan kodlar sipariş sayfasında görünür
- Sipariş sonrası satıcıya puan ve yorum (sipariş başına bir kez)
- Alıcı - satıcı mesajlaşma, destek talepleri (ticket), işlem geçmişi

**Satıcı paneli** (`/satici`)
- Kazanç özeti, günlük grafik, stoğu azalan ilanlar, satış listesi ve CSV çıktısı
- İlan oluşturma / düzenleme, kapak görseli, toplu kod ekleme (mükerrerler atlanır), duraklatma
- Komisyon sayfası ve ilan formunda anlık net kazanç hesabı
- Yorumlara yanıt, mağaza bilgileri, profil fotoğrafı/logo ve mağaza kapak görseli
- API anahtarları (anahtar yalnızca oluşturulduğunda bir kez gösterilir)

**Kimlik (KYC) ve satıcı başvurusu**
- Kimlik kartı veya ehliyet: ön, arka ve belgeyle selfie
- Görseller sunucuda yeniden işlenir (EXIF silinir); çözünürlük, karanlık/parlak, bulanıklık kontrolü; aynı görselin veya kimlik numarasının başka hesapta kullanılması uyarısı
- Yönetici onayı için üç kontrol kutusu (belge, bilgiler, yüz eşleşmesi) zorunlu; ret nedenleri hazır
- Satıcı olmak için yalnızca yönetici onayı gerekir (ayarlardan kapatılabilir); kimlik yalnızca ilk para çekiminde istenir
- İlan verirken telefon numarası zorunludur (yalnızca yönetime görünür)

**Rozetler**
- Otomatik: Kimliği Doğrulandı, Onaylı Satıcı, Güvenilir Satıcı (satış adedi, yorum sayısı ve puana göre; eşikler ayarlanabilir)
- Elle verilen: Güvenilir Satıcı, Mağaza Üyesi, Yıldız Satıcı

**Komisyon**
- Genel oran, kategoriye özel oran, satıcıya özel oran. Öncelik: satıcı, kategori, genel
- Uygulanan oran her siparişe kaydedilir; sonradan oran değişse de eski siparişler etkilenmez
- Çekimde ayrıca kesinti oranı
- Yönetici komisyon raporu (kategori, satıcı, günlük grafik) ve CSV
- Varsayılan: yalnızca satış kazancı ve yönetici eklemeleri çekilebilir, yüklenen bakiye çekilemez (ayarlardan değiştirilebilir)

**Vitrin (yeni)**
- Slider, güven şeridi, canlı satış bandı, "Günün oyunları" posterleri ve geri sayım, reklam şeritleri, fırsat ürünleri, çok satanlar, öne çıkan satıcılar, yorumlar, sayaçlı istatistik bandı
- 20 kategori (Discord, Steam, Roblox, Valorant, PUBG, Fortnite, Free Fire, Netflix, Spotify, Google Play vb.), kategori sayfası ve kategori başlıkları. Kategori afişleri `Admin > Kategoriler > Toplu afiş yükle` ile `discord.jpg`, `steam.png` gibi dosya adlarıyla tek seferde yüklenir
- Canlı arama önerisi, favoriler, bildirimler, kupon kodu, indirimli fiyat rozeti, son gezilenler, paylaş düğmesi
- robots.txt ve sitemap.xml, bakım modu, kayıt açma/kapama

**Yönetici paneli** (`/admin`)
- Yeni: genel arama, raporlar (7/30/90/365 gün), CSV dışa aktarma, banner yönetimi (gösterim/tıklama sayaçlı), kupon yönetimi, toplu duyuru/bildirim, kullanıcı notu, IP ve giriş geçmişi, kategori rengi/afişi/günün oyunu, sistem sağlığı, veritabanı yedeği indirme, demo veri yükleme/silme
- Demo veri ilk açılışta kendiliğinden yüklenir (`AUTO_DEMO=0` ile kapatılır); admin panelinden silersen geri gelmez. Eski sürüm demo veri açılışta otomatik yenilenir.
- Kupon indirimini platform karşılar: satıcı kazancı ve komisyon indirimden etkilenmez
- Pano, kullanıcılar (engelleme, bakiye düzenleme, satıcı yetkisi, rozet, özel komisyon, şifre sıfırlama)
- **Üye oluşturma** ve **ilan oluşturma** (kapak ve kodlarla, herhangi bir satıcı adına), ilan öne çıkarma / engelleme
- Bakiye yükleme, çekim talebi, satıcı başvurusu, kimlik onayı
- Destek talepleri: önceliklendirme, yanıt, kullanıcının görmediği iç not, durum değiştirme
- Sohbet denetimi: mesajları okuma ve sohbeti kilitleme (her erişim yönetici günlüğüne yazılır)
- Yorum gizleme, kategoriler, ödeme yöntemleri, entegrasyon, site ayarları, işlem defteri, yönetici günlüğü

**Güven ve ödeme (yeni)**
- Emanet: satın alma tutarı, alıcı siparişi onaylayana kadar satıcıda bloke kalır; onaylanınca bakiyeye geçer. Onay gelmezse `escrow_days` (varsayılan 3 gün) sonunda otomatik aktarılır. Alıcı "Sorun var" derse tutar bloke kalır, yönetici satıcıya aktarır veya alıcıya iade eder
- Şikayet: ilan ve kullanıcı bildirimi, sipariş itirazı; Yönetim > Şikayetler kuyruğundan ilan engelleme, hesap askıya alma, emanet aktarma/iade
- Mağaza yorumları: giriş yapan herkes satıcı profiline yorum yazabilir (kişi başı bir yorum, düzenlenebilir); yönetici gizleyebilir
- Ek rozetler: 100+ Satış, Satış Ustası, Kusursuz Puan, Hızlı Yanıt, Deneyimli Satıcı, Yeni Mağaza, Sadık Alıcı, Topluluk Sesi (otomatik); İş Ortağı, VIP Satıcı (elle)
- Bakiye yükleme ödeme linkleriyle yapılır (kart bilgisi bu sitede hiç alınmaz); banka havalesi bildirimi yalnızca yönetimin açık bıraktığı ödeme yöntemleri varsa görünür
- Canlı bildirim: yeni mesaj/bildirimde ses + tarayıcı bildirimi (izin gerekir) + sayfa içi uyarı; sohbet 1,5 sn'de bir güncellenir ve mesaj yenilemeden gönderilir

**Ödeme linkleri**
- Yönetim > Ödeme linkleri sayfasında başlık, https:// ödeme linki ve sabit fiyat tanımlanır (hazır gelen örnek link pasiftir; kendi linkini yazıp aktif yap).
- Kullanıcı Bakiye Yükle sayfasındaki "Öde" düğmesine basınca link yeni sekmede açılır, aynı sekmede "Ödemen işleniyor" ekranı gelir (ödeme/dekont no yazabilir, vazgeçebilir). Ekran 20 saniyede bir kendiliğinden yenilenir.
- Yönetici Yönetim > Bakiye yüklemeleri sayfasında kaydı onaylayınca fiyat kadar tutar bakiyeye eklenir (reddederse eklenmez). Aynı kayıt iki kez onaylanamaz.
- Kullanıcıya elle bakiye: Yönetim > Kullanıcılar listesindeki "Bakiye ekle" bağlantısı kullanıcı sayfasındaki bakiye formuna götürür.

## API

**Satıcı API'si** - satıcı panelinde `API Erişimi` sayfasından anahtar oluştur. Her istekte `Authorization: Bearer itm_...` gönder. Dakikada 120 istek.

| Uç | Açıklama |
| --- | --- |
| `GET /api/v1/me` | Profil, bakiye, satış özeti |
| `GET /api/v1/listings` | İlanlar |
| `POST /api/v1/listings/<id>/stock` | `{"codes": ["KOD1", "KOD2"]}` ile stok ekler |
| `POST /api/v1/listings/<id>/status` | `{"status": "active"}` veya `"paused"` |
| `GET /api/v1/orders` | Satışlar ve komisyon bilgisi |

**Ödeme bildirimi (webhook)** - `POST /api/webhook/odeme`

```bash
body='{"deposit_id": 12, "amount": "250.00", "status": "success", "transaction_id": "TX-98765"}'
sig=$(printf '%s' "$body" | openssl dgst -sha256 -hmac "$PAYMENT_WEBHOOK_SECRET" | awk '{print $2}')
curl -X POST http://127.0.0.1:5000/api/webhook/odeme -H "Content-Type: application/json" -H "X-Signature: $sig" -d "$body"
```

İmza, ham gövdenin HMAC-SHA256 özetidir. Tutar talep edilenle eşleşmezse reddedilir; aynı `transaction_id` ikinci kez bakiye eklemez. Belirli bir ödeme sağlayıcısına (PayTR, Shopier vb.) bağlamak için sağlayıcının bildirim biçimini bu uca uyarlayan küçük bir dönüştürücü gerekir.

## Demo veri, yedek, bakım

- `Admin > Sistem ve araçlar` sayfasından demo veri (Kodhane, PinPark, Dijital Durak, Arena Pin adlı 4 mağaza; her birinin özgün logosu, kapak görseli ve farklı satış/yorum rakamları; 65 ilan, kart görünümlü ürün görselleri; yorumların hepsi 5 puan, mağaza başına en fazla 10) yüklenir. Demo ilanlar varsayılan olarak satın alınabilir (örnek kodlarla, stokları kendiliğinden yenilenir); Sistem sayfasındaki karttan satışa kapatılabilir. Yalnızca önizleme içindir, canlıda gerçek satıcı ve yorumlarla değiştirilmelidir; canlıya çıkmadan önce aynı sayfadan silinir.
- `Sistem ve araçlar` sayfasında tek tıkla SQLite yedeği indirilir. `uploads/` klasörünü ayrıca yedekle.
- `Ayarlar` sayfasından bakım modu (yöneticiler siteyi görmeye devam eder) ve kayıt kapatma açılır.
- Ters vekil (nginx/caddy) arkasında gerçek IP için `.env` içine `TRUST_PROXY=1` ekle.

## Canlıya alırken

- Ödeme yöntemleri **pasif** gelir ve içlerindeki IBAN / adresler örnektir. `Admin > Ödeme Yöntemleri` bölümünden kendi bilgilerini girip aktifleştir; aksi halde kullanıcılar bakiye yükleyemez.
- HTTPS arkasında çalıştır (nginx / caddy) ve `.env` içinde `COOKIE_SECURE=1` yap. Geliştirme sunucusu yerine `gunicorn -w 2 app:app` gibi bir sunucu kullan. Hız sınırlayıcı bellek içidir; birden fazla işlem çalıştırırsan işlem başına ayrı sayılır.
- `uploads/kyc/` kimlik görselleri içerir. Erişimi yalnızca uygulamaya ver, yedeklerini şifrele ve saklama süresi için KVKK yükümlülüklerini gözden geçir. Veritabanı ve `uploads` klasörünü düzenli yedekle.
- Sohbetler yönetici tarafından görüntülenebilir; kullanıcılar bu konuda sohbet ekranında bilgilendirilir. Gizlilik metnine de ekle.
- Bu proje bir başlangıç noktasıdır. E-pin satışı, ödeme toplama ve kimlik verisi işleme için geçerli mevzuat (vergi, MASAK, KVKK vb.) konusunda uzmanına danış.


## Güvenlik

Yetki denetimi, giriş/istek hız sınırları, girdi doğrulama, CORS kilidi, parola hash'i, güvenli çerez, log maskeleme, XSS savunması ve yükleme sınırları için bkz. `docs/SECURITY.md`. Yönetici şifresini hash'lemek için: `python manage.py hash-admin`.

## Doping, mağaza paketleri ve kategori banner'ları
- **Doping** (Satıcı > Doping, ilan eklerken de seçilebilir): Pazar vitrini (ilanlar sayfası üstü), Kategori vitrini ("Vitrin ürün") ve ana sayfa Reklam banneri; bakiyeden ödenir. Reklam banneri satın alınınca ilanın kapağı ve linkiyle ana sayfa banner dönüsüne otomatik girer. Fiyatlar ve reklam panosu kapasitesi Yönetici > Doping sayfasından değiştirilir. Süresi dolmuş reklam banner'ları `/cron/gunluk` ile temizlenir.
- **Mağaza paketleri** (Satıcı > Paketler): Mavi Tik (250 TL, kalıcı), Altın Mağaza, Elmas Mağaza, Öne Çıkan Mağaza, Düşük Komisyon, Hızlı Teslimat Rozeti. Fiyat/süre/özellikler Yönetici > Paketler'den düzenlenir; satıcıya elle paket verilebilir.
- **Kategori banner'ları:** 20 kategori için hazır görseller `static_src/kategori/` altındadır; Yönetici > Kategoriler'den kendi görselini yükleyince onun yerine geçer.

## Mağaza+ ve topluluk
- **Özel mağaza adresi:** Satıcı > Vitrin ve adres sayfasından `alanadiniz.com/magazaadi`. Ayrılmış kelimeler engellenir, adres 7 günde bir değişir, eski adres 30 gün yönlenir. Yönetici > Mağazalar'dan elle atanır.
- **Vitrin ayarları:** tema rengi (3 ücretsiz; diğerleri Premium Vitrin, Elmas ya da Altın paketiyle), duyuru çubuğu, sosyal bağlantılar, tatil modu, otomatik karşılama, aylık hedef, QR kod; Müşterilerim (CSV), toplu ilan işlemleri, ilan kopyalama.
- **Takip ve çekiliş:** Alıcılar satıcıları takip eder; satıcılar çekiliş açar (aynı anda 3; Çekiliş/Elmas paketiyle daha fazla), süre dolunca kura otomatik çekilir. Yönetici > Çekilişler'den yönetilir.
- **Bildirimler:** tıklanınca tam içerik, durum etiketi ve ilgili sipariş özeti. Mağaza yorumunu yalnızca o mağazadan alışveriş yapanlar yazar.
- **Yeni paketler:** Çekiliş Paketi, Premium Vitrin, Öncelikli Destek; Elmas Mağaza hepsini kapsar. Yönetici ek sayfaları: Finans ve kasa, Canlı akış, Mağazalar, Çekilişler.

## Ödeme yöntemleri
- Yönetici > Ödeme yöntemleri: hazır şablondan ekle (Havale, FAST, Papara, USDT, Bitcoin, Ininal) ya da özel yöntem oluştur; minimum/maksimum tutar, yükleme bonusu (%), tahmini süre, rozet, simge ve renk ayarlanır; tek tıkla aktif/pasif yapılır, yönteme göre onaylı ve bekleyen yükleme özeti görünür.
- Kullanıcı tarafı: Bakiye yükle sayfası yöntem kartları, kopyalanabilir IBAN/cüzdan satırları ve bonus özetiyle çalışır; ilan sayfasında eksik tutar kadar yükleme bağlantısı, sayfa altlığında kabul edilen yöntemler, para çekmede önceki hesabın otomatik doldurulması vardır.
- Bonus, yönetici yüklemeyi onaylayınca ayrı bir işlem satırı olarak eklenir.
