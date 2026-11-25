#!/usr/bin/env python3
"""pass@k / pass^k unbiased estimators (Anthropic Demystifying evals / tau-bench).
Usage: passk.py N C K  -> prints pass@k and pass^k for n trials, c passes.
Stdlib only, no API. Estimators: pass@k = 1 - C(n-c,k)/C(n,k); pass^k = C(c,k)/C(n,k).
"""
import sys
from math import comb

def pass_at_k(n, c, k):
    if k > n: raise ValueError("k must be <= n")
    if n - c < k: return 1.0
    return 1 - comb(n - c, k) / comb(n, k)

def pass_hat_k(n, c, k):
    if k > n: raise ValueError("k must be <= n")
    if c < k: return 0.0
    return comb(c, k) / comb(n, k)

if __name__ == "__main__":
    n, c, k = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    print(f"n={n} c={c} k={k} pass@k={pass_at_k(n,c,k):.4f} pass^k={pass_hat_k(n,c,k):.4f}")
