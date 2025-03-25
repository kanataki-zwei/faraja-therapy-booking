import re
import streamlit as st
import pandas as pd
from PIL import Image
import base64

# ✅ Use local version for development
from utils.gsheet import connect_to_gsheet, get_sessions  # Local
# from utils.gsheet import connect_to_gsheet, get_sessions      # Streamlit Cloud
from utils.booking import book_session, save_booking

# =========================
# ✅ Encode logo to base64
# =========================
def get_base64_image(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

logo_base64 = get_base64_image("assets/logo.png")

# =========================
# ✅ Header with Full-Width Styling
# =========================
st.markdown(
    f"""
    <div style="display: flex; align-items: center; width: 100%; padding: 20px 0; border-bottom: 1px solid #555;">
        <img src="data:image/png;base64,{logo_base64}" style="height: 60px; margin-right: 20px;">
        <h1 style="margin: 0; font-size: 2rem;">Faraja Cancer Therapy Booking System</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ✅ Connect to Google Sheets using secrets
client, spreadsheet, sheet = connect_to_gsheet()

# =========================
# ✅ Connect to Google Sheet
# =========================
#client, spreadsheet, sheet = connect_to_gsheet(
#    sheet_id="1VpvxpRZOkLprum6D7F_ozYO26l20Y0GgVqkOktzEaQU",
#    json_key_file="credentials/google_sheets_creds.json"
#)

if sheet is None:
    st.error("❌ Failed to connect to Google Sheets. Please check credentials.")
    st.stop()

st.subheader("Available Therapy Sessions")

# ✅ Fetch session data
df = get_sessions(sheet)

if df.empty:
    st.error("⚠ No therapy session data found. Please check your Google Sheet.")
    st.stop()

# =========================
# ✅ Filters
# =========================
df_filtered = df.copy()

therapy_filter = st.selectbox("Select Therapy Type", ["All"] + sorted(df["Therapy Name"].dropna().unique()))
if therapy_filter != "All":
    df_filtered = df_filtered[df_filtered["Therapy Name"] == therapy_filter]

location_filter = st.selectbox("Select Faraja Center Location", ["All"] + sorted(df["Faraja Center Location"].dropna().unique()))
if location_filter != "All":
    df_filtered = df_filtered[df_filtered["Faraja Center Location"] == location_filter]

format_filter = st.selectbox("Select Session Format", ["All"] + sorted(df["Online or Physical"].dropna().unique()))
if format_filter != "All":
    df_filtered = df_filtered[df_filtered["Online or Physical"] == format_filter]

start_date = st.date_input("Start Date", min_value=pd.to_datetime(df["Date Available"]).min())
end_date = st.date_input("End Date", min_value=start_date)

df_filtered = df_filtered[
    (pd.to_datetime(df_filtered["Date Available"]) >= pd.to_datetime(start_date)) &
    (pd.to_datetime(df_filtered["Date Available"]) <= pd.to_datetime(end_date))
]

booking_status_filter = st.selectbox("Select Booking Status", ["All"] + sorted(df_filtered["Booking Status"].dropna().unique()))
if booking_status_filter != "All":
    df_filtered = df_filtered[df_filtered["Booking Status"] == booking_status_filter]

# =========================
# ✅ Display Available Sessions (without index)
# =========================
st.subheader("Available Sessions")
if not df_filtered.empty:
    df_filtered_display = df_filtered[[
        "Therapy Name", "Therapist Name", "Faraja Center Location", "Online or Physical",
        "Date Available", "Start Time", "End Time", "Booking Status"
    ]]
    st.dataframe(df_filtered_display, hide_index=True)
else:
    st.warning("⚠ No sessions available for the selected filters.")

    relaxed_df = df.copy()
    if therapy_filter != "All":
        relaxed_df = relaxed_df[relaxed_df["Therapy Name"] == therapy_filter]
    if location_filter != "All":
        relaxed_df = relaxed_df[relaxed_df["Faraja Center Location"] == location_filter]
    if format_filter != "All":
        relaxed_df = relaxed_df[relaxed_df["Online or Physical"] == format_filter]

    relaxed_df = relaxed_df[relaxed_df["Booking Status"] != "Full"]

    relaxed_df["Date Available"] = pd.to_datetime(relaxed_df["Date Available"])
    relaxed_df["Start Time"] = pd.to_datetime(relaxed_df["Start Time"], format="%I:%M %p").dt.time
    relaxed_df = relaxed_df.sort_values(by=["Date Available", "Start Time"])

    top_alternatives = relaxed_df.head(3)[[
        "Therapy Name", "Therapist Name", "Faraja Center Location", "Online or Physical",
        "Date Available", "Start Time", "End Time", "Booking Status"
    ]]

    if not top_alternatives.empty:
        st.info("🔍 Here are the top 3 nearest available sessions based on your preferences. Please re adjust your filters to select one of them:")
        st.dataframe(top_alternatives, hide_index=True)
    else:
        st.info("😔 Sorry, no similar sessions are currently available.")

# =========================
# ✅ Booking Section
# =========================
if not df_filtered.empty:
    df_filtered["session_display"] = df_filtered.apply(
        lambda row: f"{row['Therapy Name']} - {row['Therapist Name']} - {row['Faraja Center Location']} - {row['Date Available']} {row['Start Time']} to {row['End Time']} (Status: {row['Booking Status']})",
        axis=1
    )
    session_selection = st.selectbox("Select a Session", df_filtered["session_display"])
    matching_row = df_filtered[df_filtered["session_display"] == session_selection]

    if not matching_row.empty:
        session_index_filtered = matching_row.index[0]
        selected_session = matching_row.iloc[0]

        session_index = df[
            (df["Therapy Name"] == selected_session["Therapy Name"]) &
            (df["Therapist Name"] == selected_session["Therapist Name"]) &
            (df["Date Available"] == selected_session["Date Available"]) &
            (df["Start Time"] == selected_session["Start Time"]) &
            (df["End Time"] == selected_session["End Time"])
        ].index[0]

        session_status = selected_session["Booking Status"]

        if session_status == "Full":
            st.error("❌ This session is full. Please select an available session.")
        else:
            name = st.text_input("Full Name")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            attendee_type = st.selectbox("Attendee Type", ["Patient", "Caregiver"])
            phone = st.text_input("Phone Number")

            def is_valid_phone(phone):
                return re.fullmatch(r"\d{10}", phone) is not None

            if phone and not is_valid_phone(phone):
                st.error("❌ Invalid phone number. Please enter a 10-digit number.")

            if phone and is_valid_phone(phone):
                if st.button("Book Now"):
                    if not name:
                        st.error("❌ Please enter your full name.")
                    else:
                        try:
                            bookings_sheet = spreadsheet.worksheet("Bookings")
                            bookings_data = bookings_sheet.get_all_records()
                            bookings_df = pd.DataFrame(bookings_data)

                            already_booked = bookings_df[
                                (bookings_df["Phone"] == phone) &
                                (bookings_df["Therapy Name"] == selected_session["Therapy Name"]) &
                                (bookings_df["Date"] == selected_session["Date Available"]) &
                                (bookings_df["Time"] == f"{selected_session['Start Time']} - {selected_session['End Time']}")
                            ]

                            if not already_booked.empty:
                                booked_row = already_booked.iloc[0]
                                st.error("❌ You already have a booking for this session.")
                                st.info(
                                    f"**Booking Details:**\n\n"
                                    f"- Therapy: {booked_row['Therapy Name']}\n"
                                    f"- Date: {booked_row['Date']}\n"
                                    f"- Time: {booked_row['Time']}\n"
                                    f"- Location: {booked_row['Location']}\n"
                                    f"- Format: {booked_row['Format']}"
                                )
                            else:
                                status = book_session(sheet, df, session_index)
                                if status == "Success":
                                    save_booking(spreadsheet, name, gender, attendee_type, phone, df.loc[session_index])
                                    st.success("✅ Booking confirmed!")
                                else:
                                    st.error("❌ This session is already full. Please choose another session.")

                        except Exception as e:
                            st.error("❌ Failed to check for duplicate booking.")
                            st.text(str(e))