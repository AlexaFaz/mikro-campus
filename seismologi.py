# 3. Peta Interaktif Plotly (SUDAH DITAMBAH LABEL ANGKA TITIK PERMANEN)
st.subheader("🗺️ Peta Lokasi & Distribusi Titik Pengukuran Mikrotremor")

fig_map = px.scatter_mapbox(
    df, 
    lat=lat_col, 
    lon=lon_col, 
    color="potensi_kerusakan_tanah", 
    size=df[kg_col].clip(upper=100),    
    color_continuous_scale=px.colors.sequential.YlOrRd, 
    hover_name=titik_col,
    text=titik_col, # <-- INI UNTUK MEMUNCULKAN TEKS ANGKA TITIK DI PETA
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
    height=500
)

# Mengatur tampilan text/label agar muncul secara permanen di atas lingkaran titik ukur
fig_map.update_traces(
    textposition='top center',
    textfont=dict(size=13, color='black', family='Arial Black')
)

fig_map.update_layout(mapbox_style="open-street-map")
fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig_map, use_container_width=True)
