# MisiskiScad

Aplicativo CAD desktop experimental para gerar e editar malhas 3D e exportar STL.

## Instalação e execução

```powershell
python -m pip install -r requirements.txt
python app.py
```

## Reconstrução a partir de seis imagens

Na aba **Imagem para STL > Reconstrução por 6 vistas**, selecione imagens do mesmo
objeto nas direções frente, trás, esquerda, direita, cima e baixo. Informe as
dimensões finais aproximadas em milímetros, escolha a resolução e salve o arquivo
STL. A resolução é o número de voxels no maior eixo; valores maiores preservam
mais contorno, mas aumentam o tempo de processamento e o tamanho da malha.

Para melhores resultados, fotografe com a câmera perpendicular ao objeto, sem
perspectiva, com o objeto inteiro visível, fundo uniforme e margem ao redor.
Capture frente e trás, laterais esquerda e direita, e vistas superior e inferior.
Mantenha o eixo vertical do objeto para cima e as vistas opostas na mesma escala.
O controle de limiar ajusta a diferença de cor usada para separar o objeto do
fundo.

O programa recorta o contorno detectado e o ajusta às dimensões X, Y e Z
informadas. Portanto, essas medidas devem corresponder ao tamanho real do objeto;
o modelo não recupera escala em milímetros a partir das fotos automaticamente.

O programa calcula um **casco visual** pela interseção das seis silhuetas. Isso
estima o volume externo, mas não recupera concavidades ou detalhes escondidos
entre as vistas; fotos comuns em perspectiva podem produzir resultados imprecisos.
A saída é uma malha triangular STL com contornos em degraus, conforme a resolução
escolhida. Ela pode ser redimensionada, centralizada, reaberta para edição e
exportada novamente na aba **Manipular Vértices/Faces**. STL não preserva um
histórico paramétrico de CAD.

O modo **Relevo de uma imagem** continua disponível para extrudar uma silhueta 2D.
