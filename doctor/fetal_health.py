import streamlit as st
import joblib
import pandas as pd
import pdfplumber
import re
import base64
from database import create_connection

# Load model and scaler
fetal_model = joblib.load("models/fetal_health_model.joblib")
scaler = joblib.load("models/fetal_scaler.joblib")


# ---------------------------
# PDF Preview
# ---------------------------
def show_pdf(file):
    base64_pdf = base64.b64encode(file.read()).decode('utf-8')
    pdf_display = f"""
        <iframe src="data:application/pdf;base64,{base64_pdf}" 
        width="100%" height="600px"></iframe>
    """
    st.markdown(pdf_display, unsafe_allow_html=True)


# ---------------------------
# Robust Extract Function (FIXED)
# ---------------------------
def extract_value(pattern, text, default=0):
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        for g in reversed(match.groups()):
            if g is not None and re.match(r'^-?\d+(\.\d+)?$', g):
                return float(g)
    return default


def fetal_health_page():

    conn = create_connection()
    cursor = conn.cursor(buffered=True)
    doctor_id = st.session_state.user_id

    st.title("Fetal Health Prediction")
    st.markdown(
        "<b>Cardiotocograms (CTGs) help assess fetal health and prevent risks.</b>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    # =============================
    # Patient Selection
    # =============================
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

    st.markdown("---")

    # =============================
    # Input Method
    # =============================
    input_method = st.selectbox(
        "Select Input Method",
        ["Manual Entry", "Upload CTG Report (PDF)"]
    )

    # =============================
    # MANUAL ENTRY (UNCHANGED)
    # =============================
    if input_method == "Manual Entry":

        col1, col2, col3 = st.columns(3)

        with col1:
            BaselineValue = st.number_input("Baseline Value", 80.0, 200.0, 120.0)
            uterine_contractions = st.number_input("Uterine Contractions", 0.0, 1.0, 0.002, step=0.001)
            prolongued_decelerations = st.number_input("Prolongued Decelerations", 0.0, 1.0, 0.0, step=0.001)
            percentage_of_time_with_abnormal_long_term_variability = st.number_input("Percentage Of Time With ALTV", 0.0, 100.0, 10.0)
            histogram_width = st.number_input("Histogram Width", 0.0, 200.0, 70.0)
            histogram_number_of_zeroes = st.number_input("Histogram Number Of Zeroes", 0.0, 10.0, 0.0)
            histogram_median = st.number_input("Histogram Median", 0.0, 200.0, 120.0)

        with col2:
            Accelerations = st.number_input("Accelerations", 0.0, 1.0, 0.001, step=0.001)
            light_decelerations = st.number_input("Light Decelerations", 0.0, 1.0, 0.001, step=0.001)
            abnormal_short_term_variability = st.number_input("Abnormal Short Term Variability", 0.0, 100.0, 20.0)
            mean_value_of_long_term_variability = st.number_input("Mean Long Term Variability", 0.0, 50.0, 8.0)
            histogram_min = st.number_input("Histogram Min", 0.0, 200.0, 80.0)
            histogram_mode = st.number_input("Histogram Mode", 0.0, 200.0, 120.0)
            histogram_variance = st.number_input("Histogram Variance", 0.0, 200.0, 20.0)

        with col3:
            fetal_movement = st.number_input("Fetal Movement", 0.0, 1.0, 0.01, step=0.001)
            severe_decelerations = st.number_input("Severe Decelerations", 0.0, 1.0, 0.0, step=0.001)
            mean_value_of_short_term_variability = st.number_input("Mean Value Short Term Variability", 0.0, 10.0, 1.5)
            histogram_max = st.number_input("Histogram Max", 0.0, 250.0, 160.0)
            histogram_number_of_peaks = st.number_input("Histogram Number Of Peaks", 0.0, 10.0, 3.0)
            histogram_mean = st.number_input("Histogram Mean", 0.0, 200.0, 120.0)
            histogram_tendency = st.number_input("Histogram Tendency (-1,0,1)", -1, 1, 0)

        predict_button = st.button("Predict Fetal Health")

    # =============================
    # PDF UPLOAD
    # =============================
    else:
        uploaded_file = st.file_uploader("Upload CTG Report", type=["pdf"])
        predict_button = False

        if uploaded_file:
            st.success("PDF Uploaded Successfully")

            # Preview
            show_pdf(uploaded_file)

            # Reset pointer
            uploaded_file.seek(0)

            with pdfplumber.open(uploaded_file) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text()

            st.text_area("Extracted Text", text, height=200)

            # =============================
            # EXTRACTION (ROBUST)
            # =============================
            BaselineValue = extract_value(r'Baseline Value.*?(\d+)', text)
            Accelerations = extract_value(r'Accelerations.*?([\d.]+)', text)
            fetal_movement = extract_value(r'Fetal Movement.*?([\d.]+)', text)
            uterine_contractions = extract_value(r'Uterine Contractions.*?([\d.]+)', text)
            light_decelerations = extract_value(r'Light Decelerations.*?([\d.]+)', text)
            severe_decelerations = extract_value(r'Severe Decelerations.*?([\d.]+)', text)
            prolongued_decelerations = extract_value(r'Prolongued Decelerations.*?([\d.]+)', text)
            abnormal_short_term_variability = extract_value(r'Abnormal Short Term Variability.*?(\d+)', text)
            mean_value_of_short_term_variability = extract_value(r'Mean.*Short Term Variability.*?([\d.]+)', text)

            # ✅ FIXED ALTV (NO ERROR)
            percentage_of_time_with_abnormal_long_term_variability = extract_value(
                r'Percentage.*ALTV.*?(\d+)|Percentage.*Long Term Variability.*?(\d+)', text
            )

            mean_value_of_long_term_variability = extract_value(r'Mean Long Term Variability.*?([\d.]+)', text)
            histogram_width = extract_value(r'Histogram Width.*?(\d+)', text)
            histogram_min = extract_value(r'Histogram Min.*?(\d+)', text)
            histogram_max = extract_value(r'Histogram Max.*?(\d+)', text)
            histogram_number_of_peaks = extract_value(r'Histogram Number Of Peaks.*?(\d+)', text)
            histogram_number_of_zeroes = extract_value(r'Histogram Number Of Zeroes.*?(\d+)', text)
            histogram_mode = extract_value(r'Histogram Mode.*?(\d+)', text)
            histogram_mean = extract_value(r'Histogram Mean.*?(\d+)', text)
            histogram_median = extract_value(r'Histogram Median.*?(\d+)', text)
            histogram_variance = extract_value(r'Histogram Variance.*?(\d+)', text)
            histogram_tendency = extract_value(r'Histogram Tendency.*?(-?\d+)', text)

            predict_button = st.button("Predict from Report")

    # =============================
    # PREDICTION
    # =============================
    if predict_button:

        input_data = pd.DataFrame({
            "baseline value":[BaselineValue],
            "accelerations":[Accelerations],
            "fetal_movement":[fetal_movement],
            "uterine_contractions":[uterine_contractions],
            "light_decelerations":[light_decelerations],
            "severe_decelerations":[severe_decelerations],
            "prolongued_decelerations":[prolongued_decelerations],
            "abnormal_short_term_variability":[abnormal_short_term_variability],
            "mean_value_of_short_term_variability":[mean_value_of_short_term_variability],
            "percentage_of_time_with_abnormal_long_term_variability":[percentage_of_time_with_abnormal_long_term_variability],
            "mean_value_of_long_term_variability":[mean_value_of_long_term_variability],
            "histogram_width":[histogram_width],
            "histogram_min":[histogram_min],
            "histogram_max":[histogram_max],
            "histogram_number_of_peaks":[histogram_number_of_peaks],
            "histogram_number_of_zeroes":[histogram_number_of_zeroes],
            "histogram_mode":[histogram_mode],
            "histogram_mean":[histogram_mean],
            "histogram_median":[histogram_median],
            "histogram_variance":[histogram_variance],
            "histogram_tendency":[histogram_tendency]
        })

        # Handle missing
        input_data = input_data.fillna(0)

        st.write("Extracted Data:", input_data)

        input_scaled = scaler.transform(input_data)

        predicted = fetal_model.predict(input_scaled)
        probs = fetal_model.predict_proba(input_scaled)

        if predicted[0] == 1:
            result_text = "Normal"
            st.success("🟢 Normal")
        elif predicted[0] == 2:
            result_text = "Suspect"
            st.warning("🟡 Suspect")
        else:
            result_text = "Pathological"
            st.error("🔴 Pathological")

        st.write(f"Normal: {probs[0][0]:.2f}")
        st.write(f"Suspect: {probs[0][1]:.2f}")
        st.write(f"Pathological: {probs[0][2]:.2f}")

        # Save
        cursor.execute("""
            INSERT INTO patient_reports
            (patient_id, doctor_id, prediction_type, prediction_result, input_data)
            VALUES (%s,%s,%s,%s,%s)
        """, (patient_id, doctor_id, "fetal_health", result_text, input_data.to_json()))

        conn.commit()

        st.success("Prediction saved successfully!")