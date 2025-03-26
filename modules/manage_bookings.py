import streamlit as st
import pandas as pd
import re
from utils.gsheet import connect_to_gsheet
from utils.booking import cancel_booking

def is_valid_kenyan_phone(phone):
    return re.fullmatch(r"07\d{8}", phone) is not None

def render_manage_bookings():
    st.subheader("Manage Your Bookings")
    st.info("Enter your phone number to reschedule or cancel your booking.")

    phone_lookup = st.text_input("Enter your phone number (e.g., 07XXXXXXXX)")

    if phone_lookup and not is_valid_kenyan_phone(phone_lookup):
        st.error("❌ Please enter a valid 10-digit Kenyan phone number starting with 07.")
        st.stop()

    if phone_lookup:
        try:
            client, spreadsheet, sheet = connect_to_gsheet()

            bookings_sheet = spreadsheet.worksheet("Bookings")
            bookings_data = bookings_sheet.get_all_records()
            bookings_df = pd.DataFrame(bookings_data)

            bookings_df["Phone"] = bookings_df["Phone"].astype(str).str.zfill(10)
            bookings_df["Date"] = pd.to_datetime(bookings_df["Date"].astype(str).str.strip(), format="%Y-%m-%d", errors="coerce")
            today = pd.to_datetime(pd.Timestamp.today().date())
            upcoming_bookings = bookings_df[(bookings_df["Phone"] == phone_lookup) & (bookings_df["Date"] >= today) & (bookings_df["is_cancelled"] != True)]

            if upcoming_bookings.empty:
                st.warning("No upcoming bookings found for this number.")
                st.write("Debug: Parsed Dates", bookings_df[["Phone", "Date"]])
                return

            therapies = sorted(upcoming_bookings["Therapy Name"].dropna().unique())
            selected_therapy = st.selectbox("Select Therapy", ["All"] + therapies)
            filtered_by_therapy = upcoming_bookings if selected_therapy == "All" else upcoming_bookings[upcoming_bookings["Therapy Name"] == selected_therapy]

            therapists = sorted(filtered_by_therapy["Therapist"].dropna().unique())
            selected_therapist = st.selectbox("Select Therapist", ["All"] + therapists)
            filtered_by_therapist = filtered_by_therapy if selected_therapist == "All" else filtered_by_therapy[filtered_by_therapy["Therapist"] == selected_therapist]

            session_options = filtered_by_therapist.apply(
                lambda row: f"{row['Therapy Name']} with {row['Therapist']} on {row['Date'].date()} at {row['Time']}",
                axis=1
            ).tolist()

            if not session_options:
                st.warning("No matching sessions found with selected filters.")
                return

            selected_session_label = st.selectbox("Select a session to manage", session_options)
            selected_session_index = session_options.index(selected_session_label)
            selected_session = filtered_by_therapist.iloc[selected_session_index]

            action = st.radio("What would you like to do?", ["Cancel", "Reschedule"])

            if action == "Cancel":
                reason = st.text_area("Reason for cancellation")
                if st.button("Confirm Cancellation"):
                    cancel_booking(spreadsheet, selected_session, reason)
                    st.success("✅ Booking cancellation saved.")
                    st.info(f"Cancelled: {selected_session_label}\nReason: {reason}")

            elif action == "Reschedule":
                st.markdown("### 📆 Select a new session")
                session_sheet = spreadsheet.sheet1
                all_sessions_df = pd.DataFrame(session_sheet.get_all_records())

                all_sessions_df["Date Available"] = pd.to_datetime(all_sessions_df["Date Available"].astype(str).str.strip(), errors="coerce")
                all_sessions_df = all_sessions_df[all_sessions_df["Booking Status"] != "Full"]
                all_sessions_df = all_sessions_df[all_sessions_df["Date Available"] >= today]
                all_sessions_df = all_sessions_df.sort_values(by=["Date Available", "Start Time"]).head(3)

                if all_sessions_df.empty:
                    st.warning("No sessions available to reschedule.")
                    return

                session_dropdown = all_sessions_df.apply(
                    lambda row: f"{row['Therapy Name']} with {row['Therapist Name']} on {row['Date Available'].date()} at {row['Start Time']}",
                    axis=1
                ).tolist()

                new_session = st.selectbox("Choose a new session", session_dropdown)
                reason = st.text_area("Reason for rescheduling")

                if st.button("Confirm Reschedule"):
                    st.success("✅ Booking rescheduled.")
                    st.info(f"Moved to: {new_session}\nReason: {reason}")

        except Exception as e:
            st.error("❌ Could not fetch bookings.")
            st.text(str(e))
