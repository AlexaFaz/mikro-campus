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

# Logika Geofisika
def estimasi_geologi(row):
    f0, A0 = row[f0_col], row[a0_col]
    if f0 > 5.0 and A0 < 2.5: return "Formasi Batuan Keras (Hard Rock)"
    elif 2.0 <= f0 <= 5.0: return "Sedimen Klasik Padat / Batupasir-Batugamping"
    else: return "Formasi Alluvium Lunak / Sedimen Permukaan Tebal" if A0 > 4.0 else "Formasi Sedimen Setengah Padat"

df['estimasi_geologi'] = df.apply(estimasi_geologi, axis=1)
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

# LOGIKA BARU: Tembak koordinat bumi langsung begitu marker tersentuh/diklik
if peta_output and peta_output.get("last_object_clicked"):
    lat_klik = peta_output["last_object_clicked"]["lat"]
    lon_klik = peta_output["last_object_clicked"]["lng"]
    
    # Mencari baris data di CSV yang memiliki selisih koordinat sangat kecil (toleransi kedekatan posisi)
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
        
    ax.set_title(f"Spektrum Mikrotremor Titik Ukur {pilihan_titik}", fontsize=12, fontweight='bold')
    st.pyplot(fig)

with col2:
    st.write("📊 **Hasil Interpretasi & Geofisika Teknik:**")
    st.success(f"🗺️ **Prediksi Formasi:** \n\n **{data_terpilih['estimasi_geologi']}**")
    st.markdown("---")
    st.metric(label="Potensi Kerusakan Tanah Lokal", value=f"{data_terpilih['potensi_kerusakan_tanah']}%")
    st.metric(label="Indeks Kerentanan Seismik (Kg)", value=f"{data_terpilih[kg_col]:.2f}")
