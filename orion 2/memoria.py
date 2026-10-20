# ============================================================
# ORION 2.0 — MEMÓRIA
# ============================================================

import json
import os
from config import MEMORY_FILE, TASKS_FILE


# ============================================================
# MEMÓRIA
# ============================================================

def carregar_memoria():
    """Carrega as memórias salvas do ORION."""

    if not os.path.exists(MEMORY_FILE):
        return []

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

            if isinstance(dados, list):
                return dados

            return []

    except (json.JSONDecodeError, OSError):
        return []


def salvar_memoria(memoria):
    """Salva a memória no arquivo JSON."""

    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as arquivo:
            json.dump(
                memoria,
                arquivo,
                ensure_ascii=False,
                indent=4
            )

        return True

    except OSError:
        return False


def adicionar_memoria(texto):
    """Adiciona uma nova memória."""

    memoria = carregar_memoria()

    if texto.strip():
        memoria.append(texto.strip())
        salvar_memoria(memoria)

    return memoria


def limpar_memoria():
    """Apaga todas as memórias."""

    salvar_memoria([])
    return []


def quantidade_memorias():
    """Retorna quantas memórias existem."""

    return len(carregar_memoria())



# ============================================================
# TAREFAS
# ============================================================

def carregar_tarefas():
    """Carrega as tarefas salvas."""

    if not os.path.exists(TASKS_FILE):
        return []

    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        if isinstance(dados, list):
            return [
                tarefa for tarefa in dados
                if isinstance(tarefa, dict)
                and "titulo" in tarefa
                and "concluida" in tarefa
            ]

        return []

    except (json.JSONDecodeError, OSError):
        return []


def salvar_tarefas(tarefas):
    """Salva as tarefas e informa se deu certo."""

    try:
        with open(TASKS_FILE, "w", encoding="utf-8") as arquivo:
            json.dump(
                tarefas,
                arquivo,
                ensure_ascii=False,
                indent=4
            )

        return True

    except OSError:
        return False


def adicionar_tarefa(titulo):
    """Cria uma tarefa se o título não estiver vazio."""

    if not isinstance(titulo, str) or not titulo.strip():
        return None

    tarefas = carregar_tarefas()

    nova_tarefa = {
        "titulo": titulo.strip(),
        "concluida": False
    }

    tarefas.append(nova_tarefa)

    if salvar_tarefas(tarefas):
        return nova_tarefa

    return None


def concluir_tarefa(numero):
    """Marca uma tarefa existente como concluída."""

    tarefas = carregar_tarefas()

    if not isinstance(numero, int) or isinstance(numero, bool):
        return False

    indice = numero - 1

    if 0 <= indice < len(tarefas):
        if tarefas[indice]["concluida"]:
            return False

        tarefas[indice]["concluida"] = True
        return salvar_tarefas(tarefas)

    return False


def remover_tarefa(numero):
    """Remove uma tarefa existente."""

    tarefas = carregar_tarefas()

    if not isinstance(numero, int) or isinstance(numero, bool):
        return False

    indice = numero - 1

    if 0 <= indice < len(tarefas):
        tarefas.pop(indice)
        return salvar_tarefas(tarefas)

    return False


def listar_tarefas():
    """Retorna todas as tarefas salvas."""

    return carregar_tarefas()
