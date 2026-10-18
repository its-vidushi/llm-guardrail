from laya import Router

router = Router()  # downloads a checkpoint on first run
complaint = "Hostel Wi-Fi has been down since yesterday and my assignment is due tonight."
questions = {
    "office": {"type": "choice", "instructions": "Which office should handle this?",
               "criteria": {"hostel": "rooms, water, electricity",
                            "it": "Wi-Fi, college portal, email",
                            "academics": "classes, exams, marks"}},
    "urgency": {"type": "score", "instructions": "How urgent is this?",
                "criteria": ["can wait", "this week", "today"]},
    "needs_human": {"type": "noul", "instructions": "Does a staff member need to step in personally?"},
}
print(router.predict(complaint, questions)["answers"])  # office + probabilities, urgency, P(needs_human)