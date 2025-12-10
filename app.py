import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Page config
st.set_page_config(
    page_title="Dashboard Stunting Sidoarjo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e40af 0%, #3b82f6 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Load data function with caching
@st.cache_data
def load_csv_data(file_path):
    """Load and process CSV data"""
    try:
        df = pd.read_csv("data/data_skrinning_stunting(1).csv", sep='\t', encoding='utf-8')
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return None

@st.cache_data
def load_geojson_data(file_path):
    """Load GeoJSON data"""
    try:
        with open("data/kecamatan_sidoarjo.geojson", 'r', encoding='utf-8') as f:
            geojson = json.load(f)
        return geojson
    except Exception as e:
        st.error(f"Error loading GeoJSON: {e}")
        return None

def aggregate_by_kecamatan(df):
    """Aggregate stunting data by kecamatan"""
    kec_stats = []
    
    for kecamatan in df['nama_kecamatan'].unique():
        kec_data = df[df['nama_kecamatan'] == kecamatan]
        
        total = len(kec_data)
        stunting = len(kec_data[kec_data['stunting_balita'] == 'Ya'])
        normal = total - stunting
        
        stats = {
            'kecamatan': kecamatan,
            'total': total,
            'stunting': stunting,
            'normal': normal,
            'persentase_stunting': round((stunting / total * 100), 2) if total > 0 else 0,
            'pendek': len(kec_data[kec_data['status_tbu'] == 'Pendek']),
            'sangat_pendek': len(kec_data[kec_data['status_tbu'] == 'Sangat Pendek']),
            'gizi_kurang': len(kec_data[kec_data['status_bbtb'] == 'Gizi Kurang']),
            'gizi_baik': len(kec_data[kec_data['status_bbtb'] == 'Gizi Baik']),
            'bb_kurang': len(kec_data[kec_data['status_bbu'] == 'BB Kurang']),
            'bb_normal': len(kec_data[kec_data['status_bbu'] == 'BB Normal']),
            'laki_laki': len(kec_data[kec_data['jenis_kelamin_balita'] == 'Laki - Laki']),
            'perempuan': len(kec_data[kec_data['jenis_kelamin_balita'] == 'Perempuan'])
        }
        
        # Prediksi sederhana
        if stats['persentase_stunting'] > 20:
            stats['prediksi'] = 'Perlu Perhatian'
            stats['tren'] = '+2.5%'
            stats['kategori'] = 'Tinggi'
        elif stats['persentase_stunting'] > 10:
            stats['prediksi'] = 'Perlu Monitoring'
            stats['tren'] = '+1.2%'
            stats['kategori'] = 'Sedang'
        else:
            stats['prediksi'] = 'Stabil'
            stats['tren'] = '+0.5%'
            stats['kategori'] = 'Rendah'
        
        kec_stats.append(stats)
    
    return pd.DataFrame(kec_stats)

def create_choropleth_map(geojson, stats_df):
    """Create choropleth map with stunting data"""
    
    # Merge geojson properties with stats
    for feature in geojson['features']:
        kecamatan_name = feature['properties']['WADMKC']
        kec_stat = stats_df[stats_df['kecamatan'] == kecamatan_name]
        
        if not kec_stat.empty:
            feature['properties']['stunting_count'] = int(kec_stat['stunting'].values[0])
            feature['properties']['persentase_stunting'] = float(kec_stat['persentase_stunting'].values[0])
            feature['properties']['total_balita'] = int(kec_stat['total'].values[0])
            feature['properties']['kategori'] = kec_stat['kategori'].values[0]
        else:
            feature['properties']['stunting_count'] = 0
            feature['properties']['persentase_stunting'] = 0
            feature['properties']['total_balita'] = 0
            feature['properties']['kategori'] = 'Tidak Ada Data'
    
    # Create choropleth map
    fig = px.choropleth_mapbox(
        stats_df,
        geojson=geojson,
        locations='kecamatan',
        featureidkey='properties.WADMKC',
        color='persentase_stunting',
        hover_name='kecamatan',
        hover_data={
            'total': True,
            'stunting': True,
            'persentase_stunting': ':.2f',
            'prediksi': True
        },
        color_continuous_scale=[
            [0, '#10b981'],      # Green (0-10%)
            [0.33, '#f59e0b'],   # Amber (10-20%)
            [0.66, '#ea580c'],   # Orange (20-30%)
            [1, '#dc2626']       # Red (>30%)
        ],
        mapbox_style="open-street-map",
        center={"lat": -7.45, "lon": 112.72},
        zoom=10,
        opacity=0.7,
        labels={
            'persentase_stunting': 'Persentase Stunting (%)',
            'total': 'Total Balita',
            'stunting': 'Kasus Stunting',
            'prediksi': 'Prediksi'
        }
    )
    
    fig.update_layout(
        height=600,
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )
    
    return fig

# Main app
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 Dashboard Stunting Kabupaten Sidoarjo</h1>
        <p>Sistem Informasi Geografis dan Prediksi Stunting Balita</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    csv_path = 'data_skrinning_stunting(1).csv'
    geojson_path = 'kecamatan_sidoarjo.geojson'
    
    with st.spinner('Memuat data...'):
        df = load_csv_data(csv_path)
        geojson = load_geojson_data(geojson_path)
    
    if df is None or geojson is None:
        st.error("⚠️ Pastikan file data tersedia di folder 'data/'")
        st.info("""
        **Struktur folder yang dibutuhkan:**
        ```
        project/
        ├── app.py
        ├── requirements.txt
        └── data/
            ├── data_stunting.csv
            └── kecamatan_sidoarjo.geojson
        ```
        """)
        return
    
    # Process data
    stats_df = aggregate_by_kecamatan(df)
    
    # Sidebar filters
    st.sidebar.header("🔍 Filter Data")
    
    selected_kecamatan = st.sidebar.multiselect(
        "Pilih Kecamatan:",
        options=['Semua'] + list(stats_df['kecamatan'].unique()),
        default=['Semua']
    )
    
    selected_puskesmas = st.sidebar.multiselect(
        "Pilih Puskesmas:",
        options=['Semua'] + list(df['nama_puskesmas'].unique()),
        default=['Semua']
    )
    
    # Filter data
    filtered_df = df.copy()
    if 'Semua' not in selected_kecamatan and selected_kecamatan:
        filtered_df = filtered_df[filtered_df['nama_kecamatan'].isin(selected_kecamatan)]
    if 'Semua' not in selected_puskesmas and selected_puskesmas:
        filtered_df = filtered_df[filtered_df['nama_puskesmas'].isin(selected_puskesmas)]
    
    # Recalculate stats for filtered data
    if not filtered_df.empty:
        display_stats = aggregate_by_kecamatan(filtered_df)
    else:
        display_stats = stats_df
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_balita = display_stats['total'].sum()
    total_stunting = display_stats['stunting'].sum()
    persentase_stunting = round((total_stunting / total_balita * 100), 2) if total_balita > 0 else 0
    total_pendek = display_stats['pendek'].sum()
    
    with col1:
        st.metric(
            label="👶 Total Balita",
            value=f"{total_balita:,}",
            delta="Terdata"
        )
    
    with col2:
        st.metric(
            label="⚠️ Kasus Stunting",
            value=f"{total_stunting:,}",
            delta=f"{persentase_stunting}%",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="📉 Pendek",
            value=f"{total_pendek:,}",
            delta="Status TBU"
        )
    
    with col4:
        st.metric(
            label="🏥 Puskesmas",
            value=len(df['nama_puskesmas'].unique()),
            delta="Terdaftar"
        )
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺️ Peta Stunting", 
        "📊 Analisis Per Kecamatan", 
        "🔮 Prediksi & Tren",
        "📈 Statistik Detail"
    ])
    
    with tab1:
        st.subheader("Peta Sebaran Stunting")
        
        # Create and display map
        map_fig = create_choropleth_map(geojson, stats_df)
        st.plotly_chart(map_fig, use_container_width=True)
        
        # Legend
        st.markdown("**Kategori Prevalensi Stunting:**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("🟢 **0-10%** Rendah")
        with col2:
            st.markdown("🟡 **10-20%** Sedang")
        with col3:
            st.markdown("🟠 **20-30%** Tinggi")
        with col4:
            st.markdown("🔴 **>30%** Sangat Tinggi")
    
    with tab2:
        st.subheader("Analisis Data Per Kecamatan")
        
        # Bar chart - Top kecamatan dengan stunting tertinggi
        top_kecamatan = display_stats.nlargest(10, 'persentase_stunting')
        
        fig_bar = px.bar(
            top_kecamatan,
            x='kecamatan',
            y='persentase_stunting',
            color='persentase_stunting',
            color_continuous_scale='Reds',
            title='Top 10 Kecamatan dengan Persentase Stunting Tertinggi',
            labels={'persentase_stunting': 'Persentase (%)', 'kecamatan': 'Kecamatan'}
        )
        fig_bar.update_layout(height=400)
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Table with detailed stats
        st.subheader("Data Detail Per Kecamatan")
        
        display_table = display_stats[[
            'kecamatan', 'total', 'stunting', 'persentase_stunting',
            'pendek', 'sangat_pendek', 'gizi_kurang', 'kategori', 'prediksi'
        ]].sort_values('persentase_stunting', ascending=False)
        
        st.dataframe(
            display_table.style.background_gradient(
                subset=['persentase_stunting'], 
                cmap='Reds'
            ),
            use_container_width=True,
            height=400
        )
    
    with tab3:
        st.subheader("Prediksi dan Proyeksi Stunting")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart - Kategori prediksi
            prediksi_counts = display_stats['prediksi'].value_counts()
            
            fig_pie = px.pie(
                values=prediksi_counts.values,
                names=prediksi_counts.index,
                title='Distribusi Status Prediksi Kecamatan',
                color_discrete_sequence=px.colors.sequential.RdYlGn_r
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Bar chart - Kategori risiko
            kategori_counts = display_stats['kategori'].value_counts()
            
            fig_kategori = px.bar(
                x=kategori_counts.index,
                y=kategori_counts.values,
                title='Jumlah Kecamatan per Kategori Risiko',
                labels={'x': 'Kategori', 'y': 'Jumlah Kecamatan'},
                color=kategori_counts.values,
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig_kategori, use_container_width=True)
        
        # Prediction table
        st.subheader("Detail Prediksi Per Kecamatan")
        
        prediction_table = display_stats[[
            'kecamatan', 'persentase_stunting', 'kategori', 'prediksi', 'tren'
        ]].sort_values('persentase_stunting', ascending=False)
        
        st.dataframe(prediction_table, use_container_width=True, height=400)
        
        # Alert untuk kecamatan yang perlu perhatian
        high_risk = display_stats[display_stats['kategori'] == 'Tinggi']
        if not high_risk.empty:
            st.warning(f"⚠️ **Perhatian!** Ada {len(high_risk)} kecamatan dengan kategori risiko TINGGI yang memerlukan intervensi segera.")
            st.dataframe(high_risk[['kecamatan', 'persentase_stunting', 'stunting']], use_container_width=True)
    
    with tab4:
        st.subheader("Statistik Detail")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Status TBU
            st.markdown("**Status Tinggi Badan menurut Umur (TBU)**")
            tbu_data = {
                'Normal': len(filtered_df[filtered_df['status_tbu'] == 'Normal']),
                'Pendek': len(filtered_df[filtered_df['status_tbu'] == 'Pendek']),
                'Sangat Pendek': len(filtered_df[filtered_df['status_tbu'] == 'Sangat Pendek'])
            }
            
            fig_tbu = px.pie(
                values=list(tbu_data.values()),
                names=list(tbu_data.keys()),
                color_discrete_sequence=['#10b981', '#f59e0b', '#dc2626']
            )
            st.plotly_chart(fig_tbu, use_container_width=True)
            
            # Jenis Kelamin
            st.markdown("**Distribusi Berdasarkan Jenis Kelamin**")
            gender_stunting = filtered_df.groupby(['jenis_kelamin_balita', 'stunting_balita']).size().unstack(fill_value=0)
            
            fig_gender = px.bar(
                gender_stunting,
                barmode='group',
                title='Stunting Berdasarkan Jenis Kelamin',
                labels={'value': 'Jumlah', 'jenis_kelamin_balita': 'Jenis Kelamin'}
            )
            st.plotly_chart(fig_gender, use_container_width=True)
        
        with col2:
            # Status BB/TB
            st.markdown("**Status Berat Badan menurut Tinggi Badan (BB/TB)**")
            bbtb_counts = filtered_df['status_bbtb'].value_counts()
            
            fig_bbtb = px.bar(
                x=bbtb_counts.index,
                y=bbtb_counts.values,
                color=bbtb_counts.values,
                color_continuous_scale='RdYlGn_r',
                labels={'x': 'Status BB/TB', 'y': 'Jumlah'}
            )
            st.plotly_chart(fig_bbtb, use_container_width=True)
            
            # Status BB/U
            st.markdown("**Status Berat Badan menurut Umur (BB/U)**")
            bbu_counts = filtered_df['status_bbu'].value_counts()
            
            fig_bbu = px.bar(
                x=bbu_counts.index,
                y=bbu_counts.values,
                color=bbu_counts.values,
                color_continuous_scale='RdYlGn_r',
                labels={'x': 'Status BB/U', 'y': 'Jumlah'}
            )
            st.plotly_chart(fig_bbu, use_container_width=True)
        
        # Top Puskesmas dengan kasus tertinggi
        st.subheader("Top 10 Puskesmas dengan Kasus Stunting Tertinggi")
        
        puskesmas_stunting = filtered_df[filtered_df['stunting_balita'] == 'Ya'].groupby('nama_puskesmas').size().sort_values(ascending=False).head(10)
        
        fig_puskesmas = px.bar(
            x=puskesmas_stunting.values,
            y=puskesmas_stunting.index,
            orientation='h',
            color=puskesmas_stunting.values,
            color_continuous_scale='Reds',
            labels={'x': 'Jumlah Kasus', 'y': 'Puskesmas'}
        )
        fig_puskesmas.update_layout(height=400)
        st.plotly_chart(fig_puskesmas, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: gray; padding: 20px;">
        <p>Dashboard Stunting Kabupaten Sidoarjo | Data diperbarui: {}</p>
        <p>Dikembangkan untuk monitoring dan analisis data stunting balita</p>
    </div>
    """.format(datetime.now().strftime("%d %B %Y")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()

