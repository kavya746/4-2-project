import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from database import create_connection


def patient_reports_page(patient_id=None):

    st.title("🩺Health Reports")

    conn = create_connection()
    cursor = conn.cursor(buffered=True)

    # patient_id = st.session_state.user_id
    if patient_id is None:
        patient_id = st.session_state.user_id

    cursor.execute("""
    SELECT prediction_type, prediction_result, created_at
    FROM patient_reports
    WHERE patient_id=%s
    ORDER BY created_at
    """, (patient_id,))

    data = cursor.fetchall()

    if not data:
        st.info("No reports available yet.")
        return

    df = pd.DataFrame(
        data,
        columns=["Prediction Type", "Result", "Date"]
    )

    # ---------------- SUMMARY ---------------- #

    col1, col2 = st.columns(2)

    col1.metric("Total Reports", len(df))
    col2.metric("Latest Result", df.iloc[-1]["Result"])

    st.divider()

    # ---------------- TABS ---------------- #

    tab1, tab2 = st.tabs(["Pregnancy Risk", "Fetal Health"])

    # =========================================================
    # TAB 1 : PREGNANCY RISK
    # =========================================================

    with tab1:

        preg_df = df[df["Prediction Type"] == "pregnancy_risk"]

        if preg_df.empty:
            st.info("No Pregnancy Risk reports available.")
        else:

            st.subheader("Pregnancy Risk History")

            st.dataframe(preg_df, use_container_width=True)

            risk_map = {
                "Low Risk": 0,
                "Medium Risk": 1,
                "High Risk": 2
            }

            preg_df["Risk_Value"] = preg_df["Result"].map(risk_map)

            col1, col2 = st.columns(2)

            # Trend Chart
            with col1:

                st.subheader("Risk Trend")

                fig, ax = plt.subplots()

                ax.plot(preg_df["Date"], preg_df["Risk_Value"], marker="o")

                ax.set_ylabel("Risk Level")
                ax.set_xlabel("Date")

                ax.set_yticks([0,1,2])
                ax.set_yticklabels(["Low","Medium","High"])

                st.pyplot(fig)

            # Pie Chart
            with col2:

                st.subheader("Risk Distribution")

                risk_counts = preg_df["Result"].value_counts()

                fig2, ax2 = plt.subplots()

                ax2.pie(
                    risk_counts,
                    labels=risk_counts.index,
                    autopct="%1.1f%%"
                )

                st.pyplot(fig2)

    # =========================================================
    # TAB 2 : FETAL HEALTH
    # =========================================================

    with tab2:

        fetal_df = df[df["Prediction Type"] == "fetal_health"]

        if fetal_df.empty:
            st.info("No Fetal Health reports available.")
        else:

            st.subheader("Fetal Health Prediction History")

            st.dataframe(fetal_df, use_container_width=True)

            col1, col2 = st.columns(2)

            # Distribution Chart
            with col1:

                st.subheader("Health Distribution")

                fetal_counts = fetal_df["Result"].value_counts()

                fig3, ax3 = plt.subplots()

                ax3.pie(
                    fetal_counts,
                    labels=fetal_counts.index,
                    autopct="%1.1f%%"
                )

                st.pyplot(fig3)

            # Trend Chart
            with col2:

                st.subheader("Health Trend")

                fetal_map = {
                    "Normal": 0,
                    "Suspect": 1,
                    "Pathological": 2
                }

                fetal_df["Health_Value"] = fetal_df["Result"].map(fetal_map)

                fig4, ax4 = plt.subplots()

                ax4.plot(fetal_df["Date"], fetal_df["Health_Value"], marker="o")

                ax4.set_ylabel("Health Level")
                ax4.set_xlabel("Date")

                ax4.set_yticks([0,1,2])
                ax4.set_yticklabels(["Normal","Suspect","Pathological"])

                st.pyplot(fig4)