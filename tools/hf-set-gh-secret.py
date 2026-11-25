import json, os, subprocess

path = os.path.expanduser("~/workspace/anicca-ops/credentials.json")
d = json.load(open(path))
tok = d["huggingface"]["read_token_manager_bfm_read"]
assert tok and len(tok) > 10

r = subprocess.run(
    ["gh", "secret", "set", "HF_TOKEN", "-R", "Daisuke134/life-manager"],
    input=tok.encode(), capture_output=True, timeout=120,
)
print("gh secret set rc:", r.returncode)
if r.returncode != 0:
    print("stderr:", r.stderr.decode()[:300])

r2 = subprocess.run(
    ["gh", "secret", "list", "-R", "Daisuke134/life-manager"],
    capture_output=True, timeout=60,
)
names = [ln.split("\t")[0] for ln in r2.stdout.decode().splitlines()]
print("HF_TOKEN present in secret list:", "HF_TOKEN" in names)
