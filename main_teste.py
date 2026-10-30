from misiski_core import MisiskiScadCore

# Inicializa o motor CAD
cad = MisiskiScadCore()

print("1. A criar polígono paramétrico com 8 arestas (octógono)...")
peca_poligono = cad.criar_forma_parametrica(raio=25.0, altura=20.0, lados=8)
cad.exportar_stl(peca_poligono, "octogono_custom.stl")

print("2. A manipular vértices e faces (esticando a altura no eixo Z em 1.5x)...")
peca_modificada = cad.manipular_malha(peca_poligono, operacao="escala_z", fator=1.5)
cad.exportar_stl(peca_modificada, "octogono_esticado.stl")

print("3. A gerar manequim humanoide articulado...")
manequim = cad.gerar_manequim_humanoide()
cad.exportar_stl(manequim, "manequim_base.stl")

# Se quiser testar com uma imagem real:
# img_mesh = cad.imagem_para_3d("assets/sua_imagem.png", altura_extrusao=8.0)
# cad.exportar_stl(img_mesh, "de_imagem_para_3d.stl")

print("\nProcesso lógico concluído com sucesso! Verifique a pasta 'exports/'.")