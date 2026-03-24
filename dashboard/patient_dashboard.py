import streamlit as st
from streamlit_option_menu import option_menu

from patient.pregnancy_risk import pregnancy_risk_page
# from features.fetal_health import fetal_health_page
from patient.chatbot import chatbot_page
from patient.patient_connections import patient_connections_page
from patient.patient_reports import patient_reports_page

def patient_dashboard():

    with st.sidebar:
        selected = option_menu(
            "Patient Panel",
            ["Dashboard", "Pregnancy Risk", "Connections", "Chatbot", "Logout"],
            icons=["info-circle", "activity", "people", "chat", "box-arrow-right"],
            default_index=0
            )

    if selected == "Dashboard":
        st.title(f"Welcome {st.session_state.name}")
        patient_reports_page()
        # st.title(f"Welcome {st.session_state.name}")
        # st.write("This is your patient dashboard.")

    elif selected == "Pregnancy Risk":
        pregnancy_risk_page()

    # elif selected == "Fetal Health":
    #     fetal_health_page()

    elif selected == "Connections":
        patient_connections_page()

    elif selected == "Chatbot":
        chatbot_page()

    elif selected == "Logout":
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.name = None
        st.rerun()