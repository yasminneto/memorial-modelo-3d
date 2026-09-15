# Integração SketchUp

A ponte foi portada da skill original e renomeada para `Codex::Memorial3D` / `Codex_Memorial3D`, evitando substituir a ponte anterior. O formato bruto continua em v1; normalize para v2 separadamente.

## Execução no Windows

Feche o modelo de trabalho após salvar suas alterações, ou abra uma cópia de trabalho numa sessão dedicada. Não execute extração numa sessão com alterações que precisem ser mantidas: o extrator cria vistas/cotas temporárias e encerra descartando mudanças.

Na pasta da skill:

```powershell
.\scripts\run_sketchup_extract.ps1 -ModelPath 'C:\projeto\modelo.skp' -OutputDir 'C:\projeto\extracao-nova' -SketchUpVersion 2026 -MaxDepth 3
python .\scripts\memorial_cli.py normalize-sketchup --help
```

Use uma pasta de saída nova. A instalação copia somente a ponte deste plugin para a pasta de plugins do SketchUp; não instala SketchUp. Pode indicar `-SketchUpExe` para um executável fora do caminho padrão.

Em modelos grandes, profundidade 2–4 é um início para reconhecimento. Aprofunde os conjuntos selecionados; profundidade reduzida não prova completude. O núcleo deixa limites aninhados antigos sem confirmação por causa da diferença entre coordenadas locais/globais no manifesto herdado.

## Recortes técnicos

`-FocusSetsPath` recebe lista JSON com `name` e seletores `persistent_ids`, `definition_names` ou `tag_names`; `center_filter_m` separa objetos da mesma tag. Vistas `front`, `rear`, `left`, `right`, `top`, `bottom`, `iso_front`, `iso_rear`. Use `projection: parallel` nas ortogonais, `dimension_mode` em `union`, `first`, `union_and_first` e `dimension_axes` em `width`, `depth`, `height` quando apropriado.

Reutilize intenção das cenas existentes, auditando projeção e visibilidade. Não use envelope como substituto de vãos/espessuras. As regras e rubrica gerais continuam obrigatórias.

O gerador de LayOut específico do projeto anterior não integra este pacote. A rota comum recebe as imagens e produz PPTX. A execução da ponte portada ainda precisa de teste de regressão nativo; não equivale à homologação prévia do agente original.

