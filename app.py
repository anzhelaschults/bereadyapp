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
import streamlit as st

st.set_page_config(page_title="BeReady", page_icon="🏔️", layout="centered")

# ---------- Brand (Icelandic highlands): moss, lichen, warm bone, Inter ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #f8f7f0; }
    .brand-title { font-size: 2.4rem; font-weight: 700; color: #2b412e; margin-bottom: 0.1rem; }
    .brand-sub { font-size: 1.05rem; color: #5F7D3F; margin-bottom: 1.2rem; }
    .card { background: #ffffff; border: 1px solid #e3e2d6; border-radius: 14px;
            padding: 1.1rem 1.3rem; margin-top: 0.8rem; }
    .verdict-ready   { border-left: 6px solid #425844; }
    .verdict-cond    { border-left: 6px solid #b98a2e; }
    .verdict-hard    { border-left: 6px solid #a1502f; }
    .verdict-unknown { border-left: 6px solid #6b7280; }
    .verdict-head { font-size: 1.25rem; font-weight: 600; color: #2b412e; margin-bottom: 0.3rem; }
    .plan-title { font-weight: 600; color: #425844; margin-top: 0.4rem; }
    .note { color: #6b7280; font-size: 0.9rem; }
    .stButton>button { background: #425844; color: #f8f7f0; border: 0; border-radius: 10px;
                       padding: 0.55rem 1.3rem; font-weight: 600; }
    .stButton>button:hover { background: #2b412e; color: #ffffff; }
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
        return ("I don't have verified data for that trail, so I won't guess. Try one of Laugavegur, "
                "Fimmvorduhals, Trolltunga, Besseggen, or Preikestolen, or give me its length and elevation gain.")
    if any(w in q for w in ["don't train", "dont train", "no training", "never train", "sedentary", "beginner"]):
        fit = 1
    elif any(w in q for w in ["regularly", "every week", "often", "fit", "athletic", "train a lot"]):
        fit = 3
    else:
        fit = 2
    m = re.search(r"(\d+)\s*week", q)
    weeks = int(m.group(1)) if m else None
    status, head, plan = _verdict(rec["diff"], fit, weeks, rec["risk"])
    tail = f" You have {weeks} weeks." if weeks else ""
    plan_txt = " ".join(f"({i+1}) {s}" for i, s in enumerate(plan))
    return (f"{rec['name']}, difficulty {DIFF_WORD[rec['diff']]}, your level {FIT_WORD[fit]}.{tail} "
            f"{head} Plan: {plan_txt} This is an approximate fitness assessment, not a medical opinion.")


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
            query: The user's question, including trail name, training level, and weeks.

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
            "You are not a doctor. For injuries or illness, tell the person to see a doctor.",
            "Never invent trail facts. If a trail is unknown, say so honestly.",
            "Be warm, concise, and specific.",
        ],
        markdown=True,
        retries=3,
        delay_between_retries=8,
        exponential_backoff=True,
    )


# ---------- Header ----------
st.markdown('<div class="brand-title">BeReady</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="brand-sub">An honest answer on whether you\'re ready for a trail, and what to do next.</div>',
    unsafe_allow_html=True,
)

tab_form, tab_chat = st.tabs(["Check readiness", "Ask BeReady"])

# ---------- Tab 1: deterministic form ----------
with tab_form:
    with st.form("readiness"):
        trail_choice = st.selectbox(
            "Trail",
            options=[t["name"] for t in TRAILS.values()] + ["My trail isn't on the list"],
        )
        fitness = st.radio("Fitness level", options=list(FIT_MAP.keys()), horizontal=True)
        weeks = st.slider("Weeks until the hike", min_value=1, max_value=24, value=8)
        submitted = st.form_submit_button("Check my readiness")

    if submitted:
        if trail_choice == "My trail isn't on the list":
            st.markdown(
                '<div class="card verdict-unknown">'
                '<div class="verdict-head">I don\'t know this trail yet</div>'
                "I don't have verified data for it, so I won't guess at a verdict. "
                "Pick a trail from the list, or send me its length and elevation gain and I'll add it."
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            with st.spinner("Assessing your readiness..."):
                r = assess(trail_choice, fitness, weeks)
            css = {"ready": "verdict-ready", "cond": "verdict-cond",
                   "hard": "verdict-hard", "toosoon": "verdict-hard"}[r["status"]]
            plan_html = "".join(f"<li>{s}</li>" for s in r["plan"])
            st.markdown(
                f'<div class="card {css}"><div class="verdict-head">{r["head"]}</div>'
                f'<div class="note">{r["meta"]}</div>'
                f'<div class="plan-title">Plan</div><ul>{plan_html}</ul></div>',
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

    if not api_key:
        st.info(
            "Chat needs a Google Gemini API key. Add GOOGLE_API_KEY in the app settings "
            "(Manage app, Secrets) to turn it on. The readiness form works without a key."
        )
    else:
        os.environ["GOOGLE_API_KEY"] = api_key
        st.caption("Ask in your own words, for example: Am I ready for Laugavegur in 6 weeks if I don't train?")
        if "messages" not in st.session_state:
            st.session_state.messages = []
        for m in st.session_state.messages:
            st.chat_message(m["role"]).markdown(m["content"])

        if prompt := st.chat_input("Ask BeReady about a trail..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        agent = get_agent()
                        resp = agent.run(prompt)
                        answer = getattr(resp, "content", None) or str(resp)
                    except Exception as e:
                        answer = ("Something went wrong reaching the model. This is usually the free-tier "
                                  f"limit, try again in a moment. ({type(e).__name__})")
                    st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
