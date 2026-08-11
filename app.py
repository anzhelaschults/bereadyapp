"""
BeReady, Streamlit interface (English, for public deployment and the Behance case study).
An honest answer on whether someone is ready for a specific trail, and what to do next.

The readiness logic is deterministic (the same rules as the readiness_score tool),
so the interface runs instantly and needs no API key or quota.

Run locally:
    pip install streamlit
    streamlit run app.py
"""

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
    .brand-sub { font-size: 1.05rem; color: #5F7D3F; margin-bottom: 1.4rem; }
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
    "Laugavegur (Iceland)":      {"km": 55, "days": 4, "diff": 3, "risk": "long hiking days four days in a row"},
    "Fimmvorduhals (Iceland)":   {"km": 25, "days": 1, "diff": 3, "risk": "a steep, long descent that stresses the knees"},
    "Trolltunga (Norway)":       {"km": 28, "days": 1, "diff": 3, "risk": "a long day with big elevation gain"},
    "Besseggen (Norway)":        {"km": 14, "days": 1, "diff": 2, "risk": "a sharp, exposed ridge"},
    "Preikestolen (Norway)":     {"km": 8,  "days": 1, "diff": 1, "risk": "a moderate climb on a popular trail"},
}
DIFF_WORD = {1: "low", 2: "moderate", 3: "high"}
FIT_MAP = {"I don't train": 1, "Sometimes active": 2, "I train regularly": 3}
FIT_WORD = {1: "low", 2: "moderate", 3: "high"}


def assess(trail_name, fitness_label, weeks):
    """Returns a structured readiness assessment. Same rules as readiness_score."""
    t = TRAILS[trail_name]
    diff = t["diff"]
    fit = FIT_MAP[fitness_label]
    gap = diff - fit

    if gap <= 0:
        status = "ready"
        head = "You're ready. Your fitness matches this trail."
        plan = [
            "Keep your current activity level up until the start.",
            "Do one trial hike with a full pack to check your boots and gear.",
        ]
    elif gap == 1:
        status = "cond"
        head = "Almost ready. You'll need about 6 weeks of preparation."
        plan = [
            "Weeks 1-2: three walks a week, 5-8 km at an easy pace.",
            "Weeks 3-4: add a light pack (4-6 kg) and one longer hike on the weekend.",
            "Weeks 5-6: a loaded hike close to a real day on the trail.",
        ]
    else:
        if weeks >= 8:
            status = "hard"
            head = "Tough but doable with 8+ weeks of focused preparation."
            plan = [
                "Weeks 1-3: build a base, 3-4 walks a week, working up to 10 km.",
                "Weeks 4-6: pack 6-8 kg, one long hike every week.",
                "Weeks 7-8: two loaded hikes back to back to simulate the hardest day.",
                f"Keep the trail's risk in mind: {t['risk']}.",
            ]
        else:
            status = "toosoon"
            head = "Too soon this time. Consider an easier trail or more time."
            plan = [
                "Pick a lower-difficulty trail this season (for example Preikestolen).",
                "Start with regular walks and come back to this trail when you have 8+ weeks.",
            ]

    return {
        "status": status,
        "head": head,
        "plan": plan,
        "meta": f"{trail_name}: {t['km']} km, {t['days']} day(s), {DIFF_WORD[diff]} difficulty. "
                f"Your level: {FIT_WORD[fit]}. Time to the hike: {weeks} weeks.",
        "risk": t["risk"],
    }


# ---------- Header ----------
st.markdown('<div class="brand-title">BeReady</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="brand-sub">An honest answer on whether you\'re ready for a trail, and what to do next.</div>',
    unsafe_allow_html=True,
)

# ---------- Form ----------
with st.form("readiness"):
    trail_choice = st.selectbox(
        "Trail",
        options=list(TRAILS.keys()) + ["My trail isn't on the list"],
    )
    fitness = st.radio(
        "Fitness level",
        options=list(FIT_MAP.keys()),
        horizontal=True,
    )
    weeks = st.slider("Weeks until the hike", min_value=1, max_value=24, value=8)
    submitted = st.form_submit_button("Check my readiness")

# ---------- Result ----------
if submitted:
    if trail_choice == "My trail isn't on the list":
        st.markdown(
            '<div class="card verdict-unknown">'
            '<div class="verdict-head">I don\'t know this trail yet</div>'
            "I don't have verified data for it, so I won't guess at a verdict. "
            "Pick a trail from the list, or send me its length and elevation gain and I'll add it to the database."
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        with st.spinner("Assessing your readiness..."):
            r = assess(trail_choice, fitness, weeks)

        css = {"ready": "verdict-ready", "cond": "verdict-cond",
               "hard": "verdict-hard", "toosoon": "verdict-hard"}[r["status"]]

        plan_html = "".join(f"<li>{step}</li>" for step in r["plan"])
        st.markdown(
            f'<div class="card {css}">'
            f'<div class="verdict-head">{r["head"]}</div>'
            f'<div class="note">{r["meta"]}</div>'
            f'<div class="plan-title">Plan</div>'
            f"<ul>{plan_html}</ul>"
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="card"><span class="note">'
            "BeReady is not a doctor. This is an approximate assessment of physical readiness. "
            "If you have injuries, pain, or chronic conditions, talk to a doctor before hiking."
            "</span></div>",
            unsafe_allow_html=True,
        )
