"""
BeReady, Streamlit interface (English, for public deployment and the Behance case study).
An honest answer on whether someone is ready for a specific trail, and what to do next.

Two modes:
- Check readiness: a deterministic form. Runs instantly and needs no API key.
- Ask BeReady: a deterministic chat using the same guarded readiness policy.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""

import base64
import pathlib
import json
import streamlit as st

from beready.catalog import compile_catalog
from beready.core import assess as core_assess
from beready.discovery import answer as guarded_answer
from beready.trails import TRAILS as CORE_TRAILS
import streamlit.components.v1 as components

st.set_page_config(page_title="BeReady", page_icon="🏔️", layout="centered")


@st.cache_data(show_spinner=False)
def _hero_b64():
    """Load the hero photo next to this file and inline it, so no static server is needed.
    If the file is missing, the app falls back to a text header and still works."""
    p = pathlib.Path(__file__).with_name("hero.jpg")
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else ""

# ---------- Brand (Icelandic highlands): moss, lichen, warm bone, Inter ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #f8f7f0; }
    .brand-title { font-size: 2.4rem; font-weight: 700; color: #2b412e; margin-bottom: 0.1rem; }
    .brand-sub { font-size: 1.05rem; color: #5F7D3F; margin-bottom: 1.2rem; }
    /* hero banner */
    .hero { position: relative; height: 250px; border-radius: 16px; overflow: hidden;
            margin: 0 0 1.4rem 0; background-size: cover; background-position: center 60%;
            display: flex; flex-direction: column; justify-content: center;
            align-items: center; text-align: center;
            padding: 1.3rem 1.5rem; }
    .hero-mark { font-size: 2.7rem; font-weight: 700; color: #f8f7f0; line-height: 1;
                 text-shadow: 0 2px 10px rgba(0,0,0,0.45); }
    .hero-tag { font-size: 1.12rem; color: #dbe3d5; margin-top: 0.25rem;
                text-shadow: 0 1px 6px rgba(0,0,0,0.55); }
    .hero-loc { position: absolute; top: 1rem; left: 1.5rem; font-size: 0.78rem;
                color: #d9ddd3; letter-spacing: 0.04em; text-shadow: 0 1px 4px rgba(0,0,0,0.5); }
    /* smaller hero on phones so the form is reachable with less scrolling */
    @media (max-width: 640px) {
        .hero { height: 190px; padding: 1rem 1.1rem; }
        .hero-mark { font-size: 2.1rem; }
        .hero-tag { font-size: 0.98rem; }
    }
    .card { background: #ffffff; border: 1px solid #e3e2d6; border-radius: 14px;
            padding: 1.1rem 1.3rem; margin-top: 0.8rem;
            box-shadow: 0 6px 22px rgba(43,65,46,0.06); }
    /* group the form inputs into one floating white card, like the design mockup */
    div[data-testid="stForm"] { background: #ffffff; border: 1px solid #e3e2d6;
            border-radius: 16px; padding: 1.2rem 1.4rem; margin-top: 0.4rem;
            box-shadow: 0 8px 26px rgba(43,65,46,0.08); }
    .verdict-ready    { border-left: 6px solid #425844; }
    .verdict-cond     { border-left: 6px solid #b98a2e; }
    .verdict-hard     { border-left: 6px solid #b07d1f; }
    .verdict-toosoon  { border-left: 6px solid #50808e; }
    .verdict-unknown  { border-left: 6px solid #6b7280; }
    .verdict-kicker { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.09em;
                      text-transform: uppercase; color: #5F7D3F; margin-bottom: 0.15rem; }
    .verdict-head { font-size: 1.25rem; font-weight: 600; color: #2b412e; margin-bottom: 0.3rem; }
    .badge { display: inline-block; background: #eef2e8; color: #425844; font-size: 0.7rem;
             font-weight: 600; padding: 0.16rem 0.6rem; border-radius: 999px;
             margin-bottom: 0.55rem; letter-spacing: 0.02em; }
    .plan-title { font-weight: 600; color: #425844; margin-top: 0.5rem; }
    .plan-list { list-style: none; padding-left: 0; margin: 0.3rem 0 0 0; }
    .plan-list li { position: relative; padding-left: 1.5rem; margin-bottom: 0.35rem; color: #2e3a28; }
    .plan-list li:before { content: "\\2713"; position: absolute; left: 0; color: #425844; font-weight: 700; }
    .note { color: #6b7280; font-size: 0.9rem; }
    /* primary action buttons (form submits: Check my readiness, Ask BeReady) */
    .stFormSubmitButton>button, div[data-testid="stFormSubmitButton"] button {
        background: #425844; color: #f8f7f0; border: 0; border-radius: 10px;
        padding: 0.55rem 1.3rem; font-weight: 600; }
    .stFormSubmitButton>button:hover, div[data-testid="stFormSubmitButton"] button:hover {
        background: #2b412e; color: #ffffff; }
    /* secondary buttons (example quick-asks): light outline chips, not solid */
    .stButton>button {
        background: #ffffff; color: #425844; border: 1px solid #cfd8c5; border-radius: 10px;
        padding: 0.5rem 1.1rem; font-weight: 500; }
    .stButton>button:hover {
        background: #f2f4ec; color: #2b412e; border-color: #a9b79a; }
    /* chat tab: alert/info boxes match the palette instead of default blue */
    div[data-testid="stAlert"] { background: #eef2e8; border: 1px solid #dfe5d6;
        border-radius: 12px; }
    div[data-testid="stAlert"], div[data-testid="stAlert"] p { color: #2b412e; }
    /* chat tab: message bubbles read as soft cards */
    div[data-testid="stChatMessage"] { background: #ffffff; border: 1px solid #e8e7db;
        border-radius: 14px; box-shadow: 0 4px 16px rgba(43,65,46,0.05); }
    .honest-note { color: #5F7D3F; font-size: 0.82rem; margin: 0.2rem 0 0.6rem 0; }
    /* make the two modes read as a segmented control, not faint text tabs */
    div[role="tablist"] { gap: 6px; background: #eceee4; padding: 5px; border-radius: 12px;
        display: inline-flex; border-bottom: none; margin-bottom: 0.7rem; }
    [data-testid="stTab"] { padding: 0.45rem 1.15rem !important; border-radius: 9px;
        color: #6b7280 !important; font-weight: 600; border-bottom: none !important;
        box-shadow: none !important; }
    [data-testid="stTab"] > * { color: inherit !important; }
    [data-testid="stTab"][aria-selected="true"] { background: #425844; color: #f8f7f0 !important; }
    [data-testid="stTab"]:hover { color: #2b412e !important; }
    [data-testid="stTab"][aria-selected="true"]:hover { color: #f8f7f0 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Shared policy bridge ----------
FIT_MAP = {"I don't train": 1, "Sometimes active": 2, "I train regularly": 3}


def assess(trail_name, fitness_label, weeks):
    """Compatibility wrapper for callers using display labels."""
    trail_id = next(k for k, rec in CORE_TRAILS.items() if rec["name"] == trail_name)
    return core_assess(trail_id, FIT_MAP[fitness_label], weeks)


def readiness_from_text(query: str) -> str:
    """Keep session rendering in Streamlit, policy and parsing in shared Python."""
    result = guarded_answer(query or "")
    verdict = result.get("assessment")
    st.session_state.pop("_chat_verdict", None)
    st.session_state.pop("_needs_fitness", None)
    if verdict is None:
        if "training level" in result["message"]:
            st.session_state["_needs_fitness"] = True
            st.session_state["_fitness_query"] = query
        return result["message"]
    st.session_state["_chat_verdict"] = {**verdict, "comfort": verdict["comfortable"]}
    plan_text = "\n".join(f"- {step}" for step in verdict["plan"])
    return f"{result['message']}\n\nPlan:\n{plan_text}\n\nFitness preparation only, not medical or mountain-safety clearance."


HERO_TPL = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body{margin:0;background:transparent}
  :root{
    --bone:#f4f2e9; --bone-2:#efece0; --ink:#20301f; --ink-soft:#4a5a44;
    --moss:#42583f; --moss-deep:#2b3f2b; --moss-bright:#5f7d3f;
    --line:#e4e1d3; --white:#ffffff; --muted:#8a917f;
    --ready:#42583f; --cond:#5f7d3f; --hard:#b07d1f; --toosoon:#3f7286;
    --shadow:0 18px 44px rgba(33,48,31,.10), 0 4px 14px rgba(33,48,31,.06);
  }
  *{box-sizing:border-box}
  html,body{margin:0}
  body{
    font-family:'Inter',system-ui,sans-serif; background:var(--bone); color:var(--ink);
    -webkit-font-smoothing:antialiased; line-height:1.5;
    background-image:radial-gradient(1200px 500px at 50% -10%, #f8f7f0 0%, var(--bone) 55%);
  }
  .wrap{max-width:600px; margin:0 auto; padding:26px 18px 60px}

  /* hero */
  .hero{position:relative; height:290px; border-radius:22px; overflow:hidden;
    box-shadow:var(--shadow); display:flex; align-items:center; justify-content:center;}
  .hero img{position:absolute; inset:0; width:100%; height:100%; object-fit:cover; object-position:center 58%}
  .hero .veil{position:absolute; inset:0;
    background:linear-gradient(180deg, rgba(28,40,28,.28) 0%, rgba(28,40,28,.20) 42%, rgba(28,40,28,.62) 100%)}
  .loc{position:absolute; top:16px; left:18px; z-index:2; color:#eaeee2; font-size:12.5px;
    letter-spacing:.03em; font-weight:500; display:flex; align-items:center; gap:6px; text-shadow:0 1px 5px rgba(0,0,0,.5)}
  .loc .ring{width:12px;height:12px;border:2px solid #eaeee2;border-radius:50%;display:inline-block;opacity:.9}
  .hero .center{position:relative; z-index:2; text-align:center; padding:0 20px}
  .brand{font-size:46px; font-weight:800; letter-spacing:-.02em; color:#fff; margin:0; line-height:1;
    text-shadow:0 2px 18px rgba(0,0,0,.4)}
  .tag{margin:10px 0 0; font-size:18px; font-weight:500; color:#e7ece0; text-shadow:0 1px 8px rgba(0,0,0,.5)}

  /* segmented */
  .seg{display:flex; gap:5px; background:var(--bone-2); border:1px solid var(--line);
    padding:5px; border-radius:14px; margin:18px 0 16px}
  .seg button{flex:1; border:0; background:transparent; font-family:inherit; font-weight:600; font-size:14.5px;
    color:var(--ink-soft); padding:10px 12px; border-radius:10px; cursor:pointer; transition:.15s}
  .seg button.on{background:var(--moss); color:#fff; box-shadow:0 3px 10px rgba(43,63,43,.22)}

  /* card */
  .card{background:var(--white); border:1px solid var(--line); border-radius:18px;
    box-shadow:var(--shadow); padding:22px 22px}
  .field{margin-bottom:18px}
  .field:last-child{margin-bottom:0}
  .lbl{font-size:11.5px; font-weight:700; letter-spacing:.10em; text-transform:uppercase; color:var(--moss-bright); margin:0 0 8px}

  /* select */
  .select{position:relative}
  select{width:100%; appearance:none; font-family:inherit; font-size:16px; font-weight:600; color:var(--ink);
    background:var(--bone); border:1px solid var(--line); border-radius:12px; padding:13px 42px 13px 14px; cursor:pointer}
  .select .chev{position:absolute; right:14px; top:50%; transform:translateY(-50%); pointer-events:none; color:var(--ink-soft)}

  /* facts */
  .facts{display:flex; flex-wrap:wrap; gap:7px; margin-top:10px}
  .chip{font-size:12.5px; font-weight:600; color:var(--ink-soft); background:var(--bone-2);
    border:1px solid var(--line); border-radius:999px; padding:5px 11px}
  .facts .risk{width:100%; margin-top:4px; font-size:13px; color:var(--muted)}
  .facts .risk b{color:var(--ink-soft); font-weight:600}

  /* fitness chips */
  .toggle{display:grid; grid-template-columns:repeat(3,1fr); gap:8px}
  .toggle button{font-family:inherit; font-size:14px; font-weight:600; color:var(--ink-soft);
    background:var(--bone); border:1px solid var(--line); border-radius:12px; padding:12px 8px; cursor:pointer; transition:.15s}
  .toggle button.on{background:var(--moss); color:#fff; border-color:var(--moss)}

  /* slider */
  .slider-row{display:flex; align-items:baseline; justify-content:space-between; margin-bottom:8px}
  .slider-row .val{font-size:16px; font-weight:700; color:var(--ink)}
  input[type=range]{width:100%; -webkit-appearance:none; height:6px; border-radius:999px; outline:none;
    background:linear-gradient(90deg,var(--moss) 0%,var(--moss) var(--pct,30%),var(--line) var(--pct,30%),var(--line) 100%)}
  input[type=range]::-webkit-slider-thumb{-webkit-appearance:none; width:20px; height:20px; border-radius:50%;
    background:var(--moss); border:3px solid #fff; box-shadow:0 2px 6px rgba(43,63,43,.35); cursor:pointer}

  /* button */
  .btn{width:100%; margin-top:20px; border:0; font-family:inherit; font-weight:700; font-size:15.5px; color:#fff;
    background:var(--moss); padding:15px; border-radius:13px; cursor:pointer; transition:.15s; box-shadow:0 8px 20px rgba(43,63,43,.22)}
  .btn:hover{background:var(--moss-deep)}

  /* verdict */
  .verdict{margin-top:16px; background:var(--white); border:1px solid var(--line); border-radius:18px;
    box-shadow:var(--shadow); overflow:hidden; display:none}
  .verdict.show{display:block; animation:rise .28s ease}
  @keyframes rise{from{opacity:0; transform:translateY(8px)}to{opacity:1; transform:none}}
  .verdict .bar{height:5px; background:var(--accent)}
  .verdict .body{padding:22px}
  .vhead{display:flex; align-items:center; gap:12px}
  .emblem{width:42px;height:42px;border-radius:12px;flex:none;display:flex;align-items:center;justify-content:center;
    background:color-mix(in srgb, var(--accent) 14%, #fff); color:var(--accent)}
  .kick{font-size:11px; font-weight:800; letter-spacing:.12em; text-transform:uppercase; color:var(--accent); margin:0}
  .vtitle{font-size:24px; font-weight:800; letter-spacing:-.01em; color:var(--ink); margin:2px 0 0}
  .why{margin:12px 0 0; font-size:15px; color:var(--ink-soft)}
  .computed{margin:16px 0 4px; padding-top:15px; border-top:1px solid var(--line); font-size:12px;
    font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--muted)}
  .inputs{display:flex; flex-wrap:wrap; gap:7px; margin-top:9px}
  .inputs .chip{background:#fff; border-color:var(--line)} .inputs .chip.grade{color:var(--moss); background:#eef2e8; border-color:#dbe6d0}
  .plan{list-style:none; padding:0; margin:16px 0 0}
  .plan li{display:flex; gap:10px; align-items:flex-start; padding:7px 0; font-size:14.5px; color:var(--ink)}
  .plan svg{flex:none; margin-top:2px; color:var(--accent)}
  .foot{display:flex; align-items:center; gap:10px; margin-top:16px; padding-top:15px; border-top:1px solid var(--line); flex-wrap:wrap}
  .badge{font-size:12px; font-weight:600; color:var(--moss); background:#eef2e8; border:1px solid #dfe6d6; border-radius:999px; padding:5px 11px; display:inline-flex; align-items:center; gap:6px}
  .disc{font-size:12.5px; color:var(--muted); margin:0}

  .note{font-size:12.5px;color:var(--muted);text-align:center;margin:14px 4px 0}
  .ask-lead{margin:0 0 14px;font-size:14.5px;color:var(--ink-soft)}
  .ask-box{display:flex;gap:9px}
  .ask-box input{flex:1;font-family:inherit;font-size:15px;color:var(--ink);background:var(--bone);border:1px solid var(--line);border-radius:12px;padding:13px 14px;outline:none}
  .ask-box .btn{width:auto;margin:0;white-space:nowrap;box-shadow:none;padding:13px 20px}
  .examples{display:flex;flex-direction:column;gap:8px}
  .examples button{text-align:left;font-family:inherit;font-size:14px;font-weight:500;color:var(--ink);background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 14px;cursor:pointer;transition:.15s}
  .examples button:hover{background:var(--bone);border-color:#cfd3c2}
</style></head><body><div class="hero">
    <img src="data:image/jpeg;base64,__HERO__" alt="Icelandic highlands">
    <div class="veil"></div>
    <div class="loc"><span class="ring"></span> Th&oacute;rsm&ouml;rk, Iceland</div>
    <div class="center">
      <h1 class="brand">BeReady</h1>
      <p class="tag">Can you handle this trail?</p>
    </div>
  </div><script>(function(){function rz(){var el=document.querySelector(".wrap");var h=Math.ceil(el?el.getBoundingClientRect().bottom:document.documentElement.scrollHeight)+12;window.parent.postMessage({isStreamlitMessage:true,type:"streamlit:setFrameHeight",height:h},"*");}window.addEventListener('load',rz);setInterval(rz,400);try{new ResizeObserver(rz).observe(document.body);}catch(e){}})();</script></body></html>'''

QC_HTML = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body{margin:0;background:transparent}
  :root{
    --bone:#f4f2e9; --bone-2:#efece0; --ink:#20301f; --ink-soft:#455540;
    --moss:#42583f; --moss-deep:#2b3f2b; --moss-bright:#4f6a34;
    --line:#e4e1d3; --white:#fff; --muted:#6b7360;
    --ready:#42583f; --cond:#5f7d3f; --hard:#b07d1f; --toosoon:#356274;
    --zoneSoon:#e7d3c9; --zoneTight:#efe2c4; --zoneOk:#dce7d0;
    --shadow:0 18px 44px rgba(33,48,31,.10), 0 4px 14px rgba(33,48,31,.06);
  }
  *{box-sizing:border-box}
  body{font-family:'Inter',system-ui,sans-serif;background:transparent;color:var(--ink);-webkit-font-smoothing:antialiased;line-height:1.5}
  .wrap{max-width:600px;margin:0 auto;padding:0}
  .card{background:var(--white);border:1px solid var(--line);border-radius:18px;box-shadow:var(--shadow);padding:22px}
  .field{margin-bottom:18px} .field:last-child{margin-bottom:0}
  .lbl{font-size:11.5px;font-weight:700;letter-spacing:.10em;text-transform:uppercase;color:var(--moss-bright);margin:0 0 8px}
  .select{position:relative}
  select{width:100%;appearance:none;font-family:inherit;font-size:16px;font-weight:600;color:var(--ink);background:var(--bone);border:1px solid var(--line);border-radius:12px;padding:13px 42px 13px 14px;cursor:pointer}
  .select .chev{position:absolute;right:14px;top:50%;transform:translateY(-50%);pointer-events:none;color:var(--ink-soft)}
  .facts{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px}
  .chip{font-size:12.5px;font-weight:600;color:var(--ink-soft);background:var(--bone-2);border:1px solid var(--line);border-radius:999px;padding:5px 11px}
  .facts .risk{width:100%;margin-top:4px;font-size:13px;color:var(--muted)}
  .facts .risk b{color:var(--ink-soft);font-weight:600}
  #facts{display:block;margin-top:10px}
  #facts .meta{font-size:13.5px;color:var(--ink-soft);font-weight:600}
  #facts .risk{margin-top:3px;font-size:13px;color:var(--muted)}
  .fithint{font-size:12.5px;color:var(--muted);margin:-2px 0 8px}
  .toggle{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
  .toggle button{display:flex;align-items:center;justify-content:center;gap:8px;font-family:inherit;font-size:13.5px;font-weight:600;color:var(--ink-soft);background:#fff;border:1px solid #cdd5c4;border-radius:12px;padding:13px 6px;cursor:pointer;transition:.15s}
  .toggle button .dot{width:15px;height:15px;border-radius:50%;border:2px solid #b9c3af;flex:none}
  .toggle button:hover{border-color:var(--moss);box-shadow:0 2px 8px rgba(43,63,43,.08)}
  .toggle button:hover .dot{border-color:var(--moss)}
  .toggle button.on{background:var(--moss);color:#fff;border-color:var(--moss)}
  .toggle button.on .dot{border-color:#fff;background:#fff;box-shadow:inset 0 0 0 3px var(--moss)}
  .toggle button:focus-visible,select:focus-visible,input[type=range]:focus-visible{outline:2px solid var(--moss-bright);outline-offset:2px}
  .slider-row{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:8px}
  .slider-row .val{font-size:16px;font-weight:700;color:var(--ink)}
  input[type=range]{width:100%;-webkit-appearance:none;height:6px;border-radius:999px;outline:none;background:linear-gradient(90deg,var(--moss) 0%,var(--moss) var(--pct,30%),var(--line) var(--pct,30%),var(--line) 100%)}
  input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:26px;height:26px;border-radius:50%;background:var(--moss);border:3px solid #fff;box-shadow:0 2px 6px rgba(43,63,43,.35);cursor:pointer}
  input[type=range]::-moz-range-thumb{width:26px;height:26px;border-radius:50%;background:var(--moss);border:3px solid #fff;cursor:pointer}
  .track{position:relative}
  .ticks{position:relative;height:24px;margin-top:5px}
  .ticks .t{position:absolute;top:0;display:flex;flex-direction:column;align-items:center;font-size:11px;color:var(--muted);transform:translateX(-50%);white-space:nowrap}
  .ticks .t.edgeL{transform:none;align-items:flex-start}
  .ticks .t.edgeR{transform:translateX(-100%);align-items:flex-end}
  .ticks .t i{width:1px;height:6px;background:var(--line);margin-bottom:3px}
  .ticks .t.brk{color:var(--moss-bright);font-weight:600}
  .ticks .t.brk i{height:11px;width:2px;background:var(--moss-bright)}
  /* verdict, simplified */
  .verdict{margin-top:16px;background:var(--white);border:1px solid var(--line);border-radius:18px;box-shadow:var(--shadow);overflow:hidden}
  .verdict .bar{height:5px;background:var(--accent)}
  .vb{padding:22px}
  .vhead{display:flex;align-items:center;gap:12px}
  .emblem{width:42px;height:42px;border-radius:12px;flex:none;display:flex;align-items:center;justify-content:center;background:color-mix(in srgb,var(--accent) 14%,#fff);color:var(--accent)}
  .kick{font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);margin:0}
  .vtitle{font-size:24px;font-weight:800;letter-spacing:-.01em;color:var(--ink);margin:2px 0 0}
  .why{margin:13px 0 0;font-size:15px;color:var(--ink-soft)}
  .runway{margin:18px 0 0}
  .runway .rtrack{position:relative;height:14px;border-radius:999px;overflow:hidden;display:flex}
  .runway .zone{height:100%}
  .runway .z1{background:var(--zoneSoon)} .runway .z2{background:var(--zoneTight)} .runway .z3{background:var(--zoneOk)}
  .runway .you{position:absolute;top:-5px;width:4px;height:24px;border-radius:2px;background:var(--ink);transform:translateX(-50%);box-shadow:0 0 0 3px #fff}
  .runway .scale{position:relative;height:16px;margin-top:7px}
  .runway .mk{position:absolute;transform:translateX(-50%);font-size:11px;color:var(--muted);white-space:nowrap}
  .runway .note{margin:12px 0 0;font-size:13.5px;color:var(--ink);font-weight:600}
  .runway .note span{color:var(--muted);font-weight:500}
  details.more{margin:16px 0 0;border-top:1px solid var(--line);padding-top:12px}
  details.more summary{cursor:pointer;font-size:13px;font-weight:600;color:var(--moss-bright);list-style:none}
  details.more summary::-webkit-details-marker{display:none}
  details.more summary::after{content:" +";color:var(--muted)}
  details.more[open] summary::after{content:" -"}
  .plan{list-style:none;padding:0;margin:12px 0 0}
  .plan li{display:flex;gap:10px;align-items:flex-start;padding:6px 0;font-size:14px;color:var(--ink)}
  .plan svg{flex:none;margin-top:2px;color:var(--accent)}
  .computed{margin:18px 0 4px;padding-top:15px;border-top:1px solid var(--line);font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
  .inputs{display:flex;flex-wrap:wrap;gap:7px;margin-top:9px}
  .inputs .chip{background:#fff;border-color:var(--line)} .inputs .chip.grade{color:var(--moss);background:#eef2e8;border-color:#dbe6d0}
  .disc{font-size:12px;color:var(--muted);margin:12px 0 0}
  .foot{display:flex;align-items:center;gap:8px;margin-top:16px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;font-weight:600;color:var(--moss)}
</style></head><body><div class="wrap">
  <div class="card">
    <div class="field">
      <p class="lbl" id="lbl-trail">Trail</p>
      <div class="select"><select id="trail" aria-labelledby="lbl-trail"></select>
        <svg class="chev" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M6 9l6 6 6-6"/></svg></div>
      <div class="facts" id="facts"></div>
    </div>
    <div class="field">
      <p class="lbl" id="lbl-fit">Fitness level</p>
      <p class="fithint">Choose one to see your verdict</p>
      <div class="toggle" id="fit" role="radiogroup" aria-labelledby="lbl-fit">
        <button role="radio" aria-checked="false" data-v="1"><span class="dot"></span>I don't train</button>
        <button role="radio" aria-checked="false" data-v="2"><span class="dot"></span>Sometimes active</button>
        <button role="radio" aria-checked="false" data-v="3"><span class="dot"></span>I train regularly</button>
      </div>
    </div>
    <div class="field">
      <div class="slider-row"><p class="lbl" style="margin:0" id="lbl-weeks">Time until the hike</p><span class="val" id="wval">8 weeks</span></div>
      <div class="track">
        <input type="range" id="weeks" min="0" max="51" value="7" aria-labelledby="lbl-weeks" aria-valuetext="8 weeks">
        <div class="ticks" id="ticks"></div>
      </div>
    </div>
  </div>

  <div class="verdict" id="verdict" aria-live="polite">
    <div class="bar"></div>
    <div class="vb">
      <div class="vhead"><div class="emblem" id="emblem"></div>
        <div><p class="kick">Verdict</p><h2 class="vtitle" id="vtitle"></h2></div></div>
      <p class="why" id="why"></p>
      <div id="result">
      <div class="runway" id="runway">
        <div class="rtrack"><div class="zone z1" id="z1"></div><div class="zone z2" id="z2"></div><div class="zone z3" id="z3"></div><div class="you" id="you"></div></div>
        <div class="scale" id="scale"></div>
        <p class="note" id="rnote"></p>
      </div>
      <p class="computed">Computed from</p>
      <div class="inputs" id="inputs"></div>
      <ul class="plan" id="plan"></ul>
      <p class="disc">Fitness readiness only, not a medical or mountain-safety clearance.</p>
      </div>
      <div class="foot"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6"><path d="M20 6L9 17l-5-5"/></svg> Computed, not guessed</div>
    </div>
  </div>
</div>
<script>
const CATALOG=__CATALOG__;
const TRAILS=Object.fromEntries(CATALOG.trails.map(t=>[t.name,t]));
const GRADE={1:"Easy",2:"Moderate",3:"Demanding",4:"Very demanding"};
const WEEKS=CATALOG.weeks;
const ICON={ready:'<path d="M20 6L9 17l-5-5"/>',cond:'<path d="M12 19V5M5 12l7-7 7 7"/>',hard:'<path d="M3 20h18L12 4z"/>',toosoon:'<circle cx="12" cy="12" r="9"/><path d="M12 8v4l3 2"/>'};
const ACC={ready:"var(--ready)",cond:"var(--cond)",hard:"var(--hard)",toosoon:"var(--toosoon)"};
let fit=null;
const trail=document.getElementById('trail'), weeks=document.getElementById('weeks');
Object.keys(TRAILS).forEach(n=>{const o=document.createElement('option');o.textContent=n;trail.appendChild(o);});
const curWeeks=()=>WEEKS[+weeks.value];
function fmtVal(w){ return w===1 ? '1 week' : (w+' weeks'); }
function lookupAssessment(t,fit,w){const a=t.assessments[String(fit)][String(w)];return {...a,s:a.status,h:a.head,fl:a.floor,co:a.comfortable};}
function facts(){const t=TRAILS[trail.value];
  document.getElementById('facts').innerHTML=
    `<div class="meta">${t.km} km &middot; ${t.days} day${t.days>1?'s':''} &middot; ${GRADE[t.grade]}</div>`+
    `<div class="risk">Watch: <b>${t.risk}</b>.</div>`;}
let lastKey="";
function render(animate){
  const v=document.getElementById('verdict'), res=document.getElementById('result');
  if(fit===null){
    v.style.setProperty('--accent','#8a917f');
    document.getElementById('emblem').innerHTML='<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M5 12h14"/></svg>';
    document.getElementById('vtitle').textContent='Your verdict';
    document.getElementById('why').textContent='Choose your training level above, and your verdict appears here.';
    res.style.display='none'; lastKey=''; return;
  }
  res.style.display='';
  const t={...TRAILS[trail.value],name:trail.value}, w=curWeeks();
  const r=lookupAssessment(t,fit,w);
  v.style.setProperty('--accent',ACC[r.s]);
  document.getElementById('emblem').innerHTML=`<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">${ICON[r.s]}</svg>`;
  document.getElementById('vtitle').textContent=r.h;
  document.getElementById('why').textContent=r.why;
  const rw=document.getElementById('runway');
  if(r.s==="ready"){rw.style.display="none";}
  else{rw.style.display="block";
    const fl=r.fl, co=r.co, end=Math.max(co+(t.diff>=4?8:6), w);
    const pct=x=>Math.max(0,Math.min(100,((x-1)/(end-1))*100));
    document.getElementById('z1').style.width=pct(fl)+"%";
    document.getElementById('z2').style.width=(pct(co)-pct(fl))+"%";
    document.getElementById('z3').style.width=(100-pct(co))+"%";
    document.getElementById('you').style.left=pct(w)+"%";
    document.getElementById('scale').innerHTML=`<span class="mk" style="left:${pct(fl)}%">${fl} wk</span><span class="mk" style="left:${pct(co)}%">${co} wk, comfortable</span>`;
    document.getElementById('rnote').innerHTML= w>=co
      ? `You have ${fmtVal(w)}. <span>Comfortable is about ${co} weeks. You are set.</span>`
      : (w<fl ? `You have ${fmtVal(w)}. <span>This trip needs about ${co} weeks. Give it more time.</span>`
             : `You have ${fmtVal(w)}. <span>Comfortable is about ${co} weeks. Add weeks if you can.</span>`);
  }
  document.getElementById('plan').innerHTML=r.plan.map(p=>`<li><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6"><path d="M20 6L9 17l-5-5"/></svg><span>${p}</span></li>`).join('');
  const inputs=document.getElementById('inputs');
  inputs.replaceChildren(...r.inputs.map(text=>{const span=document.createElement('span');span.className='chip';span.textContent=text;return span;}));
  const key=r.s+r.h;
  if(animate && key!==lastKey){v.classList.remove('flash');void v.offsetWidth;v.classList.add('flash');}
  lastKey=key;
}
function setPct(){weeks.style.setProperty('--pct',(weeks.value/51*100)+'%');
  const txt=fmtVal(curWeeks());document.getElementById('wval').textContent=txt; weeks.setAttribute('aria-valuetext',txt);}
document.getElementById('ticks').innerHTML=
  [[0,"1 wk","edgeL"],[7,"8 wks",""],[23,"24 wks","brk"],[51,"1 year","edgeR"]]
  .map(a=>'<span class="t '+a[2]+'" style="left:'+(a[0]/51*100)+'%"><i></i>'+a[1]+'</span>').join('');
trail.onchange=()=>{facts();render(true);};
weeks.oninput=()=>{setPct();render(true);};
document.querySelectorAll('#fit button').forEach(b=>b.onclick=()=>{document.querySelectorAll('#fit button').forEach(x=>{x.classList.remove('on');x.setAttribute('aria-checked','false');});b.classList.add('on');b.setAttribute('aria-checked','true');fit=+b.dataset.v;render(true);});
facts();setPct();render(false);
</script><script>(function(){function rz(){var el=document.querySelector(".wrap");var h=Math.ceil(el?el.getBoundingClientRect().bottom:document.documentElement.scrollHeight)+12;window.parent.postMessage({isStreamlitMessage:true,type:"streamlit:setFrameHeight",height:h},"*");}window.addEventListener("load",rz);setInterval(rz,400);try{new ResizeObserver(rz).observe(document.body);}catch(e){}})();</script></body></html>'''

VERDICT_CARD = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body{margin:0;background:transparent}.verdict{margin-top:0 !important}
  :root{
    --bone:#f4f2e9; --bone-2:#efece0; --ink:#20301f; --ink-soft:#4a5a44;
    --moss:#42583f; --moss-deep:#2b3f2b; --moss-bright:#5f7d3f;
    --line:#e4e1d3; --white:#ffffff; --muted:#8a917f;
    --ready:#42583f; --cond:#5f7d3f; --hard:#b07d1f; --toosoon:#3f7286;
    --shadow:0 18px 44px rgba(33,48,31,.10), 0 4px 14px rgba(33,48,31,.06);
  }
  *{box-sizing:border-box}
  html,body{margin:0}
  body{
    font-family:'Inter',system-ui,sans-serif; background:var(--bone); color:var(--ink);
    -webkit-font-smoothing:antialiased; line-height:1.5;
    background-image:radial-gradient(1200px 500px at 50% -10%, #f8f7f0 0%, var(--bone) 55%);
  }
  .wrap{max-width:600px; margin:0 auto; padding:26px 18px 60px}

  /* hero */
  .hero{position:relative; height:290px; border-radius:22px; overflow:hidden;
    box-shadow:var(--shadow); display:flex; align-items:center; justify-content:center;}
  .hero img{position:absolute; inset:0; width:100%; height:100%; object-fit:cover; object-position:center 58%}
  .hero .veil{position:absolute; inset:0;
    background:linear-gradient(180deg, rgba(28,40,28,.28) 0%, rgba(28,40,28,.20) 42%, rgba(28,40,28,.62) 100%)}
  .loc{position:absolute; top:16px; left:18px; z-index:2; color:#eaeee2; font-size:12.5px;
    letter-spacing:.03em; font-weight:500; display:flex; align-items:center; gap:6px; text-shadow:0 1px 5px rgba(0,0,0,.5)}
  .loc .ring{width:12px;height:12px;border:2px solid #eaeee2;border-radius:50%;display:inline-block;opacity:.9}
  .hero .center{position:relative; z-index:2; text-align:center; padding:0 20px}
  .brand{font-size:46px; font-weight:800; letter-spacing:-.02em; color:#fff; margin:0; line-height:1;
    text-shadow:0 2px 18px rgba(0,0,0,.4)}
  .tag{margin:10px 0 0; font-size:18px; font-weight:500; color:#e7ece0; text-shadow:0 1px 8px rgba(0,0,0,.5)}

  /* segmented */
  .seg{display:flex; gap:5px; background:var(--bone-2); border:1px solid var(--line);
    padding:5px; border-radius:14px; margin:18px 0 16px}
  .seg button{flex:1; border:0; background:transparent; font-family:inherit; font-weight:600; font-size:14.5px;
    color:var(--ink-soft); padding:10px 12px; border-radius:10px; cursor:pointer; transition:.15s}
  .seg button.on{background:var(--moss); color:#fff; box-shadow:0 3px 10px rgba(43,63,43,.22)}

  /* card */
  .card{background:var(--white); border:1px solid var(--line); border-radius:18px;
    box-shadow:var(--shadow); padding:22px 22px}
  .field{margin-bottom:18px}
  .field:last-child{margin-bottom:0}
  .lbl{font-size:11.5px; font-weight:700; letter-spacing:.10em; text-transform:uppercase; color:var(--moss-bright); margin:0 0 8px}

  /* select */
  .select{position:relative}
  select{width:100%; appearance:none; font-family:inherit; font-size:16px; font-weight:600; color:var(--ink);
    background:var(--bone); border:1px solid var(--line); border-radius:12px; padding:13px 42px 13px 14px; cursor:pointer}
  .select .chev{position:absolute; right:14px; top:50%; transform:translateY(-50%); pointer-events:none; color:var(--ink-soft)}

  /* facts */
  .facts{display:flex; flex-wrap:wrap; gap:7px; margin-top:10px}
  .chip{font-size:12.5px; font-weight:600; color:var(--ink-soft); background:var(--bone-2);
    border:1px solid var(--line); border-radius:999px; padding:5px 11px}
  .facts .risk{width:100%; margin-top:4px; font-size:13px; color:var(--muted)}
  .facts .risk b{color:var(--ink-soft); font-weight:600}

  /* fitness chips */
  .toggle{display:grid; grid-template-columns:repeat(3,1fr); gap:8px}
  .toggle button{font-family:inherit; font-size:14px; font-weight:600; color:var(--ink-soft);
    background:var(--bone); border:1px solid var(--line); border-radius:12px; padding:12px 8px; cursor:pointer; transition:.15s}
  .toggle button.on{background:var(--moss); color:#fff; border-color:var(--moss)}

  /* slider */
  .slider-row{display:flex; align-items:baseline; justify-content:space-between; margin-bottom:8px}
  .slider-row .val{font-size:16px; font-weight:700; color:var(--ink)}
  input[type=range]{width:100%; -webkit-appearance:none; height:6px; border-radius:999px; outline:none;
    background:linear-gradient(90deg,var(--moss) 0%,var(--moss) var(--pct,30%),var(--line) var(--pct,30%),var(--line) 100%)}
  input[type=range]::-webkit-slider-thumb{-webkit-appearance:none; width:20px; height:20px; border-radius:50%;
    background:var(--moss); border:3px solid #fff; box-shadow:0 2px 6px rgba(43,63,43,.35); cursor:pointer}

  /* button */
  .btn{width:100%; margin-top:20px; border:0; font-family:inherit; font-weight:700; font-size:15.5px; color:#fff;
    background:var(--moss); padding:15px; border-radius:13px; cursor:pointer; transition:.15s; box-shadow:0 8px 20px rgba(43,63,43,.22)}
  .btn:hover{background:var(--moss-deep)}

  /* verdict */
  .verdict{margin-top:16px; background:var(--white); border:1px solid var(--line); border-radius:18px;
    box-shadow:var(--shadow); overflow:hidden; display:none}
  .verdict.show{display:block; animation:rise .28s ease}
  @keyframes rise{from{opacity:0; transform:translateY(8px)}to{opacity:1; transform:none}}
  .verdict .bar{height:5px; background:var(--accent)}
  .verdict .body{padding:22px}
  .vhead{display:flex; align-items:center; gap:12px}
  .emblem{width:42px;height:42px;border-radius:12px;flex:none;display:flex;align-items:center;justify-content:center;
    background:color-mix(in srgb, var(--accent) 14%, #fff); color:var(--accent)}
  .kick{font-size:11px; font-weight:800; letter-spacing:.12em; text-transform:uppercase; color:var(--accent); margin:0}
  .vtitle{font-size:24px; font-weight:800; letter-spacing:-.01em; color:var(--ink); margin:2px 0 0}
  .why{margin:12px 0 0; font-size:15px; color:var(--ink-soft)}
  .computed{margin:16px 0 4px; padding-top:15px; border-top:1px solid var(--line); font-size:12px;
    font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--muted)}
  .inputs{display:flex; flex-wrap:wrap; gap:7px; margin-top:9px}
  .inputs .chip{background:#fff; border-color:var(--line)} .inputs .chip.grade{color:var(--moss); background:#eef2e8; border-color:#dbe6d0}
  .plan{list-style:none; padding:0; margin:16px 0 0}
  .plan li{display:flex; gap:10px; align-items:flex-start; padding:7px 0; font-size:14.5px; color:var(--ink)}
  .plan svg{flex:none; margin-top:2px; color:var(--accent)}
  .foot{display:flex; align-items:center; gap:10px; margin-top:16px; padding-top:15px; border-top:1px solid var(--line); flex-wrap:wrap}
  .badge{font-size:12px; font-weight:600; color:var(--moss); background:#eef2e8; border:1px solid #dfe6d6; border-radius:999px; padding:5px 11px; display:inline-flex; align-items:center; gap:6px}
  .disc{font-size:12.5px; color:var(--muted); margin:0}

  .note{font-size:12.5px;color:var(--muted);text-align:center;margin:14px 4px 0}
  .ask-lead{margin:0 0 14px;font-size:14.5px;color:var(--ink-soft)}
  .ask-box{display:flex;gap:9px}
  .ask-box input{flex:1;font-family:inherit;font-size:15px;color:var(--ink);background:var(--bone);border:1px solid var(--line);border-radius:12px;padding:13px 14px;outline:none}
  .ask-box .btn{width:auto;margin:0;white-space:nowrap;box-shadow:none;padding:13px 20px}
  .examples{display:flex;flex-direction:column;gap:8px}
  .examples button{text-align:left;font-family:inherit;font-size:14px;font-weight:500;color:var(--ink);background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 14px;cursor:pointer;transition:.15s}
  .examples button:hover{background:var(--bone);border-color:#cfd3c2}
  .runway{margin:16px 0 0}
  .runway .rtrack{position:relative;height:14px;border-radius:999px;overflow:hidden;display:flex}
  .runway .zone{height:100%}
  .runway .z1{background:#e7d3c9}.runway .z2{background:#efe2c4}.runway .z3{background:#dce7d0}
  .runway .you{position:absolute;top:-5px;width:4px;height:24px;border-radius:2px;background:var(--ink);transform:translateX(-50%);box-shadow:0 0 0 3px #fff}
  .runway .scale{position:relative;height:16px;margin-top:7px}
  .runway .mk{position:absolute;transform:translateX(-50%);font-size:11px;color:var(--muted);white-space:nowrap}
  .runway .rnote{margin:12px 0 0;font-size:13.5px;color:var(--ink);font-weight:600}
  .runway .rnote span{color:var(--muted);font-weight:500}
</style></head><body><div class="wrap" style="padding:0"><div class="verdict show" style="--accent:__ACCENT__">
  <div class="bar"></div>
  <div class="body">
    <div class="vhead">
      <div class="emblem">__ICON__</div>
      <div><p class="kick">Verdict</p><h2 class="vtitle">__HEAD__</h2></div>
    </div>
    <p class="why">__WHY__</p>
    <div class="runway" id="rw">
      <div class="rtrack"><div class="zone z1" id="z1"></div><div class="zone z2" id="z2"></div><div class="zone z3" id="z3"></div><div class="you" id="you"></div></div>
      <div class="scale" id="scale"></div>
      <p class="rnote" id="rnote"></p>
    </div>
    <p class="computed">Computed from</p>
    <div class="inputs">__INPUTS__</div>
    <ul class="plan">__PLAN__</ul>
    <div class="foot">
      <span class="badge"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6"><path d="M20 6L9 17l-5-5"/></svg> Computed, not guessed</span>
      <p class="disc">Approximate fitness assessment, not a medical opinion.</p>
    </div>
  </div>
</div></div><script>(function(){var S="__STATUS__",W=__WK__,FL=__FL__,CO=__CO__;var rw=document.getElementById('rw');if(!rw)return;if(S==="ready"||!CO){rw.style.display="none";return;}var end=Math.max(CO+6,W);function pct(x){return Math.max(0,Math.min(100,((x-1)/(end-1))*100));}document.getElementById('z1').style.width=pct(FL)+"%";document.getElementById('z2').style.width=(pct(CO)-pct(FL))+"%";document.getElementById('z3').style.width=(100-pct(CO))+"%";document.getElementById('you').style.left=pct(W)+"%";document.getElementById('scale').innerHTML='<span class="mk" style="left:'+pct(FL)+'%">'+FL+' wk</span><span class="mk" style="left:'+pct(CO)+'%">'+CO+' wk, comfortable</span>';var n=document.getElementById('rnote');n.innerHTML=W>=CO?'You have '+W+' weeks. <span>Comfortable is about '+CO+' weeks. You are set.</span>':(W<FL?'You have '+W+' weeks. <span>This trip needs about '+CO+' weeks. Give it more time.</span>':'You have '+W+' weeks. <span>Comfortable is about '+CO+' weeks. Add weeks if you can.</span>');})();</script><script>(function(){function rz(){var el=document.querySelector(".wrap");var h=Math.ceil(el?el.getBoundingClientRect().bottom:document.documentElement.scrollHeight)+12;window.parent.postMessage({isStreamlitMessage:true,type:"streamlit:setFrameHeight",height:h},"*");}window.addEventListener('load',rz);setInterval(rz,400);try{new ResizeObserver(rz).observe(document.body);}catch(e){}})();</script></body></html>'''

_VICON = {
 "ready": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M20 6L9 17l-5-5"/></svg>',
 "cond": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M12 19V5M5 12l7-7 7 7"/></svg>',
 "hard": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M3 20h18L12 4z"/></svg>',
 "toosoon": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="9"/><path d="M12 8v4l3 2"/></svg>',
}
_CHK = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6"><path d="M20 6L9 17l-5-5"/></svg>'

def _quick_check_html():
    """Embed the Python-compiled assessment lookup catalog."""
    return QC_HTML.replace("__CATALOG__", json.dumps(compile_catalog(), separators=(",", ":")).replace("<", "\\u003c"))


# ---------- Header ----------
_hero = _hero_b64()
components.html(HERO_TPL.replace("__HERO__", _hero), height=330)

tab_form, tab_chat = st.tabs(["Quick check", "Ask BeReady"])

# ---------- Tab 1: Quick check (embedded HTML design, works client-side) ----------
with tab_form:
    components.html(_quick_check_html(), height=920, scrolling=False)

# ---------- Tab 2: deterministic chat ----------
with tab_chat:
    AVATARS = {"user": "\U0001F97E", "assistant": "\U0001F3D4️"}
    STARTERS = [
        "Laugavegur in 6 weeks, I don't train",
        "Trolltunga in 4 weeks, I train sometimes",
        "Besseggen in 8 weeks, I train regularly",
    ]
    # Do not present a previous non-deterministic transcript as deterministic output.
    if st.session_state.get("_chat_mode_version") != 2:
        st.session_state.messages = []
        st.session_state["_chat_mode_version"] = 2
        st.session_state.pop("_chat_verdict", None)
        st.session_state.pop("_needs_fitness", None)
        st.session_state.pop("_fitness_query", None)
    if "messages" not in st.session_state:
        st.session_state.messages = []

    show_reasoning = st.session_state.get("show_reasoning", False)
    starter_q = None
    if not st.session_state.messages:
        with st.chat_message("assistant", avatar=AVATARS["assistant"]):
            st.markdown("Hi, I'm BeReady. Tell me a trail, how you train, and how many "
                        "weeks you have, and I'll give you an honest verdict.")
        st.caption("Try asking")
        for _i, _q in enumerate(STARTERS):
            if st.button(_q, key=f"st_{_i}", use_container_width=True):
                starter_q = _q

    for m in st.session_state.messages:
        box = st.chat_message(m["role"], avatar=AVATARS[m["role"]])
        v = m.get("verdict")
        if v:
            acc = {"ready": "#42583f", "cond": "#5f7d3f", "hard": "#b07d1f", "toosoon": "#3f7286"}.get(v["status"], "#6b7280")
            inputs_html = "".join(f'<span class="chip{" grade" if str(x).endswith("grade") else ""}">{x}</span>' for x in v.get("inputs", []))
            plan_html = "".join(f'<li>{_CHK}<span>{s}</span></li>' for s in v["plan"])
            card = (VERDICT_CARD
                    .replace("__ACCENT__", acc).replace("__ICON__", _VICON.get(v["status"], ""))
                    .replace("__HEAD__", v["head"]).replace("__WHY__", v.get("why", ""))
                    .replace("__INPUTS__", inputs_html).replace("__PLAN__", plan_html)
                    .replace("__STATUS__", v["status"]).replace("__WK__", str(v.get("weeks", 0)))
                    .replace("__FL__", str(v.get("floor", 0))).replace("__CO__", str(v.get("comfort", 0))))
            with box:
                components.html(card, height=540, scrolling=False)
            if show_reasoning:
                box.markdown(m["content"])
        else:
            box.markdown(m["content"])

    followup_q = None
    _msgs = st.session_state.messages
    if _msgs and _msgs[-1].get("needs_fitness"):
        base = _msgs[-1]["needs_fitness"]
        st.caption("Your training level:")
        fc1, fc2, fc3 = st.columns(3)
        if fc1.button("I don't train", key="fq1", use_container_width=True):
            followup_q = f"{base} I don't train."
        if fc2.button("Sometimes active", key="fq2", use_container_width=True):
            followup_q = f"{base} I sometimes train."
        if fc3.button("I train regularly", key="fq3", use_container_width=True):
            followup_q = f"{base} I train regularly."

    typed = st.chat_input("Ask about a trail in Iceland or Norway...")
    query = (typed.strip() if typed and typed.strip() else None) or starter_q or followup_q
    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        answer = readiness_from_text(query)
        msg = {"role": "assistant", "content": answer}
        verdict = st.session_state.pop("_chat_verdict", None)
        if verdict:
            msg["verdict"] = verdict
        needs_fit = st.session_state.pop("_needs_fitness", False)
        fit_query = st.session_state.pop("_fitness_query", None)
        if needs_fit and fit_query:
            msg["needs_fitness"] = fit_query
        st.session_state.messages.append(msg)
        st.rerun()

    with st.expander("How BeReady answers"):
        st.caption("Every answer is computed from the same fixed catalog and rules. "
                   "Showing the canonical assessment text does not change or delay the verdict.")
        st.toggle("Show the reasoning", key="show_reasoning")
