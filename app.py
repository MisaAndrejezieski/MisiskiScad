import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
import trimesh
from PIL import Image

from visual_hull import VIEW_NAMES, reconstruct_visual_hull


class MisiskiScadApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MisiskiScad - Modelador Paramétrico & Conversor 3D")
        self.root.geometry("800x650")
        
        os.makedirs("exports", exist_ok=True)
        self.current_mesh = None  # Armazena a malha atual para edição de vértices/faces
        
        self.criar_interface()

    def criar_interface(self):
        titulo = tk.Label(self.root, text="MisiskiScad - Estúdio de Modelagem 3D", font=("Arial", 16, "bold"))
        titulo.pack(pady=10)
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Abas
        self.aba_img = ttk.Frame(self.notebook)
        self.aba_formas = ttk.Frame(self.notebook)
        self.aba_editar = ttk.Frame(self.notebook)
        
        self.notebook.add(self.aba_img, text="1. Imagem para STL")
        self.notebook.add(self.aba_formas, text="2. Formas Paramétricas")
        self.notebook.add(self.aba_editar, text="3. Manipular Vértices/Faces")
        
        self.setup_aba_imagem()
        self.setup_aba_formas()
        self.setup_aba_editar()

    def setup_aba_imagem(self):
        image_tabs = ttk.Notebook(self.aba_img)
        image_tabs.pack(fill="both", expand=True, padx=8, pady=8)

        self.aba_seis_vistas = ttk.Frame(image_tabs)
        self.aba_relevo = ttk.Frame(image_tabs)
        image_tabs.add(self.aba_seis_vistas, text="Reconstrução por 6 vistas")
        image_tabs.add(self.aba_relevo, text="Relevo de uma imagem")

        self.setup_aba_seis_vistas(self.aba_seis_vistas)
        self.setup_aba_relevo(self.aba_relevo)

    def setup_aba_seis_vistas(self, frame):
        self.imagens_vistas = {}
        tk.Label(
            frame,
            text="Selecione seis fotos ortográficas do mesmo objeto",
            font=("Arial", 12, "bold"),
        ).pack(pady=(12, 4))
        tk.Label(
            frame,
            text="Use fundo uniforme, objeto centralizado e topo sempre para cima. "
            "Vistas opostas devem manter a mesma escala. Direções: frente/trás, "
            "esquerda/direita e cima/baixo.",
            wraplength=680,
            justify="center",
        ).pack(pady=(0, 10))

        views_frame = tk.LabelFrame(frame, text="Imagens")
        views_frame.pack(fill="x", padx=20, pady=5)
        for row, name in enumerate(VIEW_NAMES):
            tk.Label(views_frame, text=name.capitalize() + ":").grid(
                row=row, column=0, sticky="w", padx=8, pady=3
            )
            button = tk.Button(
                views_frame,
                text="Selecionar imagem...",
                command=lambda view=name: self.selecionar_vista(view),
                width=20,
            )
            button.grid(row=row, column=1, padx=6, pady=3)
            label = tk.Label(views_frame, text="Não selecionada", anchor="w")
            label.grid(row=row, column=2, sticky="ew", padx=6, pady=3)
            self.imagens_vistas[name] = {"path": None, "label": label}
        views_frame.columnconfigure(2, weight=1)

        dimensions = ttk.LabelFrame(frame, text="Dimensões finais aproximadas (mm)")
        dimensions.pack(fill="x", padx=20, pady=8)
        self.dimension_entries = {}
        for column, (key, title, initial) in enumerate(
            (("width", "Largura X", "50"), ("depth", "Profundidade Y", "50"), ("height", "Altura Z", "50"))
        ):
            tk.Label(dimensions, text=title + ":").grid(
                row=0, column=column * 2, padx=6, pady=8
            )
            entry = tk.Entry(dimensions, width=9)
            entry.insert(0, initial)
            entry.grid(row=0, column=column * 2 + 1, padx=6, pady=8)
            self.dimension_entries[key] = entry

        settings = ttk.Frame(frame)
        settings.pack(fill="x", padx=20, pady=3)
        tk.Label(settings, text="Resolução (maior eixo):").pack(side="left")
        self.resolution_entry = tk.Spinbox(
            settings, from_=16, to=128, increment=8, width=6
        )
        self.resolution_entry.delete(0, "end")
        self.resolution_entry.insert(0, "64")
        self.resolution_entry.pack(side="left", padx=(5, 16))
        tk.Label(settings, text="Limiar do fundo (1–255):").pack(side="left")
        self.threshold_entry = tk.Spinbox(
            settings, from_=1, to=255, increment=5, width=6
        )
        self.threshold_entry.delete(0, "end")
        self.threshold_entry.insert(0, "30")
        self.threshold_entry.pack(side="left", padx=5)

        tk.Button(
            frame,
            text="Reconstruir modelo 3D e salvar STL...",
            command=self.reconstruir_seis_vistas,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 11, "bold"),
        ).pack(pady=12)
        tk.Label(
            frame,
            text="Aviso: o casco visual estima o volume externo; não recupera cavidades "
            "ou detalhes ocultos. A malha gerada é editável por escala e transformação.",
            wraplength=700,
            justify="center",
            fg="#555555",
        ).pack(padx=16, pady=(0, 8))

    def setup_aba_relevo(self, frame):
        self.caminho_imagem = None
        
        btn_carregar = tk.Button(frame, text="Carregar Imagem (PNG/JPG)", command=self.carregar_imagem, width=30, bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
        btn_carregar.pack(pady=20)
        
        self.lbl_img = tk.Label(frame, text="Nenhuma imagem selecionada.", font=("Arial", 9, "italic"))
        self.lbl_img.pack(pady=5)
        
        f_cfg = tk.LabelFrame(frame, text=" Configurações de Extrusão ", font=("Arial", 10, "bold"))
        f_cfg.pack(fill="x", padx=20, pady=15)
        
        tk.Label(f_cfg, text="Altura / Espessura 3D (mm):").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.ent_alt_img = tk.Entry(f_cfg, width=10)
        self.ent_alt_img.insert(0, "10.0")
        self.ent_alt_img.grid(row=0, column=1, padx=10, pady=10)
        
        btn_conv = tk.Button(frame, text="Converter Imagem em 3D e Salvar STL", command=self.converter_imagem_3d, bg="#4CAF50", fg="white", font=("Arial", 11, "bold"))
        btn_conv.pack(pady=20)

    def selecionar_vista(self, view):
        path = filedialog.askopenfilename(
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff")]
        )
        if path:
            self.imagens_vistas[view]["path"] = path
            self.imagens_vistas[view]["label"].config(text=os.path.basename(path))

    def reconstruir_seis_vistas(self):
        image_paths = {
            name: selection["path"] for name, selection in self.imagens_vistas.items()
        }
        missing = [name for name, path in image_paths.items() if not path]
        if missing:
            messagebox.showwarning(
                "Imagens faltando",
                "Selecione as seis vistas: " + ", ".join(missing) + ".",
            )
            return

        output_path = filedialog.asksaveasfilename(
            title="Salvar modelo reconstruído",
            initialdir="exports",
            initialfile="modelo_6_vistas.stl",
            defaultextension=".stl",
            filetypes=[("Modelo STL", "*.stl")],
        )
        if not output_path:
            return

        try:
            dimensions = {
                name: float(entry.get())
                for name, entry in self.dimension_entries.items()
            }
            mesh, grid_shape = reconstruct_visual_hull(
                image_paths,
                dimensions["width"],
                dimensions["depth"],
                dimensions["height"],
                resolution=int(self.resolution_entry.get()),
                threshold=int(self.threshold_entry.get()),
            )
            mesh.export(output_path)
            self.current_mesh = mesh
            self.atualizar_stats_interface()
            self.notebook.select(self.aba_editar)
            messagebox.showinfo(
                "Modelo criado",
                f"Malha reconstruída e salva em:\n{output_path}\n\n"
                f"Grade: {grid_shape[0]} × {grid_shape[1]} × {grid_shape[2]} voxels\n"
                f"Vértices: {len(mesh.vertices)} | Faces: {len(mesh.faces)}",
            )
        except (OSError, ValueError, RuntimeError) as error:
            messagebox.showerror("Erro na reconstrução", str(error))

    def setup_aba_formas(self):
        frame = self.aba_formas
        
        tk.Label(frame, text="Selecione a Forma Base:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=15, pady=15)
        self.combo_forma = ttk.Combobox(frame, values=["Cilindro / Polígono Customizável", "Tampa Paramétrica de Encaixe"], width=35)
        self.combo_forma.current(0)
        self.combo_forma.grid(row=0, column=1, padx=15, pady=15)
        
        tk.Label(frame, text="Número de Lados (Faces/Arestas):", font=("Arial", 10)).grid(row=1, column=0, sticky="w", padx=15, pady=10)
        self.sp_lados = tk.Spinbox(frame, from_=3, to=64, value=32, width=10)
        self.sp_lados.grid(row=1, column=1, sticky="w", padx=15, pady=10)
        
        tk.Label(frame, text="Raio / Diâmetro (mm):", font=("Arial", 10)).grid(row=2, column=0, sticky="w", padx=15, pady=10)
        self.ent_raio = tk.Entry(frame, width=12)
        self.ent_raio.insert(0, "25.0")
        self.ent_raio.grid(row=2, column=1, sticky="w", padx=15, pady=10)
        
        tk.Label(frame, text="Altura (mm):", font=("Arial", 10)).grid(row=3, column=0, sticky="w", padx=15, pady=10)
        self.ent_alt = tk.Entry(frame, width=12)
        self.ent_alt.insert(0, "20.0")
        self.ent_alt.grid(row=3, column=1, sticky="w", padx=15, pady=10)
        
        btn_f = tk.Button(frame, text="Gerar e Salvar STL Paramétrico", command=self.gerar_forma, bg="#4CAF50", fg="white", font=("Arial", 11, "bold"))
        btn_f.grid(row=4, column=0, columnspan=2, pady=25)

    def setup_aba_editar(self):
        frame = self.aba_editar
        
        tk.Label(frame, text="Manipulação Direta de Malha (Vértices e Faces)", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(frame, text="Ajuste as dimensões da malha ativa ou abra um STL existente.", font=("Arial", 9)).pack(pady=5)
        
        f_info = tk.Frame(frame)
        f_info.pack(pady=15)
        
        self.lbl_stats = tk.Label(f_info, text="Nenhuma malha ativa na memória.", font=("Arial", 10), fg="gray")
        self.lbl_stats.pack()
        
        f_trans = tk.LabelFrame(frame, text=" Definir dimensões finais (mm) ", font=("Arial", 10, "bold"))
        f_trans.pack(fill="x", padx=20, pady=10)
        self.edit_dimension_entries = {}
        for column, (key, title) in enumerate(
            (("width", "Largura X"), ("depth", "Profundidade Y"), ("height", "Altura Z"))
        ):
            tk.Label(f_trans, text=title + ":").grid(
                row=0, column=column * 2, padx=6, pady=8
            )
            entry = tk.Entry(f_trans, width=9)
            entry.grid(row=0, column=column * 2 + 1, padx=6, pady=8)
            self.edit_dimension_entries[key] = entry

        tk.Button(
            f_trans,
            text="Aplicar dimensões",
            command=self.aplicar_dimensoes_malha,
        ).grid(row=1, column=0, columnspan=6, pady=6)
        
        btn_centralizar = tk.Button(f_trans, text="Centralizar Origem (0,0,0)", command=lambda: self.modificar_malha("centro"), width=25)
        btn_centralizar.grid(row=2, column=0, columnspan=6, pady=5)

        tk.Button(
            frame,
            text="Abrir malha STL para edição...",
            command=self.carregar_malha_stl,
        ).pack(pady=8)
        
        btn_salvar_edit = tk.Button(frame, text="Exportar Malha Editada para .stl", command=self.salvar_malha_atual, bg="#FF9800", fg="white", font=("Arial", 11, "bold"))
        btn_salvar_edit.pack(pady=20)

    def carregar_imagem(self):
        path = filedialog.askopenfilename(filetypes=[("Imagens", "*.png *.jpg *.jpeg")])
        if path:
            self.caminho_imagem = path
            self.lbl_img.config(text=f"Selecionado: {os.path.basename(path)}")

    def converter_imagem_3d(self):
        if not self.caminho_imagem:
            messagebox.showwarning("Aviso", "Selecione uma imagem primeiro.")
            return
        try:
            altura = float(self.ent_alt_img.get())
            
            # Carrega a imagem e converte em matriz binária robusta
            img = Image.open(self.caminho_imagem).convert("L")
            img = img.resize((80, 80)) # Resolução ideal para 3D sem pesar
            arr = np.array(img) < 128  # Pixels escuros viram relevo
            
            # Criação de malha via voxel grid (100% livre de erros de triangulação)
            voxel_array = np.zeros((*arr.shape, int(altura)), dtype=bool)
            for z in range(int(altura)):
                voxel_array[:, :, z] = arr
                
            grid = trimesh.voxel.VoxelGrid(voxel_array)
            mesh = grid.as_boxes()
            
            self.current_mesh = mesh
            caminho_saida = "exports/modelo_de_imagem.stl"
            mesh.export(caminho_saida)
            
            self.atualizar_stats_interface()
            messagebox.showinfo("Sucesso", f"Imagem convertida com sucesso!\nSalvo em: {caminho_saida}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao processar imagem: {str(e)}")

    def gerar_forma(self):
        try:
            tipo = self.combo_forma.get()
            lados = int(self.sp_lados.get())
            raio = float(self.ent_raio.get())
            altura = float(self.ent_alt.get())
            
            if "Cilindro" in tipo:
                mesh = trimesh.creation.cylinder(radius=raio, height=altura, sections=lados)
                nome = f"exports/cilindro_{lados}lados.stl"
            else:
                # Tampa paramétrica combinada
                tampa_topo = trimesh.creation.cylinder(radius=raio, height=3.0, sections=lados)
                encaixe = trimesh.creation.cylinder(radius=raio-2.0, height=altura, sections=lados)
                encaixe.apply_translation([0, 0, altura/2 + 1.5])
                mesh = trimesh.util.concatenate([tampa_topo, encaixe])
                nome = "exports/tampa_parametrica.stl"
                
            self.current_mesh = mesh
            mesh.export(nome)
            self.atualizar_stats_interface()
            messagebox.showinfo("Sucesso", f"Peça gerada com sucesso!\nSalvo em: {nome}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar forma: {str(e)}")

    def modificar_malha(self, operacao):
        if self.current_mesh is None:
            messagebox.showwarning("Aviso", "Nenhuma peça carregada na memória para editar.")
            return
        
        if operacao == "escala_z":
            self.current_mesh.vertices[:, 2] *= 1.5
            messagebox.showinfo("Editado", "Altura dos vértices (Z) multiplicada por 1.5!")
        elif operacao == "centro":
            self.current_mesh.apply_translation(-self.current_mesh.centroid)
            messagebox.showinfo("Editado", "Malha centralizada na origem (0,0,0)!")
            
        self.atualizar_stats_interface()

    def aplicar_dimensoes_malha(self):
        if self.current_mesh is None:
            messagebox.showwarning("Aviso", "Nenhuma malha carregada para editar.")
            return
        try:
            target = np.array(
                [float(self.edit_dimension_entries[key].get()) for key in ("width", "depth", "height")]
            )
            current = self.current_mesh.extents
            if not np.all(np.isfinite(target)) or np.any(target <= 0) or np.any(current <= 0):
                raise ValueError("As dimensões precisam ser maiores que zero.")
            scale = target / current
            bounds = self.current_mesh.bounds
            center = bounds.mean(axis=0)
            vertices = self.current_mesh.vertices.copy()
            vertices[:, :2] = (vertices[:, :2] - center[:2]) * scale[:2] + center[:2]
            vertices[:, 2] = (vertices[:, 2] - bounds[0, 2]) * scale[2] + bounds[0, 2]
            self.current_mesh.vertices = vertices
            self.current_mesh.fix_normals()
            self.atualizar_stats_interface()
        except ValueError as error:
            messagebox.showerror("Dimensões inválidas", str(error))

    def carregar_malha_stl(self):
        path = filedialog.askopenfilename(
            filetypes=[("Malhas STL", "*.stl")]
        )
        if not path:
            return
        try:
            mesh = trimesh.load_mesh(path, file_type="stl", process=True)
            if mesh.is_empty or len(mesh.faces) == 0:
                raise ValueError("O arquivo não contém uma malha STL válida.")
            self.current_mesh = mesh
            self.atualizar_stats_interface()
            messagebox.showinfo("Malha carregada", f"Malha aberta para edição:\n{path}")
        except (OSError, ValueError, TypeError, IndexError) as error:
            messagebox.showerror("Erro ao abrir STL", str(error))

    def salvar_malha_atual(self):
        if self.current_mesh is None:
            messagebox.showwarning("Aviso", "Nenhuma malha para salvar.")
            return
        caminho = filedialog.asksaveasfilename(
            title="Exportar malha editada",
            initialdir="exports",
            initialfile="malha_editada.stl",
            defaultextension=".stl",
            filetypes=[("Modelo STL", "*.stl")],
        )
        if not caminho:
            return
        try:
            self.current_mesh.export(caminho)
        except (OSError, ValueError, TypeError, ImportError) as error:
            messagebox.showerror("Erro ao salvar STL", str(error))
            return
        messagebox.showinfo("Salvo", f"Arquivo editado exportado com sucesso para:\n{caminho}")

    def atualizar_stats_interface(self):
        if self.current_mesh is not None:
            v_count = len(self.current_mesh.vertices)
            f_count = len(self.current_mesh.faces)
            bounds = self.current_mesh.extents
            self.lbl_stats.config(
                text=f"Vértices: {v_count} | Faces: {f_count} | "
                f"Dimensões: {bounds[0]:.1f} × {bounds[1]:.1f} × {bounds[2]:.1f} mm",
                fg="blue",
            )

if __name__ == "__main__":
    root = tk.Tk()
    app = MisiskiScadApp(root)
    root.mainloop()