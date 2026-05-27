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
