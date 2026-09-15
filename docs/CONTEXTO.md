# Contexto transferível da equipe

## Objetivo

Preservar a qualidade do agente de memorial que já funcionava com SketchUp e permitir o mesmo processo em Rhino e 3ds Max, nos computadores dos colegas, sem instalação obrigatória de SketchUp. Blender ficou fora da prioridade inicial.

O progresso útil está nos scripts, regras, exemplos, evidências e decisões deste repositório. Uma conversa compartilhada pode ajudar a entender a história, mas não instala ferramentas e não sincroniza futuras melhorias.

## Decisões preservadas

- Entradas: modelo, briefing, plantas, anexos, referências e recorte explícito dos itens.
- Anexos têm papel `pattern_only`, `project_evidence` ou `approved_specification`. Referência visual não comprova material do projeto atual.
- Inventariar câmeras e vistas existentes antes de gerar novas. Nome “frontal” não comprova projeção ortogonal.
- Cada elemento citado nas fontes precisa estar detalhado, consolidado, fora da revisão ou não localizado/confirmar.
- Vistas técnicas: objeto isolado, fundo branco, contornos pretos, projeção adequada e cotas pretas legíveis em metros.
- Mobiliário com interior, profundidade ou acesso precisa das vistas que expliquem fabricação, incluindo frontal, lateral e superior quando aplicáveis.
- Envelope geométrico é diagnóstico; não substitui dimensão nominal, vão, espessura, módulo e detalhe construtivo.
- Materiais, método construtivo, quantidade de produção e acabamento só são confirmados com evidência. Nome de material no render é pista.
- Saídas: manifesto, vistas, memorial_spec.json, PPTX revisado; PDF quando solicitado e efetivamente gerado/revisado.
- Nenhum original deve ser salvo com modificações temporárias de estilo, cotas ou visibilidade.

## Proveniência

Base: skill local `sketchup-criar-memorial`, importada em 15/09/2026. A instalação original foi preservada. Regras e código reutilizáveis foram trazidos ao pacote; exemplos de clientes e caminhos da estação não fazem parte da distribuição.

A ponte nova usa o módulo Ruby `Codex::Memorial3D` e pasta `Codex_Memorial3D`, separados do extrator original. O gerador específico de LayOut do projeto anterior não foi incorporado; a rota compartilhada gera PPTX.

## Como continuar em outro Codex

> Leia AGENTS.md, docs/STATUS.md, a skill e a referência do meu aplicativo. Rode o diagnóstico. Continue o adaptador usando a API oficial e o contrato JSON existente. Teste em modelo sintético ou cópia de trabalho. Preserve os critérios técnicos, documente o que foi executado e prepare a melhoria para voltar ao repositório.

O processo de adaptação pode criar ou corrigir scripts específicos da versão instalada. Ele não garante leitura de formatos desconhecidos, licença de programa nem homologação automática. Uma integração só muda para “validada no aplicativo” com evidência da execução.

