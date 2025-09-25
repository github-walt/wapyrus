import streamlit as st
from groq import Groq

def get_groq_client():
    # Use Streamlit secrets for API key
    try:
        api_key = st.secrets["api"]["GROQ_API_KEY"]
    except KeyError:
        raise ValueError("GROQ_API_KEY not found in Streamlit secrets. Please check your .streamlit/secrets.toml file.")
    
    if not api_key:
        raise ValueError("GROQ_API_KEY is empty in Streamlit secrets")
    
    return Groq(api_key=api_key)

def ask_roo(prompt, signals=None, max_signals=50):
    try:
        client = get_groq_client()
        
        # Better signal formatting with fallbacks
        signal_text = ""
        if signals and isinstance(signals, list):
            trimmed_signals = signals[:max_signals]
            signal_entries = []
            for s in trimmed_signals:
                title = s.get('title', 'Unknown Study')
                sponsor = s.get('sponsor', 'Unknown Sponsor')
                status = s.get('status', 'Status Unknown')
                signal_entries.append(f"- {title} by {sponsor} ({status})")
            
            signal_text = "\n".join(signal_entries)
            prompt = f"{prompt}\n\nRelevant MedTech trials:\n{signal_text}"

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are Roo, a helpful MedTech analyst. Use the provided clinical trial data to answer questions accurately. Be specific and cite relevant trials when possible.",
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.1-8b-instant",
            timeout=30  # Add timeout
        )
        return chat_completion.choices[0].message.content

    except Exception as e:
        return f"❌ Sorry, I encountered an error: {str(e)}"



