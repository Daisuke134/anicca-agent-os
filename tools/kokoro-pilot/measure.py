#!/usr/bin/env python3
"""Measure a narration WAV the same way as the 2026-11-06 voice-diff audit:
autocorrelation pitch on voiced frames, energy-based pauses, spectral centroid.
Usage: measure.py WAV [WORDS]
"""
import sys
import subprocess
import numpy as np
import soundfile as sf

SR = 16000


def load_mono_16k(path):
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        capture_output=True, check=True,
    )
    return np.frombuffer(out.stdout, dtype=np.float32).copy()


def autocorr_pitch(frame, sr, fmin=60, fmax=400):
    frame = frame - np.mean(frame)
    if np.max(np.abs(frame)) < 1e-4:
        return 0.0
    corr = np.correlate(frame, frame, mode="full")[len(frame) - 1:]
    lo = int(sr / fmax)
    hi = int(sr / fmin)
    if hi >= len(corr):
        return 0.0
    seg = corr[lo:hi]
    if len(seg) == 0:
        return 0.0
    peak = lo + int(np.argmax(seg))
    if corr[peak] <= 0:
        return 0.0
    # normalized autocorrelation strength; reject weak periodicity (unvoiced/noise)
    if corr[peak] / (corr[0] + 1e-12) < 0.3:
        return 0.0
    return sr / peak


def main():
    path = sys.argv[1]
    words = int(sys.argv[2]) if len(sys.argv) > 2 else 207
    x = load_mono_16k(path)
    dur = len(x) / SR
    frame_len = int(SR * 0.025)
    hop = int(SR * 0.010)
    n_frames = max(1, (len(x) - frame_len) // hop + 1)
    rms = np.zeros(n_frames)
    pitch = np.zeros(n_frames)
    for i in range(n_frames):
        fr = x[i * hop: i * hop + frame_len]
        rms[i] = np.sqrt(np.mean(fr ** 2) + 1e-12)
    peak_rms = np.max(rms)
    voiced = rms > peak_rms * 0.08  # energy VAD
    for i in range(n_frames):
        if voiced[i]:
            pitch[i] = autocorr_pitch(x[i * hop: i * hop + frame_len], SR)
    p = pitch[pitch > 0]
    # pauses: contiguous unvoiced runs
    pauses = []
    run = 0
    for v in voiced:
        if not v:
            run += 1
        else:
            if run > 0:
                pauses.append(run * 0.010)
            run = 0
    if run > 0:
        pauses.append(run * 0.010)
    pauses = np.array(pauses) if pauses else np.array([0.0])
    internal = pauses[1:-1] if len(pauses) > 2 else pauses
    # spectral centroid on voiced frames
    cents = []
    for i in range(n_frames):
        if voiced[i]:
            fr = x[i * hop: i * hop + frame_len] * np.hanning(frame_len)
            mag = np.abs(np.fft.rfft(fr))
            freqs = np.fft.rfftfreq(frame_len, 1 / SR)
            if mag.sum() > 0:
                cents.append(float((freqs * mag).sum() / mag.sum()))
    last_voiced_end = (np.max(np.where(voiced)[0]) + 1) * 0.010 if voiced.any() else dur
    print(f"file={path}")
    print(f"duration_sec={dur:.2f}")
    print(f"last_voiced_end_sec={last_voiced_end:.2f}")
    print(f"wpm_by_last_voiced={words/last_voiced_end*60:.1f}  wpm_by_total={words/dur*60:.1f}")
    if len(p):
        print(f"pitch_median_hz={np.median(p):.1f} pitch_mean_hz={np.mean(p):.1f} "
              f"p10={np.percentile(p,10):.1f} p90={np.percentile(p,90):.1f} "
              f"IQR={np.percentile(p,75)-np.percentile(p,25):.1f}")
    print(f"pauses_ge_0.4s={int((internal>=0.4).sum())} max_pause_sec={internal.max() if len(internal) else 0:.2f} "
          f"pauses_ge_0.25s={int((internal>=0.25).sum())}")
    if cents:
        print(f"spectral_centroid_hz={np.median(cents):.0f}")


if __name__ == "__main__":
    main()
