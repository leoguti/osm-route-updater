# OSM Route Generator con Valhalla

Este script permite generar archivos `.osm` que contienen relaciones de tipo `route=bus`, basadas en coordenadas extraídas de un archivo GeoJSON y procesadas mediante el servicio Valhalla.

## 🚀 Requisitos

- Python 3.8 o superior
- Conexión a Internet (para consultar el endpoint de Valhalla)
- Archivo GeoJSON válido con rutas (tipo `FeatureCollection`)

## 🔧 Instalación

```bash
git clone https://github.com/leoguti/osm-route-updater.git
cd osm-route-updater
pip install -r requirements.txt

## Uso
python main.py --geojson tu_archivo.geojson --mode nuevo
