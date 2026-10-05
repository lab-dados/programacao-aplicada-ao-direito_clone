# Instruções para o agente

Este repositório é usado em aula, no curso *Programação Aplicada ao Direito* (LabDados, FGV
Direito SP). Quem faz os pedidos são estudantes de direito começando em Python, não
programadores.

## Como responder

- Responda em português, em linguagem simples.
- Antes de mudar um arquivo, diga o que vai fazer e por quê.
- Depois de cada análise, mostre o resultado e diga em quantos casos ele se baseia.
- Se o pedido for ambíguo (qual coluna? qual período? o que conta como vitória?), pergunte antes de
  escolher por conta própria.

## Os dados

`dados/processos.csv` tem 7.000 sentenças de primeiro grau, de 24 tribunais estaduais, em processos
ajuizados entre 2014 e 2025. É uma linha por processo, e a coluna `processo` não se repete.

| Coluna | Tipo | O que é | Linhas preenchidas |
|---|---|---|---|
| `processo` | texto | número CNJ do processo | 7.000 |
| `ano` | inteiro | ano do ajuizamento | 7.000 |
| `tribunal` | texto | sigla do tribunal estadual (24 valores) | 7.000 |
| `comarca` | texto | comarca onde a ação tramitou | 5.252 |
| `autor_tipo` | texto | `PESSOA FÍSICA` ou `PESSOA JURÍDICA` | 5.629 |
| `reu` | texto | nome da empresa no polo passivo | 4.266 |
| `setor` | texto | setor econômico do réu (12 valores) | 4.266 |
| `resultado` | texto | resultado da sentença (5 valores, abaixo) | 6.850 |
| `ganhou_autor` | verdadeiro/falso | o autor ganhou alguma coisa? | 4.153 |
| `valor_condenacao` | decimal | valor em reais que a sentença manda pagar | 1.221 |
| `n_chars` | inteiro | tamanho da sentença, em caracteres | 7.000 |

`dados/dispositivos.csv` tem o texto do dispositivo, a parte final da sentença, uma linha por
processo. As colunas são `processo`, `autor_tipo`, `reu` e `dispositivo`. Para juntar com
`processos.csv`, use a coluna `processo` e traga só `dispositivo`: `autor_tipo` e `reu` já estão na
outra tabela.

Não modifique os arquivos de `dados/`.

## Regras da base

Cada regra abaixo vem de um erro que já aconteceu em aula.

- Leia os dados com `carregar_processos()` e `carregar_dispositivos()`, do `analise_2.py`. A
  primeira já lê `ganhou_autor` com o tipo certo.
- `ganhou_autor` fica **vazia** em 2.847 processos: 2.697 acordos homologados, em que não há
  vencedor, e 150 sentenças sem resultado. Esses vazios ficam fora das taxas de êxito. Nunca
  preencha com `False` (`fillna(False)`) nem converta com `astype(bool)`: os dois dão um número
  plausível e errado, sem mensagem de erro.
- `resultado` tem exatamente estes valores, em maiúsculas: `PROCEDENTE`, `PARCIALMENTE PROCEDENTE`,
  `IMPROCEDENTE`, `EXTINTO SEM MÉRITO` e `ACORDO HOMOLOGADO`. Compare com o texto exato.
- `setor` e `reu` ficam vazios em 2.734 processos. Diga quando uma análise por setor deixa esses
  processos de fora.
- Toda taxa vem com o número de casos em que foi calculada. Avise quando um grupo tiver menos de 30
  casos.
- Não suponha o ano de hoje. Para calcular idade ou tempo, use o ano informado no pedido; se não
  houver, pergunte.
- Não altere a tabela original: crie colunas com `assign` ou trabalhe numa cópia.

## Como rodar

- `python analise_2.py` imprime as tabelas e grava seis gráficos na pasta `graficos/`.
- O código usa só pandas e matplotlib. Se o matplotlib não estiver instalado, o script imprime as
  tabelas e avisa. Para instalar, rode `python -m pip install matplotlib`. Esse comando precisa de
  internet e o sandbox bloqueia a rede: peça permissão a quem está usando antes de rodar.
- Para conferir se rodou certo: 2.382 processos entram na análise de êxito, e Transporte aéreo tem
  taxa de êxito de 0,579, em 195 casos.

## Onde colocar o código

- `analise_2.py` é a análise de referência da aula. Não sobrescreva esse arquivo: os gráficos dele
  são os que aparecem nos slides.
- Cada análise pedida vira um arquivo novo em `analises/`, com nome descritivo (por exemplo,
  `analises/exito_por_tribunal.py`), que importa as funções do `analise_2.py` e imprime o resultado.
  Crie a pasta se ela não existir. Rode a partir da pasta do repositório, com
  `python -m analises.exito_por_tribunal` (sem o `.py`): `python analises/exito_por_tribunal.py`
  não encontra o `analise_2`.
- Gráficos novos vão para `graficos/`, com nome descritivo.
- Funções novas têm docstring em português.
