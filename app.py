import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
import trimesh
from PIL import Image
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon


class MisiskiScadApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MisiskiScad - Modelador 3D Paramétrico para Bambu Studio")
        self.root.geometry("750x600")
        
        os.makedirs("exports", exist_ok=True)
        os.makedirs("assets", exist_ok=True)
        
        self.criar_interface()

    def criar_interface(self):
        titulo = tk.Label(self.root, text="MisiskiScad - Gerador de STL", font=("Arial", 16, "bold"))
        titulo.pack(pady=10)
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.aba_formas = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_formas, text="Formas & Tampas")
        self.setup_aba_formas()
        
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
        
        btn_converter = tk.Button(frame, text="Converter Imagem Real em STL 3D", bg="#2196F3", fg="white", font=("Arial", 11, "bold"), command=self.converter_imagem_para_stl)
        btn_converter.pack(pady=20)

    def carregar_imagem(self):
        file_path = filedialog.askopenfilename(filetypes=[("Imagens", "*.png *.jpg *.jpeg")])
        if file_path:
            self.caminho_imagem = file_path
            self.lbl_info_img.config(text=f"Selecionado: {os.path.basename(file_path)}")

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
                poly = Polygon(vertices_2d)
                mesh = trimesh.creation.extrude_polygon(poly, height=altura)
                nome_saida = f"exports/poligono_{lados}lados.stl"
            else:
                angulos = np.linspace(0, 2 * np.pi, lados, endpoint=False)
                ext_v = np.column_stack((medida * np.cos(angulos), medida * np.sin(angulos)))
                int_v = np.column_stack(((medida - 2) * np.cos(angulos), (medida - 2) * np.sin(angulos)))
                
                externo = trimesh.creation.extrude_polygon(Polygon(ext_v), height=2.0)
                borda = trimesh.creation.extrude_polygon(Polygon(int_v), height=altura)
                mesh = trimesh.util.concatenate([externo, borda])
                nome_saida = "exports/tampa_parametrica.stl"
                
            mesh.export(nome_saida)
            messagebox.showinfo("Sucesso", f"Arquivo gerado com sucesso!\nSalvo em: {nome_saida}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {str(e)}")

    def converter_imagem_para_stl(self):
        if not self.caminho_imagem:
            messagebox.showwarning("Aviso", "Por favor, selecione uma imagem primeiro.")
            return
        
        try:
            altura_extrusao = float(self.entry_altura_img.get())
            
            # Carrega a imagem, converte para escala de cinza e redimensiona
            img = Image.open(self.caminho_imagem).convert("L")
            img = img.resize((120, 120))
            pixels = np.array(img)
            
            # Máscara binária baseada no contraste
            mascara = pixels < 128
            if not np.any(mascara):
                mascara = pixels < 255

            y_indices, x_indices = np.where(mascara)
            pontos = np.column_stack((x_indices, y_indices))
            
            if len(pontos) < 3:
                messagebox.showerror("Erro", "A imagem é muito uniforme ou não foi possível detetar o formato.")
                return

            # Cria o contorno poligonal em volta da figura real da imagem
            hull = ConvexHull(pontos)
            vertices_contorno = pontos[hull.vertices]
            vertices_contorno = vertices_contorno - vertices_contorno.mean(axis=0)
            
            # Utiliza o Polygon do Shapely corretamente
            polygon_2d = Polygon(vertices_contorno)
            mesh = trimesh.creation.extrude_polygon(polygon_2d, height=altura_extrusao)
            
            nome_saida = "exports/imagem_customizada_3d.stl"
            mesh.export(nome_saida)
            
            messagebox.showinfo("Sucesso", f"Contorno da imagem convertido em STL real!\nSalvo em: {nome_saida}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao converter o formato da imagem: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MisiskiScadApp(root)
    root.mainloop()