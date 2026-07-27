# Aviso Formal · Formal Notice

> **Estatuto deste documento.** Isto é um **aviso**, não uma condição de licença.
> O software é distribuído sob a licença MIT, sem modificações e sem restrições
> adicionais — ver `LICENSE`. Nada neste ficheiro limita os direitos que a MIT
> concede: usar, copiar, modificar, fundir, publicar, distribuir, sublicenciar e
> vender. Se alguma frase aqui parecer contradizer a MIT, **prevalece a MIT**.
>
> *Status of this document. This is a **notice**, not a licence condition. The
> software is distributed under the MIT licence, unmodified and with no
> additional restrictions — see `LICENSE`. Nothing here limits the rights MIT
> grants. Where this file appears to conflict with MIT, **MIT prevails**.*

---

## Português

### 1. Isto não é aconselhamento jurídico

`porreceber` é uma **ferramenta de apoio à decisão**. Não é aconselhamento
jurídico, financeiro nem fiscal, e não substitui advogado, solicitador ou
qualquer profissional habilitado.

Nem os autores nem o projecto Mowei exercem advocacia, nem estabelecem qualquer
relação profissional com quem usa este software.

### 2. A responsabilidade é de quem decide

O motor calcula prazos a partir dos factos **que o utilizador introduz**. Não os
verifica, não os pode verificar, e não tem forma de saber se estão certos.

Em concreto, o utilizador é responsável por:

- **as datas** — uma data de início errada produz um prazo errado que passa em
  todos os testes deste repositório;
- **a qualificação jurídica** — escolher a categoria errada é a maior fonte de
  erro deste produto, e **nenhum teste automático a apanha**. Está declarada
  como ponto cego em `scripts/oracle.py --blind-spots`;
- **a decisão** — agir, não agir, pagar, não pagar, invocar ou não invocar.

Esta responsabilidade não é uma formalidade defensiva: é uma consequência
estrutural. O software corre **inteiramente na máquina do utilizador**, sem rede
e sem telemetria. Nada é enviado a lado nenhum, ninguém do outro lado vê o caso,
e portanto ninguém do outro lado o pode validar. A privacidade e a
responsabilidade são o mesmo facto visto de dois lados.

### 3. O que o resultado significa — e o que não significa

Um resultado `PRAZO_DECORRIDO` **não** significa que a dívida está extinta.

- O art. 304.º n.º 1 do Código Civil cria uma **faculdade de recusar** o
  cumprimento — não uma extinção.
- O art. 303.º proíbe o tribunal de conhecer da prescrição **de ofício**: tem de
  ser **invocada**.
- O art. 304.º n.º 2 torna **irrepetível** o pagamento de dívida prescrita, ainda
  que feito com ignorância da prescrição.

Quem tratar um resultado deste software como uma declaração de extinção está a
lê-lo mal, e o próprio software di-lo em cada execução.

### 4. Limites conhecidos, declarados

- O corpus de teste é derivado do **texto legal**, não de sentenças reais. Prova
  coerência com a lei escrita, não com a prática dos tribunais.
- Os textos legais em `assets/law/` vêm de uma **compilação privada** (PGDLisboa).
  Para efeitos legais vale o **Diário da República**.
- A lei muda. Uma captura tem data. Confirme a versão em vigor.
- O motor **recusa** nove classes de casos que não consegue modelar. Uma recusa
  não é uma falha — é a resposta correcta.

### 5. Sem garantia

Nos termos da licença MIT, o software é fornecido **"tal como está"**, sem
garantia de qualquer espécie. Os autores não respondem por quaisquer danos.

### 6. Uso

O software é livre para qualquer uso permitido pela MIT, incluindo comercial.
O projecto foi desenhado a pensar em **particulares** e é sobre esse caso que os
avisos são escritos; quem o use noutro contexto assume a adequação dessa escolha.

---

## English

### 1. This is not legal advice

`porreceber` is a **decision-support tool**. It is not legal, financial or tax
advice, and it does not replace a qualified professional. Neither the authors nor
the Mowei project practise law or enter into any professional relationship with
users of this software.

### 2. Responsibility sits with the person deciding

The engine computes limitation periods from facts **the user supplies**. It does
not verify them and cannot. The user is responsible for the dates, for the legal
characterisation of the debt (the single largest source of error, and one **no
automated test catches** — it is a declared blind spot), and for the decision.

This follows from the architecture: the software runs **entirely on the user's
machine**, with no network and no telemetry. Nothing is transmitted, so nobody on
the other side sees the case — and nobody on the other side can validate it.
Privacy and responsibility are the same fact seen from two sides.

### 3. What a result means

`PRAZO_DECORRIDO` does **not** mean the debt is extinguished. Under the
Portuguese Civil Code it creates a **right to refuse** performance (art. 304.º
n.º 1) which must be **actively invoked** (art. 303.º); a court may not raise it
on its own motion. Payment of a time-barred debt **cannot be recovered**, even if
made in ignorance (art. 304.º n.º 2).

### 4. Declared limits

The test corpus is derived from statutory text, not from real judgments. Statute
in `assets/law/` comes from a private compilation; the *Diário da República* is
authoritative. Law changes; captures are dated. The engine **refuses** nine
classes of case it cannot model — a refusal is the correct answer, not a failure.

### 5. No warranty

Provided **"as is"** under MIT, without warranty of any kind. The authors accept
no liability for any damages.

---

*Última revisão: 2026-07-27 · [mowei.pt](https://mowei.pt)*
