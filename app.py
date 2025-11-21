import streamlit as st
import pyrebase
import json
import time
import pandas as pd
from pathlib import Path
from datetime import datetime

# Modules
from modules.pdf_processor import extract_text_from_pdf
from modules.data_handler import save_result_to_cloud, load_history_from_cloud
from modules.llm_handler import explain_with_emotion, simplify_concept, generate_quick_activity, simplify_previous_answer
from modules.voice_handler import listen_to_user, text_to_audio_file
from modules.quiz_generator import generate_quiz

# ==========================
# 1. PAGE CONFIG
# ==========================
st.set_page_config(page_title="AuraLearn Cloud", page_icon="🧠", layout="wide")

# ==========================
# 2. THEME & CSS ENGINE
# ==========================
if "theme" not in st.session_state: st.session_state.theme = "dark"

def inject_css():
    main_bg = "#05050a"
    text_color = "#ffffff"
    aura_gradient = "linear-gradient(90deg, #3cd7f6 0%, #9f5af0 50%, #ff6ac6 100%)"

    st.markdown(f"""
    <style>
        .stApp {{ background-color: {main_bg}; color: {text_color}; }}
        /* --- HIDE STREAMLIT BRANDING (The "Credits") --- */
        #MainMenu {{visibility: hidden;}} /* Hides the top-right hamburger menu */
        footer {{visibility: hidden;}}    /* Hides "Made with Streamlit" footer */
        header {{visibility: hidden;}}    /* Hides the top colored running bar */
        
        /* --- GLOBAL BUTTONS --- */
        /* We use a very specific selector to target ONLY standard buttons, not icons */
        .stButton > button {{
            background: {aura_gradient} !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            height: 50px !important;
            font-weight: 700 !important;
            font-size: 18px !important;
            transition: 0.3s;
            box-shadow: 0 4px 15px rgba(159, 90, 240, 0.3);
        }}
        .stButton > button:hover {{ 
            transform: scale(1.02); 
            box-shadow: 0 6px 20px rgba(159, 90, 240, 0.6);
        }}

        /* --- FIX PASSWORD EYE ICON --- */
        /* Force the eye button to be transparent */
        button[aria-label="Show password"] {{
            background-color: transparent !important;
            border: none !important;
            color: inherit !important;
            box-shadow: none !important;
        }}
        button[aria-label="Show password"]:hover {{
            background-color: transparent !important;
        }}

        /* --- EMOTION BUTTONS --- */
        div[data-testid="column"] .stButton > button {{
            background: #181825 !important; 
            color: #e0e0e0 !important; 
            border: 1px solid #3cd7f6 !important;
            height: 60px !important;
            box-shadow: none !important;
        }}
        div[data-testid="column"] .stButton > button:hover {{
            background: {aura_gradient} !important;
            border: none !important;
            color: white !important;
        }}
        
        /* UI CARDS */
        .tutor-box {{
            background: #13131f; padding: 20px; border-radius: 15px;
            border-left: 5px solid #3cd7f6; margin: 20px 0;
            animation: fadeIn 0.5s; color: #e0e0e0;
        }}
        .boost-card {{ 
            background: linear-gradient(135deg, #2e1a47 0%, #4a1c40 100%);
            padding: 25px; border-radius: 15px;
            border: 2px solid #ff6ac6; color: white; margin: 20px 0;
        }}
        .ai-response {{
            background-color: #1e1e2e; padding: 20px; border-radius: 12px;
            border-left: 5px solid #9f5af0; margin-top: 20px; color: white;
        }}

        /* INPUT FIELDS */
        .stTextInput > div > div > input {{
            background-color: #181825 !important; color: white !important; border-radius: 10px; border: 1px solid #555;
        }}

        @keyframes fadeIn {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
    </style>
    """, unsafe_allow_html=True)

# ==========================
# 3. FIREBASE SETUP (Cloud Compatible)
# ==========================
try:
    # 1. Try loading from Streamlit Secrets (Cloud)
    if "firebase" in st.secrets:
        firebaseConfig = dict(st.secrets["firebase"])
    # 2. Try loading from Local JSON (Localhost)
    else:
        config_path = Path("config/firebase_config.json")
        if config_path.exists():
            with open(config_path) as f:
                firebaseConfig = json.load(f)
        else:
            st.error("Firebase config not found in Secrets or local file.")
            st.stop()

    firebase = pyrebase.initialize_app(firebaseConfig)
    auth = firebase.auth()
    db = firebase.database()
except Exception as e:
    st.error(f"Database Connection Error: {e}")
    st.stop() 

# ==========================
# 4. SESSION STATE
# ==========================
if "user" not in st.session_state: st.session_state.user = None
if isinstance(st.session_state.user, str): st.session_state.user = None

if "extracted_text" not in st.session_state: st.session_state.extracted_text = ""
if "current_mood" not in st.session_state: st.session_state.current_mood = "neutral"
if "tutor_message" not in st.session_state: st.session_state.tutor_message = ""

# AUDIO (Independent channels)
if "chat_audio_path" not in st.session_state: st.session_state.chat_audio_path = None
if "tutor_audio_path" not in st.session_state: st.session_state.tutor_audio_path = None

if "quiz_data" not in st.session_state: st.session_state.quiz_data = []
if "quiz_submitted" not in st.session_state: st.session_state.quiz_submitted = False
if "quiz_ref" not in st.session_state: st.session_state.quiz_ref = 0 
if "last_bot_answer" not in st.session_state: st.session_state.last_bot_answer = ""
if "last_user_question" not in st.session_state: st.session_state.last_user_question = ""
if "username_display" not in st.session_state: st.session_state.username_display = ""

# ==========================
# 5. AUTHENTICATION PAGE
# ==========================
def auth_screen():
    inject_css()
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🧠 AuraLearn Cloud")
        st.caption("Secure Login via Firebase")
        
        tab1, tab2, tab3 = st.tabs(["Login", "Register", "Forgot Password"])
        
        # LOGIN
        with tab1:
            with st.form("login"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Sign In")
                
                if submit:
                    # 1. Attempt Login Logic
                    user_obj = None
                    error_msg = None
                    
                    try:
                        user_obj = auth.sign_in_with_email_and_password(email, password)
                    except Exception as e:
                        error_msg = "Login failed. Please check your credentials."

                    # 2. Handle Result OUTSIDE the try block to prevent weird UI states
                    if user_obj:
                        st.session_state.user = user_obj
                        try:
                            uid = user_obj['localId']
                            profile = db.child("users").child(uid).child("profile").get().val()
                            st.session_state.username_display = profile['username'] if profile else email.split('@')[0]
                        except:
                            st.session_state.username_display = email.split('@')[0]
                        
                        st.success("Welcome back!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(error_msg)
        
        # REGISTER
        with tab2:
            with st.form("signup"):
                new_username = st.text_input("Username (for Profile)")
                new_email = st.text_input("Email")
                new_pass = st.text_input("Password", type="password")
                confirm_pass = st.text_input("Confirm Password", type="password")
                submit_reg = st.form_submit_button("Create Account")
                
                if submit_reg:
                    if new_pass != confirm_pass: st.error("Passwords do not match!")
                    elif not new_username: st.error("Username is required.")
                    else:
                        try:
                            user = auth.create_user_with_email_and_password(new_email, new_pass)
                            uid = user['localId']
                            db.child("users").child(uid).child("profile").set({"username": new_username})
                            st.success("Account created! Please login.")
                        except Exception as e: st.error(f"Error: {e}")

        # FORGOT PASSWORD
        with tab3:
            st.info("ℹ️ Check Spam folder if email doesn't appear.")
            reset_email = st.text_input("Enter your email")
            if st.button("Send Reset Link"):
                try:
                    auth.send_password_reset_email(reset_email)
                    st.success(f"Link sent to {reset_email}!")
                except: st.error("Email not found.")

# ==========================
# 6. MAIN APPLICATION
# ==========================
def main_app():
    inject_css()
    try:
        user_id = st.session_state.user['localId']
        if not st.session_state.username_display:
             profile = db.child("users").child(user_id).child("profile").get().val()
             st.session_state.username_display = profile['username'] if profile else st.session_state.user['email'].split('@')[0]
    except:
        st.session_state.user = None
        st.rerun()

    with st.sidebar:
        st.title("Let's Learn!")
        st.write(f"**{st.session_state.username_display}**")
        st.divider()
        nav = st.radio("Navigation", ["Classroom", "Progress & Badges", "About AuraLearn"])
        st.divider()
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    # -------------------------
    # PAGE: CLASSROOM
    # -------------------------
    if nav == "Classroom":
        st.title("Interactive Classroom")
        
        # 1. MOOD CHECK
        st.subheader("How are you feeling?")
        col1, col2, col3, col4 = st.columns(4)
        
        def trigger_mood(mood):
            st.session_state.current_mood = mood
            st.session_state.tutor_message = "" 
            st.session_state.tutor_audio_path = None 
            
            # === FIX: STOP PREVIOUS AUDIO ===
            # This line wipes the explanation audio so it doesn't overlap
            st.session_state.chat_audio_path = None 
            
            if mood == "confused":
                with st.spinner("🧠 Teacher is simplifying..."):
                    if st.session_state.last_bot_answer:
                        simplified = simplify_previous_answer(st.session_state.last_bot_answer, st.session_state.last_user_question)
                        st.session_state.tutor_message = f"**Let me rephrase that:**\n\n{simplified}"
                    elif st.session_state.extracted_text:
                        simplified = simplify_concept(st.session_state.extracted_text)
                        st.session_state.tutor_message = f"**Topic Simplification:**\n\n{simplified}"
                    else:
                        st.session_state.tutor_message = "Please upload notes first!"

                    if st.session_state.tutor_message:
                        st.session_state.tutor_audio_path = text_to_audio_file(st.session_state.tutor_message.replace("*", ""))
                        st.session_state.force_autoplay = True
            
            elif mood == "sleepy" and st.session_state.extracted_text:
                with st.spinner("Generating Energy Booster..."):
                    act = generate_quick_activity(st.session_state.extracted_text)
                    st.session_state.tutor_message = f"⚡ ENERGY BOOST :\n\n{act}"
                    st.session_state.tutor_audio_path = text_to_audio_file(act)
                    st.session_state.force_autoplay = True
                    # st.session_state.tutor_audio_key = time.time()
        with col1: 
            if st.button("🙂 Ready", use_container_width=True): trigger_mood("neutral")
        with col2: 
            if st.button("🤔 Confused", use_container_width=True): trigger_mood("confused")
        with col3: 
            if st.button("🥱 Sleepy", use_container_width=True): trigger_mood("sleepy")
        with col4: 
            if st.button("😃 Happy", use_container_width=True): trigger_mood("happy")

        # 2. TUTOR MESSAGE (WAKE UP / CONFUSED)
        if st.session_state.tutor_message:
            style = "boost-card" if st.session_state.current_mood == "sleepy" else "tutor-box"
            st.markdown(f"<div class='{style}'>{st.session_state.tutor_message}</div>", unsafe_allow_html=True)
            
            # TUTOR AUDIO (No key to avoid crash on old Streamlit)
            if st.session_state.tutor_audio_path:
                # Try to use autoplay if supported, else just show
                try:
                    st.audio(st.session_state.tutor_audio_path, format="audio/mp3", autoplay=True)
                except:
                    st.audio(st.session_state.tutor_audio_path, format="audio/mp3")

        # 3. LEARNING AREA
        t1, t2 = st.tabs(["📚 Study Material", "📝 Quiz"])
        
        with t1:
            c_upload, c_chat = st.columns([1, 2])
            
            with c_upload:
                st.subheader("Source")
                if st.session_state.extracted_text:
                    st.success("✅ Notes Active")
                    if st.button("Clear & Upload New"):
                        st.session_state.extracted_text = ""
                        st.session_state.quiz_data = []
                        st.session_state.quiz_submitted = False
                        st.rerun()
                else:
                    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
                    if uploaded_file:
                        with st.spinner("Processing..."):
                            text = extract_text_from_pdf(uploaded_file)
                            st.session_state.extracted_text = text
                            st.session_state.quiz_data = []
                            st.session_state.quiz_submitted = False
                            st.rerun()

            with c_chat:
                st.subheader(f"Chat ({st.session_state.current_mood.upper()})")
                
                # AI Response Area (PERSISTENT)
                if st.session_state.last_bot_answer:
                    st.markdown(f"<div class='ai-response'><b>🧠 Aura:</b> {st.session_state.last_bot_answer}</div>", unsafe_allow_html=True)
                    
                    # CHAT AUDIO (Always Visible)
                    if st.session_state.chat_audio_path:
                        st.markdown("**Audio Explanation:**")
                        try:
                            st.audio(st.session_state.chat_audio_path, format="audio/mp3", autoplay=True)
                        except:
                            st.audio(st.session_state.chat_audio_path, format="audio/mp3")

                input_container = st.container()
                col_mic, col_text = input_container.columns([1, 6])
                with col_mic:
                    st.write("") 
                    st.write("") 
                    if st.button("🎙️", help="Speak"):
                        txt = listen_to_user()
                        if txt: st.session_state.last_user_question = txt
                
                with col_text:
                    q_val = st.session_state.get("last_user_question", "")
                    user_q = st.text_input("Ask a doubt...", value=q_val, label_visibility="hidden", placeholder="Type or Speak...")

                if st.button("✨ Explain It", type="primary", use_container_width=True):
                    if st.session_state.extracted_text and user_q:
                        st.session_state.last_user_question = user_q
                        with st.spinner("Thinking..."):
                            ans = explain_with_emotion(st.session_state.extracted_text[:3000], user_q, st.session_state.current_mood)
                            st.session_state.last_bot_answer = ans
                            st.session_state.chat_audio_path = text_to_audio_file(ans.replace("*", ""))
                            st.rerun()
                    else:
                        st.warning("Please upload notes.")

        with t2:
            if st.session_state.extracted_text:
                # 1. GENERATE BUTTON
                if not st.session_state.quiz_data:
                    if st.button("Generate Cloud Quiz", type="primary"):
                        with st.spinner("Creating..."):
                            st.session_state.quiz_data = generate_quiz(st.session_state.extracted_text)
                            st.session_state.quiz_submitted = False
                            st.session_state.quiz_ref += 1
                            st.rerun()
                
                # 2. QUIZ FORM
                elif not st.session_state.quiz_submitted:
                    with st.form(f"quiz_f_{st.session_state.quiz_ref}"):
                        for i, q in enumerate(st.session_state.quiz_data):
                            st.markdown(f"**{i+1}. {q['question']}**")
                            st.radio("Choose:", q['options'], key=f"q{i}_{st.session_state.quiz_ref}", index=None)
                        
                        if st.form_submit_button("Submit & Save"):
                            st.session_state.quiz_submitted = True
                            score = 0
                            for i, q in enumerate(st.session_state.quiz_data):
                                user_choice = st.session_state.get(f"q{i}_{st.session_state.quiz_ref}")
                                if user_choice == q['options'][q['answer']]:
                                    score += 1
                            try:
                                save_result_to_cloud(user_id, score, len(st.session_state.quiz_data), st.session_state.current_mood)
                            except: pass
                            st.rerun()

                # 3. RESULTS
                else:
                    st.success("🎉 Quiz Submitted & Saved!")
                    score = 0
                    for i, q in enumerate(st.session_state.quiz_data):
                        user_choice = st.session_state.get(f"q{i}_{st.session_state.quiz_ref}")
                        correct_choice = q['options'][q['answer']]
                        st.markdown(f"**Q{i+1}: {q['question']}**")
                        if user_choice == correct_choice:
                            score += 1
                            st.success(f"✅ Correct")
                        else:
                            st.error(f"❌ Incorrect (Your Answer: {user_choice})")
                            st.info(f"👉 Correct Answer: **{correct_choice}**")
                        st.divider()
                    
                    st.metric("Final Score", f"{score}/{len(st.session_state.quiz_data)}")
                    
                    # if st.button("🔄 Generate New Questions"):
                    #     with st.spinner("Refreshing..."):
                    #         st.session_state.quiz_data = [] 
                    #         new_q = generate_quiz(st.session_state.extracted_text)
                    #         st.session_state.quiz_data = new_q
                    #         st.session_state.quiz_submitted = False
                    #         st.session_state.quiz_ref += 1
                    #         st.rerun()
            else:
                st.info("Upload notes first.")

    # -------------------------
    # PAGE: PROGRESS
    # -------------------------
    elif nav == "Progress & Badges":
        st.title("🏆 Your Achievement Hub")
        try:
            history = load_history_from_cloud(user_id)
        except:
            history = []
            st.warning("No database connection.")
        
        if history:
            df = pd.DataFrame(history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            total_sessions = len(df)
            avg_score = df['percentage'].mean()
            perfect_scores = len(df[df['percentage'] == 100])
            
            st.subheader("🎖️ Badges Earned")
            c1, c2, c3 = st.columns(3)
            with c1:
                if total_sessions >= 1: st.success("🎓 **Novice**\n\n1st Session")
                else: st.info("🔒 **Novice**\n\nComplete 1 session")
            with c2:
                if total_sessions >= 5: st.success("🚀 **Scholar**\n\n5 Sessions")
                else: st.info(f"🔒 **Scholar**\n\n{5-total_sessions} to go")
            with c3:
                if total_sessions >= 10: st.success("👑 **Master**\n\n10 Sessions")
                else: st.info(f"🔒 **Master**\n\n{10-total_sessions} to go")
            st.write("")
            c4, c5, c6 = st.columns(3)
            with c4:
                if avg_score >= 90: st.success("🧠 **Genius**\n\nAvg > 90%")
                else: st.info("🔒 **Genius**\n\nGet >90% Avg")
            with c5:
                if perfect_scores >= 1: st.success("🎯 **Sharpshooter**\n\n100% Score")
                else: st.info("🔒 **Sharpshooter**\n\nGet 100% once")
            with c6:
                if total_sessions >= 20: st.success("🔥 **Unstoppable**\n\n20 Sessions")
                else: st.info("🔒 **Unstoppable**\n\nKeep going!")

            st.divider()
            st.subheader("📅 Weekly Activity")
            df['date'] = df['timestamp'].dt.date
            st.bar_chart(df['date'].value_counts())

            with st.expander("View Full History"):
                st.dataframe(df.sort_values(by='timestamp', ascending=False))
        else:
            st.info("Start learning to earn badges!")

    # -------------------------
    # PAGE: ABOUT
    # -------------------------
    elif nav == "About Project":
        st.title("🚀 About AuraLearn")
        st.markdown("""
        ### **What is AuraLearn?**
        AuraLearn is an intelligent, empathy-driven AI Tutoring Platform designed to make learning personalized and adaptive.
        
        ### **🌟 Unique Features**
        1.  **🧠 Emotion-Adaptive Intelligence:**
            * **Confused?** The AI auto-detects this and simplifies complex concepts using analogies.
            * **Sleepy?** It generates physical/sensory wake-up activities instead of boring quizzes.
        2.  **💬 Conversational Memory:** Chat with your PDF notes naturally. The AI remembers context.
        3.  **📚 Document Mastery:** Upload any PDF, and the system instantly learns it to answer questions and generate quizzes.
        4.  **☁️ Cloud Sync:** Your progress, badges, and history are saved securely in the cloud (Firebase).
        5.  **🗣️ Voice Interaction:** Speak to your tutor and hear explanations read back to you.
        
        ---
        *Built with Python, Streamlit, Firebase, and Llama 3.*
        """)

# ==========================
# 7. RUN
# ==========================
if st.session_state.user:
    main_app()
else:
    auth_screen()