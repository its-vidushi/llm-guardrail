import csv, time
from fastapi import FastAPI
from pydantic import BaseModel
from guard import check

app = FastAPI()
ALLOW_BELOW, BLOCK_ABOVE = 0.2, 0.8

class Prompt(BaseModel):
    text: str
    confirmed: bool = False

def call_llm(text):
    """Placeholder: connect any LLM here and return its reply as a string."""
    return None

def decide(risk):
    top = max(risk.values())
    if top > BLOCK_ABOVE:
        return "block"
    if top < ALLOW_BELOW:
        return "allow"
    return "ask"

@app.post("/chat")
def chat(p: Prompt):
    t = time.perf_counter()
    risk = check(p.text)
    ms = round((time.perf_counter() - t) * 1000)
    decision = decide(risk)
    if decision == "ask" and p.confirmed:
        decision = "confirmed"
    with open("log.csv", "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([round(time.time()), round(risk["injection"], 2), round(risk["sensitive"], 2), decision, ms])
    if decision == "block":
        return {"decision": "block", "risk": risk, "guard_ms": ms}
    if decision == "ask":
        return {"decision": "ask", "risk": risk, "guard_ms": ms,
                "warning": "This prompt may contain sensitive data or an injection. Remove that part, or send it anyway."}
    reply = call_llm(p.text)
    note = "no LLM connected" if reply is None else None
    return {"decision": decision, "risk": risk, "guard_ms": ms, "reply": reply, "note": note}