import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

# 1. Setting Config Halaman
st.set_page_config(page_title="Seismic Risk Dashboard", layout="wide", page_icon="🏢")

st.title("🏢 Dashboard Peta Mikrotremor & Formasi Geologi Regional")
st.write("Aplikasi geofisika teknik interaktif. Klik langsung pada PIN ANGKA di peta untuk melihat detail grafik!")

st.markdown("---")

# 2. Fitur Upload Data
st.sidebar.header("📥 Input Data")
uploaded_file = st.sidebar.file_uploader("Unggah file CSV Parameter Mikrotremor", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.sidebar.success("Data berhasil dimuat!")
else:
    st.sidebar.info("💡 Menampilkan data simulasi bawaan. Silakan unggah file CSV kamu.")
    data_default = {
        'Titik': ['MR01', 'MR02', 'MR03', 'MR04'],
        'Longitude': [110.3942, 110.3936, 110.3941, 110.3941],
        'Latitude': [-7.78559, -7.78529, -7.7843, -7.7843],
        'A0': [2.99115, 5.5779, 5.08743, 2.05877],
        'f0': [1.1388, 0.482802, 0.333627, 1.21229],
        'Kg': [7.856497, 64.4425, 77.57749, 3.496304]
    }
    df = pd.DataFrame(data_default)

# Standarisasi Nama Kolom
df.columns = [col.strip().lower() for col in df.columns]
lon_col = next((c for c in ['longitude', 'lon', 'long', 'x'] if c in df.columns), None)
lat_col = next((c for c in ['latitude', 'lat', 'y'] if c in df.columns), None)
titik_col = 'titik' if 'titik' in df.columns else df.columns[0]
f0_col = 'f0' if 'f0' in df.columns else ('f0(hz)' if 'f0(hz)' in df.columns else None)
a0_col = 'a0' if 'a0' in df.columns else None
kg_col = 'kg' if 'kg' in df.columns else None

if not lon_col or not lat_col or not f0_col:
    st.error("❌ Format kolom koordinat atau parameter utama tidak ditemukan di CSV kamu!")
    st.stop()

# Bersihkan teks kolom titik
df[titik_col] = df[titik_col].astype(str).str.strip()

# LOGIKA INTERPRETASI BARU (Lebih Valid Secara Seismologi Teknik)
def interpretasi_sedimen_tanah(row):
    f0 = row[f0_col]
    
    # Klasifikasi perkiraan ketebalan sedimen berdasarkan Frekuensi Alami (f0)
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

# Terapkan fungsi interpretasi baru ke dataframe
df[['perkiraan_tebal_sedimen', 'perkiraan_jenis_tanah']] = df.apply(interpretasi_sedimen_tanah, axis=1)
df['potensi_kerusakan_tanah'] = df[kg_col].apply(lambda x: min(round((x / 50.0) * 100, 1), 100.0))

# Inisialisasi awal Session State untuk titik aktif
if "titik_aktif" not in st.session_state or st.session_state.titik_aktif not in df[titik_col].values:
    st.session_state.titik_aktif = df[titik_col].iloc[0]

# 3. Pembuatan Peta Satelit Esri dengan Pin Angka
st.subheader("🗺️ Peta Klik Interaktif (Klik langsung pada Angka Titik)")

center_lat = df[lat_col].mean()
center_lon = df[lon_col].mean()

m = folium.Map(location=[center_lat, center_lon], zoom_start=15, tiles=None)
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Esri World Imagery',
    name='Satelit Esri'
).add_to(m)

# Pasang PIN Teks Angka tanpa Popup mengganggu
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

# Tampilkan peta dan tangkap data klik koordinat marker
peta_output = st_folium(m, width="100%", height=450, key="peta_geofisika")

# Tangkap koordinat bumi langsung begitu marker diklik
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

# 4. Tampilan Dashboard Bawah Berdasarkan Titik yang Diklik
pilihan_titik = st.session_state.titik_aktif
data_terpilih = df[df[titik_col] == pilihan_titik].iloc[0]

st.subheader(f"🔍 Detail Analisis Geofisika: Titik {pilihan_titik}")

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
        
    ax.set_title(f"Spektrum Mikrotremor Titik Ukur {pilihan_titik}", fontsize=12, fontweight='bold")
    st.pyplot(fig)

with col2:
    st.write("📊 **Hasil Interpretasi & Geofisika Teknik:**")
    
    # DISPLAY BARU: Memecah Perkiraan Tebal Sedimen dan Jenis Tanah
    st.info(f"⏳ **Perkiraan Tebal Sedimen:** \n\n **{data_terpilih['perkiraan_tebal_sedimen']}**")
    st.success(f"🌱 **Perkiraan Jenis Tanah:** \n\n **{data_terpilih['perkiraan_jenis_tanah']}**")
    
    st.markdown("---")
    st.metric(label="Potensi Kerusakan Tanah Lokal", value=f"{data_terpilih['potensi_kerusakan_tanah']}%")
    st.metric(label="Indeks Kerentanan Seismik (Kg)", value=f"{data_terpilih[kg_col]:.2f}")
