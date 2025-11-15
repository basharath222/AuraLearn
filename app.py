import streamlit as st
import pyrebase
import json
from pathlib import Path
from modules.pdf_processor import extract_text_from_pdf

# ======================
# 🔧 Load Firebase Config
# ======================
config_path = Path("config/firebase_config.json")
if not config_path.exists():
    st.error("Firebase config file not found! Please add 'firebase_config.json' under /config folder.")
    st.stop()

with open(config_path) as f:
    firebaseConfig = json.load(f)

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# ======================
# 🧠 Session Management
# ======================
if "user" not in st.session_state:
    st.session_state.user = None

st.set_page_config(page_title="AuraLearn", page_icon="🧠", layout="centered")

st.title("🧠 AuraLearn - Smart Learning Companion")
st.write("Welcome to **AuraLearn**, your Emotion-Aligned AI Tutor and Context-Aware Study Companion!")

# ======================
# 🔐 Sidebar Navigation
# ======================
if st.session_state.user:
    choice = st.sidebar.radio("Navigation", ["Upload Notes", "Logout"])
else:
    choice = st.sidebar.radio("Navigation", ["Login", "Signup", "Forgot Password"])

# ======================
# 🔑 LOGIN SECTION
# ======================
if choice == "Login":
    st.subheader("Login to Your Account")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state.user = user
            st.success("Logged in Successfully ✅")
            st.balloons()
        except Exception as e:
            st.error(f"Error: {e}")

    if st.session_state.user:
        st.info(f"Logged in as: {st.session_state.user['email']}")
        st.success("Proceed to upload your notes and start learning!")

# ======================
# 🆕 SIGNUP SECTION
# ======================
elif choice == "Signup":
    st.subheader("Create a New Account")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Create Account"):
        if password != confirm_password:
            st.error("Passwords do not match ❌")
        elif len(password) < 6:
            st.warning("Password should be at least 6 characters long.")
        else:
            try:
                user = auth.create_user_with_email_and_password(email, password)
                st.success("Account created successfully ✅")
                st.info("Now go to the Login section to sign in.")
            except Exception as e:
                st.error(f"Error: {e}")

# ======================
# 🔄 FORGOT PASSWORD SECTION
# ======================
elif choice == "Forgot Password":
    st.subheader("Reset Your Password")
    email = st.text_input("Enter your registered email")

    if st.button("Send Reset Email"):
        try:
            auth.send_password_reset_email(email)
            st.info("Password reset link sent to your email. Check your spam folder.")
        except Exception as e:
            st.error(f"Error: {e}")

# ======================
# 📚 UPLOAD NOTES SECTION
# ======================
elif choice == "Upload Notes":
    if st.session_state.user:
        st.subheader("📘 Upload Your Study Notes (PDF)")
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

        if uploaded_file:
            with st.spinner("Extracting text..."):
                text = extract_text_from_pdf(uploaded_file)
            st.success("Text extraction complete ✅")

            # Display extracted text in a scrollable text area
            st.text_area("📄 Extracted Content", text, height=400)

            # Optionally, allow download
            st.download_button(
                label="Download Extracted Text",
                data=text,
                file_name="extracted_notes.txt",
                mime="text/plain"
            )
        else:
            st.info("Please upload a PDF file to begin.")
    else:
        st.warning("Please log in to access this feature.")

# ======================
# 🚪 LOGOUT
# ======================
if choice == "Logout":
    if st.session_state.user:
        st.session_state.user = None
        st.success("You have been logged out successfully.")
