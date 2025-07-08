import streamlit as st
import pdfplumber
import re

# ---- Extract Text from PDF ----
def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text() or ''
    return text

# ---- Score Resume Based on JD ----
def score_resume(resume_text, jd_text):
    jd_keywords = set(re.findall(r'\b\w+\b', jd_text.lower()))
    resume_words = set(re.findall(r'\b\w+\b', resume_text.lower()))
    matched = jd_keywords.intersection(resume_words)
    score = (len(matched) / len(jd_keywords)) * 100 if jd_keywords else 0
    return round(score, 2), matched

# ---- Streamlit UI ----
st.set_page_config(page_title="Resume Screening Agent", layout="centered")
st.title("📄 Resume Screening Agent")
st.markdown("Upload a **resume (PDF)** and a **job description (TXT)** to see how well they match.")

resume_file = st.file_uploader("Upload Resume (PDF)", type="pdf")
jd_file = st.file_uploader("Upload Job Description (TXT)", type="txt")

if resume_file and jd_file:
    with st.spinner("Extracting resume content..."):
        resume_text = extract_text_from_pdf(resume_file)
        jd_text = jd_file.read().decode("utf-8")

        score, matched_keywords = score_resume(resume_text, jd_text)

    st.success(f"✅ Resume Match Score: {score}%")

    st.markdown("### 🔍 Matched Keywords:")
    st.write(", ".join(sorted(matched_keywords)))

    with st.expander("📃 Resume Content Preview"):
        st.text(resume_text[:2000])
