'''
Se proporciona un archivo zip con la siguiente estructura:

datos
├── json
└── csv
    ├── areas
    └── catalogos

El objetivo es leer los archivos csv del subfolder areas y catálogos, crear un diccionario de revistas donde la llave sea el título de la revista y el valor un diccionario con las llaves "areas" y "catalogos". Ejemplo:

    { "acta geophysica"       : { "areas": ["CIENCIAS_EXA", "ING"], "catalogos":["JCR","SCOPUS"]},
      "acta geophysica sinica": { "areas": ["CIENCIAS_EXA"], "catalogos":["SCOPUS"]}  
    }

Una vez creado el diccionario, guardarlo como archivo json en el subfolder del mismo nombre (datos/json). Verificar que puede ser leído

'''

import csv
import os
import json

def leer_csv(carpeta, campo):
    datos = {}
    for archivo in os.listdir(carpeta):
        if archivo.endswith('.csv'):
            ruta_archivo = os.path.join(carpeta, archivo)
            with open(ruta_archivo, mode='r', encoding='latin-1') as archivo_csv:
                lector = csv.DictReader(archivo_csv)
                for fila in lector:
                    titulo = fila[campo].strip().lower()
                    valor_original = fila[campo].strip()
                    if titulo not in datos:
                        datos[titulo] = set()
                    datos[titulo].add(valor_original)
    return datos

def crear_diccionario(datos_areas, datos_catalogos):
    diccionario = {}
    titulos = set(datos_areas.keys()).union(datos_catalogos.keys())

    for titulo in titulos:
        diccionario[titulo] = {
            "areas": sorted(datos_areas.get(titulo, [])),
            "catalogos": sorted(datos_catalogos.get(titulo, []))
        }
    return diccionario

if __name__ == "__main__":
    def main():
        # CHECAR BIEN
        ruta_areas = r'datos/csv/areas'
        ruta_catalogos = r'datos/csv/catalogos'
        salida_json = r'datos/json/revistas.json'

        datos_areas = leer_csv(ruta_areas, 'TITULO:')
        datos_catalogos = leer_csv(ruta_catalogos, 'TITULO:')
        diccionario_revistas = crear_diccionario(datos_areas, datos_catalogos)

        with open(salida_json, mode='w', encoding='utf-8') as archivo_json:
            json.dump(diccionario_revistas, archivo_json, indent=4, ensure_ascii=False)

        print(f"Se ha generado el archivo JSON con éxito en {salida_json}")

    main()
