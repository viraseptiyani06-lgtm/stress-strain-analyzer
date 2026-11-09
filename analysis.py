"""Inti perhitungan Stress-Strain Analyzer (tanpa tampilan)."""
import numpy as np
from scipy.signal import savgol_filter
from scipy.stats import linregress


def eng_stress_strain(force_n, dl_mm, a0_mm2, l0_mm):
    """Langkah 3: sigma = F/A0 (MPa), epsilon = dL/L0."""
    return np.asarray(force_n) / a0_mm2, np.asarray(dl_mm) / l0_mm


def _smooth(y, win=15):
    win = min(win if win % 2 else win + 1, (len(y) // 2) * 2 - 1)
    return savgol_filter(y, win, 3) if win >= 5 else np.asarray(y)


def analyze(force_n, dl_mm, a0_mm2, l0_mm, fit_lo=0.10, fit_hi=0.40, tol=0.02):
    sig, eps = eng_stress_strain(force_n, dl_mm, a0_mm2, l0_mm)

    # Buang data setelah patah (tegangan jatuh < 50% UTS setelah UTS)
    i_max = int(np.argmax(sig))
    after = np.where(sig[i_max:] < 0.5 * sig[i_max])[0]
    n = i_max + after[0] if len(after) else len(sig)
    sig, eps = sig[:n], eps[:n]
    sig_s = _smooth(sig)
    uts_i = int(np.argmax(sig_s))
    uts = float(sig_s[uts_i])

    # Langkah 4: Modulus Young dari rentang 10-40% UTS (sebelum UTS)
    m = np.where((sig_s[:uts_i] >= fit_lo * uts) & (sig_s[:uts_i] <= fit_hi * uts))[0]
    if len(m) < 5:
        raise ValueError('Titik data di daerah elastis terlalu sedikit untuk fit linear.')
    fit = linregress(eps[m], sig[m])
    E = fit.slope                      # MPa
    eps0 = -fit.intercept / E          # koreksi toe region
    e = eps - eps0

    # Batas elastis: perluas dari rentang fit selama simpangan <= tol*UTS
    dev = np.abs(sig - E * e)
    k = int(m[-1])
    while k + 1 < uts_i and dev[k + 1] <= tol * uts:
        k += 1
    elastic_i = k

    # Yield 0.2% offset
    diff = sig - E * (e - 0.002)
    j = np.where((diff[elastic_i:] <= 0))[0]
    if len(j):
        j = elastic_i + int(j[0])
        t = diff[j - 1] / (diff[j - 1] - diff[j])
        ys_eps = eps[j - 1] + t * (eps[j] - eps[j - 1])
        ys = sig[j - 1] + t * (sig[j] - sig[j - 1])
    else:
        j, ys_eps, ys = elastic_i, np.nan, np.nan

    # Langkah 6: necking (kriteria Considere: d(sigma_t)/d(eps_t) = sigma_t)
    st = sig_s * (1 + eps)
    et = np.log1p(eps)
    start = max(elastic_i, j) + 1
    neck_i = uts_i
    if uts_i - start > 40:
        # resample ke grid seragam supaya turunan numerik stabil
        eg = np.linspace(et[start], et[uts_i], 300)
        sg = savgol_filter(np.interp(eg, et, st), 31, 3)
        dg = savgol_filter(np.interp(eg, et, st), 31, 3, deriv=1, delta=eg[1] - eg[0])
        c = np.where(dg <= sg)[0]
        c = c[c > 15] if len(c) else c      # abaikan efek tepi filter
        if len(c):
            neck_i = int(np.searchsorted(et, eg[c[0]]))
            neck_i = min(neck_i, uts_i)

    return dict(
        eps=eps, sig=sig, sig_s=sig_s, sig_true=st, eps_true=et, eps0=eps0,
        E_gpa=E / 1000, r2=fit.rvalue ** 2,
        fit_idx=(int(m[0]), int(m[-1])), elastic_i=elastic_i,
        elastic_limit=(float(eps[elastic_i]), float(sig[elastic_i])),
        yield_pt=(float(ys_eps), float(ys)),
        uts_pt=(float(eps[uts_i]), uts),
        neck_pt=(float(eps[neck_i]), float(sig_s[neck_i])),
        fracture_eps=float(eps[-1] - eps0),
    )
