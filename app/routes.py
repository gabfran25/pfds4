from flask import Flask, render_template, request
import json
import os

app = Flask(__name__)

from urllib.parse import quote
app.jinja_env.filters['urlencode'] = lambda u: quote(u)


# Ruta al archivo JSON generado por parteDos.py
JSON_PATH = os.path.join('datos', 'json', 'revistas_scimagojr.json')

# Cargar datos
with open(JSON_PATH, 'r', encoding='utf-8') as f:
    revistas_data = json.load(f)

# ---- FUNCIONES AUXILIARES ----
def normalizar(titulo):
    return titulo.strip().lower()

def buscar_revistas_por_letra(letra):
    resultados = []
    for titulo, datos in revistas_data.items():
        if titulo.startswith(letra.lower()):
            resultados.append({
                "titulo": titulo,
                "h_index": datos.get("h_index", ""),
                "areas": datos.get("areas", []),
                "catalogos": datos.get("catalogos", [])
            })
    return resultados

def buscar_revistas_por_texto(texto):
    texto = texto.lower()
    resultados = []
    for titulo, datos in revistas_data.items():
        if texto in titulo:
            resultados.append({
                "titulo": titulo,
                "h_index": datos.get("h_index", ""),
                "areas": datos.get("areas", []),
                "catalogos": datos.get("catalogos", [])
            })
    return resultados

# ---- RUTAS PRINCIPALES ----

@app.context_processor
def inject_now():
    from datetime import datetime
    return {'now': datetime.now}

@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/areas')
def areas():
    lista_areas = set()
    for datos in revistas_data.values():
        if 'areas' in datos:
            lista_areas.update(datos['areas'])
    return render_template('areas.html', areas=sorted(lista_areas))

@app.route('/areas/<nombre>')
def ver_area(nombre):
    revistas = []
    for titulo, datos in revistas_data.items():
        if nombre in datos.get('areas', []):
            revistas.append({
                "titulo": titulo,
                "h_index": datos.get("h_index", "")
            })
    return render_template('areas.html', area_actual=nombre, revistas=revistas)

@app.route('/catalogos')
def catalogos():
    catalogos_unicos = set()
    for datos in revistas_data.values():
        for cat in datos.get('catalogos', []):
            catalogos_unicos.add(cat)
    return render_template('catalogos.html', catalogos=sorted(catalogos_unicos))

@app.route('/catalogos/<nombre>')
def ver_catalogo(nombre):
    revistas = []
    for titulo, datos in revistas_data.items():
        if nombre in datos.get('catalogos', []):
            revistas.append({
                "titulo": titulo,
                "h_index": datos.get("h_index", "")
            })
    return render_template('catalogos.html', catalogo_actual=nombre, revistas=revistas)

@app.route('/explorar')
def explorar():
    letras = sorted(set(t[0].upper() for t in revistas_data.keys()))
    return render_template('explorar.html', letras=letras)

@app.route('/explorar/<letra>')
def explorar_letra(letra):
    revistas = buscar_revistas_por_letra(letra)
    letras = sorted(set(t[0].upper() for t in revistas_data.keys()))
    return render_template('explorar.html', revistas=revistas, letra_actual=letra.upper(), letras=letras)

@app.route('/busqueda')
def buscar():
    query = request.args.get('q', '')
    resultados = buscar_revistas_por_texto(query) if query else []
    return render_template('busqueda.html', resultados=resultados, query=query)

@app.route('/revista/<titulo>')
def ver_revista(titulo):
    for nombre, datos in revistas_data.items():
        if normalizar(nombre) == normalizar(titulo):
            return render_template('revista.html', titulo=nombre, datos=datos)
    return f"No se encontró información para: {titulo}", 404

@app.route('/creditos')
def creditos():
    integrantes = [
        {"nombre": "José Alberto Germán López", "foto": "/static/images/yop.jpg"},
    ]
    return render_template('creditos.html', integrantes=integrantes)
