import streamlit as st
import pandas as pd
from utils.gsheet import connect_to_gsheet

def render_manage_bookings():
    st.subheader("Manage Your Bookings")
    st.info("You can reschedule or cancel your session. Enter your phone number to continue.")

    phone_lookup = st.text_input("Enter your phone number to find your booking")
    action = st.radio("What would you like to do?", ["Reschedule", "Cancel"])
    reason = st.text_area("Please provide a reason for this action")

    if st.button("Find My Bookings") and phone_lookup:
        try:
            # ✅ Connect to Google Sheets using secrets
            client, spreadsheet, sheet = connect_to_gsheet()

            bookings_sheet = spreadsheet.worksheet("Bookings")
            bookings_data = bookings_sheet.get_all_records()
            bookings_df = pd.DataFrame(bookings_data)
            user_bookings = bookings_df[bookings_df["Phone"] == phone_lookup]

            if user_bookings.empty:
                st.warning("No bookings found for this phone number.")
            else:
                st.success(f"Found {len(user_bookings)} booking(s)")
                st.dataframe(user_bookings, hide_index=True)

                st.warning("⚠️ Reschedule/cancel logic will go here.")
                st.text("(To be implemented: select one, update/delete it, log the reason)")

        except Exception as e:
            st.error("❌ Could not fetch bookings.")
            st.text(str(e))
