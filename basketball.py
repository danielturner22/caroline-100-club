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
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    client = gspread.authorize(credentials)
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
        
        row_to_insert = [
            str(entry_date), bool(handling), bool(drives), bool(spin),
            int(left_corner), int(left_elbow), int(right_elbow), int(right_corner), int(free_throws)
        ]
        
        sheet.append_row(row_to_insert)
        
        days_after_save = days_before_save + 1
        if days_after_save in [25, 50, 75, 100]:
            st.session_state.show_balloons = True
            
        st.success("Workout saved securely to Google Sheets!")
        st.rerun()

# --- MAIN DASHBOARD ---
if df.empty:
    st.info("👈 No data yet! Log Caroline's first workout in the sidebar to see the dashboard.")
else:
    # 1. CLEAN & SORT DATES (Oldest to Newest)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by='Date').reset_index(drop=True)
    days_completed = len(df)
    
    # Calculate Totals
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

    # --- TROPHY ROOM (PERSONAL BESTS) ---
    st.markdown(f"<h3 style='color: {NAVY}; text-align: center;'>🏆 Trophy Room: Personal Bests</h3>", unsafe_allow_html=True)
    col_pb1, col_pb2 = st.columns(2)
    
    best_court = df.loc[df['Court_Makes'].idxmax()]
    col_pb1.success(f"**🔥 Most Court Shots Made:** {best_court['Court_Makes']} / 20  *(Set on {best_court['Date'].strftime('%b %d')})*")
    
    best_ft = df.loc[df['Free_Throws'].idxmax()]
    col_pb2.success(f"**🎯 Best Free Throw Day:** {best_ft['Free_Throws']} / 10  *(Set on {best_ft['Date'].strftime('%b %d')})*")
    
    st.markdown("---")

    # Visuals Row
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown(f"<h3 style='color: {NAVY}; text-align: center;'>Journey to 100 Days</h3>", unsafe_allow_html=True)
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = days_completed,
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': NAVY},
                'steps': [{'range': [0, 100], 'color': BACKGROUND}],
                'threshold': {'line': {'color': GOLD, 'width': 4}, 'thickness': 0.75, 'value': 100}
            }
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_chart2:
        # --- VISUAL COURT HEATMAP ---
        st.markdown(f"<h3 style='color: {NAVY}; text-align: center;'>Shooting Heatmap</h3>", unsafe_allow_html=True)
        spots = ['Left Corner', 'Left Elbow', 'Right Elbow', 'Right Corner', 'Free Throws']
        makes = [df['Left_Corner'].sum(), df['Left_Elbow'].sum(), df['Right_Elbow'].sum(), df['Right_Corner'].sum(), df['Free_Throws'].sum()]
        attempts = [days_completed * 5] * 4 + [days_completed * 10]
        percentages = [(m / a * 100) if a > 0 else 0 for m, a in zip(makes, attempts)]
        
        # Coordinates using true High School basketball court proportions
        court_data = pd.DataFrame({
            'Spot': spots,
            'X': [-16, -6, 6, 16, 0],
            'Y': [5, 19, 19, 5, 19],
            'Percentage': percentages,
            'Makes': makes,
            'Attempts': attempts,
            'MarkerSize': [45, 45, 45, 45, 45]
        })
        
        fig_heatmap = px.scatter(
            court_data, x='X', y='Y', size='MarkerSize', color='Percentage',
            text='Spot', hover_data={'MarkerSize': False, 'X': False, 'Y': False, 'Makes': True, 'Attempts': True, 'Percentage': ':.1f'},
            color_continuous_scale='RdYlGn', range_color=[0, 100]
        )
        
        fig_heatmap.update_traces(textposition='top center', textfont=dict(color=NAVY, size=14, family="Arial Black"))
        
        fig_heatmap.update_layout(
            xaxis=dict(range=[-22, 22], visible=False),
            yaxis=dict(
                range=[-2, 28], 
                visible=False, 
                scaleanchor="x",    
                scaleratio=1        
            ),
            height=450,
            plot_bgcolor=BACKGROUND, coloraxis_showscale=True,
            margin=dict(l=0, r=0, t=20, b=10)
        )
        
        # Draw the virtual court lines with real dimensions
        fig_heatmap.add_shape(type="rect", x0=-6, y0=0, x1=6, y1=19, line=dict(color=NAVY, width=2), fillcolor="rgba(11, 34, 64, 0.05)") 
        fig_heatmap.add_shape(type="circle", x0=-6, y0=13, x1=6, y1=25, line=dict(color=NAVY, width=2)) 
        fig_heatmap.add_shape(type="circle", x0=-0.75, y0=4, x1=0.75, y1=5.5, line=dict(color=GOLD, width=3)) 
        fig_heatmap.add_shape(type="line", x0=-3, y0=4, x1=3, y1=4, line=dict(color=NAVY, width=4)) 
        
        st.plotly_chart(fig_heatmap, use_container_width=True)

    # --- TREND WITH 7-DAY MOVING AVERAGE ---
    st.markdown(f"<h3 style='color: {NAVY}; text-align: center;'>Daily Shooting Trend & Averages</h3>", unsafe_allow_html=True)
    df['Court_Pct'] = (df['Court_Makes'] / 20) * 100
    df['FT_Pct'] = (df['FT_Makes'] / 10) * 100
    
    df_chart = df[['Date', 'Court_Pct', 'FT_Pct']].copy()
    df_chart.rename(columns={'Court_Pct': 'Daily Court Shots', 'FT_Pct': 'Free Throws'}, inplace=True)
    
    # Format the dates strictly to "Mon Day" (e.g., "Mar 1")
    df_chart['Display Date'] = df_chart['Date'].dt.strftime('%b ') + df_chart['Date'].dt.day.astype(str)
    
    df_chart['7-Day Avg (Court)'] = df_chart['Daily Court Shots'].rolling(window=7, min_periods=1).mean()
    
    fig_line = px.line(
        df_chart, x='Display Date', y=['Daily Court Shots', '7-Day Avg (Court)', 'Free Throws'], 
        markers=True, 
        labels={'value': 'Shooting %', 'Display Date': 'Workout Date', 'variable': 'Metric'},
        color_discrete_map={
            'Daily Court Shots': 'rgba(11, 34, 64, 0.3)', 
            '7-Day Avg (Court)': NAVY, 
            'Free Throws': GOLD
        }
    )
    
    # Force X-axis to sort chronologically using our custom formatted list
    fig_line.update_xaxes(type='category', categoryorder='array', categoryarray=df_chart['Display Date'])
    fig_line.update_layout(yaxis_range=[0, 100], plot_bgcolor=BACKGROUND, legend_title_text='')
    st.plotly_chart(fig_line, use_container_width=True)
