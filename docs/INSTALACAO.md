# Instalação no Codex dos colegas

## Requisitos

- Codex local com acesso à pasta do projeto e execução de scripts.
- Python 3.10+ para o núcleo. O Codex pode localizar seu runtime empacotado quando disponível.
- Apenas para extrair modelos: o aplicativo correspondente, acessível e com licença ativa quando exigida.
- Para o gerador PPTX herdado: Node.js e `@oai/artifact-tool` disponibilizado pelo runtime do Codex. O pacote não redistribui essa biblioteca. Use a ferramenta `load_workspace_dependencies` quando disponível e defina `RUNTIME_NODE_MODULES` com o caminho informado. Se indisponível, registre a dependência faltante antes de prometer o PPTX.

## Instalar o marketplace local

Na raiz deste repositório, com o CLI do Codex no PATH:

```powershell
codex plugin marketplace add .
codex plugin add memorial-modelo-3d@personal
```

O nome `personal` acima é o nome efetivamente criado no manifesto deste repositório pelo gerador oficial. Confira o nome em `.agents/plugins/marketplace.json` antes de instalar se a equipe publicar uma variante. Este marketplace está no repositório e precisa ser adicionado explicitamente; não é o catálogo pessoal implícito da pasta do usuário.

Depois, abra uma nova tarefa. Se existir conflito com outro marketplace chamado `personal`, peça ao Codex para gerar um marketplace de equipe com nome livre usando `$plugin-creator`, mantendo a origem local correta. Não sobrescreva um catálogo de terceiros.

Se o CLI não estiver acessível, peça ao Codex local para localizar o CLI empacotado e instalar o pacote. Como alternativa de desenvolvimento, `$skill-installer` pode instalar a pasta `plugins/memorial-modelo-3d/skills/memorial-modelo-3d` do repositório acessível, incluindo todos os recursos — não somente SKILL.md.

## Primeiro diagnóstico

```powershell
python plugins/memorial-modelo-3d/skills/memorial-modelo-3d/scripts/memorial_cli.py doctor
```

Encontrar um executável não comprova que a licença ou o adaptador funcionam. Faça o teste nativo descrito em HOMOLOGACAO.md.

## Escolha do aplicativo

- `.skp`: siga `references/sketchup.md`. A ponte é instalada só quando esse fluxo for usado.
- `.3dm`: siga `references/rhino.md`. Extração dentro do Rhino; sem SketchUp.
- `.max`: siga `references/3dsmax.md`. Extração dentro do 3ds Max; sem SketchUp.
- Outro formato: registrar a lacuna e planejar adaptador ou conversão verificável. Não importar silenciosamente nem atribuir fidelidade que não foi verificada.

## Atualizações

Receba a versão nova do repositório, reinstale o plugin da mesma origem e teste numa nova tarefa. Atualizações não são sincronizadas entre cópias locais automaticamente.

Em workspace administrado, um administrador pode importar um marketplace de um repositório privado no GitHub e controlar a distribuição. A importação não concede acesso ao repositório, aplicativos ou licenças: cada pessoa precisa ter o acesso pertinente.

Documentação oficial: https://learn.chatgpt.com/docs/build-skills ; https://learn.chatgpt.com/docs/build-plugins ; https://learn.chatgpt.com/docs/enterprise/plugin-management

