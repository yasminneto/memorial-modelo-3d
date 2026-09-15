# Adaptador 3ds Max — piloto 0.1

Este extrator lê a cena ativa pelo `pymxs` do próprio 3ds Max. Produz `manifest.json` no esquema `2.0` sem instalar SketchUp ou Blender. O código inicial ainda **não foi executado em um 3ds Max real**; nesta máquina não foi encontrada uma instalação do programa no diretório padrão da Autodesk. Compilação Python não equivale a homologação nativa.

## Requisitos e execução

- Windows com 3ds Max 2021 ou posterior, Python 3 e `pymxs` integrados; versões específicas ainda não homologadas.
- Abrir uma cópia de trabalho do `.max` no programa e escolher o frame que representa o projeto.
- Resolver avisos de plugins e referências ausentes antes de confiar em medidas.
- Ter uma pasta existente para receber um novo arquivo `.json`.

No **MAXScript Listener**, execute a linha abaixo, substituindo somente o caminho pelo local do repositório instalado:

```maxscript
python.ExecuteFile @"C:\projetos\memorial-modelo-3d\plugins\memorial-modelo-3d\skills\memorial-modelo-3d\adapters\3dsmax\run_export.py" clearUndoBuffer:false
```

Escolha um novo nome, por exemplo `manifest-max-001.json`. O lançador abre apenas a escolha do destino do JSON. O extrator rejeita destinos existentes e extensões diferentes de `.json`. Ele não abre outros modelos, não salva o `.max`, não muda seleção, frame, layers ou vistas. `clearUndoBuffer:false` preserva o histórico de desfazer ao iniciar o Python pela interface MAXScript. [Interface Python oficial](https://help.autodesk.com/cloudhelp/2026/ENU/MAXScript-Help/files/3ds-Max-Objects-and-Interfaces/Interfaces/Core-Interfaces/Core-Interfaces-Documentation/P-Q/GUID-860B6BEB-AE3E-4F99-96E9-CCD70DF4B772.html).

O JSON corresponde ao documento **em memória**, inclusive alterações que o usuário ainda não salvou. `source.path` é a procedência do documento, não uma garantia de igualdade com o arquivo em disco. Uma cena nova sem arquivo de origem é rejeitada: primeiro deve existir uma cópia de trabalho salva pelo usuário. A exportação registra versão, frame, ticks, taxa de frames e escala. Rodar o script com Python externo resulta em erro por ausência de `pymxs`.

## O que é extraído

| Dado | Tratamento |
|---|---|
| Hierarquia | Percorre filhos do nó raiz; preserva grupos, membros e pais. |
| Unidade | `SystemScale × fator(SystemType)` em metros; não usa a unidade de exibição. |
| Limites | `nodeGetBoundingBox(node, matrix3(1))` para geometria e shapes no frame atual. |
| Instâncias | `InstanceMgr.GetInstances` filtrado por `areNodesInstances`; não agrupa por nome. |
| Layers e visibilidade | Nome do layer e `isHiddenInVpt`; inclui objetos ocultos no inventário. |
| Materiais | Identificador, nome, classe e submateriais; não infere material construtivo. |
| Propriedades | Buffer textual de User Defined Properties, sem avaliar seu conteúdo. |
| Câmeras | Nome, posição, base de transformação e frame; sem imagens geradas. |

A unidade do sistema é distinta da apresentação da medida na interface. [System globals da Autodesk](https://help.autodesk.com/cloudhelp/2024/ENU/MAXScript-Help/files/MAXScript-Language-Reference/Reserved-Keywords-Symbols/GUID-141213A1-B5A8-457B-8838-E602022C8798.html).

Os limites são alinhados aos eixos globais e usam a geometria avaliada do nó; não são automaticamente largura/profundidade/altura de fabricação. Render-only displacement, proxies e plugins podem divergir da representação de viewport. [Node Bounding Box Methods](https://help.autodesk.com/cloudhelp/2023/ENU/MAXScript-Help/files/3ds-Max-Objects-and-Interfaces/Node-MAXWrapper/Node-Common-Properties-Operators/Node-Common-Methods/GUID-A8BF79D1-FAEE-413E-B552-3E486DA21EC3.html).

O filtro de instâncias evita tratar similaridades de modelos vinculados como uma prova de instanciamento nativo. Mesmo instâncias reais precisam ser reconciliadas com escopo, escala, material e função antes de virar quantidade de produção. [InstanceMgr](https://help.autodesk.com/cloudhelp/2026/ENU/MAXScript-Help/files/3ds-Max-Objects-and-Interfaces/Interfaces/Core-Interfaces/Core-Interfaces-Documentation/I-J-K/GUID-EB69A035-7FF4-4A0A-8A82-409C4145B9DF.html), [parâmetros por referência em pymxs](https://help.autodesk.com/cloudhelp/2021/ENU/Max-Python-API/using_pymxs/pymxs_differences/pymxs_by_ref_parameters.html).

## Limites desta versão

`extraction.status` permanece `partial`, mesmo se todos os nós forem lidos. Falta implementar e homologar a captura das vistas técnicas, isolamento de itens e cotagem. A lista `views` contém metadados, e não deve ser interpretada como imagens disponíveis. O memorial completo ainda precisa dessas evidências visuais.

Não calcula automaticamente contagem produtiva a partir de todos os nós: um grupo e seus membros representam níveis sobrepostos. Não percorre Custom Attributes arbitrários, não garante conteúdo de XRefs ou proxies e não verifica disponibilidade de todos os plugins da cena. Falhas por nó/campo entram em `warnings`; bounds indisponíveis ficam `null`. IDs baseados em handles devem ser usados junto do documento e da extração, nunca como UUID global entre arquivos.

## Homologação no computador do colega

1. Preparar cena simples com uma caixa de dimensão conhecida, cópia e instância, uma instância escalada/rotacionada, grupo aninhado, layer oculto, câmera e User Defined Properties.
2. Aplicar um modificador que mude o tamanho e conferir que o envelope exportado reflete o resultado da viewport no frame registrado.
3. Comparar uma cena com unidade do sistema em milímetros e outra em polegadas; mudar só Display Units não pode alterar os metros exportados.
4. Conferir pais, relações de instância e material; nomes iguais não devem fundir objetos diferentes.
5. Confirmar no programa que seleção, frame, unidades e vistas permanecem iguais; verificar que o arquivo original em disco mantém o mesmo hash.
6. Executar o validador comum do projeto no JSON e anexar versão exata do Max, checklist preenchido e um exemplo anonimizado ao registro de compatibilidade.
7. Só registrar suporte validado após essas verificações. Para liberar memorial completo, implementar e testar também vistas, cotas e verificação visual.
