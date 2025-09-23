# streamlit_app.py

import streamlit as st
import json
from llm_interface import ask_roo
from scrape_trials import fetch_trials, update_knowledge_base

# Load signals
def load_signals(file_path="knowledge_base.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# Filter signals by type
def filter_signals(signals, selected_type):
    if selected_type == "All":
        return signals
    return [s for s in signals if s.get("type") == selected_type]

# UI setup
st.set_page_config(page_title="Wapyrus", page_icon="🧠")
st.title("🧠 Wapyrus — MedTech Signal Explorer")
st.markdown("Ask Roo anything about recent MedTech signals.")

# Refresh button
if st.button("🔄 Refresh Clinical Trials"):
    new_trials = fetch_trials()
    update_knowledge_base(new_trials)
    st.success("Knowledge base updated!")

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

# Load and filter signals
signals = load_signals()
filtered_signals = filter_signals(signals, selected_type)

# Ask Roo
if query:
    with st.spinner("Roo is thinking..."):
        response = ask_roo(query, filtered_signals)
    st.markdown("### 🧠 Roo says:")
    st.write(response)

# Optional: Show raw signals
with st.expander("📊 View signal data"):
    st.json(filtered_signals)
