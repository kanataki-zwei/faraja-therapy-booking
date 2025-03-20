def filter_sessions(df, therapy_name, therapist_name, date):
    if therapy_name != "All":
        df = df[df["Therapy Name"] == therapy_name]
    if therapist_name != "All":
        df = df[df["Therapist Name"] == therapist_name]
    if date:
        df = df[df["Date Available"] == date.strftime("%Y-%m-%d")]
    return df
