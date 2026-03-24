import warnings
warnings.filterwarnings("ignore")
import streamlit as st
import bcrypt
import re
import base64
from database import create_connection

from dashboard.patient_dashboard import patient_dashboard
from dashboard.doctor_dashboard import doctor_dashboard

st.set_page_config(page_title="Maternal Care AI", page_icon="🩺")

# ---------- BACKGROUND IMAGE ----------
def set_bg(image_file):
    with open(image_file, "rb") as f:
        data = f.read()

    encoded = base64.b64encode(data).decode()

    css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    </style>
    """

    st.markdown(css, unsafe_allow_html=True)

set_bg("gradient_bg.png")


# ---------- CSS ----------
st.markdown("""
<style>

/* Title */
.title {
    text-align: center;
    font-size: 42px;
    font-weight: bold;
    margin-top: -10px;
}

/* Form Box */
.form-box {
    background-color: rgba(255,255,255,0.9);
    padding: 50px;
    border-radius: 15px;
    box-shadow: 0px 0px 15px rgba(0,0,0,0.2);
}

/* Buttons */
div.stButton > button {
    border-radius: 8px;
    height: 2.8em;
    font-weight: bold;
}

/* Green buttons */
button[kind="primary"] {
    background-color: #28a745 !important;
    color: white !important;
}

</style>
""", unsafe_allow_html=True)


# ---------- SESSION ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.name = None
    st.session_state.user_id = None


# ---------- DATABASE ----------
connection = create_connection()
cursor = connection.cursor()


# ---------- VALIDATIONS ----------
def is_valid_password(password):

    if len(password) < 8:
        return False, "Password must be at least 8 characters"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain uppercase letter"

    if not re.search(r"[0-9]", password):
        return False, "Password must contain number"

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain special character"

    return True, "Valid Password"


def is_valid_email(email):
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.com$"
    return re.fullmatch(pattern, email) is not None


# ================= AUTH =================

if not st.session_state.logged_in:

    # ---------- DOCTOR IMAGE ----------
    c1, c2, c3 = st.columns([1.3,1,1])

    with c2:
        st.image("doctor.png", width=130)

    # ---------- TITLE ----------
    st.markdown('<p class="title">Maternal Care AI</p>', unsafe_allow_html=True)


    col1, col2, col3 = st.columns([1,3,1])

    with col2:

        #st.markdown('<div class="form-box">', unsafe_allow_html=True)

        menu = ["Login", "Signup"]
        choice = st.selectbox("Select Option", menu)

        # ---------- SIGNUP ----------
        if choice == "Signup":

            st.subheader("Create Account")

            name = st.text_input("Name *")
            email = st.text_input("Email *")
            password = st.text_input("Password *", type="password")
            confirm_password = st.text_input("Confirm Password *", type="password")

            role = st.selectbox("Register As *", ["doctor", "patient"])

            specialization = None
            if role == "doctor":
                specialization = st.text_input("Specialization *")

            b1,b2,b3 = st.columns([1,1,1])

            with b2:
                signup_clicked = st.button("Signup", type="primary")

            if signup_clicked:

                name = name.strip()
                email = email.strip()

                if not name or not email or not password or not confirm_password:
                    st.error("All fields required")

                elif role == "doctor" and (specialization is None or specialization.strip() == ""):
                    st.error("Specialization required")

                elif not is_valid_email(email):
                    st.error("Invalid email")

                elif password != confirm_password:
                    st.error("Passwords do not match")

                else:

                    valid, msg = is_valid_password(password)

                    if not valid:
                        st.error(msg)

                    else:

                        try:

                            hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

                            cursor.execute(
                                "INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
                                (name,email,hashed_pw,role)
                            )

                            connection.commit()

                            user_id = cursor.lastrowid

                            if role == "patient":

                                cursor.execute(
                                    "INSERT INTO patients (patient_id,name,email) VALUES (%s,%s,%s)",
                                    (user_id,name,email)
                                )

                            else:

                                cursor.execute(
                                    "INSERT INTO doctors (doctor_id,name,email,specialization) VALUES (%s,%s,%s,%s)",
                                    (user_id,name,email,specialization)
                                )

                            connection.commit()

                            st.success("Account created successfully. Please login.")

                        except:
                            st.error("Email already exists")


        # ---------- LOGIN ----------
        if choice == "Login":

            st.subheader("Login")

            email = st.text_input("Email")
            password = st.text_input("Password", type="password")

            b1,b2,b3 = st.columns([1,1,1])

            with b2:
                login_clicked = st.button("Login", type="primary")

            if login_clicked:

                email = email.strip()

                if not email or not password:
                    st.error("All fields required")

                elif not is_valid_email(email):
                    st.error("Invalid email")

                else:

                    cursor.execute("SELECT * FROM users WHERE email=%s",(email,))
                    user = cursor.fetchone()

                    if user:

                        if bcrypt.checkpw(password.encode(), user[3].encode()):

                            st.session_state.logged_in = True
                            st.session_state.user_id = user[0]
                            st.session_state.name = user[1]
                            st.session_state.role = user[4]

                            st.rerun()

                        else:
                            st.error("Incorrect password")

                    else:
                        st.error("User not found")

        st.markdown('</div>', unsafe_allow_html=True)


# ================= DASHBOARD =================

else:

    if st.session_state.role == "patient":
        patient_dashboard()

    elif st.session_state.role == "doctor":
        doctor_dashboard()