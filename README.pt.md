<p align="center">
  <img src="docs/images/porreceber-wide-light-1k.svg#gh-light-mode-only" alt="porreceber" width="640">
  <img src="docs/images/porreceber-wide-dark-1k.svg#gh-dark-mode-only" alt="porreceber" width="640">
</p>

<p align="center">
  <b>Aquela dívida antiga ainda pode ser cobrada?</b><br>
  Prescrição e caducidade em Portugal, calculadas <i>offline</i>, com o artigo que
  as fundamenta — e os erros que destroem a sua própria defesa.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/licen%C3%A7a-MIT-blue.svg" alt="MIT">
  <img src="https://img.shields.io/badge/depend%C3%AAncias-0-brightgreen.svg" alt="zero dependências">
  <img src="https://img.shields.io/badge/rede-nenhuma-brightgreen.svg" alt="sem rede">
  <img src="https://img.shields.io/badge/verifica%C3%A7%C3%B5es-28-brightgreen.svg" alt="28 verificações">
</p>

<p align="center">
  <a href="README.md"><b>🇬🇧 Read in English</b></a> ·
  <a href="SKILL.md">Skill</a> ·
  <a href="AVISO-FORMAL.md">Aviso formal</a> ·
  <a href="https://mowei.pt">mowei.pt</a>
</p>

---

> **Isto não é aconselhamento jurídico.** É uma ferramenta de apoio à decisão.
> Os factos e a decisão são de quem os introduz. Ver [`AVISO-FORMAL.md`](AVISO-FORMAL.md).

## A carta que toda a gente acaba por receber

> *«Regularize a sua situação: 340,00 € — fatura de água, 2021.»*

A pergunta é simples. A resposta honesta quase nunca é:

**O prazo não extingue a dívida.** Cria uma *faculdade de recusar* o cumprimento
(art. 304.º n.º 1). E o tribunal **não pode** conhecer da prescrição de ofício —
tem de ser **invocada** (art. 303.º). Um prazo que decorreu e nunca foi invocado
não produz efeito nenhum.

**Pagar é uma porta que só abre num sentido.** O dinheiro pago numa dívida
prescrita **não se reavê** — nem que ignorasse a prescrição (art. 304.º n.º 2). O
mesmo vale para reconhecer a dívida ou prestar garantias. Um «pago qualquer coisa
só para resolver isto» pode custar-lhe a defesa inteira, para sempre.

**E a contra-intuitiva.** Nas prescrições *presuntivas* a lei presume que a
dívida **foi paga** (art. 312.º). Quem alegar em juízo que *nunca pagou* pratica
acto incompatível com essa presunção — a dívida considera-se **confessada**
(art. 314.º). Há pessoas que destroem o próprio caso ao dizer a verdade no sítio
errado.

O `porreceber` existe porque são estes quatro factos que decidem o desfecho, e
nenhum deles é o que uma pessoa razoavelmente assume.

## Começar

Sem instalação. Sem dependências. Python 3.8+.

```bash
git clone https://github.com/yeer0s/porreceber.git && cd porreceber
python scripts/prescricao.py --categoria servico_publico_essencial --data-inicio 2025-01-15
```

```bash
python scripts/prescricao.py --categorias   # os 12 regimes modelados
python scripts/prescricao.py --recusas      # o que recusa analisar, e ao abrigo de que artigo
python scripts/prescricao.py --caso caso.json --json
```

## A distinção que quase todas as ferramentas erram

**A Lei 23/96 art. 10.º não é um prazo de seis meses.** São três mecanismos:

| | Mecanismo | Interrompe-se? |
|---|---|---|
| **n.º 1** | **prescrição** do preço do serviço prestado | sim — arts. 323.º, 325.º |
| **n.º 2** | **caducidade** da diferença após pagamento inferior | **não** — art. 328.º |
| **n.º 4** | prazo para propor acção ou injunção | prazo processual autónomo |

Reconhecer a dívida **reinicia o n.º 1 do zero** e **não o interrompe** no n.º 2.
Colapsar os dois num único «seis meses» produz respostas erradas nos dois
sentidos. O caso dourado `cad-01` existe só para segurar esta linha.

**Mas o art. 328.º não é o fim da história** — e a primeira versão deste motor
errou aqui. O art. 328.º proíbe *suspensão e interrupção*. Não proíbe o
**impedimento**, que é um terceiro mecanismo: art. 331.º n.º 1 (acto tempestivo
com efeito impeditivo), art. 331.º n.º 2 (reconhecimento, sendo o direito
disponível) e art. 332.º n.º 1 (acção proposta a tempo). Por isso o motor
**recusa** acções judiciais sobre prazos de caducidade, e o aviso do
reconhecimento diz que a questão está em aberto em vez de a fechar.

## O que se recusa a fazer

O motor **recusa** casos que não consegue modelar, e cada recusa cita o artigo
que a obriga. Isto é a funcionalidade:

| Facto | Porquê | Artigo |
|---|---|---|
| alta tensão | excluída do regime | Lei 23/96 art. 10.º n.º 5 |
| herança / devedor falecido | não se completa antes de 6 meses após haver quem represente | 322.º |
| fiador ou garantia prestada | regime fora dos arts. 300.º–333.º | 304.º n.º 2 |
| dívida solidária | rege-se pelos arts. 512.º e ss. | — |
| dívida assumida por terceiro | a assunção pode ser reconhecimento interruptivo | 308.º n.º 2 |
| relação do art. 318.º | a prescrição **não começa nem corre** | 318.º |
| menor / maior acompanhado | não é pausa: é proibição de **completar** | 320.º |
| militar em guerra | não começa nem corre | 319.º |
| força maior ou dolo | só nos últimos três meses do prazo | 321.º |
| acção judicial sobre prazo de **caducidade** | o art. 328.º não exclui o **impedimento** | 331.º n.º 1 |
| título executivo obtido **depois** do prazo | caso julgado consolidado; «pode invocar» levaria a ignorar uma execução | 303.º |

Uma ferramenta que responde a tudo está a mentir sobre alguma coisa.

## Como se sabe que está certo

Não por a suite estar verde. Por ela **saber ficar vermelha**:

```bash
python scripts/oracle.py --crosscheck      # 1836 combinações, dois caminhos independentes
python scripts/oracle.py --mutation-test   # prova que o crosscheck apanha aritmética corrompida
python scripts/oracle.py --blind-spots     # o que este motor NÃO cobre
python scripts/sweep.py --self-test        # prova que o gate sabe falhar e voltar a passar
python scripts/mutants.py                  # 10 mutantes contra os invariantes de produto
python scripts/offline_audit.py            # prova estrutural de que não há caminho para a rede
python scripts/sweep.py                    # 28 verificações
```

- **Duas implementações independentes.** O `prescricao.py` soma meses ao
  calendário; o `oracle.py` resolve o termo por pesquisa binária sobre uma
  contagem de meses completos, sem aritmética de datas. Concordarem por acidente
  exigiria que ambos errassem da mesma maneira.
- **Oráculo de conjunto exacto.** Cada caso dourado declara o conjunto **exacto**
  de avisos esperados. Um aviso a mais reprova tanto quanto um a menos — senão o
  motor podia deixar de emitir o aviso do art. 304.º n.º 2 e continuar verde.
- **Mutantes dirigidos aos invariantes que protegem o utilizador**, não só à
  aritmética: nunca declarar a dívida extinta; avisar sempre do art. 304.º n.º 2
  quando uma **prescrição** decorreu; avisar da confissão nas presuntivas; nunca
  *interromper* a caducidade; nunca citar regras da prescrição numa saída de
  caducidade. Morrem os dez.
- **Uma verificação que falha quando os números deste README envelhecem.**

### Direcção do erro — declarada, e verificada

Perante dúvida, o motor diz que o prazo **ainda corre**. Nunca o contrário.

O dano é assimétrico: dizer «já prescreveu» a quem tem uma dívida viva leva a
ignorar uma citação e a uma condenação à revelia. O erro inverso custa, no
máximo, um pagamento — e o motor avisa **antes** de qualquer pagamento, ao abrigo
do art. 304.º n.º 2.

Até 2026-07-27 isto era apenas uma **declaração**: a verificação que a guardava
lia uma string de um ficheiro JSON, e ficou verde durante três violações reais
encontradas por revisão adversarial. Existem agora duas verificações — uma lê a
declaração, a outra testa *comportamento*: adiantar o relógio nunca pode
transformar `DECORRIDO` em `A_CORRER`, e um acto do credor dentro do prazo nunca
pode aproximar o termo.

### Ponto cego — declarado

O motor **não** verifica se a categoria escolhida é a juridicamente correcta para
os factos. Qualificar mal a dívida produz um prazo errado que **os dois caminhos**
confirmam alegremente. É a maior fonte de erro do produto e nenhum teste
automático a apanha. Fica dito em voz alta, e não enterrado.

## Totalmente offline — por estrutura, não por promessa

Zero dependências. Zero chamadas de rede. Zero telemetria. Nada sobre a sua
dívida, as suas datas ou o seu nome sai da máquina — não existe caminho de código
por onde pudesse sair. O `offline_audit.py` prova-o a partir da AST e traz um
self-test que prova que a própria auditoria sabe falhar.

Corre contra um modelo local sem internet nenhuma. As suas dívidas não são dados
de treino de ninguém.

## Fontes

Texto legal capturado verbatim em [`assets/law/`](assets/law/), com data e método:

- **Código Civil, arts. 300.º–333.º** — os 34 artigos, sem lacunas
- **Código Civil, arts. 279.º, 296.º–299.º** — a convenção de contagem que todos
  os prazos deste motor implementam, e a regra supletiva prescrição/caducidade
- **Lei n.º 23/96, arts. 1.º e 10.º**

Fonte: PGDLisboa (compilação privada). **Para efeitos legais vale o Diário da
República.** O gate falha se algum regime citar um artigo ausente das capturas.

## Relacionados

- **[AoCentimo](https://github.com/yeer0s/AoCentimo)** — motor de IRS português
- **[recibosegarantia](https://github.com/yeer0s/recibosegarantia)** — recibos, QR e-Fatura, garantias UE

## Licença

MIT — ver [`LICENSE`](LICENSE). Sem modificações, sem restrições adicionais.

## Apoiar

Livre e MIT, para sempre. Se lhe poupou um pagamento que não devia:

☕ [Buy me a coffee](https://buymeacoffee.com/letsmoweis) · [Ko-fi](https://ko-fi.com/letsmowei)

Construído a par do **[mowei.pt](https://mowei.pt)** — comparação de energia,
telecomunicações, seguros, banca e mais.
