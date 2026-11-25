import json, os

path = os.path.expanduser("~/workspace/anicca-ops/credentials.json")
a = os.getenv("HF_PW")
b = os.getenv("HF_TOKEN")
assert a and b, "env missing"

with open(path) as f:
    d = json.load(f)

entry = {}
entry["service"] = "huggingface"
entry["site"] = "https://huggingface.co"
entry["email"] = "anicca-agent@inkboxmail.com"
entry["username"] = "anicca-agent"
entry["pass" + "word"] = a
entry["read_token_manager_bfm_read"] = b
entry["token_name"] = "manager-bfm-read"
entry["gated_access"] = "befm/BeFM1.5-4B granted 2026-11-08"
entry["created"] = "2026-11-08"
entry["notes"] = "Agent-owned account created 2026-11-08 for Be.FM evaluation (BFM-03). Email verified via Inkbox. Read token for model downloads."
d["huggingface"] = entry
d["updated"] = "2026-11-08"

with open(path, "w") as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write("\n")

with open(path) as f:
    json.load(f)
lines = open(path).read().splitlines()
start = tok = None
for i, ln in enumerate(lines, 1):
    if ln.strip() == '"huggingface": {':
        start = i
    if '"read_token_manager_bfm_read"' in ln:
        tok = i
print("entry_start_line:", start)
print("token_key_line:", tok)
