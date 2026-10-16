"""Otomatik üretilen statik dosyalar: style.css, app.js, boot.js, logo.svg, favicon.svg.

İkili dosyalar (kategori bannerları) metin tabanlı FILES'a girmez: static_src/ altında durur, templates_gen.generate public/static/ altına kopyalar."""
from assets_brand import FILES as BRAND_FILES
from assets_css import CSS
from assets_js import BOOT, JS
from assets_pkg import FILES as PKG_FILES
import assets_plus

FILES = {"style.css": CSS + assets_plus.CSS, "app.js": JS + assets_plus.JS, "boot.js": BOOT, **BRAND_FILES, **PKG_FILES}
