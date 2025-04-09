import re
import streamlit as st
import pandas as pd
from utils.gsheet import connect_to_gsheet, get_sessions
from utils.booking import book_session, save_booking

def render_book_session():
    st.subheader("Available Therapy Sessions")

    client, spreadsheet, sheet = connect_to_gsheet()


    if sheet is None:
        st.error("❌ Failed to connect to Google Sheets. Please check credentials.")
        st.stop()

    df = get_sessions(sheet)
    if df.empty:
        st.error("⚠ No therapy session data found.")
        st.stop()

    df_filtered = df.copy()

    # === Filter 1: Location ===
    location_filter = st.selectbox("📍 **Location** – Select your nearest Faraja center", ["All"] + sorted(df["Faraja Center Location"].dropna().unique()))
    if location_filter != "All":
        df_filtered = df_filtered[df_filtered["Faraja Center Location"] == location_filter]

    # === Filter 2: Date Range ===
    st.markdown("📅 **Date Range** – Select the period you're available for therapy.")
    start_date = st.date_input("Start Date", min_value=pd.to_datetime(df["Date Available"]).min())
    end_date = st.date_input("End Date", min_value=start_date)
    df_filtered = df_filtered[
        (pd.to_datetime(df_filtered["Date Available"]) >= pd.to_datetime(start_date)) &
        (pd.to_datetime(df_filtered["Date Available"]) <= pd.to_datetime(end_date))
    ]

    # === Filter 3: Booking Status ===
    booking_status_filter = st.selectbox("📌 **Booking Status** – Only pick available sessions", ["All"] + sorted(df_filtered["Booking Status"].dropna().unique()))
    if booking_status_filter != "All":
        df_filtered = df_filtered[df_filtered["Booking Status"] == booking_status_filter]

    # === Filter 4: Therapy Type ===
    therapy_filter = st.selectbox("💆 **Therapy Type** – Choose a therapy you're interested in", ["All"] + sorted(df_filtered["Therapy Name"].dropna().unique()))
    if therapy_filter != "All":
        df_filtered = df_filtered[df_filtered["Therapy Name"] == therapy_filter]

    # === Filter 5: Format ===
    format_filter = st.selectbox("🖥️🏥 **Session Format** – Choose online or in-person", ["All"] + sorted(df_filtered["Online or Physical"].dropna().unique()))
    if format_filter != "All":
        df_filtered = df_filtered[df_filtered["Online or Physical"] == format_filter]

    # === Display Filtered Sessions ===
    st.subheader("Available Sessions")
    display_cols = [
        "Booking Status",               # 1
        "Therapy Name",                 # 2
        "Therapist Name",               # 3
        "Online or Physical",           # 4
        "Date Available",               # 5
        "Start Time",                   # 6
        "End Time",                     # 7
        "Faraja Center Location"        # 8
    ]

    if not df_filtered.empty:
        st.dataframe(df_filtered[display_cols], hide_index=True)
    else:
        st.warning("⚠ No sessions available for the selected filters.")
        relaxed_df = df[df["Booking Status"] != "Full"]
        relaxed_df["Date Available"] = pd.to_datetime(relaxed_df["Date Available"])
        relaxed_df["Start Time"] = pd.to_datetime(relaxed_df["Start Time"], format="%I:%M %p", errors="coerce").dt.time
        top_alternatives = relaxed_df.sort_values(by=["Date Available", "Start Time"]).head(3)
        if not top_alternatives.empty:
            st.info("🔍 Top 3 nearest available sessions based on your filters:")
            st.dataframe(top_alternatives[display_cols], hide_index=True)
        else:
            st.info("😔 No similar sessions are currently available.")

    # === Booking Section ===
    if not df_filtered.empty:
        df_filtered["session_display"] = df_filtered.apply(
            lambda row: f"{row['Therapy Name']} - {row['Therapist Name']} - {row['Faraja Center Location']} - {row['Date Available']} {row['Start Time']} to {row['End Time']} (Status: {row['Booking Status']})",
            axis=1
        )

        st.markdown("🎯 **Select a Session** – Choose the therapy session to book.")
        session_selection = st.selectbox("Select a Session", df_filtered["session_display"])
        selected_session = df_filtered[df_filtered["session_display"] == session_selection].iloc[0]

        session_index = df[
            (df["Therapy Name"] == selected_session["Therapy Name"]) &
            (df["Therapist Name"] == selected_session["Therapist Name"]) &
            (df["Date Available"] == selected_session["Date Available"]) &
            (df["Start Time"] == selected_session["Start Time"]) &
            (df["End Time"] == selected_session["End Time"])
        ].index[0]

        if selected_session["Booking Status"] == "Full":
            st.error("❌ This session is full.")
        else:
            name = st.text_input("🧑‍💼 **Full Name** – Enter your name")
            gender = st.selectbox("🚻 **Gender** – Select gender", ["Male", "Female", "Other"])
            attendee_type = st.selectbox("👥 **Attendee Type** – Patient or Caregiver", ["Patient", "Caregiver"])
            phone = st.text_input("📞 **Phone Number** – Kenyan 10-digit number")
            alt_phone = st.text_input("📱 **Alternative Phone Number** (Optional)")

            def is_valid_phone(phone): return re.fullmatch(r"07\d{8}", phone) is not None
            # validate main phone
            if phone and not is_valid_phone(phone):
                st.error("❌ Invalid! Phone number must be a valid 10-digit Kenyan phone number.")
            
            # validate alt phone
            # Validate alternative phone if provided
            if alt_phone and not is_valid_phone(alt_phone):
                st.warning("❌ Invalid! Phone number must be a valid 10-digit Kenyan phone number.")

            if phone and is_valid_phone(phone):
                if st.button("Book Now"):
                    if not name:
                        st.error("❌ Name is required.")
                    else:
                        try:
                            bookings_sheet = spreadsheet.worksheet("Bookings")
                            bookings_data = bookings_sheet.get_all_records()
                            bookings_df = pd.DataFrame(bookings_data)

                            bookings_df["Phone"] = bookings_df["Phone"].astype(str).str.zfill(10)
                            session_date = pd.to_datetime(selected_session["Date Available"]).strftime("%Y-%m-%d")
                            session_time = f"{selected_session['Start Time']} - {selected_session['End Time']}"

                            # Prevent booking same session
                            already_booked = bookings_df[
                                (bookings_df["Phone"] == phone) &
                                (bookings_df["Therapy Name"] == selected_session["Therapy Name"]) &
                                (bookings_df["Therapist"] == selected_session["Therapist Name"]) &
                                (bookings_df["Date"] == session_date) &
                                (bookings_df["Time"] == session_time)
                            ]

                            if not already_booked.empty:
                                st.error("❌ You already booked this session.")
                                st.stop()

                            # Prevent booking any other session at same time
                            overlapping = bookings_df[
                                (bookings_df["Phone"] == phone) &
                                (bookings_df["Date"] == session_date) &
                                (bookings_df["Time"] == session_time)
                            ]

                            if not overlapping.empty:
                                st.error("❌ You already have another session at the same time.")
                                st.stop()

                            status = book_session(sheet, df, session_index)
                            if status == "Success":
                                save_booking(spreadsheet, name, gender, attendee_type, phone, df.loc[session_index], alt_phone)
                                st.success("✅ Booking confirmed!")
                            else:
                                st.error("❌ This session is already full.")
                        except Exception as e:
                            st.error("❌ Error during booking.")
                            st.text(str(e))
