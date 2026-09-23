"""
Streamlit dashboard for the operational RAG + agentic assistant.
Run with: streamlit run dashboard/app.py
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
from retrieval.search import search
from retrieval.generate import answer
from agent.triage import triage

st.set_page_config(page_title="Ops Ticket Assistant", layout="wide")
st.title("Operational Ticket Triage Assistant")
st.caption(
    "Paste a new ticket below. The assistant retrieves similar past issues from "
    "microsoft/vscode's issue history, generates a grounded answer citing its "
    "sources, and an agent decides whether this looks like a duplicate and what "
    "category it likely belongs to."
)

ticket_text = st.text_area(
    "New ticket / question",
    height=120,
    placeholder="e.g. VS Code crashes every time I try to debug an extension with F5",
)

col1, col2 = st.columns(2)
with col1:
    run_answer = st.button("Get grounded answer", type="primary")
with col2:
    run_triage = st.button("Run agentic triage")

if run_answer and ticket_text.strip():
    with st.spinner("Retrieving similar issues and generating an answer..."):
        result = answer(ticket_text)

    st.subheader("Grounded Answer")
    st.write(result["answer"])

    st.subheader("Sources")
    for s in result["sources"]:
        st.markdown(f"- **#{s['issue_number']}** — {s['title']}  \n  {s['url']}")

if run_triage and ticket_text.strip():
    with st.spinner("Agent is checking for duplicates and suggesting a category..."):
        triage_result = triage(ticket_text)

    st.subheader("Agentic Triage")
    st.write(triage_result)

if ticket_text.strip() and (run_answer or run_triage):
    with st.expander("Raw retrieved issues (top 5)"):
        for r in search(ticket_text, k=5):
            st.markdown(
                f"**[{r['similarity']:.3f}] #{r['issue_number']}** — {r['title']}  \n"
                f"labels: {r['labels']} | state: {r['state']}  \n{r['url']}"
            )
