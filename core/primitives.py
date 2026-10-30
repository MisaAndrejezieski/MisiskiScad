import numpy as np
import trimesh


def criar_poligono_extrudado(raio=10.0, altura=20.0, nucleos_lados=6):
    """
    Cria um prisma/polígono regular com número customizável de lados (faces/arestas),
    perfeito para exportar para .stl e abrir no Bambu Studio.
    """
    # Gera os ângulos baseados no número de lados (ex: 3=triângulo, 4=quadrado, 32=quase círculo)
    angulos = np.linspace(0, 2 * np.pi, nucleos_lados, endpoint=False)
    
    # Coordenadas X e Y da base
    x = raio * np.cos(angulos)
    y = raio * np.sin(angulos)
    vertices_2d = np.column_stack((x, y))
    
    # Extruda a geometria 2D para 3D
    mesh = trimesh.creation.extrude_polygon(trimesh.path.Polygon(vertices_2d), height=altura)
    return mesh

def criar_tampa_parametrica(diametro=50.0, altura_borda=10.0, espessura=2.0, lados=64):
    """
    Cria uma tampa paramétrica ajustável para potes ou recipientes.
    """
    # Corpo principal da tampa (disco superior + borda)
    externo = criar_poligono_extrudado(raio=diametro/2, altura=espessura, nucleos_lados=lados)
    borda = criar_poligono_extrudado(raio=diametro/2, altura=altura_borda, nucleos_lados=lados)
    
    # Aqui você pode combinar operações booleanas (união, subtração) no futuro
    tampa = trimesh.util.concatenate([externo, borda])
    return tampa