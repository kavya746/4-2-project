import streamlit as st
import joblib
import pandas as pd
import pdfplumber
import re
import base64
from database import create_connection

# =============================
# LOAD MODEL
# =============================
preg_model = joblib.load("models/finalized_maternal_model.joblib")
scaler = joblib.load("models/maternal_scaler.joblib")

# =============================
# PDF VALUE EXTRACTION
# =============================
def extract_value(pattern, text, default=None):
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1)) if match else default


def pregnancy_risk_page():

    st.title("Pregnancy Risk Prediction")

    conn = create_connection()
    cursor = conn.cursor(buffered=True)

    role = st.session_state.role

    # =============================
    # PATIENT SELECTION
    # =============================
    if role == "doctor":

        doctor_id = st.session_state.user_id

        cursor.execute("""
        SELECT p.patient_id, p.name, p.email
        FROM connection_requests c
        JOIN patients p ON c.patient_id = p.patient_id
        WHERE c.doctor_id=%s AND c.status='accepted'
        """, (doctor_id,))

        patients = cursor.fetchall()

        if not patients:
            st.warning("No connected patients found.")
            return

        patient_options = {
            f"{name} ({email})": pid
            for pid, name, email in patients
        }

        selected_patient = st.selectbox("Select Patient", list(patient_options.keys()))
        patient_id = patient_options[selected_patient]

    else:

        patient_id = st.session_state.user_id

        cursor.execute("""
        SELECT doctor_id
        FROM connection_requests
        WHERE patient_id=%s AND status='accepted'
        """, (patient_id,))

        doctor = cursor.fetchone()
        doctor_id = doctor[0] if doctor else None

    st.markdown("---")

    # =============================
    # INPUT METHOD
    # =============================
    input_method = st.selectbox(
        "Select Input Method",
        ["Manual Entry", "Upload PDF Report"]
    )

    st.markdown("---")

    # =============================
    # MANUAL ENTRY UI
    # =============================
    if input_method == "Manual Entry":

        col1, col2, col3 = st.columns(3)

        with col1:
            age = st.text_input("Age of the Person")

        with col2:
            systolic_bp = st.text_input("Systolic BP in mmHg")

        with col3:
            diastolic_bp = st.text_input("Diastolic BP in mmHg")

        with col1:
            bs = st.text_input("Blood Glucose Level in mmol/L")

        with col2:
            body_temp = st.text_input("Body Temperature in Fahrenheit")

        with col3:
            heart_rate = st.text_input("Heart Rate (bpm)")

        btn1, btn2 = st.columns(2)

        with btn1:
            predict = st.button("Predict Pregnancy Risk", type="primary")

        with btn2:
            clear = st.button("Clear", type="secondary")

        if clear:
            st.rerun()

    # =============================
    # PDF UPLOAD FLOW
    # =============================
    else:

        uploaded_file = st.file_uploader("Upload Pregnancy Report", type=["pdf"])

        predict = False
        extracted = {}

        if uploaded_file:

            # ---------- PDF PREVIEW ----------
            base64_pdf = base64.b64encode(uploaded_file.read()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="400"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)

            uploaded_file.seek(0)

            # ---------- EXTRACT TEXT ----------
            text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    text += page.extract_text()

            st.success("Values extracted from report!")

            # ---------- EXTRACT VALUES ----------
            extracted = {
                "Age": extract_value(r'Age.*?(\d+)', text),
                "SystolicBP": extract_value(r'Systolic BP.*?(\d+)', text),
                "DiastolicBP": extract_value(r'Diastolic BP.*?(\d+)', text),
                "BS": extract_value(r'Blood Glucose.*?([\d.]+)', text),
                "BodyTemp": extract_value(r'Body Temperature.*?([\d.]+)', text),
                "HeartRate": extract_value(r'Heart Rate.*?(\d+)', text),
            }

            # ---------- SHOW EXTRACTED VALUES ----------
            st.subheader("Extracted Values")
            st.json(extracted)

            predict = st.button("Predict from Report", type="primary")

    # =============================
    # COMMON PREDICTION LOGIC
    # =============================
    if predict:

        try:

            if input_method == "Manual Entry":

                input_data = pd.DataFrame({
                    "Age": [float(age)],
                    "SystolicBP": [float(systolic_bp)],
                    "DiastolicBP": [float(diastolic_bp)],
                    "BS": [float(bs)],
                    "BodyTemp": [float(body_temp)],
                    "HeartRate": [float(heart_rate)]
                })

            else:
                input_data = pd.DataFrame([extracted])

            input_scaled = scaler.transform(input_data)
            prediction = preg_model.predict(input_scaled)

            st.subheader("Risk Level")

            if prediction[0] == 0:
                result = "Low Risk"
                st.success("🟢 Low Risk")
            elif prediction[0] == 1:
                result = "Medium Risk"
                st.warning("🟡 Medium Risk")
            else:
                result = "High Risk"
                st.error("🔴 High Risk")

            # =============================
            # SAVE TO DB
            # =============================
            input_text = str(input_data.to_dict())

            cursor.execute("""
            INSERT INTO patient_reports
            (patient_id, doctor_id, prediction_type, prediction_result, input_data)
            VALUES (%s,%s,%s,%s,%s)
            """,
            (patient_id, doctor_id, "pregnancy_risk", result, input_text))

            conn.commit()

            st.success("Prediction saved successfully!")

        except Exception as e:
            st.error("Error in prediction. Check input data.")