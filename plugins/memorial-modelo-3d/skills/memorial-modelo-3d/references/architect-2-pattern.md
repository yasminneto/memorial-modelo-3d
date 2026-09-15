# Padrão técnico aprofundado - arquiteto 2

Usar este padrão quando o pedido for um memorial completo para produção, quando a referência trouxer pranchas ortográficas detalhadas ou quando mobiliário e sistemas integrados exigirem fabricação. Ele complementa, sem substituir, as regras gerais.

## Similaridades preservadas

- Um tema produtivo identificável por prancha.
- Imagens ou vistas suficientes para reconhecer o elemento.
- Cotas, quantidade, material/acabamento e texto de produção.
- Alertas para validação local e responsabilidade técnica quando aplicáveis.

## Ganhos de completude observados

- Sequência de perspectivas, planta, elevações, detalhes e consolidado.
- Planta com áreas, portas, cotas totais e parciais, legenda numerada e quantidades.
- Elevações de todas as faces relevantes, incluindo alturas, vãos e chamadas vinculadas à descrição.
- Frontal, lateral, superior e perspectiva para mobiliário.
- Cotas de partes: bases, espessuras, rodapés, prateleiras, nichos, ranhuras e afastamentos.
- Sistema construtivo declarado por camada: perfil, fechamento, revestimento, pintura/laminado/adesivo, vidro/acrílico e espessura.
- Função e integração: acesso traseiro, portas, manutenção, fitas de LED, backlight, iluminação de prateleira e fixadores.
- Consolidação final de todos os elementos, inclusive itens de fornecedor não detalhados geometricamente.

## Refinamentos confirmados pelos memoriais originais

- A planta não é apenas uma silhueta cotada: ela fecha áreas, acessos, portas, divisões, posições sucessivas de mobiliário, legenda numerada e quantidades.
- As elevações usam cotas gerais e cadeias parciais para explicar modulação, vãos, testeiras, bases, portas, logos e equipamentos; as quatro faces são mostradas quando não são equivalentes.
- As vistas de mobiliário revelam a construção interna com linhas ocultas ou transparência técnica e cotam base, corpo, prateleiras, espessuras e folgas, além do envelope.
- Uma perspectiva do item é usada para reconhecimento, enquanto frontal, lateral e superior sustentam fabricação. Nenhuma delas deve tentar cumprir todas as funções sozinha.
- Elementos lineares ou modulares recebem dimensão da unidade ou segmento, quantidade, passo/ângulo quando aplicável e dimensão total do arranjo.
- Chamadas ancoradas na vista identificam localização de sistemas e acabamentos. A descrição lateral complementa essas chamadas, não as substitui.
- Cenas de apresentação ajudam a entender prioridade e contexto, mas vistas técnicas novas são obrigatórias quando o arquivo não contém planta, elevação ou detalhe adequado.

## Como aplicar sem inventar

1. Extrair do modelo geometria, posição, tags, materiais nomeados, quantidades e cenas.
2. Extrair do briefing/memorial atual materiais, espessuras, métodos, alternativas e notas de instalação.
3. Manter cada afirmação com sua fonte; não atribuir ao modelo 3D uma especificação que existe apenas no texto.
4. Quando o modelo não sustentar espessura, divisão interna ou acesso, usar a evidência documental ou marcar `confirmar`.
5. Tratar alternativas literalmente: “pintura ou vinil” continua pendente de decisão.

## Ordem recomendada para teste de cobertura

- Reconhecimento geral.
- Implantação e inventário.
- Envelope e elevações.
- Estruturas e sistemas integrados.
- Um detalhe por tipo/variação produtiva.
- Consolidado de materiais, quantidades, interfaces e pendências.

Não exigir esta extensão para um pedido restrito a poucos objetos; aplicar somente as pranchas necessárias ao recorte solicitado.
