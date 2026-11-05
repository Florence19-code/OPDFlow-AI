
import streamlit as st
import pandas as pd
import joblib
import uuid
import qrcode
from io import BytesIO
from supabase import create_client

# ---------------------------------
# PAGE CONFIGURATION
# ---------------------------------

st.set_page_config(
    page_title="OPDFlow AI",
    page_icon="🏥",
    layout="wide"
)

APP_URL = "https://opdflow-ai-9fduheria83du5dof2vbi8.streamlit.app"

# ---------------------------------
# LOAD MODEL
# ---------------------------------

model = joblib.load("OPDFlow_AI_Model.joblib")
config = joblib.load("OPDFlow_AI_Config.joblib")

# ---------------------------------
# SUPABASE CONNECTION
# ---------------------------------

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

# ---------------------------------
# PATIENT PORTAL
# ---------------------------------

patient_id = st.query_params.get("patient")

if patient_id:

    st.title("🏥 OPDFlow AI")
    st.subheader("Patient Queue Status")

    try:
        uuid.UUID(patient_id)

        supabase = get_supabase()

        result = supabase.rpc(
            "get_patient_status",
            {"p_public_id": patient_id}
        ).execute()

        records = result.data

        if records:

            patient = records[0]

            st.success("Your token was found!")

            st.metric(
                "Your Token Number",
                patient["token_number"]
            )

            st.metric(
                "Queue Position",
                patient["queue_position"]
            )

            st.metric(
                "Estimated Waiting Time",
                f'{patient["estimated_wait_minutes"]} minutes'
            )

            st.write(
                "**Department:**",
                patient["department"]
            )

            st.write(
                "**Status:**",
                patient["status"]
            )

            if st.button("Refresh Queue Status"):
                st.rerun()

        else:
            st.error("Patient token not found.")

    except Exception as e:
        st.error("Unable to retrieve queue status.")
        st.caption(str(e))

    st.caption(
        "Waiting times are estimates and may change."
    )

    st.stop()

# ---------------------------------
# MANAGEMENT DASHBOARD
# ---------------------------------

st.title("🏥 OPDFlow AI")

st.subheader(
    "OPD Waiting-Time Prediction and Congestion Management"
)

st.write(
    "Enter the outpatient department details below "
    "to predict the patient's expected waiting time."
)

# ---------------------------------
# AUTOMATIC QUEUE POSITION UPDATE
# ---------------------------------

def recalculate_queue_positions(supabase, department):

    response = (
        supabase.table("queue_entries")
        .select("id")
        .eq("department", department)
        .eq("status", "Waiting")
        .order("created_at")
        .execute()
    )

    waiting_patients = response.data or []

    for position, patient in enumerate(
        waiting_patients, start=1
    ):

        (
            supabase.table("queue_entries")
            .update({"queue_position": position})
            .eq("id", patient["id"])
            .execute()
        )

    return len(waiting_patients)

# ---------------------------------
# STAFF QUEUE DASHBOARD
# ---------------------------------

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

with st.expander("🔐 Staff Queue Dashboard"):

    if not st.session_state.admin_authenticated:

        admin_password = st.text_input(
            "Enter Staff Password",
            type="password",
            key="admin_password_input"
        )

        if st.button("Staff Login", key="staff_login"):

            if admin_password == st.secrets["ADMIN_PASSWORD"]:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")

    else:

        st.success("Staff login successful!")

        if st.button("Staff Logout", key="staff_logout"):
            st.session_state.admin_authenticated = False
            st.rerun()

        st.subheader("Registered Patient Queue")

        if st.button("Refresh Queue", key="refresh_queue"):
            st.rerun()

        try:
            response = (
                get_supabase()
                .table("queue_entries")
                .select(
    "public_id, token_number, patient_name, department, "
    "queue_position, estimated_wait_minutes, "
    "status, created_at"
)
                .order("created_at")
                .execute()
            )

            queue_data = response.data or []

            if queue_data:

                queue_df = pd.DataFrame(queue_data)

                st.dataframe(
                    queue_df,
                    use_container_width=True,
                    hide_index=True
                )

                st.metric(
                    "Total Registered Patients",
                    len(queue_data)
                )

                # ---------------------------------
                # RESHOW / REPRINT PATIENT QR CODE
                # ---------------------------------

                st.subheader("Reshow Patient QR Code")

                qr_token = st.selectbox(
                    "Select Patient Token to Reshow QR",
                    [p["token_number"] for p in queue_data],
                    key="qr_reprint_token"
                )

                if st.button("Show Patient QR Code"):

                    selected_patient = next(
                        p for p in queue_data
                        if p["token_number"] == qr_token
                    )

                    patient_url = (
                        f"{APP_URL}/?patient={selected_patient['public_id']}"
                    )

                    qr = qrcode.QRCode(
                        box_size=8,
                        border=4
                    )

                    qr.add_data(patient_url)
                    qr.make(fit=True)

                    qr_image = qr.make_image(
                        fill_color="black",
                        back_color="white"
                    )

                    qr_buffer = BytesIO()
                    qr_image.save(qr_buffer, format="PNG")

                    st.success("Original patient QR code retrieved!")

                    st.write(
                        "**Token Number:**",
                        selected_patient["token_number"]
                    )

                    st.image(
                        qr_buffer.getvalue(),
                        width=250
                    )

                    st.download_button(
                        "Download Patient QR Code",
                        data=qr_buffer.getvalue(),
                        file_name=f"{qr_token}.png",
                        mime="image/png",
                        key="download_reprinted_qr"
                    )

                st.subheader("Update Patient Status")

                selected_token = st.selectbox(
                    "Select Patient Token",
                    [p["token_number"] for p in queue_data],
                    key="selected_patient_token"
                )

                new_status = st.selectbox(
                    "Select New Status",
                    ["Waiting", "In Consultation", "Completed"],
                    key="new_patient_status"
                )

                
                if st.button("Update Patient Status"):

                    try:

                        selected_patient = next(
                            p for p in queue_data
                            if p["token_number"] == selected_token
                        )

                        supabase = get_supabase()

                        # Update selected patient's status
                        update_data = {
                            "status": new_status
                        }

                        if new_status != "Waiting":
                            update_data["queue_position"] = 0

                        (
                            supabase.table("queue_entries")
                            .update(update_data)
                            .eq("token_number", selected_token)
                            .execute()
                        )

                        # Recalculate remaining waiting patients
                        updated_count = recalculate_queue_positions(
                            supabase,
                            selected_patient["department"]
                        )

                        st.success(
                            f"{selected_token} status updated to {new_status}!"
                        )

                        st.info(
                            f"{updated_count} waiting patients now have updated queue positions."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error("Unable to update patient status.")
                        st.exception(e)


                    try:
                        (
                            get_supabase()
                            .table("queue_entries")
                            .update({"status": new_status})
                            .eq("token_number", selected_token)
                            .execute()
                        )

                        st.success(
                            f"{selected_token} status updated to {new_status}!"
                        )

                        st.rerun()

                    except Exception as e:
                        st.error("Unable to update patient status.")
                        st.exception(e)

            else:
                st.info("No patients registered yet.")

        except Exception as e:
            st.error("Unable to load the patient queue.")
            st.caption(str(e))

st.header("Patient Registration")

patient_name = st.text_input("Patient Name")

col1, col2 = st.columns(2)

with col1:

    department = st.selectbox(
        "Select Department",
        [
            "General Medicine",
            "Cardiology",
            "Orthopaedics",
            "Paediatrics",
            "Dermatology",
            "ENT"
        ]
    )

    arrival_hour = st.slider(
        "Arrival Hour",
        8, 19, 11
    )

    day_of_week = st.selectbox(
        "Day of the Week",
        [
            "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday"
        ]
    )

    appointment_type = st.selectbox(
        "Appointment Type",
        ["Appointment", "Walk-in"]
    )

with col2:

    patients_waiting = st.number_input(
        "Number of Patients Waiting",
        min_value=0,
        max_value=100,
        value=10
    )

    doctors_available = st.number_input(
        "Number of Doctors Available",
        min_value=1,
        max_value=10,
        value=2
    )

    avg_consultation_time = st.number_input(
        "Average Consultation Time (minutes)",
        min_value=5,
        max_value=60,
        value=15
    )

# ---------------------------------
# MODEL INPUT
# ---------------------------------

peak_hour = 1 if 9 <= arrival_hour <= 12 else 0

weekend = 1 if day_of_week in [
    "Saturday", "Sunday"
] else 0

input_data = pd.DataFrame([{
    "Arrival_Hour": arrival_hour,
    "Department": department,
    "Day_of_Week": day_of_week,
    "Appointment_Type": appointment_type,
    "Patients_Waiting": patients_waiting,
    "Doctors_Available": doctors_available,
    "Avg_Consultation_Time": avg_consultation_time,
    "Peak_Hour": peak_hour,
    "Weekend": weekend
}])

# ---------------------------------
# PREDICTION FUNCTION
# ---------------------------------

def predict_wait():

    prediction = model.predict(input_data)[0]

    if prediction < 20:
        congestion = "Low"
    elif prediction <= 45:
        congestion = "Moderate"
    else:
        congestion = "High"

    return max(0, float(prediction)), congestion

# ---------------------------------
# PREDICT WAITING TIME
# ---------------------------------

if st.button("Predict Waiting Time"):

    waiting_time, congestion = predict_wait()

    st.subheader("Prediction Results")

    st.metric(
        "Predicted Waiting Time",
        f"{waiting_time:.1f} minutes"
    )

    st.write("**Congestion Level:**", congestion)

# ---------------------------------
# REGISTER PATIENT AND GENERATE QR
# ---------------------------------

if st.button("Register Patient & Generate QR Code"):

    if not patient_name.strip():

        st.warning("Please enter the patient's name.")

    else:

        try:

            supabase = get_supabase()

            waiting_time, congestion = predict_wait()

            # Generate unique token and patient ID
            token_number = "OPD-" + uuid.uuid4().hex[:6].upper()

            public_id = str(uuid.uuid4())

            # Calculate queue position
            existing = (
                supabase.table("queue_entries")
                .select("id")
                .eq("department", department)
                .eq("status", "Waiting")
                .execute()
            )

            queue_position = len(existing.data or []) + 1

            # Save patient record
            patient_record = {
                "public_id": public_id,
                "token_number": token_number,
                "patient_name": patient_name.strip(),
                "department": department,
                "queue_position": queue_position,
                "estimated_wait_minutes": round(waiting_time),
                "status": "Waiting"
            }

            supabase.table(
                "queue_entries"
            ).insert(patient_record).execute()

            # Create patient status URL
            patient_url = (
                f"{APP_URL}/?patient={public_id}"
            )

            # Generate QR code
            qr = qrcode.QRCode(
                box_size=8,
                border=4
            )

            qr.add_data(patient_url)
            qr.make(fit=True)

            qr_image = qr.make_image(
                fill_color="black",
                back_color="white"
            )

            buffer = BytesIO()
            qr_image.save(buffer, format="PNG")

            # Display registration result
            st.success("Patient registered successfully!")

            st.subheader("Patient Token")

            st.metric(
                "Token Number",
                token_number
            )

            st.write("**Department:**", department)
            st.write("**Queue Position:**", queue_position)

            st.metric(
                "Estimated Waiting Time",
                f"{waiting_time:.1f} minutes"
            )

            st.write("**Congestion Level:**", congestion)

            st.subheader("Patient QR Code")

            st.image(
                buffer.getvalue(),
                width=250
            )

            st.info(
                "Ask the patient to scan this QR code "
                "to view their queue status."
            )

            st.download_button(
                "Download Patient QR Code",
                data=buffer.getvalue(),
                file_name=f"{token_number}.png",
                mime="image/png"
            )

        except Exception as e:

            st.error("Patient registration failed.")
            st.exception(e)

# ---------------------------------
# PROJECT LIMITATION
# ---------------------------------

st.caption(
    "Academic prototype using synthetic data. "
    "Predictions are illustrative and should not be used "
    "as a substitute for actual hospital queue information."
)
