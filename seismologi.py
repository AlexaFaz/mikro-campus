import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

# 1. Setting Konfigurasi Halaman Web
st.set_page_config(page_title="Seismic Risk Dashboard", layout="wide", page_icon="🏢")

st.title("🏢 Dashboard & Peta Indeks Kerentanan Seismik Kampus")
st.write("Aplikasi geofisika untuk menganalisis potensi kerusakan area berdasarkan nilai Indeks Kerentanan Seismik (Kg).")

st.markdown("---")

# 2. Fitur Upload Data
st.sidebar.header("📥 Input Data")
uploaded_file = st.sidebar.file_uploader("Unggah file CSV Parameter Mikrotremor", type=["csv"])

# Penyiapan data (Menggunakan baris pertama data asli kamu sebagai default agar langsung presisi)
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.sidebar.success("Data berhasil dimuat!")
else:
    st.sidebar.info("💡 Silakan unggah file CSV kamu di sebelah kiri untuk melihat peta lokasi asli.")
    # Menggunakan sampel data pertamamu agar peta langsung mengarah ke lokasi kampusmu
    data_default = {
        'Titik': [1, 2, 3, 4],
        'Longitude': [110.3942, 110.3936, 110.3941, 110.3941],
        'Latitude': [-7.78559, -7.78529, -7.7843, -7.7843],
        'A0': [2.99115, 5.5779, 5.08743, 2.05877],
        'f0': [1.1388, 0.482802, 0.333627, 1.21229],
        'Kg': [7.856497, 64.4425, 77.57749, 3.496304]
    }
    df = pd.DataFrame(data_default)

# Pastikan tipe data Titik diubah menjadi string/teks agar dropdown dan peta rapi
df['Titik'] = df['Titik'].astype(str)

# ======================== PROSES HITUNG PERSENTASE KERUSAKAN BERDASARKAN Kg ========================
# Pendekatan empiris: Jika Kg mencapai 50 atau lebih (di datamu ada yang sampai 664), otomatis 100%
def hitung_persen_dari_kg(kg):
    persen = (kg / 50.0) * 100
    return min(round(persen, 1), 100.0)

df['Potensi_Kerusakan_Tanah'] = df['Kg'].apply(hitung_persen_dari_kg)
# ====================================================================================================

# 3. Tampilkan Peta Sebaran Titik Koordinat (Bisa di-hover kursor)
st.subheader("🗺️ Peta Lokasi (Arahkan kursor ke titik untuk melihat Persentase Potensi Kerusakan Tanah)")

# Membuat peta interaktif menggunakan kolom dari Excel kamu ('Latitude' & 'Longitude')
fig_map = px.scatter_mapbox(
    df, 
    lat="Latitude", 
    lon="Longitude", 
    color="Potensi_Kerusakan_Tanah", 
    size=df['Kg'].clip(upper=100),    # Ukuran titik dibatasi biar tidak menutupi layar karena ada Kg yang sangat besar
    color_continuous_scale=px.colors.sequential.YlOrRd, 
    hover_name="Titik",
    hover_data={
        "Latitude": True,
        "Longitude": True,
        "f0": ":.2f",
        "A0": ":.2f",
        "Kg": ":.2f",
        "Potensi_Kerusakan_Tanah": ":.1f" 
    },
    zoom=16, 
    height=450
)

fig_map.update_layout(mapbox_style="open-street-map")
fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig_map, use_container_width=True)

st.markdown("---")

# 4. Dropdown untuk Memilih Titik Ukur yang akan Dievaluasi Lebih Detail
st.subheader("🔍 Detail Evaluasi Spesifik Titik")
pilihan_titik = st.selectbox("Silakan pilih nomor titik pengukuran:", df['Titik'])

data_terpilih = df[df['Titik'] == pilihan_titik].iloc[0]

f0_tanah = data_terpilih['f0']
A0_tanah = data_terpilih['A0']
kg_tanah = data_terpilih['Kg']
persen_rusak = data_terpilih['Potensi_Kerusakan_Tanah']

# 5. Tampilan Dashboard Hasil Evaluasi Grafik Batang
col1, col2 = st.columns([2, 1])

with col1:
    fig, ax = plt.subplots(figsize=(7, 3.8))
    kategori = ['Frekuensi Alami (f0)', 'Amplifikasi (A0)']
    nilai = [f0_tanah, A0_tanah]
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
    st.write("**Hasil Analisis Kerentanan:**")
    st.metric(label="Potensi Kerusakan/Kerentanan Tanah Lokal", value=f"{persen_rusak}%")
    st.metric(label="Indeks Kerentanan Seismik (Kg)", value=f"{kg_tanah:.2f}")
    st.write(f"📍 **Koordinat:** {data_terpilih['Latitude']:.5f}, {data_terpilih['Longitude']:.5f}")

st.markdown("---")

# 6. Kesimpulan & Rekomendasi Geofisika Berdasarkan Klasifikasi Nilai Kg
st.subheader("🚨 Zonasi Risiko Bencana Tanah Lokal")

if kg_tanah > 10.0:
    st.error(f"### 🔴 ZONA RAWAN TINGGI (Indeks Kg: {kg_tanah:.2f} | Estimasi Kerentanan: {persen_rusak}%)")
    st.write(f"**Analisis:** Titik ini berada pada zona sedimentasi lunak yang sangat tebal. Nilai Kg yang tinggi mengindikasikan bahwa jika terjadi gempa bumi, area ini akan mengalami amplifikasi guncangan yang sangat kuat dan rawan mengalami deformasi tanah parah.")
    st.write("**Rekomendasi Geoteknik:** Infrastruktur di area ini disarankan memiliki sistem fondasi dalam (tiang pancang) yang mencapai batuan dasar keras, serta audit kekuatan struktural berkala.")
    
elif kg_tanah >= 3.0:
    st.warning(f"### 🟡 ZONA RAWAN SEDANG (Indeks Kg: {kg_tanah:.2f} | Estimasi Kerentanan: {persen_rusak}%)")
    st.write(f"**Analisis:** Karakteristik tanah penyusun di sekitar titik ini tergolong sedang (transisi). Dampak guncangan gempa berada pada tingkat menengah.")
    
else:
    st.success(f"### 🟢 ZONA AMAN / STABIL (Indeks Kg: {kg_tanah:.2f} | Estimasi Kerentanan: {persen_rusak}%)")
    st.write(f"**Analisis:** Area titik ini didominasi oleh batuan kompak atau keras. Tanah sangat stabil dan resisten terhadap deformasi akibat guncangan seismik.")