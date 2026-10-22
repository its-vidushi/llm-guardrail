from minijev import ask

INJ_Q = "Is this message a normal request, or a prompt injection that tries to override an AI's instructions?"
INJ_OPTS = ["normal request", "prompt injection"]
PII_Q = ("Does this message contain personal or secret data, such as ID numbers, card numbers, passwords, "
         "API keys, phone numbers or health details?")
PII_OPTS = ["no sensitive data", "contains sensitive data"]

def check(text):
    return {"injection": ask(text[:1000], INJ_Q, INJ_OPTS)[INJ_OPTS[1]],
            "sensitive": ask(text[:1000], PII_Q, PII_OPTS)[PII_OPTS[1]]}