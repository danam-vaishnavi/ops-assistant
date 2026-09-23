"""
Agentic triage: given a new ticket, Gemini decides for itself whether and
when to call check_duplicate() and suggest_category(), then produces a
final structured triage summary. This is genuine agentic tool use --
we don't hardcode the call order, the model does.
"""
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from agent.tools import check_duplicate, suggest_category

load_dotenv()

import os

def _get_env(key: str) -> str:
    """Reads a config value from the environment, falling back to Streamlit's
    secrets store when running on Streamlit Cloud (which doesn't populate
    os.environ from a .env file the way local dev does)."""
    if key in os.environ:
        return os.environ[key]
    try:
        import streamlit as st
        return st.secrets[key]
    except Exception:
        raise KeyError(f"{key} not found in environment or Streamlit secrets")

client = genai.Client(api_key=_get_env("GOOGLE_API_KEY"))

MODEL_NAME = "gemini-flash-lite-latest"

SYSTEM_INSTRUCTION = """You are an operational ticket triage agent. Given a new ticket,
you MUST call check_duplicate to see if it's a repeat of an existing issue, and
call suggest_category to find likely labels for it. Use both tools before answering.

Then give a short triage summary with three parts:
1. Duplicate status: is this a likely duplicate? Of which issue, if so?
2. Suggested category/labels.
3. One-sentence recommended next action for whoever is triaging this queue.
"""


def triage(ticket_text: str) -> str:
    chat = client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=[check_duplicate, suggest_category],
        ),
    )
    response = chat.send_message(ticket_text)
    return response.text


if __name__ == "__main__":
    import sys
    ticket = " ".join(sys.argv[1:]) or "VS Code crashes every time I try to debug an extension with F5"
    print("New ticket:", ticket)
    print("\nTriage result:\n")
    print(triage(ticket))
