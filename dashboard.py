import os, pandas as pd, requests, streamlit as st

st.title("Guardrail & PII Shield")
text = st.text_area("Prompt")
if st.button("Send") and text:
    st.json(requests.post("http://127.0.0.1:8000/chat", json={"text": text}).json())
if os.path.exists("log.csv"):
    log = pd.read_csv("log.csv", names=["time", "injection", "sensitive", "blocked", "ms"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Checked", len(log))
    c2.metric("Blocked", int(log.blocked.sum()))
    c3.metric("Median check", f"{log.ms.median():.0f} ms")
    st.dataframe(log.tail(20))