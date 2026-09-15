# Regras de conteúdo do memorial

Estas regras consolidam padrões técnicos de memoriais de stands e ativações. A estética das referências não é requisito.

## Arquitetura do caderno

Para um memorial completo, estruturar a informação em camadas e omitir somente as que não se aplicarem:

1. Perspectivas gerais para reconhecimento.
2. Planta ou implantação cotada, com áreas/ambientes, circulações, portas, mobiliário e legenda numerada com quantidades.
3. Elevações ortográficas das faces relevantes, com cotas totais, parciais, alturas, vãos e chamadas de sistemas.
4. Detalhes individuais de estruturas, comunicação, mobiliário e equipamentos.
5. Consolidado descritivo por classe produtiva, incluindo itens que dependam de fornecedor ou confirmação.

Manter a ligação entre legenda da planta, título da prancha de detalhe e quantidade consolidada.

## Auditoria e aproveitamento das cenas do modelo

- Inventariar todas as cenas antes de gerar novas vistas. Para cada uma, registrar câmera, projeção, recorte, estado de visibilidade e elemento enfatizado.
- Tratar cenas existentes como evidência da intenção do autor: elas podem indicar a fachada prioritária, o ponto de acesso, o ambiente interno ou o detalhe que deve aparecer. Não tratá-las automaticamente como desenho técnico correto.
- Confirmar geometricamente a orientação. Uma cena nomeada “frontal”, “planta” ou “lateral” que permaneça em perspectiva, inclinada ou com eixo produtivo deformado deve ser corrigida em uma cópia temporária.
- Reutilizar o estado de visibilidade da cena quando ele isolar corretamente o assunto. Não executar `zoom extents` sobre protótipos, componentes estacionados ou geometrias ocultas fora do conjunto.
- Quando o modelo 3D tiver somente cenas de renderização, criar o conjunto técnico ausente: planta sem cobertura, elevações ortogonais das faces relevantes, vistas de detalhe e cortes necessários para mostrar interior, acesso ou espessura.
- Construir uma matriz de cobertura antes da diagramação: `item`, `vista exigida`, `cena existente`, `vista nova`, `cotas suportadas` e `pendência`. Nenhum item produtivo deve depender apenas de uma perspectiva.

## Padrão visual técnico das imagens

- Toda vista do modelo deve usar fundo branco uniforme.
- Desligar céu, solo, horizonte, eixos, planos de seção, sombras de ambiente e marcas do estilo da cena.
- Isolar o stand, estrutura ou objeto de geometria externa que não pertença ao item documentado.
- Preservar somente o contexto que faça parte do próprio conjunto produtivo e seja necessário para entender interfaces.
- Rejeitar renders com fundo cinza, degradê, transparência, ambiente externo ou objetos estacionados ao redor do modelo.
- Nas vistas técnicas, preferir projeção paralela, faces planas sem textura e contornos/arestas pretos nítidos, produzindo leitura próxima de desenho vetorial sem modificar os elementos do modelo.
- Preservar texturas somente quando forem necessárias para reconhecer grafismo, comunicação visual ou acabamento em uma perspectiva geral.

O fundo branco é requisito documental, não uma decisão estética: ele melhora leitura de contornos, cotas e recortes e mantém consistência entre pranchas.

## Conteúdo mínimo por item

1. Título inequívoco e número da prancha.
2. Uma ou mais vistas que permitam reconhecer o objeto.
3. Cotas gerais: largura, profundidade e altura quando aplicáveis.
4. Cotas funcionais relevantes: vão livre, espessura, altura útil, módulos, recuos, base, guarda-corpo, tela ou área aplicada.
5. Descrição do sistema ou material quando sustentada por evidência.
6. Revestimento, cor, impressão, adesivação, pintura ou acabamento quando informados.
7. Comunicação visual, iluminação, telas, acessórios e equipamentos integrados.
8. Quantidade e unidade de contagem.
9. Observações de montagem, fixação, contrapeso, acabamento de faces, segurança ou interface com o local.
10. Pendências explícitas para qualquer dado não confirmado.

## Profundidade por item produtivo

- Mobiliário, totens e expositores: frontal, lateral e superior; perspectiva quando útil; dimensões totais; base/rodapé; espessuras; divisões e prateleiras; portas ou acesso traseiro; área transparente; logomarca; iluminação integrada; quantidade e variações esquerda/direita.
- Estrutura/envelope: implantação, faces externas e internas relevantes; perfil ou sistema declarado; espessura de fechamento; portas/vãos; testeira/forro/piso; interfaces com LED, elétrica e equipamentos.
- Comunicação luminosa: largura/altura/profundidade; face e laterais; substrato/espessura declarados; adesivação; tipo de iluminação; acesso e alimentação.
- Iluminação especial: vista superior da geometria, módulo, ângulo quando produtivo, extensão total, conectores/fixadores e interface estrutural.
- Equipamentos: quantidade, envelope, posição, acesso, energia/dados/dreno e dados de fabricante somente quando fornecidos.

Não usar apenas o envelope de vários objetos quando a fabricação depende da dimensão de uma unidade. Separar por posição ou variação e documentar a unidade representativa.

## Fontes e nível de certeza

- `model`: geometria, quantidade, tags, materiais nomeados e textos verificados no modelo.
- `briefing`, `reference` ou `user`: especificações declaradas fora do modelo, sempre com localizador.
- `pending`: alternativa, sugestão, incompatibilidade ou dado não sustentado.

Materiais e espessuras declarados em um memorial do projeto podem ser transcritos com fonte `reference`; não devem ser reclassificados como `model`. Alternativas com “ou” permanecem alternativas e não viram decisão de produção.

### Reconciliação entre dimensão nominal e geometria

- Diferenciar `dimensão nominal/de projeto`, `dimensão medida entre pontos produtivos` e `envelope geométrico`. Registrar qual delas sustenta cada cota publicada.
- Não publicar automaticamente `bounds.width/depth/height` como medida de fabricação. Bases, saliências, letras, acessórios, objetos rotacionados, geometria auxiliar e componentes aninhados podem alterar o bounding box sem alterar a dimensão nominal desejada.
- Quando um documento do projeto e o modelo 3D divergirem, conferir unidade, revisão, seletor, eixos e pontos medidos. Se a diferença persistir, mostrar a divergência como pendência de compatibilização; não escolher silenciosamente o valor que parecer mais conveniente.
- Medidas extraídas do modelo devem guardar, sempre que viável, os pontos/arestas de origem ou identificadores das entidades medidas para permitir auditoria posterior.
- Reconciliar também quantidades e natureza do item. Distinguir suporte físico, conteúdo gráfico intercambiável e consumível: por exemplo, uma malha de quadros modelados não prova por si só a quantidade de capas impressas a produzir.

### Controle de cobertura das fontes

- Criar um inventário de todos os elementos nomeados em briefing, plantas, memoriais do projeto, textos e chamadas das cenas. Vincular cada entrada a um seletor do modelo, uma ou mais vistas e uma prancha ou linha do consolidado.
- Não encerrar o memorial com entradas órfãs. Classificar cada uma como `detalhada`, `consolidada`, `não aplicável à revisão` ou `não localizada/confirmar`.
- Reconciliar nomes equivalentes antes de consolidar, mas não fundir funções diferentes apenas por semelhança visual: painel de LED, mesa DJ, plano de mídia, fechamento, logo, vinil impresso e luminária são classes produtivas distintas.
- Repetir esse controle após a diagramação, pois um item presente no inventário pode ainda ter ficado sem imagem, cota, quantidade ou descrição suficiente.

## Classes produtivas

Classificar em estrutura base, fechamento ou revestimento, comunicação visual, iluminação, elétrica/LED/audiovisual, mobiliário, vegetação/decoração, piso/carpete, ferragem/fixação/contrapeso e equipamento/acessório operacional.

## Linguagem e unidades

- Descrever para produção e orçamento, não para marketing.
- Preferir frases verificáveis: “volume geral 4,50 x 1,00 x 4,00 m”.
- Usar “material a confirmar” quando não houver evidência suficiente.
- Separar especificação confirmada de recomendação ou pendência.
- Não chamar 0,40 m de 0,40 cm. Normalizar todas as cotas exibidas para metros e sinalizar suspeitas das fontes.

## Padrão das cotas

- Linhas, setas e textos de cota devem ser pretos e permanecer visíveis sobre o fundo branco.
- Exibir valores em metros; usar duas casas por padrão e mais precisão somente quando necessária para não perder um detalhe produtivo.
- Inserir apenas cotas cuja linha, extensão, setas e valor possam ser associados claramente aos pontos medidos.
- Em vistas ortográficas, não cotar o eixo alinhado com a profundidade da câmera: frontal/traseira mostram largura e altura; esquerda/direita mostram profundidade e altura; superior/inferior mostram largura e profundidade.
- Omitir cotas muito pequenas, sobrepostas, cortadas ou visualmente ambíguas e documentá-las em outra vista mais adequada.
- A ausência de uma cota ilegível é preferível a um valor solto ou enganoso.

O bounding box fornece somente largura, profundidade e altura globais. No manifesto, conferir a ordem de eixos `X/Y/Z = largura/profundidade/altura` também pelas diferenças entre `min_m` e `max_m`. Adicionar cotas internas quando elas alterarem fabricação, transporte, operação ou preço: vão de túnel, espessura de painel, altura de balcão, dimensão do LED embutido, patamares de arquibancada e recorte de carpete.

Antes de compor uma planta por tags, comparar `min_m`/`max_m` de cada tag com o perímetro da implantação. Tags que também contenham protótipos ou objetos estacionados fora do stand precisam de `center_filter_m`, de isolamento por identificador, ou devem ser omitidas da vista e registradas no inventário textual. Nunca aceitar a cota da união se ela ultrapassar o perímetro declarado sem justificativa.

Para mobiliário, informar tipo, material/acabamento conhecido, cor, quantidade e composição do conjunto. Não presumir que objetos visualmente semelhantes são idênticos se tiverem definições, dimensões ou nomes diferentes.

## Hierarquia e densidade das cotas

Aplicar as cotas em camadas. O envelope geral é apenas a primeira camada, não o detalhamento completo:

1. **Geral:** largura, profundidade e altura totais do conjunto.
2. **Parcial ou modular:** vãos, eixos, módulos, painéis, trechos de parede, divisões e distâncias sucessivas.
3. **Funcional:** largura livre de passagem, altura útil, acesso, circulação, bancada, assento, nicho, tela e manutenção.
4. **Fabricação:** espessuras, base/rodapé, prateleiras, portas, rebaixos, ranhuras, perfis, diâmetros, raios e ângulos.
5. **Implantação/interface:** afastamentos e posição do item em relação a paredes, piso, teto, eixo ou outro datum verificável.

- Usar a vista mais clara para cada camada. Não repetir apenas o mesmo envelope em vistas diferentes quando uma delas poderia mostrar profundidade interna, composição ou posição.
- Em cadeias de cotas, exibir o total e os segmentos que explicam sua composição. Conferir se a soma dos segmentos reconcilia com o total dentro da precisão adotada; qualquer diferença deve ser explicada ou marcada para revisão.
- Ancorar cada cota em arestas, centros ou planos efetivamente visíveis e pertencentes ao item. Não cotar o limite de geometria oculta, auxiliar ou aninhada sem mostrar o que está sendo medido.
- Para formas não retangulares, cotar a geometria que governa a produção: diâmetro, raio, comprimento do segmento, ângulo, passo, quantidade de módulos e envelope do conjunto quando útil.
- Dimensionar também a posição de logos, telas, portas, luminárias e acessórios quando o posicionamento afetar montagem ou comunicação visual.
- Revisar o PDF no tamanho final de leitura. O texto da cota deve conservar altura visual mínima equivalente a aproximadamente 2,5 mm no impresso, com setas, linhas de extensão e folga suficientes para não tocar geometria, outras cotas ou chamadas.

## Conteúdo técnico específico das vistas

- **Planta/implantação:** retirar ou seccionar cobertura e forro que ocultem o interior; mostrar perímetro, paredes, espessuras relevantes, portas com sentido de abertura, vãos livres, ambientes/áreas, circulação, mobiliário, equipamentos, legenda e cotas gerais e parciais.
- **Elevações:** cobrir todas as faces que mudem construção ou comunicação. Mostrar alturas totais e parciais, base/piso, forro/testeira, vãos, portas, painéis, logos, equipamentos e sua posição. Diferenciar face interna e externa quando houver acabamento ou montagem distintos.
- **Mobiliário:** combinar frontal, lateral, superior e perspectiva. Usar linhas ocultas, transparência técnica ou corte quando necessário para revelar prateleiras, divisórias, portas, acesso traseiro, iluminação e espessuras; preenchimento sólido não pode apagar a construção interna.
- **Variações:** representar separadamente peças espelhadas, esquerda/direita ou assimétricas, mesmo que compartilhem envelope. Consolidar somente peças cuja geometria e fabricação sejam equivalentes.
- **Chamadas:** ligar notas de material, iluminação, comunicação, acesso ou instalação ao ponto correspondente da vista por linha de chamada legível. Texto descritivo solto não substitui a localização gráfica quando a posição importa.
- **Contraste:** reforçar arestas pretas de objetos claros, transparentes ou brancos. Nenhum logo, texto, vidro ou detalhe pode desaparecer sobre o fundo branco; quando necessário, usar contorno técnico, linha tracejada ou vista monocromática complementar sem alterar a geometria.
