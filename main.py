import argparse
import json
import logging
import os
import requests
from shapely.geometry import shape

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

def validar_geojson(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if data.get("type") != "FeatureCollection":
            raise ValueError("El GeoJSON no es una FeatureCollection.")
        if "features" not in data:
            raise ValueError("No se encuentra la clave 'features'.")
        for idx, feature in enumerate(data["features"]):
            geom = feature.get("geometry")
            if not geom:
                raise ValueError(f"Falta la geometría en la 'Feature' #{idx + 1}.")
            coords = geom.get("coordinates")
            if not coords or not isinstance(coords, list):
                raise ValueError(f"Coordenadas inválidas en la 'Feature' #{idx + 1}.")
            shape(geom)
        return data
    except Exception as e:
        logging.error(f"❌ Error al validar el GeoJSON: {e}")
        return None

def solicitar_valhalla(coordenadas):
    url = "https://valhalla1.openstreetmap.de/trace_attributes"
    payload = {
        "shape": [{"lat": lat, "lon": lon} for lon, lat, *_ in coordenadas],
        "costing": "auto",
        "shape_match": "walk_or_snap"
    }
    try:
        respuesta = requests.post(url, json=payload)
        respuesta.raise_for_status()
        resultado = respuesta.json()
        logging.info("📡 Respuesta Valhalla recibida.")
        return resultado
    except Exception as e:
        logging.error(f"❌ Error en la petición a Valhalla: {e}")
        return None

def eliminar_repetidos_consecutivos(lista):
    resultado = []
    anterior = None
    for elem in lista:
        if elem != anterior:
            resultado.append(elem)
        anterior = elem
    return resultado

def generar_osm(way_ids, archivo="output.osm"):
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<osm version="0.6" generator="Trufi-Valhalla">\n')
        f.write('  <relation id="-1" visible="true" version="1">\n')
        for way_id in way_ids:
            f.write(f'    <member type="way" ref="{way_id}" role=""/>\n')
        f.write('    <tag k="type" v="route"/>\n')
        f.write('    <tag k="route" v="bus"/>\n')
        f.write('  </relation>\n')
        f.write('</osm>\n')
    logging.info(f"📁 Archivo OSM generado: {archivo}")

def main():
    parser = argparse.ArgumentParser(description="OSM Route Updater")
    parser.add_argument("--geojson", required=True, help="Ruta al archivo GeoJSON")
    parser.add_argument("--mode", required=True, choices=["nuevo", "actualizar"], help="Modo de operación")
    parser.add_argument("--relation_id", type=int, help="ID de la relación OSM a actualizar")

    args = parser.parse_args()

    if not os.path.exists(args.geojson):
        logging.error(f"❌ Archivo '{args.geojson}' no encontrado.")
        return
    else:
        logging.info(f"✔ Archivo '{args.geojson}' encontrado.")

    logging.info(f"✔ Modo seleccionado: {args.mode}")
    geojson = validar_geojson(args.geojson)
    if not geojson:
        return

    logging.info("✔ GeoJSON válido.")

    if args.mode == "nuevo":
        for feature in geojson["features"]:
            coordenadas = feature["geometry"]["coordinates"]
            respuesta = solicitar_valhalla(coordenadas)
            if respuesta and "edges" in respuesta:
                way_ids = [edge["way_id"] for edge in respuesta["edges"] if "way_id" in edge]
                way_ids_sin_repetidos = eliminar_repetidos_consecutivos(way_ids)
                logging.info("🛣️ Total de way_ids (sin repeticiones consecutivas): %d", len(way_ids_sin_repetidos))
                generar_osm(way_ids_sin_repetidos)
            else:
                logging.error("❌ La respuesta de Valhalla no contiene 'edges'.")
    elif args.mode == "actualizar":
        if not args.relation_id:
            logging.error("❌ El parámetro --relation_id es obligatorio en modo actualizar.")
            return

        logging.info(f"🔄 Modo actualizar: relation_id = {args.relation_id}")

        for feature in geojson["features"]:
            coordenadas = feature["geometry"]["coordinates"]
            respuesta = solicitar_valhalla(coordenadas)
            if respuesta and "edges" in respuesta:
                way_ids = [edge["way_id"] for edge in respuesta["edges"] if "way_id" in edge]
                way_ids_sin_repetidos = eliminar_repetidos_consecutivos(way_ids)
                logging.info("🛣️ Total de way_ids (sin repeticiones consecutivos): %d", len(way_ids_sin_repetidos))

                # 🧩 Aquí más adelante reemplazaremos el cuerpo de la relación existente.
                # Por ahora solo creamos un nuevo archivo con el mismo ID.
                generar_osm(way_ids_sin_repetidos, archivo=f"output_relation_{args.relation_id}.osm")
            else:
                logging.error("❌ La respuesta de Valhalla no contiene 'edges'.")
    

if __name__ == "__main__":
    main()
