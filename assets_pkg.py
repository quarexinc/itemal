"""Mağaza paketi rozetleri (mavi tik, altın/elmas mağaza) - statik SVG dosyaları."""

FILES = {}

FILES['mavitik.svg'] = r"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" role="img" aria-label="Mavi tik: doğrulanmış mağaza">
  <defs>
    <linearGradient id="vb" x1="4" y1="2" x2="20" y2="22" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#4cbcff"/>
      <stop offset="0.55" stop-color="#1d9bf0"/>
      <stop offset="1" stop-color="#1580d6"/>
    </linearGradient>
  </defs>
  <path d="M12.00,0.85 L12.24,0.87 L12.48,0.92 L12.72,1.01 L12.95,1.13 L13.17,1.27 L13.39,1.44 L13.60,1.63 L13.79,1.83 L13.98,2.05 L14.16,2.26 L14.33,2.47 L14.50,2.68 L14.66,2.87 L14.82,3.05 L14.98,3.21 L15.15,3.35 L15.32,3.46 L15.50,3.55 L15.69,3.61 L15.89,3.65 L16.11,3.67 L16.33,3.68 L16.57,3.66 L16.82,3.64 L17.09,3.62 L17.36,3.59 L17.64,3.56 L17.92,3.54 L18.20,3.54 L18.48,3.55 L18.76,3.58 L19.02,3.64 L19.26,3.72 L19.49,3.82 L19.70,3.96 L19.88,4.12 L20.04,4.30 L20.18,4.51 L20.28,4.74 L20.36,4.98 L20.42,5.24 L20.45,5.52 L20.46,5.80 L20.46,6.08 L20.44,6.36 L20.41,6.64 L20.38,6.91 L20.36,7.17 L20.34,7.43 L20.32,7.67 L20.33,7.89 L20.35,8.11 L20.39,8.31 L20.45,8.50 L20.54,8.68 L20.65,8.85 L20.79,9.02 L20.95,9.18 L21.13,9.34 L21.32,9.50 L21.53,9.67 L21.74,9.84 L21.95,10.02 L22.17,10.21 L22.37,10.40 L22.56,10.61 L22.73,10.83 L22.87,11.05 L22.99,11.28 L23.08,11.52 L23.13,11.76 L23.15,12.00 L23.13,12.24 L23.08,12.48 L22.99,12.72 L22.87,12.95 L22.73,13.17 L22.56,13.39 L22.37,13.60 L22.17,13.79 L21.95,13.98 L21.74,14.16 L21.53,14.33 L21.32,14.50 L21.13,14.66 L20.95,14.82 L20.79,14.98 L20.65,15.15 L20.54,15.32 L20.45,15.50 L20.39,15.69 L20.35,15.89 L20.33,16.11 L20.32,16.33 L20.34,16.57 L20.36,16.82 L20.38,17.09 L20.41,17.36 L20.44,17.64 L20.46,17.92 L20.46,18.20 L20.45,18.48 L20.42,18.76 L20.36,19.02 L20.28,19.26 L20.18,19.49 L20.04,19.70 L19.88,19.88 L19.70,20.04 L19.49,20.18 L19.26,20.28 L19.02,20.36 L18.76,20.42 L18.48,20.45 L18.20,20.46 L17.92,20.46 L17.64,20.44 L17.36,20.41 L17.09,20.38 L16.83,20.36 L16.57,20.34 L16.33,20.32 L16.11,20.33 L15.89,20.35 L15.69,20.39 L15.50,20.45 L15.32,20.54 L15.15,20.65 L14.98,20.79 L14.82,20.95 L14.66,21.13 L14.50,21.32 L14.33,21.53 L14.16,21.74 L13.98,21.95 L13.79,22.17 L13.60,22.37 L13.39,22.56 L13.17,22.73 L12.95,22.87 L12.72,22.99 L12.48,23.08 L12.24,23.13 L12.00,23.15 L11.76,23.13 L11.52,23.08 L11.28,22.99 L11.05,22.87 L10.83,22.73 L10.61,22.56 L10.40,22.37 L10.21,22.17 L10.02,21.95 L9.84,21.74 L9.67,21.53 L9.50,21.32 L9.34,21.13 L9.18,20.95 L9.02,20.79 L8.85,20.65 L8.68,20.54 L8.50,20.45 L8.31,20.39 L8.11,20.35 L7.89,20.33 L7.67,20.32 L7.43,20.34 L7.17,20.36 L6.91,20.38 L6.64,20.41 L6.36,20.44 L6.08,20.46 L5.80,20.46 L5.52,20.45 L5.24,20.42 L4.98,20.36 L4.74,20.28 L4.51,20.18 L4.30,20.04 L4.12,19.88 L3.96,19.70 L3.82,19.49 L3.72,19.26 L3.64,19.02 L3.58,18.76 L3.55,18.48 L3.54,18.20 L3.54,17.92 L3.56,17.64 L3.59,17.36 L3.62,17.09 L3.64,16.83 L3.66,16.57 L3.68,16.33 L3.67,16.11 L3.65,15.89 L3.61,15.69 L3.55,15.50 L3.46,15.32 L3.35,15.15 L3.21,14.98 L3.05,14.82 L2.87,14.66 L2.68,14.50 L2.47,14.33 L2.26,14.16 L2.05,13.98 L1.83,13.79 L1.63,13.60 L1.44,13.39 L1.27,13.17 L1.13,12.95 L1.01,12.72 L0.92,12.48 L0.87,12.24 L0.85,12.00 L0.87,11.76 L0.92,11.52 L1.01,11.28 L1.13,11.05 L1.27,10.83 L1.44,10.61 L1.63,10.40 L1.83,10.21 L2.05,10.02 L2.26,9.84 L2.47,9.67 L2.68,9.50 L2.87,9.34 L3.05,9.18 L3.21,9.02 L3.35,8.85 L3.46,8.68 L3.55,8.50 L3.61,8.31 L3.65,8.11 L3.67,7.89 L3.68,7.67 L3.66,7.43 L3.64,7.18 L3.62,6.91 L3.59,6.64 L3.56,6.36 L3.54,6.08 L3.54,5.80 L3.55,5.52 L3.58,5.24 L3.64,4.98 L3.72,4.74 L3.82,4.51 L3.96,4.30 L4.12,4.12 L4.30,3.96 L4.51,3.82 L4.74,3.72 L4.98,3.64 L5.24,3.58 L5.52,3.55 L5.80,3.54 L6.08,3.54 L6.36,3.56 L6.64,3.59 L6.91,3.62 L7.18,3.64 L7.43,3.66 L7.67,3.68 L7.89,3.67 L8.11,3.65 L8.31,3.61 L8.50,3.55 L8.68,3.46 L8.85,3.35 L9.02,3.21 L9.18,3.05 L9.34,2.87 L9.50,2.68 L9.67,2.47 L9.84,2.26 L10.02,2.05 L10.21,1.83 L10.40,1.63 L10.61,1.44 L10.83,1.27 L11.05,1.13 L11.28,1.01 L11.52,0.92 L11.76,0.87Z" fill="url(#vb)"/>
  <path d="M7.2 12.4l3.45 3.5 6.2-7" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

FILES['tier-gold.svg'] = r"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" role="img" aria-label="Altın mağaza">
  <defs>
    <linearGradient id="gg" x1="4" y1="1" x2="20" y2="23" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#ffe27a"/>
      <stop offset="0.5" stop-color="#f7b500"/>
      <stop offset="1" stop-color="#d98a00"/>
    </linearGradient>
  </defs>
  <path d="M12 1.6l8.1 2.9v6.3c0 5.2-3.4 9.1-8.1 11.6C7.3 19.9 3.9 16 3.9 10.8V4.5z" fill="url(#gg)" stroke="#b86e00" stroke-width="0.6" stroke-linejoin="round"/>
  <path d="M12.00,6.60 L13.26,9.96 L16.85,10.12 L14.04,12.36 L15.00,15.83 L12.00,13.85 L9.00,15.83 L9.96,12.36 L7.15,10.12 L10.74,9.96Z" fill="#fff8dc" stroke="#fff8dc" stroke-width="0.5" stroke-linejoin="round"/>
</svg>
"""

FILES['tier-diamond.svg'] = r"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" role="img" aria-label="Elmas mağaza">
  <defs>
    <linearGradient id="dtop" x1="12" y1="3" x2="12" y2="9" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#e9fbff"/><stop offset="1" stop-color="#8fe3ff"/></linearGradient>
    <linearGradient id="dl" x1="3" y1="9" x2="12" y2="21" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#5cc8ff"/><stop offset="1" stop-color="#3d6bff"/></linearGradient>
    <linearGradient id="dr" x1="21" y1="9" x2="12" y2="21" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#8b7bff"/><stop offset="1" stop-color="#3a46d8"/></linearGradient>
    <linearGradient id="dm" x1="12" y1="9" x2="12" y2="21" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#7fd6ff"/><stop offset="1" stop-color="#5a62f0"/></linearGradient>
    <linearGradient id="dc" x1="7" y1="3" x2="17" y2="9" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#b8ecff"/></linearGradient>
  </defs>
  <path d="M7.2 3.4h9.6l4.6 5.4L12 21 2.6 8.8z" fill="#2f55c8"/>
  <path d="M7.2 3.4 9.6 8.8H2.6z" fill="url(#dl)" opacity=".55"/>
  <path d="M7.2 3.4h4.8L9.6 8.8z" fill="url(#dc)"/>
  <path d="M12 3.4h4.8l-2.4 5.4z" fill="url(#dtop)"/>
  <path d="M16.8 3.4l2.2 0 2.4 5.4h-7z" fill="url(#dr)" opacity=".7"/>
  <path d="M9.6 8.8h4.8L12 3.4z" fill="url(#dtop)" opacity=".8"/>
  <path d="M2.6 8.8h7L12 21z" fill="url(#dl)"/>
  <path d="M21.4 8.8h-7L12 21z" fill="url(#dr)"/>
  <path d="M9.6 8.8h4.8L12 21z" fill="url(#dm)"/>
  <path d="M7.2 3.4h9.6l4.6 5.4L12 21 2.6 8.8z" fill="none" stroke="#1e3a9e" stroke-opacity=".55" stroke-width=".55" stroke-linejoin="round"/>
  <path d="M2.8 8.8h18.4M9.6 8.8 7.2 3.5M14.4 8.8l2.4-5.3M9.6 8.8 12 3.5l2.4 5.3M9.6 8.8 12 20.6M14.4 8.8 12 20.6" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width=".5" stroke-linejoin="round" stroke-linecap="round"/>
  <path d="M5.2 6.2 7 5.2" stroke="#fff" stroke-width="1" stroke-linecap="round" opacity=".9"/>
  <path d="M19.6 1.2v3M18.1 2.7h3" stroke="#fff" stroke-width=".7" stroke-linecap="round"/>
  <path d="M3.6 13.4v2M2.6 14.4h2" stroke="#bdeaff" stroke-width=".6" stroke-linecap="round"/>
</svg>
"""

