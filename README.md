# Guardrail & PII Shield

A small, local guardrail that screens every prompt **before** it reaches an LLM. It blocks prompt injections and personal data (Aadhaar and PAN numbers, card numbers, passwords, API keys and similar) in milliseconds, on your own GPU, so the check itself leaks nothing and blocked prompts cost no LLM tokens.

The checker is a **mini-Jev**: a small language model (Qwen3-0.6B) fine-tuned with LoRA, whose answer letters are read as probabilities. It never generates text, which keeps each check fast.

The guard is independent of any particular LLM. The proxy has a single placeholder function, `call_llm`, where a model of your choice can be connected.

---

## How it works

For each prompt the guard asks the mini-Jev two questions and reads the probabilities of the answers:

1. Is this a normal request, or a prompt injection?
2. Does this contain personal or secret data?

The higher of the two scores decides:

| Score | Decision | What happens |
| --- | --- | --- |
| below 0.2 | **allow** | the prompt is passed on |
| between 0.2 and 0.8 | **ask** | a warning is shown; the user can edit the prompt or send it anyway |
| above 0.8 | **block** | the prompt is stopped and nothing is sent on |

Every check is written to `log.csv`, and the Streamlit dashboard shows the counts and the median check time.

```
dashboard (Streamlit) -> proxy (FastAPI, /chat) -> guard (mini-Jev) -> allow / ask / block
```

---

## Project files

| File | Purpose |
| --- | --- |
| `minijev.py` | loads the model and turns answer letters into probabilities |
| `guard.py` | the two questions and the `check(text)` function |
| `guard_api.py` | the FastAPI proxy with the allow / ask / block logic and the `call_llm` placeholder |
| `dashboard.py` | the Streamlit dashboard |
| `clef.py` | wrapper for the Clef-flash comparison engine |
| `01_guard.ipynb` | baseline: untuned mini-Jev vs Laya |
| `02_finetune.ipynb` | LoRA fine-tuning |
| `03_comparison.ipynb` | scores all guards on both test sets |
| `04_thresholds.ipynb` | score distributions, thresholds and the allow / ask / block charts |
| `pii.csv`, `pii_test.csv` | personal-data training set (300) and test set (60), all fake data |
| `results/` | saved tables and charts |
| `logs/` | daily project log |

---

## How to run it

**Requirements:** Windows with an NVIDIA GPU (developed on an RTX 3050 laptop GPU with 4 GB), Python 3.12 or newer (last run on Python 3.14), and [uv](https://docs.astral.sh/uv/).

### 1. Set up the environment

```
uv venv
uv pip install torch --index-url https://download.pytorch.org/whl/cu126
uv pip install -r requirements.txt
```

Install the CUDA build of PyTorch first, so the other packages don't replace it with a CPU build. Then check the GPU:

```
.venv\Scripts\python -c "import torch; print(torch.cuda.is_available())"
```

This should print `True`. The base model (Qwen3-0.6B) downloads automatically from Hugging Face the first time it is used.

### 2. Recreate `guard-lora/` (the fine-tuned adapter)

The adapter is not stored in the repo, so create it by training:

1. Open `02_finetune.ipynb` with the `.venv` kernel.
2. Run the training cell. It trains on the public [deepset/prompt-injections](https://huggingface.co/datasets/deepset/prompt-injections) training set plus `pii.csv`, for 2 epochs, and saves the adapter to `guard-lora/`. This takes a few minutes on a laptop GPU.
3. In `minijev.py`, set:
   ```python
   ADAPTER = "guard-lora"
   ```
4. Restart any running kernel or server, because the adapter is only read at start-up. Run the training cell only once per kernel; to retrain, restart the kernel first.

If CUDA runs out of memory, change `torch.float32` to `torch.bfloat16` in `minijev.py`.

### 3. Create `keys.py` (only for the Clef-flash comparison)

The proxy and the dashboard do not need any key. `keys.py` is only used by the comparison notebook to call Clef-flash, and it is not committed. Create it in the project folder:

```python
CF_ACCOUNT_ID = "your Cloudflare account id"
CF_API_TOKEN = "your Workers AI API token"
```

Get both from the Cloudflare dashboard under Workers AI, then Use REST API, then Create a Workers AI API Token. Keep `keys.py` in `.gitignore`.

### 4. Start the proxy and the dashboard

In one terminal:

```
.venv\Scripts\uvicorn guard_api:app
```

Wait for "Application startup complete" (the model takes a moment to load). In a second terminal:

```
.venv\Scripts\streamlit run dashboard.py
```

You can also try the proxy directly at `http://127.0.0.1:8000/docs`.

---

## Results

All numbers are on held-out test sets: 116 prompts from the public injection dataset's test split and 60 personal-data prompts (30 with fake data, 30 normal) in `pii_test.csv`. A prompt counts as flagged above a score of 0.5.

| Guard | Injection accuracy | Missed / false alarms | Personal data accuracy | Missed / false alarms | Median ms (injection / personal data) |
| --- | --- | --- | --- | --- | --- |
| mini-Jev, untuned | 52.6% | 51 / 4 | 46.7% | 23 / 9 | 107 / 120 |
| **mini-Jev, tuned** | **96.6%** | **3 / 1** | 76.7% | **0 / 14** | 144 / 225 |
| Laya | 66.4% | 39 / 0 | 65.0% | 17 / 4 | 239 / 322 |
| Clef-flash | 56.0% | 51 / 0 | **93.3%** | 3 / 1 | 520 / 320 |

With the allow (below 0.2) and block (above 0.8) bands, the tuned mini-Jev gives:

| Test set | Real attacks or leaks: allow / ask / block | Normal prompts: allow / ask / block |
| --- | --- | --- |
| Injections (60 attacks, 56 normal) | 0 / 9 / 51 | 53 / 3 / 0 |
| Personal data (30 leaks, 30 normal) | 0 / 0 / 30 | 14 / 7 / 9 |

Charts are in `results/`: score distributions, the effect of each decision, the threshold sweep and the before and after tuning comparison.

**Reading the results**
- Tuning lifted injection detection from 52.6% to 96.6%, and the tuned model is also the fastest of the compared guards.
- The tuned model missed no personal-data leak in the test set, but it over-flags normal prompts.
- No guard wins on both tasks: Clef-flash is more accurate on personal data, but it runs on Cloudflare's servers, so every prompt checked leaves the machine, which weakens its use as a privacy guard.
- Tuning has a speed cost: the tuned mini-Jev is slower than the untuned one. It is still faster than Laya and Clef-flash.
- Timings are not like for like. The mini-Jev and Laya run on the local GPU, while Clef-flash is called over the internet, so its time includes the network.

---

## Limitations

- **Personal-data false alarms.** At the 0.5 cut-off, 14 of the 30 normal test prompts are flagged. Most mention a sensitive topic without containing any data (a database schema with an Aadhaar column, a form template with placeholders, a story about OTP fraud), so the model seems to react to topic words. A few plain technical prompts were also flagged, and I could not tell why. With the allow / ask / block bands, 9 of the 30 are still hard-blocked, because the model is very confident on them.
- **Small test sets.** With 60 personal-data prompts, one prompt moves the score by about 1.7 points, so small differences should not be over-read. The injection test set has 116 prompts.
- **Hinglish.** Mixed Hindi-English prompts are under-tested. Three of the 13 false alarms I examined were in Hinglish, and I did not measure Hinglish accuracy separately.
- **Fairness of the comparison.** The mini-Jev was trained on the same kind of data it is tested on, and I wrote the personal-data test prompts to include hard normal cases. Laya and Clef-flash were not trained for this task, so the table compares a tuned small local model with general-purpose engines on this task. It is not a general ranking of the engines.
- **Thresholds.** The 0.2 and 0.8 bands were fixed in advance and were not tuned on the test sets.
- **Not a complete security product.** It was tested on a small set of prompts, uses only fake personal data, and should not be relied on as the only protection for real sensitive data.

---

## Future improvements

- Connect an LLM through `call_llm` in `guard_api.py` (any provider, or a local model).
- Check the LLM's reply with the same sensitive-data question before returning it.
- Train a second adapter with more tricky normal prompts and more Hinglish examples, and compare it with this one on a fresh test set.
- Merge the adapter into the base model to remove its speed cost.
- Larger and more varied test data, with Hinglish accuracy measured separately.
- Redact only the sensitive part of a prompt instead of blocking all of it.

---

## Data and privacy

All personal data in `pii.csv` and `pii_test.csv` is fake. `keys.py`, `log.csv` and `guard-lora/` are not committed.
