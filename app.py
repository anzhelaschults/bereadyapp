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
            display: flex; flex-direction: column; justify-content: flex-end;
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


def _verdict(diff, fit, weeks, risk):
    gap = diff - fit
    if gap <= 0:
        return "ready", "You're ready. Your fitness matches this trail.", [
            "Keep your current activity level up until the start.",
            "Do one trial hike with a full pack to check your boots and gear.",
        ]
    if gap == 1:
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
        "meta": f"{rec['name']}: {rec['km']} km, {rec['days']} day(s), {DIFF_WORD[rec['diff']]} difficulty. "
                f"Your level: {FIT_WORD[fit]}. Time to the hike: {weeks} weeks.",
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
        return ("Almost there, I just need your training level. Do you train regularly, "
                "sometimes, or not at all? Then I can give you an honest verdict.")
    weeks = _weeks_from_text(q)
    status, head, plan = _verdict(rec["diff"], fit, weeks, rec["risk"])
    tail = f" You have {weeks} weeks." if weeks else ""
    plan_txt = "\n".join(f"- {s}" for s in plan)
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
            "Never invent trail facts. If a trail is unknown, say so honestly.",
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
            "If the trail is unknown, refuse honestly and ask for verified data. Do not guess.",
            "You are not a doctor. For injuries, pain, or illness, tell the person to see a doctor and give no verdict.",
            "Be warm, concise, and specific.",
        ],
        markdown=True,
        retries=3,
        delay_between_retries=8,
        exponential_backoff=True,
    )


# ---------- Header ----------
_hero = _hero_b64()
if _hero:
    st.markdown(
        '<div class="hero" style="background-image: '
        'linear-gradient(180deg, rgba(30,44,32,0.10) 0%, rgba(30,44,32,0.80) 100%), '
        f'url(\'data:image/jpeg;base64,{_hero}\');">'
        '<div class="hero-loc">&#9678;&nbsp; Th&oacute;rsm&ouml;rk, Iceland</div>'
        '<div class="hero-mark">BeReady</div>'
        '<div class="hero-tag">Can you handle this trail?</div>'
        "</div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown('<div class="brand-title">BeReady</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="brand-sub">An honest answer on whether you\'re ready for a trail, and what to do next.</div>',
        unsafe_allow_html=True,
    )

tab_form, tab_chat = st.tabs(["Quick check", "Ask BeReady"])

# ---------- Tab 1: deterministic form ----------
with tab_form:
    trail_choice = st.selectbox(
        "Trail",
        options=[t["name"] for t in TRAILS.values()],
    )
    st.caption("Five trails in Iceland and Norway for now, more coming.")

    with st.form("readiness"):
        fitness = st.radio("Fitness level", options=list(FIT_MAP.keys()), horizontal=True)
        weeks = st.slider("Weeks until the hike", min_value=1, max_value=24, value=8, format="%d weeks")
        submitted = st.form_submit_button("Check my readiness")

    if submitted:
        with st.spinner("Assessing your readiness..."):
            r = assess(trail_choice, fitness, weeks)
        css = {"ready": "verdict-ready", "cond": "verdict-cond",
               "hard": "verdict-hard", "toosoon": "verdict-toosoon"}[r["status"]]
        plan_html = "".join(f"<li>{s}</li>" for s in r["plan"])
        st.markdown(
            f'<div class="card {css}">'
            '<div class="verdict-kicker">Verdict</div>'
            f'<div class="verdict-head">{r["head"]}</div>'
            '<span class="badge">Carefully assessed, not a guess</span>'
            f'<div class="note">{r["meta"]}</div>'
            f'<div class="plan-title">Plan</div><ul class="plan-list">{plan_html}</ul></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="card"><span class="note">'
            "BeReady is not a doctor. This is an approximate assessment of physical readiness. "
            "If you have injuries, pain, or chronic conditions, talk to a doctor before hiking."
            "</span></div>",
            unsafe_allow_html=True,
            )

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

        # 3) Optional look behind the scenes. Same verdict, just shows the reasoning.
        with st.expander("How BeReady answers"):
            st.caption("Same verdict either way. Turn this on to see the reasoning behind "
                       "the answer, which takes a bit longer.")
            use_team = st.toggle("Show the reasoning")

        query = (typed.strip() if asked and typed.strip() else None) or example_q
        if query:
            st.session_state.messages.append({"role": "user", "content": query})
            spinner_text = "Reasoning through it..." if use_team else "Thinking..."
            with st.spinner(spinner_text):
                try:
                    runner = get_team() if use_team else get_agent()
                    resp = runner.run(query)
                    answer = getattr(resp, "content", None) or str(resp)
                except Exception as e:
                    answer = ("Something went wrong reaching the model. This is usually the free-tier "
                              f"limit, try again in a moment. ({type(e).__name__})")
            st.session_state.messages.append({"role": "assistant", "content": answer})

        # 4) Answer(s) render below the input, newest last.
        for m in st.session_state.messages:
            st.chat_message(m["role"], avatar=AVATARS[m["role"]]).markdown(m["content"])
