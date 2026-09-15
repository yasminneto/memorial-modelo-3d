# Desenvolvimento do Memorial Modelo 3D

Este projeto transfere para a equipe o conhecimento acumulado no agente de SketchUp. Leia README.md e docs/CONTEXTO.md antes de alterar o fluxo.

- Prioridade: SketchUp, Rhino e 3ds Max. Blender não é dependência.
- O núcleo deve funcionar sem aplicativos 3D; os adaptadores dependem somente do aplicativo correspondente.
- Preserve cotas funcionais, cobertura das fontes, rastreabilidade e revisão visual. Não reduza o memorial a bounding boxes.
- Nunca sobrescreva o arquivo de modelagem original. Use saída nova para cada execução e preserve a sessão de trabalho do usuário.
- Diferencie código implementado, teste sintático, teste automatizado e execução real no aplicativo. Não anuncie homologação por ter compilado Python.
- Antes de mudar o contrato JSON, atualize schema, consumidores, exemplos e testes juntos.
- Código dos adaptadores deve permanecer no plugin para acompanhar a instalação. Caminhos locais não entram no repositório.
- Registre melhorias em docs/STATUS.md; mudanças específicas da máquina ficam fora do versionamento.
- Execute `python -m unittest discover -s tests -v` antes de entregar mudanças de lógica. Não versione modelos de clientes nem saídas geradas.

