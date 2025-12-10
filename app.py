import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

# ==========================================
# LOAD DATA
# ==========================================
@st.cache_data
def load_csv(path):
    return pd.read_csv("data/data_skrinning_stunnting(1).csv")

@st.cache_data
def load_geojson(path):
    return gpd.read_file("data/kecamatan_sidoarjo.geojson).__geo_interface__


# ==========================================
# PREPARASI GEOJSON + DATA CSV
# ==========================================
def prepare_geojson_and_stats(geojson, stats_df, csv_kec_col='kecamatan'):
    """
    Menyamakan nama kecamatan antara CSV & GeoJSON.
    Menambahkan feature['id'] agar choropleth mapbox bisa membaca polygon.
    """

    # --- Normalisasi nama kecamatan di GeoJSON ---
    for f in geojson['features']:
        # Ambil nama kecamatan dari properties (WADMKC biasanya untuk kecamatan)
        nama_asli = (
            f["properties"].get("WADMKC") or
            f["properties"].get("WADMKEC") or
            f["properties"].get("kecamatan") or ""
        )

        nama_norm = str(nama_asli).upper().strip()

        # Simpan nama normalisasi
        f["properties"]["KEC_NORM"] = nama_norm

        # Set feature ID → ini kunci penting untuk choropleth
        f["id"] = nama_norm

    # --- Normalisasi nama kecamatan di CSV ---
    stats_df[csv_kec_col + "_norm"] = (
        stats_df[csv_kec_col]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    # --- Filter data agar hanya kecamatan yang cocok dengan geojson ---
    geo_ids = {f["id"] for f in geojson["features"]}

    stats_df = stats_df[stats_df[csv_kec_col + "_norm"].isin(geo_ids)].copy()

    return geojson, stats_df


# ==========================================
# BIKIN PETA CHOROPLETH
# ==========================================
def create_choropleth_map(geojson, stats_df, kec_col='kecamatan'):
    """
    Membuat peta polygon choropleth berdasarkan kecamatan.
    """

    loc_col = kec_col + "_norm"    # kolom normalized untuk lokasi

    fig = px.choropleth_mapbox(
        stats_df,
        geojson=geojson,
        locations=loc_col,         # harus sama dengan feature['id']
        featureidkey="id",
        color="persentase_stunting",
        hover_name=kec_col,
        hover_data={
            loc_col: False,
            "total": True,
            "stunting": True,
            "persentase_stunting": ':.2f',
            "prediksi": True if "prediksi" in stats_df.columns else False
        },
        color_continuous_scale="Reds",
        mapbox_style="open-street-map",
        center={"lat": -7.45, "lon": 112.72},
        zoom=10.2,
        opacity=0.7
    )

    fig.update_traces(marker_line_width=1.2, marker_line_color="white")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=650)

    return fig


# ==========================================
# AGGREGASI DATA BY KECAMATAN
# ==========================================
def aggregate_by_kecamatan(df):
    df_grouped = df.groupby("kecamatan").agg(
        total=("nama_balita", "count"),
        stunting=("stunting", "sum")
    )
    df_grouped["persentase_stunting"] = (df_grouped["stunting"] / df_grouped["total"]) * 100
    df_grouped = df_grouped.reset_index()
    return df_grouped


# ==========================================
# STREAMLIT APP
# ==========================================
def main():
    st.title("🗺️ Peta Sebaran Stunting per Kecamatan — Sidoarjo")

    # Load data
    df = load_csv("data_skrinning_stunting.csv")
    geojson = load_geojson("kecamatan_sidoarjo.geojson")

    # Agregasi data
    stats_df = aggregate_by_kecamatan(df)

    # Sinkronisasi nama kecamatan
    geojson, stats_df_map = prepare_geojson_and_stats(geojson, stats_df, csv_kec_col="kecamatan")

    # DEBUG jika ada kecamatan yang tidak match
    geo_ids = {f["id"] for f in geojson["features"]}
    stats_ids = set(stats_df["kecamatan"].str.upper().str.strip())
    not_match = sorted(list(stats_ids - geo_ids))
    if not_match:
        st.warning(f"Kecamatan berikut TIDAK ada di geojson: {not_match}")

    # Bikin peta
    st.subheader("Choropleth Map — Kecamatan")
    map_fig = create_choropleth_map(geojson, stats_df_map, kec_col="kecamatan")
    st.plotly_chart(map_fig, use_container_width=True)


# ==========================================
# EXECUTE
# ==========================================
if __name__ == "__main__":
    main()
