import os

import numpy as np
import trimesh
from PIL import Image
from scipy.spatial import Delaunay


class MisiskiScadCore:
    """
    Motor lógico de CAD paramétrico do MisiskiScad.
    Permite criar formas, converter imagens 2D em 3D, e manipular diretamente
    vértices, arestas e faces de qualquer figura.
    """
    def __init__(self, output_dir="exports"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def criar_forma_parametrica(self, raio=20.0, altura=15.0, lados=6):
        """
        Cria um polígono/cilindro base onde você controla o número exato 
        de faces, arestas e vértices.
        """
        # Gera os ângulos baseados no número de lados (lados = arestas/faces verticais)
        angulos = np.linspace(0, 2 * np.pi, lados, endpoint=False)
        x = raio * np.cos(angulos)
        y = raio * np.sin(angulos)
        pts_2d = np.column_stack((x, y))
        
        # Triangulação e extrusão tridimensional matemática direta
        tri = Delaunay(pts_2d)
        faces_2d = tri.simplices
        n = len(pts_2d)

        verts_bottom = np.column_stack((pts_2d, np.zeros(n)))
        verts_top = np.column_stack((pts_2d, np.full(n, altura)))
        vertices_3d = np.vstack((verts_bottom, verts_top))

        faces = []
        # Faces inferiores
        for f in faces_2d:
            faces.append([f[0], f[2], f[1]])
        # Faces superiores
        for f in faces_2d:
            faces.append([f[0] + n, f[1] + n, f[2] + n])
        # Paredes laterais (arestas e faces laterais)
        for i in range(n):
            next_i = (i + 1) % n
            faces.append([i, next_i, next_i + n])
            faces.append([i, next_i + n, i + n])

        mesh = trimesh.Trimesh(vertices=vertices_3d, faces=faces)
        return mesh

    def imagem_para_3d(self, caminho_imagem, altura_extrusao=10.0, resolucao=90):
        """
        Lógica para ler uma imagem 2D (logotipo, desenho ou silhueta) 
        e transformá-la num objeto sólido 3D (.stl).
        """
        img = Image.open(caminho_imagem).convert("L").resize((resolucao, resolucao))
        arr = np.array(img) < 128  # Converte pixels escuros em geometria sólida
        
        # Constrói malha volumétrica (voxel grid) livre de erros de malha aberta
        voxel_array = np.zeros((*arr.shape, int(altura_extrusao)), dtype=bool)
        for z in range(int(altura_extrusao)):
            voxel_array[:, :, z] = arr
            
        grid = trimesh.voxel.VoxelGrid(voxel_array)
        mesh = grid.as_boxes()
        return mesh

    def manipular_malha(self, mesh, operacao="escala_z", fator=1.5):
        """
        Manipulação direta da estrutura geométrica (Vértices e Faces).
        Permite deformações, esticar e ajustar proporções de qualquer peça.
        """
        if operacao == "escala_z":
            # Manipula diretamente a matriz de coordenadas Z de todos os vértices
            mesh.vertices[:, 2] *= fator
        elif operacao == "centralizar":
            mesh.apply_translation(-mesh.centroid)
        elif operacao == "rotacionar_x":
            matrix = trimesh.transformations.rotation_matrix(np.radians(fator), [1, 0, 0])
            mesh.apply_transform(matrix)
        
        # Atualiza as normais após manipular os vértices
        mesh.fix_normals()
        return mesh

    def gerar_manequim_humanoide(self):
        """
        Gera a estrutura de um manequim humanoide articulado utilizando primitivas 
        e blocos modulares estruturados para customização.
        """
        partes = []
        
        # Cabeça
        cabeca = trimesh.creation.icosphere(subdivisions=2, radius=6.0)
        cabeca.apply_translation([0, 0, 60.0])
        partes.append(cabeca)

        # Tronco
        tronco = trimesh.creation.box(extents=[16.0, 10.0, 24.0])
        tronco.apply_translation([0, 0, 38.0])
        partes.append(tronco)

        # Membros (Braços e Pernas paramétricos)
        for lado in [-1, 1]:
            braco = trimesh.creation.cylinder(radius=2.2, height=20.0, sections=12)
            braco.apply_translation([lado * 11.0, 0, 35.0])
            partes.append(braco)

            perna = trimesh.creation.cylinder(radius=2.8, height=25.0, sections=12)
            perna.apply_translation([lado * 5.5, 0, 10.0])
            partes.append(perna)

        manequim = trimesh.util.concatenate(partes)
        return manequim

    def exportar_stl(self, mesh, nome_arquivo):
        """Salva a malha final em formato .stl pronto para o Bambu Studio."""
        caminho = os.path.join(self.output_dir, nome_arquivo)
        mesh.export(caminho)
        print(f"[STL GERADO] Ficheiro guardado em: {caminho}")
        return caminho