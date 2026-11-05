
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
# ---------------------------------
# CUSTOM DASHBOARD DESIGN
# ---------------------------------

st.markdown("""
<style>


/* Main dashboard content */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}

/* Section headings */
h1, h2, h3 {
    color: #173B57 !important;
    font-weight: 700 !important;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #FFFFFF, #F0F7FA);
    border: 1px solid #D6E6ED;
    padding: 18px;
    border-radius: 14px;
    box-shadow: 0 3px 10px rgba(23, 59, 87, 0.06);
}

/* Metric values */
[data-testid="stMetricValue"] {
    color: #176B78;
    font-weight: 700;
}

/* Input fields and dropdowns */
.stTextInput input,
.stSelectbox div[data-baseweb="select"] {
    border-radius: 10px;
}

/* Buttons */
.stButton button,
.stDownloadButton button {
    border-radius: 10px;
    font-weight: 600;
    border: 1px solid #A8D9D7;
    transition: all 0.2s ease;
}

/* Buttons on hover */
.stButton button:hover,
.stDownloadButton button:hover {
    border-color: #4A9D9A;
    transform: translateY(-1px);
}

/* Data tables */
[data-testid="stDataFrame"] {
    border: 1px solid #D8E6ED;
    border-radius: 12px;
    overflow: hidden;
}

/* Expanders */
[data-testid="stExpander"] {
    background-color: #FFFFFF;
    border: 1px solid #D8E6ED;
    border-radius: 12px;
}

/* Horizontal separators */
hr {
    border-color: #D8E6ED;
}

/* SIDEBAR DESIGN */
[data-testid="stSidebar"] {
    background-color: #173B57;
    border-right: 1px solid #D5E9ED;
}

/* Sidebar headings */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
}

/* Sidebar text */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label {
    color: #E4F0F5 !important;
}

/* Sidebar radio navigation */
[data-testid="stSidebar"] .stRadio label {
    background-color: transparent;
    padding: 10px;
    border-radius: 8px;
}

/* Sidebar navigation hover */
[data-testid="stSidebar"] .stRadio label:hover {
    background-color: #315C75;
}

/* Sidebar divider */
[data-testid="stSidebar"] hr {
    border-color: #547287;
}

</style>
""", unsafe_allow_html=True)


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
# PATIENT PORTAL - AUTO REFRESH
# ---------------------------------
# Get patient ID from QR link
patient_id = st.query_params.get("patient")
if patient_id:

    st.title("🏥 OPDFlow AI")
    st.subheader("Patient Queue Status")

    try:
        uuid.UUID(patient_id)

        @st.fragment(run_every="15s")
        def display_patient_status():

            try:
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

                    st.caption(
                        "Queue information refreshes automatically every 15 seconds."
                    )

                    if st.button(
                        "Refresh Now",
                        key="manual_patient_refresh"
                    ):
                        st.rerun()

                else:
                    st.error("Patient token not found.")

            except Exception:
                st.error("Unable to retrieve queue status. Please try again.")

        display_patient_status()

    except ValueError:
        st.error("Invalid patient token link.")

    st.stop()


# ---------------------------------
# MANAGEMENT DASHBOARD
# ---------------------------------
# ---------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------

with st.sidebar:

    st.markdown("# 🏥 OPDFlow AI")
    st.caption("Hospital Management Portal")

    st.divider()

    st.markdown("### MAIN MENU")

    selected_page = st.radio(
        "Navigate",
        [
            "Overview",
            "Prediction & Registration",
            "Staff Queue Dashboard"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    st.caption("OPDFlow AI | Academic Prototype")
# ---------------------------------
# DASHBOARD WELCOME BANNER
# ---------------------------------
if selected_page == "Overview":
    st.markdown("""
    <div style="background-color:#E8F5F7;
                padding:25px;
                border-radius:15px;
                border:1px solid #D5E9ED;">

    <h1 style="color:#173B57;">🏥 OPDFlow AI</h1>

    <h3 style="color:#426477;">
    OPD Waiting-Time Prediction & Congestion Management
    </h3>

    <p style="color:#607D8B;">
    Monitor patient queues, predict waiting times and manage
    outpatient department operations efficiently.
    </p>

    </div>
    """, unsafe_allow_html=True)
# ---------------------------------
# AUTOMATIC QUEUE POSITION UPDATE
# ---------------------------------


# ---------------------------------
# AUTOMATIC QUEUE POSITION AND WAIT UPDATE
# ---------------------------------

def recalculate_queue_positions(supabase, department):

    response = (
        supabase.table("queue_entries")
        .select(
            "id, avg_consultation_time, doctors_available"
        )
        .eq("department", department)
        .eq("status", "Waiting")
        .order("created_at")
        .execute()
    )

    waiting_patients = response.data or []

    for position, patient in enumerate(
        waiting_patients, start=1
    ):

        avg_time = patient.get("avg_consultation_time") or 15
        doctors = patient.get("doctors_available") or 1

        estimated_wait = round(
            position * avg_time / max(doctors, 1)
        )

        (
            supabase.table("queue_entries")
            .update({
                "queue_position": position,
                "estimated_wait_minutes": estimated_wait
            })
            .eq("id", patient["id"])
            .execute()
        )

    return len(waiting_patients)


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


if selected_page == "Staff Queue Dashboard":
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

                # KEEP THE REST OF YOUR EXISTING
                # DASHBOARD CODE HERE, INSIDE THIS try BLOCK

                # QUEUE SUMMARY CARDS
                total_patients = len(queue_data)

                waiting_count = sum(
                    1 for p in queue_data if p["status"] == "Waiting"
                )
                consultation_count = sum(
                    1 for p in queue_data if p["status"] == "In Consultation"
                )
                completed_count = sum(
                    1 for p in queue_data if p["status"] == "Completed"
                )

                st.subheader("📊 OPD Overview")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Patients", total_patients)

                with col2:
                    st.metric("Waiting", waiting_count)

                with col3:
                    st.metric("In Consultation", consultation_count)

                with col4:
                    st.metric("Completed", completed_count)

                if queue_data:

                    queue_df = pd.DataFrame(queue_data)

                    # OPD ANALYTICS DASHBOARD
                    st.subheader("📈 OPD Analytics Dashboard")

                    # Average waiting time
                    waiting_patients = queue_df[
                        queue_df["status"] == "Waiting"
                    ]

                    if not waiting_patients.empty:
                        avg_wait = round(
                            waiting_patients["estimated_wait_minutes"].mean(),
                            1
                        )
                    else:
                        avg_wait = 0

                    st.metric(
                        "Average Estimated Waiting Time",
                        f"{avg_wait} minutes"
                    )

                    # Prepare charts
                    col1, col2 = st.columns(2)

                    # Patients by Department
                    with col1:
                        st.write("**Patients by Department**")

                        department_counts = queue_df["department"].value_counts()

                        st.bar_chart(
                            department_counts,
                            color="#4682B4"
                        )

                    # Patient Status Distribution
                    with col2:
                        st.write("**Patient Status Distribution**")

                        status_counts = queue_df["status"].value_counts()

                        st.bar_chart(
                            status_counts,
                            color="#9370DB"
                        )

                    # Waiting Patients by Department
                    st.write("**Waiting Patients by Department**")

                    waiting_by_department = (
                        waiting_patients["department"].value_counts()
                    )

                    st.bar_chart(
                        waiting_by_department,
                        color="#20A38A"
                    )

                    # SEARCH AND FILTER PATIENTS
                    st.subheader("🔍 Search and Filter Patients")

                    search_text = st.text_input(
                        "Search by token, patient name or department",
                        placeholder="Enter token number, name or department..."
                    )

                    filter_col1, filter_col2 = st.columns(2)

                    with filter_col1:
                        selected_department = st.selectbox(
                            "Filter by Department",
                            ["All"] + sorted(
                                queue_df["department"].dropna().unique().tolist()
                            ),
                            key="filter_department"
                        )

                    with filter_col2:
                        selected_status = st.selectbox(
                            "Filter by Status",
                            ["All", "Waiting", "In Consultation", "Completed"],
                            key="filter_status"
                        )

                    filtered_df = queue_df.copy()

                    if search_text:
                        search_mask = (
                            filtered_df["token_number"].astype(str).str.contains(
                                search_text, case=False, na=False
                            )
                            | filtered_df["patient_name"].astype(str).str.contains(
                                search_text, case=False, na=False
                            )
                            | filtered_df["department"].astype(str).str.contains(
                                search_text, case=False, na=False
                            )
                        )

                        filtered_df = filtered_df[search_mask]

                    if selected_department != "All":
                        filtered_df = filtered_df[
                            filtered_df["department"] == selected_department
                        ]

                    if selected_status != "All":
                        filtered_df = filtered_df[
                            filtered_df["status"] == selected_status
                        ]

                    st.subheader("Registered Patient Queue")

                    st.caption(
                        f"Showing {len(filtered_df)} of {len(queue_df)} patients"
                    )

                    st.dataframe(
                        filtered_df,
                        use_container_width=True,
                        hide_index=True
                    )


                    # RESHOW PATIENT QR CODE
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

                        qr = qrcode.QRCode(box_size=8, border=4)
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
                            "Token Number:",
                            selected_patient["token_number"]
                        )
                        st.image(qr_buffer.getvalue(), width=250)

                        st.download_button(
                            "Download Patient QR Code",
                            data=qr_buffer.getvalue(),
                            file_name=f"{qr_token}.png",
                            mime="image/png",
                            key="download_reprinted_qr"
                        )


                # UPDATE PATIENT STATUS
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

                            update_data = {"status": new_status}

                            if new_status != "Waiting":
                                update_data["queue_position"] = 0

                            (
                                supabase.table("queue_entries")
                                .update(update_data)
                                .eq("token_number", selected_token)
                                .execute()
                            )

                            updated_count = recalculate_queue_positions(
                                supabase,
                                selected_patient["department"]
                            )

                            st.success(
                                f"{selected_token} status updated to {new_status}!"
                            )

                            st.info(
                                f"{updated_count} waiting patients now have "
                                "updated queue positions and waiting times."
                            )

                            st.rerun()

                        except Exception as e:
                            st.error("Unable to update patient status.")
                            st.exception(e)

                else:
                    st.info("No patients registered yet.")

            except Exception as e:
                st.error("Unable to load the patient queue.")
                st.exception(e)


if selected_page == "Prediction & Registration":

    st.header("🧑‍⚕️ Patient Registration")
    st.caption(
        "Enter patient details to predict waiting time and generate a queue token."
    )


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

    # MODEL INPUT

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

    # PREDICTION FUNCTION

    def predict_wait():

        prediction = model.predict(input_data)[0]

        if prediction < 20:
            congestion = "Low"
        elif prediction <= 45:
            congestion = "Moderate"
        else:
            congestion = "High"

        return max(0, float(prediction)), congestion

    # PREDICT WAITING TIME

    st.divider()

    if st.button("Predict Waiting Time"):

        waiting_time, congestion = predict_wait()

        st.subheader("Prediction Results")

        result_col1, result_col2 = st.columns(2)

        with result_col1:
            st.metric(
                "Predicted Waiting Time",
                f"{waiting_time:.1f} minutes"
            )

        with result_col2:
            st.metric(
                "Congestion Level",
                congestion
            )

    # REGISTER PATIENT AND GENERATE QR

    st.divider()

    if st.button("Register Patient & Generate QR Code"):

        if not patient_name.strip():

            st.warning("Please enter the patient's name.")

        else:

            try:

                supabase = get_supabase()

                waiting_time, congestion = predict_wait()

                token_number = "OPD-" + uuid.uuid4().hex[:6].upper()

                public_id = str(uuid.uuid4())

                existing = (
                    supabase.table("queue_entries")
                    .select("id")
                    .eq("department", department)
                    .eq("status", "Waiting")
                    .execute()
                )

                queue_position = len(existing.data or []) + 1

                patient_record = {
                    "public_id": public_id,
                    "token_number": token_number,
                    "patient_name": patient_name.strip(),
                    "department": department,
                    "queue_position": queue_position,
                    "estimated_wait_minutes": round(waiting_time),
                    "avg_consultation_time": int(avg_consultation_time),
                    "doctors_available": int(doctors_available),
                    "status": "Waiting"
                }

                supabase.table(
                    "queue_entries"
                ).insert(patient_record).execute()

                recalculate_queue_positions(supabase, department)

                patient_url = (
                    f"{APP_URL}/?patient={public_id}"
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

                buffer = BytesIO()
                qr_image.save(buffer, format="PNG")

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
