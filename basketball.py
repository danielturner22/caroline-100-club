import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIG & COLORS ---
st.set_page_config(page_title="Caroline's 100 Club Tracker", layout="wide")

NAVY = "#0B2240"
GOLD = "#B9975B"
BACKGROUND = "#F4F6F9"

# --- GOOGLE SHEETS SETUP ---
@st.cache_resource
def get_google_sheet():
    # This pulls your secret key from Streamlit's secure vault
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(credentials)
    # Make sure this matches your Google Sheet name exactly!
    return client.open("Caroline 100 Club").sheet1 

sheet = get_google_sheet()

def load_data():
    records = sheet.get_all_records()
    if records:
        return pd.DataFrame(records)
    else:
        columns = [
            "Date", "Handling_Done", "Drives_Done", "Spin_Done", 
            "Left_Corner", "Left_Elbow", "Right_Elbow", "Right_Corner", "Free_Throws"
        ]
        return pd.DataFrame(columns=columns)

df = load_data()

# --- SESSION STATE FOR ANIMATIONS ---
if 'show_balloons' not in st.session_state:
    st.session_state.show_balloons = False

if st.session_state.show_balloons:
    st.balloons()
    st.session_state.show_balloons = False

# --- HEADER ---
col1, col2 = st.columns([1, 4])
with col1:
    try:
        st.image("Logo_Teays-01.png", width=150)
    except:
        st.write("*(Logo not found)*")
with col2:
    st.markdown(f"<h1 style='color: {NAVY};'>Caroline's 100 Club Tracker</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: {GOLD}; font-size: 20px; font-weight: bold;'>Summer Basketball Workouts</p>", unsafe_allow_html=True)

st.markdown("---")

# --- SIDEBAR: DATA ENTRY ---
st.sidebar.header("🏀 Log Daily Workout")
with st.sidebar.form("daily_entry_form", clear_on_submit=True):
    entry_date = st.date_input("Date", date.today())
    
    st.markdown("**Daily Drills**")
    handling = st.checkbox("10 Mins - Basic Ball Handling")
    drives = st.checkbox("5 Mins - Drives to the Basket")
    spin = st.checkbox("5 Mins - Backboard Spin Study")
    
    st.markdown("**Court Shooting (Makes out of 5)**")
    left_corner = st.number_input("Left Short Corner", min_value=0, max_value=5, step=1)
    left_elbow = st.number_input("Left Elbow", min_value=0, max_value=5, step=1)
    right_elbow = st.number_input("Right Elbow", min_value=0, max_value=5, step=1)
    right_corner = st.number_input("Right Short Corner", min_value=0, max_value=5, step=1)
    
    st.markdown("**Free Throws (Makes out of 10)**")
    free_throws = st.number_input("Free Throws", min_value=0, max_value=10, step=1)
    
    submit = st.form_submit_button("Save Workout")
    
    if submit:
        days_before_save = len(df)
        
        # Format the data for Google Sheets
        row_to_insert = [
            str(entry_date), bool(handling), bool(drives), bool(spin),
            int(left_corner), int(left_elbow), int(right_elbow), int(right_corner), int(free_throws)
        ]
        
        # Append directly to Google Sheet
        sheet.append_row(row_to_insert)
        
        # Check for Milestones! 
        days_after_save = days_before_save + 1
        if days_after_save in [25, 50, 75, 100]:
            st.session_state.show_balloons = True
            
        st.success("Workout saved securely to Google Sheets!")
        st.rerun()

# --- MAIN DASHBOARD ---
if df.empty:
    st.info("👈 No data yet! Log Caroline's first workout in the sidebar to see the dashboard.")
else:
    days_completed = len(df)
    
    # Calculate Separate Totals
    df['Court_Makes'] = df['Left_Corner'] + df['Left_Elbow'] + df['Right_Elbow'] + df['Right_Corner']
    df['FT_Makes'] = df['Free_Throws']
    
    total_court_makes = df['Court_Makes'].sum()
    total_court_attempts = days_completed * 20 
    court_pct = (total_court_makes / total_court_attempts) * 100 if total_court_attempts > 0 else 0
    
    total_ft_makes = df['FT_Makes'].sum()
    total_ft_attempts = days_completed * 10
    ft_pct = (total_ft_makes / total_ft_attempts) * 100 if total_ft_attempts > 0 else 0

    # Top Row Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Days Completed", f"{days_completed} / 100")
    col2.metric("Court Makes", f"{total_court_makes} / {total_court_attempts}")
    col3.metric("Court %", f"{court_pct:.1f}%")
    col4.metric("Free Throw Makes", f"{total_ft_makes} / {total_ft_attempts}")
    col5.metric("Free Throw %", f"{ft_pct:.1f}%")

    st.markdown("---")

    # Visuals
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown(f"<h3 style='color: {NAVY}; text-align: center;'>Journey to 100 Days</h3>", unsafe_allow_html=True)
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = days_completed,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Days Completed"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': NAVY},
                'steps': [{'range': [0, 100], 'color': BACKGROUND}],
                'threshold': {'line': {'color': GOLD, 'width': 4}, 'thickness': 0.75, 'value': 100}
            }
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_chart2:
        st.markdown(f"<h3 style='color: {NAVY}; text-align: center;'>Accuracy by Location</h3>", unsafe_allow_html=True)
        spots = ['Left Corner', 'Left Elbow', 'Right Elbow', 'Right Corner', 'Free Throws']
        makes = [
            df['Left_Corner'].sum(), df['Left_Elbow'].sum(), 
            df['Right_Elbow'].sum(), df['Right_Corner'].sum(), df['Free_Throws'].sum()
        ]
        attempts = [days_completed * 5, days_completed * 5, days_completed * 5, days_completed * 5, days_completed * 10]
        percentages = [(m / a * 100) if a > 0 else 0 for m, a in zip(makes, attempts)]
        
        fig_bar = px.bar(x=spots, y=percentages, labels={'x': 'Location', 'y': 'Shooting Percentage (%)'}, color_discrete_sequence=[GOLD])
        fig_bar.update_layout(yaxis_range=[0, 100], plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown(f"<h3 style='color: {NAVY}; text-align: center;'>Daily Shooting Trend</h3>", unsafe_allow_html=True)
    df['Court_Pct'] = (df['Court_Makes'] / 20) * 100
    df['FT_Pct'] = (df['FT_Makes'] / 10) * 100
    df_chart = df[['Date', 'Court_Pct', 'FT_Pct']].copy()
    df_chart.rename(columns={'Court_Pct': 'Court Shots', 'FT_Pct': 'Free Throws'}, inplace=True)
    
    fig_line = px.line(df_chart, x='Date', y=['Court Shots', 'Free Throws'], markers=True, labels={'value': 'Shooting %', 'Date': 'Date', 'variable': 'Shot Type'}, color_discrete_map={'Court Shots': NAVY, 'Free Throws': GOLD})
    fig_line.update_layout(yaxis_range=[0, 100], plot_bgcolor=BACKGROUND, legend_title_text='')
    st.plotly_chart(fig_line, use_container_width=True)
