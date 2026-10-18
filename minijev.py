import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

NAME = "Qwen/Qwen3-0.6B"
ADAPTER = None  # after fine-tuning (Core guide), set this to "guard-lora"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # up to 26 options

tok = AutoTokenizer.from_pretrained(NAME)
lm = AutoModelForCausalLM.from_pretrained(NAME, dtype=torch.float32).to(DEVICE).eval()
if ADAPTER:
    from peft import PeftModel
    lm = PeftModel.from_pretrained(lm, ADAPTER).to(DEVICE).eval()

def option_logits(state, question, options, model=None):
    """One score per option: the model's next-token logit for that option's letter."""
    menu = "\n".join(f"{l}. {o}" for l, o in zip(LETTERS, options))
    msgs = [{"role": "user", "content": f"{state}\n\nQuestion: {question}\n{menu}\nAnswer with one letter."}]
    prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    ids = [tok.encode(l, add_special_tokens=False)[0] for l in LETTERS[:len(options)]]
    return (model or lm)(**tok(prompt, return_tensors="pt").to(DEVICE)).logits[0, -1, ids]

def ask(state, question, options):
    """Return {option: probability} without generating any text."""
    with torch.no_grad():
        probs = torch.softmax(option_logits(state, question, options).float(), dim=0)
    return dict(zip(options, probs.tolist()))

if __name__ == "__main__":
    print(DEVICE, ask("Hostel Wi-Fi has been down since yesterday.", "Which office should handle this?",
                      ["hostel office", "IT help desk", "exam cell"]))