# app.py
import streamlit as st
import pandas as pd
from datetime import date
import requests
import re

st.set_page_config(page_title="Mood Checker", page_icon="🧠", layout="centered")

# ---------- App config ----------
MOODS = ["😄 Great", "🙂 Good", "😐 Okay", "🙁 Low", "😢 Bad"]
SCORE = {"😄 Great": 5, "🙂 Good": 4, "😐 Okay": 3, "🙁 Low": 2, "😢 Bad": 1}

# ---------- Nhost GraphQL helper ----------
def gql(query: str, variables=None):
    if "nhost" not in st.secrets:
        raise RuntimeError("Missing Nhost secrets (graphql_url, admin_secret).")
    url = st.secrets["nhost"]["graphql_url"]
    headers = {
        "Content-Type": "application/json",
        "x-hasura-admin-secret": st.secrets["nhost"]["admin_secret"],
    }
    r = requests.post(url, json={"query": query, "variables": variables or {}},
                      headers=headers, timeout=15)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]

# score = smallint!  <-- গুরুত্বপূর্ণ: টেবিলে smallint বলে এখানে smallint! দেয়া
UPSERT = """
mutation Upsert($team_member: String!, $pin: String!, $mood_label: String!, $score: smallint!, $comments: String) {
  insert_mood_logs_one(
    object: {team_member: $team_member, pin: $pin, mood_label: $mood_label, score: $score, comments: $comments},
    on_conflict: {constraint: mood_logs_pin_date_unique, update_columns: [team_member, mood_label, score, comments]}
  ) { id date team_member pin mood_label score comments created_at }
}
"""

# last N-days list: from তারিখ ভ্যারিয়েবলে পাঠাচ্ছি
LIST = """
query List($from: date!) {
  mood_logs(where: {date: {_gte: $from}}, order_by: {date: desc}) {
    date
    team_member
    pin
    mood_label
    score
    comments
  }
}
"""

def upsert_mood(team_member: str, pin: str, mood_label: str, comments: str):
    return gql(UPSERT, {
        "team_member": team_member.strip(),
        "pin": pin.strip(),
        "mood_label": mood_label,
        "score": int(SCORE[mood_label]),
        "comments": comments.strip() or None
    })

def load_last(days: int = 90) -> pd.DataFrame:
    from_dt = pd.Timestamp.today().normalize() - pd.Timedelta(days=days-1)
    res = gql(LIST, {"from": str(from_dt.date())})
    rows = res["mood_logs"]
    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    else:
        df = pd.DataFrame(columns=["date","team_member","pin","mood_label","score","comments"])
    return df

# ---------- UI ----------
st.title("🧠 Mood Checker")
st.caption("Data stored on Nhost (Postgres via GraphQL). Date is auto (today).")

with st.form("entry_form", clear_on_submit=False):
    st.text_input("Date (auto)", value=str(date.today()), disabled=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        team_member = st.text_input("Team Member", placeholder="e.g., Rahim Uddin", max_chars=80)
    with c2:
        pin = st.text_input("PIN", placeholder="e.g., 85 or 01234", max_chars=10)

    mood = st.radio("Mood", MOODS, horizontal=True)
    comments = st.text_area("Comments (optional)", placeholder="Anything notable today?")

    submitted = st.form_submit_button("Save / Update", type="primary")

if submitted:
    if not team_member.strip():
        st.error("Team Member required.")
    elif not pin.strip() or not re.fullmatch(r"[0-9A-Za-z\-]+", pin.strip()):
        st.error("Valid PIN required (digits/letters/-).")
    else:
        try:
            upsert_mood(team_member, pin, mood, comments)
            st.success("Saved ✅ (per PIN per day)")
            st.rerun()  # save সফল হলে সাথে সাথে তালিকা রিফ্রেশ
        except Exception as e:
            st.error(f"Save failed: {e}")

st.subheader("Timeline")
try:
    df = load_last(90)
    if df.empty:
        st.info("No entries yet.")
    else:
        show = df.copy()
        show["date"] = pd.to_datetime(show["date"]).dt.date
        show = show.rename(columns={
            "date":"Date", "team_member":"Team Member", "pin":"PIN",
            "mood_label":"Mood", "comments":"Comments"
        })
        st.dataframe(show[["Date","Team Member","PIN","Mood","Comments"]], use_container_width=True)

        st.subheader("Trend (last 30 days)")
        cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=29)
        recent = df[df["date"] >= cutoff]
        if not recent.empty:
            line = recent.set_index("date")["score"].resample("D").mean().interpolate()
            st.line_chart(line)
except Exception as e:
    st.error(f"Load failed: {e}")

st.markdown("<small>Not medical advice.</small>", unsafe_allow_html=True)
