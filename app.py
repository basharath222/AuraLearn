import streamlit as st
import pandas as pd
from modules.pdf_processor import extract_text_from_pdf

# Page Config
st.set_page_config(page_title="AuraLearn", page_icon="🧠", layout="wide")

# Session State Init
if "user" not in st.session_state: st.session_state.user = {"email": "student@auralearn.ai"} # Simulating logged in user
if "extracted_text" not in st.session_state: st.session_state.extracted_text = ""
if "current_mood" not in st.session_state: st.session_state.current_mood = "neutral"

# CSS Styling
st.markdown("""
<style>
    .aura-card { background-color: #e0f7fa; padding: 20px; border-radius: 12px; border: 2px solid #00bcd4; color: #006064; }
    .metric-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ==========================
# SIDEBAR (Navigation)
# ==========================
st.sidebar.title("🧠 AuraLearn")
choice = st.sidebar.radio("Go to", ["Study Room", "Progress Dashboard"])

# ==========================
# 1. STUDY ROOM (Main App)
# ==========================
if choice == "Study Room":
    st.title("📘 Interactive Classroom")
    
    tab1, tab2 = st.tabs(["🤖 Chat & Voice", "📝 Take Quiz"])

    # --- TAB 1: LEARNING ---
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("1. Material")
            uploaded_file = st.file_uploader("Upload PDF Notes", type=["pdf"])
            if uploaded_file:
                with st.spinner("Analyzing Content..."):
                    text = extract_text_from_pdf(uploaded_file)
                    st.session_state.extracted_text = text
                    st.success("Notes Loaded!")

        with col2:
            st.subheader("2. Aura Sense")
            # Mood Display
            st.markdown(f"""
            <div class="aura-card">
                <h4>Current Vibe: {st.session_state.current_mood.upper()}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📷 Update Mood"):
                with st.spinner("Scanning..."):
                    from modules.emotion_detector import capture_live_mood
                    st.session_state.current_mood = capture_live_mood(duration=3)
                    st.rerun()

            st.divider()
            
            # Voice & Chat
            col_v1, col_v2 = st.columns([1, 5])
            with col_v1:
                if st.button("🎤", help="Speak your question"):
                    from modules.voice_handler import listen_to_user
                    with st.spinner("Listening..."):
                        v_text = listen_to_user()
                        if v_text: st.session_state.voice_query = v_text
            
            with col_v2:
                def_val = st.session_state.get("voice_query", "")
                q = st.text_input("Ask your teacher:", value=def_val)

            if st.button("Explain It"):
                if st.session_state.extracted_text:
                    with st.spinner("Thinking..."):
                        from modules.llm_handler import explain_with_emotion, explain_with_emotion
                        from modules.voice_handler import text_to_speech
                        
                        ans = explain_with_emotion(st.session_state.extracted_text[:3000], q, st.session_state.current_mood)
                        st.info(ans)
                        
                        # Audio
                        audio_file = text_to_speech(ans.replace("*", ""))
                        if audio_file: st.audio(audio_file)
                else:
                    st.warning("Upload a PDF first!")

    # --- TAB 2: QUIZ (Enhanced) ---
    with tab2:
        st.header("🧠 Knowledge Check")
        
        if st.button("Generate New Quiz"):
            if st.session_state.extracted_text:
                with st.spinner("Drafting questions..."):
                    from modules.quiz_generator import generate_quiz
                    st.session_state.quiz_data = generate_quiz(st.session_state.extracted_text)
                    st.session_state.quiz_submitted = False
            else:
                st.error("Upload PDF first!")

        if "quiz_data" in st.session_state and st.session_state.quiz_data:
            # Use a form so we can submit all at once
            with st.form("quiz_form"):
                user_answers = {}
                for i, q in enumerate(st.session_state.quiz_data):
                    st.markdown(f"**Q{i+1}: {q['question']}**")
                    user_answers[i] = st.radio(f"Select:", q['options'], key=f"q{i}", index=None)
                    st.write("---")
                
                submitted = st.form_submit_button("Submit Answers")
                
                if submitted:
                    st.session_state.quiz_submitted = True
                    
            # --- RESULTS SECTION (Outside Form) ---
            if st.session_state.get("quiz_submitted", False):
                score = 0
                total = len(st.session_state.quiz_data)
                
                st.subheader("📊 Results")
                for i, q in enumerate(st.session_state.quiz_data):
                    correct_idx = q['answer']
                    correct_txt = q['options'][correct_idx]
                    user_txt = st.session_state.get(f"q{i}")
                    
                    if user_txt == correct_txt:
                        score += 1
                        st.success(f"Q{i+1}: Correct! ✅")
                    else:
                        st.error(f"Q{i+1}: Incorrect ❌")
                        st.caption(f"👉 Correct Answer: **{correct_txt}**")

                # Save Data
                from modules.data_handler import save_result
                save_result(score, total, st.session_state.current_mood)
                
                # Teacher Feedback
                percentage = (score/total)*100
                if percentage == 100:
                    st.balloons()
                    st.success("🏆 Perfect Score! You mastered this topic.")
                elif percentage >= 50:
                    st.info("👍 Good effort! Review the wrong answers to improve.")
                else:
                    st.warning("📚 Let's review the notes again. Don't give up!")

# ==========================
# 2. DASHBOARD (New!)
# ==========================
elif choice == "Progress Dashboard":
    st.title("📈 Student Progress Report")
    
    from modules.data_handler import load_history
    history = load_history()
    
    if not history:
        st.info("No quiz data yet. Take a quiz in the Study Room!")
    else:
        # KPIs
        df = pd.DataFrame(history)
        avg_score = df["percentage"].mean()
        total_quizzes = len(df)
        common_mood = df["mood"].mode()[0] if not df["mood"].empty else "N/A"
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Quizzes", total_quizzes)
        c2.metric("Average Score", f"{avg_score:.1f}%")
        c3.metric("Dominant Mood", common_mood.upper())
        
        st.divider()
        
        # Charts
        col_chart1, col_chart2 = st.columns([2, 1])
        
        with col_chart1:
            st.subheader("Performance History")
            st.line_chart(df[["timestamp", "percentage"]].set_index("timestamp"))
        
        with col_chart2:
            st.subheader("Mood Distribution")
            mood_counts = df["mood"].value_counts()
            st.bar_chart(mood_counts)

        st.subheader("Recent Activity")
        st.dataframe(df.tail(5))