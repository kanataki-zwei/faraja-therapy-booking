import re
import streamlit as st
import pandas as pd
from utils.gsheet import connect_to_gsheet, get_sessions
from utils.booking import book_session, save_booking

# ✅ Connect to Google Sheets using secrets
client, spreadsheet, sheet = connect_to_gsheet()

if sheet is None:
    st.error("❌ Failed to connect to Google Sheets. Please check credentials.")
    st.stop()  # Prevent further execution if no connection

st.title("Faraja Cancer Therapy Booking System")
st.subheader("Available Therapy Sessions")

# ✅ Fetch session data safely
df = get_sessions(sheet)

if df.empty:
    st.error("⚠ No therapy session data found. Please check your Google Sheet.")
    st.stop()

# ✅ First Filter: Therapy Name
therapy_filter = st.selectbox("Select Therapy Type", ["All"] + list(df["Therapy Name"].unique()))

# Apply therapy name filter
df_filtered = df.copy()
if therapy_filter != "All":
    df_filtered = df_filtered[df_filtered["Therapy Name"] == therapy_filter]

# ✅ Second Filter: Date Range
start_date = st.date_input("Start Date", min_value=pd.to_datetime(df["Date Available"]).min())
end_date = st.date_input("End Date", min_value=start_date)

# Apply date range filter
df_filtered = df_filtered[
    (pd.to_datetime(df_filtered["Date Available"]) >= pd.to_datetime(start_date)) &
    (pd.to_datetime(df_filtered["Date Available"]) <= pd.to_datetime(end_date))
]

# ✅ Third Filter: Booking Status
booking_status_filter = st.selectbox("Select Booking Status", ["All"] + list(df_filtered["Booking Status"].unique()))

# Apply booking status filter
if booking_status_filter != "All":
    df_filtered = df_filtered[df_filtered["Booking Status"] == booking_status_filter]

# ✅ Display Available Sessions
st.subheader("Available Sessions")
if not df_filtered.empty:
    df_filtered_display = df_filtered[["Therapy Name", "Therapist Name", "Date Available", "Start Time", "End Time", "Booking Status"]]
    st.dataframe(df_filtered_display)
else:
    st.warning("⚠ No sessions available for the selected filters.")

# ✅ Let User Select a Session
if not df_filtered.empty:
    # ✅ Include Booking Status in selection dropdown
    session_selection = st.selectbox(
        "Select a Session",
        df_filtered.apply(lambda row: f"{row['Therapy Name']} - {row['Therapist Name']} - {row['Date Available']} {row['Start Time']} to {row['End Time']} (Status: {row['Booking Status']})", axis=1)
    )

    # ✅ Get the matching row based on selection
    matching_row = df_filtered[df_filtered.apply(lambda row: f"{row['Therapy Name']} - {row['Therapist Name']} - {row['Date Available']} {row['Start Time']} to {row['End Time']} (Status: {row['Booking Status']})", axis=1) == session_selection]

    if not matching_row.empty:
        session_index = matching_row.index[0]  # Get valid index safely
        session_status = matching_row.iloc[0]["Booking Status"]  # Get status

        if session_status == "Full":
            st.error("❌ This session is full. Please select an available session.")
        else:
            # ✅ Get user details
            name = st.text_input("Full Name")
            attendee_type = st.selectbox("Attendee Type", ["Patient", "Caregiver"])
            
            # ✅ Instant Phone Number Validation
            phone = st.text_input("Phone Number")

            def is_valid_phone(phone):
                return re.fullmatch(r"\d{10}", phone) is not None

            if phone and not is_valid_phone(phone):  # Instant validation
                st.error("❌ Invalid phone number. Please enter a 10-digit number.")

            # ✅ Only show "Book Now" if phone is valid
            if phone and is_valid_phone(phone):
                if st.button("Book Now"):
                    if not name:
                        st.error("❌ Please enter your full name.")
                    else:
                        status = book_session(sheet, df, session_index)

                        if status == "Success":
                            save_booking(spreadsheet, name, attendee_type, phone, df.loc[session_index])  # Pass full spreadsheet object
                            st.success("✅ Booking confirmed!")
                        else:
                            st.error("❌ This session is already full. Please choose another session.")
