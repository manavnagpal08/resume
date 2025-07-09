import streamlit as st
from login import login_section
from email_sender import send_email_to_candidate
import pdfplumber
import pandas as pd
import re
import os
import plotly.express as px
import zipfile
import io
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# --- Page Setup ---
st.set_page_config(page_title="Resume Screener Pro", layout="wide")

# --- Dark Mode Toggle ---
dark_mode = st.sidebar.toggle("🌙 Dark Mode")
if dark_mode:
    st.markdown("""
    <style>
    body { background: #121212 !important; color: #ffffff !important; }
    .block-container { background-color: #1e1e1e !important; }
    </style>
    """, unsafe_allow_html=True)

# --- Enhanced UI Styling ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    transition: all 0.3s ease-in-out;
}
body {
    background: linear-gradient(135deg, #f3f4f6, #f0fdf4);
    padding: 0;
    margin: 0;
}
.main .block-container {
    padding: 2rem;
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.95);
    box-shadow: 0 12px 36px rgba(0,0,0,0.12);
    animation: fadeInZoom 0.9s ease-in-out;
    border: 1px solid #e0e0e0;
}
@keyframes fadeInZoom {
    from { opacity: 0; transform: scale(0.98); }
    to { opacity: 1; transform: scale(1); }
}
button[kind="primary"] {
    background: linear-gradient(90deg, #00b894, #00cec9);
    color: white;
    border-radius: 10px;
    font-weight: 600;
    box-shadow: 0 3px 8px rgba(0,0,0,0.15);
}
[data-testid="stMetric"] > div {
    background: #ffffffdd;
    padding: 1.2rem;
    border-radius: 14px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.07);
    margin-bottom: 1rem;
    transition: transform 0.2s ease;
}
[data-testid="stMetric"] > div:hover {
    transform: translateY(-4px);
}
</style>
""", unsafe_allow_html=True)

# --- Utility Functions ---
def extract_text_from_pdf(uploaded_file):
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            return ''.join(page.extract_text() or '' for page in pdf.pages)
    except Exception as e:
        return f"[ERROR] {str(e)}"

def extract_years_of_experience(text):
    text = text.lower()
    patterns = [
        r'(\d{1,2})\s*\+?\s*(years?|yrs?|year)',              # e.g. 4 years, 4+ years, 4 yr
        r'experience\s*[-:]?\s*(\d{1,2})\s*(years?|yrs?|year)'  # e.g. Experience – 4 years
    ]
    years = []
    for pattern in patterns:
        found = re.findall(pattern, text)
        for match in found:
            if isinstance(match, tuple):
                years.append(int(match[0]))
            elif match.isdigit():
                years.append(int(match))
    return max(years) if years else 0



def smart_score(resume_text, jd_text, years_exp):
    resume_text = resume_text.lower()
    jd_text = jd_text.lower()
    jd_keywords = set(re.findall(r'\b\w+\b', jd_text))
    resume_words = set(re.findall(r'\b\w+\b', resume_text))
    important_skills = [word for word in jd_keywords if word in resume_words]
    core_skills = ['python', 'java', 'sql', 'html', 'css', 'javascript', 'react', 'machine', 'learning']
    weight = sum([3 if word in core_skills else 1 for word in important_skills])
    total_possible = sum([3 if word in core_skills else 1 for word in jd_keywords])
    score = (weight / total_possible) * 100 if total_possible else 0
    boost = min(years_exp, 10)
    score += boost
    score = round(min(score, 100), 2)
    missing = [word for word in core_skills if word in jd_keywords and word not in resume_words]
    feedback = "✅ Excellent match!" if score >= 80 else (
        f"⚠️ Missing important skills: {', '.join(missing)}" if missing else "⚠️ Needs more relevant content."
    )
    return score, ", ".join(important_skills), feedback

def generate_summary(text, experience, skills):
    return f"{experience}+ years experience in {skills}."[:160]

def get_tag(score, exp):
    if score > 90 and exp >= 3:
        return "🔥 Top Talent"
    elif score >= 75:
        return "✅ Good Fit"
    return "⚠️ Needs Review"

def plot_wordcloud(all_keywords):
    text = ' '.join(all_keywords)
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)

# --- Main App ---
st.image("logo.png", width=200)
st.title("🧠 Resume Screener Pro")
if not login_section():
    st.stop()

job_roles = {
    "Upload my own": None,
    "Data Scientist": "data_scientist.txt",
    "Web Developer": "web_developer.txt",
    "Software Engineer": "software_engineer.txt"
}
jd_option = st.selectbox("📌 Select Job Role or Upload Your Own JD", list(job_roles.keys()))
jd_text = ""
if jd_option == "Upload my own":
    jd_file = st.file_uploader("Upload Job Description (TXT)", type="txt")
    if jd_file:
        jd_text = jd_file.read().decode("utf-8")
else:
    jd_path = job_roles[jd_option]
    if jd_path and os.path.exists(jd_path):
        with open(jd_path, "r", encoding="utf-8") as f:
            jd_text = f.read()

resume_files = st.file_uploader("📥 Upload Resumes (PDFs)", type="pdf", accept_multiple_files=True)
cutoff = st.slider("📈 Score Cutoff for Email", 0, 100, 80)
min_experience = st.slider("💼 Minimum Years of Experience Required", 0, 15, 2)

if jd_text and resume_files:
    results = []
    resume_text_map = {}
    summary_map = {}
    with st.spinner("🔍 Screening resumes..."):
        for file in resume_files:
            resume_text = extract_text_from_pdf(file)
            if resume_text.startswith("[ERROR]"):
                st.error(f"❌ Could not read {file.name}. Skipping.")
                continue
            experience = extract_years_of_experience(resume_text)
            score, matched_keywords, feedback = smart_score(resume_text, jd_text, experience)
            summary = generate_summary(resume_text, experience, matched_keywords)
            if experience < min_experience:
                feedback = f"❌ Less than {min_experience} years experience."
            results.append({
                "File Name": file.name,
                "Score (%)": score,
                "Years Experience": experience,
                "Matched Keywords": matched_keywords,
                "Feedback": feedback,
                "Summary": summary
            })
            resume_text_map[file.name] = resume_text
            summary_map[file.name] = summary
            if score >= cutoff and experience >= min_experience:
                send_email_to_candidate(file.name, score, feedback)

    if results:
        df = pd.DataFrame(results).sort_values(by="Score (%)", ascending=False)
        avg_score = df['Score (%)'].mean()
        avg_exp = df['Years Experience'].mean()
        shortlisted = df[(df['Score (%)'] >= cutoff) & (df['Years Experience'] >= min_experience)]
        st.markdown("### 📌 Smart Insights")
        col1, col2, col3 = st.columns(3)
        col1.metric("📊 Avg. Score", f"{avg_score:.2f}%")
        col2.metric("🧓 Avg. Experience", f"{avg_exp:.1f} yrs")
        col3.metric("✅ Shortlisted", f"{len(shortlisted)} candidates")

        df['Tag'] = df.apply(lambda row: get_tag(row['Score (%)'], row['Years Experience']), axis=1)

        all_keywords = []
        for kw in df['Matched Keywords']:
            all_keywords.extend(kw.split(', '))
        st.markdown("### ☁️ Skill Cloud from Matches")
        plot_wordcloud(all_keywords)

        st.markdown("### 🔎 Filter by Tag")
        selected_tags = st.multiselect("Filter candidates by tag:", df['Tag'].unique().tolist(), default=df['Tag'].unique().tolist())
        filtered_df = df[df['Tag'].isin(selected_tags)]
        st.dataframe(filtered_df, use_container_width=True)

        st.markdown("### 🏆 Top 3 Resumes")
        top3 = df.head(3)
        for i, row in top3.iterrows():
            st.markdown(f"**{row['File Name']}** — 🥇 Score: {row['Score (%)']}% | 💼 {row['Years Experience']} yrs exp")
            st.caption(f"🔍 Matched: {row['Matched Keywords']}")
            st.markdown(f"📝 **Summary:** _{row['Summary']}_")
            st.info(row['Feedback'])
            with st.expander("📄 View Resume Text"):
                st.code(resume_text_map.get(row['File Name'], "Text not available"))
            st.markdown("---")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for fname, text in resume_text_map.items():
                cleaned_name = os.path.splitext(fname)[0].replace(" ", "_")
                zip_file.writestr(f"{cleaned_name}.txt", text)

        st.download_button("📦 Download All Resume Texts (ZIP)", data=zip_buffer.getvalue(), file_name="resume_texts.zip", mime="application/zip")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📤 Download CSV", data=csv, file_name="results.csv", mime="text/csv")
    else:
        st.warning("⚠️ No resumes were successfully processed.")
