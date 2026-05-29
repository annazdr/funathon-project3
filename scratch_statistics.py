# %%
import geopandas as gpd
import requests
import json

api_url = "https://funathon-2026-project3-api.lab.sspcloud.fr"

image_filepath = (
    "projet-funathon/"
    "2026/project3/data/images/MT001/2024/"
    "4731490_1429730_0_77.tif"
)
response_pred = requests.get(
    f"{api_url}/predict_image",
    params={
        "image": image_filepath,
        "polygons": True
    }
)
gdf_tile = gpd.GeoDataFrame.from_features(
    json.loads(response_pred.json())["features"],
    crs="EPSG:3035"
)

class_names = {
    1:  "Sealed",
    2:  "Woody - needle leaved",
    3:  "Woody - broadleaved deciduous",
    4:  "Woody - broadleaved evergreen",
    5:  "Low-growing woody plants",
    6:  "Permanent herbaceous",
    7:  "Periodically herbaceous",
    8:  "Lichens and mosses",
    9:  "Non- and sparsely-vegetated",
    10: "Water",
}

gdf_tile["area_m2"] = gdf_tile.geometry.area
gdf_tile["area_km2"] = gdf_tile["area_m2"] / 1e6
gdf_tile["class_name"] = gdf_tile["label"].map(class_names)

# %%
from great_tables import GT, style, loc

stats_tile = (
    gdf_tile.groupby(["label", "class_name"])
    .agg(
        n_polygons=("geometry", "count"),
        total_area_km2=("area_km2", "sum"),
        mean_polygon_area_m2=("area_m2", "mean"),
        max_polygon_area_m2=("area_m2", "max")
    )
    .reset_index()
    .sort_values("total_area_km2", ascending=False)
)

total_km2 = stats_tile["total_area_km2"].sum()
stats_tile["share_pct"] = (stats_tile["total_area_km2"] / total_km2 * 100).round(2)
(
    GT(stats_tile, rowname_col="class_name")
    .tab_header(title="Land-cover statistics — single tile (MT001, 2024)")
    .cols_label(
        label="label",
        n_polygons="N polygons",
        total_area_km2="Total area [km²]",
        mean_polygon_area_m2="Mean area [m²]",
        max_polygon_area_m2="Max area [m²]",
        share_pct="Share [%]"
    )
    .fmt_number(columns=["total_area_km2"], decimals=2)
    .fmt_number(columns=["mean_polygon_area_m2", "max_polygon_area_m2"], decimals=0)
    .fmt_number(columns=["share_pct"], decimals=1)
    .data_color(columns=["share_pct"], palette=["white", "steelblue"])
)

# %%
import pandas as pd

sealed_km2 = stats_tile.loc[stats_tile["label"] == 1, "total_area_km2"].sum()
forest_km2 = stats_tile.loc[stats_tile["label"].isin([2, 3, 4]), "total_area_km2"].sum()
agri_km2 = stats_tile.loc[stats_tile["label"].isin([6, 7]), "total_area_km2"].sum()
water_km2 = stats_tile.loc[stats_tile["label"] == 10, "total_area_km2"].sum()

summary_df = pd.DataFrame({
    "Group": ["Sealed (built-up)", "Forest", "Agricultural", "Water"],
    "area_km2": [sealed_km2, forest_km2, agri_km2, water_km2],
    "share_pct": [
        sealed_km2 / total_km2 * 100,
        forest_km2 / total_km2 * 100,
        agri_km2 / total_km2 * 100,
        water_km2 / total_km2 * 100,
    ]
})
(
    GT(summary_df, rowname_col="Group")
    .tab_header(title="Key land-cover groups - single tile (MT001, 2024)")
    .cols_label(area_km2="Area [km²]", share_pct="Share [%]")
    .fmt_number(columns=["area_km2"], decimals=2)
    .fmt_number(columns=["share_pct"], decimals=1)
    .data_color(columns=["share_pct"], palette=["white", "#FF0100"])
)

# %%
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 4))

stats_tile.set_index("class_name")["total_area_km2"].sort_values().plot(
    kind="barh", ax=ax, color="steelblue"
)
ax.set_xlabel("area [km2]")
ax.set_title('tytuł wykresu')
plt.tight_layout()
plt.show()

# %%
nuts_id = "MT001"
year = 2024

response_nuts = requests.get(
    f"{api_url}/predict_nuts",
    params={"nuts_id": nuts_id, "year": year},
)

gdf_nuts = gpd.GeoDataFrame.from_features(
    json.loads(response_nuts.json()["predictions"])["features"],
    crs="EPSG:3035",
)

gdf_nuts["area_m2"] = gdf_nuts.geometry.area
gdf_nuts["area_km2"] = gdf_nuts["area_m2"] / 1e6
gdf_nuts["class_name"] = gdf_nuts["label"].map(class_names)


stats_nuts = (
    gdf_nuts.groupby(["label", "class_name"])
    .agg(
        n_polygons=("geometry", "count"),
        total_area_km2=("area_km2", "sum"),
        mean_polygon_area_m2=("area_m2",  "mean"),
        max_polygon_area_m2=("area_m2",  "max"),
    )
    .reset_index()
    .sort_values("total_area_km2", ascending=False)
)

total_nuts_km2 = stats_nuts["total_area_km2"].sum()  # TODO: sum of total_area_km2
stats_nuts["share_pct"] = (stats_nuts["total_area_km2"] / total_nuts_km2 * 100).round(2)  # TODO: column

(
    GT(stats_nuts, rowname_col="class_name")
    .tab_header(title="Land-cover statistics — LU000 NUTS3 (2024)")
    .cols_label(
        label                = "Label",
        n_polygons           = "N polygons",
        total_area_km2       = "Total area (km²)",
        mean_polygon_area_m2 = "Mean area (m²)",
        max_polygon_area_m2  = "Max area (m²)",
        share_pct            = "Share (%)",
    )
    .fmt_number(columns=["total_area_km2"], decimals=2)
    .fmt_number(columns=["mean_polygon_area_m2", "max_polygon_area_m2"], decimals=0)
    .fmt_number(columns=["share_pct"], decimals=1)
    .data_color(columns=["share_pct"], palette=["white", "steelblue"])
)

tile_shares = stats_tile.set_index("class_name")["share_pct"].rename("tile_share_pct")  # TODO: column name
nuts_shares = stats_nuts.set_index("class_name")["share_pct"].rename("nuts3_share_pct")  # TODO: column name

comparison = pd.concat([tile_shares, nuts_shares], axis=1).fillna(0).reset_index()  # TODO: tile_shares, nuts_shares

(
    GT(comparison, rowname_col="class_name")
    .tab_header(title="Land-cover share — tile vs. NUTS3 (2024)")
    .cols_label(**{"tile_share_pct": "Tile (%)", "nuts3_share_pct": "NUTS3 (%)"})
    .fmt_number(decimals=1)
    .data_color(palette=["white", "steelblue"])
)
# %%
import folium
from folium.plugins import HeatMap

gdf_nuts_wgs84 = gdf_nuts.to_crs("EPSG:4326")
nuts_center    = gdf_nuts_wgs84.geometry.centroid.union_all().centroid

gdf_sealed = gdf_nuts_wgs84[gdf_nuts_wgs84["label"] == 1].copy()
gdf_sealed["centroid"] = gdf_sealed.geometry.centroid

heat_data = [
    [row.centroid.y, row.centroid.x, row.area_km2]
    for _, row in gdf_sealed.iterrows()
]

m = folium.Map(location=[nuts_center.y, nuts_center.x], zoom_start=10)

HeatMap(
    heat_data,
    radius=15,
    blur=20,
    max_zoom=13,
    gradient={0.4: "blue", 0.6: "yellow", 0.8: "orange", 1.0: "red"},
).add_to(m)

m
# %%
import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
from great_tables import GT, style, loc

image_filepath_2021 = (
    "projet-funathon/"
    "2026/project3/data/images/MT001/2021/"
    "4731490_1429730_0_77.tif"
)

response_2021 = requests.get(
    f"{api_url}/predict_image",
    params={"image": image_filepath_2021, "polygons": True},
)

gdf_tile_2021 = gpd.GeoDataFrame.from_features(
    json.loads(response_2021.json())["features"],
    crs="EPSG:3035",
)

gdf_tile_2021["area_m2"]    = gdf_tile_2021.geometry.area
gdf_tile_2021["area_km2"]   = gdf_tile_2021["area_m2"] / 1e6
gdf_tile_2021["class_name"] = gdf_tile_2021["label"].map(class_names)


def compute_stats(gdf):
    stats = (
        gdf.groupby(["label", "class_name"])
        .agg(
            n_polygons           = ("geometry", "count"),
            total_area_km2       = ("area_km2", "sum"),
            mean_polygon_area_m2 = ("area_m2",  "mean"),
            max_polygon_area_m2  = ("area_m2",  "max"),
        )
        .reset_index()
        .sort_values("total_area_km2", ascending=False)
    )
    total = stats["total_area_km2"].sum()
    stats["share_pct"] = (stats["total_area_km2"] / total * 100).round(2)
    return stats, total


stats_tile_2021, _ = compute_stats(gdf_tile_2021)
stats_tile_2024, _ = compute_stats(gdf_tile)

tile_2021 = stats_tile_2021.set_index("class_name")["share_pct"].rename("2021 (%)")
tile_2024 = stats_tile_2024.set_index("class_name")["share_pct"].rename("2024 (%)")

tile_comparison = pd.concat([tile_2021, tile_2024], axis=1).fillna(0)
tile_comparison["change (pp)"] = (tile_comparison["2024 (%)"] - tile_comparison["2021 (%)"]).round(2)

(
    GT(tile_comparison.reset_index(), rowname_col="class_name")
    .tab_header(title="Land-cover share — single tile, 2021 → 2024")
    .fmt_number(decimals=1)
    .data_color(
        columns=["change (pp)"],
        palette=["red", "white", "green"],
        domain=[-5, 5],
    )
    .data_color(columns=["2021 (%)", "2024 (%)"], palette=["white", "steelblue"])
)

fig, ax = plt.subplots(figsize=(9, 5))
x     = range(len(tile_comparison))
width = 0.35
ax.barh([i + width / 2 for i in x], tile_comparison["2021 (%)"], width, label="2021", color="steelblue")
ax.barh([i - width / 2 for i in x], tile_comparison["2024 (%)"], width, label="2024", color="darkorange")
ax.set_yticks(list(x))
ax.set_yticklabels(tile_comparison.index.tolist())
ax.set_xlabel("Share (%)")
ax.set_title("Land-cover share — single tile, 2021 vs 2024")
ax.legend()
plt.tight_layout()
plt.show()

# %%
response_nuts_2021 = requests.get(
    f"{api_url}/predict_nuts",
    params={"nuts_id": "MT001", "year": 2021},
)

gdf_nuts_2021 = gpd.GeoDataFrame.from_features(
    json.loads(response_nuts_2021.json()["predictions"])["features"],
    crs="EPSG:3035",
)

gdf_nuts_2021["area_m2"] = gdf_nuts_2021.geometry.area
gdf_nuts_2021["area_km2"] = gdf_nuts_2021["area_m2"] / 1e6
gdf_nuts_2021["class_name"] = gdf_nuts_2021["label"].map(class_names)

stats_nuts_2021, _ = compute_stats(gdf_nuts_2021)
stats_nuts_2024, _ = compute_stats(gdf_nuts)

nuts_2021 = stats_nuts_2021.set_index("class_name")["share_pct"].rename("2021 (%)")
nuts_2024 = stats_nuts_2024.set_index("class_name")["share_pct"].rename("2024 (%)")

nuts_comparison = pd.concat([nuts_2021, nuts_2024], axis=1).fillna(0)
nuts_comparison["change (pp)"] = (nuts_comparison["2024 (%)"] - nuts_comparison["2021 (%)"]).round(2)

(
    GT(nuts_comparison.reset_index(), rowname_col="class_name")
    .tab_header(title="Land-cover share — LU000 NUTS3, 2021 → 2024")
    .fmt_number(decimals=1)
    .data_color(
        columns=["change (pp)"],
        palette=["red", "white", "green"],
        domain=[-5, 5],
    )
    .data_color(columns=["2021 (%)", "2024 (%)"], palette=["white", "steelblue"])
)

rows = []
for label, category in [
    (1,         "Sealed"),
    ([2, 3, 4], "Forest"),
    ([6, 7],    "Agricultural"),
    (10,        "Water"),
]:
    labels_list = [label] if isinstance(label, int) else label
    km2_2021 = stats_nuts_2021.loc[stats_nuts_2021["label"].isin(labels_list), "total_area_km2"].sum()
    km2_2024 = stats_nuts_2024.loc[stats_nuts_2024["label"].isin(labels_list), "total_area_km2"].sum()
    rows.append({"Group": category, "2021 (km²)": round(km2_2021, 2),
                 "2024 (km²)": round(km2_2024, 2), "Δ (km²)": round(km2_2024 - km2_2021, 2)})

area_summary = pd.DataFrame(rows)

(
    GT(area_summary, rowname_col="Group")
    .tab_header(title="Absolute area change — LU000, 2021 → 2024")
    .fmt_number(decimals=2)
    .data_color(
        columns=["Δ (km²)"],
        palette=["red", "white", "green"],
        domain=[-10, 10],
    )
)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
x      = range(len(nuts_comparison))
width  = 0.35
labels = nuts_comparison.index.tolist()
axes[0].barh([i + width / 2 for i in x], nuts_comparison["2021 (%)"], width, label="2021", color="steelblue")
axes[0].barh([i - width / 2 for i in x], nuts_comparison["2024 (%)"], width, label="2024", color="darkorange")
axes[0].set_yticks(list(x))
axes[0].set_yticklabels(labels)
axes[0].set_xlabel("Share (%)")
axes[0].set_title("Land-cover share — MT001, 2021 vs 2024")
axes[0].legend()
colors = ["green" if v >= 0 else "red" for v in nuts_comparison["change (pp)"]]
axes[1].barh(labels, nuts_comparison["change (pp)"], color=colors)
axes[1].axvline(0, color="black", linewidth=0.8)
axes[1].set_xlabel("Change (percentage points)")
axes[1].set_title("Land-cover change 2021 → 2024 — LU000")
plt.tight_layout()
plt.show()

# %%
import folium
from folium.plugins import HeatMap

FOREST_LABELS = [2, 3, 4]

forest_2021 = (
    gdf_nuts_2021[gdf_nuts_2021["label"].isin(FOREST_LABELS)]
    .to_crs("EPSG:3035")
    .dissolve()
    .reset_index(drop=True)
)
forest_2024 = (
    gdf_nuts[gdf_nuts["label"].isin(FOREST_LABELS)]
    .to_crs("EPSG:3035")
    .dissolve()
    .reset_index(drop=True)
)

forest_lost = forest_2021.overlay(forest_2024, how="difference")
forest_gained = forest_2024.overlay(forest_2021, how="difference")

forest_lost["area_km2"] = forest_lost.geometry.area / 1e6
forest_gained["area_km2"] = forest_gained.geometry.area / 1e6

forest_lost = forest_lost[forest_lost["area_km2"] > 1e-6]
forest_gained = forest_gained[forest_gained["area_km2"] > 1e-6]

forest_lost_wgs84 = forest_lost.to_crs("EPSG:4326")
forest_gained_wgs84 = forest_gained.to_crs("EPSG:4326")

forest_lost_wgs84["centroid"] = forest_lost_wgs84.geometry.centroid
forest_gained_wgs84["centroid"] = forest_gained_wgs84.geometry.centroid

heat_lost = [
    [row.centroid.y, row.centroid.x, row.area_km2]
    for _, row in forest_lost_wgs84.iterrows()
]
heat_gained = [
    [row.centroid.y, row.centroid.x, row.area_km2]
    for _, row in forest_gained_wgs84.iterrows()
]

center = forest_lost_wgs84.geometry.centroid.union_all().centroid
m = folium.Map(location=[center.y, center.x], zoom_start=11)

HeatMap(
    heat_lost,
    radius=15,
    blur=20,
    max_zoom=13,
    gradient={0.4: "lightyellow", 0.65: "orange", 1.0: "red"},
    name="Forest loss 2021→2024",
).add_to(m)

HeatMap(
    heat_gained,
    radius=15,
    blur=20,
    max_zoom=13,
    gradient={0.4: "lightgreen", 0.65: "forestgreen", 1.0: "darkgreen"},
    name="Forest gain 2021→2024",
).add_to(m)

folium.LayerControl().add_to(m)

# %%
