import gspread
import pandas as pd  # Required for generating timestamps

def book_session(sheet, df, session_index):
    """Update session details in Google Sheets"""
    try:
        # ✅ Read Maximum Attendees (column H / index 7)
        max_raw = df.at[session_index, "Maximum Attendees"]
        max_attendees = int(max_raw) if str(max_raw).strip().isdigit() else 0

        # ✅ Read Current Attendees (column I / index 8)
        current_raw = df.at[session_index, "Current Attendees"]
        current_attendees = int(current_raw) if str(current_raw).strip().isdigit() else 0

        if current_attendees < max_attendees:
            current_attendees += 1
            booking_status = "Full" if current_attendees == max_attendees else "Available"

            # ✅ Update in-memory DataFrame
            df.at[session_index, "Current Attendees"] = current_attendees
            df.at[session_index, "Booking Status"] = booking_status

            # ✅ Update Google Sheets (column I = Current Attendees, J = Booking Status)
            sheet.update(f"I{session_index + 2}", [[str(current_attendees)]])
            sheet.update(f"J{session_index + 2}", [[booking_status]])

            return "Success"

        return "Full"

    except Exception as e:
        print(f"❌ Error updating session in Google Sheets: {e}")
        return "Error"


def save_booking(spreadsheet, name, gender, attendee_type, phone, session_details):
    """Store user booking details in a 'Bookings' tab in Google Sheets"""
    try:
        # ✅ Access or create the 'Bookings' worksheet
        try:
            bookings_sheet = spreadsheet.worksheet("Bookings")
        except gspread.WorksheetNotFound:
            bookings_sheet = spreadsheet.add_worksheet(title="Bookings", rows="1000", cols="11")
            bookings_sheet.append_row([
                "Name", "Attendee Type", "Gender", "Phone", "Therapy Name",
                "Therapist", "Date", "Time", "Location", "Format", "Timestamp"
            ])
            print("✅ Created 'Bookings' worksheet")

        # ✅ Prepare booking data (with correct order: attendee_type ➝ gender)
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
            pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")  # Timestamp
        ]

        bookings_sheet.append_row(booking_data)
        print("✅ Booking saved successfully!")

    except Exception as e:
        print(f"❌ Error saving booking in Google Sheets: {e}")
