import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
import trimesh
from PIL import Image


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
        frame = self.aba_img
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
        tk.Label(frame, text="Aqui você pode aplicar modificações matemáticas diretas na última peça gerada.", font=("Arial", 9)).pack(pady=5)
        
        f_info = tk.Frame(frame)
        f_info.pack(pady=15)
        
        self.lbl_stats = tk.Label(f_info, text="Nenhuma malha ativa na memória.", font=("Arial", 10), fg="gray")
        self.lbl_stats.pack()
        
        f_trans = tk.LabelFrame(frame, text=" Operações Geométricas em Lote ", font=("Arial", 10, "bold"))
        f_trans.pack(fill="x", padx=20, pady=10)
        
        btn_escala = tk.Button(f_trans, text="Esticar Eixo Z (Altura x1.5)", command=lambda: self.modificar_malha("escala_z"), width=25)
        btn_escala.pack(pady=5)
        
        btn_centralizar = tk.Button(f_trans, text="Centralizar Origem (0,0,0)", command=lambda: self.modificar_malha("centro"), width=25)
        btn_centralizar.pack(pady=5)
        
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
            # Manipulação direta dos vértices no eixo Z
            self.current_mesh.vertices[:, 2] *= 1.5
            messagebox.Info = messagebox.showinfo("Editado", "Altura dos vértices (Z) multiplicada por 1.5!")
        elif operacao == "centro":
            self.current_mesh.apply_translation(-self.current_mesh.centroid)
            messagebox.showinfo("Editado", "Malha centralizada na origem (0,0,0)!")
            
        self.atualizar_stats_interface()

    def salvar_malha_atual(self):
        if self.current_mesh is None:
            messagebox.showwarning("Aviso", "Nenhuma malha para salvar.")
            return
        caminho = "exports/malha_editada_customizada.stl"
        self.current_mesh.export(caminho)
        messagebox.showinfo("Salvo", f"Arquivo editado exportado com sucesso para:\n{caminho}")

    def atualizar_stats_interface(self):
        if self.current_mesh:
            v_count = len(self.current_mesh.vertices)
            f_count = len(self.current_mesh.faces)
            self.lbl_stats.config(text=f"Vértices: {v_count} | Faces (Triângulos): {f_count}", fg="blue")

if __name__ == "__main__":
    root = tk.Tk()
    app = MisiskiScadApp(root)
    root.mainloop()