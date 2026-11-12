import os
import sys
import io
import json
import shutil
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageOps, ImageCms
from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parent
RUTA_GALERIA_JSON = BASE_DIR / "galeria.json"
CARPETA_GALERIA_WEB = BASE_DIR / "galeria"

MAX_LADO_LARGO = 1600
CALIDAD_JPG = 80

# --- 1. OPTIMIZACIÓN (PIL) ---
def asegurar_srgb(img):
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

import time

import time

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
            # Si hay congestión temporal (503), espera y vuelve a intentar
            if intento < max_intentos:
                print(f"  [!] Servidor ocupado (503/alta demanda). Esperando {espera}s para reintentar...")
                time.sleep(espera)
                espera *= 2
            else:
                print("  [X] Se agotaron los intentos.")
                raise e

# --- 3. GESTIÓN LOCAL DE DATOS ---
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
        catalogo.insert(0, nuevo_registro)
        with open(RUTA_GALERIA_JSON, "w", encoding="utf-8") as f:
            json.dump(catalogo, f, indent=2, ensure_ascii=False)

        # Verificación estricta de sintaxis
        with open(RUTA_GALERIA_JSON, "r", encoding="utf-8") as f:
            json.load(f)

        if backup_path.exists():
            backup_path.unlink()
    except Exception as e:
        if backup_path.exists():
            shutil.copy2(backup_path, RUTA_GALERIA_JSON)
            backup_path.unlink()
        raise RuntimeError(f"Fallo al actualizar galeria.json: {e}")

# --- 4. FLUJO DE ENSAYO PILOTO ---
def ejecutar_piloto(ruta_archivo_origen: str, sesion_gaveta: str = "Prueba_Piloto"):
    origen = Path(ruta_archivo_origen)
    if not origen.exists():
        print(f"\n[!] Error: No se encontró el archivo: {origen.resolve()}")
        return

    print("=" * 60)
    print("      ENSAYO PILOTO LOCAL (MODO SEGURO - SIN GIT PUSH)")
    print("=" * 60)

    # 1. Asignar ID
    catalogo = cargar_catalogo()
    nuevo_id = obtener_siguiente_id(catalogo)
    nombre_web = f"foto{nuevo_id}.jpg"
    destino_web = CARPETA_GALERIA_WEB / nombre_web

    # 2. Optimización con Pillow
    print(f"\n[1/3] Optimizando imagen de prueba...")
    procesar_imagen_web(origen, destino_web)
    peso_kb = destino_web.stat().st_size / 1024
    print(f"  [OK] Generada: {destino_web.name} ({peso_kb:.1f} KB, sRGB, máx {MAX_LADO_LARGO}px)")

    # 3. Consulta a la IA
    print(f"\n[2/3] Analizando con Gemini (gemini-2.5-flash)...")
    datos_ia = consultar_ia_vision(destino_web)

    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    ahora = datetime.now()
    fecha_str = f"{meses[ahora.month - 1]} {ahora.year}"

    # 4. Construcción del registro
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

    print("\n--- PROPUESTA GENERADA ---")
    print(json.dumps(registro, indent=2, ensure_ascii=False))
    print("--------------------------")

    confirmacion = input("\n¿Inyectar este registro en galeria.json? [Enter = Sí / n = Cancelar]: ").strip().lower()
    if confirmacion == "n":
        print("\n[!] Operación cancelada. Eliminando archivo web temporal...")
        if destino_web.exists():
            destino_web.unlink()
        return

    # 5. Inyección local
    print(f"\n[3/3] Guardando en galeria.json...")
    inyectar_en_catalogo(registro)
    print("  [OK] galeria.json actualizado con éxito.")

    print("\n" + "=" * 60)
    print(f" [ENSAYO COMPLETADO] Foto #{nuevo_id} lista en disco local.")
    print(" (No se ejecutó ningún comando Git. Tu web remota no ha cambiado)")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ejecutar_piloto(sys.argv[1])
    else:
        # Si no pasas argumentos, busca cualquier foto de prueba en la carpeta
        print("Indica el nombre de la foto de prueba:")
        foto = input("Nombre o ruta de la foto (ej. prueba.jpg): ").strip().strip('"')
        if foto:
            ejecutar_piloto(foto)
