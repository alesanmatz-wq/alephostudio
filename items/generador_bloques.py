import os
import sys
import json
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

# Persistencia local de borradores
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "catalogo_web.db")

CATEGORIAS = [
    ("studio", "Estudio / Retrato"),
    ("exterior", "Exterior"),
    ("producto", "Producto & Gastronomía"),
    ("arte", "Música & Arte"),
    ("archivo", "Archivo / Histórico")
]

class GeneradorBloquesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Alepho Studio — Generador de Bloques para index.html")
        self.geometry("1120x720")
        self.minsize(980, 640)
        self.configure(bg="#0d0d0f")

        self.current_edit_id = None
        self._init_db()
        self._setup_style()
        self._build_ui()
        self._cargar_registros()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fotos_web (
                    id_foto INTEGER PRIMARY KEY,
                    src TEXT NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    category_label TEXT NOT NULL,
                    fecha TEXT,
                    description TEXT,
                    tech_note TEXT
                )
            """)
            conn.commit()

    def _setup_style(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        bg_main = "#0d0d0f"
        bg_card = "#16181d"
        bg_input = "#1f2229"
        accent = "#c59b60"
        fg_text = "#e2e4e9"

        self.style.configure(".", background=bg_main, foreground=fg_text, font=("Segoe UI", 9))
        self.style.configure("TLabel", background=bg_card, foreground="#9ca3af")
        self.style.configure("Header.TLabel", background=bg_card, foreground=accent, font=("Georgia", 10, "bold"))
        self.style.configure("TEntry", fieldbackground=bg_input, foreground=fg_text, insertcolor=fg_text)
        self.style.configure("TCombobox", fieldbackground=bg_input, background=bg_card, foreground=fg_text)

        self.style.configure("Treeview", 
                             background="#121316", 
                             foreground=fg_text, 
                             fieldbackground="#121316",
                             rowheight=26,
                             font=("Segoe UI", 9))
        self.style.configure("Treeview.Heading", background="#1e2026", foreground=accent, font=("Segoe UI", 9, "bold"))
        self.style.map("Treeview", background=[("selected", "#2a2d36")])

        self.style.configure("Action.TButton", background=accent, foreground="#0d0d0f", font=("Segoe UI", 9, "bold"))
        self.style.map("Action.TButton", background=[("active", "#d8af74")])
        self.style.configure("Secondary.TButton", background="#262930", foreground=fg_text)
        self.style.map("Secondary.TButton", background=[("active", "#323640")])
        self.style.configure("Danger.TButton", background="#4a1e1e", foreground="#f87171")
        self.style.map("Danger.TButton", background=[("active", "#6b2828")])

    def _build_ui(self):
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # ==========================================
        # PANEL IZQUIERDO: FORMULARIO DE CAPTURA
        # ==========================================
        left = tk.Frame(paned, bg="#16181d", padx=16, pady=16)
        paned.add(left, weight=1)

        tk.Label(left, text="DATOS DE LA FOTOGRAFÍA", bg="#16181d", fg="#c59b60", font=("Georgia", 11, "bold")).pack(anchor="w", pady=(0, 10))

        # ID de la foto y Archivo de Imagen
        f_id_src = tk.Frame(left, bg="#16181d")
        f_id_src.pack(fill="x", pady=2)

        f_id = tk.Frame(f_id_src, bg="#16181d")
        f_id.pack(side="left", fill="x", padx=(0, 4))
        ttk.Label(f_id, text="ID numérico:").pack(anchor="w")
        self.ent_id = ttk.Entry(f_id, width=8)
        self.ent_id.pack(fill="x")

        f_src = tk.Frame(f_id_src, bg="#16181d")
        f_src.pack(side="right", fill="x", expand=True, padx=(4, 0))
        ttk.Label(f_src, text="Ruta relativa (ej. galeria/foto1.jpg):").pack(anchor="w")
        self.ent_src = ttk.Entry(f_src)
        self.ent_src.pack(fill="x")

        # Título
        ttk.Label(left, text="Título de la toma:").pack(anchor="w", pady=(6, 0))
        self.ent_title = ttk.Entry(left)
        self.ent_title.pack(fill="x", pady=(0, 4))

        # Categoría y Fecha
        f_meta = tk.Frame(left, bg="#16181d")
        f_meta.pack(fill="x", pady=4)

        f_cat = tk.Frame(f_meta, bg="#16181d")
        f_cat.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ttk.Label(f_cat, text="Categoría del filtro:").pack(anchor="w")
        cat_opciones = [f"{c[0]} — {c[1]}" for c in CATEGORIAS]
        self.cb_cat = ttk.Combobox(f_cat, values=cat_opciones, state="readonly")
        self.cb_cat.current(0)
        self.cb_cat.pack(fill="x")

        f_fec = tk.Frame(f_meta, bg="#16181d")
        f_fec.pack(side="right", fill="x", expand=True, padx=(4, 0))
        ttk.Label(f_fec, text="Fecha visual (ej. Octubre 2026):").pack(anchor="w")
        self.ent_fecha = ttk.Entry(f_fec)
        self.ent_fecha.insert(0, "Noviembre 2026")
        self.ent_fecha.pack(fill="x")

        # Descripción
        ttk.Label(left, text="Descripción breve:").pack(anchor="w", pady=(4, 0))
        self.txt_desc = tk.Text(left, height=3, bg="#1f2229", fg="#e2e4e9", relief="flat", insertbackground="white")
        self.txt_desc.pack(fill="x", pady=(0, 4))

        # Nota Técnica / Esquema
        ttk.Label(left, text="Nota Técnica / Esquema de iluminación:").pack(anchor="w", pady=(4, 0))
        self.txt_tech = tk.Text(left, height=3, bg="#1f2229", fg="#c59b60", relief="flat", insertbackground="white", font=("Consolas", 8))
        self.txt_tech.pack(fill="x", pady=(0, 8))

        # Botones de Formulario
        f_btns = tk.Frame(left, bg="#16181d")
        f_btns.pack(fill="x", pady=(6, 0))

        ttk.Button(f_btns, text="Guardar / Actualizar", style="Action.TButton", command=self._guardar_foto).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ttk.Button(f_btns, text="Limpiar", style="Secondary.TButton", command=self._limpiar_formulario).pack(side="right", padx=(4, 0))

        # ==========================================
        # PANEL DERECHO: CATÁLOGO Y VISOR DEL CHORIZO
        # ==========================================
        right = tk.Frame(paned, bg="#0d0d0f", padx=6, pady=6)
        paned.add(right, weight=2)

        # Tabla superior
        cols = ("id", "title", "category", "fecha", "src")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", selectmode="browse", height=9)
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Título")
        self.tree.heading("category", text="Categoría")
        self.tree.heading("fecha", text="Fecha")
        self.tree.heading("src", text="Ruta de Imagen")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("title", width=170)
        self.tree.column("category", width=90)
        self.tree.column("fecha", width=95)
        self.tree.column("src", width=140)

        self.tree.pack(fill="x", pady=(0, 6))
        self.tree.bind("<<TreeviewSelect>>", self._al_seleccionar_fila)

        # Botones de gestión rápida de fila
        f_tbl_act = tk.Frame(right, bg="#0d0d0f")
        f_tbl_act.pack(fill="x", pady=(0, 8))
        ttk.Button(f_tbl_act, text="Eliminar ID seleccionado", style="Danger.TButton", command=self._eliminar_foto).pack(side="left")
        ttk.Button(f_tbl_act, text="Generar Bloque JavaScript", style="Action.TButton", command=self._generar_bloque_js).pack(side="right")

        # Visor de Texto Plano de Salida
        tk.Label(right, text="SALIDA DE TEXTO PLANO LISTA PARA COPIAR EN INDEX.HTML:", bg="#0d0d0f", fg="#9ca3af", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(4, 2))
        
        self.txt_salida = tk.Text(right, bg="#121316", fg="#c59b60", insertbackground="white", font=("Consolas", 9), relief="flat")
        self.txt_salida.pack(fill="both", expand=True)

        # Barra inferior de copiado
        bot_bar = tk.Frame(right, bg="#0d0d0f")
        bot_bar.pack(fill="x", pady=(8, 0))
        ttk.Button(bot_bar, text="Copiar Todo al Portapapeles (Ctrl + C directo)", style="Action.TButton", command=self._copiar_portapapeles).pack(fill="x")

    def _sugerir_siguiente_id(self):
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT MAX(id_foto) FROM fotos_web")
            max_id = c.fetchone()[0]
            next_id = 1 if max_id is None else max_id + 1
            self.ent_id.delete(0, tk.END)
            self.ent_id.insert(0, str(next_id))
            self.ent_src.delete(0, tk.END)
            self.ent_src.insert(0, f"galeria/foto{next_id}.jpg")

    def _guardar_foto(self):
        id_str = self.ent_id.get().strip()
        src = self.ent_src.get().strip()
        title = self.ent_title.get().strip()
        fecha = self.ent_fecha.get().strip()
        desc = self.txt_desc.get("1.0", tk.END).strip()
        tech = self.txt_tech.get("1.0", tk.END).strip()

        if not id_str or not id_str.isdigit():
            messagebox.showwarning("Dato requerido", "Ingresa un ID numérico válido.")
            return
        if not title or not src:
            messagebox.showwarning("Dato requerido", "Indica al menos el Título y la Ruta relativa de la foto.")
            return

        cat_full = self.cb_cat.get()
        cat_slug = cat_full.split(" — ")[0]
        cat_label = cat_full.split(" — ")[1]
        fid = int(id_str)

        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO fotos_web (id_foto, src, title, category, category_label, fecha, description, tech_note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id_foto) DO UPDATE SET
                    src=excluded.src,
                    title=excluded.title,
                    category=excluded.category,
                    category_label=excluded.category_label,
                    fecha=excluded.fecha,
                    description=excluded.description,
                    tech_note=excluded.tech_note
            """, (fid, src, title, cat_slug, cat_label, fecha, desc, tech))
            conn.commit()

        self._cargar_registros()
        self._limpiar_formulario()
        self._generar_bloque_js()

    def _cargar_registros(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT id_foto, title, category, fecha, src FROM fotos_web ORDER BY id_foto ASC")
            for row in c.fetchall():
                self.tree.insert("", tk.END, values=row)

        if not self.current_edit_id:
            self._sugerir_siguiente_id()

    def _al_seleccionar_fila(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        valores = self.tree.item(sel[0], "values")
        if not valores:
            return
        fid = valores[0]
        self.current_edit_id = fid

        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM fotos_web WHERE id_foto = ?", (fid,))
            r = c.fetchone()
            if r:
                self.ent_id.delete(0, tk.END)
                self.ent_id.insert(0, str(r[0]))
                self.ent_src.delete(0, tk.END)
                self.ent_src.insert(0, r[1])
                self.ent_title.delete(0, tk.END)
                self.ent_title.insert(0, r[2])
                
                # Seleccionar la categoría en el combobox
                for idx, cat in enumerate(CATEGORIAS):
                    if cat[0] == r[3]:
                        self.cb_cat.current(idx)
                        break

                self.ent_fecha.delete(0, tk.END)
                self.ent_fecha.insert(0, r[5] or "")
                self.txt_desc.delete("1.0", tk.END)
                self.txt_desc.insert("1.0", r[6] or "")
                self.txt_tech.delete("1.0", tk.END)
                self.txt_tech.insert("1.0", r[7] or "")

    def _eliminar_foto(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona una foto de la lista para eliminar.")
            return
        fid = self.tree.item(sel[0], "values")[0]
        if messagebox.askyesno("Confirmar", f"¿Eliminar la foto ID #{fid} del catálogo web?"):
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("DELETE FROM fotos_web WHERE id_foto = ?", (fid,))
                conn.commit()
            self._cargar_registros()
            self._limpiar_formulario()
            self._generar_bloque_js()

    def _limpiar_formulario(self):
        self.current_edit_id = None
        self.ent_title.delete(0, tk.END)
        self.txt_desc.delete("1.0", tk.END)
        self.txt_tech.delete("1.0", tk.END)
        self._sugerir_siguiente_id()

    def _generar_bloque_js(self):
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT id_foto, src, title, category, category_label, fecha, description, tech_note FROM fotos_web ORDER BY id_foto ASC")
            filas = c.fetchall()

        if not filas:
            self.txt_salida.delete("1.0", tk.END)
            self.txt_salida.insert("1.0", "// No hay fotos capturadas aún en catalogo_web.db")
            return

        lineas = ["const galleryItems = ["]
        for r in filas:
            fid, src, tit, cat, cat_lbl, fec, desc, tech = r
            # Limpieza básica para evitar romper cadenas en JS
            desc_clean = (desc or "").replace('"', '\\"').replace('\n', ' ')
            tech_clean = (tech or "").replace('"', '\\"').replace('\n', ' ')
            tit_clean = tit.replace('"', '\\"')

            lineas.append("  {")
            lineas.append(f"    id: {fid},")
            lineas.append(f'    src: "{src}",')
            lineas.append(f'    title: "{tit_clean}",')
            lineas.append(f'    category: "{cat}",')
            lineas.append(f'    categoryLabel: "{cat_lbl}",')
            lineas.append(f'    date: "{fec}",')
            lineas.append(f'    description: "{desc_clean}",')
            lineas.append(f'    techNote: "{tech_clean}"')
            lineas.append("  },")
        lineas.append("];")

        texto_js = "\n".join(lineas)
        self.txt_salida.delete("1.0", tk.END)
        self.txt_salida.insert("1.0", texto_js)

    def _copiar_portapapeles(self):
        contenido = self.txt_salida.get("1.0", tk.END).strip()
        if not contenido or contenido.startswith("//"):
            messagebox.showwarning("Aviso", "No hay código generado para copiar.")
            return
        self.clipboard_clear()
        self.clipboard_append(contenido)
        self.update()
        messagebox.showinfo("Copiado", "¡Código JS copiado al portapapeles!\n\nListo para pegar (Ctrl+V) en tu index.html.")

if __name__ == "__main__":
    app = GeneradorBloquesApp()
    app.mainloop()
