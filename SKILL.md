---
name: porreceber
description: Use when a Portuguese consumer receives a demand for an old debt — a utility bill from years ago, a debt-collector letter, a "regularize a sua situação" SMS — and needs to know whether the limitation period (prescrição) or forfeiture period (caducidade) has run, which article governs, and what would destroy their own defence. Runs entirely offline.
license: MIT
---

# porreceber — prescrição e caducidade de dívidas em Portugal

> **Isto não é aconselhamento jurídico.** É uma ferramenta de apoio à decisão.
> Os factos, as datas e a decisão são de quem os introduz. Leia o `AVISO-FORMAL.md`.

## O problema que resolve

Chega uma carta a exigir 340 € de uma factura de água de 2021. A pergunta do
utente é simples — *ainda tenho de pagar isto?* — e a resposta real quase nunca
é a que ele espera:

- O prazo **não extingue** a dívida. Cria uma **faculdade de recusar** (art. 304.º n.º 1).
- O tribunal **não pode** conhecer da prescrição sozinho. Tem de ser **invocada** (art. 303.º).
- Quem paga uma dívida prescrita **não reavê o dinheiro** — nem que ignorasse a
  prescrição (art. 304.º n.º 2). Um "pagamento por conta para resolver isto"
  pode custar a defesa inteira.
- Nas prescrições **presuntivas**, a lei presume que a dívida **foi paga**
  (art. 312.º). Quem alegar em juízo que *nunca pagou* confessa a dívida
  (art. 314.º) e destrói a própria defesa. É contra-intuitivo e é onde as
  pessoas se enganam sozinhas.

## O que faz

```bash
python scripts/prescricao.py --categoria servico_publico_essencial \
                             --data-inicio 2025-01-15
```

Devolve: mecanismo aplicável, prazo, data de início efectiva, o que o
interrompeu, a data de termo, **e os avisos que impedem o utente de se
prejudicar a si próprio**.

```bash
python scripts/prescricao.py --categorias   # regimes modelados
python scripts/prescricao.py --recusas      # o que se recusa a analisar, e porquê
python scripts/prescricao.py --caso c.json --json
```

## A distinção que quase todas as ferramentas erram

A Lei 23/96 art. 10.º **não é um prazo de seis meses**. São três mecanismos:

| N.º | Mecanismo | Interrompe? |
|---|---|---|
| n.º 1 | **prescrição** do preço do serviço | sim — art. 323.º, 325.º |
| n.º 2 | **caducidade** da diferença após pagamento a menos | **não** — art. 328.º |
| n.º 4 | prazo para propor acção/injunção | prazo processual autónomo |

Um reconhecimento de dívida reinicia o n.º 1 do zero e **não o interrompe** no n.º 2.
Colapsar os dois num único "seis meses" produz respostas erradas nos dois
sentidos. O caso dourado `cad-01` existe só para isso.

**Mas o art. 328.º não é o fim da história**, e a primeira versão deste motor
errou aqui. O art. 328.º proíbe **suspensão e interrupção** — não proíbe o
**impedimento**, que é um terceiro mecanismo:

- **art. 331.º n.º 1** — impede a caducidade a prática, dentro do prazo, do acto
  a que a lei atribua efeito impeditivo;
- **art. 331.º n.º 2** — e também o reconhecimento, quando o prazo respeita a
  direito disponível;
- **art. 332.º n.º 1** — acção tempestivamente proposta convoca o art. 327.º n.º 3.

Por isso o motor **recusa** analisar acções judiciais sobre prazos de caducidade,
e o aviso do reconhecimento diz que a questão está em aberto em vez de a fechar.

## O que se recusa a fazer

O motor **recusa** casos que não consegue modelar, e cada recusa cita o artigo
que a obriga. Isto é a funcionalidade, não uma limitação:

| Facto | Porquê | Artigo |
|---|---|---|
| alta tensão | excluída do regime | Lei 23/96 art. 10.º n.º 5 |
| herança / devedor falecido | não se completa antes de 6 meses após haver quem represente | 322.º |
| fiador ou garantia prestada | regime fora dos arts. 300.º–333.º | 304.º n.º 2 |
| dívida solidária | propagação rege-se pelos arts. 512.º e ss. | — |
| dívida assumida por terceiro | a assunção pode ser reconhecimento interruptivo | 308.º n.º 2 |
| relação do art. 318.º | a prescrição **não começa nem corre** | 318.º |
| menor / maior acompanhado | não é pausa: é proibição de **completar** | 320.º |
| militar em guerra | não começa nem corre | 319.º |
| força maior ou dolo | só nos últimos três meses do prazo | 321.º |
| acção judicial sobre prazo de **caducidade** | o art. 328.º não exclui o **impedimento** | 331.º n.º 1 |
| título executivo obtido **depois** do prazo | caso julgado consolidado; dizer "pode invocar" levaria a ignorar uma execução | 303.º |

## Como se sabe que está certo

Não se sabe por a suite estar verde. Sabe-se por ela **saber ficar vermelha**:

```bash
python scripts/oracle.py --crosscheck      # 1836 combinações, dois caminhos independentes
python scripts/oracle.py --mutation-test   # prova que o crosscheck detecta aritmética corrompida
python scripts/oracle.py --blind-spots     # o que este motor NÃO cobre
python scripts/sweep.py --self-test        # prova que o gate sabe falhar e voltar a passar
python scripts/mutants.py                  # mutantes contra os invariantes de produto
python scripts/sweep.py                    # 28 verificações
python scripts/offline_audit.py            # prova estrutural de que não há rede
```

- **Dois caminhos independentes.** `prescricao.py` soma meses ao calendário;
  `oracle.py` resolve o termo por pesquisa binária sobre uma contagem de meses
  completos, sem aritmética de datas. Concordarem por acidente exigiria que
  ambos errassem da mesma maneira.
- **Oráculo de conjunto exacto.** Os avisos esperados de cada caso dourado são
  um conjunto **exacto**: um aviso a mais reprova tanto quanto um a menos. Sem
  isto, o motor podia deixar de emitir o aviso do art. 304.º n.º 2 e continuar verde.
- **Invariantes de produto**, não só de aritmética: nunca declarar uma dívida
  extinta; avisar sempre do art. 304.º n.º 2 quando uma **prescrição** decorreu;
  avisar da confissão nas presuntivas; a caducidade nunca ser *interrompida*; e
  uma saída de caducidade nunca citar regras da prescrição.
- **Pontos cegos declarados**, incluindo o maior de todos: o motor não verifica
  se a **categoria escolhida** é a juridicamente correcta para os factos.
  Qualificar mal a dívida produz um prazo errado que os dois caminhos confirmam
  alegremente.

## Direcção do erro — declarada, e verificada

Perante dúvida, o motor diz que o prazo **ainda corre**. Nunca o contrário.

O dano é assimétrico: dizer "já prescreveu" a quem tem uma dívida viva leva a
ignorar uma citação e a uma condenação à revelia. Dizer "ainda corre" a quem já
podia recusar custa, no máximo, um pagamento — e por isso o motor avisa **antes**
de qualquer pagamento, ao abrigo do art. 304.º n.º 2.

Isto era, até 2026-07-27, apenas uma **declaração**: havia uma verificação, mas
ela só lia a string `"conservadora_para_o_devedor"` do JSON. Ficou verde durante
as três violações reais que a revisão adversarial encontrou. Uma política
afirmada não é uma política testada.

Hoje existem duas verificações: uma lê a declaração, a outra testa
**comportamento** — adiantar o relógio nunca pode transformar `DECORRIDO` em
`A_CORRER`, e um acto do credor dentro do prazo nunca pode aproximar o termo.

## Offline

Sem dependências, sem rede, sem telemetria. `offline_audit.py` prova-o por
análise da AST, não por promessa. Nenhuma dívida, data ou nome sai da máquina.

## Fontes

Texto legal capturado verbatim em `assets/law/`, com data e método:

- Código Civil, **arts. 300.º–333.º** — os 34 artigos, sem lacunas
- Código Civil, **arts. 279.º, 296.º–299.º** — a convenção de contagem e a
  qualificação prescrição/caducidade
- **Lei n.º 23/96**, arts. 1.º e 10.º

Fonte: PGDLisboa (compilação privada). **Para efeitos legais vale o Diário da
República.** O gate falha se algum regime citar um artigo que não esteja nas capturas.

---

## Changelog

### v1.0.0 — 2026-07-27

Versão inicial. Publicada **depois** de uma revisão adversarial que a rejeitou —
o que segue descreve o que essa revisão encontrou, porque a versão que ela
rejeitou parecia tão saudável como esta: 26/26 verificações verdes, crosscheck
1683/1683, seis mutantes mortos, auditoria offline limpa.

**Três defeitos que faziam o motor declarar decorrido um prazo vivo** — exactamente
a saída perigosa contra a qual o projecto foi desenhado:

1. **Acção tempestiva sobre um prazo de caducidade era ignorada.** O motor lia o
   art. 328.º ("não se suspende nem se interrompe") como "nenhum acto produz
   efeito", e nunca mencionava o **impedimento** dos arts. 331.º e 332.º. Um
   consumidor que propôs acção em Janeiro era informado em Julho de que o direito
   do prestador tinha caducado em Maio. Passou a ser recusa fundamentada.
2. **A requalificação do art. 311.º evaporava-se na interrupção seguinte.** Depois
   de um título executivo elevar o prazo a 20 anos, um reconhecimento posterior
   reiniciava o prazo *curto*, porque o cálculo voltava à categoria. O art. 326.º
   n.º 2 manda seguir o prazo primitivo *"salvo o disposto no artigo 311.º"*. A
   saída chegava a imprimir `20 anos (requalificado)` e um termo de 2 anos na
   mesma página — contradizia-se a si própria e nada reparou.
3. **Fronteira invertida.** `hoje >= termo` dava o prazo por decorrido no próprio
   dia do termo. O art. 279.º al. c) diz que termina *"às 24 horas do dia que
   corresponda"*. Pior: o caso dourado `spe-03` afirmava o lado errado, pelo que
   **o gate passou a impor o defeito**. A convenção de contagem que todo o motor
   implementa estava, além disso, fora do corpo legal capturado.

**Mais quatro correcções:** título executivo posterior ao termo recebia o aviso
de renúncia tácita redigido para o *reconhecimento* (agora recusa); saídas de
caducidade citavam os arts. 303.º e 304.º n.º 2, que são regras da *prescrição*;
o compromisso arbitral não recebia o aviso do art. 327.º n.º 1, apesar de o
artigo o nomear expressamente; e faltava a categoria do **art. 310.º al. e)**
(prestações de crédito com juros) — a dívida mais comum nas cartas de cobrança,
que sem categoria própria caía em `ordinário` e rendia 20 anos em vez de 5.

**Duas verificações eram teatro** e foram substituídas: a "direcção do erro" só
lia uma string do JSON (ficou verde durante as três violações acima), e a
verificação de promessas de aconselhamento estava ancorada a fim de linha,
deixando passar qualquer promessa no meio de uma frase.

Estado final: 12 categorias, 3 mecanismos, **11 portas de recusa**, **26 casos
dourados**, **28 verificações**, e uma verificação que falha se este ficheiro
desactualizar a contagem.

**Limites honestos desta versão:**

- Nenhum caso dourado vem de uma sentença real. O corpus prova coerência com o
  texto legal, não com a prática dos tribunais.
- A revisão adversarial que produziu esta lista correu numa **só linhagem** de
  modelo — a segunda não arrancou. Um segundo par de olhos independente ainda
  não passou por aqui.
- Se o prazo do art. 10.º n.º 2 da Lei 23/96 é matéria disponível para efeitos do
  art. 331.º n.º 2 é questão contestada. O motor não a decide, e di-lo.

---

🔗 Comparar contratos, tarifas e alternativas: **[mowei.pt](https://mowei.pt)**
☕ [Buy me a coffee](https://buymeacoffee.com/letsmoweis) · [Ko-fi](https://ko-fi.com/letsmowei)
