#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mutantes dirigidos aos INVARIANTES DE PRODUTO.

O `--self-test` do sweep corrompe a aritmetica, e a aritmetica e a parte facil.
Os checks que realmente protegem o utilizador - avisar do art. 304.º n.º 2,
avisar da confissao nas presuntivas, nao interromper a caducidade, nunca
declarar a divida extinta - nunca foram vistos a ficar vermelhos.

Um check que nunca ficou vermelho nao esta testado: esta observado.

Cada mutante abaixo desliga UM comportamento e nomeia o check que TEM de o
apanhar. Se o check sobreviver ao mutante, o check nao vale nada.
"""

import io
import os
import re
import sys
import contextlib

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import prescricao  # noqa: E402
import sweep       # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def _correr_silencioso():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        res = sweep.correr()
    return {nome: ok for nome, ok, _ in res}


# ------------------------------------------------------------------- mutantes

def m_sem_aviso_304():
    """Deixa de avisar que o pagamento e irrepetivel (art. 304.º n.º 2)."""
    orig = prescricao._saida

    def patched(*a, **k):
        out = orig(*a, **k)
        out.pop("antes_de_pagar_seja_o_que_for", None)
        return out
    prescricao._saida = patched
    return lambda: setattr(prescricao, "_saida", orig)


def m_sem_aviso_confissao():
    """Deixa de avisar da confissao nas prescricoes presuntivas (art. 314.º)."""
    orig = prescricao._saida

    def patched(*a, **k):
        out = orig(*a, **k)
        out.pop("armadilha_prescricao_presuntiva", None)
        return out
    prescricao._saida = patched
    return lambda: setattr(prescricao, "_saida", orig)


def m_caducidade_interrompivel():
    """Faz a caducidade comportar-se como prescricao (viola o art. 328.º)."""
    orig = prescricao.carregar_regimes

    def patched(*a, **k):
        r = orig(*a, **k)
        r["categorias"]["servico_publico_essencial_diferenca"]["mecanismo"] = \
            "prescricao_extintiva"
        return r
    prescricao.carregar_regimes = patched
    return lambda: setattr(prescricao, "carregar_regimes", orig)


def m_declara_divida_extinta():
    """Passa a dizer ao utilizador que a divida esta extinta."""
    orig = prescricao._saida

    def patched(*a, **k):
        out = orig(*a, **k)
        if out["estado"] == "PRAZO_DECORRIDO":
            out["o_que_isto_significa"] = "A divida esta extinta e nao tem de pagar."
        return out
    prescricao._saida = patched
    return lambda: setattr(prescricao, "_saida", orig)


def m_facto_desconhecido_silencioso():
    """Ignora factos de recusa que nao reconhece, em vez de rebentar."""
    orig = prescricao.analisar

    def patched(caso, *a, **k):
        caso = dict(caso)
        caso["factos"] = {kk: vv for kk, vv in (caso.get("factos") or {}).items()
                          if kk in prescricao.RECUSAS_POR_CHAVE}
        return orig(caso, *a, **k)
    prescricao.analisar = patched
    return lambda: setattr(prescricao, "analisar", orig)


def m_regime_cita_artigo_inventado():
    """Um regime passa a citar um artigo que nao existe nas capturas."""
    orig = prescricao.carregar_regimes

    def patched(*a, **k):
        r = orig(*a, **k)
        r["categorias"]["juros"]["artigo"] = "999.º"
        return r
    prescricao.carregar_regimes = patched
    return lambda: setattr(prescricao, "carregar_regimes", orig)


def m_caducidade_cita_prescricao():
    """Faz uma saida de caducidade citar os arts. 303.º/304.º n.º 2 (regras da prescricao)."""
    orig = prescricao._saida

    def patched(*a, **k):
        out = orig(*a, **k)
        if out["mecanismo"] == "caducidade" and out["estado"] == "PRAZO_DECORRIDO":
            out["o_que_isto_significa"] = (
                "O prazo decorreu. Art. 303.º: tem de ser invocada. Art. 304.º n.º 2: "
                "o pagamento nao pode ser repetido.")
        return out
    prescricao._saida = patched
    return lambda: setattr(prescricao, "_saida", orig)


def m_fronteira_invertida():
    """Volta a dar o prazo por decorrido NO dia do termo (viola o art. 279.º al. c))."""
    orig = prescricao._saida

    def patched(caso, cat, mec, a, inicio, termo, prazo_txt, hoje, regimes):
        out = orig(caso, cat, mec, a, inicio, termo, prazo_txt, hoje, regimes)
        if out["estado"] == "PRAZO_A_CORRER" and out.get("dias_ate_ao_termo") == 0:
            out["estado"] = "PRAZO_DECORRIDO"
        return out
    prescricao._saida = patched
    return lambda: setattr(prescricao, "_saida", orig)


def m_requalificacao_evapora():
    """Interrupcao posterior a um titulo do art. 311.º volta a reiniciar o prazo CURTO."""
    orig = prescricao._add_meses

    def patched(d, n):
        # 240 meses = os 20 anos requalificados; devolve-os ao prazo de 2 anos.
        return orig(d, 24 if n == 240 else n)
    prescricao._add_meses = patched
    return lambda: setattr(prescricao, "_add_meses", orig)


def m_interrupcao_encurta():
    """Faz a interrupcao ANTECIPAR o termo em vez de o reiniciar.

    E a violacao pura da direccao do erro declarada: um acto do CREDOR dentro do
    prazo passaria a APROXIMAR o termo, e o motor diria `decorrido` a quem tem uma
    divida bem viva.

    Repare-se que encurtar o prazo UNIFORMEMENTE nao serve como mutante aqui: o
    check e relativo (compara o caso com e sem o acto interruptivo), e uma reducao
    uniforme desloca os dois lados por igual. Foi preciso atacar exactamente o
    invariante que o check afirma - o que e, em si, a prova de que o check afirma
    alguma coisa. Nenhum caso dourado exercita esta combinacao; por isso e que o
    check de comportamento tem de existir a par deles.
    """
    orig = prescricao.analisar

    def patched(caso, *a, **k):
        out = orig(caso, *a, **k)
        if (caso.get("eventos") and out.get("data_termo")
                and out["mecanismo"] != "caducidade"):
            out["data_termo"] = min(e["data"] for e in caso["eventos"])
        return out
    prescricao.analisar = patched
    return lambda: setattr(prescricao, "analisar", orig)


MUTANTES = [
    ("sem-aviso-304", m_sem_aviso_304, "prescricao-decorrida-avisa-sempre-art-304"),
    ("caducidade-cita-prescricao", m_caducidade_cita_prescricao,
     "caducidade-nao-cita-regras-da-prescricao"),
    # A fronteira e monotona nos dois lados (ontem A_CORRER, hoje DECORRIDO), pelo
    # que o check de direccao do erro NAO a apanha - quem a apanha e o caso dourado
    # `spe-03`. Apontar o mutante ao check errado dava um sobrevivente enganador:
    # o defeito ESTA coberto, so nao por ali.
    ("fronteira-invertida", m_fronteira_invertida, "golden-estado"),
    ("interrupcao-encurta-o-prazo", m_interrupcao_encurta,
     "direccao-do-erro-verificada-no-comportamento"),
    ("requalificacao-evapora", m_requalificacao_evapora, "golden-data-termo"),
    ("sem-aviso-confissao", m_sem_aviso_confissao, "presuntiva-avisa-da-confissao"),
    ("caducidade-interrompivel", m_caducidade_interrompivel, "caducidade-imune-a-interrupcao"),
    ("declara-divida-extinta", m_declara_divida_extinta, "nunca-declara-divida-extinta"),
    ("facto-desconhecido-silencioso", m_facto_desconhecido_silencioso, "facto-desconhecido-rebenta"),
    ("regime-cita-artigo-inventado", m_regime_cita_artigo_inventado, "regimes-citam-artigos-capturados"),
]


def main():
    base = _correr_silencioso()
    vivos = [n for n, ok in base.items() if not ok]
    if vivos:
        print("ABORTADO: o gate ja esta vermelho: %s" % vivos)
        return 1

    # Um alvo que ja nao existe no sweep tornava o mutante num SOBREVIVENTE mudo:
    # `res.get(alvo)` devolvia None, `None is False` e falso, e a renomeacao de um
    # check desarmava silenciosamente o mutante que o protegia. Aconteceu de facto
    # em 2026-07-27 ao renomear `decorrido-avisa-sempre-art-304`. Um alvo
    # desconhecido passa a ser erro, nao sobrevivencia.
    fantasmas = [(n, alvo) for n, _, alvo in MUTANTES if alvo not in base]
    if fantasmas:
        for n, alvo in fantasmas:
            print("ERRO: o mutante '%s' aponta para '%s', que nao existe no sweep. "
                  "Foi renomeado? Este mutante nao estava a testar nada." % (n, alvo))
        return 1

    print("%-32s %-38s %s" % ("MUTANTE", "CHECK QUE O DEVE APANHAR", "RESULTADO"))
    print("-" * 88)
    sobreviventes = []
    for nome, aplicar, alvo in MUTANTES:
        restaurar = aplicar()
        try:
            res = _correr_silencioso()
        finally:
            restaurar()
        apanhado = res.get(alvo) is False
        print("%-32s %-38s %s" % (nome, alvo, "MORTO (bom)" if apanhado else "SOBREVIVEU"))
        if not apanhado:
            sobreviventes.append((nome, alvo))

    depois = _correr_silencioso()
    if any(not ok for ok in depois.values()):
        print("\nFALHA: os mutantes nao foram totalmente revertidos")
        return 1

    print()
    if sobreviventes:
        for nome, alvo in sobreviventes:
            print("SOBREVIVENTE: '%s' nao foi apanhado por '%s' - o check nao protege nada"
                  % (nome, alvo))
        return 1
    print("%d/%d mutantes mortos - todos os invariantes de produto estao mesmo a guardar"
          % (len(MUTANTES), len(MUTANTES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
