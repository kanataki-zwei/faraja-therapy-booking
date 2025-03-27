import re
import streamlit as st
import pandas as pd
from utils.gsheet import connect_to_gsheet, get_sessions
from utils.booking import book_session, save_booking

def render_book_session():
    st.subheader("Available Therapy Sessions")

    # ✅ Connect to Google Sheets
    client, spreadsheet, sheet = connect_to_gsheet()

    if sheet is None:
        st.error("❌ Failed to connect to Google Sheets. Please check credentials.")
        st.stop()

    df = get_sessions(sheet)
    if df.empty:
        st.error("⚠ No therapy session data found. Please check your Google Sheet.")
        st.stop()

    df_filtered = df.copy()

    # === 1. Faraja Center Location Filter ===
    location_filter = st.selectbox("**📍 Location Filter:** Select your nearest Faraja center.", ["All"] + sorted(df["Faraja Center Location"].dropna().unique()))
    if location_filter != "All":
        df_filtered = df_filtered[df_filtered["Faraja Center Location"] == location_filter]

    # === 2. Date Range Filter ===
    st.markdown("📅 **Date Range** – Select the period you're available for therapy.")
    start_date = st.date_input("Start Date", min_value=pd.to_datetime(df["Date Available"]).min())
    end_date = st.date_input("End Date", min_value=start_date)

    df_filtered = df_filtered[
        (pd.to_datetime(df_filtered["Date Available"]) >= pd.to_datetime(start_date)) &
        (pd.to_datetime(df_filtered["Date Available"]) <= pd.to_datetime(end_date))
    ]

    # === 3. Booking Status Filter ===
    booking_status_filter = st.selectbox("📌 **Booking Status** – Only pick available sessions.", ["All"] + sorted(df_filtered["Booking Status"].dropna().unique()))
    if booking_status_filter != "All":
        df_filtered = df_filtered[df_filtered["Booking Status"] == booking_status_filter]

    # === 4. Therapy Type Filter ===
    therapy_filter = st.selectbox("💆 **Therapy Type** – Select the type of therapy you're interested in.", ["All"] + sorted(df_filtered["Therapy Name"].dropna().unique()))
    if therapy_filter != "All":
        df_filtered = df_filtered[df_filtered["Therapy Name"] == therapy_filter]

    # === 5. Format Filter ===
    format_filter = st.selectbox("🖥️🏥 **Session Format** – Choose between online or in-person sessions.", ["All"] + sorted(df_filtered["Online or Physical"].dropna().unique()))
    if format_filter != "All":
        df_filtered = df_filtered[df_filtered["Online or Physical"] == format_filter]

    # === Display Sessions ===
    st.subheader("Available Sessions")
    if not df_filtered.empty:
        display_cols = [
            "Therapy Name", "Therapist Name", "Faraja Center Location", "Online or Physical",
            "Date Available", "Start Time", "End Time", "Booking Status"
        ]
        st.dataframe(df_filtered[display_cols], hide_index=True)
    else:
        st.warning("⚠ No sessions available for the selected filters.")

        relaxed_df = df.copy()
        if location_filter != "All":
            relaxed_df = relaxed_df[relaxed_df["Faraja Center Location"] == location_filter]

        relaxed_df = relaxed_df[relaxed_df["Booking Status"] != "Full"]
        relaxed_df["Date Available"] = pd.to_datetime(relaxed_df["Date Available"])
        relaxed_df["Start Time"] = pd.to_datetime(relaxed_df["Start Time"], format="%I:%M %p", errors="coerce").dt.time
        relaxed_df = relaxed_df.sort_values(by=["Date Available", "Start Time"])

        top_alternatives = relaxed_df.head(3)[display_cols]
        if not top_alternatives.empty:
            st.info("🔍 Here are the top 3 nearest available sessions based on your filters:")
            st.dataframe(top_alternatives, hide_index=True)
        else:
            st.info("😔 Sorry, no similar sessions are currently available.")

    # === Booking Section ===
    if not df_filtered.empty:
        df_filtered["session_display"] = df_filtered.apply(
            lambda row: f"{row['Therapy Name']} - {row['Therapist Name']} - {row['Faraja Center Location']} - {row['Date Available']} {row['Start Time']} to {row['End Time']} (Status: {row['Booking Status']})",
            axis=1
        )
        st.markdown("🎯 **Select a Session** – Choose the specific therapy session to book.")
        session_selection = st.selectbox("Select a Session", df_filtered["session_display"])
        matching_row = df_filtered[df_filtered["session_display"] == session_selection]

        if not matching_row.empty:
            selected_session = matching_row.iloc[0]
            session_index = df[
                (df["Therapy Name"] == selected_session["Therapy Name"]) &
                (df["Therapist Name"] == selected_session["Therapist Name"]) &
                (df["Date Available"] == selected_session["Date Available"]) &
                (df["Start Time"] == selected_session["Start Time"]) &
                (df["End Time"] == selected_session["End Time"])
            ].index[0]

            if selected_session["Booking Status"] == "Full":
                st.error("❌ This session is full. Please select an available session.")
            else:
                name = st.text_input("🧑‍💼 **Full Name** – Provide your full name for the booking.")
                gender = st.selectbox("🚻 **Gender** – Choose your gender (for record purposes).", ["Male", "Female", "Other"])
                attendee_type = st.selectbox("👥 **Attendee Type** – Are you booking as a patient or a caregiver?", ["Patient", "Caregiver"])
                phone = st.text_input("📞 **Phone Number** – Please enter your correct phone no.")

                def is_valid_phone(phone): return re.fullmatch(r"\d{10}", phone) is not None
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

                                session_date = pd.to_datetime(selected_session["Date Available"]).strftime("%Y-%m-%d")
                                session_time = f"{selected_session['Start Time']} - {selected_session['End Time']}"

                                already_booked = bookings_df[
                                    (bookings_df["Phone"] == phone) &
                                    (bookings_df["Therapy Name"] == selected_session["Therapy Name"]) &
                                    (bookings_df["Therapist"] == selected_session["Therapist Name"]) &
                                    (bookings_df["Date"] == session_date) &
                                    (bookings_df["Time"] == session_time)
                                ]

                                if not already_booked.empty:
                                    booked_row = already_booked.iloc[0]
                                    st.error("❌ You already have a booking for this session.")
                                    st.info(
                                        f"**Booking Details:**\n"
                                        f"- Therapy: {booked_row.get('Therapy Name', 'N/A')}\n"
                                        f"- Date: {booked_row.get('Date', 'N/A')}\n"
                                        f"- Time: {booked_row.get('Time', 'N/A')}\n"
                                        f"- Location: {booked_row.get('Faraja Center Location', 'N/A')}\n"
                                        f"- Format: {booked_row.get('Online or Physical', 'N/A')}"
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
