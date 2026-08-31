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
# grade = official technical grade (Norwegian national scale / park descriptions).
# diff  = effective difficulty the verdict uses: grade plus a bump for multi-day
#         treks, where days back to back are the real load, not the terrain.
TRAILS = {
    "laugavegur":     {"name": "Laugavegur (Iceland)",     "km": 55, "days": 4, "grade": 2, "diff": 3, "risk": "long hiking days four days in a row"},
    "fimmvorduhals":  {"name": "Fimmvorduhals (Iceland)",  "km": 25, "days": 1, "grade": 3, "diff": 3, "risk": "a steep, long descent that stresses the knees"},
    "trolltunga":     {"name": "Trolltunga (Norway)",      "km": 28, "days": 1, "grade": 4, "diff": 4, "risk": "a long day with big elevation gain"},
    "romsdalseggen":  {"name": "Romsdalseggen (Norway)",   "km": 11, "days": 1, "grade": 4, "diff": 4, "risk": "a narrow, exposed ridge with chain scrambles"},
    "besseggen":      {"name": "Besseggen (Norway)",       "km": 14, "days": 1, "grade": 3, "diff": 3, "risk": "a sharp, exposed ridge"},
    "kjeragbolten":   {"name": "Kjeragbolten (Norway)",    "km": 12, "days": 1, "grade": 3, "diff": 3, "risk": "chain-assisted scrambles and big drops"},
    "preikestolen":   {"name": "Preikestolen (Norway)",    "km": 8,  "days": 1, "grade": 3, "diff": 3, "risk": "two steep sections and exposed drops near the top"},
    "dalsnuten":      {"name": "Dalsnuten (Norway)",       "km": 3,  "days": 1, "grade": 1, "diff": 1, "risk": "a short steep push to the summit on an otherwise gentle trail"},
    "gaustatoppen":   {"name": "Gaustatoppen (Norway)",    "km": 9,  "days": 1, "grade": 2, "diff": 2, "risk": "a rocky final stretch after a steady climb"},
}
GRADE_WORD = {1: "Easy", 2: "Moderate", 3: "Demanding", 4: "Very demanding"}
DIFF_WORD = {1: "low", 2: "moderate", 3: "high"}
FIT_MAP = {"I don't train": 1, "Sometimes active": 2, "I train regularly": 3}
FIT_WORD = {1: "low", 2: "moderate", 3: "high"}
# Preparation time (weeks) that a fitness gap needs: (too-soon floor, comfortable runway).
THRESH = {1: (3, 6), 2: (6, 12), 3: (12, 20)}
GAPWORD = {1: "one step short", 2: "two steps short", 3: "a big jump up"}
TRAIN_NOTE = "These weeks only count if you actually train them."


def _plan_for(weeks, multiday):
    """Training plan scaled to the runway: tight, medium, or long build."""
    w = weeks or 0
    if w < 8:
        p = ["Start now. Three to four sessions a week: easy aerobic walks plus one strength day (step-ups, lunges, core).",
             "A loaded long hike every weekend, adding about 10 percent time and vertical each week.",
             "Train the downhill early so descents don't wreck your legs, then taper the last five days."]
        if multiday:
            p.insert(2, "Add one back-to-back weekend to rehearse consecutive days.")
        return p
    if w < 20:
        p = ["Weeks 1 to 4: build an aerobic base, easy volume, strength twice a week.",
             "Middle weeks: progressive loaded long hikes, more vertical, hill repeats.",
             "Final weeks: rehearse the real terrain and pack weight, then taper the last week."]
        if multiday:
            p.insert(2, "Add back-to-back weekends to prepare for consecutive days.")
        return p
    p = ["Months 1 to 3: build the aerobic engine and general strength, steady and consistent, conditioning tendons for the load.",
         "Middle months: heavier leg strength and rising weekly vertical on loaded hikes.",
         "Final 12 to 16 weeks: the trail-specific block, long days and terrain practice, then taper. Deload every third or fourth week."]
    if multiday:
        p.insert(2, "Rehearse back-to-back days in the final block.")
    return p


def _plural(n, word):
    """'1 day', '4 days', '1 week', '8 weeks'."""
    return f"{n} {word}" + ("" if n == 1 else "s")


def _verdict(rec, fit, weeks):
    """Verdict from the fitness gap and the preparation runway (weeks)."""
    gap = rec["diff"] - fit
    multiday = rec["diff"] > rec["grade"]
    if gap <= 0:
        p = ["Hold your current activity level until the start.",
             "One trial hike with a loaded pack to check boots and gear."]
        if multiday:
            p.append("Rehearse a back-to-back weekend so consecutive days are not a surprise.")
        return "ready", "You're ready", p
    tt, to = THRESH[gap]
    if weeks is None or weeks < tt:
        return "toosoon", "Too soon this time", [
            "Choose a lower-difficulty trail this season (for example Gaustatoppen or Preikestolen).",
            "Start regular walks and strength now, and come back when you have more time.",
        ]
    if weeks < to:
        return "hard", "Tough but doable", _plan_for(weeks, multiday)
    return "cond", "Enough time to prepare", _plan_for(weeks, multiday)

FIT_FRIENDLY = {1: "not training", 2: "sometimes active", 3: "training regularly"}


def _why(rec, status, fit, weeks):
    gw = GRADE_WORD[rec["grade"]].lower()
    multiday = rec["diff"] > rec["grade"]
    gap = rec["diff"] - fit
    wl = _plural(weeks, "week") if weeks else "no timeframe"
    if status == "ready":
        return f"Your fitness matches this {gw} trail. Keep it up and do one trial hike with a full pack."
    tt, to = THRESH.get(gap, (0, 0))
    if multiday:
        midbody = (f"Technically {rec['name']} is a {gw} trail, but {_plural(rec['days'], 'day')} "
                   "back to back are the real load for your level.")
    else:
        midbody = f"You are {GAPWORD.get(gap, 'short')} for a {gw} trail ({rec['risk']})."
    if status == "toosoon":
        return (f"{midbody} From your level that takes around {to} weeks of training, well past the "
                f"{wl} you have. Pick an easier trail this season, or give it more runway.")
    if status == "hard":
        return (f"{midbody} {wl} clears the {tt}-week floor but sits under the {to} weeks a comfortable "
                f"build needs, so it is doable only if you train consistently and do not miss sessions. {TRAIN_NOTE}")
    return f"{midbody} {wl} is enough runway to arrive genuinely prepared if you start now. {TRAIN_NOTE}"

def assess(trail_name, fitness_label, weeks):
    """Structured readiness (kept for reference and tests)."""
    rec = next(t for t in TRAILS.values() if t["name"] == trail_name)
    fit = FIT_MAP[fitness_label]
    status, head, plan = _verdict(rec, fit, weeks)
    inputs = [rec["name"], f"{GRADE_WORD[rec['grade']]} grade"]
    if rec["diff"] > rec["grade"]:
        inputs.append(_plural(rec["days"], "day"))
    inputs += [FIT_FRIENDLY[fit], (_plural(weeks, "week") if weeks else "no timeframe")]
    return {"status": status, "head": head, "plan": plan,
            "why": _why(rec, status, fit, weeks), "inputs": inputs}


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
    if weeks is None:
        return "How many weeks until the hike? The verdict depends on how much time you have to train for it."
    status, head, plan = _verdict(rec, fit, weeks)
    tail = f" You have {_plural(weeks, 'week')}." if weeks else ""
    plan_txt = "\n".join(f"- {s}" for s in plan)
    # Stash the structured verdict so the chat renders the same card as Quick check.
    try:
        _inputs = [rec["name"], f"{GRADE_WORD[rec['grade']]} grade"]
        if rec["diff"] > rec["grade"]:
            _inputs.append(_plural(rec["days"], "day"))
        _inputs += [FIT_FRIENDLY[fit], (_plural(weeks, "week") if weeks else "no timeframe")]
        st.session_state["_chat_verdict"] = {
            "status": status, "head": head, "plan": plan,
            "why": _why(rec, status, fit, weeks), "inputs": _inputs,
        }
    except Exception:
        pass
    return (f"{rec['name']}, {GRADE_WORD[rec['grade']]} grade, your level {FIT_WORD[fit]}.{tail}\n\n"
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
            "If a message is not a readiness question (no trail, or unclear), do not re-introduce "
            "yourself or list the trails. Reply with exactly this one line and nothing else: "
            "I work from three things: the trail, your training level, and the weeks you have. Tell me those.",
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
            "If a message is not a readiness question (no trail, or unclear), do not re-introduce "
            "yourself or list the trails. Reply with exactly this one line and nothing else: "
            "I work from three things: the trail, your training level, and the weeks you have. Tell me those.",
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
    --ready:#42583f; --cond:#5f7d3f; --hard:#a1502f; --toosoon:#3f7286;
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
  </div><script>(function(){function rz(){var h=Math.ceil(document.documentElement.scrollHeight);window.parent.postMessage({isStreamlitMessage:true,type:"streamlit:setFrameHeight",height:h},"*");}window.addEventListener('load',rz);setInterval(rz,400);try{new ResizeObserver(rz).observe(document.body);}catch(e){}})();</script></body></html>'''

QC_HTML = r'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root{
    --bone:#f4f2e9; --bone-2:#efece0; --ink:#20301f; --ink-soft:#455540;
    --moss:#42583f; --moss-deep:#2b3f2b; --moss-bright:#4f6a34;
    --line:#e4e1d3; --white:#fff; --muted:#6b7360;
    --ready:#42583f; --cond:#5f7d3f; --hard:#a1502f; --toosoon:#356274;
    --shadow:0 18px 44px rgba(33,48,31,.10), 0 4px 14px rgba(33,48,31,.06);
  }
  *{box-sizing:border-box} html,body{margin:0}
  body{font-family:'Inter',system-ui,sans-serif; background:transparent; color:var(--ink);
    -webkit-font-smoothing:antialiased; line-height:1.5}
  .wrap{max-width:600px; margin:0 auto; padding:0}
  .card{background:var(--white); border:1px solid var(--line); border-radius:18px; box-shadow:var(--shadow); padding:22px}
  .field{margin-bottom:18px} .field:last-child{margin-bottom:0}
  .lbl{font-size:11.5px;font-weight:700;letter-spacing:.10em;text-transform:uppercase;color:var(--moss-bright);margin:0 0 8px}
  .select{position:relative}
  select{width:100%; appearance:none; font-family:inherit; font-size:16px; font-weight:600; color:var(--ink);
    background:var(--bone); border:1px solid var(--line); border-radius:12px; padding:13px 42px 13px 14px; cursor:pointer}
  .select .chev{position:absolute; right:14px; top:50%; transform:translateY(-50%); pointer-events:none; color:var(--ink-soft)}
  .facts{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px}
  .chip{font-size:12.5px;font-weight:600;color:var(--ink-soft);background:var(--bone-2);border:1px solid var(--line);border-radius:999px;padding:5px 11px}
  .facts .risk{width:100%;margin-top:4px;font-size:13px;color:var(--muted)}
  .facts .risk b{color:var(--ink-soft);font-weight:600}
  .toggle{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
  .toggle button{font-family:inherit;font-size:13.5px;font-weight:600;color:var(--ink-soft);background:var(--bone);
    border:1px solid var(--line);border-radius:12px;padding:12px 6px;cursor:pointer;transition:.15s}
  .toggle button.on{background:var(--moss);color:#fff;border-color:var(--moss)}
  .toggle button:focus-visible,select:focus-visible,input[type=range]:focus-visible{outline:2px solid var(--moss-bright);outline-offset:2px}
  .slider-row{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:8px}
  .slider-row .val{font-size:16px;font-weight:700;color:var(--ink)}
  input[type=range]{width:100%;-webkit-appearance:none;height:6px;border-radius:999px;outline:none;
    background:linear-gradient(90deg,var(--moss) 0%,var(--moss) var(--pct,30%),var(--line) var(--pct,30%),var(--line) 100%)}
  input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:26px;height:26px;border-radius:50%;
    background:var(--moss);border:3px solid #fff;box-shadow:0 2px 6px rgba(43,63,43,.35);cursor:pointer}
  input[type=range]::-moz-range-thumb{width:26px;height:26px;border-radius:50%;background:var(--moss);border:3px solid #fff;cursor:pointer}
  .track{position:relative}
  .ticks{position:relative;height:24px;margin-top:5px}
  .ticks .t{position:absolute;top:0;display:flex;flex-direction:column;align-items:center;font-size:11px;color:var(--muted);transform:translateX(-50%);white-space:nowrap}
  .ticks .t.edgeL{transform:none;align-items:flex-start}
  .ticks .t.edgeR{transform:translateX(-100%);align-items:flex-end}
  .ticks .t i{width:1px;height:6px;background:var(--line);margin-bottom:3px}
  .ticks .t.brk{color:var(--moss-bright);font-weight:600}
  .ticks .t.brk i{height:11px;width:2px;background:var(--moss-bright)}
  /* verdict */
  .verdict{margin-top:16px;background:var(--white);border:1px solid var(--line);border-radius:18px;box-shadow:var(--shadow);overflow:hidden}
  .verdict .bar{height:5px;background:var(--accent)}
  .verdict .body{padding:22px}
  .vhead{display:flex;align-items:center;gap:12px}
  .emblem{width:42px;height:42px;border-radius:12px;flex:none;display:flex;align-items:center;justify-content:center;
    background:color-mix(in srgb,var(--accent) 14%,#fff);color:var(--accent);transition:background .3s}
  .kick{font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);margin:0}
  .vtitle{font-size:24px;font-weight:800;letter-spacing:-.01em;color:var(--ink);margin:2px 0 0}
  .why{margin:12px 0 0;font-size:15px;color:var(--ink-soft)}
  .computed{margin:16px 0 4px;padding-top:15px;border-top:1px solid var(--line);font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
  .inputs{display:flex;flex-wrap:wrap;gap:7px;margin-top:9px}
  .inputs .chip{background:#fff;border-color:var(--line)}
  .inputs .chip.grade{color:var(--moss);background:#eef2e8;border-color:#dbe6d0}
  .plan{list-style:none;padding:0;margin:16px 0 0}
  .plan li{display:flex;gap:10px;align-items:flex-start;padding:7px 0;font-size:14.5px;color:var(--ink)}
  .plan svg{flex:none;margin-top:2px;color:var(--accent)}
  .trainnote{margin:12px 0 0;font-size:12.5px;color:var(--muted);font-style:italic}
  .foot{display:flex;align-items:center;gap:10px;margin-top:16px;padding-top:15px;border-top:1px solid var(--line);flex-wrap:wrap}
  .badge{font-size:12px;font-weight:600;color:var(--moss);background:#eef2e8;border:1px solid #dfe6d6;border-radius:999px;padding:5px 11px;display:inline-flex;align-items:center;gap:6px}
  .disc{font-size:12.5px;color:var(--muted);margin:0}
  @keyframes flash{0%{box-shadow:0 0 0 0 color-mix(in srgb,var(--accent) 45%,transparent)}100%{box-shadow:0 0 0 8px transparent}}
  .verdict.flash{animation:flash .5s ease-out}
  @media (prefers-reduced-motion: reduce){.verdict.flash{animation:none}}
</style></head><body><div class="wrap">
  <div class="card">
    <div class="field">
      <p class="lbl" id="lbl-trail">Trail</p>
      <div class="select">
        <select id="trail" aria-labelledby="lbl-trail"></select>
        <svg class="chev" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M6 9l6 6 6-6"/></svg>
      </div>
      <div class="facts" id="facts"></div>
    </div>
    <div class="field">
      <p class="lbl" id="lbl-fit">Fitness level</p>
      <div class="toggle" id="fit" role="radiogroup" aria-labelledby="lbl-fit">
        <button role="radio" aria-checked="true" class="on" data-v="1">I don't train</button>
        <button role="radio" aria-checked="false" data-v="2">Sometimes active</button>
        <button role="radio" aria-checked="false" data-v="3">I train regularly</button>
      </div>
    </div>
    <div class="field">
      <div class="slider-row"><p class="lbl" style="margin:0" id="lbl-weeks">Time until the hike</p><span class="val" id="wval">8 weeks</span></div>
      <div class="track">
        <input type="range" id="weeks" min="0" max="30" value="7" aria-labelledby="lbl-weeks" aria-valuetext="8 weeks">
        <div class="ticks" id="ticks"></div>
      </div>
    </div>
  </div>

  <div class="verdict" id="verdict" aria-live="polite">
    <div class="bar"></div>
    <div class="body">
      <div class="vhead"><div class="emblem" id="emblem"></div>
        <div><p class="kick">Verdict</p><h2 class="vtitle" id="vtitle"></h2></div></div>
      <p class="why" id="why"></p>
      <p class="computed">Computed from</p>
      <div class="inputs" id="vinputs"></div>
      <ul class="plan" id="plan"></ul>
      <p class="trainnote" id="trainnote"></p>
      <div class="foot">
        <span class="badge"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6"><path d="M20 6L9 17l-5-5"/></svg> Computed, not guessed</span>
        <p class="disc">Fitness readiness only, not a medical opinion.</p>
      </div>
    </div>
  </div>
</div>
<script>
const TRAILS={
 "Dalsnuten (Norway)":{km:3,days:1,grade:1,diff:1,risk:"a short steep push to the summit on an otherwise gentle trail"},
 "Gaustatoppen (Norway)":{km:9,days:1,grade:2,diff:2,risk:"a rocky final stretch after a steady climb"},
 "Laugavegur (Iceland)":{km:55,days:4,grade:2,diff:3,risk:"long hiking days four days in a row"},
 "Preikestolen (Norway)":{km:8,days:1,grade:3,diff:3,risk:"two steep sections and exposed drops near the top"},
 "Besseggen (Norway)":{km:14,days:1,grade:3,diff:3,risk:"a sharp, exposed ridge"},
 "Fimmvorduhals (Iceland)":{km:25,days:1,grade:3,diff:3,risk:"a steep, long descent that stresses the knees"},
 "Kjeragbolten (Norway)":{km:12,days:1,grade:3,diff:3,risk:"chain-assisted scrambles and big drops"},
 "Trolltunga (Norway)":{km:28,days:1,grade:4,diff:4,risk:"a long day with big elevation gain"},
 "Romsdalseggen (Norway)":{km:11,days:1,grade:4,diff:4,risk:"a narrow, exposed ridge with chain scrambles"},
};
const GRADE={1:"Easy",2:"Moderate",3:"Demanding",4:"Very demanding"};
const FITWORD={1:"not training",2:"sometimes active",3:"training regularly"};
const THRESH={1:[3,6],2:[6,12],3:[12,20]};   // [too-soon floor, on-track] weeks, per gap
const GAPWORD={1:"one step short",2:"two steps short",3:"a big jump up"};
// One-week steps where the verdict can change (1-24), then coarse 4-week steps to a year.
const WEEKS=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,28,32,36,40,44,48,52];
const curWeeks=()=>WEEKS[+weeks.value];
let fit=1;
const ICON={
 ready:'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M20 6L9 17l-5-5"/></svg>',
 cond:'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M12 19V5M5 12l7-7 7 7"/></svg>',
 hard:'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M3 20h18L12 4z"/></svg>',
 toosoon:'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="9"/><path d="M12 8v4l3 2"/></svg>',
};
const ACC={ready:"var(--ready)",cond:"var(--cond)",hard:"var(--hard)",toosoon:"var(--toosoon)"};
const trail=document.getElementById('trail'), weeks=document.getElementById('weeks');
Object.keys(TRAILS).forEach(n=>{const o=document.createElement('option');o.textContent=n;trail.appendChild(o);});

// friendly durations: small numbers in weeks, larger in months
function dur(w){ return w<=8 ? (w+' week'+(w>1?'s':'')) : ('about '+Math.round(w/4.345)+' months'); }
function fmtVal(w){ return w===1 ? '1 week' : (w+' weeks'); }

function planTight(multiday){ const p=[
  "Start now. Three to four sessions a week: easy aerobic walks plus one strength day (step-ups, lunges, core).",
  "A loaded long hike every weekend, adding about 10 percent time and vertical each week.",
  "Train the downhill early so descents don't wreck your legs, then taper the last five days."];
  if(multiday) p.splice(2,0,"Add one back-to-back weekend to rehearse consecutive days."); return p; }
function planMedium(multiday){ const p=[
  "Weeks 1 to 4: build an aerobic base, easy volume, strength twice a week.",
  "Middle weeks: progressive loaded long hikes, more vertical, hill repeats.",
  "Final weeks: rehearse the real terrain and pack weight, then taper the last week."];
  if(multiday) p.splice(2,0,"Add back-to-back weekends to prepare for consecutive days."); return p; }
function planLong(multiday){ const p=[
  "Months 1 to 3: build the aerobic engine and general strength, steady and consistent, conditioning tendons for the load.",
  "Middle months: heavier leg strength and rising weekly vertical on loaded hikes.",
  "Final 12 to 16 weeks: the trail-specific block, long days and terrain practice, then taper. Deload every third or fourth week."];
  if(multiday) p.splice(2,0,"Rehearse back-to-back days in the final block."); return p; }
function planFor(w,multiday){ return w<8?planTight(multiday):(w<20?planMedium(multiday):planLong(multiday)); }

function verdict(rec,fit,weeks){
  const gap=rec.diff-fit, gw=GRADE[rec.grade].toLowerCase(), multiday=rec.diff>rec.grade;
  const wl=fmtVal(weeks);
  if(gap<=0){
    const p=["Hold your current activity level until the start.","One trial hike with a loaded pack to check boots and gear."];
    if(multiday) p.push("Rehearse a back-to-back weekend so consecutive days are not a surprise.");
    return {s:"ready",h:"You're ready",why:`Your fitness matches this ${gw} trail. Keep it up and do one trial hike with a full pack.`,plan:p,note:""};
  }
  const [tt,to]=THRESH[gap];
  const midbody = multiday
    ? `Technically ${rec.name} is a ${gw} trail, but ${rec.days} days back to back are the real load for your level.`
    : `You are ${GAPWORD[gap]} for a ${gw} trail (${rec.risk}).`;
  const note = "These weeks only count if you actually train them.";
  if(weeks<tt){
    return {s:"toosoon",h:"Too soon this time",
      why:`${midbody} From your level that takes around ${to} weeks of training, well past the ${wl} you have. Pick an easier trail this season, or give it more runway.`,
      plan:["Choose a lower-difficulty trail this season (for example Gaustatoppen or Preikestolen).","Start regular walks and strength now, and come back when you have more time."],note:""};
  }
  if(weeks<to){
    return {s:"hard",h:"Tough but doable",
      why:`${midbody} ${wl} clears the ${tt}-week floor but sits under the ${to} weeks a comfortable build needs, so it is doable only if you train consistently and do not miss sessions.`,
      plan:planFor(weeks,multiday),note};
  }
  return {s:"cond",h:"Enough time to prepare",
    why:`${midbody} ${wl} is enough runway to arrive genuinely prepared, so start now and train it.`,
    plan:planFor(weeks,multiday),note};
}

function facts(){
  const t=TRAILS[trail.value];
  document.getElementById('facts').innerHTML=
    `<span class="chip">${t.km} km</span><span class="chip">${t.days} day${t.days>1?'s':''}</span>`+
    `<span class="chip">${GRADE[t.grade]}</span>`+
    `<div class="risk">Watch: <b>${t.risk}</b>.</div>`;
}
let lastKey="";
function run(animate){
  const t={...TRAILS[trail.value],name:trail.value}, w=curWeeks();
  const r=verdict(t,fit,w);
  const v=document.getElementById('verdict');
  v.style.setProperty('--accent',ACC[r.s]);
  document.getElementById('emblem').innerHTML=ICON[r.s];
  document.getElementById('vtitle').textContent=r.h;
  document.getElementById('why').textContent=r.why;
  const dchip=(t.diff>t.grade)?`<span class="chip">${t.days} days</span>`:"";
  document.getElementById('vinputs').innerHTML=
    `<span class="chip">${trail.value}</span><span class="chip grade">${GRADE[t.grade]} grade</span>${dchip}<span class="chip">${FITWORD[fit]}</span><span class="chip">${fmtVal(w)}</span>`;
  document.getElementById('plan').innerHTML=r.plan.map(p=>
    `<li><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6"><path d="M20 6L9 17l-5-5"/></svg><span>${p}</span></li>`).join('');
  document.getElementById('trainnote').textContent=r.note||"";
  const key=r.s+r.h;
  if(animate && key!==lastKey){v.classList.remove('flash');void v.offsetWidth;v.classList.add('flash');}
  lastKey=key;
}
function setPct(){weeks.style.setProperty('--pct',(weeks.value/30*100)+'%');
  const txt=fmtVal(curWeeks());
  document.getElementById('wval').textContent=txt; weeks.setAttribute('aria-valuetext',txt);}
trail.onchange=()=>{facts();run(true);};
weeks.oninput=()=>{setPct();run(true);};
document.querySelectorAll('#fit button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('#fit button').forEach(x=>{x.classList.remove('on');x.setAttribute('aria-checked','false');});
  b.classList.add('on');b.setAttribute('aria-checked','true');fit=+b.dataset.v;run(true);});
// chunk the track: anchor ticks with an emphasized density break at 24 weeks
document.getElementById('ticks').innerHTML=
  [[0,"1 wk","edgeL"],[7,"8 wks",""],[23,"24 wks","brk"],[30,"1 year","edgeR"]]
  .map(function(a){return '<span class="t '+a[2]+'" style="left:'+(a[0]/30*100)+'%"><i></i>'+a[1]+'</span>';}).join('');
facts();setPct();run(false);
</script><script>(function(){function rz(){var h=Math.ceil(document.documentElement.scrollHeight);window.parent.postMessage({isStreamlitMessage:true,type:"streamlit:setFrameHeight",height:h},"*");}window.addEventListener("load",rz);setInterval(rz,400);try{new ResizeObserver(rz).observe(document.body);}catch(e){}})();</script></body></html>
'''

VERDICT_CARD = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body{margin:0;background:transparent}.verdict{margin-top:0 !important}
  :root{
    --bone:#f4f2e9; --bone-2:#efece0; --ink:#20301f; --ink-soft:#4a5a44;
    --moss:#42583f; --moss-deep:#2b3f2b; --moss-bright:#5f7d3f;
    --line:#e4e1d3; --white:#ffffff; --muted:#8a917f;
    --ready:#42583f; --cond:#5f7d3f; --hard:#a1502f; --toosoon:#3f7286;
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
</style></head><body><div class="wrap" style="padding:0"><div class="verdict show" style="--accent:__ACCENT__">
  <div class="bar"></div>
  <div class="body">
    <div class="vhead">
      <div class="emblem">__ICON__</div>
      <div><p class="kick">Verdict</p><h2 class="vtitle">__HEAD__</h2></div>
    </div>
    <p class="why">__WHY__</p>
    <p class="computed">Computed from</p>
    <div class="inputs">__INPUTS__</div>
    <ul class="plan">__PLAN__</ul>
    <div class="foot">
      <span class="badge"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6"><path d="M20 6L9 17l-5-5"/></svg> Computed, not guessed</span>
      <p class="disc">Approximate fitness assessment, not a medical opinion.</p>
    </div>
  </div>
</div></div><script>(function(){function rz(){var h=Math.ceil(document.documentElement.scrollHeight);window.parent.postMessage({isStreamlitMessage:true,type:"streamlit:setFrameHeight",height:h},"*");}window.addEventListener('load',rz);setInterval(rz,400);try{new ResizeObserver(rz).observe(document.body);}catch(e){}})();</script></body></html>'''

_VICON = {
 "ready": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M20 6L9 17l-5-5"/></svg>',
 "cond": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M12 19V5M5 12l7-7 7 7"/></svg>',
 "hard": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M3 20h18L12 4z"/></svg>',
 "toosoon": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="9"/><path d="M12 8v4l3 2"/></svg>',
}
_CHK = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6"><path d="M20 6L9 17l-5-5"/></svg>'

# ---------- Header ----------
_hero = _hero_b64()
components.html(HERO_TPL.replace("__HERO__", _hero), height=330)

tab_form, tab_chat = st.tabs(["Quick check", "Ask BeReady"])

# ---------- Tab 1: Quick check (embedded HTML design, works client-side) ----------
with tab_form:
    components.html(QC_HTML, height=820, scrolling=False)

# ---------- Tab 2: chat ----------
with tab_chat:
    api_key = None
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY")
    except Exception:
        api_key = None
    api_key = api_key or os.environ.get("GOOGLE_API_KEY")


    if not api_key:
        st.info(
            "This needs a Google Gemini API key. Add GOOGLE_API_KEY in the app settings "
            "(Manage app, Secrets) to turn it on. The readiness form works without a key."
        )
    else:
        os.environ["GOOGLE_API_KEY"] = api_key
        AVATARS = {"user": "\U0001F97E", "assistant": "\U0001F3D4️"}
        STARTERS = [
            "Laugavegur in 6 weeks, I don't train",
            "Trolltunga in 4 weeks, I train sometimes",
            "Besseggen in 8 weeks, I train regularly",
        ]
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Reasoning mode is a subtle toggle at the bottom; read its saved value here.
        use_team = st.session_state.get("show_reasoning", False)

        # Empty state: a friendly opener plus a few conversation starters.
        starter_q = None
        if not st.session_state.messages:
            with st.chat_message("assistant", avatar=AVATARS["assistant"]):
                st.markdown("Hi, I'm BeReady. Tell me a trail, how you train, and how many "
                            "weeks you have, and I'll give you an honest verdict.")
            st.caption("Try asking")
            for _i, _q in enumerate(STARTERS):
                if st.button(_q, key=f"st_{_i}", use_container_width=True):
                    starter_q = _q

        # The conversation so far, newest last.
        for m in st.session_state.messages:
            box = st.chat_message(m["role"], avatar=AVATARS[m["role"]])
            v = m.get("verdict")
            if v:
                acc = {"ready": "#42583f", "cond": "#5f7d3f", "hard": "#a1502f", "toosoon": "#3f7286"}.get(v["status"], "#6b7280")
                inputs_html = "".join(f'<span class="chip{" grade" if str(x).endswith("grade") else ""}">{x}</span>' for x in v.get("inputs", []))
                plan_html = "".join(f'<li>{_CHK}<span>{s}</span></li>' for s in v["plan"])
                card = (VERDICT_CARD
                        .replace("__ACCENT__", acc).replace("__ICON__", _VICON.get(v["status"], ""))
                        .replace("__HEAD__", v["head"]).replace("__WHY__", v.get("why", ""))
                        .replace("__INPUTS__", inputs_html).replace("__PLAN__", plan_html))
                with box:
                    components.html(card, height=470, scrolling=False)
                if m.get("show_text"):
                    box.markdown(m["content"])
            else:
                box.markdown(m["content"])

        # If the last answer asked for a training level, offer it inline in the thread.
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

        # Pinned input at the bottom, like a real chat.
        typed = st.chat_input("Ask about a trail in Iceland or Norway...")
        query = (typed.strip() if typed and typed.strip() else None) or starter_q or followup_q
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
                msg["verdict"] = verdict
                msg["show_text"] = bool(use_team)
            needs_fit = st.session_state.pop("_needs_fitness", False)
            fit_query = st.session_state.pop("_fitness_query", None)
            if needs_fit and fit_query:
                msg["needs_fitness"] = fit_query
            st.session_state.messages.append(msg)
            st.rerun()

        # A subtle "how it works" toggle, kept out of the way at the bottom.
        with st.expander("How BeReady answers"):
            st.caption("Same verdict either way. Turn this on to see the reasoning behind "
                       "the answer, which takes a bit longer.")
            st.toggle("Show the reasoning", key="show_reasoning")
