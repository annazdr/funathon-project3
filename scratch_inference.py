# %%
import s3fs
import mlflow
import requests
import tempfile
import numpy as np
from pathlib import Path

minio_url = """https://minio.lab.sspcloud.fr/projet-funathon/mlflow-artifacts/
    1/88138b467a484c54b9935b66460413cd/artifacts/
"""
minio_url = "https://minio.lab.sspcloud.fr"
fs = s3fs.S3FileSystem(
    anon=True,
    endpoint_url=minio_url
)

s3_run_path = "projet-funathon/mlflow-artifacts/1/88138b467a484c54b9935b66460413cd/artifacts/"
s3_model_path = s3_run_path + "model"
local_model_dir = Path(tempfile.mktemp()) / "model"
fs.get(s3_model_path, str(local_model_dir), recursive=True)
model = mlflow.pyfunc.load_model(str(local_model_dir))
params_url = "https://minio.lab.sspcloud.fr/" + s3_run_path + "params.json"

response = requests.get(params_url)
run_params = response.json()
n_bands = int(run_params["n_bands"])
tiles_size = int(run_params["tiles_size"])
augment_size = int(run_params["augment_size"])
module_name = str(run_params["module_name"])
normalization_mean = run_params["normalization_mean"][:n_bands]
normalization_std = run_params["normalization_std"][:n_bands]

print(f"n_bands={n_bands}, tiles_size={tiles_size}, augment_size={augment_size}")
print(f"mean={normalization_mean}")
print(f"std={normalization_std}")

# %%
from src.inference.prediction import predict

image_target = "MT001/2024/4731490_1429730_0_77.tif"
image_path = (
    "https://minio.lab.sspcloud.fr/projet-funathon/"
    "2026/project3/data/images/"
    f"{image_target}"
)
satellite_img, predictions = predict(
    images=image_path,  # TODO: full image URL
    model=model,  # TODO: model loaded in Exercise 1
    tiles_size=tiles_size,  # TODO: tile size from model metadata
    augment_size=augment_size,  # TODO: augmentation size from model metadata
    n_bands=n_bands,  # TODO: number of bands
    normalization_mean=normalization_mean,  # TODO: normalisation mean
    normalization_std=normalization_std,  # TODO: normalisation std
    module_name=module_name,  # TODO: module name
)
print(f"Mask shape : {predictions.shape}")
print(f"Classes found : {set(predictions.flatten().tolist())}")

# %%
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

classes = [
    ("Sealed (1)",                        "#FF0100"),
    ("Woody – needle leaved trees (2)",   "#238B23"),
    ("Woody – broadleaved deciduous (3)", "#80FF00"),
    ("Woody – broadleaved evergreen (4)", "#00FF00"),
    ("Low-growing woody plants (5)",      "#804000"),
    ("Permanent herbaceous (6)",          "#CCF24E"),
    ("Periodically herbaceous (7)",       "#FEFF80"),
    ("Lichens and mosses (8)",            "#FF81FF"),
    ("Non- and sparsely-vegetated (9)",   "#BFBFBF"),
    ("Water (10)",                        "#0080FF"),
]
cmap = ListedColormap([color for _, color in classes])
label_to_color = {i + 1: color for i, (_, color) in enumerate(classes)}
legend_elements = [
    Patch(facecolor=color, edgecolor="black", label=label)
    for label, color in classes
]
# RGB composite — bands 4, 3, 2 → indices 3, 2, 1
satellite_img_array = satellite_img["array"]
rgb = np.transpose(
    satellite_img_array[[3, 2, 1]],  # TODO: band indices for R, G, B
    (1, 2, 0)
).astype(np.float32)
p98 = np.percentile(rgb, 98)
rgb = np.clip(rgb / p98, 0, 1)

fig, axes = plt.subplots(1, 2, figsize=(12, 6))

axes[0].imshow(rgb)                             # TODO: display the RGB composite
axes[0].set_title("Sentinel-2 RGB (B4, B3, B2)")
axes[0].axis("off")

axes[1].imshow(predictions, cmap=cmap, vmin=1, vmax=10)   # TODO: predictions array, colormap
axes[1].set_title("Predicted land cover")
axes[1].axis("off")

fig.legend(
    handles=legend_elements,
    loc="center left",
    bbox_to_anchor=(1.0, 0.5),
    frameon=True,
)
plt.tight_layout()
plt.show()

# %%
from src.inference.prediction import create_geojson_from_mask

gdf_pred = create_geojson_from_mask(satellite_img, predictions)
print(f"{len(gdf_pred)} polygons extracted")
print(gdf_pred.head())

fig, axes = plt.subplots(1, 3, figsize=(20, 6))

axes[0].imshow(rgb)                             # TODO: display the RGB composite
axes[0].set_title("Sentinel-2 RGB (B4, B3, B2)")
axes[0].axis("off")

axes[1].imshow(predictions, cmap=cmap, vmin=1, vmax=10)   # TODO: predictions array, colormap
axes[1].set_title("Predicted land cover")
axes[1].axis("off")

gdf_pred.plot(
    column="label",  # TODO: column to use for colouring (str)
    cmap=cmap,    # TODO: colormap
    vmin=1, vmax=10,
    ax=axes[2],
    legend=False,
)
# axes[2].imshow(gdf_pred)
axes[2].set_title("Predicted polygons")
axes[2].set_aspect("equal")
xmin, ymin, xmax, ymax = gdf_pred.total_bounds
axes[2].set_xlim(xmin, xmax)
axes[2].set_ylim(ymin, ymax)
axes[2].axis("off")

fig.legend(handles=legend_elements, loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=True)
plt.show()

# %%
import folium
from folium.raster_layers import ImageOverlay
from rasterio.warp import transform_bounds, reproject, Resampling, calculate_default_transform
from rasterio.crs import CRS

src_crs = satellite_img["crs"]
src_transform = satellite_img["transform"]
src_bounds = satellite_img["bounds"]
dst_crs = CRS.from_epsg(4326)

raw_bands = satellite_img["array"][[3, 2, 1]].astype(np. float32)
h, w = raw_bands.shape[1], raw_bands.shape[2]
dst_transform, dst_w, dst_h = calculate_default_transform(
    src_crs, dst_crs, w, h, *src_bounds
)
rgb_wgs84_bands = np.zeros((3, dst_h, dst_w), dtype=np.float32)
for i in range(3):
    reproject(
        source=raw_bands[i], destination=rgb_wgs84_bands[i],
        src_transform=src_transform, src_crs=src_crs,
        dst_transform=dst_transform, dst_crs=dst_crs,
        resampling=Resampling.bilinear,
    )
p98 = np.percentile(rgb_wgs84_bands[rgb_wgs84_bands > 0], 98)
rgb_wgs84 = np.clip(np.transpose(rgb_wgs84_bands, (1, 2, 0)) / p98, 0, 1)
alpha = (rgb_wgs84_bands.max(axis=0) > 0).astype(np.float32)
rgba_wgs84 = np.dstack([rgb_wgs84, alpha])

west, south, east, north = transform_bounds(src_crs, dst_crs, *src_bounds)
center_lat = (south + north) / 2
center_lon = (west + east) / 2

m = folium.Map(location=[center_lat, center_lon], zoom_start=14)

# layer1 - rgb image
fg_image = folium.FeatureGroup(name="rgb", show=True)
ImageOverlay(
    image=rgba_wgs84,                              # TODO: warped RGBA array (rgba_wgs84)
    bounds=[[south, west], [north, east]],
    opacity=0.7,
).add_to(fg_image)  # TODO: add to fg_image
fg_image.add_to(m)

# layer2 - predictions
fg_pred = folium.FeatureGroup(name="predictions, show=True")
gdf_pred_wgs84 = gdf_pred.to_crs("EPSG:4326")

folium.GeoJson(
    gdf_pred_wgs84,
    style_function=lambda feature: {
        "fillColor": label_to_color,  # TODO: use label_to_color to colour by label
        "color": "black",
        "weight": 0.5,
        "fillOpacity": 0.6,
    },
    tooltip=folium.GeoJsonTooltip(fields=["label"], aliases=["Class:"]),
).add_to(fg_pred)  # TODO: add to fg_pred
fg_pred.add_to(m)  # TODO: add fg_pred to map

# Layer control toggle widget
folium.LayerControl(collapsed=False).add_to(m)  # TODO: collapsed (bool)

m
# %%
import json
import requests

api_url = "https://funathon-2026-project3-api.lab.sspcloud.fr"
lat = 52.2319581
lon = 21.0067249

gps_point = [lat, lon]
year = 2023
response_find = requests.get(
    f"{api_url}/find_image",
    params={
        "gps_point": gps_point,
        "year": year
    }
)
response_find.raise_for_status()

image_filename = response_find.json()
print(f"Image found: {image_filename}")
# %%
import geopandas as gpd
nuts_id = "MT001"
year = 2024

response_nuts = requests.get(
    f"{api_url}/predict_nuts",
    params={
        "nuts_id": nuts_id,
        "year": year
    }
)
response_nuts.raise_for_status()

gdf_nuts = gpd.GeoDataFrame.from_features(
    json.loads(response_nuts.json()["predictions"])["features"],
    crs="EPSG:3035"
)

print(f"{len(gdf_nuts)} polygons received")
print(gdf_nuts.head())
# %%
import folium
import pandas as pd

gdf_nuts_wgs84 = gdf_nuts.to_crs("EPSG:4326")
nuts_center = gdf_nuts_wgs84.geometry.centroid.union_all().centroid
m_nuts = folium.Map(location=[nuts_center.y, nuts_center.x], zoom_start=10)

# layer1
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Ersi",
    name="Sat. Im.",
    show=True,
    overlay=True,
    control=True
).add_to(m_nuts)

# layer2
fg_pred = folium.FeatureGroup(name="Prediction", show=True)
folium.GeoJson(
    gdf_nuts_wgs84,
    style_function=lambda feature: {
        "fillColor": "label_to_color",
        "color": "black",
        "weight": 0.3,
        "fillOpacity": 0.6
    },
    tooltip=folium.GeoJsonTooltip(fields=["label"], aliases=["Class:"]),
).add_to(fg_pred)
fg_pred.add_to(m_nuts)

folium.LayerControl(collapsed=False).add_to(m_nuts)
m_nuts.save("map_nuts.html")
# %%
