import gspread
import pandas as pd  # Required for generating timestamps

def book_session(sheet, df, session_index):
    try:
        max_raw = df.at[session_index, "Maximum Attendees"]
        max_attendees = int(max_raw) if str(max_raw).strip().isdigit() else 0

        current_raw = df.at[session_index, "Current Attendees"]
        current_attendees = int(current_raw) if str(current_raw).strip().isdigit() else 0

        if current_attendees < max_attendees:
            current_attendees += 1
            booking_status = "Full" if current_attendees == max_attendees else "Available"

            df.at[session_index, "Current Attendees"] = current_attendees
            df.at[session_index, "Booking Status"] = booking_status

            sheet.update(f"I{session_index + 2}", [[str(current_attendees)]])
            sheet.update(f"J{session_index + 2}", [[booking_status]])

            return "Success"

        return "Full"

    except Exception as e:
        print(f"❌ Error updating session in Google Sheets: {e}")
        return "Error"

def save_booking(spreadsheet, name, gender, attendee_type, phone, session_details):
    try:
        try:
            bookings_sheet = spreadsheet.worksheet("Bookings")
        except gspread.WorksheetNotFound:
            bookings_sheet = spreadsheet.add_worksheet(title="Bookings", rows="1000", cols="14")
            bookings_sheet.append_row([
                "Name", "Attendee Type", "Gender", "Phone", "Therapy Name",
                "Therapist", "Date", "Time", "Faraja Center Location", "Online or Physical",
                "Timestamp", "is_cancelled", "is_rescheduled", "reason"
            ])

        booking_data = [
            name,
            attendee_type,
            gender,
            phone,
            session_details["Therapy Name"],
            session_details["Therapist Name"],
            session_details["Date Available"],
            f"{session_details['Start Time']} - {session_details['End Time']}",
            session_details["Faraja Center Location"],
            session_details["Online or Physical"],
            pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            False,  # is_cancelled
            False,  # is_rescheduled
            ""       # reason
        ]

        bookings_sheet.append_row(booking_data)

    except Exception as e:
        print(f"❌ Error saving booking in Google Sheets: {e}")

def cancel_booking(spreadsheet, selected_session, reason):
    try:
        bookings_sheet = spreadsheet.worksheet("Bookings")
        bookings_data = bookings_sheet.get_all_records()
        df = pd.DataFrame(bookings_data)

        # Clean up phone and date just in case
        df["Phone"] = df["Phone"].astype(str).str.strip().str.zfill(10)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        session_match = (
            (df["Phone"] == selected_session["Phone"]) &
            (df["Therapy Name"] == selected_session["Therapy Name"]) &
            (df["Therapist"] == selected_session["Therapist"]) &
            (df["Date"].dt.date == selected_session["Date"].date()) &
            (df["Time"] == selected_session["Time"])
        )

        if not session_match.any():
            print("❌ No matching session found in Bookings sheet.")
            return

        row_index = df[session_match].index[0] + 2  # account for header row

        # ✅ Update cancellation and reason
        bookings_sheet.update(f"L{row_index}", [["TRUE"]])
        bookings_sheet.update(f"N{row_index}", [[reason]])

        # ✅ Decrement session's attendee count
        session_sheet = spreadsheet.sheet1
        sessions = pd.DataFrame(session_sheet.get_all_records())

        session_row = sessions[
            (sessions["Therapy Name"] == selected_session["Therapy Name"]) &
            (sessions["Therapist Name"] == selected_session["Therapist"]) &
            (sessions["Date Available"] == str(selected_session["Date"].date())) &
            (sessions["Start Time"] == selected_session["Time"].split(" - ")[0]) &
            (sessions["End Time"] == selected_session["Time"].split(" - ")[1])
        ]

        if not session_row.empty:
            session_idx = session_row.index[0]
            raw_attendees = sessions.at[session_idx, "Current Attendees"]
            current_attendees = int(raw_attendees) if str(raw_attendees).strip().isdigit() else 0

            updated_count = max(current_attendees - 1, 0)

            max_attendees = int(sessions.at[session_idx, "Maximum Attendees"])
            new_status = "Available" if updated_count < max_attendees else "Full"

            session_sheet.update(f"I{session_idx + 2}", [[updated_count]])
            session_sheet.update(f"J{session_idx + 2}", [[new_status]])

    except Exception as e:
        print(f"❌ Error cancelling booking: {e}")
