# llm_interface.py

import os
import json
from dotenv import load_dotenv
from groq import Groq

# Load API key from .env
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize Groq client
client = Groq(api_key=groq_api_key)

def format_prompt(query, signals):
    signal_text = "\n".join([
        f"- {s['company']} | {s['type']} | {s['date']} | {s['summary']}"
        for s in signals
    ])

    prompt = f"""
You are Roo, a MedTech-savvy assistant. You help users understand signals from the MedTech industry such as funding rounds, clinical trials, regulatory filings, and hiring trends.

Here are some recent signals:
{signal_text}

User question:
{query}

Answer clearly and helpfully based on the signals above.
"""
    return prompt

def ask_roo(query, signals):
    prompt = format_prompt(query, signals)

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are Roo, a helpful MedTech assistant."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",  # You can change this to another Groq-supported model
            temperature=0.7
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error contacting Roo: {e}"
