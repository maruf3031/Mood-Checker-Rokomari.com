import streamlit as st
import datetime

# অ্যাপের শিরোনাম
st.title("😊 Mood Checker App")

# আজকের তারিখ দেখানো
st.write(f"আজকের তারিখ: {datetime.date.today().strftime('%d %B %Y')}")

# ইউজারের নাম ইনপুট
name = st.text_input("তোমার নাম লিখো:")

# মুড বাছাই করা
mood = st.selectbox(
    "আজ তোমার মুড কেমন?",
    ["😃 খুশি", "😐 স্বাভাবিক", "😢 মন খারাপ", "😡 রাগান্বিত", "😴 ক্লান্ত"]
)

# ফিডব্যাক বাটন
if st.button("Submit"):
    if name.strip():
        st.success(f"হ্যালো {name}! তুমি আজ {mood} মুডে আছো।")
        if "খুশি" in mood:
            st.balloons()
        elif "মন খারাপ" in mood:
            st.write("💡 টিপস: প্রিয় কোনো গান শুনে ফেলো!")
        elif "রাগান্বিত" in mood:
            st.write("💡 টিপস: গভীর শ্বাস নাও, ধীরে ধীরে ছাড়ো।")
        elif "ক্লান্ত" in mood:
            st.write("💡 টিপস: একটু বিশ্রাম নাও বা চা/কফি খাও।")
    else:git --version

        st.error("অনুগ্রহ করে তোমার নাম লিখো।")
