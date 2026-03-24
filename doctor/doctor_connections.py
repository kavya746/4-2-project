import streamlit as st
from database import create_connection

def doctor_connections_page():

    st.title("Patient Connections")

    conn = create_connection()
    cursor = conn.cursor()

    doctor_id = st.session_state.user_id

     # ---------------- MY PATIENTS ---------------- #

    st.subheader("My Patients")

    cursor.execute("""
        SELECT p.name
        FROM connection_requests r
        JOIN patients p ON r.patient_id = p.patient_id
        WHERE r.doctor_id=%s AND r.status='accepted'
    """,(doctor_id,))

    patients = cursor.fetchall()

    if not patients:
        st.info("No patients connected yet")

    for patient in patients:
        st.success(patient[0])

    # ---------------- PENDING REQUESTS ---------------- #

    st.subheader("Pending Requests")

    cursor.execute("""
        SELECT r.request_id,p.name
        FROM connection_requests r
        JOIN patients p ON r.patient_id = p.patient_id
        WHERE r.doctor_id=%s AND r.status='pending'
    """,(doctor_id,))

    requests = cursor.fetchall()

    if not requests:
        st.info("No pending requests")

    for req in requests:

        request_id = req[0]
        patient_name = req[1]

        col1,col2,col3 = st.columns([3,1,1])

        col1.write(patient_name)

        if col2.button("Accept",key=f"a{request_id}"):

            cursor.execute(
                "UPDATE connection_requests SET status='accepted' WHERE request_id=%s",
                (request_id,)
            )

            conn.commit()
            st.success("Request accepted")
            st.rerun()

        if col3.button("Reject",key=f"r{request_id}"):

            cursor.execute(
                "UPDATE connection_requests SET status='rejected' WHERE request_id=%s",
                (request_id,)
            )

            conn.commit()
            st.warning("Request rejected")
            st.rerun()

    st.divider()

   