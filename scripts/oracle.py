#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Oraculo independente - segunda implementacao do calculo de prazos.

PORQUE EXISTE
    Um corpus de teste derivado do proprio motor nao prova nada: se o motor
    estiver errado, os casos dourados ficam errados da mesma maneira e a suite
    fica verde. Foi exactamente assim que o AoCentimo carregou nove taxas
    obsoletas com 29/29 checks verdes.

    Este ficheiro calcula o mesmo resultado por um CAMINHO DIFERENTE:

        prescricao.py   soma meses/anos ao calendario (dia correspondente,
                        encurtado ao ultimo dia do mes quando nao existe)

        oracle.py       resolve o termo por pesquisa binaria sobre uma funcao
                        de "meses completos decorridos" contada por comparacao
                        de tuplos (ano, mes, dia) - sem aritmetica de calendario

    Concordarem por acidente exige que ambos errem da mesma forma, o que a
    diferenca de metodo torna improvavel. Discordarem e sempre um defeito.

USO
    python scripts/oracle.py --crosscheck        confronta com prescricao.py
    python scripts/oracle.py --mutation-test     prova que o crosscheck sabe falhar
"""

import argparse
import datetime as _dt
import itertools
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)

import prescricao  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


# ------------------------------------------------------- caminho independente

def meses_completos(inicio, fim):
    """Quantos meses INTEIROS decorreram entre duas datas, sem aritmetica de datas.

    Compara apenas (ano, mes) e depois o dia. Deliberadamente nao usa timedelta
    nem soma de meses - e esse o ponto.
    """
    n = (fim.year - inicio.year) * 12 + (fim.month - inicio.month)
    if fim.day < inicio.day:
        # ...excepto quando o mes de chegada nao TEM o dia de partida: nesse caso
        # o ultimo dia do mes conta como o dia correspondente.
        ultimo = _ultimo_dia(fim.year, fim.month)
        if not (fim.day == ultimo and inicio.day > ultimo):
            n -= 1
    return n


def _ultimo_dia(ano, mes):
    if mes == 12:
        return 31
    return (_dt.date(ano + (mes // 12), mes % 12 + 1, 1) - _dt.timedelta(days=1)).day


def termo_por_pesquisa(inicio, n_meses):
    """Menor data d tal que meses_completos(inicio, d) >= n_meses. Pesquisa binaria."""
    lo, hi = inicio, inicio + _dt.timedelta(days=int(n_meses * 31.5) + 40)
    if meses_completos(inicio, hi) < n_meses:
        raise AssertionError("limite superior insuficiente")
    while lo < hi:
        mid = lo + _dt.timedelta(days=(hi - lo).days // 2)
        if meses_completos(inicio, mid) >= n_meses:
            hi = mid
        else:
            lo = mid + _dt.timedelta(days=1)
    return lo


def termo_oracle(inicio, cat):
    n = cat["meses"] if "meses" in cat else cat["anos"] * 12
    return termo_por_pesquisa(inicio, n)


# ------------------------------------------------------------- pontos cegos
#
# Registo explicito do que este oraculo NAO cobre. Um oraculo silencioso sobre
# os seus limites e pior do que nenhum, porque convida a confiar demais.

BLIND_SPOTS = [
    "Nao modela o art. 327.º n.º 1 (novo prazo suspenso ate transito em julgado): "
    "prescricao.py emite aviso, mas nenhum dos dois calcula a data real.",
    "Nao modela o art. 321.º (forca maior nos ultimos tres meses) - e porta de recusa.",
    "Nao modela o art. 320.º (menores/maiores acompanhados) - e porta de recusa, "
    "porque o efeito e extensao da CONCLUSAO e nao suspensao.",
    "Nao verifica se a categoria escolhida e a juridicamente correcta para os "
    "factos: qualificar mal a divida produz um prazo errado que os dois caminhos "
    "confirmam alegremente. Esta e a maior fonte de erro do produto e nenhum "
    "teste automatico a apanha.",
    "Nao ha ainda um corpus de decisoes judiciais reais contra o qual calibrar. "
    "Os casos dourados sao construidos a partir do texto legal, nao de sentencas.",
]


# ------------------------------------------------------------------ crosscheck

def _casos_sinteticos():
    """Grelha de datas duras: fins de mes, bissextos, 29/30/31."""
    dias = [1, 15, 28, 29, 30, 31]
    meses = [1, 2, 3, 4, 7, 8, 12]
    anos = [2023, 2024, 2025, 2026]  # 2024 bissexto
    for ano, mes, dia in itertools.product(anos, meses, dias):
        try:
            yield _dt.date(ano, mes, dia)
        except ValueError:
            continue


def crosscheck(regimes, verboso=False):
    falhas = []
    total = 0
    for nome, cat in sorted(regimes["categorias"].items()):
        for inicio in _casos_sinteticos():
            total += 1
            a = prescricao._add_meses(inicio, cat["meses"]) if "meses" in cat \
                else prescricao._add_anos(inicio, cat["anos"])
            b = termo_oracle(inicio, cat)
            if a != b:
                falhas.append((nome, inicio.isoformat(), a.isoformat(), b.isoformat()))
    print("crosscheck: %d combinacoes categoria x data" % total)
    if falhas:
        for f in falhas[:20]:
            print("  DIVERGENCIA %-38s inicio=%s  motor=%s  oraculo=%s" % f)
        if len(falhas) > 20:
            print("  ... e mais %d" % (len(falhas) - 20))
        return False
    print("crosscheck: OK - os dois caminhos concordam em todas as combinacoes")
    return True


def mutation_test(regimes):
    """Prova que o crosscheck SABE FALHAR.

    Um guarda que so foi visto a passar nao foi testado - foi observado. Aqui
    corrompe-se deliberadamente a aritmetica do motor e exige-se vermelho.
    """
    original = prescricao._add_meses
    try:
        prescricao._add_meses = lambda d, n: original(d, n) + _dt.timedelta(days=1)
        ok = crosscheck(regimes)
    finally:
        prescricao._add_meses = original
    if ok:
        print("MUTATION TEST FALHOU: o crosscheck ficou verde com a aritmetica "
              "corrompida. O guarda nao vale nada.")
        return False
    print("mutation test: OK - o crosscheck detectou a aritmetica corrompida")
    if not crosscheck(regimes):
        print("MUTATION TEST FALHOU: nao restaurou o estado original")
        return False
    print("mutation test: OK - estado original restaurado, crosscheck verde de novo")
    return True


def main(argv=None):
    p = argparse.ArgumentParser(description="Oraculo independente do porreceber")
    p.add_argument("--crosscheck", action="store_true")
    p.add_argument("--mutation-test", action="store_true")
    p.add_argument("--blind-spots", action="store_true")
    args = p.parse_args(argv)

    regimes = prescricao.carregar_regimes()

    if args.blind_spots:
        print("PONTOS CEGOS DECLARADOS (%d)" % len(BLIND_SPOTS))
        for b in BLIND_SPOTS:
            print("  - " + b)
        return 0
    if args.mutation_test:
        return 0 if mutation_test(regimes) else 1
    if args.crosscheck or True:
        return 0 if crosscheck(regimes) else 1


if __name__ == "__main__":
    sys.exit(main())
