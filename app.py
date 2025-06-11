# app.py
import os
import json
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, simpledialog
from tkinter.ttk import Combobox
from tkinterdnd2 import DND_FILES, TkinterDnD  # Soporte para Drag & Drop

# Nombre del fichero donde guardaremos la lista de clientes
FICHERO_CLIENTES = "clientes.json"

# Nueve sufijos: MAIN + PT01..PT08
SUFIJOS = ["MAIN", "PT01", "PT02", "PT03", "PT04", "PT05", "PT06", "PT07", "PT08"]


def cargar_clientes():
    if not os.path.exists(FICHERO_CLIENTES):
        return []
    try:
        with open(FICHERO_CLIENTES, "r", encoding="utf-8") as f:
            datos = json.load(f)
            if isinstance(datos, list) and all(isinstance(c, str) for c in datos):
                return datos
    except Exception:
        return []
    return []


def guardar_clientes(lista_clientes):
    try:
        with open(FICHERO_CLIENTES, "w", encoding="utf-8") as f:
            json.dump(lista_clientes, f, indent=2, ensure_ascii=False)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar la lista de clientes:\n{e}")


class RenombradorImágenes(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Herramienta de Renombrado de Imágenes para ASINs")
        self.geometry("700x620")
        self.resizable(False, False)

        self.imagenes_seleccionadas = []
        self.clientes = cargar_clientes()
        self.var_comprimir = tk.BooleanVar(value=False)

        self._crear_widgets()

    def _crear_widgets(self):
        tk.Label(self, text="Renombrar imágenes según ASINs", font=("Arial", 16, "bold")).pack(pady=10)

        frame_cliente = tk.Frame(self)
        frame_cliente.pack(pady=(0,10), fill="x", padx=20)
        tk.Label(frame_cliente, text="Cliente:", font=("Arial", 12)).pack(side="left")
        self.cmb_clientes = Combobox(frame_cliente, state="readonly", width=35, values=self.clientes)
        self.cmb_clientes.pack(side="left", padx=(10,5))
        if self.clientes: self.cmb_clientes.set(self.clientes[0])
        tk.Button(frame_cliente, text="Añadir cliente", command=self._añadir_cliente).pack(side="left", padx=(5,0))

        tk.Frame(self, height=2, bd=1, relief="sunken").pack(fill="x", padx=20, pady=(0,10))

        tk.Label(self, text="O arrastra aquí hasta 9 imágenes (nombres 1..9):", font=("Arial", 12)).pack()
        self.drop_area = tk.Label(self,
                                  text="(Arrastra entre 1 y 9 imágenes aquí)",
                                  relief="ridge", borderwidth=2,
                                  width=60, height=5,
                                  bg="#f0f0f0", fg="#555555",
                                  font=("Arial",10))
        self.drop_area.pack(pady=(5,10))
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind("<<Drop>>", self._drop)

        self.lbl_contador = tk.Label(self, text="Imágenes seleccionadas: 0/9", font=("Arial", 11))
        self.lbl_contador.pack(pady=(0,5))

        frame_botones = tk.Frame(self)
        frame_botones.pack(pady=(0,10))
        tk.Button(frame_botones, text="Seleccionar Imágenes (hasta 9 archivos)", command=self._seleccionar_imagenes).pack(side="left", padx=(0,10))
        tk.Button(frame_botones, text="Eliminar imágenes", fg="white", bg="#D9534F", command=self._eliminar_imagenes).pack(side="left")

        tk.Label(self, text="Pega aquí los ASINs (1 por línea):", font=("Arial",12)).pack(pady=(20,0))
        self.txt_asins = scrolledtext.ScrolledText(self, width=65, height=10)
        self.txt_asins.pack(pady=(5,10))

        tk.Checkbutton(self,
                       text="Comprimir por ASIN (cada carpeta de ASIN contendrá un ZIP)",
                       variable=self.var_comprimir,
                       font=("Arial",11)).pack(pady=(0,10))

        tk.Button(self,
                  text="Generar carpetas y renombrar",
                  fg="white", bg="#4CAF50",
                  font=("Arial",12,"bold"),
                  command=self._generar).pack(pady=10)

        self.lbl_estado = tk.Label(self, text="", fg="blue", font=("Arial",10))
        self.lbl_estado.pack(pady=(10,0))

    def _añadir_cliente(self):
        nuevo = simpledialog.askstring("Añadir Cliente", "Nombre del nuevo cliente:")
        if not nuevo: return
        nuevo = nuevo.strip()
        if not nuevo:
            messagebox.showwarning("Aviso","El nombre de cliente no puede estar vacío.")
            return
        if nuevo in self.clientes:
            messagebox.showwarning("Aviso",f"El cliente '{nuevo}' ya existe.")
            return
        self.clientes.append(nuevo)
        self.clientes.sort(key=lambda s:s.lower())
        guardar_clientes(self.clientes)
        self.cmb_clientes['values']=self.clientes
        self.cmb_clientes.set(nuevo)

    def _seleccionar_imagenes(self):
        rutas = filedialog.askopenfilenames(
            title="Selecciona entre 1 y 9 imágenes",
            filetypes=[("Archivos de imagen","*.jpg *.jpeg *.png *.bmp *.gif"),("Todos los archivos","*.*")]
        )
        if not rutas: return
        if len(rutas)>9:
            messagebox.showwarning("Selección incorrecta","Solo puedes seleccionar hasta 9 imágenes.")
            return
        validas=[r for r in rutas if os.path.splitext(r)[1].lower() in (".jpg",".jpeg",".png",".bmp",".gif")]
        if len(validas)!=len(rutas):
            messagebox.showwarning("Extensiones inválidas","Solo jpg/jpeg/png/bmp/gif.")
            return

        nombres=[os.path.splitext(os.path.basename(p))[0] for p in validas]
        if len(nombres)!=len(set(nombres)):
            messagebox.showwarning("Nombres duplicados","No pueden repetirse 1..9.")
            return
        for n in nombres:
            if n not in [str(i) for i in range(1,10)]:
                messagebox.showwarning("Nombres inválidos","Nombres base deben ser 1..9.")
                return
        self.imagenes_seleccionadas=validas
        self.lbl_contador.config(text=f"Imágenes seleccionadas: {len(validas)}/9")

    def _drop(self,event):
        rutas=self.tk.splitlist(event.data)
        if len(rutas)>9:
            messagebox.showwarning("Selec. incorrecta","Solo hasta 9 imágenes.")
            return
        imagenes=[p for p in rutas if os.path.splitext(p)[1].lower() in (".jpg",".jpeg",".png",".bmp",".gif")]
        nombres=[os.path.splitext(os.path.basename(p))[0] for p in imagenes]
        if len(nombres)!=len(set(nombres)):
            messagebox.showwarning("Nombres duplicados","No pueden repetirse 1..9.")
            return
        for n in nombres:
            if n not in [str(i) for i in range(1,10)]:
                messagebox.showwarning("Nombres inválidos","Nombres base deben ser 1..9.")
                return
        self.imagenes_seleccionadas=imagenes
        self.lbl_contador.config(text=f"Imágenes seleccionadas: {len(imagenes)}/9")

    def _eliminar_imagenes(self):
        self.imagenes_seleccionadas=[]
        self.lbl_contador.config(text="Imágenes seleccionadas: 0/9")
        self.drop_area.config(text="(Arrastra entre 1 y 9 imágenes aquí)")

    def _generar(self):
        cliente=self.cmb_clientes.get().strip()
        if not cliente:
            messagebox.showerror("Error","Selecciona o añade un cliente.")
            return
        if not self.imagenes_seleccionadas:
            messagebox.showerror("Error","Debes seleccionar al menos 1 imagen (hasta 9).")
            return
        contenido=self.txt_asins.get("1.0",tk.END).strip()
        if not contenido:
            messagebox.showerror("Error","La lista de ASINs está vacía.")
            return
        asins=[l.strip() for l in contenido.splitlines() if l.strip()]
        if not asins:
            messagebox.showerror("Error","No hay ASINs válidos.")
            return
        carpeta_base=filedialog.askdirectory(title="Selecciona carpeta donde crear carpeta del cliente")
        if not carpeta_base: return
        ruta_cliente=os.path.join(carpeta_base,cliente)
        try: os.makedirs(ruta_cliente,exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error",f"No se pudo crear carpeta del cliente:\n{e}")
            return

        total=len(asins)
        self.lbl_estado.config(text="Procesando...")
        self.update_idletasks()
        errores=[]
        dic_rutas={os.path.splitext(os.path.basename(p))[0]:p for p in self.imagenes_seleccionadas}

        for asin in asins:
            ruta_asin=os.path.join(ruta_cliente,asin)
            try: os.makedirs(ruta_asin,exist_ok=True)
            except Exception as e:
                errores.append(f"ASIN {asin}: no se pudo crear carpeta ({e}).")
                continue

            copiados=[]
            for i,suf in enumerate(SUFIJOS):
                clave=str(i+1)
                orig=dic_rutas.get(clave)
                if not orig: continue
                ext=os.path.splitext(orig)[1].lower()
                dest=os.path.join(ruta_asin,f"{asin}.{suf}{ext}")
                try:
                    shutil.copyfile(orig,dest)
                    copiados.append(dest)
                except Exception as e:
                    errores.append(f"ASIN {asin}, img {os.path.basename(orig)} fallo al copiar ({e}).")

            if self.var_comprimir.get():
                base_zip=os.path.join(ruta_asin,asin)
                try:
                    shutil.make_archive(base_zip,'zip',root_dir=ruta_asin)
                    for f in copiados:
                        try: os.remove(f)
                        except: pass
                except Exception as e:
                    errores.append(f"ASIN {asin}: fallo al comprimir ({e}).")

        if errores:
            messagebox.showwarning("Errores","Algunos errores ocurrieron:\n\n"+ "\n".join(errores))
        else:
            msg=f"Se procesaron {total} ASIN(s) para '{cliente}'."
            if self.var_comprimir.get():
                msg+="\nCada carpeta de ASIN tiene su ZIP."
            messagebox.showinfo("Éxito",msg)

        self.lbl_estado.config(text="")


if __name__ == "__main__":
    app=RenombradorImágenes()
    app.mainloop()
