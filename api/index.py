"""Vercel giris noktasi: tum istekler bu WSGI uygulamasina yonlendirilir (vercel.json -> rewrites)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app  # noqa: E402,F401  (Vercel 'app' adli WSGI nesnesini arar)
