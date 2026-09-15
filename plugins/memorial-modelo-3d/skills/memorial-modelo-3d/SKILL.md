---
name: memorial-modelo-3d
description: Criar memoriais técnicos de stands, ativações e mobiliário a partir de modelos SketchUp, Rhino ou 3ds Max, cruzando briefing, vistas, cotas e quantidades. Usar para memorial descritivo, caderno técnico e inventário produtivo. Detecta capacidades locais; integrações ainda não homologadas exigem teste nativo antes de prometer resultado completo.
---

# Memorial a partir de modelo 3D

O resultado deve preservar a profundidade técnica do fluxo original de SketchUp. Cada aplicativo é uma fonte independente; Rhino e 3ds Max não dependem de SketchUp ou Blender.

## Entrada e escolha da integração

1. Leia [contrato de entrada](references/input-contract.md). Registre modelo, revisão, briefing, documentos, unidades e itens pedidos. Sem recorte explícito, faça inventário de candidatos antes de produzir memorial de tudo.
2. Rode `scripts/memorial_cli.py doctor` usando Python disponível no ambiente. O diagnóstico não instala nem executa aplicativos. Detectar o programa não homologa extração.
3. Use `.skp` com [SketchUp](references/sketchup.md), `.3dm` com [Rhino](references/rhino.md) e `.max` com [3ds Max](references/3dsmax.md). Leia apenas a referência pertinente. Preserve os originais e a sessão de trabalho do usuário; saída nova para cada extração.
4. Sem ferramenta compatível, descreva a capacidade faltante. Para adaptar a instalação ou desenvolver outro adaptador quando solicitado, siga [adaptação](references/adaptation.md). Nunca apresente código gerado como testado no programa.

## Evidência e análise

5. Normalize o resultado para `schemas/manifest.schema.json` e valide com o núcleo. No SketchUp, mantenha também o manifesto bruto. Extração parcial não comprova contagem integral, cobertura ou ausência de objetos.
6. Inventarie vistas e câmeras existentes: projeção, visibilidade, recorte e intenção. Câmera cadastrada não é imagem pronta. Construa matriz `item × vista necessária × vista existente/criada × cotas × pendência`.
7. Busque candidatos por nome, hierarquia, camada/tag, material e posição. Cruze os resultados com briefing, dimensões e imagens. Nunca escolha apenas o primeiro nome parecido.
8. Crie tabela `elemento citado × seletor no modelo × vista × prancha × status`. Todo elemento das fontes vigentes precisa ter destino explícito.
9. Leia [regras do memorial](references/memorial-rules.md). Para detalhamento executivo, leia [padrão aprofundado](references/architect-2-pattern.md). Use `scripts/new_memorial_spec.py` ou o comando `spec` do núcleo como rascunho e complete a especificação com evidências.

## Vistas, cotas e entrega

10. Crie vistas reais do modelo: fundo branco uniforme, isolamento, faces planas e arestas pretas; projeção paralela para planta/elevação. Preserve texturas apenas quando necessárias ao reconhecimento. Se o adaptador não gera vistas, registre a lacuna e complete no aplicativo antes de finalizar.
11. Use cotas pretas em metros, ligadas a pontos visíveis. Valores em caixas de texto não substituem linhas de cota. O bounding box indica envelope; cotas nominais, funcionais e de fabricação precisam de pontos ou documentos apropriados. Não converter X/Y/Z automaticamente em largura/profundidade/altura de um objeto rotacionado.
12. Materiais, quantidades de fabricação, acabamentos e métodos precisam de fonte. Use `confirmar` para lacunas; aparência e nome de material não comprovam especificação construtiva.
13. Gere PPTX com `scripts/build_memorial.mjs --spec <spec> --output <pptx> --qa-dir <pasta>`. Ele requer Node e artifact-tool do runtime do Codex. Descubra a dependência pelo ambiente; não use caminhos fixos de outra pessoa. Imagens relativas são resolvidas a partir da especificação.
14. Renderize e confira todas as páginas com [rubrica de validação](references/validation-rubric.md), corrigindo recorte, sobreposição, cotas, cobertura e rastreabilidade. PDF só conta como entregue após exportação e conferência.

Entregue manifesto, vistas, `memorial_spec.json`, PPTX e pendências. Distinga rascunho de memorial revisado. Preserve nos arquivos a evidência necessária para outro Codex continuar o trabalho.

