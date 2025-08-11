import streamlit as st
import pandas as pd

# --- Authentication ---
def login():
    st.title("🔐 Login to Horse Racing Dashboard")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        if submit:
            if username in credentials and credentials[username] == password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Invalid username or password")

credentials = {"admin": "admin"}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
    st.stop()

# --- Main App ---
st.set_page_config(page_title="Horse Racing Dashboard", layout="wide")

# Model configuration
MODEL_FILES = {
    "RandomForest": "random_forest.csv",
    "Logistic": "logistic.csv",
    "XGBoost": "xgboost.csv"
}

# Initialize session state
if "selected_model" not in st.session_state:
    st.session_state["selected_model"] = "RandomForest"

@st.cache_data
def load_data(filename):
    return pd.read_csv(filename, parse_dates=["MeetingDate"])

# Load data based on selected model
try:
    df = load_data(MODEL_FILES[st.session_state["selected_model"]])
except FileNotFoundError:
    st.error(f"Data file not found for {st.session_state['selected_model']} model")
    st.stop()

# --- Header Section ---
st.markdown("""
    <style>
    .header-style {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .download-btn {
        padding-top: 0px;
    }
    .download-container {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    </style>
""", unsafe_allow_html=True)

with st.container():
    col_date, col_track, col_race, col_model, col_space, col_download = st.columns([2, 2, 2, 3,4, 3])

    # Date selection
    with col_date:
        selected_date = st.date_input("📅 Date", df["MeetingDate"].max())
    
    # Filter data for selected date
    day_df = df[df["MeetingDate"] == pd.to_datetime(selected_date)]
    filtered_df = df[df["MeetingDate"] == pd.to_datetime(selected_date)]

    # Track selection
    with col_track:
        track_options = day_df["Track"].dropna().unique()
        if len(track_options) == 0:
            st.error("No data for selected date and model.")
            st.stop()
        selected_track = st.selectbox("📍 Track", sorted(track_options))

    # Race selection
    with col_race:
        race_options = day_df[day_df["Track"] == selected_track]["RaceNumber"].dropna().unique()
        selected_race = st.selectbox("🏁 Race", sorted(race_options))
        filtered_df = filtered_df[filtered_df["RaceNumber"] == selected_race]

    # Model selection with immediate update
    with col_model:
        new_model = st.selectbox(
            "📊 Model", 
            list(MODEL_FILES.keys()),
            index=list(MODEL_FILES.keys()).index(st.session_state["selected_model"]),
            key="model_selectbox"
        )
        
        if new_model != st.session_state["selected_model"]:
            st.session_state["selected_model"] = new_model
            st.rerun()
    
    # Download buttons (stacked vertically)
    with col_download:
        st.markdown('<div class="download-container">', unsafe_allow_html=True)
        
        # Race download button (top)
        race_csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Race CSV",
            data=race_csv,
            file_name=f"{selected_track}_Race{selected_race}_{selected_date}.csv",
            mime="text/csv",
            key="race_download"
        )
        
        # Day download button (bottom)
        day_csv = day_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Day CSV",
            data=day_csv,
            file_name=f"All_Races_{selected_date}_{st.session_state['selected_model']}.csv",
            mime="text/csv",
            key="day_download"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- Main Display ---
st.markdown(f"""
    ## 🏇 Race on {selected_date.strftime('%d %b %Y')} | {selected_track} | Race {selected_race} | Model: {st.session_state['selected_model']}
""")

# Filter and display race data
filtered_df = day_df[(day_df["Track"] == selected_track) & (day_df["RaceNumber"] == selected_race)]
filtered_df = filtered_df.sort_values(by="TabNo", ascending=True)

# Configure display columns
DISPLAY_COLS = [
    "Track", "TabNo", "Name", "Jockey.FullName", "Trainer.FullName",
    "NormalizedWinProbability", 'Odds', "Price", "Weight", "Barrier_x", "Last10",
    "RaceId", "RunnerId"
]

FRIENDLY_NAMES = {
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

# Format and display the dataframe
display_df = filtered_df[DISPLAY_COLS].rename(columns=FRIENDLY_NAMES).reset_index(drop=True)
display_df['Odds'] = display_df['Odds'].astype(float).round(3)  
display_df.index += 1
display_df.index.name = "No."

st.dataframe(display_df, use_container_width=True, height=550)