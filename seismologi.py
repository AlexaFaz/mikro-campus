import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

# 1. Setting Config Halaman
st.set_page_config(page_title="Seismic Risk Dashboard - UIN SUKA", layout="wide", page_icon="🏢")

# --- PEMBARUAN: ELEMEN HEADER KAMPUS ---
# Membuat layout kolom untuk Logo dan Judul Aplikasi di bagian atas
col_logo, col_judul = st.columns([1, 6])

with col_logo:
    # Mengambil lambang resmi UIN Sunan Kalijaga Yogyakarta
    url_logo_uin = "https://upload.wikimedia.org/wikipedia/commons/b/b2/Logo_UIN_Sunan_Kalijaga.png"
    st.image(url_logo_uin, width=110)

with col_judul:
    st.title("Dashboard Peta Mikrotremor & Karakteristik Sedimen Permukaan")
    st.subheader("Program Studi Geofisika, Fakultas Sains dan Teknologi, UIN Sunan Kalijaga")
    st.write("Aplikasi Interaktif Mikrozonasi Seismik Teknik. Silakan unggah file CSV parameter lapangan kamu melalui bilah samping (*sidebar*).")

st.markdown("---")

# 2. Fitur Upload Data (Sidebar)
st.sidebar.header("📥 Input Data")
uploaded_file = st.sidebar.file_uploader("Unggah file CSV Parameter Mikrotremor", type=["csv"])

# --- PEMBARUAN: HILANGKAN DATA SIMULASI BAWAAN ---
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.sidebar.success("Data lapangan berhasil dimuat!")
    
    # Standarisasi Nama Kolom (diubah ke lowercase & tanpa spasi luar)
    df.columns = [col.strip().lower() for col in df.columns]
    lon_col = next((c for c in ['longitude', 'lon', 'long', 'x'] if c in df.columns), None)
    lat_col = next((c for c in ['latitude', 'lat', 'y'] if c in df.columns), None)
    titik_col = 'titik' if 'titik' in df.columns else df.columns[0]
    f0_col = 'f0' if 'f0' in df.columns else ('f0(hz)' if 'f0(hz)' in df.columns else None)
    a0_col = 'a0' if 'a0' in df.columns else None
    kg_col = 'kg' if 'kg' in df.columns else None

    # Validasi keberadaan kolom esensial
    if not lon_col or not lat_col or not f0_col or not kg_col:
        st.error("❌ Format CSV tidak sesuai! Pastikan memiliki kolom: Titik, Longitude, Latitude, f0, a0, dan Kg.")
        st.stop()

    # Bersihkan teks kolom identitas titik
    df[titik_col] = df[titik_col].astype(str).str.strip()

    # LOGIKA INTERPRETASI SEISMOLOGI TEKNIK (HVSR)
    def interpretasi_sedimen_tanah(row):
        f0 = row[f0_col]
        if f0 > 9.9:
            tebal_sedimen = "Sangat Dangkal (< 10 meter)"
            jenis_tanah = "Batuan Keras / Tanah Sangat Padat"
        elif 2.0 <= f0 <= 9.9:
            tebal_sedimen = "Dangkal - Menengah (10 - 50 meter)"
            jenis_tanah = "Tanah Kaku / Pasir-Kerikil Padat"
        elif 0.75 <= f0 < 2.0:
            tebal_sedimen = "Dalam (50 - 100 meter)"
            jenis_tanah = "Tanah Lunak / Aluvium Tebal"
        else:
            tebal_sedimen = "Sangat Dalam (> 100 meter)"
            jenis_tanah = "Tanah Sangat Lunak / Sedimen Permukaan Sangat Tebal"
        return pd.Series([tebal_sedimen, jenis_tanah])

    df[['perkiraan_tebal_sedimen', 'perkiraan_jenis_tanah']] = df.apply(interpretasi_sedimen_tanah, axis=1)
    df['potensi_kerusakan_tanah'] = df[kg_col].apply(lambda x: min(round((x / 50.0) * 100, 1), 100.0))

    # --- 3. KOTAK METRICS / RINGKASAN STATISTIK REGIONAL ---
    st.subheader("📊 Ringkasan Kondisi Geofisika Wilayah")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Titik Ukur", f"{len(df)} Titik")
    m2.metric("Rata-rata Nilai Kg", f"{df[kg_col].mean():.2f}")
    max_kg_row = df.loc[df[kg_col].idxmax()]
    m3.metric("Kerentanan Tertinggi", f"Titik {max_kg_row[titik_col]}")
    m4.metric("Nilai Kg Maksimum", f"{max_kg_row[kg_col]:.2f}")

    st.markdown("---")

    # Inisialisasi awal Session State untuk titik aktif
    if "titik_aktif" not in st.session_state or st.session_state.titik_aktif not in df[titik_col].values:
        st.session_state.titik_aktif = df[titik_col].iloc[0]

    # --- 4. PEMBUATAN PETA INTERAKTIF ---
    st.subheader("🗺️ Peta Klik Interaktif (Klik langsung pada Angka Titik)")

    center_lat = df[lat_col].mean()
    center_lon = df[lon_col].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=15, tiles=None)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery',
        name='Satelit Esri',
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='openstreetmap',
        name='OpenStreetMap (Peta Jalan)',
        control=True
    ).add_to(m)

    # Plotting marker PIN angka
    for idx, row in df.iterrows():
        if row[kg_col] > 10: warna_bg = "red"
        elif row[kg_col] >= 3: warna_bg = "orange"
        else: warna_bg = "green"
        
        html_icon = f"""
        <div style="
            background-color: {warna_bg}; 
            color: white; 
            border-radius: 50%; 
            width: 32px; 
            height: 32px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            font-weight: bold; 
            border: 2px solid white;
            box-shadow: 0px 2px 5px rgba(0,0,0,0.5);
            font-family: 'Arial Black';
            font-size: 9px;">
            {row[titik_col]}
        </div>
        """
        
        folium.Marker(
            location=[row[lat_col], row[lon_col]],
            icon=folium.DivIcon(html=html_icon),
            tooltip=f"Titik {row[titik_col]}"
        ).add_to(m)

    folium.LayerControl().add_to(m)
    peta_output = st_folium(m, width="100%", height=450, key="peta_geofisika")

    # Interaktivitas Klik Peta
    if peta_output and peta_output.get("last_object_clicked"):
        lat_klik = peta_output["last_object_clicked"]["lat"]
        lon_klik = peta_output["last_object_clicked"]["lng"]
        
        match = df[
            (abs(df[lat_col] - lat_klik) < 0.0005) & 
            (abs(df[lon_col] - lon_klik) < 0.0005)
        ]
        if not match.empty:
            titik_baru = match[titik_col].iloc[0]
            if st.session_state.titik_aktif != titik_baru:
                st.session_state.titik_aktif = titik_baru
                st.rerun()

    st.markdown("---")

    # --- 5. DETAIL ANALISIS & GRAFIK (TABS) ---
    pilihan_titik = st.session_state.titik_aktif
    data_terpilih = df[df[titik_col] == pilihan_titik].iloc[0]

    tab1, tab2 = st.tabs([f"🔍 Detail Titik: {pilihan_titik}", "📈 Analisis Sebaran Regional Wilayah"])

    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            fig, ax = plt.subplots(figsize=(7, 3.5))
            kategori = ['Frekuensi Alami (f0)', 'Amplifikasi (A0)']
            nilai = [data_terpilih[f0_col], data_terpilih[a0_col]]
            
            bars = ax.bar(kategori, nilai, color=['#4B0082', '#008080'], width=0.35)
            ax.set_ylabel('Nilai Parameter', fontsize=11)
            ax.set_ylim(0, max(nilai) + 1.5)
            ax.grid(axis='y', linestyle='--', alpha=0.5)
            
            for bar in bars:
                yval = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, yval + 0.1, f"{yval:.2f}", ha='center', va='bottom', fontweight='bold')
                
            ax.set_title(f"Spektrum Mikrotremor Titik Ukur {pilihan_titik}", fontsize=12, fontweight='bold')
            st.pyplot(fig)
            
            # Tombol Download CSV Titik Terpilih
            df_download = pd.DataFrame([data_terpilih])
            csv_data = df_download.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Download Data Report Titik {pilihan_titik}",
                data=csv_data,
                file_name=f"report_titik_{pilihan_titik}.csv",
                mime="text/csv"
            )

        with col2:
            st.write("📊 **Hasil Interpretasi & Geofisika Teknik:**")
            st.info(f"⏳ **Perkiraan Tebal Sedimen:** \n\n **{data_terpilih['perkiraan_tebal_sedimen']}**")
            st.success(f"🌱 **Perkiraan Jenis Tanah:** \n\n **{data_terpilih['perkiraan_jenis_tanah']}**")
            st.markdown("---")
            st.metric(label="Potensi Kerusakan Tanah Lokal", value=f"{data_terpilih['potensi_kerusakan_tanah']}%")
            st.metric(label="Indeks Kerentanan Seismik (Kg)", value=f"{data_terpilih[kg_col]:.2f}")

    with tab2:
        st.write("📊 **Grafik Tren Parameter Wilayah Penelitian**")
        c_graph1, c_graph2 = st.columns(2)
        
        with c_graph1:
            fig2, ax2 = plt.subplots(figsize=(6, 3.5))
            ax2.scatter(df[f0_col], df[a0_col], color='purple', alpha=0.7, edgecolors='black', s=80)
            ax2.set_xlabel("Frekuensi Alami (f0) - Hz", fontsize=10)
            ax2.set_ylabel("Amplifikasi (A0)", fontsize=10)
            ax2.set_title("Scatter Plot: f0 vs A0 Seluruh Titik Ukur", fontsize=11, fontweight='bold')
            ax2.grid(True, linestyle='--', alpha=0.5)
            st.pyplot(fig2)
            
        with c_graph2:
            fig3, ax3 = plt.subplots(figsize=(6, 3.5))
            ax3.hist(df[kg_col], bins=5, color='orange', edgecolor='black', alpha=0.8)
            ax3.set_xlabel("Indeks Kerentanan Seismik (Kg)", fontsize=10)
            ax3.set_ylabel("Frekuensi Muncul", fontsize=10)
            ax3.set_title("Histogram Sebaran Nilai Indeks Kerentanan (Kg)", fontsize=11, fontweight='bold')
            ax3.grid(True, linestyle='--', alpha=0.5)
            st.pyplot(fig3)

else:
    # --- TAMPILAN AWAL (KOSONGAN) SEBELUM UPLOAD FILE ---
    st.info("👋 Selamat Datang! Silakan masukkan/unggah file CSV pengukuran mikrotremor kamu melalui panel input di sebelah kiri untuk mengaktifkan seluruh analisis peta mikrozonasi.")
    
    # Menampilkan panduan format kolom agar user tidak salah membuat file CSV
    st.subheader("📋 Panduan Format Kolom File CSV:")
    st.write("Pastikan file data lapangan `.csv` milikmu memiliki susunan nama judul kolom sebagai berikut:")
    
    contoh_format = pd.DataFrame({
        'Titik': ['MR01', 'MR02'],
        'Longitude': [110.3942, 110.3936],
        'Latitude': [-7.78559, -7.78529],
        'f0': [1.13, 0.48],
        'A0': [2.99, 5.57],
        'Kg': [7.85, 64.44]
    })
    st.table(contoh_format)
