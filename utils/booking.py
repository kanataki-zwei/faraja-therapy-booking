import gspread

def book_session(sheet, df, session_index):
    """Update session details in Google Sheets"""
    try:
        max_attendees = int(df.at[session_index, "Maximum Attendees"])  # Ensure int type
        current_attendees = int(df.at[session_index, "Current Attendees"])  # Convert int64 to int

        if current_attendees < max_attendees:
            df.at[session_index, "Current Attendees"] += 1
            df.at[session_index, "Current Attendees"] = int(df.at[session_index, "Current Attendees"])  # Convert to int again

            if df.at[session_index, "Current Attendees"] == max_attendees:
                df.at[session_index, "Booking Status"] = "Full"

            # ✅ Convert `numpy.int64` to standard Python int before updating Google Sheets
            sheet.update(f"F{session_index+2}", [[int(df.at[session_index, "Current Attendees"])]])
            sheet.update(f"H{session_index+2}", [[str(df.at[session_index, "Booking Status"])]])  # Convert status to str

            return "Success"
        return "Full"

    except Exception as e:
        print(f"❌ Error updating session in Google Sheets: {e}")
        return "Error"

def save_booking(spreadsheet, name, attendee_type, phone, session_details):
    """Store user booking details in a 'Bookings' tab in Google Sheets"""
    try:
        # ✅ Open the full Spreadsheet
        try:
            bookings_sheet = spreadsheet.worksheet("Bookings")
        except gspread.WorksheetNotFound:
            # ✅ Create "Bookings" tab if it doesn't exist
            bookings_sheet = spreadsheet.add_worksheet(title="Bookings", rows="1000", cols="7")
            bookings_sheet.append_row(["Name", "Attendee Type", "Phone", "Therapy Name", "Therapist", "Date", "Time"])
            print("✅ Created 'Bookings' worksheet")

        # ✅ Append user booking data
        booking_data = [
            name, 
            attendee_type, 
            phone, 
            session_details["Therapy Name"], 
            session_details["Therapist Name"], 
            session_details["Date Available"], 
            f"{session_details['Start Time']} - {session_details['End Time']}"
        ]
        bookings_sheet.append_row(booking_data)
        print("✅ Booking saved successfully!")

    except Exception as e:
        print(f"❌ Error saving booking in Google Sheets: {e}")
