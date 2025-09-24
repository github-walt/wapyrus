# streamlit_app.py
import streamlit as st
import json
import os
# Add charts
import pandas as pd


from datetime import datetime
from llm_interface import ask_roo
from scrape_trials import fetch_trials, save_to_json

# Set page config first
st.set_page_config(
    page_title="Wapyrus - MedTech Signal Explorer", 
    page_icon="🧠", 
    layout="wide"
)

def load_signals(file_path="knowledge_base.json"):
    """Load signals from JSON file with error handling"""
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure we return a list, even if empty
                return data if isinstance(data, list) else []
        else:
            st.warning("📁 No data file found. Click 'Refresh Clinical Trials' to fetch data.")
            return []
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return []

def filter_signals(signals, selected_type):
    """Filter signals by type with better matching"""
    if not signals:
        return []
    
    if selected_type == "All":
        return signals
    
    # More flexible type mapping
    type_map = {
        "Clinical Trial": "INTERVENTIONAL", 
        "Observational Study": "OBSERVATIONAL"
    }
    
    target_type = type_map.get(selected_type, selected_type)
    
    # Flexible matching - check if type contains target (case-insensitive)
    filtered = []
    for signal in signals:
        signal_type = signal.get("type", "").upper()
        if target_type.upper() in signal_type:
            filtered.append(signal)
    
    return filtered

# Initialize session state
if 'signals' not in st.session_state:
    st.session_state.signals = load_signals()

if 'last_update' not in st.session_state:
    st.session_state.last_update = None

# UI Header
st.title("🧠 Wapyrus — MedTech Signal Explorer")
st.markdown("Ask Roo anything about recent MedTech signals.")

# Sidebar with controls
with st.sidebar:
    st.header("Controls")
    
    max_fetch = st.number_input(
    "Clinical trials to fetch:",
    min_value=10,    # smallest allowed
    max_value=1000,  # largest allowed
    value=50,        # default value shown
    step=10
)  

    st.header("Advanced Filters")
    condition = st.text_input("Condition/Disease")
    intervention = st.text_input("Intervention/Treatment")
    location = st.text_input("Location")
    sponsor = st.text_input("Sponsor")
    only_with_results = st.checkbox("Only Studies With Results")
    date_field = st.selectbox("Date Field", ["Start Date", "Completion Date", "Last Update"])
    # Use these in your fetch_trials logic!  
   
    # Refresh button with better error handling
    if st.button("🔄 Refresh Clinical Trials", type="primary"):
        with st.spinner("Fetching latest clinical trials..."):
            try:
                new_trials = fetch_trials(max_records=int(max_fetch))
  # Start small
                if new_trials:
                    save_to_json(new_trials, "knowledge_base.json")
                    st.session_state.signals = new_trials
                    st.session_state.last_update = datetime.now()
                    st.success(f"✅ Fetched {len(new_trials)} trials!")
                else:
                    st.error("❌ No trials were fetched. API might be unavailable.")
            except Exception as e:
                st.error(f"❌ Failed to fetch trials: {str(e)}")
    # Add to sidebar
    st.sidebar.subheader("Advanced Filters")
    status_filter = st.sidebar.multiselect(
        "Trial Status:",
        ["RECRUITING", "COMPLETED", "ACTIVE_NOT_RECRUITING", "UNKNOWN"]
        )

    # Date range filter
    date_range = st.sidebar.date_input(
        "Start Date Range:",
        value=(datetime(2023, 1, 1), datetime.now())
        )
    
    # Show last update
    if st.session_state.last_update:
        st.info(f"Last update: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M')}")
    
    # Signal type filter
    st.subheader("Filters")
    signal_types = ["All", "Clinical Trial", "Observational Study"]
    selected_type = st.selectbox("Filter by study type:", signal_types)
    
    # Debug info
    st.subheader("Debug Info")
    st.write(f"Signals loaded: {len(st.session_state.signals)}")
    
    if st.session_state.signals:
        # Show file info
        if os.path.exists("knowledge_base.json"):
            file_size = os.path.getsize("knowledge_base.json")
            st.write(f"File size: {file_size} bytes")
        
        # Show first trial as sample
        if len(st.session_state.signals) > 0:
            st.write("First trial sample:")
            sample_trial = st.session_state.signals[0]
            st.json(sample_trial)

# Main content area
st.header("Ask Roo")

# Use session state signals
signals = st.session_state.signals
filtered_signals = filter_signals(signals, selected_type)

# Premade questions
premade_questions = [
    "What are the most recent MedTech clinical trials?",
    "Which companies are conducting heart-related trials?",
    "Show me trials related to diabetes technology",
    "What's new in cardiovascular MedTech trials?"
]

question = st.selectbox("💡 Try a premade question:", [""] + premade_questions)

# Custom question input
user_question = st.text_input("Or ask your own question:", value=question if question else "")

# Ask Roo
if user_question and signals:
    with st.spinner("🧠 Roo is analyzing the clinical trials..."):
        response = ask_roo(user_question, filtered_signals)
    
    st.subheader("Roo's Analysis:")
    st.write(response)

elif user_question and not signals:
    st.warning("⚠️ No clinical trial data available. Please click 'Refresh Clinical Trials' first.")

# Data explorer section
st.header("📊 Clinical Trials Data")

if signals:
    st.success(f"✅ Loaded {len(signals)} clinical trials")
    
    # Show filtered count
    if selected_type != "All":
        st.write(f"**Filtered to {len(filtered_signals)} {selected_type} trials**")
    
    # Data explorer section - SIMPLIFIED
st.header("📊 Clinical Trials Data Explorer")

if signals:
    st.success(f"✅ Loaded {len(signals)} clinical trials")
    
    # Show statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Trials", len(signals))
    with col2:
        interventional = len([s for s in signals if s.get("type") == "INTERVENTIONAL"])
        st.metric("Interventional", interventional)
    with col3:
        observational = len([s for s in signals if s.get("type") == "OBSERVATIONAL"])
        st.metric("Observational", observational)
    
    # Show filtered count
    if selected_type != "All":
        st.write(f"**Filtered to {len(filtered_signals)} {selected_type} trials**")
        
    
    
    # SIMPLE DATA DISPLAY - Always show something
    with st.expander("📋 View All Trial Data"):
        if filtered_signals:
            # Show as a simple list first
            for i, trial in enumerate(filtered_signals):
                st.write(f"**{i+1}. {trial.get('title', 'No Title')}**")
                st.write(f"   - ID: {trial.get('id', 'Unknown')}")
                st.write(f"   - Type: {trial.get('type', 'Unknown')}")
                st.write(f"   - Status: {trial.get('status', 'Unknown')}")
                st.write(f"   - Sponsor: {trial.get('sponsor', 'Unknown')}")
                st.write("---")
        else:
            # Show all signals if filter returns nothing
            st.warning("No trials match the current filter. Showing all trials:")
            for i, trial in enumerate(signals[:10]):  # Show first 10
                st.write(f"**{i+1}. {trial.get('title', 'No Title')}**")
                st.write(f"   - ID: {trial.get('id', 'Unknown')}")
                st.write(f"   - Type: {trial.get('type', 'Unknown')}")
                st.write(f"   - Status: {trial.get('status', 'Unknown')}")
                st.write("---")
            
            if len(signals) > 10:
                st.info(f"Showing first 10 of {len(signals)} total trials")
else:
    st.error("❌ No clinical trial data available. Click the 'Refresh Clinical Trials' button to fetch data.")
    
    # Add this after your data display section
st.header("📊 Trial Analytics Dashboard")

if signals:
    import pandas as pd
    
    # Convert to DataFrame
    df = pd.DataFrame(signals)
    
    # Create columns for different charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Trial Status")
        status_counts = df['status'].value_counts()
        st.dataframe(status_counts, use_container_width=True)
        st.bar_chart(status_counts)
    
    with col2:
        st.subheader("Trial Types")
        type_counts = df['type'].value_counts()
        st.dataframe(type_counts, use_container_width=True)
        st.bar_chart(type_counts)
    
    # Timeline analysis (if you have dates)
    st.subheader("Trial Timeline")
    if 'start_date' in df.columns:
        # Extract year from start_date
        df['year'] = pd.to_datetime(df['start_date'], errors='coerce').dt.year
        yearly_counts = df['year'].value_counts().sort_index()
        st.line_chart(yearly_counts)
    else:
        st.info("No date data available for timeline")
    
    # Top sponsors table
    st.subheader("Top 10 Sponsors")
    top_sponsors = df['sponsor'].value_counts().head(10)
    st.dataframe(top_sponsors, use_container_width=True)

else:
    st.info("No data available for analytics")


# Footer
st.markdown("---")
st.caption("Wapyrus MedTech Signal Explorer - Powered by ClinicalTrials.gov API")