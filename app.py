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
        
        /* GLOBAL BUTTONS (Apply Gradient) */
        /* We use :not() to ensure we don't color the password toggle */
        .stButton > button, div[data-testid="stForm"] button:not([aria-label="Show password"]) {{
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
        
        .stButton > button:hover, div[data-testid="stForm"] button:not([aria-label="Show password"]):hover {{ 
            transform: scale(1.02); 
            box-shadow: 0 6px 20px rgba(159, 90, 240, 0.6);
        }}
        
        /* --- FIX PASSWORD EYE ICON (Force Default/Transparent) --- */
        button[aria-label="Show password"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: inherit !important;
        }}
        button[aria-label="Show password"]:hover {{
            background: transparent !important;
        }}

        /* EMOTION BUTTONS */
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
        
        /* TUTOR MESSAGE BOX */
        .tutor-box {{
            background: #13131f; padding: 20px; border-radius: 15px;
            border-left: 5px solid #3cd7f6; margin: 20px 0;
            animation: fadeIn 0.5s; color: #e0e0e0;
        }}
        
        /* BOOST CARD */
        .boost-card {{ 
            background: linear-gradient(135deg, #2e1a47 0%, #4a1c40 100%);
            padding: 25px; border-radius: 15px;
            border: 2px solid #ff6ac6; color: white; margin: 20px 0;
        }}

        /* AI RESPONSE */
        .ai-response {{
            background-color: #1e1e2e; padding: 20px; border-radius: 12px;
            border-left: 5px solid #9f5af0; margin-top: 20px; color: white;
        }}

        /* TEXT INPUT */
        .stTextInput > div > div > input {{
            background-color: #181825 !important; color: white !important; border-radius: 10px; border: 1px solid #555;
        }}

        @keyframes fadeIn {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
    </style>
    """, unsafe_allow_html=True)

# ==========================
# 3. FIREBASE SETUP (Cloud + Local Support)
# ==========================
# 1. Try to load from Streamlit Cloud Secrets
if "firebase" in st.secrets:
    firebaseConfig = dict(st.secrets["firebase"])
# 2. If no secrets, try loading from Local JSON file
else:
    config_path = Path("config/firebase_config.json")
    if config_path.exists():
        with open(config_path) as f:
            firebaseConfig = json.load(f)
    else:
        st.error("❌ Configuration missing. Please set up Streamlit Secrets or add config/firebase_config.json")
        st.stop()

# Initialize Connection
try:
    firebase = pyrebase.initialize_app(firebaseConfig)
    auth = firebase.auth()
    db = firebase.database()
except Exception as e:
    st.error(f"Firebase Connection Error: {e}")
    st.stop()

# ==========================
# 4. SESSION STATE
# ==========================
if "user" not in st.session_state: st.session_state.user = None
if isinstance(st.session_state.user, str): st.session_state.user = None

if "extracted_text" not in st.session_state: st.session_state.extracted_text = ""
if "current_mood" not in st.session_state: st.session_state.current_mood = "neutral"
if "tutor_message" not in st.session_state: st.session_state.tutor_message = ""

# AUDIO PATHS
if "chat_audio_path" not in st.session_state: st.session_state.chat_audio_path = None
if "tutor_audio_path" not in st.session_state: st.session_state.tutor_audio_path = None
if "audio_autoplay_flag" not in st.session_state: st.session_state.audio_autoplay_flag = False

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
        
        # --- LOGIN ---
        with tab1:
            with st.form("login"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Sign In")
                
                if submit:
                    try:
                        user = auth.sign_in_with_email_and_password(email, password)
                        st.session_state.user = user
                        try:
                            uid = user['localId']
                            profile = db.child("users").child(uid).child("profile").get().val()
                            st.session_state.username_display = profile['username'] if profile else email.split('@')[0]
                        except:
                            st.session_state.username_display = email.split('@')[0]

                        st.success("Welcome back!")
                        time.sleep(0.5)
                        st.rerun()
                    except: st.error("Login failed. Check credentials.")
        
        # --- REGISTER ---
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

        # --- FORGOT PASSWORD ---
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
        st.title("👤 Profile")
        st.write(f"**{st.session_state.username_display}**")
        st.divider()
        nav = st.radio("Navigation", ["Classroom", "Progress & Badges", "About Project"])
        st.divider()
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    # AUDIO STOP LOGIC (Pause if leaving Classroom)
    if nav != "Classroom":
        st.session_state.tutor_audio_path = None
        # Note: We do NOT clear chat_audio_path here so it persists if you come back

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
            
            # === FIX: DO NOT CLEAR CHAT AUDIO PATH HERE ===
            # This ensures the explanation audio stays visible even if you click sleepy
            
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
                        st.session_state.audio_autoplay_flag = True # Autoplay the TUTOR message only
            
            elif mood == "sleepy" and st.session_state.extracted_text:
                with st.spinner("Generating Energy Booster..."):
                    act = generate_quick_activity(st.session_state.extracted_text)
                    st.session_state.tutor_message = f"**⚡ ENERGY BOOST:**\n\n{act}"
                    st.session_state.tutor_audio_path = text_to_audio_file(act)
                    st.session_state.audio_autoplay_flag = True # Autoplay the WAKE UP message

        with col1: 
            if st.button("🙂 Ready", use_container_width=True): trigger_mood("neutral")
        with col2: 
            if st.button("🤔 Confused", use_container_width=True): trigger_mood("confused")
        with col3: 
            if st.button("🥱 Sleepy", use_container_width=True): trigger_mood("sleepy")
        with col4: 
            if st.button("😃 Happy", use_container_width=True): trigger_mood("happy")

        # 2. TUTOR MESSAGE (TOP)
        if st.session_state.tutor_message:
            style = "boost-card" if st.session_state.current_mood == "sleepy" else "tutor-box"
            st.markdown(f"<div class='{style}'>{st.session_state.tutor_message}</div>", unsafe_allow_html=True)
            
            # TUTOR AUDIO (Wake Up / Simplify)
            if st.session_state.tutor_audio_path:
                tutor_place = st.empty()
                # Only auto-play if the flag is TRUE (newly generated)
                if st.session_state.audio_autoplay_flag:
                    try:
                        tutor_place.audio(st.session_state.tutor_audio_path, format="audio/mp3", autoplay=True)
                    except:
                        tutor_place.audio(st.session_state.tutor_audio_path, format="audio/mp3")
                    # Turn off flag so it doesn't replay on refresh
                    st.session_state.audio_autoplay_flag = False 
                else:
                    tutor_place.audio(st.session_state.tutor_audio_path, format="audio/mp3")

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
                        chat_audio_box = st.empty()
                        # Use autoplay if flag is set AND we aren't playing a tutor message
                        should_autoplay = st.session_state.audio_autoplay_flag and not st.session_state.tutor_message
                        
                        try:
                            if should_autoplay:
                                chat_audio_box.audio(st.session_state.chat_audio_path, format="audio/mp3", autoplay=True)
                                st.session_state.audio_autoplay_flag = False
                            else:
                                chat_audio_box.audio(st.session_state.chat_audio_path, format="audio/mp3")
                        except:
                             chat_audio_box.audio(st.session_state.chat_audio_path, format="audio/mp3")

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
                        # Clear previous tutor message to focus on chat
                        st.session_state.tutor_message = "" 
                        
                        with st.spinner("Thinking..."):
                            ans = explain_with_emotion(st.session_state.extracted_text[:3000], user_q, st.session_state.current_mood)
                            st.session_state.last_bot_answer = ans
                            st.session_state.chat_audio_path = text_to_audio_file(ans.replace("*", ""))
                            st.session_state.audio_autoplay_flag = True
                            st.rerun()
                    else:
                        st.warning("Please upload notes.")

        with t2:
            if st.session_state.extracted_text:
                if not st.session_state.quiz_data:
                    if st.button("Generate Cloud Quiz", type="primary"):
                        with st.spinner("Creating..."):
                            st.session_state.quiz_data = generate_quiz(st.session_state.extracted_text)
                            st.session_state.quiz_submitted = False
                            st.session_state.quiz_ref += 1
                            st.rerun()
                
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
                    
                    if st.button("🔄 Generate New Questions"):
                        with st.spinner("Refreshing..."):
                            st.session_state.quiz_data = [] 
                            new_q = generate_quiz(st.session_state.extracted_text)
                            st.session_state.quiz_data = new_q
                            st.session_state.quiz_submitted = False
                            st.session_state.quiz_ref += 1
                            st.rerun()
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