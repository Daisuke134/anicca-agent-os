import os, re, sys
sys.path.insert(0, os.path.expanduser("~/workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files"))
import importlib.util
spec = importlib.util.spec_from_file_location("inkbox_check", os.path.expanduser("~/workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files/inkbox-check.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
client = mod.make_client()
msgs = list(client.messages.list("anicca-agent@inkboxmail.com", start_datetime="2026-11-08"))
print("total today:", len(msgs))
for m in msgs:
    subj = (m.subject or "")
    frm = (m.from_address or "")
    if "hugging" in (subj + frm).lower():
        print("FOUND:", m.created_at, "|", frm, "|", subj, "| id:", m.id)
        full = client.messages.get("anicca-agent@inkboxmail.com", m.id)
        body = (getattr(full, "body_html", None) or "") + "\n" + (getattr(full, "body_text", None) or "")
        urls = re.findall(r"https://huggingface\.co/[^\s\"'<>]+", body)
        for u in dict.fromkeys(urls):
            print("URL:", u)
