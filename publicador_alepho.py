import os
import sys
import io
import time
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageOps, ImageCms
from google import genai
from google.genai import types

# ==============================================================================
# CONFIGURACIÓN Y RUTAS (E:\AlephoStudio\codigo)
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent

RUTA_GALERIA_JSON = BASE_DIR / "galeria.json"
CARPETA_GALERIA_WEB = BASE_DIR / "galeria"

# Parámetros de optimización fotográfica
MAX_LADO_LARGO = 1600
CALIDAD_JPG = 80

# ==============================================================================
# 1. MOTOR DE OPTIMIZACIÓN (Pillow + sRGB + Lanczos)
# ==============================================================================
def asegurar_srgb(img):
    """Garantiza espacio sRGB para evitar tonos lavados en navegadores móviles."""
    try:
        icc_profile = img.info.get("icc_profile")
        if icc_profile:
            f_in = io.BytesIO(icc_profile)
            p_in = ImageCms.ImageCmsProfile(f_in)
            p_out = ImageCms.createProfile("sRGB")
            img = ImageCms.profileToProfile(img, p_in, p_out, outputMode="RGB")
        else:
            if img.mode != "RGB":
                img = img.convert("RGB")
    except Exception:
        if img.mode != "RGB":
            img = img.convert("RGB")
    return img

def redimensionar_foto(img, max_lado):
    """Corrige rotación EXIF y reescala proporcionalmente a 1600px con Lanczos."""
    img = ImageOps.exif_transpose(img)
    ancho, alto = img.size
    lado_mayor = max(ancho, alto)
    if lado_mayor <= max_lado:
        return img
    factor = max_lado / float(lado_mayor)
    nuevo_ancho = int(round(ancho * factor))
    nuevo_alto = int(round(alto * factor))
    return img.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)

def procesar_imagen_web(ruta_origen: Path, ruta_destino: Path):
    with Image.open(ruta_origen) as img:
        img_proc = redimensionar_foto(img, MAX_LADO_LARGO)
        img_proc = asegurar_srgb(img_proc)
        ruta_destino.parent.mkdir(parents=True, exist_ok=True)
        img_proc.save(
            ruta_destino,
            "JPEG",
            quality=CALIDAD_JPG,
            optimize=True,
            progressive=True
        )

# ==============================================================================
# 2. MOTOR DE VISIÓN IA (Gemini 3.8 Flash con Reintentos)
# ==============================================================================
def consultar_ia_vision(ruta_foto_optimizada: Path) -> dict:
    client = genai.Client()

    prompt = """
    Eres el catalogador técnico de fotografía de Alepho Studio.
    Analiza la imagen fotográfica (sujeto, composición, dirección de la luz, modificadores y estilo).

    Responde EXCLUSIVAMENTE con un JSON válido con esta estructura:
    {
      "title": "Título sobrio y formal de máximo 5 palabras",
      "category": "studio | producto | arte | exterior",
      "categoryLabel": "Estudio / Retrato | Producto & Gastronomía | Música & Arte | Exterior",
      "description": "Descripción formal de 1 o 2 oraciones sobre el encuadre, textura, sujeto y atmósfera visual.",
      "techNote": "Nota técnica concisa deduciendo modificadores (softbox, beauty dish, stripbox, luz natural, luz dura), ángulo (45°, lateral, cenital) y reflectores o luces de recorte."
    }

    Reglas estrictas de taxonomía:
    1. Usa solo uno de los pares permitidos:
       - "category": "studio"   -> "categoryLabel": "Estudio / Retrato"
       - "category": "producto" -> "categoryLabel": "Producto & Gastronomía"
       - "category": "arte"     -> "categoryLabel": "Música & Arte"
       - "category": "exterior" -> "categoryLabel": "Exterior"
    2. Cero adjetivos promocionales o de relleno.
    """

    with open(ruta_foto_optimizada, "rb") as f:
        bytes_foto = f.read()

    modelo_oficial = "gemini-3.8-flash"
    max_intentos = 4
    espera = 2

    for intento in range(1, max_intentos + 1):
        try:
            print(f"  -> Conectando con {modelo_oficial} (intento {intento}/{max_intentos})...")
            respuesta = client.models.generate_content(
                model=modelo_oficial,
                contents=[
                    types.Part.from_bytes(data=bytes_foto, mime_type="image/jpeg"),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            return json.loads(respuesta.text)
        except Exception as e:
            if intento < max_intentos:
                print(f"  [!] Servidor ocupado (503/alta demanda). Esperando {espera}s para reintentar...")
                time.sleep(espera)
                espera *= 2
            else:
                print("  [X] Se agotaron los intentos de conexión.")
                raise e

# ==============================================================================
# 3. GESTIÓN DEL CATÁLOGO (Puente Inmune y galeria.json)
# ==============================================================================
def cargar_catalogo() -> list:
    if not RUTA_GALERIA_JSON.exists():
        return []
    with open(RUTA_GALERIA_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def obtener_siguiente_id(catalogo: list) -> int:
    ids = [item["id"] for item in catalogo if "id" in item]
    return max(ids, default=0) + 1

def inyectar_en_catalogo(nuevo_registro: dict):
    backup_path = RUTA_GALERIA_JSON.with_suffix(".json.bak")
    catalogo = cargar_catalogo()

    if RUTA_GALERIA_JSON.exists():
        shutil.copy2(RUTA_GALERIA_JSON, backup_path)

    try:
        # Se inserta al inicio para que aparezca de primera en la web
        catalogo.insert(0, nuevo_registro)
        with open(RUTA_GALERIA_JSON, "w", encoding="utf-8") as f:
            json.dump(catalogo, f, indent=2, ensure_ascii=False)

        # Validación inmediata de sintaxis
        with open(RUTA_GALERIA_JSON, "r", encoding="utf-8") as f:
            json.load(f)

        if backup_path.exists():
            backup_path.unlink()
    except Exception as e:
        if backup_path.exists():
            shutil.copy2(backup_path, RUTA_GALERIA_JSON)
            backup_path.unlink()
        raise RuntimeError(f"Fallo al escribir en galeria.json: {e}")

# ==============================================================================
# 4. DESPLIEGUE A GITHUB PAGES (Git Add, Commit, Push)
# ==============================================================================
def sincronizar_git(archivo_foto_web: Path, id_foto: int):
    print("\n[4/4] Sincronizando con repositorio remoto...")
    
    comandos = [
        ["git", "add", str(RUTA_GALERIA_JSON), "galeria/"],
        ["git", "commit", "-m", f"Publicar foto #{id_foto} en catalogo web"],
        ["git", "push", "origin", "main"]
    ]
    
    for cmd in comandos:
        res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
        if res.returncode != 0:
            # Si no hay cambios para commit, Git da código 1 pero no es fatal
            if "nothing to commit" in res.stdout or "nothing to commit" in res.stderr:
                continue
            raise RuntimeError(f"Fallo en Git ({' '.join(cmd)}):\n{res.stderr or res.stdout}")
            
    print("  [OK] Cambios empujados a GitHub exitosamente.")

# ==============================================================================
# 5. ORQUESTACIÓN PRINCIPAL
# ==============================================================================

def procesar_publicacion(ruta_archivo_origen: str, sesion_gaveta: str = "General"):
    origen = Path(ruta_archivo_origen)
    if not origen.exists():
        print(f"\n[!] Error: No se encontró el archivo: {origen.resolve()}")
        return

    print("=" * 60)
    print("      ALEPHO STUDIO — PUBLICADOR AUTOMATIZADO")
    print("=" * 60)

    # 1. Asignar ID correlativo
    catalogo = cargar_catalogo()
    nuevo_id = obtener_siguiente_id(catalogo)
    nombre_web = f"foto{nuevo_id}.jpg"
    destino_web = CARPETA_GALERIA_WEB / nombre_web

    # 2. Optimización con Pillow
    print(f"\n[1/4] Optimizando imagen...")
    procesar_imagen_web(origen, destino_web)
    peso_kb = destino_web.stat().st_size / 1024
    print(f"  [OK] Generada: {destino_web.name} ({peso_kb:.1f} KB, sRGB, máx {MAX_LADO_LARGO}px)")

    # 3. Análisis visual con IA
    print(f"\n[2/4] Analizando imagen con Gemini...")
    datos_ia = consultar_ia_vision(destino_web)

    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    ahora = datetime.now()
    fecha_str = f"{meses[ahora.month - 1]} {ahora.year}"

    # 4. Construcción del registro Puente Inmune
    registro = {
        "id": nuevo_id,
        "title": datos_ia.get("title", f"Fotografía #{nuevo_id}"),
        "category": datos_ia.get("category", "studio"),
        "categoryLabel": datos_ia.get("categoryLabel", "Estudio / Retrato"),
        "date": fecha_str,
        "src": f"galeria/{nombre_web}",
        "archivo_origen": origen.name,
        "sesion": sesion_gaveta,
        "description": datos_ia.get("description", ""),
        "techNote": datos_ia.get("techNote", "")
    }

    # Bucle interactivo de validación y edición
    while True:
        print("\n--- FICHA PROPUESTA POR LA IA ---")
        print(f"ID:            {registro['id']}")
        print(f"Título:        {registro['title']}")
        print(f"Categoría:     {registro['categoryLabel']} ({registro['category']})")
        print(f"Fecha:         {registro['date']}")
        print(f"Descripción:   {registro['description']}")
        print(f"Técnica:       {registro['techNote']}")
        print(f"Puente Gaveta: {registro['archivo_origen']} (Sesión: {registro['sesion']})")
        print("---------------------------------")

        confirmacion = input("\n¿Aprobar y desplegar? [Enter = Sí / e = Editar / n = Cancelar]: ").strip().lower()

        if confirmacion in ["", "s", "si", "sí"]:
            break  # Aprobado, continúa al paso 5

        elif confirmacion == "n":
            print("\n[!] Operación cancelada por el usuario. Eliminando archivo web generado...")
            if destino_web.exists():
                destino_web.unlink()
            return

        elif confirmacion == "e":
            print("\n--- MODO EDICIÓN (Presiona Enter para mantener el valor actual) ---")
            
            nuevo_titulo = input(f"Título [{registro['title']}]: ").strip()
            if nuevo_titulo:
                registro['title'] = nuevo_titulo

            nueva_cat_label = input(f"Etiqueta Categoría [{registro['categoryLabel']}]: ").strip()
            if nueva_cat_label:
                registro['categoryLabel'] = nueva_cat_label

            nueva_cat = input(f"Filtro Categoría (studio/exterior/arte/producto) [{registro['category']}]: ").strip()
            if nueva_cat:
                registro['category'] = nueva_cat

            nueva_desc = input(f"Descripción [{registro['description']}]: ").strip()
            if nueva_desc:
                registro['description'] = nueva_desc

            nueva_tech = input(f"Técnica / Esquema de luz [{registro['techNote']}]: ").strip()
            if nueva_tech:
                registro['techNote'] = nueva_tech

            print("\n[OK] Datos actualizados. Revisa la ficha nuevamente a continuación:")
        else:
            print("[!] Opción no reconocida. Escribe Enter, 'e' o 'n'.")

    # 5. Inyección en galeria.json
    print(f"\n[3/4] Inyectando datos en galeria.json...")
    inyectar_en_catalogo(registro)
    print("  [OK] Registro indexado y validado.")

    # 6. Sincronización Git
    sincronizar_git(destino_web, nuevo_id)

    print("\n" + "=" * 60)
    print(f" [ÉXITO] ¡Foto #{nuevo_id} publicada en vivo en alephostudio.com!")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        archivo = sys.argv[1]
        sesion = sys.argv[2] if len(sys.argv) > 2 else "Archivo_Directo"
        procesar_publicacion(archivo, sesion)
    else:
        print("Modo de uso interactivo:")
        foto = input("Arrastra la foto a esta ventana o escribe su nombre: ").strip().strip('"')
        if foto:
            sesion = input("Nombre o ID de la sesión en Gaveta (Enter = 'General'): ").strip()
            procesar_publicacion(foto, sesion if sesion else "General")
