import json
import os
import time
import requests
import argparse
import threading
from bs4 import BeautifulSoup

# Ruta base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Archivos de entrada y salida
INPUT_JSON = r'datos/json/revistas.json' 
OUTPUT_JSON = r'datos/json/revistas_scimagojr.json'
BACKUP_JSON = r'datos/json/revistas_scimagojr_backup.json'

# Argumentos desde consola
parser = argparse.ArgumentParser(description='Recolector de datos desde ScimagoJR')
parser.add_argument('--inicio', type=int, default=0, help='Índice inicial')
parser.add_argument('--fin', type=int, help='Índice final (opcional)')
parser.add_argument('--reverso', action='store_true', help='Procesar en orden inverso')
args = parser.parse_args()

# Cabecera para solicitud HTTP
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/123.0.0.0 Safari/537.36'
}
SCIMAGO_BASE_URL = 'https://www.scimagojr.com'
SEARCH_URL = f'{SCIMAGO_BASE_URL}/journalsearch.php?q='

def guardar_datos(data, titulo=""):
    try:
        with open(BACKUP_JSON, 'w', encoding='utf-8') as bkp:
            json.dump(data, bkp, indent=4, ensure_ascii=False)
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as out:
            json.dump(data, out, indent=4, ensure_ascii=False)
        if titulo:
            print(f"Información guardada: {titulo}")
        return True
    except Exception as e:
        print(f"Error al guardar: {e}")
        return False

# Cargar datos existentes
if os.path.exists(OUTPUT_JSON):
    with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
        revistas_data = json.load(f)
elif os.path.exists(BACKUP_JSON):
    print("Cargando respaldo existente...")
    with open(BACKUP_JSON, 'r', encoding='utf-8') as f:
        revistas_data = json.load(f)
else:
    revistas_data = {}

def obtener_pagina(url):
    response = requests.get(url, headers=HEADERS, timeout=15)
    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code} en {url}")
    return response

def buscar_url_revista(nombre):
    consulta = SEARCH_URL + nombre.replace(" ", "+")
    html = BeautifulSoup(obtener_pagina(consulta).text, 'html.parser')
    resultado = html.select_one('span.jrnlname')
    if resultado:
        return SCIMAGO_BASE_URL + '/' + resultado.find_parent('a')['href']
    return None

def extraer_imagen(soup):
    try:
        img = soup.find('img', class_='imgwidget')
        if img and 'src' in img.attrs:
            return f'https://www.scimagojr.com/{img["src"]}'
    except Exception as e:
        print(f"Error obteniendo imagen: {e}")
    return None

def obtener_areas(soup):
    seccion = soup.find("h2", string="Subject Area and Category")
    if not seccion:
        return None
    tabla = seccion.find_next("table")
    if not tabla:
        return None
    columnas = tabla.find_all("td")
    categorias = [td.get_text(strip=True) for td in columnas if td]
    return ', '.join(categorias)

# Función para extraer el ID de la URL del widget
def extraer_id_widget(url_widget):
    try:
        return url_widget.split('id=')[-1]
    except:
        return None

def obtener_catalogos(url):
    """Obtener los catálogos desde la página de la revista en Scimago."""
    soup = BeautifulSoup(obtener_pagina(url).text, 'html.parser')
    catalogos = []
    try:
        # Lógica para extraer los catálogos. Esto depende de la estructura de la página.
        # Ejemplo de extracción de un listado de catálogos.
        catalogos_section = soup.find('div', class_='catalogs')  # Este es un ejemplo, puede necesitar ajustes.
        if catalogos_section:
            catalogos = [cat.text.strip() for cat in catalogos_section.find_all('li')]
    except Exception as e:
        print(f"Error obteniendo catálogos: {e}")
    return catalogos

def recolectar_info_revista(url):
    """Recolecta la información de la revista y actualiza los catálogos."""
    soup = BeautifulSoup(obtener_pagina(url).text, 'html.parser')

    def extraer_texto(titulo):
        try:
            h2 = soup.find('h2', string=lambda s: s and titulo in s)
            return h2.find_next_sibling('p').text.strip() if h2 else None
        except:
            return None

    # Extraer URL del widget
    widget_url = soup.find('img', class_='imgwidget')['src'] if soup.find('img', class_='imgwidget') else None
    id_revista = extraer_id_widget(widget_url) if widget_url else None

    # Extraer catálogos desde la página
    catalogos = obtener_catalogos(url)  # Llamamos la función que obtendrá los catálogos

    return {
        "site": (soup.find('a', string='Homepage')['href'] if soup.find('a', string='Homepage') else None),
        "h_index": extraer_texto("H-Index"),
        "subject_area_category": obtener_areas(soup),
        "publisher": extraer_texto("Publisher"),
        "issn": extraer_texto("ISSN"),
        "widget": widget_url,
        "publication_type": extraer_texto("Publication type"),
        "url": url,
        "id": id_revista,  # Almacenamos el ID extraído
        "areas": obtener_areas(soup).split(",") if obtener_areas(soup) else [],  # Guardamos áreas
        "catalogos": catalogos  # Añadimos los catálogos obtenidos
    }

# Cargar entradas a procesar
with open(INPUT_JSON, 'r', encoding='utf-8') as f:
    revistas_input = json.load(f)

inicio = args.inicio
fin = args.fin if args.fin is not None else len(revistas_input)
revistas_items = list(revistas_input.items())

if args.reverso:
    revistas_items = revistas_items[::-1]
    if args.fin is not None:
        inicio = len(revistas_items) - args.fin
        fin = len(revistas_items) - args.inicio

revistas_a_procesar = revistas_items[inicio:fin]

print(f"Procesando desde índice {inicio} hasta {fin}")
print(f"Total a procesar: {len(revistas_a_procesar)}")

# Variable global para pausa
pausado = False

def alternar_pausa():
    global pausado
    pausado = not pausado
    estado = "pausado" if pausado else "activo"
    print(f"Proceso {estado}")

def contar_registros():
    if os.path.exists(OUTPUT_JSON):
        with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            return len(datos)
    return 0

def esperar_comando():
    while True:
        cmd = input("Escribe 'pausar' para alternar estado: ").strip().lower()
        if cmd == 'pausar':
            alternar_pausa()

threading.Thread(target=esperar_comando, daemon=True).start()

contador = 0
for titulo, _ in revistas_a_procesar:
    while pausado:
        print(f"En pausa. Progreso: {contar_registros()} registros")
        time.sleep(5)

    if titulo in revistas_data:
        print(f"Ya se procesó antes: {titulo}")
        continue

    print(f"Procesando revista: {titulo} (posición: {inicio + contador})")
    try:
        url = buscar_url_revista(titulo)
        if not url:
            print(f"No se encontró en Scimago: {titulo}")
            continue

        info = recolectar_info_revista(url)
        revistas_data[titulo] = info
        guardar_datos(revistas_data, titulo)
        contador += 1
        time.sleep(2)
    except Exception as e:
        print(f"Error con revista {titulo}: {e}")

guardar_datos(revistas_data)
print(f"Finalizado. Total nuevas revistas: {contador}")
print(f"Rango completado: {inicio} a {fin}")
