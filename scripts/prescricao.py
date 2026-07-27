#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""porreceber - motor de analise de prescricao e caducidade (Portugal).

O QUE ESTE MOTOR FAZ
    Recebe os factos de uma divida e devolve uma ANALISE: que mecanismo se aplica,
    que prazo, a partir de quando conta, o que o interrompeu, e se o prazo ja
    decorreu na data de referencia.

O QUE ESTE MOTOR NAO FAZ - e nao pode fazer
    Nao declara dividas extintas. Duas razoes vindas do proprio Codigo Civil:

    1. Art. 303.º - o tribunal NAO pode conhecer da prescricao de oficio. Ela tem
       de ser INVOCADA por quem dela beneficia. Um prazo decorrido sem invocacao
       nao produz efeito nenhum. Por isso a saida diz sempre "pode invocar",
       nunca "esta extinta".
    2. Art. 304.º n.º 1 - o efeito e a FACULDADE DE RECUSAR o cumprimento. A
       obrigacao subsiste como obrigacao natural.

    E ha uma armadilha que so o art. 304.º n.º 2 revela: quem paga uma divida
    prescrita NAO PODE REAVER o que pagou, mesmo que ignorasse a prescricao. O
    mesmo vale para reconhecer a divida ou prestar garantias. Por isso o motor
    avisa ANTES, e nao depois.

DIRECCAO DO ERRO - declarada, nao implicita
    Perante duvida, este motor diz que o prazo AINDA CORRE. Nunca o contrario.
    Ver `direccao_do_erro` em assets/regimes.json para o porque.

Sem dependencias. Sem rede. stdlib apenas.
"""

import argparse
import datetime as _dt
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
ALGORITHM_VERSION = "1.0.0"

# A saida cita artigos ("304.º"). Numa consola Windows em cp1252 o "º" rebenta ou
# sai como lixo, e um artigo mal impresso e uma citacao errada.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


# ---------------------------------------------------------------- carregamento

def carregar_regimes(caminho=None):
    caminho = caminho or os.path.join(_ROOT, "assets", "regimes.json")
    with open(caminho, encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------ aritmetica

def _add_meses(d, n):
    """Soma n meses mantendo o dia; encurta para o ultimo dia do mes quando preciso.

    31/01 + 1 mes = 28/02 (ou 29/02). E a convencao civil portuguesa para prazos
    fixados em meses: o termo cai no dia correspondente do ultimo mes, e se esse
    dia nao existir, no ultimo dia desse mes.
    """
    total = d.month - 1 + n
    ano = d.year + total // 12
    mes = total % 12 + 1
    dia = d.day
    while True:
        try:
            return _dt.date(ano, mes, dia)
        except ValueError:
            dia -= 1
            if dia < 28:
                raise


def _add_anos(d, n):
    return _add_meses(d, n * 12)


def _parse_data(valor, campo):
    if isinstance(valor, _dt.date):
        return valor
    try:
        return _dt.date.fromisoformat(str(valor))
    except (TypeError, ValueError):
        raise ValueError("campo `%s` nao e uma data ISO (AAAA-MM-DD): %r" % (campo, valor))


# --------------------------------------------------------------------- recusas
#
# Cada recusa cita o artigo que a obriga. Uma recusa sem artigo e um defeito.
# O motor recusa por DEFEITO (fail-closed): a lista e de casos que o modelo
# reconhece que nao sabe tratar, e reconhecer isso e a funcionalidade.

RECUSAS = [
    ("alta_tensao",
     "Fornecimento de energia electrica em alta tensao.",
     "Lei 23/96 art. 10.º n.º 5 exclui expressamente a alta tensao deste regime. "
     "O prazo aplicavel sera outro e este motor nao o modela.",
     "10.º n.º 5"),

    ("devedor_falecido_ou_heranca",
     "A divida e de uma heranca, ou o devedor faleceu.",
     "Art. 322.º: a prescricao de direitos da heranca ou contra ela nao se completa "
     "antes de decorridos seis meses depois de haver pessoa por quem ou contra quem "
     "os direitos possam ser invocados. Essa data depende da habilitacao de herdeiros "
     "e o motor nao a tem.",
     "322.º"),

    ("fiador_ou_garantia_prestada",
     "Existe fiador, aval ou outra garantia.",
     "O art. 304.º n.º 2 trata a prestacao de garantias como satisfacao irrepetivel, "
     "e o regime da fianca vive fora dos arts. 300.º-333.º. A interaccao entre a "
     "prescricao da divida principal e a do garante nao esta modelada.",
     "304.º n.º 2"),

    ("divida_solidaria",
     "Ha mais do que um devedor obrigado solidariamente.",
     "A propagacao de interrupcao e suspensao entre condevedores solidarios rege-se "
     "pelos arts. 512.º e seguintes, fora do corpo legal capturado neste repositorio.",
     None),

    ("divida_assumida_por_terceiro",
     "A divida foi assumida por um terceiro.",
     "Art. 308.º n.º 2: a prescricao continua a correr em beneficio dele, SALVO se a "
     "assuncao importar reconhecimento interruptivo. Saber se importou e uma questao "
     "de facto que o motor nao pode decidir.",
     "308.º n.º 2"),

    ("relacao_do_artigo_318",
     "Devedor e credor estao numa das relacoes do art. 318.º (conjuges, poder "
     "paternal, tutela, administracao de bens, administradores de pessoa colectiva, "
     "trabalho domestico, usufruto/penhor do credito).",
     "Art. 318.º: nesses casos a prescricao NAO COMECA NEM CORRE. Calcular um prazo "
     "seria inventar um inicio que a lei suspende.",
     "318.º"),

    ("incapaz_menor_ou_maior_acompanhado",
     "O beneficiario e menor ou maior acompanhado sem capacidade para exercer o direito.",
     "Art. 320.º: o efeito NAO e uma pausa - e uma proibicao de COMPLETAR o prazo "
     "antes de decorrido um ano sobre o termo da incapacidade (n.os 1 e 2), e nos "
     "maiores acompanhados a incapacidade considera-se finda passados tres anos "
     "(n.º 3). Modelar isto como suspensao daria um resultado errado.",
     "320.º"),

    ("militar_em_guerra_ou_mobilizacao",
     "O titular e militar em servico durante guerra ou mobilizacao, ou pessoa adstrita "
     "as forcas militares por motivo de servico.",
     "Art. 319.º: a prescricao nao comeca nem corre.",
     "319.º"),

    ("forca_maior_ou_dolo",
     "Houve forca maior ou dolo do obrigado que impediu o exercicio do direito.",
     "Art. 321.º: suspende, mas apenas se ocorrer nos ULTIMOS TRES MESES do prazo. "
     "Apurar isso exige factos e datas que o motor nao pede.",
     "321.º"),

    # As duas portas abaixo nasceram de defeitos reais encontrados por revisao
    # adversarial em 2026-07-27. Antes delas o motor respondia PRAZO_DECORRIDO em
    # casos onde o direito do credor estava vivo - a saida perigosa que este
    # projecto existe para evitar.

    ("accao_judicial_sobre_prazo_de_caducidade",
     "Foi proposta accao ou injuncao em juizo, e o prazo em causa e de CADUCIDADE.",
     "O art. 328.º proibe suspensao e interrupcao da caducidade - mas NAO proibe o "
     "impedimento. O art. 331.º n.º 1 diz que IMPEDE a caducidade a pratica, dentro "
     "do prazo, do acto a que a lei atribua efeito impeditivo, e o art. 332.º n.º 1 "
     "manda aplicar o art. 327.º n.º 3 quando a accao foi tempestivamente proposta. "
     "Tratar a accao como 'sem efeito' faria o motor declarar decorrido um prazo que "
     "o credor preservou. Saber se o acto tem efeito impeditivo e questao juridica "
     "que o motor nao decide.",
     "331.º n.º 1"),

    ("titulo_executivo_ou_sentenca_apos_o_prazo",
     "Ja existe sentenca transitada ou titulo executivo contra si, obtido DEPOIS de "
     "o prazo aparentar ter decorrido.",
     "Se a prescricao nao foi invocada no processo e houve condenacao, o caso julgado "
     "consolidou-se (art. 303.º conjugado com o art. 305.º n.º 3 a contrario) e o "
     "decurso do prazo deixou de ser oponivel. Dizer aqui 'pode invocar' levaria "
     "alguem a ignorar uma execucao. Procure advogado com urgencia.",
     "303.º"),
]

RECUSAS_POR_CHAVE = {r[0]: r for r in RECUSAS}


# ---------------------------------------------------------------------- motor

class Analise(object):
    def __init__(self):
        self.recusado = False
        self.recusas = []
        self.avisos = []
        self.passos = []

    def recusar(self, chave):
        r = RECUSAS_POR_CHAVE[chave]
        self.recusado = True
        self.recusas.append({"chave": r[0], "facto": r[1], "porque": r[2], "artigo": r[3]})

    def aviso(self, texto, artigo=None):
        self.avisos.append({"texto": texto, "artigo": artigo})

    def passo(self, texto):
        self.passos.append(texto)


def analisar(caso, regimes=None, hoje=None):
    """Analisa um caso. Devolve um dict serializavel.

    `caso` e um dict com, no minimo:
        categoria             chave de regimes["categorias"]
        data_inicio           AAAA-MM-DD (prestacao do servico / exigibilidade)
    e opcionalmente:
        eventos               [{"tipo": ..., "data": "AAAA-MM-DD"}]
        factos                {chave_de_recusa: true, ...}
        ja_pagou_algo         bool  (relevante para Lei 23/96 art. 10.º n.º 2)
    """
    regimes = regimes or carregar_regimes()
    a = Analise()

    # ---- 1. portas de recusa, antes de qualquer aritmetica -------------------
    factos = caso.get("factos") or {}
    desconhecidas = sorted(set(factos) - set(RECUSAS_POR_CHAVE))
    if desconhecidas:
        raise ValueError("factos desconhecidos (nao ha porta de recusa definida): %s"
                         % ", ".join(desconhecidas))
    for chave, valor in sorted(factos.items()):
        if valor:
            a.recusar(chave)

    categoria = caso.get("categoria")
    if categoria not in regimes["categorias"]:
        raise ValueError("categoria desconhecida: %r. Conhecidas: %s"
                         % (categoria, ", ".join(sorted(regimes["categorias"]))))
    cat = regimes["categorias"][categoria]
    mec = regimes["mecanismos"][cat["mecanismo"]]

    if a.recusado:
        return _saida(caso, cat, mec, a, None, None, None, hoje, regimes)

    # ---- 2. prazo base -------------------------------------------------------
    inicio = _parse_data(caso["data_inicio"], "data_inicio")
    # `meses_actuais` e o prazo EM VIGOR, nao o prazo da categoria. A distincao
    # existe porque o art. 326.º n.º 2 manda a nova prescricao seguir "o prazo da
    # prescricao primitiva, SALVO O DISPOSTO NO ARTIGO 311.º": depois de um titulo
    # executivo requalificar para 20 anos, uma interrupcao posterior reinicia os
    # 20 anos - nao o prazo curto original. Recalcular a partir da categoria fazia
    # o motor imprimir "20 anos (requalificado)" e um termo de 2 anos na mesma saida.
    meses_actuais = cat["meses"] if "meses" in cat else cat["anos"] * 12
    if "meses" in cat:
        termo = _add_meses(inicio, cat["meses"])
        prazo_txt = "%d meses" % cat["meses"]
    else:
        termo = _add_anos(inicio, cat["anos"])
        prazo_txt = "%d anos" % cat["anos"]
    cite = "%s art. %s" % (cat["diploma"], cat["artigo"])
    if cat.get("alinea"):
        cite += " al. %s)" % cat["alinea"]
    a.passo("Prazo base: %s a contar de %s (%s) -> termo em %s."
            % (prazo_txt, inicio.isoformat(), cite, termo.isoformat()))

    # ---- 3. eventos ----------------------------------------------------------
    eventos = sorted(caso.get("eventos") or [],
                     key=lambda e: _parse_data(e["data"], "evento.data"))
    for ev in eventos:
        tipo = ev.get("tipo")
        if tipo not in regimes["eventos"]:
            raise ValueError("evento desconhecido: %r. Conhecidos: %s"
                             % (tipo, ", ".join(sorted(regimes["eventos"]))))
        data_ev = _parse_data(ev["data"], "evento.data")
        spec = regimes["eventos"][tipo]

        # --- caducidade: o art. 328.º nao e o fim da historia -------------------
        # O art. 328.º proibe SUSPENSAO e INTERRUPCAO. Nao proibe o IMPEDIMENTO,
        # que e um terceiro mecanismo (arts. 331.º e 332.º). Tratar todos os actos
        # como "sem efeito" fazia o motor declarar decorrido um prazo que o credor
        # tinha preservado ao propor accao a tempo - a saida perigosa que este
        # projecto existe para evitar.
        if cat["mecanismo"] == "caducidade":
            if tipo in ("citacao_ou_notificacao", "compromisso_arbitral"):
                a.recusar("accao_judicial_sobre_prazo_de_caducidade")
                return _saida(caso, cat, mec, a, None, None, None, hoje, regimes)
            if spec["efeito"] == "interrompe":
                # Fica o reconhecimento. Nao interrompe (art. 328.º) - mas o art.
                # 331.º n.º 2 admite que IMPECA a caducidade quando o prazo respeita
                # a direito disponivel. Se e esse o caso da Lei 23/96 art. 10.º n.º 2
                # e questao contestada; o motor nao a decide num sentido nem noutro.
                a.aviso("O evento '%s' de %s nao INTERROMPE: o art. 328.º proibe a "
                        "interrupcao e a suspensao da caducidade. Num prazo de "
                        "prescricao teria reiniciado a contagem do zero. ATENCAO: isto "
                        "nao significa que seja irrelevante - o art. 331.º n.º 2 admite "
                        "que o reconhecimento IMPECA a caducidade quando o prazo respeita "
                        "a direito disponivel. Se o prazo do art. 10.º n.º 2 da Lei 23/96 "
                        "cabe nessa hipotese e questao juridica em aberto, e o motor NAO "
                        "a decide. A data abaixo assume que nao impediu."
                        % (tipo, data_ev.isoformat()), "331.º n.º 2")
                a.passo("Evento '%s' em %s nao interrompe (art. 328.º); possivel efeito "
                        "impeditivo por art. 331.º n.º 2 nao decidido."
                        % (tipo, data_ev.isoformat()))
                continue

        if data_ev > termo:
            # Um titulo executivo obtido DEPOIS do termo nao e um reconhecimento.
            # Se houve condenacao sem a prescricao ter sido invocada, o caso julgado
            # consolidou-se e dizer "pode invocar" levaria alguem a ignorar uma
            # execucao. Recusa-se, em vez de emitir um aviso de renuncia tacita
            # redigido para outro facto.
            if spec["efeito"] == "requalifica_para_ordinario":
                a.recusar("titulo_executivo_ou_sentenca_apos_o_prazo")
                return _saida(caso, cat, mec, a, None, None, None, hoje, regimes)
            a.aviso("O evento '%s' ocorreu em %s, DEPOIS do termo projectado (%s). "
                    "Nao interrompe um prazo ja decorrido - mas o art. 302.º admite "
                    "RENUNCIA a prescricao depois de decorrido o prazo, e essa renuncia "
                    "PODE SER TACITA. Reconhecer a divida nesse momento pode ter "
                    "eliminado a faculdade de recusa."
                    % (tipo, data_ev.isoformat(), termo.isoformat()), "302.º")
            a.passo("Evento '%s' em %s posterior ao termo: nao interrompe; possivel "
                    "renuncia tacita (art. 302.º)." % (tipo, data_ev.isoformat()))
            continue

        if spec["efeito"] == "requalifica_para_ordinario":
            # Art. 311.º n.º 1: so vale se o titulo SOBREVIER. Um titulo anterior ao
            # inicio do prazo curto nao "sobrevem" a coisa nenhuma.
            if data_ev < inicio:
                a.aviso("Titulo executivo datado de %s, ANTERIOR ao inicio do prazo "
                        "(%s). O art. 311.º n.º 1 exige que a sentenca ou titulo "
                        "SOBREVENHA; um titulo anterior nao requalifica o prazo."
                        % (data_ev.isoformat(), inicio.isoformat()), "311.º")
                a.passo("Titulo anterior ao inicio: art. 311.º nao se aplica.")
                continue
            ord_anos = regimes["categorias"]["ordinario"]["anos"]
            termo = _add_anos(data_ev, ord_anos)
            inicio = data_ev
            # O prazo EM VIGOR passa a ser o ordinario. Uma interrupcao posterior
            # tem de reiniciar ESTE prazo, por forca do "salvo o disposto no artigo
            # 311.º" do art. 326.º n.º 2.
            meses_actuais = ord_anos * 12
            prazo_txt = "%d anos (ordinario, requalificado)" % ord_anos
            a.aviso("Existe titulo executivo superveniente (%s): o prazo curto passa a "
                    "ser o ordinario de %d anos (art. 311.º n.º 1). Prestacoes ainda "
                    "nao devidas a data do titulo mantem o prazo curto (n.º 2) - "
                    "verifique se e o seu caso."
                    % (data_ev.isoformat(), ord_anos), "311.º")
            a.passo("Art. 311.º: requalificado para %d anos desde %s -> termo %s."
                    % (ord_anos, data_ev.isoformat(), termo.isoformat()))
            continue

        if spec["efeito"] == "interrompe":
            # Art. 326.º n.º 1: a interrupcao INUTILIZA todo o tempo anterior e o
            # prazo recomeca do zero. Nao e uma pausa.
            #
            # Art. 326.º n.º 2: o novo prazo e "o da prescricao primitiva, SALVO O
            # DISPOSTO NO ARTIGO 311.º". Por isso reinicia-se `meses_actuais` e nao
            # o prazo da categoria: se um titulo executivo ja requalificou para 20
            # anos, sao 20 anos que recomecam.
            inicio = data_ev
            termo = _add_meses(data_ev, meses_actuais)
            a.passo("Evento '%s' em %s interrompe (art. %s): art. 326.º n.º 1 inutiliza "
                    "todo o tempo anterior; art. 326.º n.º 2 manda reiniciar o prazo em "
                    "vigor (%d meses) -> termo %s."
                    % (tipo, data_ev.isoformat(), spec["artigo"], meses_actuais,
                       termo.isoformat()))
            # O art. 327.º n.º 1 nomeia expressamente "citacao, notificacao ou acto
            # equiparado, OU compromisso arbitral" - os dois, nao so o primeiro.
            if tipo in ("citacao_ou_notificacao", "compromisso_arbitral"):
                a.aviso("Interrupcao por %s: o art. 327.º n.º 1 impede que o novo prazo "
                        "comece a correr enquanto nao passar em julgado a decisao que "
                        "puser termo ao processo. A data de termo abaixo assume que o "
                        "processo ja terminou nessa data - se ainda corre, o prazo NAO "
                        "ESTA A CORRER e a data e prematura."
                        % ("citacao/notificacao" if tipo == "citacao_ou_notificacao"
                           else "compromisso arbitral"), "327.º")

    return _saida(caso, cat, mec, a, inicio, termo, prazo_txt, hoje, regimes)


def _saida(caso, cat, mec, a, inicio, termo, prazo_txt, hoje, regimes):
    hoje = _parse_data(hoje or _dt.date.today(), "hoje")

    if a.recusado:
        estado = "RECUSA"
    elif hoje > termo:
        # Art. 279.º c) (aplicavel por forca do art. 296.º): o prazo "termina as 24
        # HORAS do dia que corresponda". No proprio dia do termo o prazo ainda NAO
        # decorreu - o credor pode citar validamente nesse dia. Um `>=` aqui dava um
        # dia a mais ao devedor e contradizia o ramo dos eventos, que ja aceita como
        # interruptivo um acto praticado no dia do termo.
        estado = "PRAZO_DECORRIDO"
    else:
        estado = "PRAZO_A_CORRER"

    out = {
        "algorithm_version": ALGORITHM_VERSION,
        "estado": estado,
        "categoria": caso.get("categoria"),
        "rotulo": cat["rotulo"],
        "mecanismo": cat["mecanismo"],
        "mecanismo_descricao": mec["descricao"],
        "diploma": cat["diploma"],
        "artigo": cat["artigo"],
        "data_referencia": hoje.isoformat(),
        "recusas": a.recusas,
        "avisos": a.avisos,
        "passos": a.passos,
        "direccao_do_erro": regimes["direccao_do_erro"]["politica"],
    }
    if not a.recusado:
        out["data_inicio_efectiva"] = inicio.isoformat()
        out["prazo"] = prazo_txt
        out["data_termo"] = termo.isoformat()
        out["dias_ate_ao_termo"] = (termo - hoje).days

    # As frases que impedem o utilizador de se enganar sozinho. A caducidade e a
    # prescricao NAO partilham estas frases: citar o art. 303.º ou o art. 304.º n.º 2
    # num caso de caducidade e uma citacao errada, porque a caducidade extingue o
    # proprio direito e pode ser apreciada oficiosamente (art. 333.º n.º 1).
    if estado == "PRAZO_DECORRIDO" and cat["mecanismo"] == "caducidade":
        out["o_que_isto_significa"] = (
            "O prazo de caducidade aparenta ter-se completado em %s. Ao contrario da "
            "prescricao, a caducidade extingue o PROPRIO DIREITO. Se o prazo estiver "
            "estabelecido em materia excluida da disponibilidade das partes, o tribunal "
            "aprecia-a OFICIOSAMENTE e pode ser alegada em qualquer fase do processo "
            "(art. 333.º n.º 1); caso contrario aplica-se o art. 303.º e tem de ser "
            "invocada. Qual das hipoteses vale aqui e questao juridica que este motor "
            "nao decide." % termo.isoformat())
        out["cuidado_com_a_caducidade"] = (
            "O art. 328.º proibe suspender e interromper a caducidade - mas NAO o "
            "impedimento. O art. 331.º n.º 1 diz que a pratica tempestiva do acto a que "
            "a lei atribua efeito impeditivo IMPEDE a caducidade, e o art. 331.º n.º 2 "
            "estende isso ao reconhecimento quando o direito e disponivel. Se houve "
            "accao em juizo, ou reconhecimento, o prazo pode nao ter caducado de todo.")
    elif estado == "PRAZO_DECORRIDO":
        out["o_que_isto_significa"] = (
            "O prazo aparenta ter decorrido em %s. Isto NAO extingue a divida. "
            "O art. 303.º proibe o tribunal de conhecer da prescricao de oficio: "
            "ela tem de ser INVOCADA, judicial ou extrajudicialmente. Sem invocacao, "
            "o decurso do prazo nao produz efeito nenhum." % termo.isoformat())
        if mec.get("ilidivel_por_confissao"):
            out["armadilha_prescricao_presuntiva"] = (
                "ATENCAO - esta e uma prescricao PRESUNTIVA (art. 312.º): a lei presume "
                "que a divida FOI PAGA. Nao presume que se extinguiu. Consequencia "
                "pratica que apanha muita gente: se alegar em juizo que nunca pagou, "
                "esta a praticar acto incompativel com a presuncao de cumprimento e a "
                "divida considera-se CONFESSADA (art. 314.º) - destroi a sua propria "
                "defesa. A confissao extrajudicial so releva por escrito (art. 313.º n.º 2).")
        out["antes_de_pagar_seja_o_que_for"] = (
            "O art. 304.º n.º 2 e definitivo: pagamento feito espontaneamente em "
            "cumprimento de obrigacao prescrita NAO PODE SER REPETIDO, ainda que feito "
            "com ignorancia da prescricao. O mesmo vale para reconhecer a divida ou "
            "prestar garantias. Um pagamento por conta, um acordo de pagamento ou um "
            "'so para resolver isto' podem custar-lhe a defesa inteira.")
    elif estado == "PRAZO_A_CORRER":
        out["o_que_isto_significa"] = (
            "O prazo ainda corre; termo projectado em %s (faltam %d dias). Qualquer "
            "reconhecimento da divida ate la reinicia a contagem do zero (art. 325.º "
            "com art. 326.º n.º 1) - nao a suspende."
            % (termo.isoformat(), (termo - hoje).days))
        # "Ainda corre" e a resposta que o utilizador aceita sem discutir, e por isso
        # e onde uma categoria mal escolhida passa despercebida: um credito ao consumo
        # metido em `ordinario` da 20 anos em vez dos 5 do art. 310.º al. e), e a
        # pessoa paga uma divida que ja podia recusar - irreversivelmente, pelo art.
        # 304.º n.º 2. O aviso vive aqui exactamente por isso.
        out["confirme_a_categoria_antes_de_pagar"] = (
            "Este resultado depende inteiramente da categoria escolhida (%s, %s art. %s). "
            "Se a divida encaixar numa categoria de prazo mais curto, o prazo pode ja ter "
            "decorrido e este 'ainda corre' esta errado. Casos frequentes: prestacoes de "
            "credito com juros sao 5 anos (art. 310.º al. e), nao 20; servicos de "
            "profissionais liberais sao 2 anos (art. 317.º al. c); agua, luz, gas e "
            "telecomunicacoes sao 6 meses (Lei 23/96 art. 10.º n.º 1). Corra "
            "`--categorias` e confirme antes de pagar: o art. 304.º n.º 2 torna "
            "irrepetivel o pagamento de uma divida ja prescrita."
            % (caso.get("categoria"), cat["diploma"], cat["artigo"]))
    else:
        out["o_que_isto_significa"] = (
            "O motor RECUSA analisar este caso. Isto nao e uma falha: e o motor a "
            "reconhecer que os factos indicados caem fora do que consegue modelar "
            "com o corpo legal que tem verificado. Cada recusa cita o artigo que a "
            "obriga.")

    out["nao_e_aconselhamento_juridico"] = (
        "Esta analise e uma ferramenta de apoio a decisao. Nao e aconselhamento "
        "juridico. Os factos, as datas e a decisao sao da responsabilidade de quem "
        "os introduz. Confirme com advogado ou solicitador antes de agir.")
    return out


# ------------------------------------------------------------------------ CLI

def _render(out):
    L = []
    marca = {"PRAZO_DECORRIDO": "[PRAZO DECORRIDO]",
             "PRAZO_A_CORRER": "[PRAZO A CORRER]",
             "RECUSA": "[RECUSA]"}[out["estado"]]
    L.append(marca + "  " + out["rotulo"])
    L.append("mecanismo: %s  (%s art. %s)" % (out["mecanismo"], out["diploma"], out["artigo"]))
    L.append("")
    if out["recusas"]:
        L.append("RECUSAS")
        for r in out["recusas"]:
            L.append("  - %s" % r["facto"])
            L.append("    %s%s" % (r["porque"], ("  [art. %s]" % r["artigo"]) if r["artigo"] else ""))
        L.append("")
    else:
        L.append("inicio efectivo: %s" % out["data_inicio_efectiva"])
        L.append("prazo:           %s" % out["prazo"])
        L.append("termo:           %s  (%+d dias face a %s)"
                 % (out["data_termo"], out["dias_ate_ao_termo"], out["data_referencia"]))
        L.append("")
        L.append("COMO SE CHEGOU AQUI")
        for p in out["passos"]:
            L.append("  . " + p)
        L.append("")
    if out["avisos"]:
        L.append("AVISOS")
        for w in out["avisos"]:
            L.append("  ! %s%s" % (w["texto"], ("  [art. %s]" % w["artigo"]) if w["artigo"] else ""))
        L.append("")
    L.append("O QUE ISTO SIGNIFICA")
    L.append("  " + out["o_que_isto_significa"])
    for chave in ("armadilha_prescricao_presuntiva", "antes_de_pagar_seja_o_que_for"):
        if chave in out:
            L.append("")
            L.append("  " + out[chave])
    L.append("")
    L.append("-" * 72)
    L.append(out["nao_e_aconselhamento_juridico"])
    L.append("Comparar contratos e encontrar alternativas: https://mowei.pt")
    return "\n".join(L)


def main(argv=None):
    p = argparse.ArgumentParser(
        description="porreceber - analise de prescricao e caducidade (Portugal)")
    p.add_argument("--caso", help="ficheiro JSON com o caso")
    p.add_argument("--categoria")
    p.add_argument("--data-inicio")
    p.add_argument("--hoje", help="data de referencia (por omissao, hoje)")
    p.add_argument("--json", action="store_true", help="saida em JSON")
    p.add_argument("--categorias", action="store_true", help="listar categorias e sair")
    p.add_argument("--recusas", action="store_true", help="listar portas de recusa e sair")
    args = p.parse_args(argv)

    regimes = carregar_regimes()

    if args.categorias:
        for k, v in sorted(regimes["categorias"].items()):
            prazo = "%d meses" % v["meses"] if "meses" in v else "%d anos" % v["anos"]
            print("%-38s %-10s %-22s %s art. %s"
                  % (k, prazo, v["mecanismo"], v["diploma"], v["artigo"]))
        return 0

    if args.recusas:
        for chave, facto, porque, artigo in RECUSAS:
            print("%-36s %s" % (chave, ("art. " + artigo) if artigo else "(fora do corpo capturado)"))
            print("    %s" % facto)
        return 0

    if args.caso:
        with open(args.caso, encoding="utf-8") as fh:
            caso = json.load(fh)
    elif args.categoria and args.data_inicio:
        caso = {"categoria": args.categoria, "data_inicio": args.data_inicio}
    else:
        p.error("indique --caso FICHEIRO ou --categoria e --data-inicio")

    out = analisar(caso, regimes, hoje=args.hoje)
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(_render(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
