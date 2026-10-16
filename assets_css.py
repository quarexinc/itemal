"""style.css - koyu, nötr zeminli tasarım sistemi. Vurgu rengi tek (menekşe); kategoriler kendi renklerini taşır."""

CSS = r"""
:root{
  color-scheme:dark;
  --bg:#0a0a0f; --bg-2:#0e0e14; --card:#13131a; --card-2:#1a1a23; --card-3:#22222d;
  --line:rgba(255,255,255,.08); --line-2:rgba(255,255,255,.15);
  --text:#ececf2; --muted:#9b9bb0; --dim:#6e6e83;
  --p:#7c5cff; --p-h:#8f74ff; --p-d:#5b3fd6; --p-2:#a99aff; --p-3:#cfc7ff; --p-soft:rgba(124,92,255,.15);
  --accent:#f472b6; --cy:#22d3ee;
  --ok:#34d399; --warn:#fbbf24; --bad:#f87171; --info:#60a5fa;
  --r:14px; --r-sm:10px; --pad:20px;
  --shadow:0 12px 32px -14px rgba(0,0,0,.7);
  --grad:linear-gradient(135deg,#7c5cff,#b45cf0);
  --ease:cubic-bezier(.2,.7,.2,1);
  --font:"Inter","Segoe UI Variable Text","Segoe UI",system-ui,-apple-system,Roboto,"Helvetica Neue",Arial,sans-serif;
}
body.app{--r:10px;--r-sm:8px;--pad:18px;font-size:14px}
*{box-sizing:border-box;scrollbar-width:thin;scrollbar-color:#2c2c3a transparent}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;min-height:100vh;display:flex;flex-direction:column;color:var(--text);font:15px/1.6 var(--font);
  background:radial-gradient(900px 480px at 82% -12%,rgba(124,92,255,.11),transparent 60%),var(--bg);
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
::selection{background:rgba(124,92,255,.45)}
a{color:var(--p-2);text-decoration:none;transition:color .15s}
a:hover{color:#fff}
h1,h2,h3,h4{line-height:1.2;margin:0 0 .5em;letter-spacing:-.02em;font-weight:700}
h1{font-size:2.2rem} h2{font-size:1.45rem} h3{font-size:1.05rem}
p{margin:0 0 1em}
img{max-width:100%}
hr{border:0;border-top:1px solid var(--line);margin:1.4em 0}
code,.mono{font-family:ui-monospace,SFMono-Regular,"JetBrains Mono",Menlo,Consolas,monospace}
button{font-family:inherit}
:focus-visible{outline:2px solid var(--p-2);outline-offset:2px;border-radius:6px}
.container{width:100%;max-width:1240px;margin:0 auto;padding:0 22px}
.muted{color:var(--muted)} .dim{color:var(--dim)} .small{font-size:.85rem} .center{text-align:center} .right{text-align:right}
.grad{color:var(--p-2)}
.row{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
.spread{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.mt{margin-top:18px} .mb{margin-bottom:18px} .mt0{margin-top:0}
.nowrap{white-space:nowrap}
.pre{white-space:pre-wrap;word-break:break-word}
.tnum{font-variant-numeric:tabular-nums}
main{flex:1;animation:pagein .45s var(--ease)}
@keyframes pagein{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}

/* ---------- ikonlar ---------- */
.i{width:1.2em;height:1.2em;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;vertical-align:-.22em;flex:none}
.i.fill{fill:currentColor}
.i-lg{width:1.6em;height:1.6em} .i-xl{width:2.2em;height:2.2em}

/* ---------- üst bar ---------- */
.announce{background:linear-gradient(90deg,#1c1640,#231a55,#1c1640);color:var(--p-3);text-align:center;padding:8px 16px;font-weight:500;font-size:.88rem;border-bottom:1px solid var(--line)}
.topbar{position:sticky;top:0;z-index:60;background:rgba(10,10,15,.78);backdrop-filter:blur(16px) saturate(140%);-webkit-backdrop-filter:blur(16px) saturate(140%);border-bottom:1px solid var(--line);transition:box-shadow .25s}
.topbar.scrolled{box-shadow:0 10px 30px -18px #000}
.topbar-in{display:flex;align-items:center;gap:16px;height:64px}
.brand{display:flex;align-items:center;gap:10px;font-weight:800;font-size:1.22rem;color:#fff;letter-spacing:-.03em}
.brand:hover{color:#fff}
.brand-mark{display:block;flex:none;width:32px;height:32px;border-radius:9px;box-shadow:0 4px 14px rgba(124,92,255,.35)}
.nav{display:flex;align-items:center;gap:2px}
.nav a{padding:8px 12px;border-radius:9px;color:var(--muted);font-weight:500;font-size:.93rem}
.nav a:hover,.nav a.on{color:#fff;background:rgba(255,255,255,.06)}
.search{position:relative;flex:1;max-width:460px}
.search form{display:flex;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:12px;transition:border-color .2s,box-shadow .2s}
.search form:focus-within{border-color:var(--p);box-shadow:0 0 0 3px rgba(124,92,255,.2)}
.search .i{margin-left:12px;color:var(--dim)}
.search input{flex:1;background:transparent;border:0;color:var(--text);padding:10px 12px;outline:none;min-width:0;font:inherit;font-size:.93rem}
.search kbd{margin-right:10px;color:var(--dim);border:1px solid var(--line-2);border-radius:5px;padding:0 6px;font-size:.72rem;font-family:inherit}
.suggest{position:absolute;left:0;right:0;top:calc(100% + 8px);background:var(--card-2);border:1px solid var(--line-2);border-radius:14px;padding:6px;box-shadow:var(--shadow);display:none;z-index:70}
.suggest.on{display:block}
.suggest a{display:flex;align-items:center;gap:12px;padding:8px 10px;border-radius:9px;color:var(--text)}
.suggest a:hover,.suggest a.hl{background:rgba(255,255,255,.06)}
.suggest .thumb{width:44px;height:30px}
.suggest small{color:var(--muted);display:block}
.suggest .sg-h{padding:6px 10px 4px;color:var(--dim);font-size:.72rem;text-transform:uppercase;letter-spacing:.08em}
.top-right{margin-left:auto;display:flex;align-items:center;gap:6px}
.chip{display:inline-flex;align-items:center;gap:7px;padding:7px 13px;border-radius:999px;background:var(--card);border:1px solid var(--line);color:#fff;font-weight:600;font-size:.88rem;white-space:nowrap}
.chip:hover{border-color:var(--line-2);color:#fff}
.ibtn{position:relative;width:38px;height:38px;display:grid;place-items:center;border-radius:10px;color:var(--muted);background:transparent;border:0;cursor:pointer;transition:.15s}
.ibtn:hover{background:rgba(255,255,255,.07);color:#fff}
.ibtn .dot{position:absolute;top:3px;right:2px;min-width:17px;height:17px;padding:0 4px;border-radius:999px;background:var(--accent);color:#fff;font-size:10.5px;font-weight:700;display:grid;place-items:center;line-height:1}
.dd{position:relative}
.dd-menu{position:absolute;right:0;top:calc(100% + 10px);min-width:230px;background:var(--card-2);border:1px solid var(--line-2);border-radius:14px;padding:6px;box-shadow:var(--shadow);opacity:0;visibility:hidden;transform:translateY(-6px) scale(.98);transform-origin:top right;transition:.18s var(--ease);z-index:80}
.dd.open>.dd-menu{opacity:1;visibility:visible;transform:none}
.dd-menu a,.dd-menu button.dd-item{display:flex;align-items:center;gap:10px;width:100%;padding:9px 11px;border-radius:9px;color:var(--text);background:none;border:0;font:inherit;font-size:.92rem;cursor:pointer;text-align:left}
.dd-menu a:hover,.dd-menu button.dd-item:hover{background:rgba(255,255,255,.07);color:#fff}
.dd-menu .i{color:var(--muted)}
.dd-head{padding:10px 11px 8px;border-bottom:1px solid var(--line);margin-bottom:4px}
.dd-head b{display:block} .dd-head small{color:var(--muted)}
.dd-menu hr{margin:5px 0}
.dd-notif{width:340px;padding:0}
.dd-notif .n-head{display:flex;justify-content:space-between;align-items:center;padding:12px 14px;border-bottom:1px solid var(--line);font-weight:600}
.n-list{max-height:380px;overflow:auto}
.n-item{display:block;padding:11px 14px;border-bottom:1px solid var(--line);color:var(--text)}
.n-item:last-child{border:0}
.n-item:hover{background:rgba(255,255,255,.04);color:#fff}
.n-item.unread{background:rgba(124,92,255,.07)}
.n-item.unread b:before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--p);margin-right:8px}
.n-item small{display:block;color:var(--muted);margin-top:2px}
.n-empty{padding:28px 14px;text-align:center;color:var(--muted)}
.nav-toggle{display:none}
.catbar{border-bottom:1px solid var(--line);background:rgba(255,255,255,.015)}
.catbar-in{display:flex;gap:4px;overflow-x:auto;scrollbar-width:none;padding:8px 22px;max-width:1240px;margin:0 auto}
.catbar-in::-webkit-scrollbar{display:none}
.catbar a{flex:none;display:flex;align-items:center;gap:8px;padding:6px 12px;border-radius:999px;font-size:.84rem;color:var(--muted);border:1px solid transparent;transition:.2s}
.catbar a:before{content:"";width:7px;height:7px;border-radius:50%;background:var(--c,var(--p))}
.catbar a:hover{color:#fff;border-color:var(--line-2);background:rgba(255,255,255,.04)}
.catbar a.all:before{display:none}

/* ---------- butonlar ---------- */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;border:1px solid transparent;cursor:pointer;color:#fff;font:inherit;font-weight:600;font-size:.94rem;
  padding:10px 18px;border-radius:11px;background:var(--p);transition:background .15s,transform .15s,box-shadow .2s,border-color .15s;line-height:1.3;position:relative}
.btn:hover{background:var(--p-h);color:#fff;box-shadow:0 8px 22px -10px rgba(124,92,255,.9)}
.btn:active{transform:none;box-shadow:none}
.btn-ghost{background:rgba(255,255,255,.06);border-color:var(--line);color:var(--text)}
.btn-ghost:hover{background:rgba(255,255,255,.1);box-shadow:none;color:#fff}
.btn-line{background:transparent;border-color:var(--line-2);color:var(--text)}
.btn-line:hover{background:rgba(255,255,255,.06);box-shadow:none;color:#fff}
.btn-ok{background:#16a34a} .btn-ok:hover{background:#1bb955;box-shadow:0 8px 22px -10px rgba(22,163,74,.9)}
.btn-danger{background:#dc3f45} .btn-danger:hover{background:#ee5157;box-shadow:0 8px 22px -10px rgba(220,63,69,.9)}
.btn-sm{padding:6px 12px;font-size:.84rem;border-radius:8px}
.btn-lg{padding:13px 24px;font-size:1rem;border-radius:13px}
.btn-block{width:100%}
.btn[disabled]{opacity:.5;cursor:not-allowed;transform:none;box-shadow:none}
body.app .btn{border-radius:8px;padding:8px 14px;font-size:.86rem}
body.app .btn-sm{padding:5px 10px;font-size:.8rem;border-radius:7px}
.link-btn{background:none;border:0;color:var(--p-2);cursor:pointer;font:inherit;padding:0}
.link-btn:hover{color:#fff}
.link-danger{color:var(--bad)}
.btn.shine{overflow:hidden}
.btn.shine:after{content:"";position:absolute;inset:0;border-radius:inherit;background:linear-gradient(110deg,transparent 30%,rgba(255,255,255,.35) 50%,transparent 70%);transform:translateX(-120%);animation:sheen 4.5s infinite}
@keyframes sheen{0%,60%{transform:translateX(-120%)}100%{transform:translateX(120%)}}

/* ---------- kartlar / ızgara ---------- */
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:var(--pad)}
.card.flat{background:var(--card)}
.card.tight{padding:0;overflow:hidden}
.card-h{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px 10px;margin-bottom:14px}
.card-h h2,.card-h h3{margin:0}
.grid{display:grid;gap:16px}
.g2{grid-template-columns:repeat(2,minmax(0,1fr))} .g3{grid-template-columns:repeat(3,minmax(0,1fr))} .g4{grid-template-columns:repeat(4,minmax(0,1fr))}
.g-main{grid-template-columns:minmax(0,2fr) minmax(0,1fr)}
.g-main>.card:first-child{display:flex;flex-direction:column}
.g-main>.card:first-child .bars{flex:1;min-height:200px;height:auto}
.grid>*,.two-col>*{min-width:0}
.stat{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:16px 18px}
.stat .k{color:var(--muted);font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;font-weight:500}
.stat .v{font-size:1.55rem;font-weight:700;margin-top:4px;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.stat .s{color:var(--muted);font-size:.82rem;margin-top:2px}
.stat.hot .v{color:var(--warn)} .stat.good .v{color:var(--ok)}
.trunc{max-width:190px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.kpis.c3{grid-template-columns:repeat(3,1fr)}
@media (max-width:760px){.kpis.c3{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:var(--r);overflow:hidden}
.kpi{background:var(--card);padding:16px 18px;min-width:0}
.kpi .k{display:flex;align-items:center;gap:7px;color:var(--muted);font-size:.78rem;font-weight:500}
.kpi .k .i{color:var(--dim)}
.kpi .v{font-size:1.5rem;font-weight:650;letter-spacing:-.02em;margin-top:6px;font-variant-numeric:tabular-nums;white-space:nowrap}
.kpi .v.ok{color:var(--ok)} .kpi .v.warn{color:var(--warn)}
.kpi .s{color:var(--dim);font-size:.78rem;margin-top:3px}
.kpi .spark{display:block;width:100%;height:28px;margin-top:8px}
.spark polyline{fill:none;stroke:var(--p-2);stroke-width:1.6;vector-effect:non-scaling-stroke;stroke-linejoin:round;stroke-linecap:round}
.spark path{fill:url(#sparkfill);stroke:none}
.delta{display:inline-flex;align-items:center;gap:3px;font-size:.74rem;font-weight:600;padding:1px 6px;border-radius:6px}
.delta.up{color:var(--ok);background:rgba(52,211,153,.12)} .delta.down{color:var(--bad);background:rgba(248,113,113,.12)} .delta.flat{color:var(--muted);background:rgba(255,255,255,.06)}

/* ---------- formlar ---------- */
label{display:block;font-weight:500;font-size:.88rem;margin:0 0 6px;color:#d8d8e4}
.field{margin-bottom:16px}
input[type=text],input[type=email],input[type=password],input[type=number],input[type=date],input[type=datetime-local],input[type=search],input[type=tel],input[type=url],input[type=color],select,textarea{
  width:100%;background:var(--bg-2);border:1px solid var(--line-2);color:var(--text);border-radius:10px;padding:10px 12px;font:inherit;outline:none;transition:border-color .15s,box-shadow .15s}
input[type=color]{padding:3px;height:40px;cursor:pointer}
body.app input[type=text],body.app input[type=email],body.app input[type=password],body.app input[type=number],body.app input[type=date],body.app input[type=datetime-local],body.app input[type=search],body.app input[type=tel],body.app input[type=url],body.app select,body.app textarea{border-radius:8px;padding:8px 11px}
input::placeholder,textarea::placeholder{color:var(--dim)}
input:focus,select:focus,textarea:focus{border-color:var(--p);box-shadow:0 0 0 3px rgba(124,92,255,.22)}
input[type=file]{width:100%;background:var(--bg-2);border:1px dashed var(--line-2);border-radius:10px;padding:10px;color:var(--muted)}
input[type=file]::file-selector-button{background:var(--card-3);border:0;color:var(--text);padding:6px 12px;border-radius:7px;margin-right:12px;cursor:pointer;font:inherit}
textarea{min-height:110px;resize:vertical}
select{appearance:none;-webkit-appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%239b9bb0' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m5 9 7 7 7-7'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 12px center;padding-right:34px}
select option{background:var(--card-2)}
.hint{color:var(--muted);font-size:.8rem;margin-top:5px}
.check{display:flex;gap:10px;align-items:flex-start;font-weight:400}
.check input{margin-top:4px;accent-color:var(--p)}
.inline-form{display:inline}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.filters{display:flex;gap:10px;flex-wrap:wrap;align-items:end;margin-bottom:16px}
.filters .field{margin:0;min-width:150px}
.filters .grow{flex:1;min-width:200px}
.quick{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.quick button{background:rgba(255,255,255,.05);border:1px solid var(--line-2);color:var(--text);border-radius:8px;padding:5px 11px;cursor:pointer;font:inherit;font-size:.84rem;transition:.15s}
.quick button:hover{background:var(--p);border-color:var(--p);color:#fff}
.stepper{display:inline-flex;align-items:center;border:1px solid var(--line-2);border-radius:11px;background:var(--bg-2);overflow:hidden}
.stepper button{width:40px;height:42px;background:none;border:0;color:var(--text);cursor:pointer;font-size:1.1rem}
.stepper button:hover{background:rgba(255,255,255,.07)}
.stepper input{width:54px;text-align:center;border:0;background:transparent;border-radius:0;padding:10px 0;box-shadow:none!important;-moz-appearance:textfield}
.stepper input::-webkit-outer-spin-button,.stepper input::-webkit-inner-spin-button{-webkit-appearance:none}
.input-btn{display:flex;gap:8px}
.input-btn input{flex:1}
.switch{position:relative;display:inline-block;width:38px;height:22px}
.switch input{opacity:0;width:0;height:0}
.switch span{position:absolute;inset:0;background:var(--card-3);border-radius:999px;cursor:pointer;transition:.2s}
.switch span:before{content:"";position:absolute;left:3px;top:3px;width:16px;height:16px;border-radius:50%;background:#fff;transition:.2s}
.switch input:checked+span{background:var(--p)} .switch input:checked+span:before{transform:translateX(16px)}

/* ---------- uyarılar / rozetler ---------- */
.flashes{position:fixed;top:76px;right:18px;z-index:120;display:grid;gap:10px;width:min(390px,calc(100vw - 36px));margin:0!important;pointer-events:none}
.flash{pointer-events:auto;display:flex;justify-content:space-between;align-items:flex-start;gap:12px;padding:12px 14px;border-radius:12px;border:1px solid;background:var(--card-2);box-shadow:var(--shadow);animation:toast .4s var(--ease);font-size:.92rem}
.flash .x{background:none;border:0;color:inherit;font-size:1.3rem;cursor:pointer;line-height:1;opacity:.7}
.flash .x:hover{opacity:1}
@keyframes toast{from{opacity:0;transform:translateX(24px)}to{opacity:1;transform:none}}
.flash-ok{border-color:rgba(52,211,153,.45);color:#a7f3d0;background:#0f2a22}
.flash-bad{border-color:rgba(248,113,113,.5);color:#fecaca;background:#2d1417}
.flash-warn{border-color:rgba(251,191,36,.5);color:#fde68a;background:#2b2210}
.flash-info{border-color:rgba(96,165,250,.45);color:#bfdbfe;background:#0f1d33}
.notice{padding:12px 15px;border-radius:11px;border:1px solid var(--line-2);background:var(--card);margin-bottom:16px;color:#d6d6e2}
.notice.warn{border-color:rgba(251,191,36,.4);background:rgba(251,191,36,.07);color:#fde68a}
.notice.bad{border-color:rgba(248,113,113,.45);background:rgba(248,113,113,.07);color:#fecaca}
.notice.ok{border-color:rgba(52,211,153,.4);background:rgba(52,211,153,.07);color:#a7f3d0}
.badge{display:inline-flex;align-items:center;padding:1px 9px;border-radius:999px;font-size:.74rem;font-weight:600;border:1px solid;white-space:nowrap;line-height:1.7}
.b-ok{color:var(--ok);border-color:rgba(52,211,153,.35);background:rgba(52,211,153,.1)}
.b-warn{color:var(--warn);border-color:rgba(251,191,36,.35);background:rgba(251,191,36,.1)}
.b-bad{color:var(--bad);border-color:rgba(248,113,113,.4);background:rgba(248,113,113,.1)}
.b-muted{color:var(--muted);border-color:var(--line-2);background:rgba(255,255,255,.04)}
.b-info{color:var(--info);border-color:rgba(96,165,250,.4);background:rgba(96,165,250,.1)}
.cnt{display:inline-block;min-width:19px;padding:0 6px;border-radius:999px;background:var(--p);color:#fff;font-size:.7rem;text-align:center;font-weight:700;line-height:19px}
.pos{color:var(--ok)} .neg{color:var(--bad)}

/* ---------- tablo ---------- */
.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:var(--r);background:var(--card)}
table{width:100%;border-collapse:collapse;font-size:.9rem}
th{text-align:left;color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.07em;padding:11px 14px;white-space:nowrap;font-weight:600;border-bottom:1px solid var(--line);background:rgba(255,255,255,.02)}
td{padding:11px 14px;border-top:1px solid var(--line);vertical-align:middle}
tr:first-child td{border-top:0}
tr:hover td{background:rgba(255,255,255,.025)}
td.actions{white-space:nowrap;text-align:right}
td form{margin:0}
body.app th{padding:9px 12px} body.app td{padding:9px 12px}
.empty{text-align:center;padding:46px 20px;color:var(--muted)}
.empty strong{display:block;color:#d6d6e2;margin-bottom:2px}
.pager{display:flex;gap:6px;justify-content:center;margin:24px 0;flex-wrap:wrap}
.pager a,.pager span{min-width:36px;text-align:center;padding:7px 11px;border-radius:9px;background:var(--card);border:1px solid var(--line);color:var(--muted);font-size:.9rem}
.pager a:hover{border-color:var(--line-2);color:#fff}
.pager .on{background:var(--p);border-color:var(--p);color:#fff;font-weight:600}
.tabs{display:flex;gap:2px;flex-wrap:wrap;margin-bottom:18px;border-bottom:1px solid var(--line)}
.tabs a{padding:9px 14px;color:var(--muted);font-weight:500;border-bottom:2px solid transparent;margin-bottom:-1px;font-size:.92rem}
.tabs a:hover{color:#fff}
.tabs a.on{color:#fff;border-color:var(--p)}
.seg{display:inline-flex;background:var(--card);border:1px solid var(--line);border-radius:11px;padding:3px;gap:2px;flex-wrap:wrap}
.seg button,.seg a{background:none;border:0;color:var(--muted);padding:6px 13px;border-radius:8px;cursor:pointer;font:inherit;font-size:.86rem;font-weight:500}
.seg button:hover,.seg a:hover{color:#fff}
.seg .on{background:var(--card-3);color:#fff}

/* ---------- panel kabuğu (satıcı ve yönetici) ---------- */
.admin-shell,.shell{display:grid;grid-template-columns:248px minmax(0,1fr);min-height:100vh}
.a-side,.s-side{background:var(--bg-2);border-right:1px solid var(--line);padding:16px 12px 24px;position:sticky;top:0;height:100vh;overflow:auto}
.a-side .brand,.s-side .brand{padding:4px 8px 6px;font-size:1.15rem}
.s-side .who{display:flex;align-items:center;gap:10px;padding:10px 8px 14px;margin-bottom:6px;border-bottom:1px solid var(--line)}
.s-side .who b{display:block;font-size:.9rem;line-height:1.2} .s-side .who small{color:var(--muted);font-size:.78rem}
.a-side .sep,.s-side .sep{font-size:.68rem;text-transform:uppercase;letter-spacing:.1em;color:var(--dim);padding:16px 10px 5px;font-weight:600}
.a-side a,.s-side nav a{display:flex;align-items:center;gap:10px;padding:7px 10px;border-radius:8px;color:var(--muted);font-weight:500;font-size:.86rem;margin-bottom:1px;position:relative}
.a-side a .i,.s-side nav a .i{opacity:.75}
.a-side a .cnt,.s-side nav a .cnt{margin-left:auto}
.a-side a:hover,.s-side nav a:hover{background:rgba(255,255,255,.05);color:#fff}
.a-side a.on,.s-side nav a.on{background:var(--p-soft);color:#fff}
.a-side a.on .i,.s-side nav a.on .i{color:var(--p-2);opacity:1}
.a-side a.on:before,.s-side nav a.on:before{content:"";position:absolute;left:-12px;top:7px;bottom:7px;width:3px;border-radius:0 3px 3px 0;background:var(--p)}
.a-main,.s-main{padding:0 28px 60px;min-width:0}
.a-top,.s-top{display:flex;justify-content:space-between;align-items:center;padding:14px 0;margin-bottom:18px;border-bottom:1px solid var(--line);gap:12px;flex-wrap:wrap;position:sticky;top:0;z-index:30;background:rgba(10,10,15,.86);backdrop-filter:blur(10px);margin-left:-28px;margin-right:-28px;padding-left:28px;padding-right:28px}
.a-top h1,.s-top h1{font-size:1.15rem;margin:0;font-weight:650;letter-spacing:-.01em}
.a-login{max-width:400px;margin:12vh auto;padding:0 20px}
.tag-admin{display:inline-block;background:rgba(244,114,182,.12);color:#f9a8d4;border:1px solid rgba(244,114,182,.3);border-radius:6px;padding:0 8px;font-size:.68rem;font-weight:700;letter-spacing:.08em}
.tag-seller{display:inline-block;background:var(--p-soft);color:var(--p-3);border:1px solid rgba(124,92,255,.35);border-radius:6px;padding:0 8px;font-size:.68rem;font-weight:700;letter-spacing:.08em}
.gsearch{position:relative;flex:1;max-width:420px}
.gsearch form{display:flex;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:9px}
.gsearch form:focus-within{border-color:var(--p)}
.gsearch .i{margin-left:10px;color:var(--dim)}
.gsearch input{background:transparent;border:0;box-shadow:none!important;padding:7px 10px}
.mini-form{display:flex;gap:6px;align-items:center;justify-content:flex-end;flex-wrap:wrap}
.mini-form input[type=text]{width:150px;padding:6px 10px;font-size:.85rem}
.detail-list p{margin:0 0 .4em}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.log-ip{color:var(--muted);font-size:.8rem}
.page-h{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:20px;flex-wrap:wrap}
.page-h h1{font-size:1.5rem;margin:0}
.crumb{color:var(--dim);font-size:.8rem;margin-bottom:4px}
.section-t{font-size:.72rem;text-transform:uppercase;letter-spacing:.09em;color:var(--dim);font-weight:600;margin:0 0 10px}

/* ---------- hesap yerleşimi ---------- */
.layout{display:grid;grid-template-columns:240px minmax(0,1fr);gap:26px;padding-top:26px;padding-bottom:56px;align-items:start}
.side{position:sticky;top:84px;background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:12px}
.side-user{display:flex;gap:12px;align-items:center;padding:8px 8px 14px;border-bottom:1px solid var(--line);margin-bottom:8px}
.side-user b{display:block} .side-user small{color:var(--muted)}
.side nav{display:grid;gap:1px}
.side nav a{display:flex;align-items:center;gap:10px;padding:9px 11px;border-radius:9px;color:var(--muted);font-weight:500;font-size:.92rem}
.side nav a .i{opacity:.75}
.side nav a:hover{background:rgba(255,255,255,.05);color:#fff}
.side nav a.on{background:var(--p-soft);color:#fff}
.side nav a.on .i{color:var(--p-2);opacity:1}
.side .sep{font-size:.68rem;text-transform:uppercase;letter-spacing:.1em;color:var(--dim);padding:12px 11px 4px}
.balance-hero{position:relative;overflow:hidden;background:linear-gradient(120deg,#20164f,#141032 60%,#0f1226);border:1px solid rgba(124,92,255,.35);border-radius:18px;padding:24px;display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
.balance-hero:before{content:"";position:absolute;right:-60px;top:-80px;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,rgba(124,92,255,.35),transparent 70%)}
.balance-hero>*{position:relative}
.balance-hero .amt{font-size:2.3rem;font-weight:800;letter-spacing:-.03em;font-variant-numeric:tabular-nums}
.balance-hero small{color:var(--p-3)}
.balance-hero .btn{background:rgba(255,255,255,.12);border-color:rgba(255,255,255,.2)}
.balance-hero .btn:hover{background:rgba(255,255,255,.2);box-shadow:none}

/* ---------- grafik ---------- */
.bars{display:flex;gap:5px;align-items:stretch;height:170px;overflow:hidden}
.bar{flex:1;display:flex;flex-direction:column;min-width:0}
.bar-track{flex:1;display:flex;align-items:flex-end;border-radius:5px;background:rgba(255,255,255,.03)}
.bar-fill{display:block;width:100%;border-radius:5px 5px 0 0;background:var(--p);min-height:0;transform-origin:bottom;transition:filter .2s;animation:grow .8s var(--ease) backwards}
.bar:hover .bar-fill{filter:brightness(1.3)}
@keyframes grow{from{transform:scaleY(0)}}
.bar em{font-style:normal;font-size:.62rem;color:var(--dim);text-align:center;margin-top:5px;white-space:nowrap;overflow:hidden;max-width:100%}
.meter{height:6px;border-radius:999px;background:rgba(255,255,255,.07);overflow:hidden}
.meter i{display:block;height:100%;background:var(--p);border-radius:999px}
.hbar{display:grid;grid-template-columns:130px 1fr auto;gap:10px;align-items:center;margin:9px 0;font-size:.88rem}
.hbar .meter{height:8px}
.hbar b{font-variant-numeric:tabular-nums}

/* ---------- e-pin kodu ---------- */
.codebox{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 14px;border-radius:11px;background:var(--bg-2);border:1px dashed rgba(124,92,255,.6);margin-bottom:8px}
.codebox code{font-size:1.02rem;word-break:break-all;color:#fff;letter-spacing:.04em}

/* ---------- kimlik önizleme ---------- */
.kyc-imgs{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.kyc-imgs a{display:block;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:var(--bg)}
.kyc-imgs img{display:block;width:100%;height:150px;object-fit:cover}
.kyc-imgs small{display:block;text-align:center;padding:4px;color:var(--muted)}

/* ---------- alt bilgi ---------- */
.footer{margin-top:auto;border-top:1px solid var(--line);background:var(--bg-2);padding:44px 0 26px;color:var(--muted)}
.footer-in{display:grid;grid-template-columns:1.6fr 1fr 1fr 1fr;gap:30px}
.footer h4{color:#fff;font-size:.9rem;margin-bottom:12px}
.footer ul{list-style:none;padding:0;margin:0;display:grid;gap:8px;font-size:.92rem}
.footer a{color:var(--muted)} .footer a:hover{color:#fff}
.copy{border-top:1px solid var(--line);margin-top:30px;padding-top:18px;font-size:.84rem;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.socials{display:flex;gap:8px;margin-top:14px}
.socials a{display:grid;place-items:center;width:36px;height:36px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--muted)}
.socials a:hover{color:#fff;border-color:var(--line-2)}
.totop{position:fixed;right:20px;bottom:20px;z-index:70;width:44px;height:44px;border-radius:12px;background:var(--card-2);border:1px solid var(--line-2);color:#fff;display:grid;place-items:center;cursor:pointer;opacity:0;transform:translateY(12px);pointer-events:none;transition:.25s var(--ease)}
.totop.on{opacity:1;transform:none;pointer-events:auto}

/* ---------- vitrin: slider ---------- */
.hero-wrap{padding:22px 0 8px}
.slider{position:relative;border-radius:22px;overflow:hidden;height:clamp(290px,33vw,410px);isolation:isolate;background:var(--card);border:1px solid var(--line)}
.slide{position:absolute;inset:0;display:flex;align-items:center;padding:0 clamp(24px,5vw,68px);opacity:0;visibility:hidden;transition:opacity .8s var(--ease),visibility .8s;background:linear-gradient(115deg,var(--c1,#7c5cff),var(--c2,#1b1140))}
.slide.on{opacity:1;visibility:visible;z-index:1}
.slide:before{content:"";position:absolute;inset:0;background:radial-gradient(620px 320px at 82% 18%,rgba(255,255,255,.2),transparent 60%),radial-gradient(520px 420px at 8% 115%,rgba(0,0,0,.45),transparent 60%)}
.slide:after{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.06) 1px,transparent 1px);background-size:46px 46px;-webkit-mask-image:linear-gradient(100deg,transparent 30%,#000);mask-image:linear-gradient(100deg,transparent 30%,#000)}
.slide .shape{position:absolute;border-radius:50%;border:1px solid rgba(255,255,255,.22);z-index:0}
.slide .shape.a{width:340px;height:340px;right:8%;top:-90px;background:radial-gradient(circle at 30% 30%,rgba(255,255,255,.22),rgba(255,255,255,.02) 70%);animation:drift 9s ease-in-out infinite}
.slide .shape.b{width:190px;height:190px;right:26%;bottom:-70px;background:rgba(255,255,255,.07);animation:drift 11s ease-in-out infinite reverse}
.slide .shape.c{width:90px;height:90px;right:5%;bottom:22%;background:rgba(255,255,255,.12);animation:drift 7s ease-in-out infinite}
@keyframes drift{50%{transform:translate3d(-14px,16px,0) scale(1.05)}}
.slide-img{position:absolute;right:0;top:0;bottom:0;width:58%;object-fit:cover;-webkit-mask-image:linear-gradient(90deg,transparent,#000 45%);mask-image:linear-gradient(90deg,transparent,#000 45%);z-index:0}
.slide-body{position:relative;z-index:2;max-width:540px;color:#fff;transform:translateY(18px);opacity:0;transition:transform .9s .2s var(--ease),opacity .9s .2s var(--ease)}
.slide.on .slide-body{transform:none;opacity:1}
.kicker{display:inline-flex;align-items:center;gap:7px;padding:4px 11px;border-radius:999px;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);font-size:.78rem;font-weight:600;margin-bottom:14px;backdrop-filter:blur(6px)}
.slide h2{font-size:clamp(1.7rem,3.8vw,3rem);font-weight:800;letter-spacing:-.035em;line-height:1.04;margin-bottom:.4em;text-wrap:balance}
.slide p{color:rgba(255,255,255,.85);font-size:clamp(.95rem,1.4vw,1.1rem);max-width:440px;margin-bottom:22px}
.slide .btn{background:#fff;color:#111;font-weight:700}
.slide .btn:hover{background:#f1f1f6;color:#000}
.dots{position:absolute;left:clamp(24px,5vw,68px);bottom:22px;display:flex;gap:8px;z-index:5}
.dots button{width:30px;height:4px;border-radius:4px;background:rgba(255,255,255,.28);border:0;position:relative;overflow:hidden;cursor:pointer;padding:0}
.dots button.on:after{content:"";position:absolute;inset:0;background:#fff;transform-origin:left;animation:prog var(--dur,6s) linear forwards}
.slider:hover .dots button.on:after{animation-play-state:paused}
@keyframes prog{from{transform:scaleX(0)}to{transform:scaleX(1)}}
.sl-arrow{position:absolute;top:50%;transform:translateY(-50%);z-index:5;width:42px;height:42px;border-radius:50%;background:rgba(0,0,0,.35);border:1px solid rgba(255,255,255,.2);color:#fff;display:grid;place-items:center;cursor:pointer;opacity:0;transition:.25s;backdrop-filter:blur(6px)}
.slider:hover .sl-arrow{opacity:1}
.sl-arrow:hover{background:rgba(0,0,0,.6)}
.sl-prev{left:14px} .sl-next{right:14px}

.trust{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-top:14px}
.trust>div{display:flex;gap:12px;align-items:center;padding:14px 16px;border:1px solid var(--line);border-radius:14px;background:var(--card);transition:.25s var(--ease)}
.trust>div:hover{border-color:var(--line-2)}
.trust .ti{display:grid;place-items:center;width:38px;height:38px;border-radius:11px;background:var(--p-soft);color:var(--p-2);flex:none}
.trust b{display:block;font-size:.92rem;line-height:1.25} .trust small{color:var(--muted);font-size:.8rem;line-height:1.3;display:block}

.section{padding-top:30px;padding-bottom:30px}
.section-h{display:flex;justify-content:space-between;align-items:end;margin-bottom:18px;gap:12px}
.section-h h2{margin:0;display:flex;align-items:center;gap:10px;font-size:1.4rem}
.section-h h2 .i{color:var(--p-2)}
.section-h p{margin:2px 0 0;color:var(--muted);font-size:.92rem}
.more{display:inline-flex;align-items:center;gap:6px;color:var(--muted);font-size:.9rem;font-weight:500}
.more:hover{color:#fff}
.more .i{transition:transform .2s} .more:hover .i{transform:translateX(3px)}

/* günün oyunları: poster kartları */
.posters{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:14px}
.poster{position:relative;display:block;aspect-ratio:3/4;border-radius:18px;overflow:hidden;background:linear-gradient(165deg,var(--c,#7c5cff),#0b0b11 86%);color:#fff;isolation:isolate;transition:transform .35s var(--ease),box-shadow .35s,border-color .3s;border:1px solid rgba(255,255,255,.08);will-change:transform}
.poster:hover{color:#fff;box-shadow:0 26px 50px -22px var(--c,#7c5cff);border-color:rgba(255,255,255,.22)}
.poster .mono-big{position:absolute;right:-6px;top:4px;font-size:7.4rem;font-weight:900;letter-spacing:-.07em;opacity:.16;line-height:1;transition:transform .5s var(--ease);font-family:var(--font)}
.poster:hover .mono-big{transform:scale(1.12) translate(-6px,6px)}
.poster>img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .7s var(--ease);z-index:-1}
.poster:hover>img{transform:scale(1.07)}
.poster:before{content:"";position:absolute;inset:0;z-index:1;background:linear-gradient(115deg,transparent 30%,rgba(255,255,255,.22) 48%,transparent 62%);transform:translateX(-130%);transition:transform .8s var(--ease);pointer-events:none}
.poster:hover:before{transform:translateX(130%)}
.poster-tag{position:absolute;left:12px;top:12px;z-index:2;display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:999px;background:rgba(0,0,0,.42);border:1px solid rgba(255,255,255,.2);font-size:.7rem;font-weight:600;backdrop-filter:blur(6px)}
.poster-body{position:absolute;left:0;right:0;bottom:0;padding:44px 15px 15px;background:linear-gradient(0deg,rgba(0,0,0,.82),transparent);z-index:2}
.poster-body b{display:block;font-size:1.02rem;line-height:1.2;letter-spacing:-.01em}
.poster-body small{display:block;color:rgba(255,255,255,.72);margin-top:3px;font-size:.8rem}

/* kategori kutuları */
.cat-filter{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px}
.cat-filter button{background:var(--card);border:1px solid var(--line);color:var(--muted);border-radius:999px;padding:6px 14px;cursor:pointer;font:inherit;font-size:.86rem;font-weight:500;transition:.2s}
.cat-filter button:hover{color:#fff;border-color:var(--line-2)}
.cat-filter button.on{background:var(--p);border-color:var(--p);color:#fff}
.cat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px}
.cat-tile{position:relative;display:flex;align-items:center;gap:12px;padding:11px 14px 11px 11px;border-radius:14px;background:var(--card);border:1px solid var(--line);color:var(--text);transition:transform .25s var(--ease),border-color .25s;overflow:hidden}
.cat-tile:before{content:"";position:absolute;inset:0;background:radial-gradient(160px 70px at 0 0,color-mix(in srgb,var(--c) 26%,transparent),transparent);opacity:0;transition:opacity .3s}
.cat-tile:hover{border-color:color-mix(in srgb,var(--c) 60%,transparent);color:#fff}
.cat-tile:hover:before{opacity:1}
.cat-tile.hide{display:none}
.cat-ic{position:relative;width:42px;height:42px;border-radius:12px;display:grid;place-items:center;font-weight:800;font-size:.86rem;letter-spacing:-.02em;color:#fff;background:linear-gradient(140deg,var(--c),color-mix(in srgb,var(--c) 40%,#000));flex:none;box-shadow:inset 0 1px 0 rgba(255,255,255,.28)}
.cat-tile b{display:block;font-size:.92rem;line-height:1.2;position:relative}
.cat-tile small{display:block;color:var(--muted);font-size:.78rem;position:relative}

/* reklam şeridi */
.strip-ad{position:relative;display:flex;align-items:center;justify-content:space-between;gap:20px;padding:20px 28px;border-radius:18px;background:linear-gradient(100deg,var(--c1,#0f766e),var(--c2,#052e2b));color:#fff;overflow:hidden;border:1px solid rgba(255,255,255,.1);transition:transform .3s var(--ease)}
.strip-ad:hover{color:#fff}
.strip-ad:after{content:"";position:absolute;inset:0;background:linear-gradient(110deg,transparent 35%,rgba(255,255,255,.14) 50%,transparent 65%);transform:translateX(-120%);animation:sheen 6s infinite;pointer-events:none}
.strip-ad>*{position:relative;z-index:1}
.strip-ad b{display:block;font-size:1.15rem;letter-spacing:-.02em} .strip-ad span.sub{color:rgba(255,255,255,.8);font-size:.92rem}
.strip-ad .go{display:inline-flex;align-items:center;gap:8px;padding:9px 16px;border-radius:10px;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.25);font-weight:600;font-size:.88rem;white-space:nowrap}
.strip-ad img.bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.35;z-index:0}

/* canlı bant */
.ticker{overflow:hidden;border-block:1px solid var(--line);background:rgba(255,255,255,.018);-webkit-mask-image:linear-gradient(90deg,transparent,#000 7%,#000 93%,transparent);mask-image:linear-gradient(90deg,transparent,#000 7%,#000 93%,transparent)}
.ticker-track{display:flex;gap:44px;width:max-content;padding:11px 0;animation:marquee 60s linear infinite}
.ticker:hover .ticker-track{animation-play-state:paused}
.ticker-item{display:inline-flex;align-items:center;gap:9px;font-size:.86rem;color:var(--muted);white-space:nowrap}
.ticker-item b{color:#fff;font-weight:600}
.ticker-item .live{width:7px;height:7px;border-radius:50%;background:var(--ok);box-shadow:0 0 0 0 rgba(52,211,153,.6);animation:pulse 2s infinite}
@keyframes pulse{70%{box-shadow:0 0 0 8px rgba(52,211,153,0)}100%{box-shadow:0 0 0 0 rgba(52,211,153,0)}}
@keyframes marquee{to{transform:translateX(-50%)}}

/* fırsatlar */
.deal-head{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.countdown{display:inline-flex;gap:6px;font-variant-numeric:tabular-nums}
.countdown span{display:grid;place-items:center;min-width:40px;padding:5px 8px;border-radius:9px;background:var(--card-2);border:1px solid var(--line-2);font-weight:700;font-size:.95rem;line-height:1.1}
.countdown small{display:block;font-size:.58rem;font-weight:500;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}

/* ilan kartı */
.lgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(236px,1fr));gap:16px}
.lcard{position:relative;display:flex;flex-direction:column;border-radius:16px;background:var(--card);border:1px solid var(--line);overflow:hidden;color:var(--text);transition:transform .3s var(--ease),border-color .3s,box-shadow .3s}
.lcard:hover{border-color:var(--line-2);box-shadow:0 22px 44px -24px rgba(0,0,0,.9)}
.lcard .cover{border-radius:0}
.lcard .cover img{transition:transform .7s var(--ease)}
.lcard:hover .cover img{transform:scale(1.06)}
.lcard-body{padding:13px 14px 14px;display:flex;flex-direction:column;gap:9px;flex:1}
.lcard h3{margin:0;font-size:.97rem;line-height:1.3;font-weight:600;letter-spacing:-.01em;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.6em}
.lcard h3 a{color:#fff}
.lcard h3 a:after{content:"";position:absolute;inset:0;z-index:1}
.lcard-meta{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:.8rem;min-width:0}
.lcard-meta .nm{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
.lcard-meta .vf{color:var(--info);flex:none}
.lcard-foot{display:flex;justify-content:space-between;align-items:flex-end;margin-top:auto;gap:8px}
.price{font-size:1.18rem;font-weight:750;color:#fff;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.price-old{display:block;color:var(--dim);text-decoration:line-through;font-size:.78rem;font-weight:500;letter-spacing:0}
.stock{font-size:.72rem;font-weight:600;padding:2px 8px;border-radius:6px;color:var(--ok);background:rgba(52,211,153,.1);border:1px solid rgba(52,211,153,.28)}
.stock.low{color:var(--warn);background:rgba(251,191,36,.1);border-color:rgba(251,191,36,.3)}
.stock.out{color:var(--bad);background:rgba(248,113,113,.1);border-color:rgba(248,113,113,.3)}
.cover .tag-l{position:absolute;left:10px;top:10px;z-index:2;display:inline-flex;align-items:center;gap:6px;padding:3px 9px;border-radius:999px;background:rgba(10,10,15,.82);font-size:.72rem;font-weight:600;color:#fff;border:1px solid rgba(255,255,255,.12)}
.cover .tag-l:before{content:"";width:6px;height:6px;border-radius:50%;background:var(--c,var(--p))}
.cover .tag-b{position:absolute;left:10px;bottom:10px;z-index:2}
.disc{display:inline-block;background:#e5484d;color:#fff;border-radius:6px;padding:1px 7px;font-weight:700;font-size:.74rem}
.fav{position:absolute;right:9px;top:9px;z-index:3;width:34px;height:34px;border-radius:50%;background:rgba(10,10,15,.8);border:1px solid rgba(255,255,255,.14);color:#fff;display:grid;place-items:center;cursor:pointer;transition:.2s var(--ease)}
.fav:hover{transform:scale(1.1);background:rgba(10,10,15,.85)}
.fav.on{color:#fb7185;border-color:rgba(251,113,133,.5)} .fav.on .i{fill:currentColor}
.fav.pop{animation:pop .4s var(--ease)}
@keyframes pop{40%{transform:scale(1.35)}}

/* ---------- ilan detay ---------- */
.crumbs{color:var(--muted);font-size:.86rem;margin:22px 0 14px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.crumbs .sepx{color:var(--dim)}
.detail{display:grid;grid-template-columns:minmax(0,1fr) 390px;gap:24px;align-items:start}
.buybox{position:sticky;top:88px}
.buybox .price{font-size:2rem}
.kv{display:grid;grid-template-columns:auto 1fr;gap:7px 16px;margin:0}
.kv dt{color:var(--muted)} .kv dd{margin:0;text-align:right;font-weight:600}
.total-row{display:flex;justify-content:space-between;align-items:center;margin:14px 0;padding:12px 14px;border-radius:11px;background:rgba(255,255,255,.04);border:1px solid var(--line)}
.total-row strong{font-size:1.3rem;font-variant-numeric:tabular-nums}
.coupon-row{margin:12px 0 4px}
.coupon-msg{font-size:.82rem;margin-top:6px;min-height:1.2em}
.coupon-msg.ok{color:var(--ok)} .coupon-msg.bad{color:var(--bad)}
.perks{list-style:none;padding:0;margin:14px 0 0;display:grid;gap:9px;font-size:.88rem;color:var(--muted)}
.perks li{display:flex;gap:10px;align-items:flex-start}
.perks .i{color:var(--ok);margin-top:2px}
.gallery{position:relative}
.gallery .cover{border-radius:18px;aspect-ratio:16/9}
.seller-box{display:flex;align-items:center;gap:12px}
.share-row{display:flex;gap:8px;margin-top:12px}

/* ---------- giriş / kayıt ---------- */
.auth{max-width:440px;margin:50px auto}
.auth h1{font-size:1.7rem}
.auth-wrap{display:grid;grid-template-columns:1fr 1fr;max-width:940px;margin:44px auto;border:1px solid var(--line);border-radius:24px;overflow:hidden;background:var(--card)}
.auth-art{position:relative;padding:44px 40px;background:linear-gradient(155deg,#5b3fd6,#1b1140 70%);color:#fff;overflow:hidden;display:flex;flex-direction:column;justify-content:space-between;min-height:460px}
.auth-art:before{content:"";position:absolute;width:340px;height:340px;right:-120px;top:-100px;border-radius:50%;background:radial-gradient(circle,rgba(255,255,255,.2),transparent 70%)}
.auth-art h2{font-size:1.9rem;letter-spacing:-.03em;line-height:1.1;position:relative}
.auth-art ul{list-style:none;padding:0;margin:0;display:grid;gap:14px;position:relative}
.auth-art li{display:flex;gap:12px;align-items:flex-start;color:rgba(255,255,255,.88)}
.auth-art li .i{margin-top:3px;color:#fff}
.auth-form{padding:44px 40px}
.auth-form h1{font-size:1.6rem}

/* ---------- puan yıldızları ---------- */
.stars{--v:0;display:inline-block;width:80px;height:16px;vertical-align:middle;
  background:linear-gradient(90deg,#fbbf24 calc(var(--v) * 20%),rgba(255,255,255,.16) 0);
  -webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24'%3E%3Cpath d='M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z'/%3E%3C/svg%3E") repeat-x 0 0/16px 16px;
  mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24'%3E%3Cpath d='M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z'/%3E%3C/svg%3E") repeat-x 0 0/16px 16px}
.stars.sm{width:65px;height:13px;-webkit-mask-size:13px 13px;mask-size:13px 13px}
.rate-line{display:inline-flex;align-items:center;gap:6px;color:var(--muted);font-size:.84rem}
.rate-line b{color:#fff}

/* ---------- rozetler ---------- */
.bd{display:inline-flex;align-items:center;gap:6px;padding:2px 9px;border-radius:7px;font-size:.72rem;font-weight:600;border:1px solid;white-space:nowrap}
.bd:before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor}
.bd-green{color:var(--ok);border-color:rgba(52,211,153,.4);background:rgba(52,211,153,.09)}
.bd-gold{color:#fbbf24;border-color:rgba(251,191,36,.45);background:rgba(251,191,36,.09)}
.bd-purple{color:#c4b5fd;border-color:rgba(167,139,250,.45);background:rgba(124,92,255,.12)}
.bd-blue{color:var(--info);border-color:rgba(96,165,250,.4);background:rgba(96,165,250,.09)}
.badges{display:flex;gap:6px;flex-wrap:wrap}

/* ---------- kapak / avatar ---------- */
.cover{position:relative;aspect-ratio:16/10;overflow:hidden;border-radius:12px;background:var(--card-2)}
.cover img{display:block;width:100%;height:100%;object-fit:cover}
.cover-ph{display:grid;place-items:center;width:100%;height:100%;background:linear-gradient(150deg,var(--c,#7c5cff),color-mix(in srgb,var(--c,#7c5cff) 30%,#0a0a0f));color:rgba(255,255,255,.92);font-size:2.6rem;font-weight:800;letter-spacing:-.04em;position:relative;overflow:hidden}
.cover-ph:after{content:"";position:absolute;width:120%;height:120%;left:-10%;top:-10%;background:radial-gradient(circle at 80% 0,rgba(255,255,255,.22),transparent 55%)}
.cover.wide{aspect-ratio:16/8;border-radius:16px}
.avatar{width:42px;height:42px;border-radius:12px;background:linear-gradient(140deg,#7c5cff,#4b34b8);display:grid;place-items:center;font-weight:700;flex:none;overflow:hidden;color:#fff}
.avatar img{width:100%;height:100%;object-fit:cover;display:block}
.avatar.sm{width:28px;height:28px;border-radius:8px;font-size:.78rem}
.avatar.lg{width:92px;height:92px;border-radius:24px;font-size:2.2rem}
.store-head{display:flex;gap:20px;align-items:center;flex-wrap:wrap}
.thumb{width:74px;height:46px;border-radius:8px;overflow:hidden;background:var(--card-2);flex:none}
.thumb img{width:100%;height:100%;object-fit:cover;display:block}
.preview-img{max-width:280px;border-radius:12px;margin-top:10px;display:block}

/* ---------- yorumlar ---------- */
.review{padding:14px 0;border-top:1px solid var(--line)}
.review:first-child{border-top:0;padding-top:0}
.review .who{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:4px}
.reply{margin-top:8px;padding:10px 12px;border-left:3px solid var(--p);background:rgba(124,92,255,.08);border-radius:0 8px 8px 0}
.reply b{color:var(--p-3)}

/* ---------- sohbet ---------- */
.chat{display:flex;flex-direction:column;height:calc(100vh - 250px);min-height:440px;padding:0;overflow:hidden}
.chat-head{display:flex;gap:12px;align-items:center;padding:14px 18px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.chat-log{flex:1;overflow:auto;padding:16px 18px;display:flex;flex-direction:column;gap:8px}
.msg{max-width:74%;padding:9px 13px;border-radius:14px 14px 14px 4px;background:var(--card-3);align-self:flex-start;white-space:pre-wrap;word-break:break-word}
.msg.me{align-self:flex-end;background:var(--p);border-radius:14px 14px 4px 14px}
.msg time{display:block;font-size:.68rem;opacity:.7;margin-top:3px}
.chat-form{display:flex;gap:10px;padding:12px;border-top:1px solid var(--line);align-items:flex-end}
.chat-form textarea{min-height:46px;height:46px;max-height:140px;resize:none}
.chat-note{padding:8px 18px;font-size:.8rem;color:var(--muted);background:rgba(255,255,255,.025);border-top:1px solid var(--line)}
.conv{display:flex;gap:14px;align-items:center;padding:14px 16px;border-top:1px solid var(--line);color:var(--text)}
.conv:first-child{border-top:0}
.conv:hover{background:rgba(255,255,255,.035);color:var(--text)}
.conv .grow{flex:1;min-width:0}
.conv .ellipsis{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dot-count{min-width:22px;height:22px;padding:0 6px;border-radius:999px;background:var(--accent);color:#fff;font-size:.75rem;font-weight:700;display:inline-grid;place-items:center}

/* ---------- destek talebi ---------- */
.tmsg{border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:12px;background:var(--card)}
.tmsg.staff{border-color:rgba(124,92,255,.5);background:rgba(124,92,255,.08)}
.tmsg.internal{border-style:dashed;border-color:rgba(251,191,36,.5);background:rgba(251,191,36,.05)}
.tmsg .meta{display:flex;justify-content:space-between;gap:10px;color:var(--muted);font-size:.82rem;margin-bottom:6px}

/* ---------- kimlik incelemesi / görsel büyütme ---------- */
.kyc-card{margin-bottom:18px}
.flag-list{margin:0 0 12px;padding:10px 14px 10px 30px;border-radius:10px;border:1px solid rgba(251,191,36,.4);background:rgba(251,191,36,.07);color:#fde68a}
.checks{display:grid;gap:6px;margin:10px 0}
.lightbox{position:fixed;inset:0;background:rgba(5,5,10,.94);display:none;place-items:center;z-index:200;padding:20px;cursor:zoom-out}
.lightbox.on{display:grid}
.lightbox img{max-width:96vw;max-height:92vh;border-radius:8px}
[data-zoom]{cursor:zoom-in}

/* ---------- dokümantasyon ---------- */
.doc pre{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:12px 14px;overflow:auto;font-size:.84rem;margin:8px 0 14px}
.doc h3{margin-top:1.4em}
.doc code.inline{background:rgba(255,255,255,.07);border-radius:6px;padding:1px 6px;font-size:.88em}
.keybox{padding:14px;border-radius:12px;border:1px dashed var(--ok);background:rgba(52,211,153,.07);word-break:break-all}
.calc{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:10px}
.calc div{padding:10px 12px;border-radius:10px;background:rgba(255,255,255,.04);border:1px solid var(--line)}
.calc small{display:block;color:var(--muted)}

/* ---------- basamaklar ---------- */
.steps{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;counter-reset:s}
.step{position:relative;padding:20px;border-radius:16px;background:var(--card);border:1px solid var(--line)}
.step:before{counter-increment:s;content:counter(s);display:grid;place-items:center;width:32px;height:32px;border-radius:9px;background:var(--p-soft);color:var(--p-2);font-weight:700;margin-bottom:12px}
.step h3{margin-bottom:.25em}
.step p{margin:0;color:var(--muted);font-size:.9rem}
.faq details{border:1px solid var(--line);border-radius:12px;background:var(--card);margin-bottom:10px;overflow:hidden}
.faq summary{padding:15px 18px;cursor:pointer;font-weight:600;list-style:none;display:flex;justify-content:space-between;align-items:center;gap:12px}
.faq summary::-webkit-details-marker{display:none}
.faq summary:after{content:"+";font-size:1.3rem;color:var(--muted);transition:transform .2s}
.faq details[open] summary:after{transform:rotate(45deg)}
.faq details p{padding:0 18px 16px;margin:0;color:var(--muted)}

/* ---------- ek bileşenler ---------- */
[hidden]{display:none!important}
.a-toggle{display:none}
.grow-1{flex:1;min-width:240px} .mb0{margin-bottom:.15em} .d-block{display:block}
.btn.on{color:#fb7185;border-color:rgba(251,113,133,.5)} .btn.on .i{fill:currentColor}
.err-code{font-size:4.6rem;font-weight:800;letter-spacing:-.05em;background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent;line-height:1.1}
.store-card{padding:24px}
.store-card.has-banner{padding:0;overflow:hidden}
.store-banner{width:100%;height:clamp(110px,20vw,240px);overflow:hidden;background:var(--bg-2)}
.store-banner img{width:100%;height:100%;object-fit:cover;display:block}
.store-card.has-banner .store-head{padding:18px 24px 24px;align-items:flex-start}
.store-card.has-banner .store-head .avatar{margin-top:-58px;border:4px solid var(--card);box-shadow:0 10px 26px -8px rgba(0,0,0,.7)}
.store-banner-prev{width:100%;max-height:150px;object-fit:cover;border-radius:12px;margin-bottom:12px;display:block}
.store-stats{min-width:300px}
.cat-grid-lg{grid-template-columns:repeat(auto-fill,minmax(min(250px,100%),1fr))}
.chips{display:flex;gap:8px;overflow-x:auto;scrollbar-width:none;margin-bottom:16px;padding-bottom:2px}
.chips::-webkit-scrollbar{display:none}
.chip-c{flex:none;display:inline-flex;align-items:center;gap:8px;padding:6px 13px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--muted);font-size:.86rem;font-weight:500;transition:.2s}
.chip-c:before{content:"";width:7px;height:7px;border-radius:50%;background:var(--c,var(--p-2))}
.chip-c:hover{color:#fff;border-color:var(--line-2)}
.chip-c.on{color:#fff;background:color-mix(in srgb,var(--c,var(--p)) 24%,var(--card));border-color:color-mix(in srgb,var(--c,var(--p)) 70%,transparent)}
.cat-hero{display:flex;align-items:center;gap:16px;padding:20px 22px;border-radius:18px;margin-bottom:18px;border:1px solid color-mix(in srgb,var(--c) 40%,transparent);background:linear-gradient(110deg,color-mix(in srgb,var(--c) 28%,var(--card)),var(--card) 70%)}
.cat-hero{position:relative;overflow:hidden;isolation:isolate}
.cat-hero .hero-img{position:absolute;right:0;top:0;height:100%;width:46%;object-fit:cover;opacity:.5;z-index:-1;-webkit-mask-image:linear-gradient(90deg,transparent,#000 65%);mask-image:linear-gradient(90deg,transparent,#000 65%)}
.cat-hero h1{font-size:1.6rem;margin:0} .cat-hero p{margin:2px 0 0;color:var(--muted)}
.cat-hero .cat-ic{width:56px;height:56px;font-size:1.05rem;border-radius:16px}
.cat-hero .badge{margin-left:auto}
.sellers{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(290px,100%),1fr));gap:12px}
.seller-card{display:flex;gap:14px;align-items:center;padding:16px;border-radius:16px;background:var(--card);border:1px solid var(--line);color:var(--text);transition:.25s var(--ease)}
.seller-card:hover{border-color:var(--line-2);color:#fff}
.seller-card b{display:block;line-height:1.2}
.seller-card .badges{margin-top:6px}
.revs{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(300px,100%),1fr));gap:12px}
.rev-card{display:block;padding:18px;border-radius:16px;background:var(--card);border:1px solid var(--line);color:var(--text);transition:.25s var(--ease)}
.rev-card:hover{border-color:var(--line-2);color:var(--text)}
.rev-card p{margin:10px 0 12px;color:#d6d6e2;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.stat-band{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border:1px solid var(--line);border-radius:20px;background:var(--card);overflow:hidden}
.stat-band>div{padding:26px 20px;text-align:center;border-left:1px solid var(--line)}
.stat-band>div:first-child{border-left:0}
.stat-band b{display:block;font-size:2.1rem;font-weight:800;letter-spacing:-.04em;font-variant-numeric:tabular-nums}
.stat-band span{color:var(--muted);font-size:.88rem}
.cta-band{display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;padding:26px 30px;border-radius:20px;border:1px solid rgba(124,92,255,.35);background:linear-gradient(110deg,#221759,#12102a 70%)}
.cta-band h3{font-size:1.3rem;margin-bottom:.2em} .cta-band p{margin:0;color:var(--p-3);max-width:560px}
.notif-row{display:flex;gap:14px;align-items:center;padding:14px 18px;border-top:1px solid var(--line);color:var(--text)}
.notif-row:first-child{border-top:0}
.notif-row:hover{background:rgba(255,255,255,.035);color:#fff}
.notif-row.unread{background:rgba(124,92,255,.07)}
.notif-row .ti{display:grid;place-items:center;width:38px;height:38px;border-radius:11px;background:var(--p-soft);color:var(--p-2);flex:none}
.maint{display:grid;place-items:center;min-height:100vh;padding:20px}
.maint-card{max-width:460px;text-align:center;padding:40px 34px;border:1px solid var(--line);border-radius:22px;background:var(--card)}
.maint-mark{width:56px;height:56px;font-size:1.6rem;margin:0 auto 18px;border-radius:16px}
/* kategori bannerlari (varsayilan gorseller: static/kategori/) */
.sr-only{position:absolute!important;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.cat-banner{position:relative;margin-bottom:18px;border-radius:18px;overflow:hidden;border:1px solid color-mix(in srgb,var(--c) 45%,transparent);background:color-mix(in srgb,var(--c) 18%,var(--card));box-shadow:0 22px 50px -30px var(--c);aspect-ratio:10/3}
.cat-banner img{display:block;width:100%;height:100%;object-fit:cover}
.cat-banner-count{position:absolute;right:14px;top:14px;padding:5px 12px;border-radius:999px;font-size:.8rem;font-weight:600;color:#fff;background:rgba(8,8,14,.5);border:1px solid rgba(255,255,255,.22);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)}
.cat-ic-img{overflow:hidden;padding:0;background:var(--card-2)}
.cat-ic-img img{width:100%;height:100%;object-fit:cover;object-position:50% 38%;display:block}
.cat-ban-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(280px,100%),1fr));gap:16px}
.cat-ban{display:block;border-radius:16px;overflow:hidden;background:var(--card);border:1px solid var(--line);color:var(--text);transition:transform .25s var(--ease),border-color .25s,box-shadow .25s}
.cat-ban:hover{border-color:color-mix(in srgb,var(--c) 65%,transparent);box-shadow:0 20px 40px -24px var(--c);color:var(--text)}
.cat-ban-art{position:relative;display:block;aspect-ratio:8/5;overflow:hidden;background:color-mix(in srgb,var(--c) 22%,var(--card))}
.cat-ban-art img{display:block;width:100%;height:100%;object-fit:cover;transition:transform .6s var(--ease)}
.cat-ban:hover .cat-ban-art img{transform:scale(1.05)}
.cat-ban-name{position:absolute;left:0;right:0;bottom:0;padding:34px 14px 12px;font-weight:700;font-size:1.05rem;color:#fff;background:linear-gradient(0deg,rgba(0,0,0,.78),transparent)}
.cat-ban-foot{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:10px 14px;font-size:.84rem}
.cat-ban-foot span{color:var(--muted);min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cat-ban-foot em{font-style:normal;font-weight:600;white-space:nowrap}
@media (max-width:640px){.cat-banner{aspect-ratio:8/5;border-radius:14px}.cat-ban-grid{grid-template-columns:minmax(0,1fr)}}

.checklist{display:grid;gap:2px}
.cl-row{display:flex;align-items:center;gap:10px;padding:7px 4px;border-radius:7px;color:var(--muted);font-size:.86rem}
.cl-row:hover{background:rgba(255,255,255,.04);color:#fff}
.cl-row .i{color:var(--dim)} .cl-row.ok{color:var(--text)} .cl-row.ok .i{color:var(--ok)}

.todo{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.todo-i{display:grid;grid-template-columns:auto 1fr;grid-template-rows:auto auto;column-gap:10px;align-items:center;padding:12px 14px;border-radius:10px;background:var(--card);border:1px solid var(--line);color:var(--muted);transition:.2s var(--ease)}
.todo-i .i{grid-row:1 / 3;width:1.5em;height:1.5em;color:var(--dim)}
.todo-i b{font-size:1.35rem;color:var(--text);line-height:1.1;font-variant-numeric:tabular-nums}
.todo-i span{font-size:.78rem}
.todo-i:hover{border-color:var(--line-2);color:#fff}
.todo-i.hot{border-color:rgba(124,92,255,.5);background:linear-gradient(120deg,rgba(124,92,255,.14),var(--card))} .todo-i.hot .i{color:var(--p-2)} .todo-i.hot b{color:#fff}
.todo-i.warn{border-color:rgba(251,191,36,.4)} .todo-i.warn .i{color:var(--warn)}
.swatch{display:inline-block;width:14px;height:14px;border-radius:4px;vertical-align:-2px;margin-right:6px;border:1px solid rgba(255,255,255,.2)}
.ban-prev{display:flex;align-items:center;min-height:54px;padding:10px 14px;border-radius:9px;color:#fff;font-weight:650;background:linear-gradient(110deg,var(--c1),var(--c2));min-width:150px}
.a-side .brand{display:flex;align-items:center;gap:8px}
.a-side .brand .tag-admin{font-size:.6rem;padding:0 6px;margin-left:auto}
.res-h{display:flex;justify-content:space-between;align-items:center;margin:20px 0 8px}
.res-h h3{margin:0;font-size:.95rem}
.sys-row{display:flex;align-items:center;gap:10px;padding:9px 0;border-top:1px solid var(--line)}
.sys-row:first-child{border-top:0}
.sys-row .i{flex:none}
.sys-row.ok .i{color:var(--ok)} .sys-row.bad .i{color:var(--warn)}
.sys-row small{display:block;color:var(--muted)}

/* ---------- animasyon yardımcıları ---------- */
html.js .reveal{opacity:0;transform:translateY(20px);transition:opacity .8s var(--ease),transform .8s var(--ease);transition-delay:calc(var(--d,0) * 70ms)}
html.js .reveal.in{opacity:1;transform:none}
.float-a{animation:drift 8s ease-in-out infinite}

/* ---------- duyarlı ---------- */
@media (max-width:1100px){
  .footer-in{grid-template-columns:1fr 1fr}
  .steps{grid-template-columns:repeat(2,minmax(0,1fr))}
  .trust{grid-template-columns:repeat(2,minmax(0,1fr))}
}
}
@media (max-width:760px){.kpis.c3{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:var(--r);overflow:hidden}
.kpi{background:var(--card);padding:16px 18px;min-width:0}
.kpi .k{display:flex;align-items:center;gap:7px;color:var(--muted);font-size:.78rem;font-weight:500}
.kpi .k .i{color:var(--dim)}
.kpi .v{font-size:1.5rem;font-weight:650;letter-spacing:-.02em;margin-top:6px;font-variant-numeric:tabular-nums;white-space:nowrap}
.kpi .v.ok{color:var(--ok)} .kpi .v.warn{color:var(--warn)}
.kpi .s{color:var(--dim);font-size:.78rem;margin-top:3px}
.kpi .spark{display:block;width:100%;height:28px;margin-top:8px}
.spark polyline{fill:none;stroke:var(--p-2);stroke-width:1.6;vector-effect:non-scaling-stroke;stroke-linejoin:round;stroke-linecap:round}
.spark path{fill:url(#sparkfill);stroke:none}
.delta{display:inline-flex;align-items:center;gap:3px;font-size:.74rem;font-weight:600;padding:1px 6px;border-radius:6px}
.delta.up{color:var(--ok);background:rgba(52,211,153,.12)} .delta.down{color:var(--bad);background:rgba(248,113,113,.12)} .delta.flat{color:var(--muted);background:rgba(255,255,255,.06)}

/* ---------- formlar ---------- */
label{display:block;font-weight:500;font-size:.88rem;margin:0 0 6px;color:#d8d8e4}
.field{margin-bottom:16px}
input[type=text],input[type=email],input[type=password],input[type=number],input[type=date],input[type=datetime-local],input[type=search],input[type=tel],input[type=url],input[type=color],select,textarea{
  width:100%;background:var(--bg-2);border:1px solid var(--line-2);color:var(--text);border-radius:10px;padding:10px 12px;font:inherit;outline:none;transition:border-color .15s,box-shadow .15s}
input[type=color]{padding:3px;height:40px;cursor:pointer}
body.app input[type=text],body.app input[type=email],body.app input[type=password],body.app input[type=number],body.app input[type=date],body.app input[type=datetime-local],body.app input[type=search],body.app input[type=tel],body.app input[type=url],body.app select,body.app textarea{border-radius:8px;padding:8px 11px}
input::placeholder,textarea::placeholder{color:var(--dim)}
input:focus,select:focus,textarea:focus{border-color:var(--p);box-shadow:0 0 0 3px rgba(124,92,255,.22)}
input[type=file]{width:100%;background:var(--bg-2);border:1px dashed var(--line-2);border-radius:10px;padding:10px;color:var(--muted)}
input[type=file]::file-selector-button{background:var(--card-3);border:0;color:var(--text);padding:6px 12px;border-radius:7px;margin-right:12px;cursor:pointer;font:inherit}
textarea{min-height:110px;resize:vertical}
select{appearance:none;-webkit-appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%239b9bb0' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m5 9 7 7 7-7'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 12px center;padding-right:34px}
select option{background:var(--card-2)}
.hint{color:var(--muted);font-size:.8rem;margin-top:5px}
.check{display:flex;gap:10px;align-items:flex-start;font-weight:400}
.check input{margin-top:4px;accent-color:var(--p)}
.inline-form{display:inline}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.filters{display:flex;gap:10px;flex-wrap:wrap;align-items:end;margin-bottom:16px}
.filters .field{margin:0;min-width:150px}
.filters .grow{flex:1;min-width:200px}
.quick{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.quick button{background:rgba(255,255,255,.05);border:1px solid var(--line-2);color:var(--text);border-radius:8px;padding:5px 11px;cursor:pointer;font:inherit;font-size:.84rem;transition:.15s}
.quick button:hover{background:var(--p);border-color:var(--p);color:#fff}
.stepper{display:inline-flex;align-items:center;border:1px solid var(--line-2);border-radius:11px;background:var(--bg-2);overflow:hidden}
.stepper button{width:40px;height:42px;background:none;border:0;color:var(--text);cursor:pointer;font-size:1.1rem}
.stepper button:hover{background:rgba(255,255,255,.07)}
.stepper input{width:54px;text-align:center;border:0;background:transparent;border-radius:0;padding:10px 0;box-shadow:none!important;-moz-appearance:textfield}
.stepper input::-webkit-outer-spin-button,.stepper input::-webkit-inner-spin-button{-webkit-appearance:none}
.input-btn{display:flex;gap:8px}
.input-btn input{flex:1}
.switch{position:relative;display:inline-block;width:38px;height:22px}
.switch input{opacity:0;width:0;height:0}
.switch span{position:absolute;inset:0;background:var(--card-3);border-radius:999px;cursor:pointer;transition:.2s}
.switch span:before{content:"";position:absolute;left:3px;top:3px;width:16px;height:16px;border-radius:50%;background:#fff;transition:.2s}
.switch input:checked+span{background:var(--p)} .switch input:checked+span:before{transform:translateX(16px)}

/* ---------- uyarılar / rozetler ---------- */
.flashes{position:fixed;top:76px;right:18px;z-index:120;display:grid;gap:10px;width:min(390px,calc(100vw - 36px));margin:0!important;pointer-events:none}
.flash{pointer-events:auto;display:flex;justify-content:space-between;align-items:flex-start;gap:12px;padding:12px 14px;border-radius:12px;border:1px solid;background:var(--card-2);box-shadow:var(--shadow);animation:toast .4s var(--ease);font-size:.92rem}
.flash .x{background:none;border:0;color:inherit;font-size:1.3rem;cursor:pointer;line-height:1;opacity:.7}
.flash .x:hover{opacity:1}
@keyframes toast{from{opacity:0;transform:translateX(24px)}to{opacity:1;transform:none}}
.flash-ok{border-color:rgba(52,211,153,.45);color:#a7f3d0;background:#0f2a22}
.flash-bad{border-color:rgba(248,113,113,.5);color:#fecaca;background:#2d1417}
.flash-warn{border-color:rgba(251,191,36,.5);color:#fde68a;background:#2b2210}
.flash-info{border-color:rgba(96,165,250,.45);color:#bfdbfe;background:#0f1d33}
.notice{padding:12px 15px;border-radius:11px;border:1px solid var(--line-2);background:var(--card);margin-bottom:16px;color:#d6d6e2}
.notice.warn{border-color:rgba(251,191,36,.4);background:rgba(251,191,36,.07);color:#fde68a}
.notice.bad{border-color:rgba(248,113,113,.45);background:rgba(248,113,113,.07);color:#fecaca}
.notice.ok{border-color:rgba(52,211,153,.4);background:rgba(52,211,153,.07);color:#a7f3d0}
.badge{display:inline-flex;align-items:center;padding:1px 9px;border-radius:999px;font-size:.74rem;font-weight:600;border:1px solid;white-space:nowrap;line-height:1.7}
.b-ok{color:var(--ok);border-color:rgba(52,211,153,.35);background:rgba(52,211,153,.1)}
.b-warn{color:var(--warn);border-color:rgba(251,191,36,.35);background:rgba(251,191,36,.1)}
.b-bad{color:var(--bad);border-color:rgba(248,113,113,.4);background:rgba(248,113,113,.1)}
.b-muted{color:var(--muted);border-color:var(--line-2);background:rgba(255,255,255,.04)}
.b-info{color:var(--info);border-color:rgba(96,165,250,.4);background:rgba(96,165,250,.1)}
.cnt{display:inline-block;min-width:19px;padding:0 6px;border-radius:999px;background:var(--p);color:#fff;font-size:.7rem;text-align:center;font-weight:700;line-height:19px}
.pos{color:var(--ok)} .neg{color:var(--bad)}

/* ---------- tablo ---------- */
.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:var(--r);background:var(--card)}
table{width:100%;border-collapse:collapse;font-size:.9rem}
th{text-align:left;color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.07em;padding:11px 14px;white-space:nowrap;font-weight:600;border-bottom:1px solid var(--line);background:rgba(255,255,255,.02)}
td{padding:11px 14px;border-top:1px solid var(--line);vertical-align:middle}
tr:first-child td{border-top:0}
tr:hover td{background:rgba(255,255,255,.025)}
td.actions{white-space:nowrap;text-align:right}
td form{margin:0}
body.app th{padding:9px 12px} body.app td{padding:9px 12px}
.empty{text-align:center;padding:46px 20px;color:var(--muted)}
.empty strong{display:block;color:#d6d6e2;margin-bottom:2px}
.pager{display:flex;gap:6px;justify-content:center;margin:24px 0;flex-wrap:wrap}
.pager a,.pager span{min-width:36px;text-align:center;padding:7px 11px;border-radius:9px;background:var(--card);border:1px solid var(--line);color:var(--muted);font-size:.9rem}
.pager a:hover{border-color:var(--line-2);color:#fff}
.pager .on{background:var(--p);border-color:var(--p);color:#fff;font-weight:600}
.tabs{display:flex;gap:2px;flex-wrap:wrap;margin-bottom:18px;border-bottom:1px solid var(--line)}
.tabs a{padding:9px 14px;color:var(--muted);font-weight:500;border-bottom:2px solid transparent;margin-bottom:-1px;font-size:.92rem}
.tabs a:hover{color:#fff}
.tabs a.on{color:#fff;border-color:var(--p)}
.seg{display:inline-flex;background:var(--card);border:1px solid var(--line);border-radius:11px;padding:3px;gap:2px;flex-wrap:wrap}
.seg button,.seg a{background:none;border:0;color:var(--muted);padding:6px 13px;border-radius:8px;cursor:pointer;font:inherit;font-size:.86rem;font-weight:500}
.seg button:hover,.seg a:hover{color:#fff}
.seg .on{background:var(--card-3);color:#fff}

/* ---------- panel kabuğu (satıcı ve yönetici) ---------- */
.admin-shell,.shell{display:grid;grid-template-columns:248px minmax(0,1fr);min-height:100vh}
.a-side,.s-side{background:var(--bg-2);border-right:1px solid var(--line);padding:16px 12px 24px;position:sticky;top:0;height:100vh;overflow:auto}
.a-side .brand,.s-side .brand{padding:4px 8px 6px;font-size:1.15rem}
.s-side .who{display:flex;align-items:center;gap:10px;padding:10px 8px 14px;margin-bottom:6px;border-bottom:1px solid var(--line)}
.s-side .who b{display:block;font-size:.9rem;line-height:1.2} .s-side .who small{color:var(--muted);font-size:.78rem}
.a-side .sep,.s-side .sep{font-size:.68rem;text-transform:uppercase;letter-spacing:.1em;color:var(--dim);padding:16px 10px 5px;font-weight:600}
.a-side a,.s-side nav a{display:flex;align-items:center;gap:10px;padding:7px 10px;border-radius:8px;color:var(--muted);font-weight:500;font-size:.86rem;margin-bottom:1px;position:relative}
.a-side a .i,.s-side nav a .i{opacity:.75}
.a-side a .cnt,.s-side nav a .cnt{margin-left:auto}
.a-side a:hover,.s-side nav a:hover{background:rgba(255,255,255,.05);color:#fff}
.a-side a.on,.s-side nav a.on{background:var(--p-soft);color:#fff}
.a-side a.on .i,.s-side nav a.on .i{color:var(--p-2);opacity:1}
.a-side a.on:before,.s-side nav a.on:before{content:"";position:absolute;left:-12px;top:7px;bottom:7px;width:3px;border-radius:0 3px 3px 0;background:var(--p)}
.a-main,.s-main{padding:0 28px 60px;min-width:0}
.a-top,.s-top{display:flex;justify-content:space-between;align-items:center;padding:14px 0;margin-bottom:18px;border-bottom:1px solid var(--line);gap:12px;flex-wrap:wrap;position:sticky;top:0;z-index:30;background:rgba(10,10,15,.86);backdrop-filter:blur(10px);margin-left:-28px;margin-right:-28px;padding-left:28px;padding-right:28px}
.a-top h1,.s-top h1{font-size:1.15rem;margin:0;font-weight:650;letter-spacing:-.01em}
.a-login{max-width:400px;margin:12vh auto;padding:0 20px}
.tag-admin{display:inline-block;background:rgba(244,114,182,.12);color:#f9a8d4;border:1px solid rgba(244,114,182,.3);border-radius:6px;padding:0 8px;font-size:.68rem;font-weight:700;letter-spacing:.08em}
.tag-seller{display:inline-block;background:var(--p-soft);color:var(--p-3);border:1px solid rgba(124,92,255,.35);border-radius:6px;padding:0 8px;font-size:.68rem;font-weight:700;letter-spacing:.08em}
.gsearch{position:relative;flex:1;max-width:420px}
.gsearch form{display:flex;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:9px}
.gsearch form:focus-within{border-color:var(--p)}
.gsearch .i{margin-left:10px;color:var(--dim)}
.gsearch input{background:transparent;border:0;box-shadow:none!important;padding:7px 10px}
.mini-form{display:flex;gap:6px;align-items:center;justify-content:flex-end;flex-wrap:wrap}
.mini-form input[type=text]{width:150px;padding:6px 10px;font-size:.85rem}
.detail-list p{margin:0 0 .4em}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.log-ip{color:var(--muted);font-size:.8rem}
.page-h{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:20px;flex-wrap:wrap}
.page-h h1{font-size:1.5rem;margin:0}
.crumb{color:var(--dim);font-size:.8rem;margin-bottom:4px}
.section-t{font-size:.72rem;text-transform:uppercase;letter-spacing:.09em;color:var(--dim);font-weight:600;margin:0 0 10px}

/* ---------- hesap yerleşimi ---------- */
.layout{display:grid;grid-template-columns:240px minmax(0,1fr);gap:26px;padding-top:26px;padding-bottom:56px;align-items:start}
.side{position:sticky;top:84px;background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:12px}
.side-user{display:flex;gap:12px;align-items:center;padding:8px 8px 14px;border-bottom:1px solid var(--line);margin-bottom:8px}
.side-user b{display:block} .side-user small{color:var(--muted)}
.side nav{display:grid;gap:1px}
.side nav a{display:flex;align-items:center;gap:10px;padding:9px 11px;border-radius:9px;color:var(--muted);font-weight:500;font-size:.92rem}
.side nav a .i{opacity:.75}
.side nav a:hover{background:rgba(255,255,255,.05);color:#fff}
.side nav a.on{background:var(--p-soft);color:#fff}
.side nav a.on .i{color:var(--p-2);opacity:1}
.side .sep{font-size:.68rem;text-transform:uppercase;letter-spacing:.1em;color:var(--dim);padding:12px 11px 4px}
.balance-hero{position:relative;overflow:hidden;background:linear-gradient(120deg,#20164f,#141032 60%,#0f1226);border:1px solid rgba(124,92,255,.35);border-radius:18px;padding:24px;display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
.balance-hero:before{content:"";position:absolute;right:-60px;top:-80px;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,rgba(124,92,255,.35),transparent 70%)}
.balance-hero>*{position:relative}
.balance-hero .amt{font-size:2.3rem;font-weight:800;letter-spacing:-.03em;font-variant-numeric:tabular-nums}
.balance-hero small{color:var(--p-3)}
.balance-hero .btn{background:rgba(255,255,255,.12);border-color:rgba(255,255,255,.2)}
.balance-hero .btn:hover{background:rgba(255,255,255,.2);box-shadow:none}

/* ---------- grafik ---------- */
.bars{display:flex;gap:5px;align-items:stretch;height:170px;overflow:hidden}
.bar{flex:1;display:flex;flex-direction:column;min-width:0}
.bar-track{flex:1;display:flex;align-items:flex-end;border-radius:5px;background:rgba(255,255,255,.03)}
.bar-fill{display:block;width:100%;border-radius:5px 5px 0 0;background:var(--p);min-height:0;transform-origin:bottom;transition:filter .2s;animation:grow .8s var(--ease) backwards}
.bar:hover .bar-fill{filter:brightness(1.3)}
@keyframes grow{from{transform:scaleY(0)}}
.bar em{font-style:normal;font-size:.62rem;color:var(--dim);text-align:center;margin-top:5px;white-space:nowrap;overflow:hidden;max-width:100%}
.meter{height:6px;border-radius:999px;background:rgba(255,255,255,.07);overflow:hidden}
.meter i{display:block;height:100%;background:var(--p);border-radius:999px}
.hbar{display:grid;grid-template-columns:130px 1fr auto;gap:10px;align-items:center;margin:9px 0;font-size:.88rem}
.hbar .meter{height:8px}
.hbar b{font-variant-numeric:tabular-nums}

/* ---------- e-pin kodu ---------- */
.codebox{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 14px;border-radius:11px;background:var(--bg-2);border:1px dashed rgba(124,92,255,.6);margin-bottom:8px}
.codebox code{font-size:1.02rem;word-break:break-all;color:#fff;letter-spacing:.04em}

/* ---------- kimlik önizleme ---------- */
.kyc-imgs{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.kyc-imgs a{display:block;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:var(--bg)}
.kyc-imgs img{display:block;width:100%;height:150px;object-fit:cover}
.kyc-imgs small{display:block;text-align:center;padding:4px;color:var(--muted)}

/* ---------- alt bilgi ---------- */
.footer{margin-top:auto;border-top:1px solid var(--line);background:var(--bg-2);padding:44px 0 26px;color:var(--muted)}
.footer-in{display:grid;grid-template-columns:1.6fr 1fr 1fr 1fr;gap:30px}
.footer h4{color:#fff;font-size:.9rem;margin-bottom:12px}
.footer ul{list-style:none;padding:0;margin:0;display:grid;gap:8px;font-size:.92rem}
.footer a{color:var(--muted)} .footer a:hover{color:#fff}
.copy{border-top:1px solid var(--line);margin-top:30px;padding-top:18px;font-size:.84rem;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.socials{display:flex;gap:8px;margin-top:14px}
.socials a{display:grid;place-items:center;width:36px;height:36px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--muted)}
.socials a:hover{color:#fff;border-color:var(--line-2)}
.totop{position:fixed;right:20px;bottom:20px;z-index:70;width:44px;height:44px;border-radius:12px;background:var(--card-2);border:1px solid var(--line-2);color:#fff;display:grid;place-items:center;cursor:pointer;opacity:0;transform:translateY(12px);pointer-events:none;transition:.25s var(--ease)}
.totop.on{opacity:1;transform:none;pointer-events:auto}

/* ---------- vitrin: slider ---------- */
.hero-wrap{padding:22px 0 8px}
.slider{position:relative;border-radius:22px;overflow:hidden;height:clamp(290px,33vw,410px);isolation:isolate;background:var(--card);border:1px solid var(--line)}
.slide{position:absolute;inset:0;display:flex;align-items:center;padding:0 clamp(24px,5vw,68px);opacity:0;visibility:hidden;transition:opacity .8s var(--ease),visibility .8s;background:linear-gradient(115deg,var(--c1,#7c5cff),var(--c2,#1b1140))}
.slide.on{opacity:1;visibility:visible;z-index:1}
.slide:before{content:"";position:absolute;inset:0;background:radial-gradient(620px 320px at 82% 18%,rgba(255,255,255,.2),transparent 60%),radial-gradient(520px 420px at 8% 115%,rgba(0,0,0,.45),transparent 60%)}
.slide:after{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.06) 1px,transparent 1px);background-size:46px 46px;-webkit-mask-image:linear-gradient(100deg,transparent 30%,#000);mask-image:linear-gradient(100deg,transparent 30%,#000)}
.slide .shape{position:absolute;border-radius:50%;border:1px solid rgba(255,255,255,.22);z-index:0}
.slide .shape.a{width:340px;height:340px;right:8%;top:-90px;background:radial-gradient(circle at 30% 30%,rgba(255,255,255,.22),rgba(255,255,255,.02) 70%);animation:drift 9s ease-in-out infinite}
.slide .shape.b{width:190px;height:190px;right:26%;bottom:-70px;background:rgba(255,255,255,.07);animation:drift 11s ease-in-out infinite reverse}
.slide .shape.c{width:90px;height:90px;right:5%;bottom:22%;background:rgba(255,255,255,.12);animation:drift 7s ease-in-out infinite}
@keyframes drift{50%{transform:translate3d(-14px,16px,0) scale(1.05)}}
.slide-img{position:absolute;right:0;top:0;bottom:0;width:58%;object-fit:cover;-webkit-mask-image:linear-gradient(90deg,transparent,#000 45%);mask-image:linear-gradient(90deg,transparent,#000 45%);z-index:0}
.slide-body{position:relative;z-index:2;max-width:540px;color:#fff;transform:translateY(18px);opacity:0;transition:transform .9s .2s var(--ease),opacity .9s .2s var(--ease)}
.slide.on .slide-body{transform:none;opacity:1}
.kicker{display:inline-flex;align-items:center;gap:7px;padding:4px 11px;border-radius:999px;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);font-size:.78rem;font-weight:600;margin-bottom:14px;backdrop-filter:blur(6px)}
.slide h2{font-size:clamp(1.7rem,3.8vw,3rem);font-weight:800;letter-spacing:-.035em;line-height:1.04;margin-bottom:.4em;text-wrap:balance}
.slide p{color:rgba(255,255,255,.85);font-size:clamp(.95rem,1.4vw,1.1rem);max-width:440px;margin-bottom:22px}
.slide .btn{background:#fff;color:#111;font-weight:700}
.slide .btn:hover{background:#f1f1f6;color:#000}
.dots{position:absolute;left:clamp(24px,5vw,68px);bottom:22px;display:flex;gap:8px;z-index:5}
.dots button{width:30px;height:4px;border-radius:4px;background:rgba(255,255,255,.28);border:0;position:relative;overflow:hidden;cursor:pointer;padding:0}
.dots button.on:after{content:"";position:absolute;inset:0;background:#fff;transform-origin:left;animation:prog var(--dur,6s) linear forwards}
.slider:hover .dots button.on:after{animation-play-state:paused}
@keyframes prog{from{transform:scaleX(0)}to{transform:scaleX(1)}}
.sl-arrow{position:absolute;top:50%;transform:translateY(-50%);z-index:5;width:42px;height:42px;border-radius:50%;background:rgba(0,0,0,.35);border:1px solid rgba(255,255,255,.2);color:#fff;display:grid;place-items:center;cursor:pointer;opacity:0;transition:.25s;backdrop-filter:blur(6px)}
.slider:hover .sl-arrow{opacity:1}
.sl-arrow:hover{background:rgba(0,0,0,.6)}
.sl-prev{left:14px} .sl-next{right:14px}

.trust{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-top:14px}
.trust>div{display:flex;gap:12px;align-items:center;padding:14px 16px;border:1px solid var(--line);border-radius:14px;background:var(--card);transition:.25s var(--ease)}
.trust>div:hover{border-color:var(--line-2)}
.trust .ti{display:grid;place-items:center;width:38px;height:38px;border-radius:11px;background:var(--p-soft);color:var(--p-2);flex:none}
.trust b{display:block;font-size:.92rem;line-height:1.25} .trust small{color:var(--muted);font-size:.8rem;line-height:1.3;display:block}

.section{padding-top:30px;padding-bottom:30px}
.section-h{display:flex;justify-content:space-between;align-items:end;margin-bottom:18px;gap:12px}
.section-h h2{margin:0;display:flex;align-items:center;gap:10px;font-size:1.4rem}
.section-h h2 .i{color:var(--p-2)}
.section-h p{margin:2px 0 0;color:var(--muted);font-size:.92rem}
.more{display:inline-flex;align-items:center;gap:6px;color:var(--muted);font-size:.9rem;font-weight:500}
.more:hover{color:#fff}
.more .i{transition:transform .2s} .more:hover .i{transform:translateX(3px)}

/* günün oyunları: poster kartları */
.posters{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:14px}
.poster{position:relative;display:block;aspect-ratio:3/4;border-radius:18px;overflow:hidden;background:linear-gradient(165deg,var(--c,#7c5cff),#0b0b11 86%);color:#fff;isolation:isolate;transition:transform .35s var(--ease),box-shadow .35s,border-color .3s;border:1px solid rgba(255,255,255,.08);will-change:transform}
.poster:hover{color:#fff;box-shadow:0 26px 50px -22px var(--c,#7c5cff);border-color:rgba(255,255,255,.22)}
.poster .mono-big{position:absolute;right:-6px;top:4px;font-size:7.4rem;font-weight:900;letter-spacing:-.07em;opacity:.16;line-height:1;transition:transform .5s var(--ease);font-family:var(--font)}
.poster:hover .mono-big{transform:scale(1.12) translate(-6px,6px)}
.poster>img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .7s var(--ease);z-index:-1}
.poster:hover>img{transform:scale(1.07)}
.poster:before{content:"";position:absolute;inset:0;z-index:1;background:linear-gradient(115deg,transparent 30%,rgba(255,255,255,.22) 48%,transparent 62%);transform:translateX(-130%);transition:transform .8s var(--ease);pointer-events:none}
.poster:hover:before{transform:translateX(130%)}
.poster-tag{position:absolute;left:12px;top:12px;z-index:2;display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:999px;background:rgba(0,0,0,.42);border:1px solid rgba(255,255,255,.2);font-size:.7rem;font-weight:600;backdrop-filter:blur(6px)}
.poster-body{position:absolute;left:0;right:0;bottom:0;padding:44px 15px 15px;background:linear-gradient(0deg,rgba(0,0,0,.82),transparent);z-index:2}
.poster-body b{display:block;font-size:1.02rem;line-height:1.2;letter-spacing:-.01em}
.poster-body small{display:block;color:rgba(255,255,255,.72);margin-top:3px;font-size:.8rem}

/* kategori kutuları */
.cat-filter{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px}
.cat-filter button{background:var(--card);border:1px solid var(--line);color:var(--muted);border-radius:999px;padding:6px 14px;cursor:pointer;font:inherit;font-size:.86rem;font-weight:500;transition:.2s}
.cat-filter button:hover{color:#fff;border-color:var(--line-2)}
.cat-filter button.on{background:var(--p);border-color:var(--p);color:#fff}
.cat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px}
.cat-tile{position:relative;display:flex;align-items:center;gap:12px;padding:11px 14px 11px 11px;border-radius:14px;background:var(--card);border:1px solid var(--line);color:var(--text);transition:transform .25s var(--ease),border-color .25s;overflow:hidden}
.cat-tile:before{content:"";position:absolute;inset:0;background:radial-gradient(160px 70px at 0 0,color-mix(in srgb,var(--c) 26%,transparent),transparent);opacity:0;transition:opacity .3s}
.cat-tile:hover{border-color:color-mix(in srgb,var(--c) 60%,transparent);color:#fff}
.cat-tile:hover:before{opacity:1}
.cat-tile.hide{display:none}
.cat-ic{position:relative;width:42px;height:42px;border-radius:12px;display:grid;place-items:center;font-weight:800;font-size:.86rem;letter-spacing:-.02em;color:#fff;background:linear-gradient(140deg,var(--c),color-mix(in srgb,var(--c) 40%,#000));flex:none;box-shadow:inset 0 1px 0 rgba(255,255,255,.28)}
.cat-tile b{display:block;font-size:.92rem;line-height:1.2;position:relative}
.cat-tile small{display:block;color:var(--muted);font-size:.78rem;position:relative}

/* reklam şeridi */
.strip-ad{position:relative;display:flex;align-items:center;justify-content:space-between;gap:20px;padding:20px 28px;border-radius:18px;background:linear-gradient(100deg,var(--c1,#0f766e),var(--c2,#052e2b));color:#fff;overflow:hidden;border:1px solid rgba(255,255,255,.1);transition:transform .3s var(--ease)}
.strip-ad:hover{color:#fff}
.strip-ad:after{content:"";position:absolute;inset:0;background:linear-gradient(110deg,transparent 35%,rgba(255,255,255,.14) 50%,transparent 65%);transform:translateX(-120%);animation:sheen 6s infinite;pointer-events:none}
.strip-ad>*{position:relative;z-index:1}
.strip-ad b{display:block;font-size:1.15rem;letter-spacing:-.02em} .strip-ad span.sub{color:rgba(255,255,255,.8);font-size:.92rem}
.strip-ad .go{display:inline-flex;align-items:center;gap:8px;padding:9px 16px;border-radius:10px;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.25);font-weight:600;font-size:.88rem;white-space:nowrap}
.strip-ad img.bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.35;z-index:0}

/* canlı bant */
.ticker{overflow:hidden;border-block:1px solid var(--line);background:rgba(255,255,255,.018);-webkit-mask-image:linear-gradient(90deg,transparent,#000 7%,#000 93%,transparent);mask-image:linear-gradient(90deg,transparent,#000 7%,#000 93%,transparent)}
.ticker-track{display:flex;gap:44px;width:max-content;padding:11px 0;animation:marquee 60s linear infinite}
.ticker:hover .ticker-track{animation-play-state:paused}
.ticker-item{display:inline-flex;align-items:center;gap:9px;font-size:.86rem;color:var(--muted);white-space:nowrap}
.ticker-item b{color:#fff;font-weight:600}
.ticker-item .live{width:7px;height:7px;border-radius:50%;background:var(--ok);box-shadow:0 0 0 0 rgba(52,211,153,.6);animation:pulse 2s infinite}
@keyframes pulse{70%{box-shadow:0 0 0 8px rgba(52,211,153,0)}100%{box-shadow:0 0 0 0 rgba(52,211,153,0)}}
@keyframes marquee{to{transform:translateX(-50%)}}

/* fırsatlar */
.deal-head{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.countdown{display:inline-flex;gap:6px;font-variant-numeric:tabular-nums}
.countdown span{display:grid;place-items:center;min-width:40px;padding:5px 8px;border-radius:9px;background:var(--card-2);border:1px solid var(--line-2);font-weight:700;font-size:.95rem;line-height:1.1}
.countdown small{display:block;font-size:.58rem;font-weight:500;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}

/* ilan kartı */
.lgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(236px,1fr));gap:16px}
.lcard{position:relative;display:flex;flex-direction:column;border-radius:16px;background:var(--card);border:1px solid var(--line);overflow:hidden;color:var(--text);transition:transform .3s var(--ease),border-color .3s,box-shadow .3s}
.lcard:hover{border-color:var(--line-2);box-shadow:0 22px 44px -24px rgba(0,0,0,.9)}
.lcard .cover{border-radius:0}
.lcard .cover img{transition:transform .7s var(--ease)}
.lcard:hover .cover img{transform:scale(1.06)}
.lcard-body{padding:13px 14px 14px;display:flex;flex-direction:column;gap:9px;flex:1}
.lcard h3{margin:0;font-size:.97rem;line-height:1.3;font-weight:600;letter-spacing:-.01em;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.6em}
.lcard h3 a{color:#fff}
.lcard h3 a:after{content:"";position:absolute;inset:0;z-index:1}
.lcard-meta{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:.8rem;min-width:0}
.lcard-meta .nm{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
.lcard-meta .vf{color:var(--info);flex:none}
.lcard-foot{display:flex;justify-content:space-between;align-items:flex-end;margin-top:auto;gap:8px}
.price{font-size:1.18rem;font-weight:750;color:#fff;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.price-old{display:block;color:var(--dim);text-decoration:line-through;font-size:.78rem;font-weight:500;letter-spacing:0}
.stock{font-size:.72rem;font-weight:600;padding:2px 8px;border-radius:6px;color:var(--ok);background:rgba(52,211,153,.1);border:1px solid rgba(52,211,153,.28)}
.stock.low{color:var(--warn);background:rgba(251,191,36,.1);border-color:rgba(251,191,36,.3)}
.stock.out{color:var(--bad);background:rgba(248,113,113,.1);border-color:rgba(248,113,113,.3)}
.cover .tag-l{position:absolute;left:10px;top:10px;z-index:2;display:inline-flex;align-items:center;gap:6px;padding:3px 9px;border-radius:999px;background:rgba(10,10,15,.82);font-size:.72rem;font-weight:600;color:#fff;border:1px solid rgba(255,255,255,.12)}
.cover .tag-l:before{content:"";width:6px;height:6px;border-radius:50%;background:var(--c,var(--p))}
.cover .tag-b{position:absolute;left:10px;bottom:10px;z-index:2}
.disc{display:inline-block;background:#e5484d;color:#fff;border-radius:6px;padding:1px 7px;font-weight:700;font-size:.74rem}
.fav{position:absolute;right:9px;top:9px;z-index:3;width:34px;height:34px;border-radius:50%;background:rgba(10,10,15,.8);border:1px solid rgba(255,255,255,.14);color:#fff;display:grid;place-items:center;cursor:pointer;transition:.2s var(--ease)}
.fav:hover{transform:scale(1.1);background:rgba(10,10,15,.85)}
.fav.on{color:#fb7185;border-color:rgba(251,113,133,.5)} .fav.on .i{fill:currentColor}
.fav.pop{animation:pop .4s var(--ease)}
@keyframes pop{40%{transform:scale(1.35)}}

/* ---------- ilan detay ---------- */
.crumbs{color:var(--muted);font-size:.86rem;margin:22px 0 14px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.crumbs .sepx{color:var(--dim)}
.detail{display:grid;grid-template-columns:minmax(0,1fr) 390px;gap:24px;align-items:start}
.buybox{position:sticky;top:88px}
.buybox .price{font-size:2rem}
.kv{display:grid;grid-template-columns:auto 1fr;gap:7px 16px;margin:0}
.kv dt{color:var(--muted)} .kv dd{margin:0;text-align:right;font-weight:600}
.total-row{display:flex;justify-content:space-between;align-items:center;margin:14px 0;padding:12px 14px;border-radius:11px;background:rgba(255,255,255,.04);border:1px solid var(--line)}
.total-row strong{font-size:1.3rem;font-variant-numeric:tabular-nums}
.coupon-row{margin:12px 0 4px}
.coupon-msg{font-size:.82rem;margin-top:6px;min-height:1.2em}
.coupon-msg.ok{color:var(--ok)} .coupon-msg.bad{color:var(--bad)}
.perks{list-style:none;padding:0;margin:14px 0 0;display:grid;gap:9px;font-size:.88rem;color:var(--muted)}
.perks li{display:flex;gap:10px;align-items:flex-start}
.perks .i{color:var(--ok);margin-top:2px}
.gallery{position:relative}
.gallery .cover{border-radius:18px;aspect-ratio:16/9}
.seller-box{display:flex;align-items:center;gap:12px}
.share-row{display:flex;gap:8px;margin-top:12px}

/* ---------- giriş / kayıt ---------- */
.auth{max-width:440px;margin:50px auto}
.auth h1{font-size:1.7rem}
.auth-wrap{display:grid;grid-template-columns:1fr 1fr;max-width:940px;margin:44px auto;border:1px solid var(--line);border-radius:24px;overflow:hidden;background:var(--card)}
.auth-art{position:relative;padding:44px 40px;background:linear-gradient(155deg,#5b3fd6,#1b1140 70%);color:#fff;overflow:hidden;display:flex;flex-direction:column;justify-content:space-between;min-height:460px}
.auth-art:before{content:"";position:absolute;width:340px;height:340px;right:-120px;top:-100px;border-radius:50%;background:radial-gradient(circle,rgba(255,255,255,.2),transparent 70%)}
.auth-art h2{font-size:1.9rem;letter-spacing:-.03em;line-height:1.1;position:relative}
.auth-art ul{list-style:none;padding:0;margin:0;display:grid;gap:14px;position:relative}
.auth-art li{display:flex;gap:12px;align-items:flex-start;color:rgba(255,255,255,.88)}
.auth-art li .i{margin-top:3px;color:#fff}
.auth-form{padding:44px 40px}
.auth-form h1{font-size:1.6rem}

/* ---------- puan yıldızları ---------- */
.stars{--v:0;display:inline-block;width:80px;height:16px;vertical-align:middle;
  background:linear-gradient(90deg,#fbbf24 calc(var(--v) * 20%),rgba(255,255,255,.16) 0);
  -webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24'%3E%3Cpath d='M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z'/%3E%3C/svg%3E") repeat-x 0 0/16px 16px;
  mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24'%3E%3Cpath d='M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z'/%3E%3C/svg%3E") repeat-x 0 0/16px 16px}
.stars.sm{width:65px;height:13px;-webkit-mask-size:13px 13px;mask-size:13px 13px}
.rate-line{display:inline-flex;align-items:center;gap:6px;color:var(--muted);font-size:.84rem}
.rate-line b{color:#fff}

/* ---------- rozetler ---------- */
.bd{display:inline-flex;align-items:center;gap:6px;padding:2px 9px;border-radius:7px;font-size:.72rem;font-weight:600;border:1px solid;white-space:nowrap}
.bd:before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor}
.bd-green{color:var(--ok);border-color:rgba(52,211,153,.4);background:rgba(52,211,153,.09)}
.bd-gold{color:#fbbf24;border-color:rgba(251,191,36,.45);background:rgba(251,191,36,.09)}
.bd-purple{color:#c4b5fd;border-color:rgba(167,139,250,.45);background:rgba(124,92,255,.12)}
.bd-blue{color:var(--info);border-color:rgba(96,165,250,.4);background:rgba(96,165,250,.09)}
.badges{display:flex;gap:6px;flex-wrap:wrap}

/* ---------- kapak / avatar ---------- */
.cover{position:relative;aspect-ratio:16/10;overflow:hidden;border-radius:12px;background:var(--card-2)}
.cover img{display:block;width:100%;height:100%;object-fit:cover}
.cover-ph{display:grid;place-items:center;width:100%;height:100%;background:linear-gradient(150deg,var(--c,#7c5cff),color-mix(in srgb,var(--c,#7c5cff) 30%,#0a0a0f));color:rgba(255,255,255,.92);font-size:2.6rem;font-weight:800;letter-spacing:-.04em;position:relative;overflow:hidden}
.cover-ph:after{content:"";position:absolute;width:120%;height:120%;left:-10%;top:-10%;background:radial-gradient(circle at 80% 0,rgba(255,255,255,.22),transparent 55%)}
.cover.wide{aspect-ratio:16/8;border-radius:16px}
.avatar{width:42px;height:42px;border-radius:12px;background:linear-gradient(140deg,#7c5cff,#4b34b8);display:grid;place-items:center;font-weight:700;flex:none;overflow:hidden;color:#fff}
.avatar img{width:100%;height:100%;object-fit:cover;display:block}
.avatar.sm{width:28px;height:28px;border-radius:8px;font-size:.78rem}
.avatar.lg{width:92px;height:92px;border-radius:24px;font-size:2.2rem}
.store-head{display:flex;gap:20px;align-items:center;flex-wrap:wrap}
.thumb{width:74px;height:46px;border-radius:8px;overflow:hidden;background:var(--card-2);flex:none}
.thumb img{width:100%;height:100%;object-fit:cover;display:block}
.preview-img{max-width:280px;border-radius:12px;margin-top:10px;display:block}

/* ---------- yorumlar ---------- */
.review{padding:14px 0;border-top:1px solid var(--line)}
.review:first-child{border-top:0;padding-top:0}
.review .who{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:4px}
.reply{margin-top:8px;padding:10px 12px;border-left:3px solid var(--p);background:rgba(124,92,255,.08);border-radius:0 8px 8px 0}
.reply b{color:var(--p-3)}

/* ---------- sohbet ---------- */
.chat{display:flex;flex-direction:column;height:calc(100vh - 250px);min-height:440px;padding:0;overflow:hidden}
.chat-head{display:flex;gap:12px;align-items:center;padding:14px 18px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.chat-log{flex:1;overflow:auto;padding:16px 18px;display:flex;flex-direction:column;gap:8px}
.msg{max-width:74%;padding:9px 13px;border-radius:14px 14px 14px 4px;background:var(--card-3);align-self:flex-start;white-space:pre-wrap;word-break:break-word}
.msg.me{align-self:flex-end;background:var(--p);border-radius:14px 14px 4px 14px}
.msg time{display:block;font-size:.68rem;opacity:.7;margin-top:3px}
.chat-form{display:flex;gap:10px;padding:12px;border-top:1px solid var(--line);align-items:flex-end}
.chat-form textarea{min-height:46px;height:46px;max-height:140px;resize:none}
.chat-note{padding:8px 18px;font-size:.8rem;color:var(--muted);background:rgba(255,255,255,.025);border-top:1px solid var(--line)}
.conv{display:flex;gap:14px;align-items:center;padding:14px 16px;border-top:1px solid var(--line);color:var(--text)}
.conv:first-child{border-top:0}
.conv:hover{background:rgba(255,255,255,.035);color:var(--text)}
.conv .grow{flex:1;min-width:0}
.conv .ellipsis{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dot-count{min-width:22px;height:22px;padding:0 6px;border-radius:999px;background:var(--accent);color:#fff;font-size:.75rem;font-weight:700;display:inline-grid;place-items:center}

/* ---------- destek talebi ---------- */
.tmsg{border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:12px;background:var(--card)}
.tmsg.staff{border-color:rgba(124,92,255,.5);background:rgba(124,92,255,.08)}
.tmsg.internal{border-style:dashed;border-color:rgba(251,191,36,.5);background:rgba(251,191,36,.05)}
.tmsg .meta{display:flex;justify-content:space-between;gap:10px;color:var(--muted);font-size:.82rem;margin-bottom:6px}

/* ---------- kimlik incelemesi / görsel büyütme ---------- */
.kyc-card{margin-bottom:18px}
.flag-list{margin:0 0 12px;padding:10px 14px 10px 30px;border-radius:10px;border:1px solid rgba(251,191,36,.4);background:rgba(251,191,36,.07);color:#fde68a}
.checks{display:grid;gap:6px;margin:10px 0}
.lightbox{position:fixed;inset:0;background:rgba(5,5,10,.94);display:none;place-items:center;z-index:200;padding:20px;cursor:zoom-out}
.lightbox.on{display:grid}
.lightbox img{max-width:96vw;max-height:92vh;border-radius:8px}
[data-zoom]{cursor:zoom-in}

/* ---------- dokümantasyon ---------- */
.doc pre{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:12px 14px;overflow:auto;font-size:.84rem;margin:8px 0 14px}
.doc h3{margin-top:1.4em}
.doc code.inline{background:rgba(255,255,255,.07);border-radius:6px;padding:1px 6px;font-size:.88em}
.keybox{padding:14px;border-radius:12px;border:1px dashed var(--ok);background:rgba(52,211,153,.07);word-break:break-all}
.calc{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:10px}
.calc div{padding:10px 12px;border-radius:10px;background:rgba(255,255,255,.04);border:1px solid var(--line)}
.calc small{display:block;color:var(--muted)}

/* ---------- basamaklar ---------- */
.steps{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;counter-reset:s}
.step{position:relative;padding:20px;border-radius:16px;background:var(--card);border:1px solid var(--line)}
.step:before{counter-increment:s;content:counter(s);display:grid;place-items:center;width:32px;height:32px;border-radius:9px;background:var(--p-soft);color:var(--p-2);font-weight:700;margin-bottom:12px}
.step h3{margin-bottom:.25em}
.step p{margin:0;color:var(--muted);font-size:.9rem}
.faq details{border:1px solid var(--line);border-radius:12px;background:var(--card);margin-bottom:10px;overflow:hidden}
.faq summary{padding:15px 18px;cursor:pointer;font-weight:600;list-style:none;display:flex;justify-content:space-between;align-items:center;gap:12px}
.faq summary::-webkit-details-marker{display:none}
.faq summary:after{content:"+";font-size:1.3rem;color:var(--muted);transition:transform .2s}
.faq details[open] summary:after{transform:rotate(45deg)}
.faq details p{padding:0 18px 16px;margin:0;color:var(--muted)}

/* ---------- ek bileşenler ---------- */
[hidden]{display:none!important}
.a-toggle{display:none}
.grow-1{flex:1;min-width:240px} .mb0{margin-bottom:.15em} .d-block{display:block}
.btn.on{color:#fb7185;border-color:rgba(251,113,133,.5)} .btn.on .i{fill:currentColor}
.err-code{font-size:4.6rem;font-weight:800;letter-spacing:-.05em;background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent;line-height:1.1}
.store-card{padding:24px}
.store-card.has-banner{padding:0;overflow:hidden}
.store-banner{width:100%;height:clamp(110px,20vw,240px);overflow:hidden;background:var(--bg-2)}
.store-banner img{width:100%;height:100%;object-fit:cover;display:block}
.store-card.has-banner .store-head{padding:18px 24px 24px;align-items:flex-start}
.store-card.has-banner .store-head .avatar{margin-top:-58px;border:4px solid var(--card);box-shadow:0 10px 26px -8px rgba(0,0,0,.7)}
.store-banner-prev{width:100%;max-height:150px;object-fit:cover;border-radius:12px;margin-bottom:12px;display:block}
.store-stats{min-width:300px}
.cat-grid-lg{grid-template-columns:repeat(auto-fill,minmax(min(250px,100%),1fr))}
.chips{display:flex;gap:8px;overflow-x:auto;scrollbar-width:none;margin-bottom:16px;padding-bottom:2px}
.chips::-webkit-scrollbar{display:none}
.chip-c{flex:none;display:inline-flex;align-items:center;gap:8px;padding:6px 13px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--muted);font-size:.86rem;font-weight:500;transition:.2s}
.chip-c:before{content:"";width:7px;height:7px;border-radius:50%;background:var(--c,var(--p-2))}
.chip-c:hover{color:#fff;border-color:var(--line-2)}
.chip-c.on{color:#fff;background:color-mix(in srgb,var(--c,var(--p)) 24%,var(--card));border-color:color-mix(in srgb,var(--c,var(--p)) 70%,transparent)}
.cat-hero{display:flex;align-items:center;gap:16px;padding:20px 22px;border-radius:18px;margin-bottom:18px;border:1px solid color-mix(in srgb,var(--c) 40%,transparent);background:linear-gradient(110deg,color-mix(in srgb,var(--c) 28%,var(--card)),var(--card) 70%)}
.cat-hero{position:relative;overflow:hidden;isolation:isolate}
.cat-hero .hero-img{position:absolute;right:0;top:0;height:100%;width:46%;object-fit:cover;opacity:.5;z-index:-1;-webkit-mask-image:linear-gradient(90deg,transparent,#000 65%);mask-image:linear-gradient(90deg,transparent,#000 65%)}
.cat-hero h1{font-size:1.6rem;margin:0} .cat-hero p{margin:2px 0 0;color:var(--muted)}
.cat-hero .cat-ic{width:56px;height:56px;font-size:1.05rem;border-radius:16px}
.cat-hero .badge{margin-left:auto}
.sellers{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(290px,100%),1fr));gap:12px}
.seller-card{display:flex;gap:14px;align-items:center;padding:16px;border-radius:16px;background:var(--card);border:1px solid var(--line);color:var(--text);transition:.25s var(--ease)}
.seller-card:hover{border-color:var(--line-2);color:#fff}
.seller-card b{display:block;line-height:1.2}
.seller-card .badges{margin-top:6px}
.revs{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(300px,100%),1fr));gap:12px}
.rev-card{display:block;padding:18px;border-radius:16px;background:var(--card);border:1px solid var(--line);color:var(--text);transition:.25s var(--ease)}
.rev-card:hover{border-color:var(--line-2);color:var(--text)}
.rev-card p{margin:10px 0 12px;color:#d6d6e2;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.stat-band{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border:1px solid var(--line);border-radius:20px;background:var(--card);overflow:hidden}
.stat-band>div{padding:26px 20px;text-align:center;border-left:1px solid var(--line)}
.stat-band>div:first-child{border-left:0}
.stat-band b{display:block;font-size:2.1rem;font-weight:800;letter-spacing:-.04em;font-variant-numeric:tabular-nums}
.stat-band span{color:var(--muted);font-size:.88rem}
.cta-band{display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;padding:26px 30px;border-radius:20px;border:1px solid rgba(124,92,255,.35);background:linear-gradient(110deg,#221759,#12102a 70%)}
.cta-band h3{font-size:1.3rem;margin-bottom:.2em} .cta-band p{margin:0;color:var(--p-3);max-width:560px}
.notif-row{display:flex;gap:14px;align-items:center;padding:14px 18px;border-top:1px solid var(--line);color:var(--text)}
.notif-row:first-child{border-top:0}
.notif-row:hover{background:rgba(255,255,255,.035);color:#fff}
.notif-row.unread{background:rgba(124,92,255,.07)}
.notif-row .ti{display:grid;place-items:center;width:38px;height:38px;border-radius:11px;background:var(--p-soft);color:var(--p-2);flex:none}
.maint{display:grid;place-items:center;min-height:100vh;padding:20px}
.maint-card{max-width:460px;text-align:center;padding:40px 34px;border:1px solid var(--line);border-radius:22px;background:var(--card)}
.maint-mark{width:56px;height:56px;font-size:1.6rem;margin:0 auto 18px;border-radius:16px}
/* kategori bannerlari (varsayilan gorseller: static/kategori/) */
.sr-only{position:absolute!important;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.cat-banner{position:relative;margin-bottom:18px;border-radius:18px;overflow:hidden;border:1px solid color-mix(in srgb,var(--c) 45%,transparent);background:color-mix(in srgb,var(--c) 18%,var(--card));box-shadow:0 22px 50px -30px var(--c);aspect-ratio:10/3}
.cat-banner img{display:block;width:100%;height:100%;object-fit:cover}
.cat-banner-count{position:absolute;right:14px;top:14px;padding:5px 12px;border-radius:999px;font-size:.8rem;font-weight:600;color:#fff;background:rgba(8,8,14,.5);border:1px solid rgba(255,255,255,.22);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)}
.cat-ic-img{overflow:hidden;padding:0;background:var(--card-2)}
.cat-ic-img img{width:100%;height:100%;object-fit:cover;object-position:50% 38%;display:block}
.cat-ban-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(280px,100%),1fr));gap:16px}
.cat-ban{display:block;border-radius:16px;overflow:hidden;background:var(--card);border:1px solid var(--line);color:var(--text);transition:transform .25s var(--ease),border-color .25s,box-shadow .25s}
.cat-ban:hover{border-color:color-mix(in srgb,var(--c) 65%,transparent);box-shadow:0 20px 40px -24px var(--c);color:var(--text)}
.cat-ban-art{position:relative;display:block;aspect-ratio:8/5;overflow:hidden;background:color-mix(in srgb,var(--c) 22%,var(--card))}
.cat-ban-art img{display:block;width:100%;height:100%;object-fit:cover;transition:transform .6s var(--ease)}
.cat-ban:hover .cat-ban-art img{transform:scale(1.05)}
.cat-ban-name{position:absolute;left:0;right:0;bottom:0;padding:34px 14px 12px;font-weight:700;font-size:1.05rem;color:#fff;background:linear-gradient(0deg,rgba(0,0,0,.78),transparent)}
.cat-ban-foot{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:10px 14px;font-size:.84rem}
.cat-ban-foot span{color:var(--muted);min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cat-ban-foot em{font-style:normal;font-weight:600;white-space:nowrap}
@media (max-width:640px){.cat-banner{aspect-ratio:8/5;border-radius:14px}.cat-ban-grid{grid-template-columns:minmax(0,1fr)}}

.checklist{display:grid;gap:2px}
.cl-row{display:flex;align-items:center;gap:10px;padding:7px 4px;border-radius:7px;color:var(--muted);font-size:.86rem}
.cl-row:hover{background:rgba(255,255,255,.04);color:#fff}
.cl-row .i{color:var(--dim)} .cl-row.ok{color:var(--text)} .cl-row.ok .i{color:var(--ok)}

.todo{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.todo-i{display:grid;grid-template-columns:auto 1fr;grid-template-rows:auto auto;column-gap:10px;align-items:center;padding:12px 14px;border-radius:10px;background:var(--card);border:1px solid var(--line);color:var(--muted);transition:.2s var(--ease)}
.todo-i .i{grid-row:1 / 3;width:1.5em;height:1.5em;color:var(--dim)}
.todo-i b{font-size:1.35rem;color:var(--text);line-height:1.1;font-variant-numeric:tabular-nums}
.todo-i span{font-size:.78rem}
.todo-i:hover{border-color:var(--line-2);color:#fff}
.todo-i.hot{border-color:rgba(124,92,255,.5);background:linear-gradient(120deg,rgba(124,92,255,.14),var(--card))} .todo-i.hot .i{color:var(--p-2)} .todo-i.hot b{color:#fff}
.todo-i.warn{border-color:rgba(251,191,36,.4)} .todo-i.warn .i{color:var(--warn)}
.swatch{display:inline-block;width:14px;height:14px;border-radius:4px;vertical-align:-2px;margin-right:6px;border:1px solid rgba(255,255,255,.2)}
.ban-prev{display:flex;align-items:center;min-height:54px;padding:10px 14px;border-radius:9px;color:#fff;font-weight:650;background:linear-gradient(110deg,var(--c1),var(--c2));min-width:150px}
.a-side .brand{display:flex;align-items:center;gap:8px}
.a-side .brand .tag-admin{font-size:.6rem;padding:0 6px;margin-left:auto}
.res-h{display:flex;justify-content:space-between;align-items:center;margin:20px 0 8px}
.res-h h3{margin:0;font-size:.95rem}
.sys-row{display:flex;align-items:center;gap:10px;padding:9px 0;border-top:1px solid var(--line)}
.sys-row:first-child{border-top:0}
.sys-row .i{flex:none}
.sys-row.ok .i{color:var(--ok)} .sys-row.bad .i{color:var(--warn)}
.sys-row small{display:block;color:var(--muted)}

/* ---------- animasyon yardımcıları ---------- */
html.js .reveal{opacity:0;transform:translateY(20px);transition:opacity .8s var(--ease),transform .8s var(--ease);transition-delay:calc(var(--d,0) * 70ms)}
html.js .reveal.in{opacity:1;transform:none}
.float-a{animation:drift 8s ease-in-out infinite}

/* ---------- duyarlı ---------- */
@media (max-width:1100px){
  .footer-in{grid-template-columns:1fr 1fr}
  .steps{grid-template-columns:repeat(2,minmax(0,1fr))}
  .trust{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media (max-width:1000px){
  .g4{grid-template-columns:repeat(2,minmax(0,1fr))} .g3{grid-template-columns:repeat(2,minmax(0,1fr))}
  .g-main,.detail,.two-col{grid-template-columns:minmax(0,1fr)}
  .buybox{position:static}
  .layout{grid-template-columns:minmax(0,1fr)}
  .side{position:static}
  .admin-shell,.shell{grid-template-columns:minmax(0,1fr)}
  .a-side,.s-side{position:static;height:auto;display:none}
  .a-side.open,.s-side.open{display:block}
  .a-toggle{display:inline-flex!important}
  .a-main,.s-main{padding:0 16px 40px}
  .a-top,.s-top{margin-left:-16px;margin-right:-16px;padding-left:16px;padding-right:16px}
  .auth-wrap{grid-template-columns:minmax(0,1fr)}.auth-art{min-height:0}
}
@media (max-width:760px){
  .nav-toggle{display:grid}
  .nav,.search{display:none}
  .topbar.open .topbar-in{flex-wrap:wrap;height:auto;padding:10px 22px}
  .topbar.open .nav{display:flex;flex-direction:column;align-items:stretch;width:100%;order:5}
  .topbar.open .search{display:block;max-width:none;width:100%;order:4}
  .top-right{margin-left:auto}
  .g2,.g3,.g4,.form-row,.footer-in,.kyc-imgs,.steps,.trust{grid-template-columns:minmax(0,1fr)}
  .calc{grid-template-columns:minmax(0,1fr)}.msg{max-width:90%}.chat{height:calc(100vh - 200px)}
  .slider{height:340px} .slide-img{opacity:.35;width:100%}
  .sl-arrow{display:none}
  .posters{grid-template-columns:repeat(2,minmax(0,1fr))}
  .lgrid{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
  .strip-ad{flex-direction:column;align-items:flex-start}
  .dd-notif{width:min(340px,calc(100vw - 30px))}
  .hbar{grid-template-columns:90px 1fr auto}
  .stat-band{grid-template-columns:repeat(2,minmax(0,1fr))} .stat-band>div:nth-child(3){border-left:0} .stat-band>div:nth-child(n+3){border-top:1px solid var(--line)}
  .cat-hero{flex-wrap:wrap} .store-stats{min-width:0;width:100%}
  .store-stats.grid.g3{grid-template-columns:repeat(3,minmax(0,1fr))}
}
@media (max-width:420px){.lgrid{grid-template-columns:minmax(0,1fr)}}
/* ---------- güven modülleri: rapor, emanet, kart ödemesi, canlı bildirim ---------- */
.report-box{margin-top:12px;font-size:.88rem}
.report-box summary{cursor:pointer;color:var(--muted);display:inline-flex;align-items:center;gap:6px;list-style:none}
.report-box summary::-webkit-details-marker{display:none}
.report-box summary:hover{color:#fff}
.report-box[open] summary{margin-bottom:10px;color:#fff}
.report-box form{padding:12px;border:1px solid var(--line);border-radius:12px;background:var(--bg-2)}
.report-box.inline{margin-top:0}
.report-box.inline summary{padding:8px 14px;border:1px solid var(--line-2);border-radius:10px;color:#fff}
.report-box.inline[open]{flex-basis:100%}
.row-form{display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap}
.row-form .field{margin-bottom:0}
.stack-form{display:grid;gap:6px;min-width:150px}
.escrow-held{border-color:rgba(251,191,36,.35)}
.escrow-disputed{border-color:rgba(248,113,113,.4)}
.card-method{border-color:rgba(124,92,255,.35);background:linear-gradient(135deg,rgba(124,92,255,.08),transparent 60%),var(--card)}

.cp-state{text-align:center;padding:30px 24px}
.cp-state .kv{text-align:left}
.cp-spin{width:54px;height:54px;border-radius:50%;border:4px solid var(--line-2);border-top-color:var(--p);margin:0 auto 16px;animation:cpspin .9s linear infinite}
@keyframes cpspin{to{transform:rotate(360deg)}}
.cp-done{width:64px;height:64px;border-radius:50%;display:grid;place-items:center;margin:0 auto 14px}
.cp-done .i{width:30px;height:30px}
.cp-done.ok{background:rgba(52,211,153,.14);color:var(--ok)}
.pay-plus{font-size:2.4rem;font-weight:800;color:var(--ok);letter-spacing:-.02em;margin:4px 0 6px;font-variant-numeric:tabular-nums}
.cp-done.bad{background:rgba(248,113,113,.14);color:var(--bad)}

.toasts{position:fixed;right:18px;bottom:18px;z-index:200;display:grid;gap:10px;width:min(360px,calc(100vw - 36px))}
.toast-live{display:grid;gap:2px;padding:13px 16px;border-radius:14px;border:1px solid var(--line-2);background:var(--card-2);color:var(--text);box-shadow:var(--shadow);animation:toast .35s var(--ease);transition:opacity .4s,transform .4s}
.toast-live b{color:#fff}
.toast-live span{color:var(--muted);font-size:.9rem;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.toast-live.out{opacity:0;transform:translateX(20px)}
a.toast-live:hover{border-color:var(--p);color:var(--text)}
.perm-bar{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;padding:10px 18px;background:var(--p-soft);border-bottom:1px solid rgba(124,92,255,.3);font-size:.9rem}
.perm-bar[hidden]{display:none}
.n-head .row{align-items:center}
.n-head .link-btn{font-size:.78rem}

.fee-box{margin:12px 0;padding:12px 14px;border:1px solid var(--line);border-radius:12px;background:var(--p-soft);text-align:left}
.fee-box[hidden]{display:none}
.fee-row{display:flex;justify-content:space-between;gap:12px;padding:3px 0;font-size:.92rem}
.fee-row span{color:var(--muted)}
.fee-total{margin-top:6px;padding-top:8px;border-top:1px dashed var(--line);font-size:1rem}
.fee-total span{color:var(--text)}
[data-feeerr][hidden]{display:none}

@media (prefers-reduced-motion:reduce){
  *,*:before,*:after{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important;scroll-behavior:auto!important}
  html.js .reveal{opacity:1;transform:none}
}

/* satıcı paneli */
.stack{display:grid;gap:16px;align-content:start}
.trend{display:inline-block;margin-left:6px;padding:1px 7px;border-radius:999px;font-size:.72rem;font-weight:600;font-variant-numeric:tabular-nums}
.trend.up{color:var(--ok);background:rgba(52,211,153,.12)} .trend.down{color:var(--bad);background:rgba(248,113,113,.12)}
.attn-row{display:flex;align-items:center;gap:12px;padding:10px 4px;border-top:1px solid var(--line)}
.attn-row:first-of-type{border-top:0}
.attn-row i{width:9px;height:9px;border-radius:50%;flex:none;background:var(--p)}
.attn-row.bad i{background:var(--bad)} .attn-row.warn i{background:var(--warn)} .attn-row.info i{background:#60a5fa}
.attn-row span{flex:1;min-width:0;color:#d6d6e2}
.sum-row{display:flex;justify-content:space-between;gap:12px;padding:8px 0;border-top:1px solid var(--line);font-size:.92rem}
.sum-row:first-of-type{border-top:0} .sum-row span{color:var(--muted)} .sum-row b{font-variant-numeric:tabular-nums}
.top-list{display:grid;gap:14px}
.top-t{display:flex;justify-content:space-between;gap:10px;margin-bottom:6px;font-size:.9rem} .top-t b{white-space:nowrap;font-variant-numeric:tabular-nums}
.top-row .small{margin-top:4px}
.tabs .cnt{display:inline-block;margin-left:4px;padding:0 7px;border-radius:999px;background:rgba(255,255,255,.08);font-size:.74rem;color:var(--muted)}
.s-side nav .cnt.warn{background:rgba(251,191,36,.2);color:#fde68a}
@media (max-width:760px){.attn-row{flex-wrap:wrap}.attn-row span{flex-basis:calc(100% - 30px)}}

/* ---------- mağaza paketleri: mavi tik, altın/elmas rozetleri ---------- */
.vtick,.vtier{display:inline-block;width:1.05em;height:1.05em;vertical-align:-.17em;margin-left:.25em;flex:none;user-select:none}
.vtier{margin-left:.2em}
h1 .vtick,h1 .vtier,.store-head h1 .vtick{width:.78em;height:.78em;vertical-align:-.02em;margin-left:.3em}
h2 .vtick,h2 .vtier{width:.85em;height:.85em;vertical-align:-.04em}
.lcard-meta .vtick,.lcard-meta .vtier{margin-left:-4px;width:15px;height:15px}
.bd-diamond{color:#93c5fd;border-color:rgba(125,160,255,.5);background:linear-gradient(135deg,rgba(34,211,238,.12),rgba(124,92,255,.16))}
.bd-cyan{color:var(--cy);border-color:rgba(34,211,238,.4);background:rgba(34,211,238,.09)}

.pk-lead{max-width:760px;margin-top:-6px;margin-bottom:20px}
.pk-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(285px,100%),1fr));gap:16px;align-items:stretch}
.pk-card{--c:#7c5cff;position:relative;display:flex;flex-direction:column;gap:14px;padding:22px 20px 20px;border-radius:16px;overflow:hidden;
  background:radial-gradient(240px 140px at 0 0,color-mix(in srgb,var(--c) 17%,transparent),transparent 70%),var(--card);
  border:1px solid color-mix(in srgb,var(--c) 28%,var(--line));transition:transform .25s var(--ease),border-color .25s,box-shadow .25s}
.pk-card:hover{border-color:color-mix(in srgb,var(--c) 60%,transparent);box-shadow:0 18px 40px -22px color-mix(in srgb,var(--c) 70%,transparent)}
.pk-card.owned{border-color:color-mix(in srgb,var(--ok) 55%,transparent)}
.pk-card.hot{border-color:color-mix(in srgb,var(--c) 70%,transparent);box-shadow:0 0 0 1px color-mix(in srgb,var(--c) 30%,transparent),0 22px 50px -26px color-mix(in srgb,var(--c) 80%,transparent)}
.pk-card.tier-gold{border-color:rgba(245,179,1,.5)}
.pk-ribbon{position:absolute;top:0;right:18px;padding:3px 11px 4px;border-radius:0 0 9px 9px;font-size:.66rem;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:#fff;background:linear-gradient(90deg,#3b82f6,#8a5cff);box-shadow:0 6px 16px -8px rgba(99,102,241,.9)}
.pk-top{display:flex;gap:14px;align-items:center}
.pk-top h3{margin:0 0 2px;font-size:1.12rem}
.pk-top p{margin:0}
.pk-ico{flex:none;display:grid;place-items:center;width:52px;height:52px;border-radius:15px;color:var(--c);
  background:color-mix(in srgb,var(--c) 14%,var(--card-2));border:1px solid color-mix(in srgb,var(--c) 30%,transparent)}
.pk-ico img{width:34px;height:34px;display:block}
.pk-ico .i{width:26px;height:26px}
.pk-price{display:flex;align-items:baseline;gap:8px}
.pk-price b{font-size:1.9rem;font-weight:800;letter-spacing:-.03em;font-variant-numeric:tabular-nums}
.pk-price span{color:var(--muted);font-size:.86rem}
.pk-feats{list-style:none;margin:0;padding:0;display:grid;gap:8px;font-size:.9rem}
.pk-feats li{display:flex;gap:9px;align-items:flex-start;color:#d6d6e2}
.pk-feats .i{color:var(--c);margin-top:.18em;width:1.05em;height:1.05em;stroke-width:2.4}
.pk-desc{margin:0;line-height:1.5}
.pk-foot{margin-top:auto;display:grid;gap:10px}
.pk-own{display:flex;gap:8px;align-items:center;color:var(--ok);font-weight:600;font-size:.88rem;padding:8px 11px;border-radius:10px;background:rgba(52,211,153,.08);border:1px solid rgba(52,211,153,.3)}
.pk-chip{--c:#7c5cff;display:inline-flex;align-items:center;gap:8px;padding:5px 12px;border-radius:999px;font-size:.84rem;
  background:color-mix(in srgb,var(--c) 14%,var(--card-2));border:1px solid color-mix(in srgb,var(--c) 38%,transparent)}
.pk-chip em{font-style:normal;color:var(--muted);font-size:.78rem}
.pk-mini .row{gap:10px}
.pk-admin-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.pk-edit{--c:#7c5cff;display:flex;flex-direction:column;gap:2px;border-color:color-mix(in srgb,var(--c) 26%,var(--line))}
.pk-edit.off{opacity:.78}
.pk-edit .pk-top{margin-bottom:10px}
.pk-edit .pk-ico{width:44px;height:44px}
.pk-edit .pk-ico img{width:28px;height:28px}
.pk-chips{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}
.pk-chips span{font-size:.72rem;padding:2px 9px;border-radius:999px;background:rgba(255,255,255,.05);border:1px solid var(--line);color:var(--muted)}

/* mağazalar listesi / mağaza sayfası: öne çıkan, altın ve elmas vurgusu */
.pk-flag{display:inline-flex;align-items:center;gap:4px;margin-top:4px;padding:1px 9px;border-radius:999px;font-size:.7rem;font-weight:700;letter-spacing:.02em;color:#fdba74;background:rgba(249,115,22,.12);border:1px solid rgba(249,115,22,.4)}
.pk-flag .i{width:.95em;height:.95em}
.seller-card.pk-featured{border-color:rgba(249,115,22,.45);background:linear-gradient(135deg,rgba(249,115,22,.08),transparent 60%),var(--card)}
.seller-card.pk-gold{border-color:rgba(245,179,1,.5);background:linear-gradient(135deg,rgba(245,179,1,.1),transparent 62%),var(--card)}
.seller-card.pk-diamond{border-color:rgba(125,160,255,.55);background:linear-gradient(135deg,rgba(34,211,238,.1),rgba(124,92,255,.1) 55%,transparent),var(--card)}
.seller-card b{display:flex;align-items:center;flex-wrap:wrap}
.store-card.pk-gold{border-color:rgba(245,179,1,.6);box-shadow:0 0 0 1px rgba(245,179,1,.25),0 22px 60px -30px rgba(245,179,1,.55);
  background:linear-gradient(135deg,rgba(245,179,1,.09),transparent 50%),var(--card)}
.store-card.pk-gold:before{content:"";display:block;height:3px;background:linear-gradient(90deg,#b86e00,#ffe27a,#f7b500,#b86e00)}
.store-card.pk-diamond{border-color:rgba(125,160,255,.65);box-shadow:0 0 0 1px rgba(125,160,255,.28),0 22px 60px -28px rgba(99,140,255,.65);
  background:linear-gradient(135deg,rgba(34,211,238,.09),rgba(124,92,255,.1) 55%,transparent),var(--card)}
.store-card.pk-diamond:before{content:"";display:block;height:3px;background:linear-gradient(90deg,#22d3ee,#6d8bff,#a78bfa,#22d3ee)}
.store-card.pk-gold.has-banner:before,.store-card.pk-diamond.has-banner:before{display:none}
.store-card.pk-gold.has-banner{box-shadow:0 0 0 2px rgba(245,179,1,.4),0 22px 60px -30px rgba(245,179,1,.55)}
.store-card.pk-diamond.has-banner{box-shadow:0 0 0 2px rgba(125,160,255,.45),0 22px 60px -28px rgba(99,140,255,.65)}
.store-card.pk-gold:not(.has-banner),.store-card.pk-diamond:not(.has-banner){padding:0 24px 24px;overflow:hidden}
.store-card.pk-gold:not(.has-banner)>.store-head,.store-card.pk-diamond:not(.has-banner)>.store-head{padding-top:22px}
@media (max-width:900px){.pk-admin-grid{grid-template-columns:minmax(0,1fr)}}
@media (max-width:640px){.pk-grid{grid-template-columns:minmax(0,1fr)}.pk-price b{font-size:1.7rem}}

/* ---------- doping (ilan öne çıkarma) ---------- */
.doping{border:1px solid var(--line-2);border-radius:14px;padding:16px 16px 14px;margin:6px 0 18px;background:rgba(255,255,255,.02);min-width:0}
.doping legend{padding:0 8px;font-weight:700;color:var(--p-3)}
.dp-lead{margin:0 0 12px}
.dp-kind{padding:12px 0;border-top:1px solid var(--line)}
.dp-kind:first-of-type{border-top:0}
.dp-h{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 12px;margin-bottom:9px}
.dp-opts{display:grid;grid-template-columns:repeat(auto-fill,minmax(112px,1fr));gap:8px}
.dp-opt{position:relative;display:block;cursor:pointer;margin:0;font-weight:400}
.dp-opt input{position:absolute;opacity:0;inset:0;width:100%;height:100%;margin:0;cursor:pointer}
.dp-opt span{display:flex;flex-direction:column;gap:1px;padding:9px 12px;border-radius:10px;border:1px solid var(--line-2);background:var(--card);transition:border-color .15s,background .15s}
.dp-opt span b{font-size:.92rem}
.dp-opt span small{color:var(--muted);font-variant-numeric:tabular-nums}
.dp-opt:hover span{border-color:var(--p-2)}
.dp-opt input:checked+span{border-color:var(--p);background:var(--p-soft);box-shadow:0 0 0 1px var(--p) inset}
.dp-opt input:checked+span small{color:var(--p-3)}
.dp-opt input:focus-visible+span{outline:2px solid var(--p-2);outline-offset:2px}
.dp-sum{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px}
.dp-sum div{padding:10px 12px;border-radius:10px;background:rgba(255,255,255,.04);border:1px solid var(--line)}
.dp-sum small{display:block;color:var(--muted)}
.dp-sum b{font-variant-numeric:tabular-nums}
.doping.dp-short [data-doping-total],.doping.dp-short [data-doping-left]{color:var(--bad)}
.dp-warn{margin:12px 0 0}
.dp-tags{display:flex;flex-wrap:wrap;gap:5px;margin-top:5px}
.dp-tag{display:inline-flex;align-items:center;gap:5px;padding:1px 9px;border-radius:999px;font-size:.74rem;font-weight:600;border:1px solid rgba(244,114,182,.4);background:rgba(244,114,182,.1);color:#f9a8d4;line-height:1.7}
.dp-tag .i{width:12px;height:12px}
.dp-tag small{font-weight:400;opacity:.85}
.dp-tag.dp-banner{border-color:rgba(251,191,36,.45);background:rgba(251,191,36,.1);color:#fde68a}
.btn-dp{background:rgba(244,114,182,.14);border-color:rgba(244,114,182,.45);color:#f9a8d4}
.btn-dp:hover{background:rgba(244,114,182,.24);box-shadow:none;color:#fff}
.dp-price-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.dp-price{padding:14px;border-radius:12px;border:1px solid var(--line);background:rgba(255,255,255,.03)}
.dp-price ul{list-style:none;margin:8px 0 0;padding:0}
.dp-price li{display:flex;justify-content:space-between;gap:10px;padding:5px 0;border-top:1px solid var(--line);font-variant-numeric:tabular-nums}
.vitrin{margin:4px 0 22px;padding:16px;border-radius:18px;border:1px solid rgba(244,114,182,.28);background:linear-gradient(160deg,rgba(244,114,182,.07),rgba(124,92,255,.05) 60%,transparent)}
.vitrin-h{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 12px;margin-bottom:12px}
.vitrin-h h2{margin:0;font-size:1.15rem;display:flex;align-items:center;gap:8px}
.vitrin-h h2 .i{color:var(--accent)}
.vitrin-sep{display:flex;align-items:center;gap:12px;margin:2px 0 16px;color:var(--dim);font-size:.78rem;text-transform:uppercase;letter-spacing:.09em;font-weight:600}
.vitrin-sep:before,.vitrin-sep:after{content:"";flex:1;height:1px;background:var(--line)}
.cover .tag-v{position:absolute;left:10px;top:40px;z-index:2;display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:999px;background:linear-gradient(135deg,#f472b6,#a855f7);font-size:.72rem;font-weight:700;color:#fff;box-shadow:0 4px 12px -4px rgba(244,114,182,.7)}
.cover .tag-v .i{width:12px;height:12px}
.slide.ad:before{background:linear-gradient(90deg,rgba(6,6,14,.78),rgba(6,6,14,.35) 55%,transparent),radial-gradient(520px 420px at 8% 115%,rgba(0,0,0,.45),transparent 60%)}
.slide.ad .slide-body{text-shadow:0 2px 14px rgba(0,0,0,.45)}
.slide.ad h2{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.kicker.kicker-ad{background:rgba(251,191,36,.18);border-color:rgba(251,191,36,.55);color:#fde68a}
@media (max-width:760px){.dp-sum{grid-template-columns:minmax(0,1fr)}.dp-opts{grid-template-columns:repeat(2,minmax(0,1fr))}.vitrin{padding:12px}}

/* hesap güvenliği: honeypot, CAPTCHA, 2FA */
.hp{position:absolute!important;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden}
.captcha{margin-bottom:18px}
.captcha label{display:block;margin-bottom:6px}
.captcha-row{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:8px}
.captcha-img{display:block;max-width:100%;height:auto;border-radius:10px;border:1px solid var(--line-2);background:#f3f1ea}
.captcha-refresh{font-size:.88rem;white-space:nowrap}
.captcha input[name=captcha]:not(:placeholder-shown){text-transform:uppercase;letter-spacing:.18em;font-weight:600}
.sec-list{display:grid;gap:16px}
.sec-stat{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:10px}
.sec-table td,.sec-table th{white-space:nowrap}
.qr-box{display:flex;gap:20px;flex-wrap:wrap;align-items:flex-start;margin:14px 0}
.qr-box svg{width:176px;height:176px;border-radius:10px;background:#fff;flex:none}
.qr-key{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:1.02rem;letter-spacing:.06em;word-break:break-all;padding:10px 12px;border:1px dashed var(--line-2);border-radius:10px;background:var(--card)}
.backup-codes{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:14px 0}
.backup-codes code{display:block;padding:9px 12px;border-radius:10px;border:1px solid var(--line-2);background:var(--card);font-size:1.02rem;letter-spacing:.08em;text-align:center}
.code-input{letter-spacing:.3em;font-size:1.25rem;text-align:center;font-weight:600}
/* ---------- yönetici güvenliği: giriş, 2FA, güvenlik sayfası ---------- */
.a-login.wide{max-width:660px}
.hp-field{position:absolute!important;left:-9999px!important;top:auto;width:1px;height:1px;overflow:hidden}
.tf-input{font-size:1.35rem;letter-spacing:.3em;text-align:center;font-variant-numeric:tabular-nums}
.tf-setup{display:grid;grid-template-columns:200px minmax(0,1fr);gap:22px;align-items:start}
.tf-qr{background:#fff;border-radius:14px;padding:10px;line-height:0}
.tf-qr svg{width:100%;height:auto;display:block}
.tf-steps{margin:0 0 12px;padding-left:20px;color:var(--muted);display:grid;gap:6px;font-size:.92rem}
.tf-key{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.98rem;letter-spacing:.04em;word-spacing:.35em;background:var(--bg-2);border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin-bottom:8px;color:#fff}
.code-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.code-grid code{display:block;text-align:center;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:1.05rem;letter-spacing:.08em;background:var(--bg-2);border:1px solid var(--line);border-radius:9px;padding:9px 6px;color:#fff}
details>summary{cursor:pointer;color:var(--p-3);font-weight:600;font-size:.92rem}
@media (max-width:560px){.tf-setup{grid-template-columns:minmax(0,1fr)}.tf-qr{max-width:220px}}
"""
