#!/usr/bin/env python3
"""Kokoro TTS generation for the Innertune-type voice sample pilot.
Generates sentence by sentence, trims edge silence, joins with fixed gaps.
Usage: gen.py VOICE SPEED GAP_SEC OUT_WAV
"""
import sys
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

BASE = "/home/hatch/workspace/tools/kokoro-pilot"

SCRIPT = [
    "You don't have five senses, they lied to you.",
    "You have 15, grab your notepad.",
    "You are a spirit.",
    "You live in a body and you have a soul.",
    "Let's start with the weakest of the three, the body, because it's limited by the physical.",
    "It's ruled by the scene.",
    "Its five senses are sight, sound, smell, taste, touch, basic, surface level.",
    "You already know those.",
    "Now let's talk soul.",
    "This is where reprogramming starts.",
    "Your mind, what you think, your will, your drive to act, your emotions, what you feel, your affections, who you feel it for, and your imagination, your ability to see what isn't visible yet.",
    "Together, that's 10 senses.",
    "This is the operating system your affirmations tap into.",
    "Now, the spirit.",
    "This is where transformation goes quantum.",
    "Prayer, speaking truth to the divine.",
    "Praise, declaring truth to your reality.",
    "Worship, aligning with the highest version of yourself.",
    "Faith, belief beyond evidence, and meditation, pure focus.",
    "So you don't have five senses, you have 15.",
    "And when you learn to reprogram the ones you can't see, you unlock the version of you that was always waiting.",
    "Use Innertune to activate all 15.",
    "Click the link in our bio to access it now.",
]
WORD_COUNT = 207


def trim_edges(x, sr, thresh_db=-45.0, pad_ms=30):
    if len(x) == 0:
        return x
    peak = np.max(np.abs(x)) + 1e-12
    thr = peak * (10 ** (thresh_db / 20.0))
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    pad = int(sr * pad_ms / 1000)
    lo = max(0, idx[0] - pad)
    hi = min(len(x), idx[-1] + pad)
    return x[lo:hi]


def main():
    voice = sys.argv[1] if len(sys.argv) > 1 else "am_michael"
    speed = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    gap = float(sys.argv[3]) if len(sys.argv) > 3 else 0.35
    out = sys.argv[4] if len(sys.argv) > 4 else f"{BASE}/out.wav"

    kokoro = Kokoro(f"{BASE}/kokoro-v1.0.onnx", f"{BASE}/voices-v1.0.bin")
    sr = 24000
    gap_n = int(sr * gap)
    parts = []
    for i, s in enumerate(SCRIPT):
        samples, s_sr = kokoro.create(s, voice=voice, speed=speed, lang="en-us")
        assert s_sr == sr
        samples = trim_edges(np.asarray(samples, dtype=np.float32), sr)
        parts.append(samples)
        if i < len(SCRIPT) - 1:
            parts.append(np.zeros(gap_n, dtype=np.float32))
    audio = np.concatenate(parts)
    sf.write(out, audio, sr)
    dur = len(audio) / sr
    print(f"voice={voice} speed={speed} gap={gap} dur={dur:.2f}s wpm_total={WORD_COUNT/dur*60:.1f} out={out}")


if __name__ == "__main__":
    main()
