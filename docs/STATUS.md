# Estado de desenvolvimento — 0.1.0

## Escopo desta primeira entrega

Repositório inicial com plugin instalável, conhecimento transferível, núcleo verificável sem SketchUp e primeiros extratores nativos. Ainda não é uma versão homologada para produção nos três programas.

| Parte | Implementação | Validação necessária |
|---|---|---|
| Pacote Codex e regras | Portados e organizados | Instalação em Codex de colega |
| Núcleo JSON, busca e especificação | Implementado | Testes automatizados locais e CI |
| SketchUp | Ponte herdada com namespace isolado | Regressão em SKP real após portabilidade |
| Rhino | Extrator Python nativo inicial | Execução real; vistas técnicas e cotas |
| 3ds Max | Extrator pymxs inicial | Execução real; vistas técnicas e cotas |
| PPTX | Gerador herdado | Dependência artifact-tool e QA visual por projeto |
| PDF | Etapa prevista no fluxo | Exportação e revisão quando solicitado |

## Próximos marcos

1. Instalar o pacote num Codex diferente e validar diagnóstico sem SketchUp.
2. Homologar extração no Rhino e 3ds Max com modelos sintéticos (docs/HOMOLOGACAO.md).
3. Implementar vistas isoladas e cotas por aplicativo; impedir que metadados de câmera sejam tratados como renders.
4. Executar um memorial completo por programa, incluindo revisão de todas as páginas.
5. Publicar versão de equipe validada, incluindo matriz de versões e limitações reais.

O pacote deve poder ser compartilhado como piloto antes dos marcos 2–4, desde que permaneça identificado como desenvolvimento. Isso permite concluir as integrações nos computadores que possuem os aplicativos.

