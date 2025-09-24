
# streamlit_app.py
import streamlit as st
import json
import os  # ADD THIS
from datetime import datetime
from llm_interface import ask_roo
from scrape_trials import fetch_trials, update_knowledge_base
from cache_utils import load_signals_cached  # Add this import
import requests  # ADD THIS

# DEBUG: Check what files exist
st.sidebar.markdown("### 🐛 Debug Info")
if os.path.exists("knowledge_base.json"):
    file_size = os.path.getsize("knowledge_base.json")
    st.sidebar.write(f"📁 knowledge_base.json: {file_size} bytes")
    try:
        with open("knowledge_base.json", "r") as f:
            data = json.load(f)
        st.sidebar.write(f"📊 Records in file: {len(data)}")
    except:
        st.sidebar.write("❌ Error reading file")
else:
    st.sidebar.write("❌ knowledge_base.json NOT FOUND")

# Check if we can make API calls
try:
    response = requests.get("https://clinicaltrials.gov/api/v2/studies", timeout=5, params={"pageSize": 1})
    st.sidebar.write(f"🌐 API accessible: {response.status_code == 200}")
except:
    st.sidebar.write("❌ API not accessible")

def load_signals(file_path="knowledge_base.json"):
    """Load signals with caching - fallback if cache fails"""
    try:
        return load_signals_cached(file_path)
    except Exception as e:
        st.warning(f"Cache load failed, reading from file: {e}")
        with open(file_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [s for s in raw if s.get("type")]

# Filter signals by type
def filter_signals(signals, selected_type):
    if selected_type == "All":
        return signals
    return [s for s in signals if s.get("type") == selected_type]

# UI setup
st.set_page_config(page_title="Wapyrus", page_icon="🧠", layout="wide")
st.title("🧠 Wapyrus — MedTech Signal Explorer")
st.markdown("Ask Roo anything about recent MedTech signals.")

# Initialize session state for caching
if 'signals' not in st.session_state:
    st.session_state.signals = load_signals()

if 'last_update' not in st.session_state:
    st.session_state.last_update = None

if 'is_loading' not in st.session_state:
    st.session_state.is_loading = False

# Better refresh functionality
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 Refresh Clinical Trials", disabled=st.session_state.is_loading):
        st.session_state.is_loading = True
        
with col2:
    if st.session_state.last_update:
        st.caption(f"Last updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M')}")

if st.session_state.is_loading:
    with st.spinner("Fetching latest trials..."):
        try:
            new_trials = fetch_trials(max_records=100)  # Reduced for faster testing
            if new_trials:  # Only update if we got data
                # Save to file
                with open("knowledge_base.json", "w", encoding="utf-8") as f:
                    json.dump(new_trials, f, indent=2)
                
                # Update session state
                st.session_state.signals = new_trials
                st.session_state.last_update = datetime.now()
                st.session_state.is_loading = False
                
                # Clear cache to force reload
                from cache_utils import load_signals_cached
                load_signals_cached.cache_clear()
                
                st.success(f"✅ Updated with {len(new_trials)} trials!")
                st.rerun()  # Refresh the app
            else:
                st.session_state.is_loading = False
                st.warning("⚠️ No new trials fetched. Using cached data.")
        except Exception as e:
            st.session_state.is_loading = False
            st.error(f"❌ Update failed: {e}"))

# Signal type filter
signal_types = ["All", "Funding", "Clinical Trial", "Regulatory Filing", "Hiring", "Product Launch"]
selected_type = st.selectbox("📂 Filter by signal type:", signal_types)

# Premade queries
premade = st.selectbox("💡 Try a premade question:", [
    "",
    "Which companies raised funding recently?",
    "Are any trials targeting Parkinson’s?",
    "Who’s preparing for regulatory approval?",
    "Any new product launches?",
    "Which companies are hiring?"
])

# Custom query
query = st.text_input("Or ask your own question:", value=premade)

# Use cached signals from session state
signals = st.session_state.signals
filtered_signals = filter_signals(signals, selected_type)

# Show stats
st.sidebar.markdown(f"**📊 Statistics:**")
st.sidebar.markdown(f"Total signals: {len(signals)}")
st.sidebar.markdown(f"Filtered: {len(filtered_signals)}")


# Ask Roo
if query:
    with st.spinner("Roo is thinking..."):
        response = ask_roo(query, filtered_signals)
    st.markdown("### 🧠 Roo says:")
    st.write(response)

# Optional: Show raw signals
with st.expander("📊 View signal data"):
    st.json(filtered_signals)
