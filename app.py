import os
import numpy as np, pandas as pd, plotly.graph_objects as go, streamlit as st
from analysis import analyze

st.set_page_config(page_title="Stress-Strain Analyzer", page_icon="📈", layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>
.hero {
    background: linear-gradient(135deg, #1f4e79 0%, #2e86c1 60%, #5dade2 100%);
    padding: 28px 32px; border-radius: 14px; color: white; margin-bottom: 18px;
}
.hero h1 { color: white; margin: 0 0 6px 0; font-size: 2.1rem; }
.hero p  { color: #eaf2f8; margin: 0; font-size: 1.02rem; }
.step-card {
    background: #f4f8fb; border-left: 5px solid #2e86c1; border-radius: 8px;
    padding: 14px 16px; height: 100%;
}
.step-card b { color: #1f4e79; }
@media (prefers-color-scheme: dark) {
    .step-card { background: #1c2733; }
    .step-card b { color: #7fb8e6; }
}
</style>
""", unsafe_allow_html=True)


def show_img(path, **kw):
    """Tampilkan gambar hanya kalau filenya ada (supaya app tidak error)."""
    if os.path.exists(path):
        st.image(path, **kw)
        return True
    return False


# ---------- Header ----------
st.markdown("""
<div class="hero">
  <h1>📈 Stress-Strain Analyzer</h1>
  <p>Deteksi otomatis daerah elastis, yield, UTS, dan titik necking dari data uji tarik</p>
</div>
""", unsafe_allow_html=True)
show_img("assets/banner.jpg", width="stretch")

# ---------- State ----------
if "use_sample" not in st.session_state:
    st.session_state.use_sample = False   # default: KOSONG saat pertama dibuka / di-refresh

# ---------- Sidebar: input data ----------
with st.sidebar:
    show_img("assets/logo.png", width=120)

    st.header("1. Data input")
    up = st.file_uploader("Upload CSV/XLSX (kolom: gaya & pertambahan panjang)", type=["csv", "xlsx"])

    c_a, c_b = st.columns(2)
    if c_a.button("Data contoh", width="stretch", help="Muat data baja dummy"):
        st.session_state.use_sample = True
    if c_b.button("Reset", width="stretch", help="Kosongkan data"):
        st.session_state.use_sample = False
    if up is None and st.session_state.use_sample:
        st.caption("✅ Memakai data contoh (baja dummy)")

    st.header("2. Spesimen")
  shape = st.radio("Penampang", ["Lingkaran (diameter)", "Segiempat (lebar x tebal)"])
    if shape.startswith("Lingkaran"):
        d = st.number_input("Diameter awal (mm)", 0.1, 100.0, 6.0)
        a0 = np.pi * d**2 / 4
    else:
        w = st.number_input("Lebar (mm)", 0.1, 100.0, 12.5)
        t = st.number_input("Tebal (mm)", 0.1, 50.0, 2.0)
        a0 = w * t
    l0 = st.number_input("Panjang ukur awal L0 (mm)", 1.0, 500.0, 50.0)
    st.write(f"A0 = **{a0:.3f} mm²**")

    # Opsi satuan gaya diperluas
    FORCE_FACTOR = {"N": 1.0, "kN": 1000.0, "kgf": 9.80665, "lbf": 4.44822}
    force_unit = st.selectbox("Satuan gaya", list(FORCE_FACTOR.keys()))

# ---------- Load data ----------
df = None
if up is not None:
    df = pd.read_excel(up) if up.name.endswith("xlsx") else pd.read_csv(up)
elif st.session_state.use_sample:
    df = pd.read_csv("data/sample_baja.csv")

tab_home, tab_data, tab_curve, tab_res, tab_method = st.tabs(
    ["🏠 Beranda", "🗂️ Data", "📉 Kurva & Deteksi", "📊 Hasil", "📘 Metode"])

# ---------- Beranda ----------
with tab_home:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("""
**Cara pakai:** upload data uji tarik (gaya & pertambahan panjang) di sidebar, isi dimensi spesimen,
lalu buka tab *Kurva & Deteksi* dan *Hasil*. Program menghitung σ = F/A₀ dan ε = ΔL/L₀, lalu
mendeteksi daerah elastis, Modulus Young, yield (0.2% offset), UTS, dan titik awal necking.""")
        s1, s2, s3 = st.columns(3)
        s1.markdown('<div class="step-card"><b>1. Upload data</b><br>File CSV/XLSX berisi gaya dan pertambahan panjang.</div>', unsafe_allow_html=True)
        s2.markdown('<div class="step-card"><b>2. Isi spesimen</b><br>Bentuk penampang, dimensi, dan panjang ukur awal.</div>', unsafe_allow_html=True)
        s3.markdown('<div class="step-card"><b>3. Lihat hasil</b><br>Kurva, titik penting, dan tabel yang bisa diunduh.</div>', unsafe_allow_html=True)
    with c2:
        if not show_img("assets/kurva.png", caption="Kurva stress-strain", width="stretch"):
            # ilustrasi otomatis kalau belum ada gambar
            ex = go.Figure(go.Scatter(
                x=[0, 0.003, 0.02, 0.08, 0.15, 0.2, 0.25],
                y=[0, 250, 270, 400, 450, 420, 330],
                mode="lines", line=dict(color="#2e86c1", width=3)))
            ex.update_layout(title="Contoh kurva", height=260, margin=dict(l=10, r=10, t=40, b=10),
                             xaxis_title="ε", yaxis_title="σ (MPa)")
            st.plotly_chart(ex, width="stretch")

# ---------- Kondisi belum ada data: tampilan kosong ----------
if df is None:
    with tab_data:
        st.info("Belum ada data. Upload file CSV/XLSX di sidebar, atau klik **Data contoh**.")
    with tab_curve:
        st.info("Kurva akan muncul setelah data dimasukkan. Berikut ilustrasi kurva umum (bukan data kamu):")
        ill = go.Figure(go.Scatter(
            x=[0, 0.003, 0.02, 0.08, 0.15, 0.2, 0.25],
            y=[0, 250, 270, 400, 450, 420, 330],
            mode="lines", line=dict(color="lightgray", width=3)))
        ill.update_layout(title="Ilustrasi", xaxis_title="Strain, ε",
                          yaxis_title="Stress, σ (MPa)", height=420)
        st.plotly_chart(ill, width="stretch")
    with tab_res:
        st.info("Hasil belum tersedia. Masukkan data terlebih dahulu.")
        c = st.columns(4)
        for col, nama in zip(c, ["Modulus Young", "Yield (0.2%)", "UTS", "Elongasi patah"]):
            col.metric(nama, "–")
    with tab_method:
        pass  # diisi di bawah (tab Metode tetap tampil)
    st.session_state["_no_data"] = True
else:
    st.session_state["_no_data"] = False

if not st.session_state["_no_data"]:
    # ---------- Data ----------
    with tab_data:
        cols = list(df.columns)
        c1, c2 = st.columns(2)
        fcol = c1.selectbox("Kolom gaya", cols, index=0)
        lcol = c2.selectbox("Kolom pertambahan panjang (mm)", cols, index=min(1, len(cols) - 1))
        st.dataframe(df.head(50), width="stretch")

    F = df[fcol].to_numpy(float) * FORCE_FACTOR[force_unit]
    r = None
    try:
        r = analyze(F, df[lcol].to_numpy(float), a0, l0)
    except Exception as ex:
        for t_ in (tab_curve, tab_res):
            with t_:
                st.error(f"Analisis gagal: {ex}")

    if r is not None:
        eps, sig, e0 = r["eps"], r["sig"], r["eps0"]

        # ---------- Kurva ----------
        with tab_curve:
            show_true = st.checkbox("Tampilkan kurva true stress-strain")
            fig = go.Figure()
            fig.add_scatter(x=eps, y=sig, name="Engineering", line=dict(color="#1f77b4"))
            fig.add_scatter(x=eps[:r["elastic_i"] + 1], y=sig[:r["elastic_i"] + 1], name="Daerah elastis",
                            line=dict(color="red", width=4))
            E = r["E_gpa"] * 1000
            x0 = e0 + 0.002  # garis offset: sigma = E(eps - eps0 - 0.002)
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
                fig.add_scatter(x=np.expm1(r["eps_true"]), y=r["sig_true"], name="True",
                                line=dict(color="green", dash="dot"))
            fig.update_layout(xaxis_title="Strain, ε", yaxis_title="Stress, σ (MPa)", height=560,
                              yaxis_range=[0, float(sig.max()) * 1.15])
            st.plotly_chart(fig, width="stretch")

        # ---------- Hasil ----------
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

# ---------- Metode ----------
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

st.divider()
st.caption("Stress-Strain Analyzer • Satuan: gaya sesuai pilihan, panjang dalam mm, tegangan dalam MPa")
