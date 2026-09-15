# Rubrica de validação

## Falhas críticas

- O item solicitado não aparece ou foi confundido com outro.
- Uma medida é inventada, usa unidade errada ou não corresponde à evidência.
- Material, acabamento ou quantidade são apresentados como confirmados sem fonte.
- A prancha não permite identificar o objeto.
- O original do modelo foi sobrescrito.
- Largura, profundidade e altura foram trocadas por erro de eixo.
- Um conjunto de objetos foi cotado apenas pelo envelope quando a produção exige a dimensão de cada unidade.
- Uma imagem técnica foi entregue com céu, chão, fundo cinza/degradê ou contexto externo em vez de fundo branco uniforme e objeto isolado.
- Uma cota está em unidade diferente de metro, não está preta, não pode ser associada aos pontos medidos ou foi colocada em posição ilegível.
- Um item fabricável foi aprovado somente com cotas de envelope quando suas divisões, vãos, espessuras, modulação ou interfaces estão modelados e afetam produção.
- Uma cena em perspectiva foi apresentada como planta, elevação ou lateral técnica, causando deformação dos eixos cotados.
- Um objeto, logo ou detalhe claro desaparece sobre o fundo branco por falta de contorno ou contraste técnico.
- Uma dimensão de bounding box foi apresentada como cota produtiva apesar de existir dimensão nominal divergente ou pontos de fabricação mais adequados, sem registrar a incompatibilidade.
- Um elemento nomeado em fonte vigente do projeto ficou ausente do detalhamento e do consolidado sem status explícito.

Qualquer falha crítica reprova a entrega.

## Pontuação por item

Avaliar de 0 a 2: identificação e recorte; arquitetura do caderno; vistas; cotas gerais; cotas funcionais; construção/materiais/acabamentos; quantidade e composição; instalação/acesso/interfaces; pendências e rastreabilidade.

Critério de sucesso: nenhuma falha crítica, nenhum eixo com nota 0 e pelo menos 15 de 18 pontos por item.

## Controle cruzado

- Comparar dimensões do manifesto com os rótulos exibidos.
- Recalcular `max_m - min_m` em X, Y e Z e confirmar `L/P/A`; não confiar apenas no rótulo do campo.
- Conferir se todas as imagens existem e correspondem ao item.
- Confirmar que quantidades consolidadas não duplicam instâncias.
- Para itens com interior, profundidade ou acesso, confirmar frontal, lateral e superior e verificar se divisões/espessuras relevantes estão cotadas ou marcadas como pendentes.
- Conferir a reconciliação entre legenda da planta, detalhes individuais e consolidado final.
- Conferir a matriz `item x vista necessária x cena aproveitada/criada`; toda lacuna deve gerar nova vista ou pendência explícita.
- Conferir a tabela `elemento nomeado x seletor x cena x prancha x status`; exigir destino explícito para todas as entradas das fontes do projeto.
- Comparar cotas publicadas com documentos do projeto, anotações do modelo e medidas entre pontos produtivos. Identificar valores originados apenas do bounding box e justificar seu uso.
- Reconciliar contagens de suportes físicos, artes/conteúdos intercambiáveis, equipamentos e consumíveis; não tratar automaticamente a quantidade visual modelada como quantidade de produção.
- Confirmar que cada cena reaproveitada preserva o recorte e o estado de visibilidade úteis do autor, mas usa projeção tecnicamente adequada à finalidade declarada.
- Para planta e elevações, conferir cotas totais e cadeias parciais. Recalcular a soma dos segmentos e investigar qualquer diferença além da precisão de arredondamento.
- Para mobiliário, verificar se a geometria interna modelada permanece visível e cotada: base, prateleiras, divisões, portas, espessuras, acessos, iluminação e variantes aplicáveis.
- Para formas circulares, angulares, lineares ou modulares, confirmar que diâmetros/raios, ângulos, segmentos, passo e quantidade foram avaliados em vez de somente o retângulo envolvente.
- Confirmar que chamadas cuja posição importa estão ancoradas graficamente no elemento correspondente.
- Rejeitar planta superior ocultada por cobertura/forro ou cujo envelope inclua objetos externos. A cota geral da vista deve reconciliar com a implantação; se houver tag ou cena dedicada de planta baixa, preferi-la.
- Renderizar todas as páginas e revisar clipping, sobreposição, legibilidade e cortes.
- Confirmar em cada imagem que o fundo é branco uniforme e que não há céu, solo, horizonte, eixos, planos de seção, sombras de contexto ou geometria externa ao recorte.
- Confirmar que as vistas técnicas usam faces planas e arestas pretas nítidas, sem alteração da geometria; aceitar textura apenas quando necessária para reconhecer comunicação visual.
- Confirmar que todas as cotas visíveis estão pretas e em metros. Rejeitar cotas na profundidade da câmera, cortadas, sobrepostas ou pequenas demais; exigir outra vista em vez de manter uma cota ruim.
- Renderizar no tamanho final e conferir que textos de cota conservam altura visual aproximada de 2,5 mm ou maior, com setas e linhas de extensão distinguíveis.
- Manter, no `memorial_spec.json`, a origem de cada afirmação: `model`, `briefing`, `reference`, `user` ou `pending`.
