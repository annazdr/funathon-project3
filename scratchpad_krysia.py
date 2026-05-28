# %%
import rasterio
print("OK")
# %%
import os
import urllib.request
import rasterio
import numpy as np

tile_url = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/"
    "2024/4042000_2951690_0_637.tif"
)

with rasterio.open(tile_url) as src:
    tile_crs = src.crs
    tile_bounds = src.bounds
    tile_count = src.count
    tile_height = src.height
    tile_width = src.width
    # Read RGB bands: B4 (Red), B3 (Green), B2 (Blue)
    rgb_data = src.read([4, 3, 2])

print(f"CRS:    {tile_crs}")
print(f"Bounds: {tile_bounds}")
print(f"Shape:  {tile_count} bands x {tile_height} x {tile_width} px")
# %%
#

import matplotlib.pyplot as plt

# Transpose to (H, W, 3) and normalize for display
rgb = np.transpose(rgb_data, (1, 2, 0)).astype(np.float32)
p98 = np.percentile(rgb, 98)
rgb = np.clip(rgb / p98, 0, 1)

fig, ax = plt.subplots(figsize=(5, 5))
ax.imshow(rgb)
ax.set_title("Sentinel-2 RGB composite (B4, B3, B2) — LU000")
ax.axis("off")
plt.tight_layout()
plt.show()

# %%
import rasterio
import numpy as np
import matplotlib.pyplot as plt

tile_url = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/"
    "2024/4042000_2951690_0_637.tif"
)

with rasterio.open(tile_url) as src:
    rgb_data = src.read([4, 3, 2])
    tile_crs = src.crs
    tile_bounds = src.bounds

rgb = np.transpose(rgb_data, (1, 2, 0)).astype(np.float32)
p98 = np.percentile(rgb, 98)
rgb = np.clip(rgb / p98, 0, 1)

fig, ax = plt.subplots(figsize=(5, 5))
ax.imshow(rgb)
ax.set_title("Sentinel-2 RGB composite")
ax.axis("off")
plt.tight_layout()
plt.show()
# %%
import rasterio
import numpy as np
import matplotlib.pyplot as plt

tile_url = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/"
    "2024/4042000_2951690_0_637.tif"
)

with rasterio.open(tile_url) as src:
    print(src.profile)
    fc_data = src.read([8, 4, 3])

fc = np.transpose(fc_data, (1, 2, 0)).astype(np.float32)
p98 = np.percentile(fc, 98)
fc = np.clip(fc / p98, 0, 1)

fig, axes = plt.subplots(1, 2, figsize=(10, 5))
axes[0].imshow(rgb)
axes[0].set_title("True colour (B4, B3, B2)")
axes[0].axis("off")
axes[1].imshow(fc)
axes[1].set_title("False colour (B8, B4, B3)")
axes[1].axis("off")
plt.tight_layout()
plt.show()
# %%
import rasterio
import numpy as np
import matplotlib.pyplot as plt

tile_url = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/"
    "2024/4042000_2951690_0_637.tif"
)

with rasterio.open(tile_url) as src:
    # Healthy vegetation strongly reflects near-infrared (B8) and absorbs red (B4),
    # so the ratio (NIR − Red) / (NIR + Red) gives a clean vegetation signal.
    nir = src.read(8).astype(np.float32)
    red = src.read(4).astype(np.float32)

# np.where guards against pixels where NIR + Red is exactly 0 (water bodies,
# nodata, deep shadow): the ratio would otherwise produce NaN and contaminate the
# colormap. Substituting 0 keeps those pixels neutral on the red-yellow-green scale.
ndvi = np.where(nir + red == 0, 0, (nir - red) / (nir + red))

fig, ax = plt.subplots(figsize=(6, 5))
# vmin=-1, vmax=1 anchors the colormap to NDVI's full theoretical range, so the
# same colour means the same vegetation cover across tiles.
im = ax.imshow(ndvi, cmap="RdYlGn", vmin=-1, vmax=1)
ax.set_title("NDVI — LU000 (2024)")
ax.axis("off")
fig.colorbar(im, ax=ax, shrink=0.8, label="NDVI")
plt.tight_layout()
plt.show()
# %%
import requests
import geopandas as gpd
from shapely.geometry import Point

# Step 1: Geocode the city name
response = requests.get(
    "https://nominatim.openstreetmap.org/search",
    params={"q": "5, rue Alphonse Weicker  Luxembourg", "format": "json", "limit": 1},
    headers={"User-Agent": "funathon-project3"},
)
result = response.json()[0]
lon, lat = float(result["lon"]), float(result["lat"])
print(f"Eurostat coordinates: lon={lon}, lat={lat}")

# Step 2: Create a GeoDataFrame with the point in WGS84, then reproject
city_point = gpd.GeoDataFrame(
    {"city": ["Luxembourg"]}, geometry=[Point(lon, lat)], crs="EPSG:4326"
)
city_point = city_point.to_crs("EPSG:3035")

# Step 3: Load NUTS3 boundaries and spatial join
nuts_url = (
    "https://gisco-services.ec.europa.eu/distribution/v2/"
    "nuts/geojson/NUTS_RG_01M_2021_3035_LEVL_3.geojson"
)
nuts = gpd.read_file(nuts_url)
city_nuts = gpd.sjoin(city_point, nuts, predicate="within")
nuts_code = city_nuts.iloc[0]["NUTS_ID"]
print(f"NUTS3 region: {nuts_code}")  # → LU000
# %%
#| eval: false

base_url = f"s3://projet-funathon/2026/project3/data/images/{nuts_code}"
print(base_url)



# %%
# Step 1: Geocode
response = requests.get(
    "https://nominatim.openstreetmap.org/search",
    params={"q": "Warsaw", "format": "json", "limit": 1},  # TODO: city name
    headers={"User-Agent": "funathon-project3"},
)
result = response.json()[0]
lon, lat = float(result["lon"]), float(result["lat"])

# %%
print(lon, lat)
# %%
city_point = gpd.GeoDataFrame(
    {"city": ["Warsaw"]},
    geometry=[Point(lon, lat)],
    crs="EPSG:4326",  # TODO
)
city_point = city_point.to_crs("EPSG:3035")  # TODO: target CRS
print(city_point)
# %%
nuts_url = (
    "https://gisco-services.ec.europa.eu/distribution/v2/"
    "nuts/geojson/NUTS_RG_01M_2021_3035_LEVL_3.geojson"
)
nuts = gpd.read_file(nuts_url)
city_nuts = gpd.sjoin(city_point, nuts, predicate="within")
nuts_code = city_nuts.iloc[0]["NUTS_ID"]
# %%
print(nuts_code)
# %%
available = [
    "AT130",
    "BE100",
    "BG411",
    "CZ010",
    "DE300",
    "DEA23",
    "EE001",
    "EL303",
    "ES300",
    "FI1B1",
    "FR101",
    "FRJ27",
    "LU000",
    "HRO41",
    "HU110",
    "ITI43",
    "LT011",
    "LV006",
    "MT001",
    "NL329",
    "PL127",
    "PT170",
    "RO321",
    "SE110",
    "SI041",
    "SK010",
]
print(f"NUTS3 code: {nuts_code}, available: {nuts_code in available}")





# %%
import pandas as pd
import rasterio
import numpy as np
import matplotlib.pyplot as plt

# Build the URL to the parquet index
year = 2024
nuts_code = "LU000"
parquet_url = (
    f"https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    f"project3/data/images/{nuts_code}/{year}/filename2bbox.parquet"
)

# Read the tile index
tiles = pd.read_parquet(parquet_url)
print(f"{len(tiles)} tiles in {nuts_code}/{year}")

# Get city coordinates in EPSG:3035
x = city_point.geometry.iloc[0].x
y = city_point.geometry.iloc[0].y
print(f"City point (EPSG:3035): x={x:.0f}, y={y:.0f}")

# Find the tile whose bbox contains the city point
tile_filename = None
for _, row in tiles.iterrows():
    xmin, ymin, xmax, ymax = row["bbox"]
    if xmin <= x <= xmax and ymin <= y <= ymax:
        tile_filename = row["filename"]
        break

print(f"Matching tile: {tile_filename}")

# Build the full HTTPS URL
tile_url = (
    f"https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    f"project3/data/images/{nuts_code}/{year}/{tile_filename}"
)

# Open the tile and display the RGB composite
with rasterio.open(tile_url) as src:
    rgb_data = src.read([4, 3, 2])  # Red, Green, Blue bands
    tile_crs = src.crs
    tile_bounds = src.bounds

rgb = np.transpose(rgb_data, (1, 2, 0)).astype(np.float32)
rgb = np.clip(rgb / np.percentile(rgb, 98), 0, 1)

fig, ax = plt.subplots(figsize=(5, 5))
ax.imshow(rgb)
ax.set_title(f"Sentinel-2 — {tile_filename}")
ax.axis("off")
plt.tight_layout()
plt.show()



# %%
import requests
import geopandas as gpd
from shapely.geometry import Point

# Step 1: Geocode Brussels
response = requests.get(
    "https://nominatim.openstreetmap.org/search",
    params={"q": "Brussels, Belgium", "format": "json", "limit": 1},
    headers={"User-Agent": "funathon-project3"},
)
result = response.json()[0]
lon, lat = float(result["lon"]), float(result["lat"])
print(f"Brussels coordinates: lon={lon}, lat={lat}")

# Step 2: Create GeoDataFrame and reproject
city_point = gpd.GeoDataFrame(
    {"city": ["Brussels"]}, geometry=[Point(lon, lat)], crs="EPSG:4326"
)
city_point = city_point.to_crs("EPSG:3035")

# Step 3: Load NUTS3 boundaries and spatial join
nuts_url = (
    "https://gisco-services.ec.europa.eu/distribution/v2/"
    "nuts/geojson/NUTS_RG_01M_2021_3035_LEVL_3.geojson"
)
nuts = gpd.read_file(nuts_url)
city_nuts = gpd.sjoin(city_point, nuts, predicate="within")
nuts_code = city_nuts.iloc[0]["NUTS_ID"]
print(f"NUTS3 region: {nuts_code}")  # → BE100

# Step 4: Check availability
available = [
    "AT130",
    "BE100",
    "BG411",
    "CZ010",
    "DE300",
    "DEA23",
    "DK011",
    "EE001",
    "EL303",
    "ES300",
    "FI1B1",
    "FR101",
    "FRJ27",
    "HRO41",
    "HU110",
    "ITI43",
    "LT011",
    "LU000",
    "LV006",
    "MT001",
    "NL329",
    "PL127",
    "PT170",
    "RO321",
    "SE110",
    "SI041",
    "SK010",
]
print(f"Available: {nuts_code in available}")  # → True

# Step 5: Build S3 URL
base_url = f"s3://projet-funathon/2026/project3/data/images/{nuts_code}"  # TODO
print(base_url)


# %%
import pandas as pd
import rasterio
import numpy as np
import matplotlib.pyplot as plt

# Build the URL to the parquet index
year = 2024
nuts_code = "BE100"
parquet_url = (
    f"https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    f"project3/data/images/{nuts_code}/{year}/filename2bbox.parquet"
)

# Read the tile index
tiles = pd.read_parquet(parquet_url)
print(f"{len(tiles)} tiles in {nuts_code}/{year}")

# Get city coordinates in EPSG:3035
x = city_point.geometry.iloc[0].x
y = city_point.geometry.iloc[0].y
print(f"City point (EPSG:3035): x={x:.0f}, y={y:.0f}")

# Find the tile whose bbox contains the city point
tile_filename = None
for _, row in tiles.iterrows():
    xmin, ymin, xmax, ymax = row["bbox"]
    if xmin <= x <= xmax and ymin <= y <= ymax:
        tile_filename = row["filename"]
        break

print(f"Matching tile: {tile_filename}")

# Build the full HTTPS URL
tile_url = (
    f"https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    f"project3/data/images/{nuts_code}/{year}/{tile_filename}"
)

# Open the tile and display the RGB composite
with rasterio.open(tile_url) as src:
    rgb_data = src.read([4, 3, 2])  # Red, Green, Blue bands
    tile_crs = src.crs
    tile_bounds = src.bounds

rgb = np.transpose(rgb_data, (1, 2, 0)).astype(np.float32)
rgb = np.clip(rgb / np.percentile(rgb, 98), 0, 1)

fig, ax = plt.subplots(figsize=(5, 5))
ax.imshow(rgb)
ax.set_title(f"Sentinel-2 — {tile_filename}")
ax.axis("off")
plt.tight_layout()
plt.show()

# %%
import geopandas as gpd
from shapely.geometry import box

# Create a GeoDataFrame with the tile extent in EPSG:3035
tile_geom = box(*tile_bounds)
gdf = gpd.GeoDataFrame({"tile": ["LU000"]}, geometry=[tile_geom], crs="EPSG:3035")

print("EPSG:3035 bounds:")
print(gdf.total_bounds)

# Convert to WGS84 (latitude/longitude)
gdf_wgs84 = gdf.to_crs("EPSG:4326")
print("\nEPSG:4326 bounds:")
print(gdf_wgs84.total_bounds)
tile_gdf = gpd.GeoDataFrame(
    {"tile": ["LU000"], "year": [2024]},
    geometry=[box(*tile_bounds)],
    crs=tile_crs,
)
tile_gdf
# %%
fig, ax = plt.subplots(figsize=(6, 6))
extent = [tile_bounds.left, tile_bounds.right, tile_bounds.bottom, tile_bounds.top]
ax.imshow(rgb, extent=extent)
tile_gdf.boundary.plot(ax=ax, color="red", linewidth=2)
ax.set_xlabel("Easting (m)")
ax.set_ylabel("Northing (m)")
ax.set_title("Sentinel-2 tile with boundary overlay (EPSG:3035)")
plt.tight_layout()
plt.show()



# %%
import geopandas as gpd
from shapely.geometry import box

tile_geom = box(*tile_bounds)
gdf = gpd.GeoDataFrame({"tile": ["LU000"]}, geometry=[tile_geom], crs="EPSG:3035")
gdf_wgs84 = gdf.to_crs("EPSG:4326")

print("EPSG:3035 bounds:", gdf.total_bounds)
print("EPSG:4326 bounds:", gdf_wgs84.total_bounds)


# %%
import geopandas as gpd
from shapely.geometry import box

nuts_url = (
    "https://gisco-services.ec.europa.eu/distribution/v2/"
    "nuts/geojson/NUTS_RG_01M_2021_3035_LEVL_3.geojson"
)
nuts = gpd.read_file(nuts_url)

tile_geom = box(*tile_bounds)
tile_gdf = gpd.GeoDataFrame(
    {"tile": ["LU000"]}, geometry=[tile_geom], crs=tile_crs
)

# Spatial join: for each tile geometry, attach the columns of every NUTS3 region
# whose geometry satisfies the predicate. `predicate="intersects"` keeps any region
# that touches the tile (even partially); alternatives are "within" (tile fully
# inside region) or "contains" (region fully inside tile). A tile straddling a
# border can therefore match several NUTS3 regions — hence the loop below.
joined = gpd.sjoin(tile_gdf, nuts, predicate="intersects")

for _, row in joined.iterrows():
    print(f"NUTS_ID: {row['NUTS_ID']}, NUTS_NAME: {row['NUTS_NAME']}")

# tile_geom is in EPSG:3035 whose unit is the metre, so .area is in m². Divide by
# 1e6 to get km². Computing area on a geographic CRS like EPSG:4326 (degrees) would
# give a meaningless figure — always use a metric projection for measurements.
area_km2 = tile_geom.area / 1e6
print(f"Tile area: {area_km2:.2f} km²")


# %%
from rasterio.warp import transform_bounds

west, south, east, north = transform_bounds(
    tile_crs, "EPSG:4326", *tile_bounds
)

print(f"WGS84 extent: W={west:.4f}, S={south:.4f}, E={east:.4f}, N={north:.4f}")

fig, ax = plt.subplots(figsize=(6, 6))
ax.imshow(rgb, extent=[west, east, south, north])
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title("Sentinel-2 tile in WGS84 coordinates")
plt.tight_layout()
plt.show()


# %%
import folium
from folium.raster_layers import ImageOverlay

center_lat = (south + north) / 2
center_lon = (west + east) / 2

m = folium.Map(location=[center_lat, center_lon], zoom_start=14)

ImageOverlay(
    image=rgb,
    bounds=[[south, west], [north, east]],
    opacity=0.7,
).add_to(m)

m
# %%
import urllib.request
import io
import numpy as np

# Label URL for a LU000 patch, year 2021
label_url = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/labels/LU000/"
    "2021/4042000_2951690_0_637.npy"
)

with urllib.request.urlopen(label_url) as response:
    label_array = np.load(io.BytesIO(response.read()))

print(f"Label shape: {label_array.shape}")
print(f"Data type:   {label_array.dtype}")
print(f"Classes:     {np.unique(label_array)}")


# %%
import rasterio
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

# CLC+ class names and colours
classes = [
    ("Sealed (1)", "#FF0100"),
    ("Woody -- needle leaved trees (2)", "#238B23"),
    ("Woody -- Broadleaved deciduous trees (3)", "#80FF00"),
    ("Woody -- Broadleaved evergreen trees (4)", "#00FF00"),
    ("Low-growing woody plants (bushes, shrubs) (5)", "#804000"),
    ("Permanent herbaceous (6)", "#CCF24E"),
    ("Periodically herbaceous (7)", "#FEFF80"),
    ("Lichens and mosses (8)", "#FF81FF"),
    ("Non- and sparsely-vegetated (9)", "#BFBFBF"),
    ("Water (10)", "#0080FF"),
]
cmap = ListedColormap([color for _, color in classes])

# Load the matching satellite image
image_url = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/"
    "2021/4042000_2951690_0_637.tif"
)
with rasterio.open(image_url) as src:
    rgb_data = src.read([4, 3, 2])

rgb = np.transpose(rgb_data, (1, 2, 0)).astype(np.float32)
rgb = np.clip(rgb / np.percentile(rgb, 98), 0, 1)

# Side-by-side plot
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].imshow(rgb)
axes[0].set_title("Sentinel-2 RGB")
axes[0].axis("off")

axes[1].imshow(label_array, cmap=cmap, vmin=1, vmax=10)
axes[1].set_title("CLC+ Backbone label")
axes[1].axis("off")

legend_elements = [
    Patch(facecolor=color, edgecolor="black", label=label)
    for label, color in classes
]
fig.legend(
    handles=legend_elements,
    loc="center right",
    bbox_to_anchor=(1.30, 0.5),
    frameon=True,
)
plt.tight_layout()
plt.show()

# %%
import urllib.request
import io
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

nuts_code = "LU000"
year = 2021
patch_id = "4042000_2951690_0_637"

label_url = f"https://minio.lab.sspcloud.fr/projet-funathon/2026/project3/data/labels/{nuts_code}/{year}/{patch_id}.npy"

with urllib.request.urlopen(label_url) as response:
    my_label = np.load(io.BytesIO(response.read()))

print(f"Shape: {my_label.shape}")
print(f"Classes: {np.unique(my_label)}")

cmap = ListedColormap(
    [
        "#FF0100",
        "#238B23",
        "#80FF00",
        "#00FF00",
        "#804000",
        "#CCF24E",
        "#FEFF80",
        "#FF81FF",
        "#BFBFBF",
        "#0080FF",
    ]
)

fig, ax = plt.subplots(figsize=(5, 5))
ax.imshow(my_label, cmap=cmap, vmin=1, vmax=10)
ax.set_title(f"CLC+ label — {nuts_code}/{year}/{patch_id}")
ax.axis("off")
plt.show()


# %%
import numpy as np
import urllib.request
import io
import rasterio
import folium
from rasterio.warp import transform_bounds
from matplotlib.colors import to_rgba

classes = [
    ("Sealed (1)", "#FF0100"),
    ("Woody -- needle leaved trees (2)", "#238B23"),
    ("Woody -- Broadleaved deciduous trees (3)", "#80FF00"),
    ("Woody -- Broadleaved evergreen trees (4)", "#00FF00"),
    ("Low-growing woody plants (bushes, shrubs) (5)", "#804000"),
    ("Permanent herbaceous (6)", "#CCF24E"),
    ("Periodically herbaceous (7)", "#FEFF80"),
    ("Lichens and mosses (8)", "#FF81FF"),
    ("Non- and sparsely-vegetated (9)", "#BFBFBF"),
    ("Water (10)", "#0080FF"),
]

# Step 1: Load satellite image
image_url = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/images/LU000/"
    "2021/4017000_2974190_0_402.tif"
)
with rasterio.open(image_url) as src:
    rgb_data = src.read([4, 3, 2])
    bounds_3035 = src.bounds
    crs = src.crs

rgb_overlay = np.transpose(rgb_data, (1, 2, 0)).astype(np.float32)
rgb_overlay = np.clip(rgb_overlay / np.percentile(rgb_overlay, 98), 0, 1)

# Step 2: Load the matching label
label_url = (
    "https://minio.lab.sspcloud.fr/projet-funathon/2026/"
    "project3/data/labels/LU000/"
    "2021/4017000_2974190_0_402.npy"
)
with urllib.request.urlopen(label_url) as response:
    label = np.load(io.BytesIO(response.read()))

# Step 3: Convert label to RGBA
color_lut = np.zeros((11, 4), dtype=np.float32)
color_lut[0] = [0, 0, 0, 0]
for i, (_, hex_color) in enumerate(classes, start=1):
    color_lut[i] = list(to_rgba(hex_color, alpha=0.7))

label_rgba = color_lut[label]

# Step 4: Reproject bounds to WGS84
west, south, east, north = transform_bounds(crs, "EPSG:4326", *bounds_3035)

center_lat = (south + north) / 2
center_lon = (west + east) / 2

# Step 5: Create the map
m = folium.Map(location=[center_lat, center_lon], zoom_start=15)

# Step 6: Add overlays
folium.raster_layers.ImageOverlay(
    image=rgb_overlay,
    bounds=[[south, west], [north, east]],
    name="Sentinel-2 RGB",
).add_to(m)

folium.raster_layers.ImageOverlay(
    image=label_rgba,
    bounds=[[south, west], [north, east]],
    name="CLC+ Label",
    opacity=0.8,
).add_to(m)

# Step 7: Layer control
folium.LayerControl().add_to(m)

m
# %%
from src.models.model import SegformerB5

# This downloads ~330 MB of weights from HuggingFace on first run
model = SegformerB5(
    # 14 matches the layout of the pre-baked GeoTIFFs: the 12 L2A spectral bands
    # (B10 is dropped by atmospheric correction) plus NDVI and NDWI as derived
    # channels. `src/download_region.py` produces the same layout. If you swap in
    # a different dataset (different band count or different derived layers), this
    # number, the normalisation statistics, and `num_channels` in the SegformerConfig
    # must all change together — otherwise the first patch-embedding layer
    # mis-shapes inputs.
    n_bands=14,
    logits=True,             # return raw logits (not probabilities)
    freeze_encoder=False,    # keep encoder trainable
)
# %%
print(model)

# %%
def count_params(module):
    total = sum(p.numel() for p in module.parameters())
    trainable = sum(p.numel() for p in module.parameters() if p.requires_grad)
    return total, trainable

total, trainable = count_params(model)
enc_total, enc_trainable = count_params(model.segformer)
dec_total, dec_trainable = count_params(model.decode_head)

print(f"{'Component':<20} {'Total params':>15} {'Trainable params':>18}")
print("-" * 55)
print(f"{'Encoder (MiT-B5)':<20} {enc_total:>15,} {enc_trainable:>18,}")
print(f"{'Decoder (MLP)':<20} {dec_total:>15,} {dec_trainable:>18,}")
print(f"{'Full model':<20} {total:>15,} {trainable:>18,}")
# %%
# Freeze all encoder parameters
model.freeze()

total, trainable = count_params(model)
print(f"After freezing encoder — trainable: {trainable:,} / {total:,}")

# Unfreeze for full fine-tuning
model.unfreeze()
total, trainable = count_params(model)
print(f"After unfreezing — trainable: {trainable:,} / {total:,}")
# %%
# 1. Parameters per encoder stage.
# Deeper stages have more channels (C₁ < C₂ < C₃ < C₄), so even with fewer transformer
# blocks they end up holding most of the encoder's capacity. This matters during
# fine-tuning: freezing stages 3–4 alone already locks the bulk of the model's weights.
for i, stage in enumerate(model.segformer.encoder.block):
    n = sum(p.numel() for p in stage.parameters())
    print(f"Stage {i+1}: {n:,} parameters")

# 2. Decoder breakdown.
# The four projection layers are tiny linear maps (one per encoder stage); the real
# decoder cost lives in the linear_fuse + classifier. Seeing how light the head is
# explains why training the decoder alone is fast and resistant to overfitting.
for i, proj in enumerate(model.decode_head.linear_c):
    n = sum(p.numel() for p in proj.parameters())
    print(f"Decoder projection {i+1}: {n:,} parameters")

clf_params = sum(p.numel() for p in model.decode_head.classifier.parameters())
dec_total = sum(p.numel() for p in model.decode_head.parameters())
print(f"Classifier: {clf_params:,} / {dec_total:,} decoder params "
      f"({100*clf_params/dec_total:.1f}%)")
# %%
import torch

B, C, H, W = 2, 14, 512, 512   # batch size, channels, height, width
dummy_input = torch.randn(B, C, H, W)
dummy_labels = torch.randint(0, model.config.num_labels, (B, H, W))

print(f"Input  shape: {tuple(dummy_input.shape)}")
print(f"Labels shape: {tuple(dummy_labels.shape)}")
# %%
model.eval()
with torch.no_grad():
    # Without labels → raw logits at H/4 × W/4
    logits = model(dummy_input)
    print(f"Logits shape (no labels):   {tuple(logits.shape)}")
    # Expected: (2, num_classes, 128, 128)  — quarter resolution

    # With labels → logits upsampled to label resolution
    upsampled = model(dummy_input, dummy_labels)
    print(f"Logits shape (with labels): {tuple(upsampled.shape)}")
    # Expected: (2, num_classes, 512, 512)
# %%
outputs = model.segformer(
    dummy_input,
    output_hidden_states=True,
    return_dict=True,
)

for i, hs in enumerate(outputs.hidden_states):
    print(f"Stage {i+1} hidden state: {tuple(hs.shape)}")
# %%
import torch.nn.functional as F

model.eval()
with torch.no_grad():
    # Logits = raw, unbounded per-class scores. They have shape (B, num_classes, H/4, W/4)
    # because the all-MLP decoder fuses everything at the finest encoder scale (H/4).
    logits = model(dummy_input)
    # output_hidden_states=True surfaces the four encoder feature maps. The decoder
    # combines all four — early stages (high resolution) carry local detail, late
    # stages (low resolution) carry semantic context. Returning them is what makes
    # multi-scale fusion possible.
    outputs = model.segformer(
        dummy_input, output_hidden_states=True, return_dict=True
    )

# 1. Manual upsampling.
# Bilinear (not nearest-neighbour) because logits are continuous scores: interpolating
# between two scores is meaningful, whereas a discrete class label is not.
logits_full = F.interpolate(
    logits,
    size=(H, W),
    mode="bilinear",
    align_corners=False,
)
print(f"Manually upsampled: {tuple(logits_full.shape)}")

# 2. Predicted class map.
# softmax converts logits → probabilities; argmax picks the most likely class at each
# pixel. The class axis disappears: (B, num_classes, H, W) → (B, H, W), one int per pixel.
probs = torch.softmax(logits_full, dim=1)
pred  = torch.argmax(probs, dim=1)
print(f"Predicted map shape: {tuple(pred.shape)}")
print(f"Unique predicted classes: {pred.unique().tolist()}")

# 3. Spatial area ratios — stage 1 is at H/4 × W/4 → 1/16 of the input area, and each
# next stage divides that by 4 again (1/64, 1/256, 1/1024).
for i, hs in enumerate(outputs.hidden_states):
    ratio = (hs.shape[-2] * hs.shape[-1]) / (H * W)
    print(f"Stage {i+1}: {ratio:.4f}")

    # %%
    from src.models.module import SegmentationModule
from torch import nn, optim

module = SegmentationModule(
    model=model,
    loss=nn.CrossEntropyLoss(ignore_index=255),
    optimizer=optim.AdamW,
    optimizer_params={"lr": 1e-3, "weight_decay": 1e-2},
    scheduler=optim.lr_scheduler.OneCycleLR,
    scheduler_params={},
    scheduler_interval="step",
)
# %%
from src.training.metrics import IOU, positive_rate

# Simulate model output and labels
B, num_classes, H, W = 2, 11, 512, 512
dummy_logits = torch.randn(B, num_classes, H, W)
dummy_labels = torch.randint(0, num_classes, (B, H, W))

iou_mean, iou_building = IOU(dummy_logits, dummy_labels, logits=True)
building_rate = positive_rate(dummy_logits, logits=True)

print(f"Mean IoU:      {iou_mean:.4f}")
print(f"Building IoU:  {iou_building:.4f}")
print(f"Building rate: {building_rate:.4f}  (fraction of pixels predicted as building)")
# %%
import s3fs
import mlflow
import requests
import tempfile
import numpy as np
from pathlib import Path

fs = s3fs.S3FileSystem(
    anon=True,
    endpoint_url="https://minio.lab.sspcloud.fr",
)

s3_run_path = "projet-funathon/mlflow-artifacts/1/88138b467a484c54b9935b66460413cd/artifacts/"

s3_model_path = s3_run_path + "model"
local_model_dir = Path(tempfile.mkdtemp()) / "model"

fs.get(s3_model_path, str(local_model_dir), recursive=True)

model = mlflow.pyfunc.load_model(str(local_model_dir))

params_url = "https://minio.lab.sspcloud.fr/" + s3_run_path + "params.json"

response = requests.get(params_url)
run_params = response.json()

n_bands = int(run_params["n_bands"])
tiles_size = int(run_params["tiles_size"])
augment_size = int(run_params["augment_size"])
module_name = run_params["module_name"]
normalization_mean = run_params["normalization_mean"][:n_bands]
normalization_std = run_params["normalization_std"][:n_bands]

print(f"n_bands={n_bands}, tiles_size={tiles_size}, augment_size={augment_size}")
print(f"mean={normalization_mean}")
print(f"std={normalization_std}")
# %%
from src.inference.prediction import predict

image_target = "LU000/2024/4022000_2979190_0_354.tif"
image_path = (
    "https://minio.lab.sspcloud.fr/projet-funathon/"
    "2026/project3/data/images/" + image_target
)
satellite_img, predictions = predict(
    images=image_path,
    model=model,
    tiles_size=tiles_size,
    augment_size=augment_size,
    n_bands=n_bands,
    normalization_mean=normalization_mean,
    normalization_std=normalization_std,
    module_name=module_name,
)

print(f"Mask shape : {predictions.shape}")
print(f"Classes found : {set(predictions.flatten().tolist())}")
# %%
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

# The 10 CLC+ Backbone classes — same set as defined in 1-acquisition.qmd § Exercise 10.
# Keep the order, IDs and hex colours in sync with that file (and with 5-statistics.qmd
# and map-nuts.qmd) so legends are consistent across the tutorial.
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
# %%
satellite_img_array = satellite_img["array"]
# Pick R/G/B (Sentinel-2 B4/B3/B2 → 0-indexed positions 3/2/1) and move
# channels last so matplotlib can render the natural-colour composite.
rgb = np.transpose(satellite_img_array[[3, 2, 1]], (1, 2, 0)).astype(np.float32)
# Cap brightness at the 98th percentile to avoid a few hot pixels washing out the image.
p98 = np.percentile(rgb, 98)
rgb = np.clip(rgb / p98, 0, 1)

fig, axes = plt.subplots(1, 2, figsize=(12, 6))

axes[0].imshow(rgb)
axes[0].set_title("Sentinel-2 RGB (B4, B3, B2)")
axes[0].axis("off")

axes[1].imshow(predictions, cmap=cmap, vmin=1, vmax=10)

axes[1].set_title("Predicted land cover")
axes[1].axis("off")

fig.legend(
    handles=legend_elements,
    loc="center left",
    bbox_to_anchor=(1.0, 0.5),
    frameon=True,
)
# %%
from src.inference.prediction import create_geojson_from_mask

gdf_pred = create_geojson_from_mask(satellite_img, predictions)

print(f"{len(gdf_pred)} polygons extracted")
print(gdf_pred.head())

fig, axes = plt.subplots(1, 3, figsize=(20, 6))

axes[0].imshow(rgb)
axes[0].set_title("Sentinel-2 RGB (B4, B3, B2)")
axes[0].axis("off")

axes[1].imshow(predictions, cmap=cmap, vmin=1, vmax=10)
axes[1].set_title("Predicted land cover")
axes[1].axis("off")

gdf_pred.plot(
    column="label",
    cmap=cmap,
    vmin=1, vmax=10,
    ax=axes[2],
    legend=False,
)
axes[2].set_title("Predicted polygons")
axes[2].set_aspect("equal")
xmin, ymin, xmax, ymax = gdf_pred.total_bounds
axes[2].set_xlim(xmin, xmax)
axes[2].set_ylim(ymin, ymax)
axes[2].axis("off")

fig.legend(handles=legend_elements, loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=True)
# %%
import folium
from folium.raster_layers import ImageOverlay
from rasterio.warp import transform_bounds, reproject, Resampling, calculate_default_transform
from rasterio.crs import CRS

# Folium / Leaflet only render WGS84 (EPSG:4326, lat/lon). The Sentinel-2 tile
# lives in EPSG:3035 (metric projection used across Europe), so both the raster
# and the prediction polygons must be reprojected before they reach the map.
src_crs = satellite_img["crs"]
src_transform = satellite_img["transform"]
src_bounds = satellite_img["bounds"]
dst_crs = CRS.from_epsg(4326)

raw_bands = satellite_img_array[[3, 2, 1]].astype(np.float32)
h, w = raw_bands.shape[1], raw_bands.shape[2]
# calculate_default_transform picks an output grid in EPSG:4326 that covers the
# same area; reproject() then resamples each band onto that grid.
dst_transform, dst_w, dst_h = calculate_default_transform(
    src_crs, dst_crs, w, h, *src_bounds
)
rgb_wgs84_bands = np.zeros((3, dst_h, dst_w), dtype=np.float32)
for i in range(3):
    reproject(
        source=raw_bands[i], destination=rgb_wgs84_bands[i],
        src_transform=src_transform, src_crs=src_crs,
        dst_transform=dst_transform, dst_crs=dst_crs,
        resampling=Resampling.bilinear,  # bilinear for continuous reflectance values
    )
p98 = np.percentile(rgb_wgs84_bands[rgb_wgs84_bands > 0], 98)
rgb_wgs84 = np.clip(np.transpose(rgb_wgs84_bands, (1, 2, 0)) / p98, 0, 1)
# Reprojection from a tilted source produces empty triangular corners. Build an
# alpha channel from "where was there any data?" so those corners stay transparent.
alpha = (rgb_wgs84_bands.max(axis=0) > 0).astype(np.float32)
rgba_wgs84 = np.dstack([rgb_wgs84, alpha])

west, south, east, north = transform_bounds(src_crs, dst_crs, *src_bounds)
center_lat = (south + north) / 2
center_lon = (west + east) / 2

m = folium.Map(location=[center_lat, center_lon], zoom_start=14)

fg_image = folium.FeatureGroup(name="Sentinel-2 RGB", show=True)
ImageOverlay(
    image=rgba_wgs84,
    bounds=[[south, west], [north, east]],
    opacity=0.7,
).add_to(fg_image)
fg_image.add_to(m)

fg_pred = folium.FeatureGroup(name="Predicted polygons", show=True)
gdf_pred_wgs84 = gdf_pred.to_crs("EPSG:4326")  # vector polygons reprojected for Folium
folium.GeoJson(
    gdf_pred_wgs84,
    style_function=lambda feature: {
        "fillColor": label_to_color.get(feature["properties"]["label"], "#808080"),
        "color": "black",
        "weight": 0.5,
        "fillOpacity": 0.6,
    },
    tooltip=folium.GeoJsonTooltip(fields=["label"], aliases=["Class:"]),
).add_to(fg_pred)
fg_pred.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

m
# %%
import requests

api_url = "https://funathon-2026-project3-api.lab.sspcloud.fr"

gps_point = [52.3879196469658, 16.987745050862774]  # [lat, lon]

response_nuts = requests.get(
    f"{api_url}/find_nuts",
    params={
        "gps_point": gps_point,
    },
)
response_nuts.raise_for_status()

nuts_id = response_nuts.json()
print(f"NUTS3 region found: {nuts_id}")

# %%
import json
import requests

api_url = "https://funathon-2026-project3-api.lab.sspcloud.fr"

gps_point = [52.3879196469658, 16.987745050862774]  # [lat, lon]
year = 2024

response_find = requests.get(
    f"{api_url}/find_image",
    params={
        "gps_point": gps_point,
        "year": year,
    },
)
response_find.raise_for_status()

image_filepath = response_find.json()
print(f"Image found: {image_filepath}")


# %%
import geopandas as gpd
from src.inference.prediction import get_satellite_image

response_pred = requests.get(
    f"{api_url}/predict_image",
    params={"image": image_filepath, "polygons": True},
)
response_pred.raise_for_status()

gdf_pred = gpd.GeoDataFrame.from_features(
    json.loads(response_pred.json())["features"],
    crs="EPSG:3035",
)

N_BANDS = 14
minio_url = "https://minio.lab.sspcloud.fr/"
image_url = minio_url + image_filepath
si = get_satellite_image(image_url, n_bands=N_BANDS)

rgb = np.transpose(si["array"][[3, 2, 1]], (1, 2, 0)).astype(np.float32)
p98 = np.percentile(rgb, 98)
rgb = np.clip(rgb / p98, 0, 1)

fig, axes = plt.subplots(1, 2, figsize=(12, 6))
axes[0].imshow(rgb)
axes[0].set_title("Sentinel-2 RGB (B4, B3, B2)")
axes[0].axis("off")
gdf_pred.plot(column="label", cmap=cmap, vmin=1, vmax=10, ax=axes[1], legend=False)
axes[1].set_title("Predicted polygons")
axes[1].set_aspect("equal")
xmin, ymin, xmax, ymax = gdf_pred.total_bounds
axes[1].set_xlim(xmin, xmax)
axes[1].set_ylim(ymin, ymax)
axes[1].axis("off")
fig.legend(handles=legend_elements, loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=True)
# %%
import geopandas as gpd
import requests
import json

api_url = "https://funathon-2026-project3-api.lab.sspcloud.fr"

image_filepath = (
    "projet-funathon/"
    "2026/project3/data/images/LU000/2024/"
    "4042000_2951690_0_637.tif"
)

response_pred = requests.get(
    f"{api_url}/predict_image",
    params={"image": image_filepath, "polygons": True},
)

gdf_tile = gpd.GeoDataFrame.from_features(
    json.loads(response_pred.json())["features"],
    crs="EPSG:3035",
)
# %%
# Same 10 CLC+ Backbone classes as in 1-acquisition.qmd / 4-inference.qmd —
# trimmed to the short names used in tables and bar-chart labels.
class_names = {
    1:  "Sealed",
    2:  "Woody – needle leaved",
    3:  "Woody – broadleaved deciduous",
    4:  "Woody – broadleaved evergreen",
    5:  "Low-growing woody plants",
    6:  "Permanent herbaceous",
    7:  "Periodically herbaceous",
    8:  "Lichens and mosses",
    9:  "Non- and sparsely-vegetated",
    10: "Water",
}

gdf_tile["area_m2"]    = gdf_tile.geometry.area
gdf_tile["area_km2"]   = gdf_tile["area_m2"] / 1e6
gdf_tile["class_name"] = gdf_tile["label"].map(class_names)
# %%
from great_tables import GT, style, loc

stats_tile = (
    gdf_tile.groupby(["label", "class_name"])
    .agg(
        n_polygons           = ("geometry", "count"),
        total_area_km2       = ("area_km2", "sum"),
        mean_polygon_area_m2 = ("area_m2",  "mean"),
        max_polygon_area_m2  = ("area_m2",  "max"),
    )
    .reset_index()
    .sort_values("total_area_km2", ascending=False)
)

total_km2 = stats_tile["total_area_km2"].sum()
stats_tile["share_pct"] = (stats_tile["total_area_km2"] / total_km2 * 100).round(2)

(
    GT(stats_tile, rowname_col="class_name")
    .tab_header(title="Land-cover statistics — single tile (LU000, 2024)")
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
# %%
import pandas as pd

sealed_km2 = stats_tile.loc[stats_tile["label"] == 1, "total_area_km2"].sum()
forest_km2 = stats_tile.loc[stats_tile["label"].isin([2, 3, 4]), "total_area_km2"].sum()
agri_km2 = stats_tile.loc[stats_tile["label"].isin([6, 7]), "total_area_km2"].sum()
water_km2 = stats_tile.loc[stats_tile["label"] == 10, "total_area_km2"].sum()

summary_df = pd.DataFrame(
    {
        "Group": ["Sealed (built-up)", "Forest", "Agricultural", "Water"],
        "area_km2": [sealed_km2, forest_km2, agri_km2, water_km2],
        "share_pct": [
            sealed_km2 / total_km2 * 100,
            forest_km2 / total_km2 * 100,
            agri_km2 / total_km2 * 100,
            water_km2 / total_km2 * 100,
        ],
    }
)
(
    GT(summary_df, rowname_col="Group")
    .tab_header(title="Key land-cover groups — single tile (LU000, 2024)")
    .cols_label(area_km2="Area (km²)", share_pct="Share (%)")
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

ax.set_xlabel("Area (km²)")
ax.set_title("Land-cover distribution — single tile (LU000, 2024)")
plt.tight_layout()
plt.show()
# %%
nuts_id = "LU000"
year = 2024

response_nuts = requests.get(
    f"{api_url}/predict_nuts",
    params={"nuts_id": nuts_id, "year": year},
)

gdf_nuts = gpd.GeoDataFrame.from_features(
    json.loads(response_nuts.json()["predictions"])["features"],
    crs="EPSG:3035",
)

gdf_nuts["area_m2"]    = gdf_nuts.geometry.area
gdf_nuts["area_km2"]   = gdf_nuts["area_m2"] / 1e6
gdf_nuts["class_name"] = gdf_nuts["label"].map(class_names)
# %%
stats_nuts = (
    gdf_nuts.groupby(["label", "class_name"])
    .agg(
        n_polygons           = ("geometry", "count"),
        total_area_km2       = ("area_km2", "sum"),
        mean_polygon_area_m2 = ("area_m2",  "mean"),
        max_polygon_area_m2  = ("area_m2",  "max"),
    )
    .reset_index()
    .sort_values("total_area_km2", ascending=False)
)

total_nuts_km2 = stats_nuts["total_area_km2"].sum()
stats_nuts["share_pct"] = (stats_nuts["total_area_km2"] / total_nuts_km2 * 100).round(2)

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

tile_shares = stats_tile.set_index("class_name")["share_pct"].rename("tile_share_pct")
nuts_shares = stats_nuts.set_index("class_name")["share_pct"].rename("nuts3_share_pct")
comparison  = pd.concat([tile_shares, nuts_shares], axis=1).fillna(0).reset_index()

(
    GT(comparison, rowname_col="class_name")
    .tab_header(title="Land-cover share — tile vs. NUTS3 (2024)")
    .cols_label(**{"tile_share_pct": "Tile (%)", "nuts3_share_pct": "NUTS3 (%)"})
    .fmt_number(decimals=1)
    .data_color(palette=["white", "steelblue"])
)
# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

stats_nuts.set_index("class_name")["total_area_km2"].sort_values().plot(
    kind="barh", ax=axes[0], color="steelblue"
)
axes[0].set_xlabel("Area (km²)")
axes[0].set_title("Land-cover area — LU000 (2024)")

stats_nuts.set_index("class_name")["share_pct"].sort_values().plot(
    kind="barh", ax=axes[1], color="darkorange"
)
axes[1].set_xlabel("Share (%)")
axes[1].set_title("Land-cover share — LU000 (2024)")

plt.tight_layout()
plt.show()
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
image_filepath_2021 = (
    "projet-funathon/"
    "2026/project3/data/images/LU000/2021/"
    "4042000_2951690_0_637.tif"
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
    params={"nuts_id": "LU000", "year": 2021},
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
axes[0].set_title("Land-cover share — LU000, 2021 vs 2024")
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
