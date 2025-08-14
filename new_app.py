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

# Model files
MODEL_FILES = {
    "RandomForest": "random_forest.csv",
    "Logistic": "logistic.csv",
    "XGBoost": "xgboost.csv",
}

# Load data
@st.cache_data
def load_data(filename):
    return pd.read_csv(filename)

try:
    base_df = load_data(MODEL_FILES["RandomForest"])
    logistic_df = load_data(MODEL_FILES["Logistic"])
    xgboost_df = load_data(MODEL_FILES["XGBoost"])
except FileNotFoundError as e:
    st.error(f"Data file not found: {e}")
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
    col_date, col_track, col_race, col_space, col_download = st.columns([3, 3, 3, 5, 3])

    # Date selection
    with col_date:
        base_df['MeetingDate'] = pd.to_datetime(base_df['MeetingDate'], errors='coerce')
        selected_date = st.date_input("📅 Date", base_df["MeetingDate"].max()) 
        print(selected_date)
        print(type(selected_date))

    # Filter data for selected date
    day_df = base_df[base_df["MeetingDate"] == pd.to_datetime(selected_date)]
    if day_df.empty:
        st.error("No data for selected date.")
        st.stop()

    # Track selection
    with col_track:
        track_options = day_df["Track"].dropna().unique()
        selected_track = st.selectbox("📍 Track", sorted(track_options))

    # Race selection
    with col_race:
        race_options = day_df[day_df["Track"] == selected_track]["RaceNumber"].dropna().unique()
        selected_race = st.selectbox("🏁 Race", sorted(race_options))

    # Download buttons
    with col_download:
        st.markdown('<div class="download-container">', unsafe_allow_html=True)
        
        race_csv = day_df[day_df["RaceNumber"] == selected_race].to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Race CSV",
            data=race_csv,
            file_name=f"{selected_track}_Race{selected_race}_{selected_date}.csv",
            mime="text/csv"
        )

        day_csv = day_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Day CSV",
            data=day_csv,
            file_name=f"All_Races_{selected_date}_RandomForest.csv",
            mime="text/csv"
        )
        st.markdown('</div>', unsafe_allow_html=True)

# --- Merge odds from other models ---
def add_model_odds(main_df, other_df, model_name):
    # Merge based on RaceId & RunnerId to align horses correctly
    odds_col_name = f"Odds_{model_name}"
    other_odds = other_df[["RaceId", "RunnerId", "Odds"]].rename(columns={"Odds": odds_col_name})
    return main_df.merge(other_odds, on=["RaceId", "RunnerId"], how="left")

filtered_df = day_df[(day_df["Track"] == selected_track) & (day_df["RaceNumber"] == selected_race)]

filtered_df = add_model_odds(filtered_df, logistic_df, "Logistic")
filtered_df = add_model_odds(filtered_df, xgboost_df, "XGBoost")
#filtered_df = add_model_odds(filtered_df, bayesian_df, "BayesianNew")

# --- Display ---
DISPLAY_COLS = [
    "Track", "TabNo", "Name", "Jockey.FullName", "Trainer.FullName",
     "Odds", "Odds_Logistic", "Odds_XGBoost",
    "Price", "Weight", "Barrier_x", "Last10", "RaceId", "RunnerId"
]

FRIENDLY_NAMES = {
    "TabNo": "Tab No.",
    "Name": "Horse",
    "Jockey.FullName": "Jockey",
    "Trainer.FullName": "Trainer",
    #"NormalizedWinProbability": "Win Prob",
    "Barrier_x": "Barrier",
    "Last10": "Last 10",
    "RaceId": "Race ID",
    "RunnerId": "Runner ID",
    "Odds": "Odds_RF",
    "Odds_Logistic": "Odds_Log",
    "Odds_XGBoost" :"Odds_Xg",
    
}

display_df = filtered_df[DISPLAY_COLS].rename(columns=FRIENDLY_NAMES).reset_index(drop=True)
for col in ["Odds_RF", "Odds_Log", "Odds_Xg"]:
    display_df[col] = display_df[col].astype(float).round(3)

display_df.index += 1
display_df.index.name = "No."

st.markdown(f"""
    ## 🏇 Race on {selected_date.strftime('%d %b %Y')} | {selected_track} | Race {selected_race} | Model: RandomForest + Other Odds
""")
st.dataframe(display_df, use_container_width=True, height=550)
