import streamlit as st
import pandas as pd

# -------------------------------
#  Simple Authentication
# -------------------------------
def login():
    st.title("🔐 Login to Horse Racing Dashboard")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if username in credentials and credentials[username] == password:
                st.success("Login successful! Press Login again to view Dashboard.")
                st.session_state["authenticated"] = True
            else:
                st.error("Invalid username or password")

# Dummy credentials dictionary
credentials = {
    "admin": "admin",
}

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Show login screen if not authenticated
if not st.session_state["authenticated"]:
    login()
    st.stop()  

# -------------------------------
#  Authenticated App Starts Here
# -------------------------------

# Set wide layout
st.set_page_config(page_title="Horse Racing Dashboard", layout="wide")

# --- Load Data ---
@st.cache_data
def load_data():
    df = pd.read_csv(r"main.csv", parse_dates=["MeetingDate"])
    return df

df = load_data()

# --- Top Filters (Navbar style) ---
with st.container():
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

    with col1:
        selected_date = st.date_input("📅 Date", df["MeetingDate"].max())

    filtered_df = df[df["MeetingDate"] == pd.to_datetime(selected_date)]

    with col2:
        track_options = filtered_df["Track"].dropna().unique()
        selected_track = st.selectbox("📍 Track", sorted(track_options))

    filtered_df = filtered_df[filtered_df["Track"] == selected_track]

    with col3:
        race_options = filtered_df["RaceNumber"].dropna().unique()
        selected_race = st.selectbox("🏁 Race", sorted(race_options))

    filtered_df = filtered_df[filtered_df["RaceNumber"] == selected_race]

    with col4:
        csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{selected_track}_Race{selected_race}_{selected_date}.csv",
            mime="text/csv"
        )

# --- Display Section ---
st.markdown(f"## 🏇 Race on {selected_date.strftime('%d %b %Y')} | {selected_track} | Race {selected_race}")

# Sort by Tab No. (for natural order)
filtered_df = filtered_df.sort_values(by="TabNo", ascending=True)

# Columns to display
display_cols = [
    "Track", "TabNo", "Name", "Jockey.FullName", "Trainer.FullName",
    "NormalizedWinProbability","Odds", "Price", "Weight", "Barrier_x", "Last10",
    "RaceId", "RunnerId"
]

# Friendly column names
friendly_names = {
    "TabNo": "Tab No.",
    "Name": "Horse",
    "Jockey.FullName": "Jockey",
    "Trainer.FullName": "Trainer",
    "NormalizedWinProbability": "Win Prob",
    "Barrier_x": "Barrier",
    "Last10": "Last 10",
    "RaceId": "Race ID",
    "RunnerId": "Runner ID"
}

# Prepare display DataFrame
display_df = filtered_df[display_cols].rename(columns=friendly_names)
display_df = display_df.reset_index(drop=True)
display_df.index+=1
display_df.index.name="No."

# Display
st.dataframe(
    display_df,
    use_container_width=True,
    height=550
)
