import numpy as np, pandas as pd, plotly.graph_objects as go, streamlit as st
from analysis import analyze

st.set_page_config(page_title="Stress-Strain Analyzer", page_icon="📈", layout="wide")
st.title("📈 Stress-Strain Analyzer")
st.caption("Deteksi otomatis daerah elastis, yield, UTS, dan titik necking dari data uji tarik")

# ---------- Sidebar: input data ----------
with st.sidebar:
    st.header("1. Data input")
    up = st.file_uploader("Upload CSV/XLSX (kolom: gaya & pertambahan panjang)", type=["csv", "xlsx"])
    use_sample = st.checkbox("Pakai data contoh (baja dummy)", value=up is None)
    st.header("2. Spesimen")
    shape = st.radio("Penampang", ["Lingkaran (diameter)", "Persegi panjang (lebar x tebal)"])
    if shape.startswith("Lingkaran"):
        d = st.number_input("Diameter awal (mm)", 0.1, 100.0, 6.0)
        a0 = np.pi * d**2 / 4
    else:
        w = st.number_input("Lebar (mm)", 0.1, 100.0, 12.5)
        t = st.number_input("Tebal (mm)", 0.1, 50.0, 2.0)
        a0 = w * t
    l0 = st.number_input("Panjang ukur awal L0 (mm)", 1.0, 500.0, 50.0)
    st.write(f"A0 = **{a0:.3f} mm²**")
    force_unit = st.selectbox("Satuan gaya", ["N", "kN"])

df = None
if up is not None:
    df = pd.read_excel(up) if up.name.endswith("xlsx") else pd.read_csv(up)
elif use_sample:
    df = pd.read_csv("data/sample_baja.csv")

tab_home, tab_data, tab_curve, tab_res, tab_method = st.tabs(
    ["Beranda", "Data", "Kurva & Deteksi", "Hasil", "Metode"])

with tab_home:
    st.markdown("""
**Cara pakai:** upload data uji tarik (gaya & pertambahan panjang) di sidebar, isi dimensi spesimen,
lalu buka tab *Kurva & Deteksi* dan *Hasil*. Program menghitung σ = F/A₀ dan ε = ΔL/L₀, lalu
mendeteksi daerah elastis, Modulus Young, yield (0.2% offset), UTS, dan titik awal necking.""")

if df is None:
    for t_ in (tab_data, tab_curve, tab_res):
        with t_: st.info("Upload data atau centang data contoh di sidebar.")
    st.stop()

with tab_data:
    cols = list(df.columns)
    c1, c2 = st.columns(2)
    fcol = c1.selectbox("Kolom gaya", cols, index=0)
    lcol = c2.selectbox("Kolom pertambahan panjang (mm)", cols, index=min(1, len(cols) - 1))
    st.dataframe(df.head(50), width="stretch")

F = df[fcol].to_numpy(float) * (1000 if force_unit == "kN" else 1)
try:
    r = analyze(F, df[lcol].to_numpy(float), a0, l0)
except Exception as ex:
    for t_ in (tab_curve, tab_res):
        with t_: st.error(f"Analisis gagal: {ex}")
    st.stop()

eps, sig, e0 = r["eps"], r["sig"], r["eps0"]
with tab_curve:
    show_true = st.checkbox("Tampilkan kurva true stress-strain")
    fig = go.Figure()
    fig.add_scatter(x=eps, y=sig, name="Engineering", line=dict(color="#1f77b4"))
    i0, i1 = r["fit_idx"]
    fig.add_scatter(x=eps[:r["elastic_i"] + 1], y=sig[:r["elastic_i"] + 1], name="Daerah elastis",
                    line=dict(color="red", width=4))
    E = r["E_gpa"] * 1000
    x0 = e0 + 0.002                     # garis offset: sigma = E(eps - eps0 - 0.002)
    x1 = x0 + 1.15 * float(sig.max()) / E
    fig.add_scatter(x=[x0, x1], y=[0, E * (x1 - x0)], mode="lines",
                    name="Garis 0.2% offset", line=dict(color="gray", dash="dash"))
    pts = {"Batas elastis": r["elastic_limit"], "Yield (0.2%)": r["yield_pt"],
           "UTS": r["uts_pt"], "Awal necking": r["neck_pt"]}
    colors = ["orange", "green", "black", "purple"]
    for (n, (x, y)), c in zip(pts.items(), colors):
        fig.add_scatter(x=[x], y=[y], mode="markers+text", text=[n], textposition="top center",
                        marker=dict(size=11, color=c), name=n)
    if show_true:
        fig.add_scatter(x=np.expm1(r["eps_true"]), y=r["sig_true"], name="True", line=dict(color="green", dash="dot"))
    fig.update_layout(xaxis_title="Strain, ε", yaxis_title="Stress, σ (MPa)", height=560,
                      yaxis_range=[0, float(sig.max()) * 1.15])
    st.plotly_chart(fig, width="stretch")

with tab_res:
    c = st.columns(4)
    c[0].metric("Modulus Young", f"{r['E_gpa']:.1f} GPa")
    c[1].metric("Yield (0.2%)", f"{r['yield_pt'][1]:.1f} MPa")
    c[2].metric("UTS", f"{r['uts_pt'][1]:.1f} MPa")
    c[3].metric("Elongasi patah", f"{r['fracture_eps'] * 100:.1f} %")
    table = pd.DataFrame({
        "Besaran": ["Modulus Young (GPa)", "R² fit elastis", "Batas elastis (MPa)", "Yield 0.2% (MPa)",
                    "UTS (MPa)", "Regangan UTS", "Awal necking: ε", "Awal necking: σ (MPa)"],
        "Nilai": [r["E_gpa"], r["r2"], r["elastic_limit"][1], r["yield_pt"][1], r["uts_pt"][1],
                  r["uts_pt"][0], r["neck_pt"][0], r["neck_pt"][1]]}).round(4)
    st.dataframe(table, hide_index=True, width="stretch")
    st.download_button("⬇️ Unduh hasil (CSV)", table.to_csv(index=False), "hasil_analisis.csv")

with tab_method:
    st.markdown(r"""
1. **Tegangan & regangan teknik:** $\sigma = F/A_0$, $\varepsilon = \Delta L/L_0$.
2. **Daerah elastis & E:** regresi linear pada rentang 10–40% UTS; kemiringannya = Modulus Young.
   Intersep dipakai untuk koreksi *toe region*. Batas elastis = titik terakhir yang simpangannya dari
   garis lurus masih ≤ 2% UTS.
3. **Yield 0.2% offset:** perpotongan kurva dengan garis $\sigma = E(\varepsilon - 0.002)$.
4. **UTS:** tegangan maksimum (kurva dihaluskan Savitzky–Golay).
5. **Necking (Considère):** pada kurva true ($\sigma_t=\sigma(1+\varepsilon)$, $\varepsilon_t=\ln(1+\varepsilon)$),
   necking dimulai saat $d\sigma_t/d\varepsilon_t = \sigma_t$.
""")
