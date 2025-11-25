import streamlit as st
import pyrebase
import json
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from streamlit_mic_recorder import mic_recorder

# Modules
from modules.pdf_processor import extract_text_from_pdf
from modules.data_handler import save_result_to_cloud, load_history_from_cloud
from modules.llm_handler import explain_with_emotion, simplify_concept, generate_quick_activity, simplify_previous_answer
from modules.voice_handler import listen_to_user, text_to_audio_file
from modules.quiz_generator import generate_quiz

# ==========================
# 1. PAGE CONFIG
# ==========================
st.set_page_config(
    page_title="AuraLearn Cloud", 
    page_icon="🧠", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

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
        
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        .stDeployButton {{ display: none; }}
        
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



import os # Ensure this is imported at the top

# ... (Your CSS and Imports remain the same)

# ==========================
# 3. FIREBASE SETUP (Universal: Cloud + Local)
# ==========================
import os

firebaseConfig = None

# 1. Try Environment Variables (Render)
if os.getenv("FIREBASE_API_KEY"):
    firebaseConfig = {
        "apiKey": os.getenv("FIREBASE_API_KEY"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
        "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID"),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.getenv("FIREBASE_APP_ID")
    }

# 2. Try Streamlit Secrets (Streamlit Cloud) - Wrapped in try/except to prevent crash
if not firebaseConfig:
    try:
        if "firebase" in st.secrets:
            firebaseConfig = dict(st.secrets["firebase"])
    except: pass # File not found, ignore

# 3. Try Local File (Localhost)
if not firebaseConfig:
    config_path = Path("config/firebase_config.json")
    if config_path.exists():
        with open(config_path) as f:
            firebaseConfig = json.load(f)

# Initialize
if firebaseConfig:
    try:
        firebase = pyrebase.initialize_app(firebaseConfig)
        auth = firebase.auth()
        db = firebase.database()
    except Exception as e:
        st.error(f"Firebase Init Error: {e}")
        st.stop()
else:
    st.error("❌ Configuration missing. Please set Environment Variables in Render.")
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
        st.title("🧠 AuraLearn ")
        st.caption("Secure Login via Firebase")
        
        tab1, tab2, tab3 = st.tabs(["Login", "Register", "Forgot Password"])
        
        # LOGIN
        with tab1:
            with st.form("login"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Sign In")
                
                if submit:
                    try:
                        # 1. Auth Check
                        user = auth.sign_in_with_email_and_password(email, password)
                        st.session_state.user = user
                        
                        # 2. Username Check (WITH TOKEN!)
                        try:
                            uid = user['localId']
                            token = user['idToken'] # <--- Get Token
                            
                            # Pass token to read protected DB
                            profile = db.child("users").child(uid).child("profile").get(token=token).val()
                            
                            if profile and 'username' in profile:
                                st.session_state.username_display = profile['username']
                            else:
                                st.session_state.username_display = email.split('@')[0]
                        except:
                            st.session_state.username_display = email.split('@')[0]

                        st.success("Welcome back!")
                        time.sleep(0.5)
                        st.rerun()
                    except: 
                        st.error("Login failed. Check credentials.")
        
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
        token = st.session_state.user['idToken'] # <--- Get Token
        
        # Fetch name if missing (using Token)
        if not st.session_state.username_display:
             profile = db.child("users").child(user_id).child("profile").get(token=token).val()
             if profile and 'username' in profile:
                 st.session_state.username_display = profile['username']
             else:
                 st.session_state.username_display = st.session_state.user['email'].split('@')[0]
    except:
        st.session_state.user = None
        st.rerun()

    with st.sidebar:
        st.title("Let's Learn!")
        # Display the fetched username
        st.markdown(f"### 👤 {st.session_state.username_display}")
        st.divider()
        # ... rest of sidebar code ...
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

        # FIX: Reset quiz state if returning from another page
        if "last_nav" not in st.session_state or st.session_state.last_nav != "Classroom":
             st.session_state.quiz_data = []
             st.session_state.quiz_submitted = False
             st.session_state.quiz_ref += 1
             st.session_state.last_nav = "Classroom"
        
        # 1. MOOD CHECK
        st.subheader("How are you feeling?")
        col1, col2, col3, col4 = st.columns(4)
        
        def trigger_mood(mood):
            st.session_state.current_mood = mood
            st.session_state.tutor_message = "" 
            st.session_state.tutor_audio_path = None 
            
            # === FIX: STOP PREVIOUS AUDIO ===
            # This line wipes the explanation audio so it doesn't overlap
            # st.session_state.chat_audio_path = None 
            
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
                    uploaded_file = st.file_uploader("Upload File", type=["pdf","txt","md","docx","pptx","xlsx","csv"])
                    if uploaded_file:
                        with st.spinner("Processing..."):
                            text = extract_text_from_pdf(uploaded_file)
                            st.session_state.extracted_text = text
                            st.session_state.quiz_data = []
                            st.session_state.quiz_submitted = False
                            st.rerun()

            with c_chat:
                st.subheader(f"Chat ({st.session_state.current_mood.upper()})")
                
                # 1. AI Response Area
                if st.session_state.last_bot_answer:
                    st.markdown(f"<div class='ai-response'><b>🧠 Aura:</b> {st.session_state.last_bot_answer}</div>", unsafe_allow_html=True)
                    
                    if st.session_state.chat_audio_path:
                        st.markdown("**Audio Explanation:**")
                        try:
                            st.audio(st.session_state.chat_audio_path, format="audio/mp3", autoplay=st.session_state.force_autoplay)
                        except:
                            st.audio(st.session_state.chat_audio_path, format="audio/mp3")
                        # Reset flag so it doesn't keep replaying on every interaction
                        st.session_state.force_autoplay = False

                # 2. INPUT AREA (Fixed Blinking & Text Sync)
                input_container = st.container()
                col_mic, col_text = input_container.columns([1, 6])
                
                with col_mic:
                    st.write("") 
                    st.write("") 
                    # Voice Recorder
                    audio_data = mic_recorder(
                        start_prompt="🎙️",
                        stop_prompt="⏹️",
                        key='recorder',
                        format="wav",
                        use_container_width=True
                    )

                # VOICE PROCESSING LOGIC (Prevents Infinite Loop)
                if audio_data:
                    # Only process if we haven't processed this specific audio yet
                    # We can't check audio ID, so we check if the text is new.
                    from modules.voice_handler import transcribe_audio_bytes
                    
                    # Transcribe (This might take a second, show a spinner)
                    if "last_audio_bytes" not in st.session_state or st.session_state.last_audio_bytes != audio_data['bytes']:
                         with st.spinner("Transcribing..."):
                            text = transcribe_audio_bytes(audio_data['bytes'])
                            if text:
                                # Update the session state used by the text input
                                st.session_state.user_query_input = text
                                st.session_state.last_user_question = text
                                st.session_state.last_audio_bytes = audio_data['bytes'] # Mark as processed
                                st.rerun() # Force refresh once to show text
                
                with col_text:
                    # LINK TEXT INPUT DIRECTLY TO SESSION STATE KEY
                    # This ensures when we update 'user_query_input' above, this box updates automatically.
                    user_q = st.text_input(
                        "Ask a doubt...", 
                        key="user_query_input", 
                        label_visibility="hidden", 
                        placeholder="Type or Speak..."
                    )

                # 3. Explain Button
                if st.button("✨ Explain It", type="primary", use_container_width=True):
                    if st.session_state.extracted_text and user_q:
                        st.session_state.last_user_question = user_q
                        # Clear tutor message
                        st.session_state.tutor_message = ""
                        
                        with st.spinner("Thinking..."):
                            ans = explain_with_emotion(st.session_state.extracted_text[:3000], user_q, st.session_state.current_mood)
                            st.session_state.last_bot_answer = ans
                            st.session_state.chat_audio_path = text_to_audio_file(ans.replace("*", ""))
                            st.session_state.force_autoplay = True
                            st.rerun()
                    else:
                        st.warning("Please upload notes first.")

        with t2:
            if st.session_state.extracted_text:
                # 1. GENERATE SETTINGS (If no quiz exists)
                if not st.session_state.quiz_data:
                    st.subheader("Generate Quiz")
                    
                    # --- NEW: Difficulty & Count Inputs ---
                    c1, c2 = st.columns(2)
                    with c1:
                        num_q = st.number_input("Number of Questions", min_value=3, max_value=20, value=5)
                    with c2:
                        diff = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1) # Index 1 = Medium default
                    
                    if st.button("Generate Quiz", type="primary"):
                        with st.spinner(f"Creating {diff} Quiz..."):
                            st.session_state.quiz_data = generate_quiz(st.session_state.extracted_text, num_q, diff)
                            st.session_state.quiz_submitted = False
                            st.session_state.quiz_ref += 1
                            st.rerun()
                
                # 2. QUIZ FORM (Only if NOT submitted)
                elif not st.session_state.quiz_submitted:
                    with st.form(f"quiz_f_{st.session_state.quiz_ref}"):
                        for i, q in enumerate(st.session_state.quiz_data):
                            st.markdown(f"**{i+1}. {q['question']}**")
                            st.radio("Select:", q['options'], key=f"q{i}_{st.session_state.quiz_ref}", index=None)
                        
                        if st.form_submit_button("Submit & Save"):
                            st.session_state.quiz_submitted = True
                            
                            # Calculate Score
                            score = 0
                            for i, q in enumerate(st.session_state.quiz_data):
                                user_choice = st.session_state.get(f"q{i}_{st.session_state.quiz_ref}")
                                if user_choice == q['options'][q['answer']]:
                                    score += 1
                            
                            # --- FIX: PASS TOKEN TO SAVE ---
                            try:
                                token = st.session_state.user['idToken'] # Get Token
                                save_result_to_cloud(
                                    user_id, 
                                    score, 
                                    len(st.session_state.quiz_data), 
                                    st.session_state.current_mood,
                                    token # <--- Passed here
                                )
                                st.success("✅ Score Saved to Cloud!")
                            except Exception as e:
                                st.error(f"Save Failed: {e}")
                            
                            time.sleep(1)
                            st.rerun()

                # 3. RESULTS (Show AFTER submission)
                else:
                    st.success("🎉 Quiz Submitted!")
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
                    
                    # Simple Close Button
                    if st.button("Close & Reset"):
                        st.session_state.quiz_data = []
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
        
        # FIX: Reset quiz if user navigates away so it doesn't auto-submit later
        st.session_state.quiz_submitted = False
        st.session_state.quiz_data = []
        
        # 1. Load Data with Token
        history = []
        try:
            token = st.session_state.user['idToken'] # Get Token
            history = load_history_from_cloud(user_id, token)
        except Exception as e:
            st.warning(f"Syncing... {e}")
        
        if history:
            df = pd.DataFrame(history)
            if 'timestamp' in df.columns:
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
                if not df.empty:
                    df['date'] = df['timestamp'].dt.date
                    st.bar_chart(df['date'].value_counts())
                    with st.expander("View Full History"):
                        st.dataframe(df.sort_values(by='timestamp', ascending=False))
            # except Exception as e:
                # st.error(f"Data Format Error: {e}")
        else:
            st.info("Start learning to earn badges! (No data found)")

    # -------------------------
    # PAGE: ABOUT
    # -------------------------
  
    # -------------------------
    # PAGE: ABOUT
    # -------------------------
    elif nav == "About AuraLearn":
        st.title("🚀 About AuraLearn")
        
        # 1. HERO SECTION
        st.markdown("""
        ### **Where AI Meets Empathy**
        **AuraLearn** is an **Emotion-Adaptive AI Tutoring Platform**. We believe that education shouldn't just be about transferring information—it should be about understanding the student.
        
        Unlike standard chatbots that treat every user the same, AuraLearn uses **Affective Computing** to detect your mental state and adapt its teaching strategy in real-time.
        """)
        
        st.divider()

        # 2. THE PROBLEM & SOLUTION
        c1, c2 = st.columns(2)
        with c1:
            st.info("🛑 **The Problem**")
            st.markdown("""
            Traditional online learning is **"blind."**
            * PDF readers and video lectures don't know if you are confused, bored, or falling asleep.
            * They keep delivering complex info even when you've stopped processing it.
            * This leads to **learning fatigue** and low retention.
            """)
        
        with c2:
            st.success("✅ **The AuraLearn Solution**")
            st.markdown("""
            We add an **Emotional Intelligence Layer** to AI.
            * **Confused?** The AI simplifies concepts using analogies (ELI5).
            * **Sleepy?** It stops the lesson to run a physical "Brain Boost" activity.
            * **Happy?** It challenges you to flow deeper into the topic.
            """)

        st.divider()

        # 3. KEY CAPABILITIES
        st.subheader("🌟 System Capabilities")
        
        st.markdown("""
        * **📚 Instant Document Mastery:** Upload any PDF textbook, and AuraLearn ingests it instantly for Q&A and Quizzing.
        * **🗣️ Bi-Directional Voice:** Speak to your tutor naturally and hear human-like audio explanations.
        * **🧠 Cognitive State Tracking:** The system remembers your confusion points and adjusts future quizzes to target your weak spots.
        * **☁️ Cloud Sync:** Your progress, badges, and chat history are saved securely in the cloud via Firebase.
        """)
        
        st.divider()
        
        # # 4. TECH STACK
        # with st.expander("🛠️ Under the Hood (Tech Stack)"):
        #     st.markdown("""
        #     * **Frontend:** Streamlit (Python)
        #     * **AI Engine:** Groq (Llama 3 70B) + LangChain
        #     * **Backend & Auth:** Google Firebase (Realtime Database)
        #     * **Voice:** SpeechRecognition (STT) & gTTS (Text-to-Speech)
        #     * **Data Processing:** PyPDF2 & PDFPlumber
        #     """)

       

        # 5. FEEDBACK FORM (Integrated)
        st.subheader("💌 We Value Your Feedback")
        st.write("Help us improve AuraLearn! Share your experience, report bugs, or suggest features.")
        
        # Display as a styled link button
        st.link_button("📝 Fill out Feedback Form", "https://docs.google.com/forms/d/e/1FAIpQLSftRzHkjcZSlfU8knlO6gGlumZWCYsCC7pFxdT-g2_IlDUOaw/viewform")

        st.caption("© 2025 AuraLearn Project. Built for the Future of Education.")

# ==========================
# 7. RUN
# ==========================
if st.session_state.user:
    main_app()
else:
    auth_screen()