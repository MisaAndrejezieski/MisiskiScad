import os

from core.primitives import criar_poligono_extrudado, criar_tampa_parametrica


def main():
    print("Iniciando MisiskiScad...")
    
    # Garante que a pasta de exportação existe
    os.makedirs("exports", exist_ok=True)
    
    # Exemplo 1: Criar um prisma triangular (3 lados)
    print("Criando triângulo 3D...")
    triangulo_3d = criar_poligono_extrudado(raio=15.0, altura=30.0, nucleos_lados=3)
    triangulo_3d.export("exports/triangulo_exemplo.stl")
    
    # Exemplo 2: Criar uma peça cilíndrica/circular com 64 faces (suave)
    print("Criando cilindro suave...")
    cilindro = criar_poligono_extrudado(raio=20.0, altura=10.0, nucleos_lados=64)
    cilindro.export("exports/cilindro_exemplo.stl")
    
    # Exemplo 3: Criar uma tampa paramétrica
    print("Criando tampa paramétrica...")
    tampa = criar_tampa_parametrica(diametro=60.0, altura_borda=12.0, espessura=3.0, lados=32)
    tampa.export("exports/tampa_customizada.stl")
    
    print("Modelos gerados com sucesso na pasta 'exports/'! Pronto para importar no Bambu Studio.")

if __name__ == "__main__":
    main()