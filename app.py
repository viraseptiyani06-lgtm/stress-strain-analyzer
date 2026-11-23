# ---------- Sidebar: input data ----------
with st.sidebar:
    show_img("assets/logo.png", width=120)

    st.header("1. Data input")
    up = st.file_uploader(
        "Upload CSV/XLSX (kolom: gaya & pertambahan panjang)",
        type=["csv", "xlsx"]
    )

    c_a, c_b = st.columns(2)

    if c_a.button("Data contoh", width="stretch", help="Muat data baja dummy"):
        st.session_state.use_sample = True

    if c_b.button("Reset", width="stretch", help="Kosongkan data"):
        st.session_state.use_sample = False

    if up is None and st.session_state.use_sample:
        st.caption("✅ Memakai data contoh (baja dummy)")

    st.header("2. Spesimen")

    shape = st.radio(
        "Penampang",
        ["Lingkaran", "Segiempat"]
    )

    if shape.startswith("Lingkaran"):
        d = st.number_input("Diameter awal (mm)", 0.1, 100.0, 6.0)
        a0 = np.pi * d**2 / 4

    else:
        w = st.number_input("Lebar (mm)", 0.1, 100.0, 12.5)
        t = st.number_input("Tebal (mm)", 0.1, 50.0, 2.0)
        a0 = w * t

    l0 = st.number_input("Panjang ukur awal L0 (mm)", 1.0, 500.0, 50.0)

    st.write(f"A0 = **{a0:.3f} mm²**")

    FORCE_FACTOR = {
        "N": 1.0,
        "kN": 1000.0,
        "kgf": 9.80665,
        "lbf": 4.44822
    }

    force_unit = st.selectbox("Satuan gaya", list(FORCE_FACTOR.keys()))
