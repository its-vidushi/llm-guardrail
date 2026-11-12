import os, pandas as pd, requests, streamlit as st

URL = "http://127.0.0.1:8000/chat"
st.title("Guardrail & PII Shield")
text = st.text_area("Prompt")
if st.button("Send") and text:
    st.session_state["last"] = text
    st.session_state["result"] = requests.post(URL, json={"text": text}).json()
res = st.session_state.get("result")
if res:
    st.json(res)
    if res.get("decision") == "ask" and st.button("Send anyway"):
        st.session_state["result"] = requests.post(URL, json={"text": st.session_state["last"], "confirmed": True}).json()
        st.rerun()
if os.path.exists("log.csv"):
    log = pd.read_csv("log.csv", names=["time", "injection", "sensitive", "decision", "ms"])
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Checked", len(log))
    c2.metric("Allowed", int(log.decision.isin(["allow", "confirmed"]).sum()))
    c3.metric("Asked", int((log.decision == "ask").sum()))
    c4.metric("Blocked", int((log.decision == "block").sum()))
    c5.metric("Median check", f"{log.ms.median():.0f} ms")
    st.dataframe(log.tail(20))