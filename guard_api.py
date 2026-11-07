import csv, time
from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from guard import check
from keys import GEMINI_API_KEY

app = FastAPI()
gemini = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-3.1-flash-lite"  # or any model with free quota in AI Studio

class Prompt(BaseModel):
    text: str

@app.post("/chat")
def chat(p: Prompt):
    t = time.perf_counter()
    risk = check(p.text)
    ms = round((time.perf_counter() - t) * 1000)
    blocked = risk["injection"] > 0.5 or risk["sensitive"] > 0.5
    with open("log.csv", "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([round(time.time()), round(risk["injection"], 2), round(risk["sensitive"], 2), blocked, ms])
    if blocked:
        return {"blocked": True, "risk": risk, "guard_ms": ms}  # Gemini is never called
    reply = gemini.interactions.create(model=MODEL, input=p.text).output_text
    return {"blocked": False, "reply": reply, "guard_ms": ms}