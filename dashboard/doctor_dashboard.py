import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from database import create_connection
from streamlit_option_menu import option_menu
from patient.pregnancy_risk import pregnancy_risk_page
from doctor.fetal_health import fetal_health_page
from doctor.doctor_connections import doctor_connections_page
from patient.patient_reports import patient_reports_page


def doctor_dashboard():

    with st.sidebar:
        selected = option_menu(
            "Doctor Panel",
            ["Dashboard", "Connections", "Pregnancy Risk", "Fetal Health", "Logout"],
            icons=["clipboard-data", "people", "activity", "heart", "box-arrow-right"],
            default_index=0
        )

    # ================= DASHBOARD =================

    if selected == "Dashboard":

        conn = create_connection()
        cursor = conn.cursor(buffered=True)
        doctor_id = st.session_state.user_id

        # -------- If doctor clicked patient --------

        if "selected_patient" in st.session_state:

            if st.button("⬅ Back to Dashboard"):
                del st.session_state.selected_patient
                st.rerun()

            patient_reports_page(st.session_state.selected_patient)
            return

        # -------- Welcome --------

        st.title(f"Welcome Dr. {st.session_state.name}")

        # -------- Total patients --------

        cursor.execute("""
        SELECT COUNT(*)
        FROM connection_requests
        WHERE doctor_id=%s AND status='accepted'
        """,(doctor_id,))

        total_patients = cursor.fetchone()[0]

        st.metric("Total Connected Patients", total_patients)

        st.divider()

        # -------- PATIENT LIST --------

        st.subheader("👩‍⚕️ My Patients")

        cursor.execute("""
        SELECT p.patient_id,p.name
        FROM connection_requests c
        JOIN patients p ON c.patient_id=p.patient_id
        WHERE c.doctor_id=%s AND c.status='accepted'
        """,(doctor_id,))

        patients = cursor.fetchall()

        cols = st.columns(3)

        for i,(pid,name) in enumerate(patients):

            with cols[i % 3]:

                with st.container(border=True):

                    st.write(f"### {name}")

                    if st.button("View Reports", key=pid):

                        st.session_state.selected_patient = pid
                        st.rerun()

        st.divider()

        # -------- FETCH ALL REPORTS --------

        cursor.execute("""
        SELECT p.name,r.prediction_result,r.created_at
        FROM patient_reports r
        JOIN patients p ON r.patient_id = p.patient_id
        WHERE r.doctor_id=%s
        ORDER BY r.created_at
        """,(doctor_id,))

        reports = cursor.fetchall()

        if reports:

            df = pd.DataFrame(
                reports,
                columns=["Patient","Result","Date"]
            )

            st.subheader("📊 Overall Patient Analytics")

            risk_map = {
                "Low Risk":0,
                "Medium Risk":1,
                "High Risk":2
            }

            df["Risk_Value"] = df["Result"].map(risk_map)

            col1, col2 = st.columns(2)

            # -------- PIE CHART --------

            with col1:

                st.write("Risk Distribution")

                risk_counts = df["Result"].value_counts()

                fig2, ax2 = plt.subplots()

                ax2.pie(
                    risk_counts,
                    labels=risk_counts.index,
                    autopct="%1.1f%%"
                )

                st.pyplot(fig2)

            # -------- LINE CHART --------

            with col2:

                st.write("Risk Trend")

                fig, ax = plt.subplots()

                ax.plot(df["Date"], df["Risk_Value"], marker="o")

                ax.set_ylabel("Risk Level")
                ax.set_xlabel("Date")

                ax.set_yticks([0,1,2])
                ax.set_yticklabels(["Low","Medium","High"])

                st.pyplot(fig)

        else:

            st.info("No patient reports available yet.")

    # ================= CONNECTIONS =================

    elif selected == "Connections":
        doctor_connections_page()

    # ================= PREGNANCY RISK =================

    elif selected == "Pregnancy Risk":
        pregnancy_risk_page()

    # ================= FETAL HEALTH =================

    elif selected == "Fetal Health":
        fetal_health_page()

    # ================= LOGOUT =================

    elif selected == "Logout":

        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.name = None
        st.rerun()