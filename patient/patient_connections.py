import streamlit as st
from database import create_connection

def patient_connections_page():

    st.title("Doctor Connections")

    conn = create_connection()
    # cursor = conn.cursor()
    cursor = conn.cursor(buffered=True)

    patient_id = st.session_state.user_id

    # ---------------- MY DOCTOR SECTION ---------------- #
    st.subheader("My Doctor")

    cursor.execute("""
        SELECT d.name,d.specialization
        FROM connection_requests r
        JOIN doctors d ON r.doctor_id=d.doctor_id
        WHERE r.patient_id=%s AND r.status='accepted'
    """,(patient_id,))

    my_doctor = cursor.fetchall()

    # if my_doctor:
    #     st.success(f"Dr. {my_doctor[0]} \n\n {my_doctor[1]}")
    if my_doctor:
        doctor_list = "\n\n".join([f"Dr. {doc}" for doc in my_doctor])
        st.success(doctor_list)

    else:
        st.info("No doctor connected yet.")

    st.divider()

    # ---------------- ALL DOCTORS ---------------- #
    st.subheader("Available Doctors")

    cursor.execute("SELECT doctor_id,name,specialization FROM doctors")
    doctors = cursor.fetchall()

    for doctor in doctors:

        doctor_id = doctor[0]
        name = doctor[1]
        specialization = doctor[2]

        col1,col2 = st.columns([3,1])

        col1.write(f"Dr. {name} - {specialization}")

        # check request status
        cursor.execute("""
            SELECT status FROM connection_requests
            WHERE patient_id=%s AND doctor_id=%s
        """,(patient_id,doctor_id))

        result = cursor.fetchone()

        if result:

            status = result[0]

            if status == "pending":
                col2.info("Request Sent")

            elif status == "accepted":
                col2.success("Connected")

            elif status == "rejected":
                col2.warning("Doctor rejected your request")

                if col2.button("Send Request",key=f"send_again_{doctor_id}"):

                    cursor.execute("""
                        UPDATE connection_requests
                        SET status='pending'
                        WHERE patient_id=%s AND doctor_id=%s
                    """,(patient_id,doctor_id))

                    conn.commit()
                    st.rerun()

        else:

            if col2.button("Send Request",key=f"send_{doctor_id}"):

                cursor.execute("""
                    INSERT INTO connection_requests (patient_id,doctor_id)
                    VALUES (%s,%s)
                """,(patient_id,doctor_id))

                conn.commit()

                st.rerun()