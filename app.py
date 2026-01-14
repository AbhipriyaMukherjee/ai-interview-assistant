import streamlit as st
import pandas as pd
import time
import random

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Career Assistant", layout="wide", initial_sidebar_state="expanded")

# --- SESSION STATE INITIALIZATION ---
if 'skills' not in st.session_state:
    st.session_state['skills'] = []
if 'name' not in st.session_state:
    st.session_state['name'] = "Candidate"
if 'resume_uploaded' not in st.session_state:
    st.session_state['resume_uploaded'] = False

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", [
    "Home",
    "1. Resume Upload",
    "2. Job Recommendations",
    "3. Mock Interview",
    "4. Feedback Report"
])

st.sidebar.markdown("---")
st.sidebar.info("Project: AI-Powered Career Assistant\n\nTech Stack: Streamlit, NLP, ML")

# ==========================================
# PAGE: HOME
# ==========================================
if page == "Home":
    st.title("AI-Powered Career & Interview Assistant")
    st.markdown("""
    Welcome to the Career Accelerator system. This tool helps you:

    1.  **Analyze your Resume** to extract key skills.
    2.  **Match with Jobs** based on AI compatibility scoring.
    3.  **Practice Interviews** with an AI agent.
    4.  **Get Detailed Feedback** on your performance.
    """)
    # FIX: Changed use_column_width to use_container_width
    st.image("https://cdn.pixabay.com/photo/2018/03/30/03/36/feedback-3274381_1280.jpg", caption="AI Career Cycle",
             use_container_width=True)

# ==========================================
# PAGE 1: RESUME UPLOAD & PARSING
# ==========================================
elif page == "1. Resume Upload":
    st.header("Upload Your Resume")
    st.write("Upload your CV (PDF/DOCX) to extract skills and experience.")

    uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'docx', 'txt'])

    if uploaded_file is not None:
        st.success("File Uploaded Successfully!")

        with st.spinner('AI is analyzing your resume...'):
            time.sleep(2)

            # Mock Extracted Data
        st.session_state['name'] = "Alex Developer"
        st.session_state['skills'] = ["Python", "Machine Learning", "Streamlit", "Data Analysis", "SQL",
                                      "Communication"]
        st.session_state['resume_uploaded'] = True

        st.divider()
        st.subheader("Analysis Results")
        col1, col2 = st.columns(2)

        with col1:
            st.info(f"**Name Detected:** {st.session_state['name']}")
            st.write("**Experience Level:** Mid-Senior (Estimated)")

        with col2:
            st.write("**Top Skills Detected:**")
            for skill in st.session_state['skills']:
                st.markdown(
                    f"<span style='background-color:#e0f2f1; padding:5px; border-radius:5px; margin:2px; color:black;'>{skill}</span>",
                    unsafe_allow_html=True)

# ==========================================
# PAGE 2: JOB RECOMMENDATIONS
# ==========================================
elif page == "2. Job Recommendations":
    st.header("Job Field & Company Suggestions")

    if not st.session_state['resume_uploaded']:
        st.warning("Please upload your resume in Step 1 first!")
    else:
        st.write(f"Based on your skills: **{', '.join(st.session_state['skills'][:3])}...**")

        data = {
            "Company": ["Google", "Spotify", "Netflix", "Tesla", "Startup Inc"],
            "Role": ["AI Engineer", "Data Scientist", "ML Ops Engineer", "Software Engineer", "Python Dev"],
            "Match Score": ["98%", "95%", "92%", "88%", "85%"],
            "Domain": ["Tech", "Music Streaming", "Media", "Automotive", "FinTech"]
        }
        df = pd.DataFrame(data)

        # Display as a table
        st.dataframe(df, use_container_width=True)

        st.subheader("Skill-Job Alignment")
        st.progress(85, text="Your profile matches **85%** of market requirements for 'AI Engineer'.")

# ==========================================
# PAGE 3: MOCK INTERVIEW
# ==========================================
elif page == "3. Mock Interview":
    st.header("AI Mock Interview (Text-Based)")
    st.caption("The AI will ask you a question based on your profile. Type your answer below.")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant",
                                      "content": "Hello! Let's start. Can you explain the difference between Supervised and Unsupervised Learning?"}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Type your answer here..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        response = "That is a solid answer! You covered the labels correctly. Now, tell me about a time you handled a difficult stakeholder."

        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# ==========================================
# PAGE 4: FEEDBACK REPORT
# ==========================================
elif page == "4. Feedback Report":
    st.title("Comprehensive Performance Report")
    st.markdown("### Summary Dashboard")
    st.divider()

    st.info(
        "**System Note:** This section aggregates results from the Resume Scan, Job Matching, "
        "and Interview Performance (Content + Voice + Body Language)."
    )

    st.write("")

    col1, col2, col3 = st.columns(3)

    # Column 1: Content
    with col1:
        st.subheader("Content")
        with st.container(border=True):
            st.success("**Strengths:** Strong technical vocabulary detected (Python, ML).")
            st.warning("**To Improve:** Answers could be more structured (STAR method).")

    # Column 2: Voice
    with col2:
        st.subheader("Voice Analysis")
        with st.container(border=True):
            st.info("**Pace:** 140 words per minute (Ideal).")
            st.error("**Issues:** Detected filler words: 'um', 'like'.")

    # Column 3: Body Language
    with col3:
        st.subheader("Body Language")
        with st.container(border=True):
            st.success("**Positives:** Good facial engagement.")
            st.warning("**Focus:** Eye contact dropped during technical questions.")

    st.divider()

    # Detailed Scores
    st.subheader("Overall Score Calculation")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Resume Strength", "85/100", "+5%")
    col_b.metric("Interview Confidence", "78/100", "-2%")
    col_c.metric("Technical Accuracy", "92/100", "+12%")

    if st.button("Download Final PDF Report"):
        st.toast("Generating PDF Report...")