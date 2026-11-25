import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "workspace" / "skills" / "reelclaw" / "scripts" / "run-card-en.sh"
HONNE_SCRIPT = ROOT / "workspace" / "skills" / "reelclaw" / "scripts" / "run-honne-en.sh"
HONNE_JA_SCRIPT = ROOT / "workspace" / "skills" / "reelclaw" / "scripts" / "run-honne-ja.sh"


class RunCardEnglishFailClosedTest(unittest.TestCase):
    def test_invalid_hook_bank_never_reaches_posting_script(self):
        with tempfile.TemporaryDirectory() as directory:
            fake_home = Path(directory)
            openclaw = fake_home / ".openclaw"
            marketing = openclaw / "workspace" / "tiktok-marketing"
            assets = openclaw / "workspace" / "reelclaw-assets" / "videos" / "card-en"
            scripts = openclaw / "workspace" / "skills" / "reelclaw" / "scripts"
            marketing.mkdir(parents=True)
            assets.mkdir(parents=True)
            scripts.mkdir(parents=True)
            (marketing / "hooks-en.json").write_text("{invalid", encoding="utf-8")
            (assets / "v1.mp4").write_bytes(b"video")
            (openclaw / ".env").write_text("POSTIZ_API_KEY=test\n", encoding="utf-8")

            marker = fake_home / "posted"
            poster = scripts / "post-video-to-instagram.sh"
            poster.write_text(
                "#!/bin/bash\ntouch \"$POST_MARKER\"\necho IG_POST_ID=unexpected\n",
                encoding="utf-8",
            )
            poster.chmod(0o755)

            completed = subprocess.run(
                ["bash", str(SCRIPT), "--ig", "test-integration"],
                text=True,
                capture_output=True,
                check=False,
                env={**os.environ, "HOME": str(fake_home), "POST_MARKER": str(marker)},
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertFalse(marker.exists(), completed.stdout + completed.stderr)

    def test_invalid_honne_hook_bank_never_reaches_posting_script(self):
        with tempfile.TemporaryDirectory() as directory:
            fake_home = Path(directory)
            openclaw = fake_home / ".openclaw"
            honne = openclaw / "workspace" / "honne-ai"
            assets = openclaw / "workspace" / "reelclaw-assets" / "videos" / "honne-en"
            scripts = openclaw / "workspace" / "skills" / "reelclaw" / "scripts"
            honne.mkdir(parents=True)
            assets.mkdir(parents=True)
            scripts.mkdir(parents=True)
            (honne / "honne-hooks-en.json").write_text("{invalid", encoding="utf-8")
            (assets / "v1.mp4").write_bytes(b"video")
            (openclaw / ".env").write_text("POSTIZ_API_KEY=test\n", encoding="utf-8")

            marker = fake_home / "posted"
            poster = scripts / "post-video-to-tiktok.sh"
            poster.write_text(
                "#!/bin/bash\ntouch \"$POST_MARKER\"\necho 'PostID: unexpected'\n",
                encoding="utf-8",
            )
            poster.chmod(0o755)

            completed = subprocess.run(
                ["bash", str(HONNE_SCRIPT), "--tt", "test-integration"],
                text=True,
                capture_output=True,
                check=False,
                env={**os.environ, "HOME": str(fake_home), "POST_MARKER": str(marker)},
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertFalse(marker.exists(), completed.stdout + completed.stderr)

    def test_invalid_japanese_honne_hook_bank_never_reaches_posting_script(self):
        with tempfile.TemporaryDirectory() as directory:
            fake_home = Path(directory)
            openclaw = fake_home / ".openclaw"
            honne = openclaw / "workspace" / "honne-ai"
            assets = openclaw / "workspace" / "reelclaw-assets" / "videos" / "honne-ja"
            scripts = openclaw / "workspace" / "skills" / "reelclaw" / "scripts"
            honne.mkdir(parents=True)
            assets.mkdir(parents=True)
            scripts.mkdir(parents=True)
            (honne / "honne-hooks-ja.json").write_text("{invalid", encoding="utf-8")
            (assets / "v1.mp4").write_bytes(b"video")
            (openclaw / ".env").write_text("POSTIZ_API_KEY=test\n", encoding="utf-8")

            marker = fake_home / "posted"
            poster = scripts / "post-video-to-tiktok.sh"
            poster.write_text(
                "#!/bin/bash\ntouch \"$POST_MARKER\"\necho 'PostID: unexpected'\n",
                encoding="utf-8",
            )
            poster.chmod(0o755)

            completed = subprocess.run(
                ["bash", str(HONNE_JA_SCRIPT), "--tt", "test-integration"],
                text=True,
                capture_output=True,
                check=False,
                env={**os.environ, "HOME": str(fake_home), "POST_MARKER": str(marker)},
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertFalse(marker.exists(), completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
