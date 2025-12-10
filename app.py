import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Dashboard Stunting", layout="wide")

# ============================
# LOAD DATA
# ============================
@st.cache_data
def load_data():
    df = pd.read_csv("data_skrinning_stunting(1).csv")

    # Normalisasi nama kecamatan
    df["nama_kecamatan"] = (
        df["nama_kecamatan"]
        .str.upper()
        .str.strip()
    )

    with open("kecamatan_sidoarjo.geojson", "r", encoding="utf-8") as f:
        geojson = json.load(f)

    # Normalisasi GeoJSON
    for ftr in geojson["features"]:
        ftr["properties"]["WADMKC"] = (
            ftr["properties"]["WADMKC"]
            .upper()
            .strip()
        )

    return df, geojson


# ============================
# AGGREGATE STATS
# ============================
def aggregate(df):
    stats = df.groupby("nama_kecamatan").agg(
        total=("nama_kecamatan", "count"),
        stunting=("stunting_balita", lambda x: (x == "Ya").sum())
    ).reset_index()

    stats["persentase_stunting"] = (
        stats["stunting"] / stats["total"] * 100
    ).round(2)

    return stats


# ============================
# FIXED CHOROPLETH (MENYEBAR)
# ============================
def make_map(geojson, stats):

    # Merge ke geojson
    for f in geojson["features"]:
        name = f["properties"]["WADMKC"]
        row = stats[stats["nama_kecamatan"] == name]

        if not row.empty:
            f["properties"]["persen"] = float(row["persentase_stunting"].values[0])
            f["properties"]["total"] = int(row["total"].values[0])
            f["properties"]["stunting"] = int(row["stunting"].values[0])
        else:
            f["properties"]["persen"] = 0
            f["properties"]["total"] = 0
            f["properties"]["stunting"] = 0

    # Gunakan GEOJSON sebagai data utama
    fig = px.choropleth_mapbox(
        geojson=geojson,
        locations=[f["properties"]["WADMKC"] for f in geojson["features"]],
        featureidkey="properties.WADMKC",
        color=[f["properties"]["persen"] for f in geojson["features"]],
        hover_name=[f["properties"]["WADMKC"] for f in geojson["features"]],
        hover_data={
            "Total Balita": [f["properties"]["total"] for f in geojson["features"]],
            "Kasus Stunting": [f["properties"]["stunting"] for f in geojson["features"]],
            "Persentase (%)": [f["properties"]["persen"] for f in geojson["features"]]
        },
        color_continuous_scale="RdYlGn_r",
        mapbox_style="carto-positron",
        center={"lat": -7.45, "lon": 112.72},
        zoom=10.3,
        opacity=0.8,
    )

    fig.update_traces(marker_line_width=1.5, marker_line_color="white")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=600)

    return fig


# ============================
# STREAMLIT PAGE
# ============================
df, geojson = load_data()
stats = aggregate(df)

st.title("📊 Dashboard Stunting Kabupaten Sidoarjo")

tab1, tab2 = st.tabs(["🗺️ Peta Stunting", "📊 Tabel Statistik"])

with tab1:
    st.subheader("Peta Sebaran Stunting (Sudah Menyebar)")

    fig = make_map(geojson, stats)
    st.plotly_chart(fig, use_container_width=True)

    st.info("Peta di atas sudah mengikuti bentuk polygon kecamatan dari GeoJSON.")

with tab2:
    st.subheader("Data Per Kecamatan")
    st.dataframe(stats.sort_values("persentase_stunting", ascending=False), use_container_width=True)


st.markdown("---")
st.caption(f"Update terakhir: {datetime.now().strftime('%d %B %Y')}")
