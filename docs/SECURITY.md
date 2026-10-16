# Güvenlik

Bu belge sitedeki güvenlik önlemlerini ve canlıya alırken yapılması gerekenleri özetler. Kodun ilgili yeri parantez içinde.

## Yetki (sunucu tarafı)
- Her istekte kullanıcı veritabanından yeniden okunur; yasaklanan ya da satıcılığı kaldırılan hesap anında yetkisini kaybeder (`app._before`).
- Yönetici alanı blueprint düzeyinde korunur (`admin._guard` -> `adminsec.guard`); oturum 30 dk boşta kalınca ya da 8 saat sonra düşer, ayrıntı aşağıdaki "Yönetici paneli girişi" bölümünde. Satıcı alanı da aynı şekilde (`seller._guard`). İstemciden gelen hiçbir rol/bakiye/durum alanı kullanılmaz (toplu atama yok).
- Sipariş, mesaj, destek talebi, ilan, stok, yorum ve ödeme sonucu gibi nesnelerde sahiplik sorguda denetlenir; başkasının nesnesi 404 döner.
- Şifre değişince diğer cihazlardaki oturumlar düşer (oturumdaki parola parmak izi).
- "Tüm cihazlardan çıkış" ve şifre değişimi `users.sess_ver` sayacını artırır; oturumdaki `sv` eşleşmeyen tüm eski oturumlar bir sonraki istekte düşer, işlemi yapan oturum yenilenir (`account_security.bump_sessions`, `app._before`). Profil > Güvenlik bölümünden yapılır.
- İsteğe bağlı iki adımlı doğrulama (TOTP, RFC 6238; Google Authenticator/Authy uyumlu): anahtar `users.totp_secret` içinde `SECRET_KEY` türevli anahtarla şifreli saklanır, yedek kodlar (10 adet) yalnızca SHA-256 hash'i olarak tutulur ve bir kez gösterilir. Parola doğruysa 5 dk'lık ön oturum açılır (`/giris/dogrula`); gerçek oturum yalnızca kod ya da yedek kod doğrulanınca verilir. Kullanılmış TOTP adımı (`totp_last_step`) ve kullanılmış yedek kod yeniden kabul edilmez (koşullu UPDATE ile yarış durumuna karşı atomik). Kapatma ve yedek kod yenileme parola + kod ister.
- Yönetici ayarı `require_seller_2fa` (varsayılan kapalı): açıkken 2FA'sız satıcı `/satici/*` alanına giremez, `/profil/2fa` sayfasına yönlendirilir (`seller._guard`).
- Güvenlik bildirimleri (uygulama içi): yeni cihaz/IP'den giriş (IP /24 ya da tarayıcı özeti daha önce görülmemişse; ilk girişte yok; IP maskeli, tarayıcı özeti ve saat ile), şifre değişimi, 2FA açma/kapama, yedek kod kullanımı/yenileme ve tüm cihazlardan çıkış.
- Otomatik test: tüm `/admin/*` ve `/satici/*` uçları anonim ve normal kullanıcıyla taranır, başkasının nesnelerine erişim denenir (`e2e`).

## Hız sınırları (SQLite tabanlı; yeniden başlatmada ve çok işlemli çalışmada geçerli)
- Kullanıcı girişi: IP başına 8 / 10 dk, hesap başına 6 / 15 dk, tüm site için 60 / 10 dk. Yönetici girişi: 5 hatada IP kilidi (15 dk, 1 saat, 24 saat), tüm site için 30 hata / saat; iki adımlı kod denemesi IP başına 5 / 10 dk ve tüm site için 30 / saat. Başarılı girişte sayaç sıfırlanır.
- Üye girişi ek korumaları (`account_security.py`, `captcha.py`):
  - **CAPTCHA** (kendi sunucumuzda Pillow ile çizilir, dış servis yok): IP'de 10 dk içinde ya da hesapta 15 dk içinde 3 hatalı denemeye ulaşılınca giriş formunda zorunlu olur (öncesinde formda görünmez); **kayıtta her zaman** zorunlu; destek talebinde kullanıcı 15 dk içinde 3 talep açtıysa zorunlu. Resim: 5-6 karakter, 0/O/1/I/L gibi karışan karakterler yok, dalga/eğim/gürültü bozulması; `/captcha/<kapsam>.png` IP başına dakikada 30, `Cache-Control: no-store`, kapsamlar beyaz liste. Cevap çerezde değil: oturumda yalnızca `SECRET_KEY` anahtarlı HMAC bulunur (çerez okunsa bile cevap çıkarılamaz), sınama 5 dk yaşar, **doğru ya da yanlış her denemede yakılır** ve kimliği sunucuda (`rate_hits`, `cap_used`) işaretlenir; böylece eski çerezi yeniden oynatarak tekrar deneme yapılamaz. Yanlış cevapta yeni sınama kurulur. Şablonda satır içi betik yoktur (CSP uyumlu); "Yenile" bağlantısı betik yokken de çalışır.
  - **Kademeli IP kilidi**: IP 10 dk'da 8 hatalı denemeye ulaşınca kilitlenir; tekrarlayan kilitlenmede süre 15 dk, 1 saat, 24 saat olarak uzar (24 saat içindeki kilit sayısına göre). Hesap başına (6 / 15 dk) ve tüm site (60 / 10 dk) sınırları aynen geçerlidir.
  - **Honeypot + imzalı form zaman damgası**: gizli `hp_site` alanı dolu, form 1,5 sn'den hızlı gönderilmiş, 30 dk'dan eski ya da imzası bozuk (imza oturum CSRF belirtecine bağlı) ise istek bot sayılır. Bu durumlar yalnızca IP sayacına yazılır (hesabı ve site sayacını etkilemez).
  - **Tek tip hata**: kullanıcı yok, parola yanlış, honeypot, hızlı/bayat form ve yanlış CAPTCHA aynı genel mesajı verir (hesap varlığı sızdırılmaz; parola doğrulaması CAPTCHA geçilmeden yapılmaz).
  - **Kalıcı kayıt**: başarısız girişler `login_failures` tablosuna (zaman, IP, tarayıcı, neden; kullanıcı adı ham değil `mask_ident` ile maskeli; hesap eşleşirse `user_id`) yazılır, 90 günden eskiler temizlenir. Kullanıcı kendi hesabına yönelik son 24 saatteki denemeleri Profil > Güvenlik'te görür.
  - İki adımlı doğrulama adımı: IP başına 5 / 10 dk ve hesap başına 5 / 15 dk deneme; 2FA ayar işlemleri (etkinleştir/kapat/yenile) kullanıcı başına 5 / 15 dk. Kayıt denemeleri IP başına 20 / 10 dk (başarılı kayıt 10 / saat).
- Kayıt, şifre değiştirme, satın alma, çekim, ödeme bildirimi, kupon denemesi, mesaj/destek/şikayet, API (anahtar başına dakikada 120, geçersiz anahtar denemesi IP başına 20 / 10 dk), yükleme (kullanıcı başına saatte 40), Shopier OSB.
- Genel yazma sınırı: IP başına dakikada 240 yazma isteği (`RATE_GLOBAL_WRITES`). Proxy arkasındaysan `TRUST_PROXY=1` ekle, yoksa tüm istekler proxy IP'sinden görünür.

## Yönetici paneli girişi (`adminsec.py`, `admin_auth.py`, `totp.py`)
- **İki adımlı doğrulama (TOTP, RFC 6238)**: `ADMIN_2FA=required` (varsayılan) | `optional` | `off`. Kullanıcı adı + parola doğruysa oturumda 5 dakika yaşayan, panele erişimi olmayan bir "ön oturum" açılır; tam yönetici oturumu (`session['admin']`) yalnızca tüm adımlar geçince verilir. 2FA kuruluysa `/admin/dogrula` (6 haneli kod ya da yedek kod), kurulu değil ve `required` ise zorunlu kurulum sayfası `/admin/guvenlik/kurulum` (QR + gizli anahtar + doğrulama kodu; 10 yedek kod bir kez gösterilir). `optional` modda 2FA kurulu değilse parolayla girilir ve panelde uyarı görünür.
- **Saklama**: gizli anahtar ve yedek kod hash'leri `settings` tablosunda `SECRET_KEY` türevli anahtarla şifreli tutulur (`security.encrypt_secret`); yedek kodlar yalnızca SHA-256 hash'idir. Son kullanılan zaman adımı saklanır: aynı (ya da eski) kod tekrar kabul edilmez, adım koşullu `UPDATE` ile atomik ilerletilir (eşzamanlı iki istek aynı kodu kullanamaz). Yedek kod tek kullanımlıktır, kullanılınca listeden düşer ve kalan sayı gösterilir. `SECRET_KEY` değişir de kayıt çözülemezse sistem parola-only'e düşmez (2. adım istenir, yedek kodlar da geçmez); çözüm `manage.py admin-2fa-reset`.
- **Deneme sınırı**: kod denemeleri IP başına 5 / 10 dk ve tüm site için 30 / saat; aşılırsa ön oturum silinir. Güvenlik sayfasındaki işlemler (yedek kod yenileme, 2FA kapatma: parola + güncel kod ister; `required` modda kapatılamaz) aynı sınırı kullanır.
- **Kademeli kilit**: 5 hatalı girişte IP 15 dk kilitlenir; tekrarlayan kilitlenmede 1 saat, sonra 24 saat (24 saat içindeki kilit sayısına göre; başarılı tam girişte sıfırlanır). Kilitliyken doğru parola da reddedilir. 2 hatadan sonra **CAPTCHA** zorunlu olur (ortak `captcha.py`, kapsam `admin`; modül yoksa yalnızca CAPTCHA atlanır, diğer korumalar çalışır).
- **Tek tip hata ve sabit süre**: kullanıcı adı doğru/yanlış, honeypot, imzasız form aynı genel mesajı verir; kullanıcı adı ve parola her zaman ikisi de değerlendirilir; başarısız girişte en az `ADMIN_FAIL_DELAY` (varsayılan 0,6 sn) + kısa rastgele gecikme uygulanır.
- **Honeypot + imzalı zaman damgası**: giriş formunda gizli `website` alanı ve imzalı `ft` alanı; honeypot dolu, imza yok/bozuk ya da form 1,5 sn'den hızlı gönderildiyse giriş denenmez (hızlı/bayat form hata sayacına yazılmaz). Form 2 saat geçerlidir.
- **IP izin listesi** (`ADMIN_ALLOWED_IPS=203.0.113.5,10.0.0.0/8,2001:db8::/32`): tanımlıysa izin dışındaki IP'ler giriş sayfası dahil `/admin/*` için 404 alır (yönetim yolu yokmuş gibi davranır; genel site etkilenmez). Geçersiz giriş açılışta hata verir; tanımlı ama hiç geçerli girişi olmayan liste kimseye izin vermez. Gerçek IP için proxy arkasında `TRUST_PROXY=1` gerekir; yoksa `X-Forwarded-For` yok sayılır.
- **Özel yönetim yolu** (`ADMIN_URL_PREFIX=/yonetim-x7`): blueprint öneki açılışta ortamdan alınır; `/admin` 404 verir. Menü, yönlendirme ve CSP/hız sınırı kodu endpoint adlarına (`admin.*`) dayanır, sabit yol yoktur. Geçersiz ya da site yollarıyla çakışan önek açılışta hata verir. `robots.txt` özel yolu yazmaz; yanıtlara `X-Robots-Tag: noindex, nofollow` eklenir.
- **Oturum sertleştirme**: girişte `session.clear()` ile yeni oturum; 30 dk boşta kalma (kayan; yalnızca yönetim paneli istekleri sayılır, `fetch` yoklamaları sayılmaz) + mutlak 8 saat; oturum `User-Agent` özetine bağlıdır (değişirse düşer), `ADMIN_BIND_IP=1` ise istemcinin /24 (IPv6 /48) ağına da; `ADMIN_USERNAME`/yönetici parolası değişirse (parmak izi `core.ADMIN_PW_FP`) mevcut oturumlar düşer; 2FA'sız açılmış bir oturum, mod `required`a çevrilince ya da 2FA kurulunca düşer. Çıkış tüm oturumu temizler. Tüm `/admin/*` yanıtları `Cache-Control: no-store` ve `X-Robots-Tag: noindex, nofollow` gönderir.
- **Giriş olayları**: her başarılı/başarısız giriş, kod denemesi ve kilit `admin_login_events` tablosuna yazılır (kullanıcı adı ham değil, `mask_ident`; en çok 2000 hata + 500 başarılı kayıt tutulur). Yönetim > Güvenlik sayfasında son 30 olay (zaman, maskeli IP, tarayıcı, sonuç) ve oturum ayarları görünür.
- **Yeni cihaz uyarısı**: daha önce başarılı giriş varsa ve IP ya da tarayıcı ilk kez görülüyorsa `admin_log`a yazılır ve tüm yönetim sayfalarında "Bendim, uyarıyı kapat" diyene kadar kalıcı uyarı gösterilir.
- **Acil kurtarma**: telefon ve yedek kodlar kaybolursa sunucuda `python manage.py admin-2fa-reset` 2FA kaydını siler (sonraki girişte `required` ise yeniden kurulum istenir). Geçici acil durum bayrağı: `.env` içine `ADMIN_2FA=off` ekleyip uygulamayı yeniden başlat; işin bitince satırı kaldır (bayrak açıkken Güvenlik sayfası uyarır).
- **Önerilen canlı ayarlar**: `ADMIN_2FA=required`, `ADMIN_ALLOWED_IPS` (sabit IP/VPN varsa), `ADMIN_URL_PREFIX` ile tahmin edilmesi zor bir yol, `ADMIN_BIND_IP=1` (IP'in sık değişmiyorsa), `ADMIN_PASSWORD_HASH` (`manage.py hash-admin`), HTTPS + `TRUST_PROXY=1`.
- Bilinen sınır: tüm site için 30 hata / saat sınırı kasıtlı olarak dağıtık saldırıyı yavaşlatır, ancak saldırgan bu sayacı doldurursa gerçek yönetici de bir süre giremez; `ADMIN_ALLOWED_IPS` bu durumu ortadan kaldırır (izin dışı IP'ler sayaca hiç ulaşamaz).

## Girdi doğrulama
- Tüm form alanlarından NUL/kontrol karakterleri, çift yönlü metin (bidi) ve sıfır genişlikli karakterler atılır; alan başına 20.000 karakter, istek başına 400 alan sınırı (`security.SafeRequest`).
- Para tutarı: yalnızca rakam/nokta/virgül, bilimsel gösterim ve işaret yok, üst sınır 10 milyon TL. Aşırı büyük sayılar 400 döner (500 değil).
- Çekim hesabı yönteme göre doğrulanır: TR IBAN (mod 97), Papara numarası, TRC20 adresi. Kullanıcı adı, e-posta, TC kimlik, telefon, renk, bağlantı alanları biçim kontrolünden geçer. `next` yönlendirmesi yalnızca site içi yola izin verir.
- Şifre: 8-128 karakter; yaygın/kolay şifreler, kullanıcı adını (3+ karakter) ya da e-postanın yerel kısmını (4+ karakter) içeren şifreler reddedilir.

## CORS ve çapraz site
- CORS varsayılan **kapalı**: hiçbir sayfa/uç dış siteye açılmaz; `Access-Control-Allow-Credentials` hiç gönderilmez. Tarayıcıdan `/api/v1/*` kullanacak dış site varsa `.env`: `CORS_ORIGINS=https://site.example`.
- Yazma isteklerinde CSRF belirteci + `Origin`/`Sec-Fetch-Site` denetimi (çapraz site ve `Origin: null` reddedilir). `/api/` (çerezsiz) bu denetimden muaftır; kendi imza/anahtarlarıyla doğrulanır. Proxy Host başlığını değiştiriyorsa `.env`: `TRUSTED_ORIGINS=https://siten.example`.
- Başlıklar: CSP (script yalnızca kendi dosyalarımızdan, `object-src 'none'`, `frame-ancestors 'none'`), `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, COOP/CORP, HTTPS'te HSTS.

## Parolalar ve sırlar
- Kullanıcı şifreleri scrypt ile hash'lenir (tuzlu); eski/zayıf parametreli hash'ler girişte yükseltilir. API anahtarları SHA-256 hash'i olarak saklanır (düz anahtar yalnızca oluşturulurken bir kez gösterilir).
- Yönetici şifresi: `python manage.py hash-admin` komutu `.env`'ye `ADMIN_PASSWORD_HASH` yazar ve düz metni siler. Düz metin `ADMIN_PASSWORD` hâlâ çalışır ama açılışta bellekte hash'lenir ve Yönetim > Sistem sayfası uyarır.
- Ödeme linkleri yalnızca `https://` kabul eder (kullanıcı adı/şifre içeren ve boşluklu adresler reddedilir); link yönetici tarafından girilir, kullanıcı girdisi değildir. Bakiye yalnızca yönetici onayıyla eklenir.
- `.env` (600), `data/` (700), `uploads/` (700) izinleri açılışta kısıtlanır.

## Çerez
- `HttpOnly`, `SameSite=Lax`. HTTPS altında otomatik `Secure` ve `__Host-` önekli (alt alan adına sızmaz, `Domain` yok). `COOKIE_SECURE=auto` (varsayılan) / `1` / `0`. Proxy arkasında `TRUST_PROXY=1` gerekir.
- Girişte oturum yenilenir (fixation yok), çıkışta tüm oturum temizlenir, "beni hatırla" yoksa tarayıcı kapanınca düşer.

## Log
- Tüm log satırlarında (erişim günlüğü dahil) `token`, `key`, `secret`, `signature`, `password`, `hash`, `Authorization: Bearer ...`, `itm_...` API anahtarları, çerez değerleri ve 40+ karakterlik rastgele diziler `[gizli]` ile maskelenir (`security.install_log_redaction`).
- Başarısız yönetici girişinde yazılan kullanıcı adı ham olarak günlüğe yazılmaz (yanlışlıkla şifre yazılmış olabilir): yalnızca ilk iki harf ve uzunluk.
- Kart bilgisi hiç alınmaz; ödeme dış sayfada yapılır.

## XSS
- Tüm şablonlar Jinja otomatik kaçışıyla çalışır; `|safe` kullanılmaz. CSP satır içi betiğe izin vermez; sayfalarda satır içi `<script>` ve `on...=` özniteliği yoktur. JSON yanıtlarında `< > &` karakterleri `<` biçiminde kaçırılır ve `nosniff` gönderilir. İstemci tarafında öneri/son gezilenler listesi yalnızca site içi yolları bağlantı yapar.
- Otomatik test: her alana XSS yükleri gönderilip kullanıcı ve yönetici sayfalarında ham etiket aranır.

## Yükleme
- Görseller gerçekten Pillow ile çözülür (yalnızca JPEG/PNG/WEBP), piksel sayısı 40 MP ile sınırlıdır (dekompresyon bombası), yeniden kodlanıp EXIF temizlenir, rastgele adla kaydedilir; SVG/HTML/PHP reddedilir. Dosya adı kullanıcıdan alınmaz.
- Uç noktaya özel gövde sınırı (kimlik 28 MB, ilan/kategori/banner 8 MB, metin formları 1 MB), yükleme beklenmeyen uçlarda multipart reddedilir, istek başına en fazla 30 dosya, kullanıcı başına saatte 40 yükleme.
- Kimlik görselleri `uploads/kyc` altında, yalnızca yönetici oturumuyla sunulur.

## Bilinen sınırlar / öneriler
- Üye 2FA'sı: telefon ve yedek kodlar birlikte kaybedilirse panelde sıfırlama ekranı yoktur; hesap sahibi kimliği doğrulandıktan sonra veritabanında `UPDATE users SET totp_secret='', totp_backup='', totp_last_step=0 WHERE id=...` ile kapatılır. `SECRET_KEY` değişirse 2FA anahtarları çözülemez (yalnızca yedek kodlar çalışır); anahtarı rotasyonda bu etkiyi hesaba kat.
- CAPTCHA resmi sistemdeki DejaVu/Poppins yazı tiplerini kullanır; bulunamazsa Pillow'un yerleşik yazı tipine düşer (okunabilirlik biraz azalabilir). Görme engelli kullanıcılar için resim alt metni ve "Yenile" bağlantısı vardır; sesli CAPTCHA yoktur, gerekirse destek talebi yolu açıktır.
- E-pin kodları teslim edilebilmeleri için veritabanında düz metin tutulur; sunucu diskini şifrele ve `data/` yedeklerini korumalı sakla. Kimlik görselleri de diskte şifresiz durur.
- Yönetici girişinde iki adımlı doğrulama varsayılan olarak zorunludur (yukarıdaki bölüm); yine de yönetim adresini `ADMIN_ALLOWED_IPS` ile IP kısıtı veya VPN arkasına almanı öneririm.
- Uygulamayı HTTPS sonlandıran bir proxy (nginx/Caddy) arkasında çalıştır: `TRUST_PROXY=1`, `COOKIE_SECURE=auto`. Geliştirme sunucusu (`python app.py`) canlı için değildir; `gunicorn` gibi bir WSGI sunucusu kullan.
- Kartla ödeme kaldırıldı. Eski veritabanlarında kalan kart ödemesi kayıtları (maskeli kart bilgisi) silinmez ama açık olanlar kapatılır; istersen `card_payments` tablosunu elle silebilirsin.
