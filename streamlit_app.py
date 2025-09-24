# streamlit_app.py
import streamlit as st
import json
import os
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
    """Filter signals by type"""
    if not signals:
        return []
    
    if selected_type == "All":
        return signals
    
    # Handle both INTERVENTIONAL/OBSERVATIONAL and your custom types
    type_map = {
        "Clinical Trial": "INTERVENTIONAL", 
        "Observational Study": "OBSERVATIONAL"
    }
    
    target_type = type_map.get(selected_type, selected_type)
    return [s for s in signals if s.get("type") == target_type]

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
    
    # Refresh button with better error handling
    if st.button("🔄 Refresh Clinical Trials", type="primary"):
        with st.spinner("Fetching latest clinical trials..."):
            try:
                new_trials = fetch_trials(max_records=50)  # Start small
                if new_trials:
                    save_to_json(new_trials, "knowledge_base.json")
                    st.session_state.signals = new_trials
                    st.session_state.last_update = datetime.now()
                    st.success(f"✅ Fetched {len(new_trials)} trials!")
                else:
                    st.error("❌ No trials were fetched. API might be unavailable.")
            except Exception as e:
                st.error(f"❌ Failed to fetch trials: {str(e)}")
    
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
    
    # Data table preview
    with st.expander("View Raw Trial Data", expanded=False):
        if filtered_signals:
            # Create a simple table view
            for i, trial in enumerate(filtered_signals[:5]):  # Show first 5
                with st.expander(f"Trial {i+1}: {trial.get('title', 'No title')}"):
                    st.json(trial)
            
            if len(filtered_signals) > 5:
                st.info(f"Showing first 5 of {len(filtered_signals)} trials")
        else:
            st.warning("No trials match the current filter")
else:
    st.error("❌ No clinical trial data available. Click the 'Refresh Clinical Trials' button in the sidebar to fetch data.")

# Footer
st.markdown("---")
st.caption("Wapyrus MedTech Signal Explorer - Powered by ClinicalTrials.gov API")