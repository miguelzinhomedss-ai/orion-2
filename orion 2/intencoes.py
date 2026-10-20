import re
import unicodedata


def _numero_tarefa(texto):
    """Converte algarismos e números por extenso de zero a noventa e nove."""
    if re.fullmatch(r"[0-9]+", texto):
        return int(texto)

    unidades = {
        "zero": 0, "um": 1, "uma": 1, "dois": 2, "duas": 2,
        "tres": 3, "quatro": 4, "cinco": 5, "seis": 6,
        "sete": 7, "oito": 8, "nove": 9, "dez": 10,
        "onze": 11, "doze": 12, "treze": 13, "catorze": 14,
        "quatorze": 14, "quinze": 15, "dezesseis": 16,
        "dezessete": 17, "dezoito": 18, "dezenove": 19,
    }
    dezenas = {
        "vinte": 20, "trinta": 30, "quarenta": 40, "cinquenta": 50,
        "sessenta": 60, "setenta": 70, "oitenta": 80, "noventa": 90,
    }
    if texto in unidades:
        return unidades[texto]
    if texto in dezenas:
        return dezenas[texto]
    partes = texto.split(" e ")
    if (len(partes) == 2 and partes[0] in dezenas
            and partes[1] in unidades and 0 < unidades[partes[1]] < 10):
        return dezenas[partes[0]] + unidades[partes[1]]
    return None


def _detectar_tarefa(texto):
    # Normalizar apenas a comparação; o título mantém sua grafia original.
    normalizado = "".join(
        letra for letra in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(letra) != "Mn"
    )
    normalizado = re.sub(r"\s+", " ", normalizado).strip()
    normalizado = re.sub(r"[.!?]+$", "", normalizado).strip()
    normalizado = re.sub(r"^por favor[, ]+", "", normalizado)
    normalizado = re.sub(r",?\s+por favor$", "", normalizado).strip()

    # Remover a cortesia antes de extrair o título, sem alterar seu conteúdo.
    texto_titulo = re.sub(r"^por favor[, ]+", "", texto, flags=re.IGNORECASE)
    texto_titulo = re.sub(r",?\s+por favor[.!?]*$", "", texto_titulo,
                          flags=re.IGNORECASE).strip()
    adicionar = re.match(
        r"^(?:adicionar|adicione|adiciona|criar|crie|cria|incluir|inclua)\s+"
        r"(?:(?:uma|a)\s+)?(?:nova\s+)?tarefa\b\s*:?\s*",
        texto_titulo, flags=re.IGNORECASE,
    )
    if adicionar:
        return {"tipo": "adicionar_tarefa",
                "titulo": texto_titulo[adicionar.end():].strip()}

    if re.fullmatch(
        r"(?:(?:listar|liste|lista|mostrar|mostre|mostra|ver) "
        r"(?:(?:todas )?(?:as )?(?:minhas )?)tarefas"
        r"|quais (?:sao )?(?:as )?minhas tarefas|minhas tarefas)", normalizado
    ):
        return {"tipo": "listar_tarefas"}

    acao = re.fullmatch(
        r"(concluir|conclua|conclui|finalizar|finalize|finaliza|"
        r"remover|remova|remove|excluir|exclua|exclui|apagar|apague|apaga) "
        r"(?:a )?tarefa(?: (?:numero )?(.+))?", normalizado
    )
    if acao:
        numero = _numero_tarefa(acao.group(2)) if acao.group(2) else None
        # Texto livre após o número pode ser conversa, não uma ordem completa.
        if acao.group(2) and numero is None:
            return None
        tipo = ("concluir_tarefa" if acao.group(1).startswith(("concl", "final"))
                else "remover_tarefa")
        return {"tipo": tipo, "numero": numero}
    return None


def detectar_intencao(texto):
    texto = re.sub(r"^\s*orion\b[\s,:;!?.-]*", "", texto,
                   flags=re.IGNORECASE).strip()
    tarefa = _detectar_tarefa(texto)
    if tarefa is not None:
        return tarefa
    texto = texto.lower().strip()

    # =========================
    # SITES
    # =========================

    sites = {
        "youtube": [
            "youtube",
            "you tube",
        ],
        "google": [
            "google",
        ],
        "spotify": [
            "spotify",
        ],
        "github": [
            "github",
        ],
        "gmail": [
            "gmail",
            "e-mail",
            "email",
        ],
        "instagram": [
            "instagram",
            "insta",
        ],
    }

    palavras_abrir = [
        "abrir",
        "abre",
        "abri",
        "entrar",
        "entra",
        "entrar no",
        "ir para",
        "vai para",
        "acessar",
        "acessa",
        "acessar o",
        "acessar a",
        "abre pra mim",
        "abre para mim",
    ]

    for site, palavras in sites.items():
        encontrou_site = any(palavra in texto for palavra in palavras)
        encontrou_acao = any(palavra in texto for palavra in palavras_abrir)

        if encontrou_site and encontrou_acao:
            return {
                "tipo": "abrir_site",
                "site": site
            }

    # Frases extremamente naturais
    for site, palavras in sites.items():
        if any(palavra in texto for palavra in palavras):
            if any(
                palavra in texto
                for palavra in [
                    "abre",
                    "abrir",
                    "acessa",
                    "acessar",
                    "entrar",
                    "entra",
                    "vai",
                ]
            ):
                return {
                    "tipo": "abrir_site",
                    "site": site
                }

    # =========================
    # PROGRAMAS
    # =========================

    if (
        "calculadora" in texto
        and any(
            palavra in texto
            for palavra in [
                "abre",
                "abrir",
                "acessa",
                "acessar",
                "inicia",
                "iniciar",
                "executa",
            ]
        )
    ):
        return {
            "tipo": "abrir_programa",
            "programa": "calculadora"
        }

    if (
        "bloco de notas" in texto
        or "notepad" in texto
    ):
        return {
            "tipo": "abrir_programa",
            "programa": "bloco de notas"
        }

    # =========================
    # HORA
    # =========================

    if (
        "que horas" in texto
        or "qual a hora" in texto
        or "que hora" in texto
        or texto == "hora"
        or "horas são" in texto
        or "horas sao" in texto
    ):
        return {
            "tipo": "hora"
        }

    # =========================
    # DATA
    # =========================

    if (
        "qual a data" in texto
        or "que dia é hoje" in texto
        or "que dia e hoje" in texto
        or "qual é a data" in texto
        or "qual e a data" in texto
        or "data de hoje" in texto
    ):
        return {
            "tipo": "data"
        }

    # =========================
    # STATUS DO PC
    # =========================

    if (
        "status do pc" in texto
        or "status do computador" in texto
        or "como está meu pc" in texto
        or "como esta meu pc" in texto
        or "como está meu computador" in texto
        or "como esta meu computador" in texto
        or "como tá meu pc" in texto
        or "como ta meu pc" in texto
        or "como tá meu computador" in texto
        or "como ta meu computador" in texto
        or "como está o pc" in texto
        or "como esta o pc" in texto
        or "como está o computador" in texto
        or "como esta o computador" in texto
    ):
        return {
            "tipo": "status_pc"
        }

    # =========================
    # VOLUME
    # =========================

    if (
        "qual o volume" in texto
        or "volume atual" in texto
        or "quanto está o volume" in texto
        or "quanto esta o volume" in texto
        or "qual está o volume" in texto
        or "qual esta o volume" in texto
    ):
        return {
            "tipo": "consultar_volume"
        }

    resultado_volume = re.search(
        r"(\d{1,3})\s*%",
        texto
    )

    if (
        resultado_volume
        and "volume" in texto
    ):
        return {
            "tipo": "alterar_volume",
            "valor": int(resultado_volume.group(1))
        }

    # =========================
    # DESLIGAMENTO
    # =========================

    if (
        "cancelar desligamento" in texto
        or "cancela o desligamento" in texto
        or "cancele o desligamento" in texto
        or "cancelar o desligamento" in texto
    ):
        return {
            "tipo": "cancelar_desligamento"
        }

    if (
        "desligar o pc" in texto
        or "desliga o pc" in texto
        or "desligar computador" in texto
        or "desliga o computador" in texto
        or "desligue o computador" in texto
        or "desligue o pc" in texto
    ):
        return {
            "tipo": "desligar_pc"
        }

    # =========================
    # PADRÃO
    # =========================

    return {
        "tipo": "ia"
    }
