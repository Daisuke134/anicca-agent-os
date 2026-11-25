import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "reelclaw" / "scripts" / "run-honne-fresh-ja.sh"


class HonneFreshLunaTest(unittest.TestCase):
    def test_generates_hook_through_shared_marketing_runner_without_direct_openai(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            openclaw = home / ".openclaw"
            honne = openclaw / "workspace" / "honne-ai"
            patterns = openclaw / "state" / "content-library"
            post_scripts = openclaw / "workspace" / "skills" / "reelclaw" / "scripts"
            honne.mkdir(parents=True)
            patterns.mkdir(parents=True)
            post_scripts.mkdir(parents=True)
            (openclaw / ".env").write_text("POSTIZ_API_KEY=fixture\n", encoding="utf-8")
            (honne / "reel-final.mp4").write_bytes(b"fixture-video")
            (patterns / "pattern-honne-ja.jsonl").write_text(
                json.dumps(
                    {
                        "source_id": "HJA-TEST",
                        "status": "active",
                        "hook": "元のフック",
                        "structure": {"char_count": 24},
                        "emotion": "calm",
                        "observed": {"views": 100},
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            post = post_scripts / "post-video-to-tiktok.sh"
            post.write_text("#!/bin/sh\necho 'PostID: post-fixture'\n", encoding="utf-8")
            post.chmod(0o755)
            schema = home / "hook.schema.json"
            schema.write_text('{"type":"object"}', encoding="utf-8")
            args_file = home / "runner-args.json"
            runner = home / "run_marketing_prompt.sh"
            runner.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, pathlib, sys\n"
                "pathlib.Path(os.environ['RUNNER_ARGS']).write_text(json.dumps(sys.argv[1:]))\n"
                "print(json.dumps({'hook': '新しい本音フック'}, ensure_ascii=False))\n",
                encoding="utf-8",
            )
            runner.chmod(0o755)

            completed = subprocess.run(
                ["bash", str(SCRIPT), "--tt", "connection-fixture"],
                env={
                    **os.environ,
                    "HOME": str(home),
                    "HONNE_MARKETING_RUNNER": str(runner),
                    "HONNE_HOOK_SCHEMA": str(schema),
                    "RUNNER_ARGS": str(args_file),
                },
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("HOOK_TEXT=新しい本音フック", completed.stdout)
            args = json.loads(args_file.read_text(encoding="utf-8"))
            self.assertEqual(args[args.index("--loop") + 1], "honne-marketing")
            self.assertEqual(args[args.index("--schema") + 1], str(schema))

        text = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("api.openai.com", text)
        self.assertNotIn("gpt-4o-mini", text)
        self.assertNotIn("OPENAI_API_KEY", text)


if __name__ == "__main__":
    unittest.main()
