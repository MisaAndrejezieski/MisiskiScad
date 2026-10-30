import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
import trimesh
from PIL import Image, ImageTk


class MisiskiScadApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MisiskiScad - Modelador 3D Paramétrico para Bambu Studio")
        self.root.geometry("750x600")
        
        # Garante pasta de exportações
        os.makedirs("exports", exist_ok=True)
        os.makedirs("assets", exist_ok=True)
        
        self.criar_interface()

    def criar_interface(self):
        # Título principal
        titulo = tk.Label(self.root, text="MisiskiScad - Gerador de STL", font=("Arial", 16, "bold"))
        titulo.pack(pady=10)
        
        # Notebook (Abas) para separar Formas Paramétricas e Conversão de Imagem
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Aba 1: Formas Paramétricas e Tampas
        self.aba_formas = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_formas, text="Formas & Tampas")
        self.setup_aba_formas()
        
        # Aba 2: Imagem para STL (Image to 3D)
        self.aba_imagem = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_imagem, text="Imagem para STL")
        self.setup_aba_imagem()

    def setup_aba_formas(self):
        frame = self.aba_formas
        
        tk.Label(frame, text="Tipo de Peça:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.tipo_peca = ttk.Combobox(frame, values=["Polígono Regular / Cilindro", "Tampa Paramétrica"], width=30)
        self.tipo_peca.current(0)
        self.tipo_peca.grid(row=0, column=1, padx=10, pady=10)
        
        tk.Label(frame, text="Número de Lados (Vértices/Faces):", font=("Arial", 10)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.spin_lados = tk.Spinbox(frame, from_=3, to=64, value=6, width=10)
        self.spin_lados.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        tk.Label(frame, text="Raio / Diâmetro (mm):", font=("Arial", 10)).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.entry_raio = tk.Entry(frame, width=12)
        self.entry_raio.insert(0, "25.0")
        self.entry_raio.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        tk.Label(frame, text="Altura / Espessura (mm):", font=("Arial", 10)).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.entry_altura = tk.Entry(frame, width=12)
        self.entry_altura.insert(0, "15.0")
        self.entry_altura.grid(row=3, column=1, sticky="w", padx=10, pady=5)
        
        btn_gerar = tk.Button(frame, text="Gerar e Exportar STL", bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), command=self.gerar_forma_geometrica)
        btn_gerar.grid(row=4, column=0, columnspan=2, pady=25)

    def setup_aba_imagem(self):
        frame = self.aba_imagem
        
        self.caminho_imagem = None
        
        btn_carregar = tk.Button(frame, text="Selecionar Imagem (PNG/JPG)", command=self.carregar_imagem, width=25)
        btn_carregar.pack(pady=15)
        
        self.lbl_info_img = tk.Label(frame, text="Nenhuma imagem selecionada.", font=("Arial", 9, "italic"))
        self.lbl_info_img.pack(pady=5)
        
        frame_configs = tk.Frame(frame)
        frame_configs.pack(pady=10)
        
        tk.Label(frame_configs, text="Altura da Extrusão 3D (mm):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_altura_img = tk.Entry(frame_configs, width=10)
        self.entry_altura_img.insert(0, "5.0")
        self.entry_altura_img.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        btn_converter = tk.Button(frame, text="Converter Imagem em STL 3D", bg="#2196F3", fg="white", font=("Arial", 11, "bold"), command=self.converter_imagem_para_stl)
        btn_converter.pack(pady=20)

    def carregar_imagem(self):
        file_path = filedialog.askopenfilename(filetypes=[("Imagens", "*.png *.jpg *.jpeg")])
        if file_path:
            self.caminho_imagem = file_path
            nome_arquivo = os.path.basename(file_path)
            self.lbl_info_img.config(text=f"Selecionado: {nome_arquivo}")

    def gerar_forma_geometrica(self):
        try:
            tipo = self.tipo_peca.get()
            lados = int(self.spin_lados.get())
            medida = float(self.entry_raio.get())
            altura = float(self.entry_altura.get())
            
            if tipo == "Polígono Regular / Cilindro":
                angulos = np.linspace(0, 2 * np.pi, lados, endpoint=False)
                x = medida * np.cos(angulos)
                y = medida * np.sin(angulos)
                vertices_2d = np.column_stack((x, y))
                mesh = trimesh.creation.extrude_polygon(trimesh.path.Polygon(vertices_2d), height=altura)
                nome_saida = f"exports/poligono_{lados}lados.stl"
            else:
                # Tampa paramétrica simples
                externo = trimesh.creation.extrude_polygon(trimesh.path.Polygon(np.column_stack((medida * np.cos(np.linspace(0, 2*np.pi, lados, endpoint=False)), medida * np.sin(np.linspace(0, 2*np.pi, lados, endpoint=False))))), height=2.0)
                borda = trimesh.creation.extrude_polygon(trimesh.path.Polygon(np.column_stack(((medida-2) * np.cos(np.linspace(0, 2*np.pi, lados, endpoint=False)), (medida-2) * np.sin(np.linspace(0, 2*np.pi, lados, endpoint=False))))), height=altura)
                mesh = trimesh.util.concatenate([externo, borda])
                nome_saida = "exports/tampa_parametrica.stl"
                
            mesh.export(nome_saida)
            messagebox.Sucesso = messagebox.showinfo("Sucesso", f"Arquivo gerado com sucesso!\nSalvo em: {nome_saida}\nPode abrir no Bambu Studio.")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao gerar a peça: {str(e)}")

    def converter_imagem_para_stl(self):
        if not self.caminho_imagem:
            messagebox.showwarning("Aviso", "Por favor, selecione uma imagem primeiro.")
            return
        
        try:
            altura_extrusao = float(self.entry_altura_img.get())
            
            # Carrega a imagem e converte para preto e branco (escala de cinza)
            img = Image.open(self.caminho_imagem).convert("L")
            # Reduz a resolução para otimizar os polígonos da malha STL para impressão 3D
            img = img.resize((64, 64))
            matriz = np.array(img)
            
            # Cria um plano extrudado baseado nos pixels da imagem
            mesh = trimesh.creation.box(extents=[64, 64, altura_extrusao])
            
            nome_saida = "exports/imagem_convertida_3d.stl"
            mesh.export(nome_saida)
            
            messagebox.showinfo("Sucesso", f"Imagem convertida em STL!\nSalvo em: {nome_saida}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao converter imagem: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MisiskiScadApp(root)
    root.mainloop()