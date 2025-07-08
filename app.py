import streamlit as st
import pdfplumber
import re
import pandas as pd
import os

# --- Job Roles and Sample JD Paths ---
job_roles = {
    "Upload my own": None,
    "Data Scientist": "data_scientist.txt",
    "Web Developer": "web_developer.txt",
    "Software Engineer": "software_engineer.txt"
}

# --- Safely Extract Text from PDF ---
def extract_text_from_pdf(uploaded_file):
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            return ''.join(page.extract_text() or '' for page in pdf.pages)
    except Exception as e:
        return f"[ERROR] {str(e)}"

# --- Smart Resume Scoring Logic ---
def smart_score(resume_text, jd_text):
    resume_text = resume_text.lower()
    jd_text = jd_text.lower()

    jd_keywords = set(re.findall(r'\b\w+\b', jd_text))
    resume_words = set(re.findall(r'\b\w+\b', resume_text))

    important_skills = [word for word in jd_keywords if word in resume_words]

    core_skills = ['python', 'java', 'sql', 'html', 'css', 'javascript', 'react', 'machine', 'learning']
    weight = sum([3 if word in core_skills else 1 for word in important_skills])
    total_possible = sum([3 if word in core_skills else 1 for word in jd_keywords])

    score = (weight / total_possible) * 100 if total_possible else 0
    score = round(score, 2)

    missing = [word for word in core_skills if word in jd_keywords and word not in resume_words]

    feedback = "✅ Excellent match!" if score >= 80 else (
        f"⚠️ Missing important skills: {', '.join(missing)}" if missing else "⚠️ Needs more relevant content."
    )

    return score, ", ".join(important_skills), feedback

# --- Streamlit App ---
st.set_page_config(page_title="Smart Resume Screener", layout="centered")
st.title("📄 Smart Resume Screening Agent")
st.markdown("Upload multiple resumes and a job description to get ranked matches with feedback.")

# --- Job Description Input ---
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

# --- Resume Upload ---
resume_files = st.file_uploader("📥 Upload Resumes (PDFs)", type="pdf", accept_multiple_files=True)

if jd_text and resume_files:
    results = []

    with st.spinner("🔍 Analyzing resumes..."):
        for file in resume_files:
            resume_text = extract_text_from_pdf(file)
            if resume_text.startswith("[ERROR]"):
                st.error(f"❌ Could not read {file.name}. Skipping.")
                continue

            score, matched_keywords, feedback = smart_score(resume_text, jd_text)
            results.append({
                "File Name": file.name,
                "Score (%)": score,
                "Matched Keywords": matched_keywords,
                "Feedback": feedback
            })

    if results:
        df = pd.DataFrame(results).sort_values(by="Score (%)", ascending=False)
        st.success("✅ Screening Complete!")
        st.markdown("### 📊 Results")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Results as CSV", data=csv, file_name="screening_results.csv", mime="text/csv")
    else:
        st.warning("⚠️ No resumes processed successfully.")
