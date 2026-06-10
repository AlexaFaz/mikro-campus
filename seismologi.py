import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

# 1. Setting Config Halaman
st.set_page_config(page_title="Seismic Risk Dashboard", layout="wide", page_icon="🏢")

st.title("🏢 Dashboard Peta Mikrotremor & Formasi Geologi Regional")
st.write("Aplikasi geofisika teknik untuk menampilkan parameter mikrotremor dan zonasi risiko kerusakan tanah.")

st.markdown("---")

# 2. Fitur Upload Data
st.sidebar.header("📥 Input Data")
uploaded_file = st.sidebar.file_uploader("Unggah file CSV Parameter Mikrotremor", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.sidebar.success("Data berhasil dimuat!")
else:
    st.sidebar.info("💡 Menampilkan data simulasi bawaan. Silakan unggah file CSV kamu di sebelah kiri.")
    data_default = {
        'Titik': [1, 2, 3, 4],
        'Longitude': [110.3942, 110.3936, 110.3941, 110.3941],
        'Latitude': [-7.78559, -7.78529, -7.7843, -7.7843],
        'A0': [2.99115, 5.5779, 5.08743, 2.05877],
        'f0': [1.1388, 0.482802, 0.333627, 1.21229],
        'Kg': [7.856497, 64.4425, 77.57749, 3.496304]
    }
    df = pd.DataFrame(data_default)

# --- STANDARISASI KOLOM AGAR ANTI-ERROR (KAPITAL/HURUF KECIL AMAN) ---
# Mengubah semua nama kolom di CSV menjadi huruf kecil agar mudah dicocokkan
df.columns = [col.strip().lower() for col in df.columns]

# Cari kolom longitude
lon_col = None
for c in ['longitude', 'lon', 'long', 'x']:
    if c in df.columns:
        lon_col = c
        break

# Cari kolom latitude
lat_col = None
for c in ['latitude', 'lat', 'y']:
    if c in df.columns:
        lat_col = c
        break

# Cari kolom titik, f0, a0, kg
titik_col = 'titik' if 'titik' in df.columns else df.columns[0]
f0_col = 'f0' if 'f0' in df.columns else ('f0(hz)' if 'f0(hz)' in df.columns else None)
a0_col = 'a0' if 'a0' in df.columns else None
kg_col = 'kg' if 'kg' in df.columns else None

# Validasi utama jika kolom wajib tidak ditemukan
if lon_col is None or lat_col is None:
    st.error("❌ Waduh! Kolom Koordinat tidak ditemukan di CSV kamu. Pastikan ada nama kolom 'Longitude' dan 'Latitude' ya!")
    st.stop()

if f0_col is None or a0_col is None or kg_col is None:
    st.error("❌ Waduh! Kolom parameter geofisika (f0, A0, atau Kg) tidak ditemukan di CSV kamu.")
    st.stop()

# Kembalikan tipe data ke string untuk dropdown
df[titik_col] = df[titik_col].astype(str)

# LOGIKA GEOFISIKA OTOMATIS
def estimasi_geologi(row):
    f0 = row[f0_col]
    A0 = row[a0_col]
    if f0 > 5.0 and A0 < 2.5:
        return "Formasi Batuan Keras (Hard Rock)"
    elif 2.0 <= f0 <= 5.0:
        return "Sedimen Klasik Padat / Batupasir-Batugamping"
    else:
        return "Formasi Alluvium Lunak / Sedimen Permukaan Tebal" if A0 > 4.0 else "Formasi Sedimen Setengah Padat"

df['estimasi_geologi'] = df.apply(estimasi_geologi, axis=1)
df['potensi_kerusakan_tanah'] = df[kg_col].apply(lambda x: min(round((x / 50.0) * 100, 1), 100.0))

# 3. Peta Interaktif Plotly
st.subheader("🗺️ Peta Lokasi (Arahkan kursor untuk melihat Formasi Geologi Asli Peta)")

fig_map = px.scatter_mapbox(
    df, 
    lat=lat_col, 
    lon=lon_col, 
    color="potensi_kerusakan_tanah", 
    size=df[kg_col].clip(upper=100),    
    color_continuous_scale=px.colors.sequential.YlOrRd, 
    hover_name=titik_col,
    hover_data={
        lat_col: True,
        lon_col: True,
        f0_col: ":.2f",
        a0_col: ":.2f",
        kg_col: ":.2f",
        "estimasi_geologi": True,
        "potensi_kerusakan_tanah": ":.1f" 
    },
    zoom=14, 
    height=450
)

fig_map.update_layout(mapbox_style="open-street-map")
fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig_map, use_container_width=True)

st.markdown("---")

# 4. Dropdown Detail Spesifik Titik
st.subheader("🔍 Detail Evaluasi Spesifik Titik")
pilihan_titik = st.selectbox("Silakan pilih nomor titik pengukuran:", df[titik_col])

data_terpilih = df[df[titik_col] == pilihan_titik].iloc[0]

# 5. Tampilan Dashboard Bawah
col1, col2 = st.columns([2, 1])

with col1:
    fig, ax = plt.subplots(figsize=(7, 3.8))
    kategori = ['Frekuensi Alami (f0)', 'Amplifikasi (A0)']
    nilai = [data_terpilih[f0_col], data_terpilih[a0_col]]
    warna_bar = ['#4B0082', '#008080'] 
    
    bars = ax.bar(kategori, nilai, color=warna_bar, width=0.4)
    ax.set_ylabel('Nilai Parameter', fontsize=12)
    ax.set_ylim(0, max(nilai) + 1.5)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 0.1, f"{yval:.2f}", ha='center', va='bottom', fontweight='bold')
        
    ax.set_title(f"Karakteristik Parameter Mikrotremor di Titik {pilihan_titik}", fontsize=14, fontweight='bold')
    st.pyplot(fig)

with col2:
    st.write("🔍 **Hasil Interpretasi & Geofisika Teknik:**")
    st.success(f"🗺️ **Prediksi Formasi:** \n\n **{data_terpilih['estimasi_geologi']}**")
    st.markdown("---")
    st.metric(label="Potensi Kerusakan Tanah Lokal", value=f"{data_terpilih['potensi_kerusakan_tanah']}%")
    st.metric(label="Indeks Kerentanan Seismik (Kg)", value=f"{data_terpilih[kg_col]:.2f}")
