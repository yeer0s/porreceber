# Contribuir · Contributing

Obrigado. Este repositório lida com prazos que decidem se alguém paga ou não paga
uma dívida, por isso as regras são mais apertadas do que o normal.

*Thank you. This repository deals with periods that decide whether someone pays a
debt, so the rules are tighter than usual.*

## As três regras que não se negoceiam

### 1. Uma afirmação sobre a lei precisa do texto da lei

Se alterar um prazo, um mecanismo ou uma porta de recusa, o artigo tem de estar
em `assets/law/`, **verbatim**, com fonte e data. O gate falha se um regime citar
um artigo que não esteja lá — não por rigor cerimonial, mas porque uma citação
inventada é indistinguível de uma citação correcta para quem lê.

Paráfrase não serve. «Li algures que são cinco anos» não serve. Nem a memória de
um modelo de linguagem, incluindo a do autor original destas linhas.

### 2. Um teste novo tem de saber ficar vermelho

Antes de submeter, prove que o seu teste falha quando o comportamento que ele
protege é removido. Se não consegue fazê-lo falhar, ele não protege nada.

```bash
python scripts/sweep.py --self-test   # o gate sabe falhar e voltar a passar?
python scripts/mutants.py             # os invariantes de produto estão mesmo a guardar?
```

Adicionou um invariante de produto? Adicione o mutante correspondente em
`scripts/mutants.py`. Um invariante sem mutante entra no repositório por
observação, não por teste.

### 3. Nada de rede, nunca

Zero dependências. Zero chamadas de rede. Zero telemetria. Não é uma preferência
de estilo — é a razão pela qual alguém confia as suas dívidas a este programa.

```bash
python scripts/offline_audit.py
```

## Antes de abrir um PR

```bash
python scripts/oracle.py --crosscheck
python scripts/oracle.py --mutation-test
python scripts/sweep.py --verboso
python scripts/sweep.py --self-test
python scripts/mutants.py
python scripts/offline_audit.py --selftest
```

Se alterar o número de verificações, actualize a contagem no `SKILL.md` e nos
dois READMEs — há um check que falha de propósito quando essa contagem envelhece.

## O contributo mais valioso

**Jurisprudência.** O maior limite declarado deste repositório é que nenhum caso
dourado vem de uma sentença real: o corpus prova coerência com o texto legal, não
com a prática dos tribunais. Um acórdão que contrarie um resultado do motor vale
mais do que qualquer refactor.

Abra um *issue* com a referência do acórdão, o tribunal, a data e o ponto
concreto em que o motor diverge.

## O que não é aceite

- Remover ou suavizar avisos (arts. 303.º, 304.º n.º 2, 312.º, 314.º). São o
  produto, não ruído.
- Fazer o motor responder onde hoje recusa, sem o estatuto que fundamente a nova
  resposta.
- Qualquer coisa que faça o motor declarar uma dívida extinta. Ele não pode
  saber isso, e há um check que o impede.

## Código de conduta

Seja decente. Estamos a construir uma coisa que ajuda pessoas com dívidas, que
raramente é o melhor dia da vida delas.
