"""Buat data dummy uji tarik (Force_N, Elongation_mm) untuk tes program."""
import numpy as np, pandas as pd
from scipy.optimize import brentq

rng = np.random.default_rng(1)
d, L0, E, sy, K, n = 6.0, 50.0, 200e3, 300.0, 700.0, 0.5
A0 = np.pi * d**2 / 4

def true_stress(ep_plastic):
    return sy + K * ep_plastic**n

# titik Considere: dsigma/depsilon = sigma
ep_u = brentq(lambda ep: K * n * ep**(n - 1) - true_stress(ep), 1e-4, 1.0)
eu = np.exp(ep_u + sy / E) - 1
ef = eu + 0.08
e = np.concatenate([np.linspace(0, 3 * sy / E, 250, endpoint=False),
                    np.linspace(3 * sy / E, ef, 600)])
sig = np.empty_like(e)
yield_e = sy / E
for i, ei in enumerate(e):
    if ei < yield_e:
        sig[i] = E * ei
    elif ei <= eu:
        sig[i] = true_stress(np.log1p(ei) - sy / E) / (1 + ei)
    else:
        s_u = true_stress(np.log1p(eu) - sy / E) / (1 + eu)
        sig[i] = s_u * (1 - 0.45 * ((ei - eu) / (ef - eu)) ** 1.6)
sig += rng.normal(0, 1.0, len(sig))
e = e + 0.0001 * (1 - np.exp(-e / 0.0002))  # toe region kecil
pd.DataFrame({"Force_N": sig * A0, "Elongation_mm": e * L0}).to_csv(
    "data/sample_baja.csv", index=False)
print(f"A0 = {A0:.3f} mm2 (d={d} mm), L0 = {L0} mm; eu teoritis = {eu:.4f}")
