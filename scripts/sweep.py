#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gate do porreceber. Falha fechado.

REGRA DA CASA: um check que nunca foi visto a ficar VERMELHO nao e um check,
e um enfeite. Corra `python scripts/oracle.py --mutation-test` e
`python scripts/sweep.py --self-test` para provar que estes sabem falhar.
"""

import argparse
import datetime as _dt
import io
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)

import prescricao  # noqa: E402
import oracle      # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

RESULTS = []


def check(nome, ok, detalhe=""):
    RESULTS.append((nome, bool(ok), detalhe))
    return bool(ok)


def _ler(*partes):
    with io.open(os.path.join(_ROOT, *partes), encoding="utf-8") as fh:
        return fh.read()


def correr():
    del RESULTS[:]
    regimes = prescricao.carregar_regimes()
    golden = json.loads(_ler("assets", "golden-cases.json"))
    leis = {"cc": _ler("assets", "law", "cc-300-333.md"),
            "l2396": _ler("assets", "law", "lei-23-96.md")}
    texto_lei = leis["cc"] + leis["l2396"]

    # ---- 1. o estatuto existe e esta completo ------------------------------
    arts_cc = set(re.findall(r"### Artigo (3[0-3][0-9])\.º", leis["cc"]))
    check("lei-cc-300-333-completa", len(arts_cc) == 34,
          "%d/34 artigos" % len(arts_cc))
    check("lei-23-96-artigos-1-e-10",
          "### Artigo 10.º" in leis["l2396"] and "### Artigo 1.º" in leis["l2396"])

    # Um artigo capturado tem de ter corpo. Uma captura vazia passaria o check
    # anterior alegremente.
    curtos = [a for a in sorted(arts_cc)
              if len(re.search(r"### Artigo %s\.º[^\n]*\n(.*?)(?=\n###|\n---|\Z)" % a,
                               leis["cc"], re.S).group(1).strip()) < 40]
    check("lei-cc-nenhum-artigo-vazio", not curtos, "vazios: %s" % curtos)

    # ---- 2. cada regime cita um artigo QUE EXISTE nas capturas -------------
    # Sem isto, um regime podia citar um artigo inventado e ninguem daria por ela.
    orfaos = []
    for nome, cat in regimes["categorias"].items():
        art = cat["artigo"]
        alvo = leis["l2396"] if "23/96" in cat["diploma"] else leis["cc"]
        if ("Artigo %s" % art) not in alvo:
            orfaos.append("%s -> %s (%s)" % (nome, art, cat["diploma"]))
    for nome, ev in regimes["eventos"].items():
        if ("Artigo %s" % ev["artigo"]) not in leis["cc"]:
            orfaos.append("evento %s -> %s" % (nome, ev["artigo"]))
    check("regimes-citam-artigos-capturados", not orfaos, "; ".join(orfaos))

    # ---- 3. as duas implementacoes concordam ------------------------------
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ok_cross = oracle.crosscheck(regimes)
    check("dual-path-concorda", ok_cross, buf.getvalue().strip().splitlines()[-1:])

    # ---- 4. casos dourados -------------------------------------------------
    falhas_estado, falhas_termo, falhas_mec = [], [], []
    falhas_avisos, falhas_recusas, falhas_conteudo = [], [], []
    for c in golden["cases"]:
        out = prescricao.analisar(c["caso"], regimes, hoje=c["hoje"])
        exp = c["esperado"]
        if out["estado"] != exp["estado"]:
            falhas_estado.append("%s: %s != %s" % (c["id"], out["estado"], exp["estado"]))
        if "data_termo" in exp and out.get("data_termo") != exp["data_termo"]:
            falhas_termo.append("%s: %s != %s" % (c["id"], out.get("data_termo"), exp["data_termo"]))
        if "mecanismo" in exp and out["mecanismo"] != exp["mecanismo"]:
            falhas_mec.append("%s: %s != %s" % (c["id"], out["mecanismo"], exp["mecanismo"]))

        # Conjunto EXACTO de avisos. Um aviso a mais reprova como um a menos:
        # senao o motor podia deixar de emitir um aviso critico e ficar verde.
        arts_avisados = sorted({w["artigo"].split(".")[0] for w in out["avisos"] if w["artigo"]})
        if arts_avisados != sorted(c["avisos_esperados"]):
            falhas_avisos.append("%s: %s != %s" % (c["id"], arts_avisados, sorted(c["avisos_esperados"])))

        recusas = sorted(r["chave"] for r in out["recusas"])
        if recusas != sorted(c["recusas_esperadas"]):
            falhas_recusas.append("%s: %s != %s" % (c["id"], recusas, sorted(c["recusas_esperadas"])))

        blob = json.dumps(out, ensure_ascii=False)
        em_falta = [a for a in c["deve_conter"] if a not in blob]
        if em_falta:
            falhas_conteudo.append("%s: falta citar %s" % (c["id"], em_falta))

    check("golden-estado", not falhas_estado, "; ".join(falhas_estado))
    check("golden-data-termo", not falhas_termo, "; ".join(falhas_termo))
    check("golden-mecanismo", not falhas_mec, "; ".join(falhas_mec))
    check("golden-avisos-conjunto-exacto", not falhas_avisos, "; ".join(falhas_avisos))
    check("golden-recusas-conjunto-exacto", not falhas_recusas, "; ".join(falhas_recusas))
    check("golden-cita-artigos-obrigatorios", not falhas_conteudo, "; ".join(falhas_conteudo))

    # ---- 5. invariantes de seguranca do produto ---------------------------
    # Estes nao sao sobre aritmetica. Sao sobre o que o utilizador le.

    # (a) O motor NUNCA pode dizer que uma divida esta extinta. Art. 303.o/304.o:
    #     o efeito e uma faculdade de recusa que tem de ser invocada.
    proibidas = re.compile(r"d[ií]vida\s+(est[aá]\s+)?extinta|j[aá]\s+n[aã]o\s+deve|"
                           r"n[aã]o\s+tem\s+de\s+pagar|est[aá]\s+livre\s+da\s+d[ií]vida",
                           re.I)
    maus = []
    for c in golden["cases"]:
        out = prescricao.analisar(c["caso"], regimes, hoje=c["hoje"])
        if proibidas.search(json.dumps(out, ensure_ascii=False)):
            maus.append(c["id"])
    check("nunca-declara-divida-extinta", not maus, "casos: %s" % maus)

    # (b) Sempre que uma PRESCRICAO aparece decorrida, o art. 304.o n.o 2 TEM de
    #     estar la. E a frase que impede alguem de pagar e perder o dinheiro para
    #     sempre. A caducidade esta fora: extingue o proprio direito, e citar-lhe
    #     o art. 304.o n.o 2 seria uma citacao errada (ver check seguinte).
    sem_aviso = []
    for c in golden["cases"]:
        out = prescricao.analisar(c["caso"], regimes, hoje=c["hoje"])
        if (out["estado"] == "PRAZO_DECORRIDO"
                and out["mecanismo"] != "caducidade"
                and "304" not in json.dumps(out, ensure_ascii=False)):
            sem_aviso.append(c["id"])
    check("prescricao-decorrida-avisa-sempre-art-304", not sem_aviso, "casos: %s" % sem_aviso)

    # (c) Presuntiva decorrida TEM de avisar da confissao (art. 314.o).
    sem_confissao = []
    for c in golden["cases"]:
        out = prescricao.analisar(c["caso"], regimes, hoje=c["hoje"])
        if (out["mecanismo"] == "prescricao_presuntiva"
                and out["estado"] == "PRAZO_DECORRIDO"
                and "armadilha_prescricao_presuntiva" not in out):
            sem_confissao.append(c["id"])
    check("presuntiva-avisa-da-confissao", not sem_confissao, "casos: %s" % sem_confissao)

    # (d) A caducidade NUNCA pode ser interrompida (art. 328.o).
    caso_cad = {"categoria": "servico_publico_essencial_diferenca",
                "data_inicio": "2025-11-01",
                "eventos": [{"tipo": "reconhecimento", "data": "2026-02-01"}]}
    sem_ev = {"categoria": "servico_publico_essencial_diferenca", "data_inicio": "2025-11-01"}
    a = prescricao.analisar(caso_cad, regimes, hoje="2026-07-27")
    b = prescricao.analisar(sem_ev, regimes, hoje="2026-07-27")
    check("caducidade-imune-a-interrupcao", a["data_termo"] == b["data_termo"],
          "com evento=%s sem evento=%s" % (a["data_termo"], b["data_termo"]))

    # (e) Toda a recusa cita um artigo, ou declara explicitamente que o assunto
    #     esta fora do corpo capturado. Uma recusa sem fundamento e arbitraria.
    sem_fund = [r[0] for r in prescricao.RECUSAS
                if r[3] is None and "fora do corpo" not in r[2] and "arts. 512" not in r[2]]
    check("recusas-tem-fundamento", not sem_fund, "sem artigo: %s" % sem_fund)

    # (f) Facto de recusa desconhecido tem de REBENTAR, nao ser ignorado em silencio.
    #     Um typo em "alta_tensao" nao pode transformar-se numa analise normal.
    try:
        prescricao.analisar({"categoria": "ordinario", "data_inicio": "2020-01-01",
                             "factos": {"alta_tenssao": True}}, regimes, hoje="2026-07-27")
        rebentou = False
    except ValueError:
        rebentou = True
    check("facto-desconhecido-rebenta", rebentou,
          "um typo num facto de recusa passaria despercebido")

    # (g) Categoria desconhecida idem.
    try:
        prescricao.analisar({"categoria": "inventada", "data_inicio": "2020-01-01"},
                            regimes, hoje="2026-07-27")
        rebentou2 = False
    except ValueError:
        rebentou2 = True
    check("categoria-desconhecida-rebenta", rebentou2)

    # ---- 6. honestidade do repositorio ------------------------------------
    check("pontos-cegos-declarados", len(oracle.BLIND_SPOTS) >= 5,
          "%d declarados" % len(oracle.BLIND_SPOTS))
    check("direccao-do-erro-documentada",
          regimes["direccao_do_erro"]["politica"] == "conservadora_para_o_devedor")

    # A verificacao acima so le uma string do JSON. Ficou verde durante as tres
    # violacoes reais da direccao do erro encontradas na revisao de 2026-07-27
    # (accao tempestiva sobre caducidade, requalificacao do art. 311.º perdida na
    # interrupcao seguinte, e a fronteira `>=`). Uma politica declarada e afirmada,
    # nao testada. A que se segue testa COMPORTAMENTO: em cada caso, adiantar o
    # relogio nunca pode transformar DECORRIDO em A_CORRER, e um acto do credor
    # dentro do prazo nunca pode aproximar o termo.
    violacoes = []
    for c in golden["cases"]:
        out = prescricao.analisar(c["caso"], regimes, hoje=c["hoje"])
        if out["estado"] == "RECUSA":
            continue
        # monotonia no tempo
        base = _dt.date.fromisoformat(c["hoje"])
        antes = prescricao.analisar(c["caso"], regimes,
                                    hoje=(base - _dt.timedelta(days=1)).isoformat())
        if antes["estado"] == "PRAZO_DECORRIDO" and out["estado"] == "PRAZO_A_CORRER":
            violacoes.append("%s: decorrido ontem, a correr hoje" % c["id"])
        # um acto interruptivo do credor dentro do prazo nunca encurta o termo
        if out["mecanismo"] != "caducidade":
            t = _dt.date.fromisoformat(out["data_termo"])
            ini = _dt.date.fromisoformat(out["data_inicio_efectiva"])
            meio = ini + (t - ini) // 2
            comb = dict(c["caso"])
            comb["eventos"] = list(comb.get("eventos") or []) + [
                {"tipo": "reconhecimento", "data": meio.isoformat()}]
            alt = prescricao.analisar(comb, regimes, hoje=c["hoje"])
            if alt.get("data_termo") and alt["data_termo"] < out["data_termo"]:
                violacoes.append("%s: reconhecimento a meio ANTECIPOU o termo (%s < %s)"
                                 % (c["id"], alt["data_termo"], out["data_termo"]))
    check("direccao-do-erro-verificada-no-comportamento", not violacoes,
          "; ".join(violacoes))

    # O art. 328.º nao e o unico artigo da caducidade. Se a saida de um caso de
    # caducidade cita o art. 303.º ou o art. 304.º n.º 2 - que sao regras da
    # PRESCRICAO - a citacao esta errada, ainda que o prazo esteja certo.
    ma_citacao = []
    for c in golden["cases"]:
        out = prescricao.analisar(c["caso"], regimes, hoje=c["hoje"])
        if out["mecanismo"] != "caducidade" or out["estado"] != "PRAZO_DECORRIDO":
            continue
        txt = out["o_que_isto_significa"] + out.get("antes_de_pagar_seja_o_que_for", "")
        if "303" in txt.replace("art. 303.º e tem de ser", "") or "304" in txt:
            ma_citacao.append(c["id"])
    check("caducidade-nao-cita-regras-da-prescricao", not ma_citacao,
          "casos: %s" % ma_citacao)

    skill = _ler("SKILL.md")
    for termo, rotulo in (("303", "art-303"), ("304", "art-304"), ("312", "art-312"),
                          ("328", "art-328")):
        check("skill-explica-%s" % rotulo, termo in skill)
    # A versao anterior ancorava a fim de linha (`\s*$`) e portanto deixava passar
    # "Prestamos aconselhamento juridico gratuito." Uma promessa dessas no meio de
    # uma frase e exactamente a forma como ela apareceria.
    # A negacao e o uso NORMAL destas frases neste repositorio ("nao substitui
    # advogado", "isto nao e aconselhamento juridico"). Sem o lookbehind negativo a
    # verificacao acendia-se com o proprio aviso legal - um guarda que reprova o
    # comportamento correcto acaba desligado, e ai deixa de guardar o que interessa.
    NEG = r"(?<!n[aã]o )(?<!n[aã]o o )(?<!n[aã]o a )"
    promessa = re.compile(
        r"(presta\w*|oferec\w*|damos|fornec\w*|garant\w*)[^.\n]{0,40}"
        r"aconselhamento (jur[ií]dico|legal)|"
        + NEG + r"substitui[^.\n]{0,20}(advogad|solicitador)|"
        r"(este|esta)[^.\n]{0,30}\b[eé] aconselhamento jur[ií]dico",
        re.I)
    achados = []
    for f in ("SKILL.md", "README.md", "README.pt.md", "AVISO-FORMAL.md", "DISCLAIMER.md"):
        for m in promessa.finditer(_ler(f)):
            achados.append("%s: %r" % (f, m.group(0)[:70]))
    check("nenhum-documento-promete-aconselhamento", not achados, "; ".join(achados))

    # O numero de checks anunciado no SKILL.md tem de bater certo com a realidade.
    # E o check que apanha a documentacao a envelhecer - o defeito que passou
    # despercebido no AoCentimo durante uma sessao inteira.
    m = re.search(r"(\d+)\s+verifica", skill)
    check("skill-conta-os-checks-corretamente", m and int(m.group(1)) == len(RESULTS) + 1,
          "SKILL.md diz %s, o sweep tem %d" % (m.group(1) if m else "?", len(RESULTS) + 1))

    return RESULTS


def _imprimir(res, verboso):
    falhou = 0
    for nome, ok, det in res:
        if ok and not verboso:
            continue
        marca = "PASS" if ok else "FAIL"
        print("%-4s %s" % (marca, nome))
        if not ok and det:
            print("       %s" % (det if isinstance(det, str) else " ".join(map(str, det)))[:400])
        if not ok:
            falhou += 1
    if not verboso:
        falhou = sum(1 for _, ok, _ in res if not ok)
    print()
    print("%d/%d verificacoes passaram" % (len(res) - falhou, len(res)))
    return falhou


def self_test():
    """Prova que o gate sabe ficar VERMELHO. Corrompe, exige falha, restaura."""
    print("--- estado normal ---")
    base = correr()
    n_falhas = sum(1 for _, ok, _ in base if not ok)
    if n_falhas:
        print("SELF-TEST ABORTADO: o gate ja esta vermelho (%d falhas)" % n_falhas)
        return 1
    print("%d/%d verde" % (len(base), len(base)))

    print("--- com a aritmetica corrompida ---")
    orig = prescricao._add_meses
    prescricao._add_meses = lambda d, n: orig(d, n)
    prescricao._add_anos = lambda d, n: orig(d, n * 12 + 1)
    try:
        mut = correr()
        falhas = [n for n, ok, _ in mut if not ok]
    finally:
        prescricao._add_meses = orig
        prescricao._add_anos = lambda d, n: orig(d, n * 12)
    if not falhas:
        print("SELF-TEST FALHOU: o gate ficou verde com a aritmetica corrompida")
        return 1
    print("o gate detectou: %s" % ", ".join(falhas[:6]))

    print("--- restaurado ---")
    fim = correr()
    if any(not ok for _, ok, _ in fim):
        print("SELF-TEST FALHOU: nao restaurou")
        return 1
    print("%d/%d verde de novo" % (len(fim), len(fim)))
    print()
    print("SELF-TEST OK - o gate sabe falhar e sabe voltar a passar")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="Gate do porreceber")
    p.add_argument("-v", "--verboso", action="store_true")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return self_test()
    res = correr()
    return 1 if _imprimir(res, args.verboso) else 0


if __name__ == "__main__":
    sys.exit(main())
