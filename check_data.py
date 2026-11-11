import pandas as pd

tr, te = pd.read_csv("pii.csv"), pd.read_csv("pii_test.csv")
for name, d in [("train", tr), ("test", te)]:
    assert list(d.columns) == ["text", "label"], f"{name}: columns must be exactly text,label"
    assert set(d.label) <= {0, 1}, f"{name}: labels must be 0 or 1"
    print(name, len(d), d.label.value_counts().to_dict(), "duplicates:", int(d.text.duplicated().sum()))
overlap = set(tr.text.str.lower().str.strip()) & set(te.text.str.lower().str.strip())
print("train/test overlap:", len(overlap))
print(tr.sample(8, random_state=0).to_string())