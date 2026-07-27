<p align="center">
  <img src="docs/images/porreceber-wide-light-1k.svg#gh-light-mode-only" alt="porreceber" width="640">
  <img src="docs/images/porreceber-wide-dark-1k.svg#gh-dark-mode-only" alt="porreceber" width="640">
</p>

<p align="center">
  <b>Is that old debt still collectable?</b><br>
  Portuguese limitation periods (<i>prescrição</i>) and forfeiture (<i>caducidade</i>),
  computed offline, with the article that governs — and the mistakes that destroy your own defence.
</p>

<p align="center">
  <a href="#licença--licence"><img src="https://img.shields.io/badge/licence-MIT-blue.svg" alt="MIT"></a>
  <img src="https://img.shields.io/badge/dependencies-0-brightgreen.svg" alt="zero dependencies">
  <img src="https://img.shields.io/badge/network-none-brightgreen.svg" alt="no network">
  <img src="https://img.shields.io/badge/checks-28-brightgreen.svg" alt="28 checks">
  <img src="https://img.shields.io/badge/statute-39%20articles%20verbatim-informational.svg" alt="statute">
</p>

<p align="center">
  <a href="README.pt.md"><b>🇵🇹 Ler em português</b></a> ·
  <a href="SKILL.md">Skill</a> ·
  <a href="AVISO-FORMAL.md">Formal notice</a> ·
  <a href="https://mowei.pt">mowei.pt</a>
</p>

---

> **This is not legal advice.** It is a decision-support tool. You supply the
> facts, you own the decision. See [`AVISO-FORMAL.md`](AVISO-FORMAL.md).

## The letter everybody eventually gets

> *"Regularize a sua situação: 340,00 € — fatura de água, 2021."*

The question is simple. The honest answer almost never is:

**A limitation period does not extinguish the debt.** It creates a *right to
refuse* (art. 304.º n.º 1). And a Portuguese court **may not raise it for you** —
it must be actively invoked (art. 303.º). A period that ran out and was never
invoked does precisely nothing.

**Paying it back is a one-way door.** Money paid on a time-barred debt **cannot
be recovered** — even if you had no idea it was time-barred (art. 304.º n.º 2).
So can acknowledging it, or offering a guarantee. A "let me just pay something to
make this go away" can cost you the entire defence, permanently.

**And the counter-intuitive one.** For *presumptive* limitation the law presumes
the debt **was paid** (art. 312.º). Argue in court that you *never paid* and you
have practised an act incompatible with that presumption — the debt is deemed
**confessed** (art. 314.º). People destroy their own case by telling the truth in
the wrong forum.

`porreceber` exists because those four facts decide the outcome, and none of them
are what a person reasonably assumes.

## Quick start

No install. No dependencies. Python 3.8+.

```bash
git clone https://github.com/yeer0s/porreceber.git && cd porreceber
python scripts/prescricao.py --categoria servico_publico_essencial --data-inicio 2025-01-15
```

```
[PRAZO DECORRIDO]  Servico publico essencial - preco do servico prestado
mecanismo: prescricao_extintiva  (Lei n.º 23/96 art. 10.º)

inicio efectivo: 2025-01-15
prazo:           6 meses
termo:           2025-07-15  (-377 dias face a 2026-07-27)

COMO SE CHEGOU AQUI
  . Prazo base: 6 meses a contar de 2025-01-15 (Lei n.º 23/96 art. 10.º) -> termo em 2025-07-15.

O QUE ISTO SIGNIFICA
  O prazo aparenta ter decorrido em 2025-07-15. Isto NAO extingue a divida.
  O art. 303.º proibe o tribunal de conhecer da prescricao de oficio...

  O art. 304.º n.º 2 e definitivo: pagamento feito espontaneamente em cumprimento
  de obrigacao prescrita NAO PODE SER REPETIDO...
```

```bash
python scripts/prescricao.py --categorias   # the 12 regimes modelled
python scripts/prescricao.py --recusas      # what it refuses, and under which article
```

## The distinction nearly every tool gets wrong

**Lei 23/96 art. 10.º is not a six-month rule.** It is three mechanisms:

| | Mechanism | Interruptible? |
|---|---|---|
| **n.º 1** | **prescription** of the price of the service | yes — arts. 323.º, 325.º |
| **n.º 2** | **forfeiture** of the shortfall after an underpayment | **no** — art. 328.º |
| **n.º 4** | deadline to bring the action/injunção | separate procedural period |

Acknowledging the debt **restarts n.º 1 from zero** and does **not interrupt** n.º 2.
Collapse them into one "six months" and you get wrong answers in both directions.
Golden case `cad-01` exists solely to hold that line.

**But art. 328.º is not the end of the story** — and the first version of this
engine got that wrong. Art. 328.º bars *suspension and interruption*. It does not
bar **impediment**, a third mechanism: art. 331.º n.º 1 (a timely act with
impeding effect), art. 331.º n.º 2 (acknowledgment, where the right is
disposable), and art. 332.º n.º 1 (a tempestively filed action). So the engine
**refuses** court actions on forfeiture periods, and the acknowledgment warning
says the question is open instead of closing it.

## What it refuses to do

The engine **refuses** cases it cannot model, and every refusal cites the article
forcing it. This is the feature:

| Fact | Why | Article |
|---|---|---|
| high-voltage electricity | excluded from the regime | Lei 23/96 art. 10.º n.º 5 |
| estate / deceased debtor | cannot complete before 6 months after there is someone to invoke against | 322.º |
| guarantor or security given | regime lives outside arts. 300.º–333.º | 304.º n.º 2 |
| joint and several debt | governed by arts. 512.º ff. | — |
| debt assumed by a third party | the assumption may itself be an interrupting acknowledgment | 308.º n.º 2 |
| art. 318.º relationships | limitation **neither starts nor runs** | 318.º |
| minor / accompanied adult | not a pause — a bar on **completing** | 320.º |
| military in wartime | neither starts nor runs | 319.º |
| force majeure or bad faith | only in the final three months | 321.º |
| court action on a **forfeiture** period | art. 328.º does not exclude **impediment** | 331.º n.º 1 |
| executive title obtained **after** the period | res judicata consolidated; "you may invoke" would invite ignoring an execution | 303.º |

A tool that answers everything is lying about something.

## How you know it's right

Not because the suite is green. Because it **knows how to go red**:

```bash
python scripts/oracle.py --crosscheck      # 1836 combinations, two independent paths
python scripts/oracle.py --mutation-test   # proves the crosscheck detects corrupted arithmetic
python scripts/oracle.py --blind-spots     # what this engine does NOT cover
python scripts/sweep.py --self-test        # proves the gate can fail and recover
python scripts/mutants.py                  # 10 mutants against the product invariants
python scripts/offline_audit.py            # structural proof there is no network path
python scripts/sweep.py                    # 28 checks
```

- **Two independent implementations.** `prescricao.py` adds months to the
  calendar; `oracle.py` binary-searches a completed-months count with no date
  arithmetic at all. Agreeing by accident would require both to be wrong the same
  way.
- **Exact-set oracle on warnings.** Each golden case declares the *exact* set of
  warnings expected. One warning too many fails as hard as one too few —
  otherwise the engine could quietly stop emitting the art. 304.º n.º 2 warning
  and stay green.
- **Mutants aimed at the invariants that protect the user**, not just the
  arithmetic: never declare a debt extinguished; always warn about art. 304.º
  n.º 2 when a **prescription** has run; always warn about confession in
  presumptive cases; never let forfeiture be *interrupted*; never let a forfeiture
  output cite prescription rules. All ten mutants die.
- **A check that fails when this README's own numbers go stale.**

### Declared direction of error

When uncertain, the engine says the period is **still running** — never the
reverse. The harm is asymmetric: telling someone "it's time-barred" when it isn't
leads to an ignored summons and a default judgment. The opposite error costs, at
worst, a payment — and the engine warns before any payment, under art. 304.º n.º 2.

Until 2026-07-27 this was only a **declaration**: the check that guarded it read a
string from a JSON file, and stayed green through three real violations found by
adversarial review. There are now two checks — one reads the declaration, the
other tests *behaviour*: advancing the clock can never turn `DECORRIDO` into
`A_CORRER`, and a creditor's act inside the period can never bring the termo
closer.

### Declared blind spot

The engine does **not** verify that the category you chose is the legally correct
one. Mischaracterise the debt and you get a wrong period that **both** paths
confirm happily. It is the largest source of error in the product and no
automated test catches it. Said out loud rather than buried.

## Fully offline — structurally, not as a promise

Zero dependencies. Zero network calls. Zero telemetry. Nothing about your debt,
your dates or your name leaves the machine — there is no code path by which it
could. `offline_audit.py` proves it from the AST and ships with a `--selftest` that
proves the audit itself can fail.

Runs against a local model with no internet at all. Your debts are nobody's
training data.

## Sources

Statute captured verbatim in [`assets/law/`](assets/law/), with date and method:

- **Código Civil, arts. 300.º–333.º** — all 34 articles, no gaps
- **Código Civil, arts. 279.º, 296.º–299.º** — the counting convention every
  period in this engine implements, and the prescription/forfeiture default rule
- **Lei n.º 23/96, arts. 1.º and 10.º**

Source: PGDLisboa (a private compilation). **The *Diário da República* is
authoritative.** The gate fails if any regime cites an article absent from the
captures.

## Related

- **[AoCentimo](https://github.com/yeer0s/AoCentimo)** — Portuguese IRS engine
- **[recibosegarantia](https://github.com/yeer0s/recibosegarantia)** — receipts, e-Fatura QR, EU guarantee tracking

## Licença · Licence

MIT — see [`LICENSE`](LICENSE). Unmodified, no additional restrictions.

## Support

Free and MIT, forever. If it saved you a payment you didn't owe:

☕ [Buy me a coffee](https://buymeacoffee.com/letsmoweis) · [Ko-fi](https://ko-fi.com/letsmowei)

Built alongside **[mowei.pt](https://mowei.pt)** — Portuguese consumer comparison
for energy, telecoms, insurance, banking and more.
