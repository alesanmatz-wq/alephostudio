import os
import json
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Rutas del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GALERIA_DIR = os.path.join(BASE_DIR, "galeria", "portafolio")
JSON_PATH = os.path.join(BASE_DIR, "galeria", "fotos.json")

class StudioBatchManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Alepho Studio — Carga por Lote de Sesión")
        self.geometry("560x720")
        self.resizable(False, False)
        self.configure(bg="#121316")

        self.selected_files = []
        self._setup_styles()
        self._build_ui()
        self._ensure_paths()

    def _ensure_paths(self):
        os.makedirs(GALERIA_DIR, exist_ok=True)
        if not os.path.exists(JSON_PATH):
            with open(JSON_PATH, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        
        style.configure(".", background="#121316", foreground="#E5E5E5", font=("Segoe UI", 10))
        style.configure("TLabel", background="#121316", foreground="#A3A3A3")
        style.configure("TButton", background="#1E2024", foreground="#E5E5E5", borderwidth=1, focuscolor="none")
        style.map("TButton", background=[("active", "#2A2D33")])
        style.configure("Accent.TButton", background="#C59B60", foreground="#121316", font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#D4AF37")])

    def _build_ui(self):
        pad_x, pad_y = 24, 6

        # Encabezado
        lbl_head = tk.Label(self, text="REGISTRO POR LOTE DE SESIÓN", bg="#121316", fg="#C59B60", font=("Georgia", 13, "bold"))
        lbl_head.pack(pady=(16, 10))

        # Selector de Lote de Imágenes
        frame_file = tk.Frame(self, bg="#121316")
        frame_file.pack(fill="x", padx=pad_x, pady=pad_y)
        ttk.Label(frame_file, text="Selección de archivos (múltiples fotos):").pack(anchor="w")
        
        self.lbl_count = tk.Label(frame_file, text="0 fotos seleccionadas", bg="#1E2024", fg="#737373", anchor="w", padx=10, pady=5)
        self.lbl_count.pack(side="left", fill="x", expand=True, pady=4)
        
        btn_browse = ttk.Button(frame_file, text="Examinar Lote...", command=self._browse_batch)
        btn_browse.pack(side="right", padx=(8, 0), pady=4)

        # Pequeña lista para previsualizar los nombres elegidos
        self.lst_preview = tk.Listbox(self, height=4, bg="#181A1E", fg="#A3A3A3", selectbackground="#C59B60", selectforeground="#121316", relief="flat")
        self.lst_preview.pack(fill="x", padx=pad_x, pady=(0, pad_y))

        # Nombre de la Sesión / Título base
        ttk.Label(self, text="Título base de la sesión:").pack(anchor="w", padx=pad_x, pady=(pad_y, 0))
        self.ent_title = ttk.Entry(self)
        self.ent_title.pack(fill="x", padx=pad_x, pady=(0, pad_y))

        # Categoría
        ttk.Label(self, text="Categoría:").pack(anchor="w", padx=pad_x, pady=(pad_y, 0))
        self.cb_category = ttk.Combobox(self, state="readonly", values=["estudio", "retrato", "exterior", "gourmet", "archivo"])
        self.cb_category.set("estudio")
        self.cb_category.pack(fill="x", padx=pad_x, pady=(0, pad_y))

        # Fecha de sesión
        ttk.Label(self, text="Fecha de sesión:").pack(anchor="w", padx=pad_x, pady=(pad_y, 0))
        self.ent_date = ttk.Entry(self)
        self.ent_date.insert(0, datetime.now().strftime("%d de %B de %Y"))
        self.ent_date.pack(fill="x", padx=pad_x, pady=(0, pad_y))

        # Nota técnica
        ttk.Label(self, text="Esquema de iluminación / Óptica:").pack(anchor="w", padx=pad_x, pady=(pad_y, 0))
        self.ent_tech = ttk.Entry(self)
        self.ent_tech.insert(0, "Luz principal · Modificador suave")
        self.ent_tech.pack(fill="x", padx=pad_x, pady=(0, pad_y))

        # Descripción
        ttk.Label(self, text="Descripción general de la serie:").pack(anchor="w", padx=pad_x, pady=(pad_y, 0))
        self.txt_desc = tk.Text(self, height=3, bg="#1E2024", fg="#E5E5E5", insertbackground="white", relief="flat", padx=8, pady=6)
        self.txt_desc.pack(fill="x", padx=pad_x, pady=(0, 15))

        # Botón Guardar Lote
        btn_save = ttk.Button(self, text="Guardar e Indexar Lote Completo", style="Accent.TButton", command=self._save_batch)
        btn_save.pack(fill="x", padx=pad_x, pady=10)

    def _browse_batch(self):
        filetypes = [("Imágenes JPG", "*.jpg *.jpeg *.JPG *.JPEG"), ("Todos los archivos", "*.*")]
        # askopenfilenames permite selección múltiple con Ctrl o Shift
        paths = filedialog.askopenfilenames(title="Seleccionar lote de fotografías", filetypes=filetypes)
        if paths:
            self.selected_files = list(paths)
            self.lbl_count.config(text=f"{len(self.selected_files)} fotos seleccionadas para indexar", fg="#C59B60")
            
            # Poblar la lista previa
            self.lst_preview.delete(0, tk.END)
            for p in self.selected_files:
                self.lst_preview.insert(tk.END, f"• {os.path.basename(p)}")

    def _save_batch(self):
        if not self.selected_files:
            messagebox.showwarning("Faltan fotos", "No has seleccionado ninguna imagen.")
            return

        base_title = self.ent_title.get().strip()
        if not base_title:
            messagebox.showwarning("Falta título", "Asigna un título base para la sesión.")
            return

        category = self.cb_category.get()
        date_str = self.ent_date.get().strip()
        tech_str = self.ent_tech.get().strip()
        desc_str = self.txt_desc.get("1.0", tk.END).strip()

        # Cargar catálogo actual
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []

        current_max_id = max([item.get("id", 0) for item in data], default=0)
        total_photos = len(self.selected_files)
        new_entries = []

        # Procesar cada foto del lote
        for idx, file_path in enumerate(self.selected_files, start=1):
            next_id = current_max_id + idx
            ext = os.path.splitext(file_path)[1].lower()
            new_filename = f"foto{next_id}{ext}"
            dest_path = os.path.join(GALERIA_DIR, new_filename)

            # Copiar imagen al portafolio
            shutil.copy2(file_path, dest_path)

            # Título individual si es más de una foto
            item_title = f"{base_title} #{idx}" if total_photos > 1 else base_title

            entry = {
                    "id": next_id,
                    "src": f"galeria/portafolio/{new_filename}",
                    "title": item_title,
                    "category": category,
                    "categoryLabel": category.capitalize(),
                    "date": date_str,
                    "description": desc_str,
                    "techNote": tech_str
                    }
            [
                {
                    "id": 1,
                    "title": "Penumbra y Claroscuro",
                    "category": "studio",
                    "categoryLabel": "Estudio / Retrato",
                    "date": "Octubre 2026",
                    "src": "galeria/foto6.jpg",
                    "description": "Estudio de claroscuro y contraste dramático.",
                    "techNote": "Luz principal puntual con panal de abeja (grid)."
                },
                {
                    "id": 2,
                    "title": "Juventud y Carácter",
                    "category": "studio",
                    "categoryLabel": "Estudio / Retrato",
                    "date": "Octubre 2026",
                    "src": "galeria/foto2.JPG",
                    "description": "Estudio de expresión y pose formal. La cita de Rubén Darío como homenaje a la juventud.",
                    "techNote": "Luz principal suave a 45° con difusor octabox y reflector inferior para suavizar sombras en cuello."
                },
                {
                    "id": 3,
                    "title": "Serenidad en el Set",
                    "category": "studio",
                    "categoryLabel": "Estudio / Retrato",
                    "date": "Octubre 2026",
                    "src": "galeria/foto3.JPG",
                    "description": "Retrato formal de estudio explorando la naturalidad en la pose y la contención en el gesto.",
                    "techNote": "Esquema cerrado con modificador frontal difuso y control estricto de rebote para modelar facciones."
                },
                {
                    "id": 4,
                    "title": "El amor todo lo vence",
                    "category": "studio",
                    "categoryLabel": "Estudio / Retrato",
                    "date": "Julio 2026",
                    "src": "galeria/foto4.JPG",
                    "description": "Una mirada, una sonrisa y estaremos juntos por siempre.",
                    "techNote": "Octabox de 120cm cenital y reflector blanco abajo para crear esquema tipo concha de ostra (clamshell)."
                },
                {
                    "id": 5,
                    "title": "Retrato en Clave Media",
                    "category": "studio",
                    "categoryLabel": "Estudio / Retrato",
                    "date": "Octubre 2026",
                    "src": "galeria/foto5.JPG",
                    "description": "Postura formal y dirección de mirada. El optimismo y la serenidad expresiva de la juventud.",
                    "techNote": "Esquema clásico a dos luces: principal difusa a 45° y luz de relleno tenue para conservar textura en sombras."
                },
                {
                    "id": 6,
                    "title": "Presencia y Soltura",
                    "category": "studio",
                    "categoryLabel": "Estudio / Retrato",
                    "date": "Octubre 2026",
                    "src": "galeria/foto6.JPG",
                    "description": "Retrato corporal en banco de estudio. Una postura relajada que proyecta seguridad y cercanía sin rigidez.",
                    "techNote": "Luz principal en tres cuartos modelando torso y extremidades; luz de recorte sutil para separar la silueta del fondo."
                },
                {
                    "id": 7,
                    "title": "Acorde y Concentración",
                    "category": "arte",
                    "categoryLabel": "Música & Arte",
                    "date": "2026",
                    "src": "galeria/guitarra.jpg",
                    "description": "Recital de guitarra clásica. Registro de la tensión expresiva de las manos sobre el diapasón y la resonancia de las cuerdas.",
                    "techNote": "Captura con luz escénica tenue; apertura amplia para aislar a la intérprete del fondo y velocidad precisa para congelar el rasgueo."
                },
                {
                    "id": 11,
                    "title": "Balcón Virreinal",
                    "category": "exterior",
                    "categoryLabel": "Exterior",
                    "date": "2026",
                    "src": "galeria/foto11.jpg",
                    "description": "Retrato ambiental en balcón del Centro Histórico de Querétaro. La cantera y la luz natural enmarcan la escena con rigor testimonial.",
                    "techNote": "Luz natural diurna rebotada en la fachada; exposición calibrada para preservar la textura de la cantera sin quemar el cielo."
                },
                {
                    "id": 12,
                    "title": "Snack & Empaque Comercial",
                    "category": "producto",
                    "categoryLabel": "Producto & Gastronomía",
                    "date": "Octubre 2026",
                    "src": "galeria/foto14.jpg",
                    "description": "Bodegón de producto sobre mesa de estudio. Control de texturas crujientes y saturación cromática de marca.",
                    "techNote": "Esquema cenital suave con luz principal difusa y rebote blanco lateral para rellenar sombras en el empaque."
                },
                {
                    "id": 13,
                    "title": "Snack & Empaque Comercial",
                    "category": "producto",
                    "categoryLabel": "Producto & Gastronomía",
                    "date": "Octubre 2026",
                    "src": "galeria/foto15.jpg",
                    "description": "Bodegón de producto sobre mesa de estudio. Control de texturas crujientes y saturación cromática de marca.",
                    "techNote": "Esquema cenital suave con luz principal difusa y rebote blanco lateral para rellenar sombras en el empaque."
                },
                {
                    "id": 14,
                    "title": "Snack & Empaque Comercial",
                    "category": "producto",
                    "categoryLabel": "Producto & Gastronomía",
                    "date": "Octubre 2026",
                    "src": "galeria/foto16.jpg",
                    "description": "Bodegón de producto sobre mesa de estudio. Control de texturas crujientes y saturación cromática de marca.",
                    "techNote": "Esquema cenital suave con luz principal difusa y rebote blanco lateral para rellenar sombras en el empaque."
                },
                {
                    "id": 26,
                    "title": "Retrato en Pareja en Exterior",
                    "category": "exterior",
                    "categoryLabel": "Retrato Exterior",
                    "date": "26 de marzo de 2026",
                    "src": "galeria/foto26.JPG",
                    "description": "Retrato ambiental en luz natural vespertina.",
                    "techNote": "Luz natural · Exterior"
                },
                {
                    "id": 27,
                    "title": "Retrato Ambiental Masculino",
                    "category": "exterior",
                    "categoryLabel": "Retrato Exterior",
                    "date": "26 de marzo de 2026",
                    "src": "galeria/foto27.JPG",
                    "description": "Plano entero en entorno urbano con iluminación de contraluz suave.",
                    "techNote": "Luz natural · Exterior"
                },
                {
                    "id": 28,
                    "title": "Retrato Femenino en Parque",
                    "category": "exterior",
                    "categoryLabel": "Retrato Exterior",
                    "date": "26 de marzo de 2026",
                    "src": "galeria/foto28.jpg",
                    "description": "Composición en plano entero aprovechando profundidad de campo en área verde.",
                    "techNote": "Luz natural · Exterior"
                },
                {
                    "id": 29,
                    "title": "Retrato Infantil Temático",
                    "category": "exterior",
                    "categoryLabel": "Retrato Exterior",
                    "date": "26 de marzo de 2026",
                    "src": "galeria/foto29.JPG",
                    "description": "Sesión temática en escalinata con luz directa y vestuario de personaje.",
                    "techNote": "Luz natural · Exterior"
                },
                {
                    "id": 30,
                    "title": "Plano Medio con Bokeh",
                    "category": "exterior",
                    "categoryLabel": "Retrato Exterior",
                    "date": "26 de marzo de 2026",
                    "src": "galeria/foto30.JPG",
                    "description": "Retrato en plano medio corto con compresión óptica y fondo vegetal desenfocado.",
                    "techNote": "Luz natural · Fondo difuminado"
                }
            ]    
            new_entries.append(entry)

        # Insertar todas al inicio para que aparezcan de primeras en la web
        data = new_entries + data

        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        messagebox.showinfo("Lote Completado", f"Se indexaron con éxito {total_photos} fotos en el catálogo.")
        self._reset_form()

    def _reset_form(self):
        self.selected_files = []
        self.lbl_count.config(text="0 fotos seleccionadas", fg="#737373")
        self.lst_preview.delete(0, tk.END)
        self.ent_title.delete(0, tk.END)
        self.txt_desc.delete("1.0", tk.END)

if __name__ == "__main__":
    app = StudioBatchManager()
    app.mainloop()
