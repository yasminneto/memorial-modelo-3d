# Memorial Modelo 3D

Plugin de equipe para Codex: criar memoriais descritivos técnicos de stands, ativações e mobiliário a partir de SketchUp, Rhino e 3ds Max.

**Versão 0.1.0 — desenvolvimento.** O fluxo SketchUp foi portado do agente existente. Os adaptadores Rhino/3ds Max estão em implantação; sua execução nativa e suas vistas técnicas precisam ser homologadas nos computadores da equipe. Instalar este pacote não exige SketchUp nem Blender.

## Primeira utilização

1. Baixe ou clone este repositório em uma pasta de trabalho.
2. Abra a pasta no Codex e peça: “Leia AGENTS.md e docs/CONTEXTO.md, instale o plugin conforme docs/INSTALACAO.md e diagnostique meu ambiente”.
3. Abra uma nova tarefa após a instalação. Selecione a skill Memorial Modelo 3D e informe modelo, briefing e itens desejados.
4. O Codex identifica o aplicativo adequado e informa a capacidade disponível antes da extração. Caminhos das máquinas são descobertos localmente.

## Teste do núcleo sem programa 3D

Na raiz do repositório, com Python 3.10 ou superior:

```powershell
python plugins/memorial-modelo-3d/skills/memorial-modelo-3d/scripts/memorial_cli.py --help
python plugins/memorial-modelo-3d/skills/memorial-modelo-3d/scripts/memorial_cli.py doctor
python -m unittest discover -s tests -v
```

`examples/manifest-demo.json`, dentro da skill, contém dados sintéticos para testar o contrato. Não representa projeto de cliente e não é evidência de homologação dos programas.

## Estrutura

```text
plugins/memorial-modelo-3d/
  .codex-plugin/plugin.json
  skills/memorial-modelo-3d/
    SKILL.md             Regras e seleção do adaptador
    scripts/             Validação, busca, especificação e PPTX
    adapters/            Rhino e 3ds Max
    assets/              Ponte SketchUp isolada
    references/          Conhecimento técnico acumulado
    schemas/             Contrato de extração comum
    examples/            Dados sintéticos
docs/                    Instalação, contexto, estado e homologação
tests/                   Testes do núcleo independente
```

O extrator produz evidência, o núcleo organiza os itens e o Codex reconcilia com as fontes e revisa todas as pranchas. Uma extração parcial pode apoiar análise, mas não prova completude nem quantidade de produção.

## Contribuir

Leia [contexto](docs/CONTEXTO.md), [estado atual](docs/STATUS.md) e [homologação](docs/HOMOLOGACAO.md). As adaptações feitas na máquina de um colega devem voltar ao repositório com versão do aplicativo, teste e limitações documentados. O pacote não transfere contas, licenças, permissões ou memória privada do Codex.

