import streamlit as st
import pyrebase
import json
from pathlib import Path
from modules.pdf_processor import extract_text_from_pdf

# ======================
# Page Settings + Global CSS
# ======================
st.set_page_config(page_title="AuraLearn", page_icon="🧠", layout="wide")

# Custom CSS Styling
st.markdown("""
<style>

/* ---------- Navbar ---------- */
.navbar {
    background: linear-gradient(90deg, #6a11cb, #2575fc);
    padding: 18px;
    border-radius: 10px;
    margin-bottom: 25px;
}

.nav-item {
    color: white !important;
    font-size: 20px;
    font-weight: 600;
    padding: 0px 25px;
    text-decoration: none;
}

.nav-item:hover {
    color: #d6e9ff !important;
}

/* Centered Card Styling */
.card {
    background: linear-gradient(180deg, #b7e1ff, #e9c7ff);
    padding: 40px;
    border-radius: 20px;
    width: 65%;
    margin-left: auto;
    margin-right: auto;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.2);
}

/* Inputs */
input, textarea {
    border-radius: 15px !important;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(90deg, #6a11cb, #2575fc);
    color: white;
    border-radius: 12px;
    padding: 10px 20px;
    font-size: 18px;
    font-weight: 600;
}

.stButton>button:hover {
    opacity: 0.9;
}

/* Headers */
h1, h2, h3 {
    font-weight: 800;
}

/* Center Text */
.center {
    text-align: center;
}

</style>
""", unsafe_allow_html=True)


# ======================
# Load Firebase Config
# ======================
config_path = Path("config/firebase_config.json")
if not config_path.exists():
    st.error("Firebase config file not found! Add 'firebase_config.json' inside /config folder.")
    st.stop()

with open(config_path) as f:
    firebaseConfig = json.load(f)

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

if "user" not in st.session_state:
    st.session_state.user = None


# ======================
# Navbar UI
# ======================
st.markdown("""
<div class="navbar">
    <span style="color:white; font-size:28px; font-weight:700; margin-right:50px;">
        AuraLearn
    </span>
</div>
""", unsafe_allow_html=True)



# ======================
# Sidebar Navigation
# ======================
if st.session_state.user:
    choice = st.sidebar.radio("Navigation", ["Upload Notes", "Live Emotion Session", "Logout"])
else:
    choice = st.sidebar.radio("Navigation", ["Login", "Signup", "Forgot Password"])




# ======================
# LOGIN PAGE
# ======================
if choice == "Login":
    st.markdown("<h2 class='center'>Login to Your Account</h2>", unsafe_allow_html=True)

    with st.container():
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                try:
                    user = auth.sign_in_with_email_and_password(email, password)
                    st.session_state.user = user
                    st.success("Login Successful 🎉")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")

    if st.session_state.user:
        st.info(f"Logged in as **{st.session_state.user['email']}**")


# ======================
# SIGNUP PAGE
# ======================
elif choice == "Signup":
    st.markdown("<h2 class='center'>Create Your AuraLearn Account</h2>", unsafe_allow_html=True)

    with st.container():
        with st.form("signup_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Create Account")

            if submit:
                if password != confirm_password:
                    st.error("Passwords do not match ❌")
                elif len(password) < 6:
                    st.warning("Password must be at least 6 characters.")
                else:
                    try:
                        user = auth.create_user_with_email_and_password(email, password)
                        st.success("Account Created 🎉")
                        st.info("Go to Login to continue.")
                    except Exception as e:
                        st.error(f"Error: {e}")


# ======================
# FORGOT PASSWORD
# ======================
elif choice == "Forgot Password":
    st.markdown("<h2 class='center'>Reset Your Password</h2>", unsafe_allow_html=True)

    email = st.text_input("Your Registered Email")

    if st.button("Send Reset Link"):
        try:
            auth.send_password_reset_email(email)
            st.info("Reset link sent to your email.")
        except Exception as e:
            st.error(f"Error: {e}")


# ======================
# UPLOAD NOTES PAGE
# ======================
elif choice == "Upload Notes" and st.session_state.user:
    st.markdown("<h2 class='center'>📘 Upload Your Study Notes</h2>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_file:
        with st.spinner("Extracting text from PDF..."):
            extracted_text = extract_text_from_pdf(uploaded_file)

        st.success("Extraction Complete ✔️")

        st.text_area("Extracted Text", extracted_text, height=400)

        st.download_button(
            "Download Extracted Notes",
            extracted_text,
            file_name="notes.txt",
            mime="text/plain"
        )


# ======================
# LOGOUT
# ======================
if choice == "Logout":
    st.session_state.user = None
    st.success("Logged out successfully.")
