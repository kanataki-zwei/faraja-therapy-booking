import streamlit as st
import pandas as pd
import re
from utils.gsheet import connect_to_gsheet
from utils.booking import cancel_booking, save_booking


def is_valid_kenyan_phone(phone):
    return re.fullmatch(r"(07|01)\d{8}", phone) is not None


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
            upcoming_bookings = bookings_df[
                (bookings_df["Phone"] == phone_lookup) &
                (bookings_df["Date"] >= today) &
                (bookings_df["is_cancelled"] != True)
            ]

            if upcoming_bookings.empty:
                st.warning("No upcoming bookings found for this number.")
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
                if not reason.strip():
                    st.error("Please provide a reason for cancellation.")
                elif st.button("Confirm Cancellation"):
                    cancel_booking(spreadsheet, selected_session, reason)
                    st.success("✅ Booking cancellation saved.")
                    st.info(f"Cancelled: {selected_session_label}\nReason: {reason}")

            elif action == "Reschedule":
                st.markdown("### 📆 Select a new session")
                session_sheet = spreadsheet.worksheet("therapy_booking_data")
                all_sessions_df = pd.DataFrame(session_sheet.get_all_records())

                all_sessions_df["Date Available"] = pd.to_datetime(all_sessions_df["Date Available"].astype(str).str.strip(), errors="coerce")
                all_sessions_df = all_sessions_df[all_sessions_df["Booking Status"] != "Full"]
                all_sessions_df = all_sessions_df[all_sessions_df["Date Available"] >= today]

                all_sessions_df = all_sessions_df[all_sessions_df["Therapy Name"] == selected_session["Therapy Name"]]

                st.markdown("📅 Select a date range to see available sessions")
                start_date = st.date_input("Start Date (Reschedule)", min_value=today, value=today)
                end_date = st.date_input("End Date (Reschedule)", min_value=start_date, value=today + pd.Timedelta(days=7))
                all_sessions_df = all_sessions_df[
                    (all_sessions_df["Date Available"] >= pd.to_datetime(start_date)) &
                    (all_sessions_df["Date Available"] <= pd.to_datetime(end_date))
                ]

                session_dropdown = all_sessions_df.apply(
                    lambda row: f"{row['Therapy Name']} with {row['Therapist Name']} on {row['Date Available'].date()} at {row['Start Time']} - {row['End Time']}",
                    axis=1
                ).tolist()

                if not session_dropdown:
                    st.warning("No available sessions in the selected date range.")
                    return

                new_session_display = st.selectbox("Choose a new session", session_dropdown)
                new_session = all_sessions_df.iloc[session_dropdown.index(new_session_display)]
                reason = st.text_area("Reason for rescheduling")

                booked_times = bookings_df[(bookings_df["Phone"] == phone_lookup) & (bookings_df["is_cancelled"] != True) & (bookings_df["is_rescheduled"] != True)]
                new_time_str = f"{new_session['Start Time']} - {new_session['End Time']}"
                already_booked_time = booked_times[
                    (booked_times["Date"] == new_session["Date Available"]) &
                    (booked_times["Time"] == new_time_str)
                ]

                if not reason.strip():
                    st.error("Please provide a reason for rescheduling.")
                elif not already_booked_time.empty:
                    st.error("❌ You already have another session booked at this date and time.")
                elif st.button("Confirm Reschedule"):
                    match = (
                        (bookings_df["Phone"] == selected_session["Phone"]) &
                        (bookings_df["Therapy Name"] == selected_session["Therapy Name"]) &
                        (bookings_df["Therapist"] == selected_session["Therapist"]) &
                        (bookings_df["Date"].dt.date == selected_session["Date"].date()) &
                        (bookings_df["Time"] == selected_session["Time"])
                    )
                    if match.any():
                        row_index = bookings_df[match].index[0] + 2
                        bookings_sheet.update(f"M{row_index}", [["TRUE"]])
                        bookings_sheet.update(f"N{row_index}", [[reason]])

                    session_match_df = pd.DataFrame(session_sheet.get_all_records())
                    session_match_df["Date Available"] = pd.to_datetime(session_match_df["Date Available"], errors="coerce")
                    match_session = (
                        (session_match_df["Therapy Name"] == selected_session["Therapy Name"]) &
                        (session_match_df["Therapist Name"] == selected_session["Therapist"]) &
                        (session_match_df["Date Available"] == selected_session["Date"]) &
                        (session_match_df["Start Time"] == selected_session["Time"].split(" - ")[0]) &
                        (session_match_df["End Time"] == selected_session["Time"].split(" - ")[1])
                    )
                    if match_session.any():
                        idx = session_match_df[match_session].index[0]
                        current_attendees = session_match_df.at[idx, "Current Attendees"]
                        updated = max(int(current_attendees) - 1, 0)
                        session_sheet.update(f"I{idx+2}", [[updated]])

                        max_attendees = int(session_match_df.at[idx, "Maximum Attendees"])
                        new_status = "Available" if updated < max_attendees else "Full"
                        session_sheet.update(f"J{idx+2}", [[new_status]])

                    # ✅ Save new session as new booking
                    save_booking(
                        spreadsheet,
                        selected_session["Name"],
                        selected_session["Gender"],
                        selected_session["Attendee Type"],
                        selected_session["Phone"],
                        new_session
                    )

                    # ✅ Increment new session's attendees
                    session_match_df = pd.DataFrame(session_sheet.get_all_records())
                    session_match_df["Date Available"] = pd.to_datetime(session_match_df["Date Available"], errors="coerce")
                    match_new = (
                        (session_match_df["Therapy Name"] == new_session["Therapy Name"]) &
                        (session_match_df["Therapist Name"] == new_session["Therapist Name"]) &
                        (session_match_df["Date Available"] == new_session["Date Available"]) &
                        (session_match_df["Start Time"] == new_session["Start Time"]) &
                        (session_match_df["End Time"] == new_session["End Time"])
                    )
                    if match_new.any():
                        new_idx = session_match_df[match_new].index[0]
                        raw_current = session_match_df.at[new_idx, "Current Attendees"]
                        new_current = int(raw_current) + 1 if str(raw_current).strip().isdigit() else 1
                        session_sheet.update(f"I{new_idx+2}", [[new_current]])

                        max_cap = int(session_match_df.at[new_idx, "Maximum Attendees"])
                        updated_status = "Full" if new_current >= max_cap else "Available"
                        session_sheet.update(f"J{new_idx+2}", [[updated_status]])

                    st.success("✅ Booking rescheduled.")
                    st.info(f"Moved to: {new_session_display}\nReason: {reason}")

        except Exception as e:
            st.error("❌ Could not fetch bookings.")
            st.text(str(e))
