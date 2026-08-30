"""
BeReady, Streamlit interface (English, for public deployment and the Behance case study).
An honest answer on whether someone is ready for a specific trail, and what to do next.

Two modes:
- Check readiness: a deterministic form. Runs instantly, no API key, cannot hallucinate.
- Ask BeReady: a chat where a Gemini agent reads a free-form question and calls the same
  deterministic readiness tool. Needs a GOOGLE_API_KEY secret; the form works without one.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""

import os
import re
import base64
import pathlib
import streamlit as st
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
    .verdict-hard     { border-left: 6px solid #a1502f; }
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

# ---------- Trail database (Norway and Iceland) ----------
TRAILS = {
    "laugavegur":     {"name": "Laugavegur (Iceland)",     "km": 55, "days": 4, "diff": 3, "risk": "long hiking days four days in a row"},
    "fimmvorduhals":  {"name": "Fimmvorduhals (Iceland)",  "km": 25, "days": 1, "diff": 3, "risk": "a steep, long descent that stresses the knees"},
    "trolltunga":     {"name": "Trolltunga (Norway)",      "km": 28, "days": 1, "diff": 3, "risk": "a long day with big elevation gain"},
    "besseggen":      {"name": "Besseggen (Norway)",       "km": 14, "days": 1, "diff": 2, "risk": "a sharp, exposed ridge"},
    "preikestolen":   {"name": "Preikestolen (Norway)",    "km": 8,  "days": 1, "diff": 1, "risk": "a moderate climb on a popular trail"},
}
DIFF_WORD = {1: "low", 2: "moderate", 3: "high"}
FIT_MAP = {"I don't train": 1, "Sometimes active": 2, "I train regularly": 3}
FIT_WORD = {1: "low", 2: "moderate", 3: "high"}


def _plural(n, word):
    """'1 day', '4 days', '1 week', '8 weeks'."""
    return f"{n} {word}" + ("" if n == 1 else "s")


def _verdict(diff, fit, weeks, risk):
    gap = diff - fit
    if gap <= 0:
        return "ready", "You're ready. Your fitness matches this trail.", [
            "Keep your current activity level up until the start.",
            "Do one trial hike with a full pack to check your boots and gear.",
        ]
    if gap == 1:
        if weeks is not None and weeks < 6:
            wk = f"{weeks} week" + ("s" if weeks != 1 else "")
            return "cond", f"Almost ready, but {wk} is tight. This step up needs about 6 weeks of preparation.", [
                "Start now: three to four walks a week, 5-8 km, with a light pack (4-6 kg).",
                "Add one longer weekend hike each week, building toward a real day on the trail.",
                "If you can't add time, pick an easier trail this season and come back to this one.",
            ]
        return "cond", "Almost ready. You'll need about 6 weeks of preparation.", [
            "Weeks 1-2: three walks a week, 5-8 km at an easy pace.",
            "Weeks 3-4: add a light pack (4-6 kg) and one longer hike on the weekend.",
            "Weeks 5-6: a loaded hike close to a real day on the trail.",
        ]
    if weeks and weeks >= 8:
        return "hard", "Tough but doable with 8+ weeks of focused preparation.", [
            "Weeks 1-3: build a base, 3-4 walks a week, working up to 10 km.",
            "Weeks 4-6: pack 6-8 kg, one long hike every week.",
            "Weeks 7-8: two loaded hikes back to back to simulate the hardest day.",
            f"Keep the trail's risk in mind: {risk}.",
        ]
    return "toosoon", "Too soon this time. Consider an easier trail or more time.", [
        "Pick a lower-difficulty trail this season (for example Preikestolen).",
        "Start with regular walks and come back to this trail when you have 8+ weeks.",
    ]


def assess(trail_name, fitness_label, weeks):
    """Structured readiness for the form."""
    rec = next(t for t in TRAILS.values() if t["name"] == trail_name)
    fit = FIT_MAP[fitness_label]
    status, head, plan = _verdict(rec["diff"], fit, weeks, rec["risk"])
    return {
        "status": status, "head": head, "plan": plan, "risk": rec["risk"],
        "meta": f"{rec['name']}: {rec['km']} km, {_plural(rec['days'], 'day')}, {DIFF_WORD[rec['diff']]} difficulty. "
                f"Your level: {FIT_WORD[fit]}. Time to the hike: {_plural(weeks, 'week')}.",
    }


def _weeks_from_text(q: str):
    """Parse the timeframe from a free-form question, in weeks.
    Understands "8 weeks" as before, and now also months: "2 months" -> 8,
    "a month and a half" -> 6, "one month" -> 4. Returns None when no clear
    timeframe is given; the verdict logic treats that honestly, as before."""
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*week", q)
    if m:
        return int(float(m.group(1).replace(",", ".")))
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*month", q)
    if m:
        return round(float(m.group(1).replace(",", ".")) * 4)
    if "month and a half" in q:
        return 6
    if re.search(r"\b(?:a|one)\s+month\b", q):
        return 4
    if re.search(r"couple\s+of\s+months", q):
        return 8
    return None


def readiness_from_text(query: str) -> str:
    """Same rules as the form, but parses a free-form question. Used by the chat agent."""
    if not query or not query.strip():
        return "Tell me the trail, your training level, and how many weeks you have."
    q = query.lower()
    if any(w in q for w in ["injury", "injured", "pain", "hurt", "sick", "illness", "prescribe", "treatment", "medication"]):
        return ("I'm not a doctor and won't give medical advice. If you have an injury, pain, or a "
                "health condition, please talk to a doctor before hiking. I can still assess a trail "
                "against your fitness once you're cleared to hike.")
    rec = next((t for k, t in TRAILS.items() if k in q), None)
    if rec is None:
        return ("That trail isn't covered yet. For now BeReady prepares for trails in Iceland and "
                "Norway: Laugavegur, Fimmvorduhals, Trolltunga, Besseggen, and Preikestolen. "
                "More countries and trails are coming. Pick one of these for an honest verdict.")
    if any(w in q for w in ["don't train", "dont train", "no training", "never train", "sedentary", "beginner", "not fit", "unfit", "out of shape"]):
        fit = 1
    elif any(w in q for w in ["regularly", "every week", "often", "very fit", "athletic", "train a lot", "in good shape"]):
        fit = 3
    elif any(w in q for w in ["sometimes", "occasionally", "moderate", "gym", "a bit", "somewhat active", "now and then"]):
        fit = 2
    else:
        # Honest default: don't assume a fitness level. Ask, the same way we refuse unknown trails.
        # Stash the question so the chat can offer inline training-level buttons that keep the
        # trail and timeframe, no retyping.
        try:
            st.session_state["_needs_fitness"] = True
            st.session_state["_fitness_query"] = query
        except Exception:
            pass
        return ("Almost there, I just need your training level. Do you train regularly, "
                "sometimes, or not at all? Then I can give you an honest verdict.")
    weeks = _weeks_from_text(q)
    status, head, plan = _verdict(rec["diff"], fit, weeks, rec["risk"])
    tail = f" You have {_plural(weeks, 'week')}." if weeks else ""
    plan_txt = "\n".join(f"- {s}" for s in plan)
    # Stash the structured verdict so the chat can render the same card as the
    # Quick check tab. Best effort: if session state is unreachable (e.g. the
    # tool ran outside the script thread), the chat falls back to the text.
    try:
        st.session_state["_chat_verdict"] = {
            "status": status, "head": head, "plan": plan,
            "meta": f"{rec['name']}: {rec['km']} km, {_plural(rec['days'], 'day')}, "
                    f"{DIFF_WORD[rec['diff']]} difficulty. Your level: {FIT_WORD[fit]}. "
                    + (f"Time to the hike: {_plural(weeks, 'week')}." if weeks else "No clear timeframe given."),
        }
    except Exception:
        pass
    return (f"{rec['name']}, difficulty {DIFF_WORD[rec['diff']]}, your level {FIT_WORD[fit]}.{tail}\n\n"
            f"**{head}**\n\nPlan:\n{plan_txt}\n\n"
            f"*This is an approximate fitness assessment, not a medical opinion.*")


@st.cache_resource(show_spinner=False)
def get_agent():
    from agno.agent import Agent
    from agno.models.google import Gemini
    from agno.tools import tool

    @tool
    def readiness_score(query: str) -> str:
        """Give an honest readiness verdict for a specific trail. Needs the trail name, the
        person's training level, and how many weeks until the hike. Use this whenever the user
        asks whether they are ready for a trail.

        Args:
            query: Pass the user's question WORD FOR WORD, including their exact training level
                (for example "I don't train") and timeframe. Do not drop, upgrade, or paraphrase
                the training level, the verdict depends on it.

        Returns:
            A readiness verdict and plan, or an honest refusal if the trail is unknown.
        """
        return readiness_from_text(query)

    return Agent(
        model=Gemini(id="gemini-3.5-flash-lite"),
        tools=[readiness_score],
        instructions=[
            "You are BeReady, an honest hiking-readiness assistant. Answer in English.",
            "For any question about readiness for a trail, call readiness_score and base your answer on it.",
            "When you call readiness_score, pass the user's full question verbatim, including their "
            "exact training level and timeframe. Never drop, upgrade, or soften the training level.",
            "Report the verdict readiness_score returns exactly. Never make it more optimistic than the tool.",
            "You are not a doctor. For injuries or illness, tell the person to see a doctor.",
            "Never invent trail facts.",
            "If readiness_score refuses (an unknown trail, or a request for missing details), report that "
            "refusal and stop. Do not add your own readiness estimate, difficulty guess, or training "
            "timeline for an uncovered trail. Only point the user to the trails BeReady covers: "
            "Laugavegur, Fimmvorduhals, Trolltunga, Besseggen, Preikestolen.",
            "Be warm, concise, and specific.",
        ],
        markdown=True,
        retries=3,
        delay_between_retries=8,
        exponential_backoff=True,
    )


@st.cache_resource(show_spinner=False)
def get_team():
    """A real multi-agent team: a Researcher who gathers verified facts, an Analyst who
    interprets them, and a reasoning coordinator that enforces the honesty rules and writes
    the final answer. Every readiness verdict still comes from the deterministic readiness_score
    tool, so the team cannot hallucinate the number."""
    from agno.agent import Agent
    from agno.team import Team
    from agno.models.google import Gemini
    from agno.tools import tool

    @tool
    def readiness_score(query: str) -> str:
        """Give an honest readiness verdict for a specific trail. Needs the trail name, the
        person's training level, and how many weeks until the hike.

        Args:
            query: Pass the user's question WORD FOR WORD, including their exact training level
                (for example "I don't train") and timeframe. Do not drop, upgrade, or paraphrase
                the training level, the verdict depends on it.

        Returns:
            A readiness verdict and plan, or an honest refusal if the trail is unknown.
        """
        return readiness_from_text(query)

    model = Gemini(id="gemini-3.5-flash-lite")

    # The Researcher can check time-sensitive facts (season, closures) via web search.
    # Optional: if the tool is unavailable, the team still works with readiness_score alone.
    research_tools = [readiness_score]
    try:
        from agno.tools.duckduckgo import DuckDuckGoTools
        research_tools.append(DuckDuckGoTools())
    except Exception:
        pass

    researcher = Agent(
        name="Researcher",
        role="Gather verified facts",
        model=model,
        tools=research_tools,
        instructions=[
            "Collect only verified facts for the question.",
            "For readiness, call readiness_score and pass the user's full question verbatim, "
            "including their exact training level (for example 'I don't train') and timeframe. "
            "Never drop, upgrade, or paraphrase the training level.",
            "You may web-search only for time-sensitive facts, such as whether a trail is open this season.",
            "Never invent trail data. If the trail is unknown to readiness_score, report that honestly.",
        ],
    )
    analyst = Agent(
        name="Analyst",
        role="Interpret and frame",
        model=model,
        instructions=[
            "Turn the Researcher's facts into a clear, honest recommendation.",
            "Separate facts from interpretation. Do not invent numbers or trail data.",
            "For a trail readiness_score does not cover, do not estimate readiness or difficulty. Say it is not covered and stop.",
        ],
    )
    return Team(
        name="BeReady team",
        members=[researcher, analyst],
        model=model,
        tools=[readiness_score],
        instructions=[
            "You are BeReady, an honest hiking-readiness assistant. Answer in English.",
            "Delegate fact-finding to the Researcher and interpretation to the Analyst, then give one clear answer.",
            "Base every readiness verdict on readiness_score. Never compute or invent the verdict yourself.",
            "Open with the exact verdict wording that readiness_score returns (for example, You're ready, or Too soon), then add context. Do not soften, reword, or make the verdict more optimistic than the tool.",
            "If readiness_score refuses (an unknown trail, or missing details), report that refusal and "
            "stop. Do not add your own readiness estimate, difficulty guess, or training timeline for an "
            "uncovered trail. Only point the user to the trails BeReady covers.",
            "You are not a doctor. For injuries, pain, or illness, tell the person to see a doctor and give no verdict.",
            "Be warm, concise, and specific.",
        ],
        markdown=True,
        retries=3,
        delay_between_retries=8,
        exponential_backoff=True,
    )


HERO_TPL = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body{margin:0;background:transparent}
  :root{
    --bone:#f4f2e9; --bone-2:#efece0; --ink:#20301f; --ink-soft:#4a5a44;
    --moss:#42583f; --moss-deep:#2b3f2b; --moss-bright:#5f7d3f;
    --line:#e4e1d3; --white:#ffffff; --muted:#8a917f;
    --ready:#42583f; --cond:#b07d1f; --hard:#a1502f; --toosoon:#3f7286;
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
  .inputs .chip{background:#fff; border-color:var(--line)}
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
  </div><script>(function(){function rz(){var h=Math.ceil(document.documentElement.scrollHeight);window.parent.postMessage({isStreamlitMessage:true,type:"streamlit:setFrameHeight",height:h},"*");}window.addEventListener('load',rz);setInterval(rz,400);try{new ResizeObserver(rz).observe(document.body);}catch(e){}})();</script></body></html>'''

QC_HTML = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body{margin:0;background:transparent}
  :root{
    --bone:#f4f2e9; --bone-2:#efece0; --ink:#20301f; --ink-soft:#4a5a44;
    --moss:#42583f; --moss-deep:#2b3f2b; --moss-bright:#5f7d3f;
    --line:#e4e1d3; --white:#ffffff; --muted:#8a917f;
    --ready:#42583f; --cond:#b07d1f; --hard:#a1502f; --toosoon:#3f7286;
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
  .inputs .chip{background:#fff; border-color:var(--line)}
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
</style></head><body><div class="wrap" style="padding:0"><div class="card" id="panel">
    <div class="field">
      <p class="lbl">Trail</p>
      <div class="select">
        <select id="trail">
          <option>Laugavegur (Iceland)</option>
          <option>Fimmvorduhals (Iceland)</option>
          <option>Trolltunga (Norway)</option>
          <option>Besseggen (Norway)</option>
          <option>Preikestolen (Norway)</option>
        </select>
        <svg class="chev" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M6 9l6 6 6-6"/></svg>
      </div>
      <div class="facts" id="facts"></div>
    </div>

    <div class="field">
      <p class="lbl">Fitness level</p>
      <div class="toggle" id="fit">
        <button class="on" data-v="1">I don't train</button>
        <button data-v="2">Sometimes active</button>
        <button data-v="3">I train regularly</button>
      </div>
    </div>

    <div class="field">
      <div class="slider-row"><p class="lbl" style="margin:0">Weeks until the hike</p><span class="val" id="wval">8 weeks</span></div>
      <input type="range" id="weeks" min="1" max="24" value="8">
    </div>

    <button class="btn" id="go">Check my readiness</button>
  </div>

  <div class="verdict" id="verdict">
    <div class="bar"></div>
    <div class="body">
      <div class="vhead">
        <div class="emblem" id="emblem"></div>
        <div>
          <p class="kick" id="kick">Verdict</p>
          <h2 class="vtitle" id="vtitle"></h2>
        </div>
      </div>
      <p class="why" id="why"></p>
      <p class="computed">Computed from</p>
      <div class="inputs" id="vinputs"></div>
      <ul class="plan" id="plan"></ul>
      <div class="foot">
        <span class="badge">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6"><path d="M20 6L9 17l-5-5"/></svg>
          Computed, not guessed
        </span>
        <p class="disc">Approximate fitness assessment, not a medical opinion.</p>
      </div>
    </div>
  </div><p class="note">Five trails in Iceland and Norway for now, more coming.</p></div><script>
const TRAILS={
 "Laugavegur (Iceland)":{km:55,days:4,diff:3,risk:"long hiking days four days in a row"},
 "Fimmvorduhals (Iceland)":{km:25,days:1,diff:3,risk:"a steep, long descent that stresses the knees"},
 "Trolltunga (Norway)":{km:28,days:1,diff:3,risk:"a long day with big elevation gain"},
 "Besseggen (Norway)":{km:14,days:1,diff:2,risk:"a sharp, exposed ridge"},
 "Preikestolen (Norway)":{km:8,days:1,diff:1,risk:"a moderate climb on a popular trail"},
};
const DIFF={1:"Low",2:"Moderate",3:"High"};
const FITWORD={1:"not training",2:"sometimes active",3:"training regularly"};
let fit=1;

const ICON={
 ready:'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M20 6L9 17l-5-5"/></svg>',
 cond:'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M12 19V5M5 12l7-7 7 7"/></svg>',
 hard:'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M3 20h18L12 4z"/></svg>',
 toosoon:'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="9"/><path d="M12 8v4l3 2"/></svg>',
};
const ACC={ready:"var(--ready)",cond:"var(--cond)",hard:"var(--hard)",toosoon:"var(--toosoon)"};

function facts(){
  const t=TRAILS[trail.value];
  document.getElementById('facts').innerHTML=
    `<span class="chip">${t.km} km</span><span class="chip">${t.days} day${t.days>1?'s':''}</span>`+
    `<span class="chip">${DIFF[t.diff]} difficulty</span>`+
    `<div class="risk">Watch: <b>${t.risk}</b>.</div>`;
}
function verdict(diff,fit,weeks,risk){
  const gap=diff-fit;
  if(gap<=0) return {s:"ready",h:"You're ready",why:"Your fitness matches this trail's demands. Keep it up and do one trial hike with a full pack.",
    plan:["Hold your current activity level until the start.","One trial hike with a loaded pack to check boots and gear."]};
  if(gap===1){
    if(weeks<6) return {s:"cond",h:"Almost ready",why:`You are one step short, and ${weeks} week${weeks>1?'s':''} is tight. This step up wants about six weeks.`,
      plan:["Start now: three to four walks a week with a light pack (4-6 kg).","One longer weekend hike each week toward a real day on the trail.","If you can't add time, pick an easier trail this season."]};
    return {s:"cond",h:"Almost ready",why:"You are one step short on fitness. About six weeks of focused prep closes the gap.",
      plan:["Weeks 1-2: three walks a week, 5-8 km easy.","Weeks 3-4: add a light pack (4-6 kg) and one longer weekend hike.","Weeks 5-6: a loaded hike close to a real day on the trail."]};
  }
  if(weeks>=8) return {s:"hard",h:"Tough but doable",why:`Your training level is the limiting factor, not the trail. Eight focused weeks can close it — mind ${risk}.`,
    plan:["Weeks 1-3: build a base, 3-4 walks a week, up to 10 km.","Weeks 4-6: pack 6-8 kg, one long hike every week.","Weeks 7-8: two loaded hikes back to back to simulate the hardest day."]};
  return {s:"toosoon",h:"Too soon this time",why:"Not enough base or time for this trail yet. Give it a lower-difficulty season first.",
    plan:["Pick a lower-difficulty trail this season (for example Preikestolen).","Start regular walks and return here when you have 8+ weeks."]};
}
function run(){
  const t=TRAILS[trail.value], weeks=+document.getElementById('weeks').value;
  const r=verdict(t.diff,fit,weeks,t.risk);
  const acc=ACC[r.s]; const v=document.getElementById('verdict');
  v.style.setProperty('--accent',acc);
  document.getElementById('emblem').innerHTML=ICON[r.s];
  document.getElementById('vtitle').textContent=r.h;
  document.getElementById('why').textContent=r.why;
  document.getElementById('vinputs').innerHTML=
    `<span class="chip">${trail.value}</span><span class="chip">${FITWORD[fit]}</span><span class="chip">${weeks} week${weeks>1?'s':''}</span>`;
  document.getElementById('plan').innerHTML=r.plan.map(p=>
    `<li><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6"><path d="M20 6L9 17l-5-5"/></svg><span>${p}</span></li>`).join('');
  v.classList.add('show');
  v.scrollIntoView({behavior:'smooth',block:'nearest'});
}
const trail=document.getElementById('trail');
const weeks=document.getElementById('weeks');
function setPct(){weeks.style.setProperty('--pct',((weeks.value-1)/23*100)+'%');document.getElementById('wval').textContent=weeks.value+' week'+(weeks.value>1?'s':'');}
trail.onchange=facts;
weeks.oninput=setPct;
document.querySelectorAll('#fit button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('#fit button').forEach(x=>x.classList.remove('on'));b.classList.add('on');fit=+b.dataset.v;});
document.getElementById('go').onclick=run;
facts();setPct();
</script><script>(function(){function rz(){var h=Math.ceil(document.documentElement.scrollHeight);window.parent.postMessage({isStreamlitMessage:true,type:"streamlit:setFrameHeight",height:h},"*");}window.addEventListener('load',rz);setInterval(rz,400);try{new ResizeObserver(rz).observe(document.body);}catch(e){}})();</script></body></html>'''

# ---------- Header ----------
_hero = _hero_b64()
components.html(HERO_TPL.replace("__HERO__", _hero), height=330)

tab_form, tab_chat = st.tabs(["Quick check", "Ask BeReady"])

# ---------- Tab 1: Quick check (embedded HTML design, works client-side) ----------
with tab_form:
    components.html(QC_HTML, height=640, scrolling=False)

# ---------- Tab 2: chat ----------
with tab_chat:
    api_key = None
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY")
    except Exception:
        api_key = None
    api_key = api_key or os.environ.get("GOOGLE_API_KEY")

    st.caption("Prefer your own words? Ask about a trail in Iceland or Norway.")

    if not api_key:
        st.info(
            "This needs a Google Gemini API key. Add GOOGLE_API_KEY in the app settings "
            "(Manage app, Secrets) to turn it on. The readiness form works without a key."
        )
    else:
        os.environ["GOOGLE_API_KEY"] = api_key
        AVATARS = {"user": "🥾", "assistant": "🏔️"}
        EXAMPLES = [
            "Am I ready for Laugavegur in 6 weeks? I don't train.",
            "Fimmvorduhals in 6 weeks, sometimes active.",
            "Trolltunga in 4 weeks, sometimes active.",
            "Besseggen in 8 weeks, I train regularly.",
            "Preikestolen in 3 weeks, I don't train.",
        ]
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # 1) Input first: a prominent ask box at the top (one-question tool, not a chat).
        with st.form("ask", clear_on_submit=True):
            typed = st.text_input(
                "Your question", placeholder="Am I ready for Besseggen in 8 weeks?",
                label_visibility="collapsed",
            )
            asked = st.form_submit_button("Ask BeReady")

        # 2) Example starters double as the coverage list: the five trails we cover.
        st.caption("The trails we cover, tap to ask:")
        example_q = None
        for q in EXAMPLES:
            if st.button(q, key=f"ex_{q}", use_container_width=True):
                example_q = q

        # If the last answer asked for a training level, offer it inline so the user can
        # continue without scrolling up or retyping the trail and weeks.
        followup_q = None
        _msgs = st.session_state.get("messages", [])
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

        # 3) Optional look behind the scenes. Same verdict, just shows the reasoning.
        with st.expander("How BeReady answers"):
            st.caption("Same verdict either way. Turn this on to see the reasoning behind "
                       "the answer, which takes a bit longer.")
            use_team = st.toggle("Show the reasoning")

        query = (typed.strip() if asked and typed.strip() else None) or example_q or followup_q
        if query:
            st.session_state.messages.append({"role": "user", "content": query})
            st.session_state.pop("_chat_verdict", None)
            st.session_state.pop("_needs_fitness", None)
            st.session_state.pop("_fitness_query", None)
            spinner_text = "Reasoning through it..." if use_team else "Thinking..."
            with st.spinner(spinner_text):
                try:
                    runner = get_team() if use_team else get_agent()
                    resp = runner.run(query)
                    answer = getattr(resp, "content", None) or str(resp)
                except Exception as e:
                    answer = ("Something went wrong reaching the model. This is usually the free-tier "
                              f"limit, try again in a moment. ({type(e).__name__})")
            msg = {"role": "assistant", "content": answer}
            verdict = st.session_state.pop("_chat_verdict", None)
            if verdict:
                # The tool computed a verdict this turn: show it as the same card
                # the Quick check tab uses. In reasoning mode the model's own
                # write-up stays visible below the card.
                msg["verdict"] = verdict
                msg["show_text"] = bool(use_team)
            needs_fit = st.session_state.pop("_needs_fitness", False)
            fit_query = st.session_state.pop("_fitness_query", None)
            if needs_fit and fit_query:
                msg["needs_fitness"] = fit_query
            st.session_state.messages.append(msg)

        # 4) Answer(s) render below the input, newest last.
        _VERDICT_CSS = {"ready": "verdict-ready", "cond": "verdict-cond",
                        "hard": "verdict-hard", "toosoon": "verdict-toosoon"}
        for m in st.session_state.messages:
            box = st.chat_message(m["role"], avatar=AVATARS[m["role"]])
            v = m.get("verdict")
            if v:
                plan_html = "".join(f"<li>{s}</li>" for s in v["plan"])
                box.markdown(
                    f'<div class="card {_VERDICT_CSS.get(v["status"], "verdict-unknown")}">'
                    '<div class="verdict-kicker">Verdict</div>'
                    f'<div class="verdict-head">{v["head"]}</div>'
                    '<span class="badge">Carefully assessed, not a guess</span>'
                    f'<div class="note">{v["meta"]}</div>'
                    f'<div class="plan-title">Plan</div><ul class="plan-list">{plan_html}</ul>'
                    '<div class="note" style="margin-top:0.6rem">This is an approximate fitness '
                    "assessment, not a medical opinion.</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )
                if m.get("show_text"):
                    box.markdown(m["content"])
            else:
                box.markdown(m["content"])
