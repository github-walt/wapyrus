# streamlit_app.py
import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
from llm_interface import ask_roo
from scrape_trials import fetch_trials, save_to_json
from scrape_eu import fetch_eu_trials  # Make sure this is imported

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

def filter_signals(signals, selected_type, status_filter=None, date_range=None):
    """Filter signals by type with better matching"""
    if not signals:
        return []
    
    filtered = signals
    
    # Filter by type
    if selected_type != "All":
        type_map = {
            "Clinical Trial": "INTERVENTIONAL", 
            "Observational Study": "OBSERVATIONAL"
        }
        
        target_type = type_map.get(selected_type, selected_type)
        filtered = [s for s in filtered if target_type.upper() in s.get("type", "").upper()]
    
    # Filter by status
    if status_filter:
        filtered = [s for s in filtered if s.get("status", "").upper() in [status.upper() for status in status_filter]]
    
    # Filter by date range (basic implementation)
    if date_range and len(date_range) == 2:
        try:
            start_date, end_date = date_range
            date_filtered = []
            for signal in filtered:
                signal_date = signal.get("start_date", "")
                if signal_date:
                    try:
                        # Try to parse various date formats
                        if "-" in signal_date:
                            signal_dt = datetime.strptime(signal_date.split("T")[0], "%Y-%m-%d")
                        else:
                            signal_dt = datetime.strptime(signal_date, "%B %Y")
                        
                        if start_date <= signal_dt.date() <= end_date:
                            date_filtered.append(signal)
                    except:
                        # If date parsing fails, include the signal
                        date_filtered.append(signal)
                else:
                    # Include signals without dates
                    date_filtered.append(signal)
            filtered = date_filtered
        except Exception as e:
            st.error(f"Error filtering by date: {e}")
    
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
        min_value=10,
        max_value=1000,
        value=50,
        step=10
    )
    
    # Advanced Filters
    st.subheader("Advanced Filters")
    status_filter = st.multiselect(
        "Trial Status:",
        ["RECRUITING", "COMPLETED", "ACTIVE_NOT_RECRUITING", "UNKNOWN", "TERMINATED", "SUSPENDED"],
        default=["RECRUITING", "ACTIVE_NOT_RECRUITING"]
    )
    
    # Date range filter
    date_range = st.date_input(
        "Start Date Range:",
        value=(datetime(2023, 1, 1).date(), datetime.now().date()),
        key="date_filter"
    )
    
    # Signal type filter
    signal_types = ["All", "Clinical Trial", "Observational Study"]
    selected_type = st.selectbox("Filter by study type:", signal_types)

    # Refresh button with proper EU trials integration
    if st.button("🔄 Refresh Clinical Trials", type="primary"):
        with st.spinner("Fetching latest clinical trials from all sources..."):
            try:
                # 1. Fetch data from ClinicalTrials.gov
                st.info("🌎 Fetching from ClinicalTrials.gov...")
                clinical_trials_gov_data = fetch_trials("medtech", max_records=int(max_fetch))
                
                # 2. Fetch data from EU CTR
                st.info("🇪🇺 Fetching from EU Clinical Trials Register...")
                eu_trials_data = fetch_eu_trials("medtech")
                
                # 3. Combine both data sources
                all_trials = clinical_trials_gov_data + eu_trials_data
                
                if all_trials:
                    # Save the combined data and update the app state
                    save_to_json(all_trials, "knowledge_base.json")
                    st.session_state.signals = all_trials
                    st.session_state.last_update = datetime.now()
                    
                    # Show success message with breakdown
                    st.success(f"✅ Successfully fetched {len(all_trials)} trials!")
                    st.info(f"📊 Breakdown: {len(clinical_trials_gov_data)} from ClinicalTrials.gov + {len(eu_trials_data)} from EU CTR")
                else:
                    st.error("❌ No trials were fetched. APIs might be unavailable.")
                    
            except Exception as e:
                st.error(f"❌ Failed to fetch trials: {str(e)}")
                # Fallback to sample data
                st.info("🔄 Loading sample data instead...")
                sample_data = [
                    {
                        "id": "NCT00123456",
                        "title": "Sample MedTech Trial - Cardiovascular Device",
                        "condition": "Heart Disease",
                        "type": "INTERVENTIONAL",
                        "status": "RECRUITING",
                        "start_date": "2024-01-15",
                        "completion_date": "2025-12-31",
                        "sponsor": "Sample Sponsor Inc.",
                        "source": "Sample Data"
                    }
                ]
                save_to_json(sample_data, "knowledge_base.json")
                st.session_state.signals = sample_data
                st.session_state.last_update = datetime.now()
    
    # Show last update
    if st.session_state.last_update:
        st.info(f"📅 Last update: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M')}")
    
    # Debug info (collapsible)
    with st.expander("Debug Info"):
        st.write(f"Signals loaded: {len(st.session_state.signals)}")
        
        if st.session_state.signals:
            if os.path.exists("knowledge_base.json"):
                file_size = os.path.getsize("knowledge_base.json")
                st.write(f"File size: {file_size} bytes")
            
            # Show sources breakdown
            sources = {}
            for signal in st.session_state.signals:
                source = signal.get('source', 'Unknown')
                sources[source] = sources.get(source, 0) + 1
            
            st.write("Data sources:")
            for source, count in sources.items():
                st.write(f"- {source}: {count} trials")

# Main content area
st.header("Ask Roo")

# Use session state signals
signals = st.session_state.signals
filtered_signals = filter_signals(signals, selected_type, status_filter, date_range)

# Premade questions
premade_questions = [
    "What are the most recent MedTech clinical trials?",
    "Which companies are conducting heart-related trials?",
    "Show me trials related to diabetes technology",
    "What's new in cardiovascular MedTech trials?",
    "Compare trials from ClinicalTrials.gov vs EU Clinical Trials Register"
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
    # Show statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Trials", len(signals))
    with col2:
        interventional = len([s for s in signals if "INTERVENTIONAL" in s.get("type", "").upper()])
        st.metric("Interventional", interventional)
    with col3:
        observational = len([s for s in signals if "OBSERVATIONAL" in s.get("type", "").upper()])
        st.metric("Observational", observational)
    with col4:
        recruiting = len([s for s in signals if "RECRUITING" in s.get("status", "").upper()])
        st.metric("Recruiting", recruiting)
    
    # Show filtered count
    if selected_type != "All" or status_filter or date_range:
        st.write(f"**Filtered to {len(filtered_signals)} trials**")
    
    # Data display
    with st.expander("📋 View Trial Data"):
        if filtered_signals:
            for i, trial in enumerate(filtered_signals):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{i+1}. {trial.get('title', 'No Title')}**")
                    st.write(f"   - **ID:** {trial.get('id', 'Unknown')}")
                    st.write(f"   - **Condition:** {trial.get('condition', 'Unknown')}")
                    st.write(f"   - **Type:** {trial.get('type', 'Unknown')}")
                    st.write(f"   - **Status:** {trial.get('status', 'Unknown')}")
                    st.write(f"   - **Sponsor:** {trial.get('sponsor', 'Unknown')}")
                    st.write(f"   - **Source:** {trial.get('source', 'Unknown')}")
                with col2:
                    if trial.get('start_date'):
                        st.write(f"**Start:** {trial.get('start_date')}")
                    if trial.get('completion_date'):
                        st.write(f"**Completion:** {trial.get('completion_date')}")
                st.write("---")
        else:
            st.warning("No trials match the current filters.")

    # Analytics Dashboard
    st.header("📈 Trial Analytics Dashboard")
    
    if signals:
        df = pd.DataFrame(signals)
        
        # Create columns for different charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Trial Status")
            if 'status' in df.columns:
                status_counts = df['status'].value_counts()
                st.dataframe(status_counts, use_container_width=True)
                st.bar_chart(status_counts)
        
        with col2:
            st.subheader("Trial Sources")
            if 'source' in df.columns:
                source_counts = df['source'].value_counts()
                st.dataframe(source_counts, use_container_width=True)
                st.bar_chart(source_counts)
        
        # Sponsor analysis
        st.subheader("Top Sponsors")
        if 'sponsor' in df.columns:
            top_sponsors = df['sponsor'].value_counts().head(10)
            st.dataframe(top_sponsors, use_container_width=True)
        
        # Condition analysis
        st.subheader("Common Conditions")
        if 'condition' in df.columns:
            condition_counts = df['condition'].value_counts().head(10)
            st.dataframe(condition_counts, use_container_width=True)

else:
    st.error("❌ No clinical trial data available. Click the 'Refresh Clinical Trials' button to fetch data.")

# Footer
st.markdown("---")
st.caption("Wapyrus MedTech Signal Explorer - Powered by ClinicalTrials.gov API and EU Clinical Trials Register")