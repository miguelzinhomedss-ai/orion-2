# ============================================================
# ORION 2.0 — MAIN
# ============================================================

from inteligencia import OrionIA
from memoria import (
    adicionar_tarefa,
    listar_tarefas,
    concluir_tarefa,
    remover_tarefa,
)
from interface import OrionInterface
from intencoes import detectar_intencao
from comandos import (
    abrir_site,
    abrir_programa,
    obter_hora,
    obter_data,
    resumo_status,
    desligar_pc,
    cancelar_desligamento,
    definir_volume,
    obter_volume,
)

from voz import falar


class Orion:

    def __init__(self):

        print("Inicializando ORION 2.0...")

        self.ia = OrionIA()

        self.interface = OrionInterface(
            self.processar
        )

        print("ORION 2.0 iniciado.")

    def processar_tarefa(self, intencao):
        """Executa uma intenção de tarefa sem acionar IA ou saída de voz."""
        tipo = intencao["tipo"]

        if tipo == "adicionar_tarefa":
            titulo = intencao.get("titulo")
            if not isinstance(titulo, str) or not titulo.strip():
                return "Informe o título da tarefa que deseja adicionar."
            tarefa = adicionar_tarefa(titulo.strip())
            if tarefa is not None:
                return f"Tarefa salva: {tarefa['titulo']}."
            return "Não consegui salvar a tarefa. Tente novamente."

        if tipo == "listar_tarefas":
            tarefas = listar_tarefas()
            if not tarefas:
                return "Nenhuma tarefa disponível na lista."
            linhas = ["Suas tarefas:"]
            for numero, tarefa in enumerate(tarefas, start=1):
                estado = "concluída" if tarefa["concluida"] else "pendente"
                linhas.append(f"{numero}. [{estado}] {tarefa['titulo']}")
            return "\n".join(linhas)

        numero = intencao.get("numero")
        if not isinstance(numero, int) or isinstance(numero, bool) or numero < 1:
            return "Informe um número de tarefa válido, começando em 1."

        if tipo == "concluir_tarefa":
            if concluir_tarefa(numero):
                return f"Tarefa {numero} concluída e salva."
            return (
                f"Não consegui concluir a tarefa {numero}. Ela pode não existir, "
                "já estar concluída ou pode ter ocorrido uma falha ao salvar."
            )

        if remover_tarefa(numero):
            return f"Tarefa {numero} removida."
        return (
            f"Não consegui remover a tarefa {numero}. Ela pode não existir "
            "ou pode ter ocorrido uma falha ao salvar."
        )

    def processar(self, texto):
        texto_original = texto.strip()

        intencao = detectar_intencao(texto_original)
        tipo = intencao["tipo"]

        if tipo in (
            "adicionar_tarefa", "listar_tarefas", "concluir_tarefa", "remover_tarefa"
        ):
            resposta = self.processar_tarefa(intencao)
            falar(resposta)
            return resposta

        # =========================
        # VOLUME
        # =========================

        if tipo == "alterar_volume":
            valor = intencao["valor"]

            sucesso = definir_volume(valor)

            resposta = (
                f"Volume ajustado para {valor}%."
                if sucesso
                else "Não consegui alterar o volume."
            )

            falar(resposta)
            return resposta

        # =========================
        # STATUS DO PC
        # =========================

        if tipo == "status_pc":
            resposta = resumo_status()
            falar(resposta)
            return resposta

        # =========================
        # CONSULTAR VOLUME
        # =========================

        if tipo == "consultar_volume":
            volume = obter_volume()

            resposta = (
                "Não consegui consultar o volume."
                if volume is None
                else f"O volume está em {volume}%."
            )

            falar(resposta)
            return resposta

        # =========================
        # ABRIR SITE
        # =========================

        if tipo == "abrir_site":
            site = intencao["site"]

            sucesso = abrir_site(site)

            resposta = (
                f"Abrindo o {site}."
                if sucesso
                else f"Não consegui abrir o {site}."
            )

            falar(resposta)
            return resposta

        # =========================
        # ABRIR PROGRAMA
        # =========================

        if tipo == "abrir_programa":
            programa = intencao["programa"]

            sucesso = abrir_programa(programa)

            resposta = (
                f"Abrindo o {programa}."
                if sucesso
                else f"Não consegui abrir o {programa}."
            )

            falar(resposta)
            return resposta

        # =========================
        # HORA
        # =========================

        if tipo == "hora":
            resposta = f"Agora são {obter_hora()}."
            falar(resposta)
            return resposta

        # =========================
        # DATA
        # =========================

        if tipo == "data":
            resposta = f"Hoje é {obter_data()}."
            falar(resposta)
            return resposta

        # =========================
        # CANCELAR DESLIGAMENTO
        # =========================

        if tipo == "cancelar_desligamento":
            sucesso = cancelar_desligamento()

            resposta = (
                "Desligamento cancelado."
                if sucesso
                else "Não consegui cancelar o desligamento."
            )

            falar(resposta)
            return resposta

        # =========================
        # DESLIGAR PC
        # =========================

        if tipo == "desligar_pc":
            sucesso = desligar_pc(3600)

            resposta = (
                "Desligamento programado para uma hora."
                if sucesso
                else "Não consegui programar o desligamento."
            )

            falar(resposta)
            return resposta

        # =========================
        # INTELIGÊNCIA ARTIFICIAL
        # =========================

        resposta = self.ia.perguntar(texto_original)
        falar(resposta)
        return resposta
        # ====================================================
        # SITES
        # ====================================================

        sites = {
            "youtube": ["youtube", "you tube"],
            "google": ["google"],
            "spotify": ["spotify"],
            "github": ["github"],
            "gmail": ["gmail", "e-mail"],
            "instagram": ["instagram", "insta"],
        }

        for site, palavras in sites.items():

            if any(
                palavra in texto_lower
                for palavra in palavras
            ):

                sucesso = abrir_site(site)

                if sucesso:
                    resposta = f"Abrindo o {site}."
                else:
                    resposta = f"Não consegui abrir o {site}."

                falar(resposta)

                return resposta

        # ====================================================
        # CALCULADORA
        # ====================================================

        if "calculadora" in texto_lower:

            sucesso = abrir_programa("calculadora")

            if sucesso:
                resposta = "Abrindo a calculadora."
            else:
                resposta = "Não consegui abrir a calculadora."

            falar(resposta)

            return resposta

        # ====================================================
        # BLOCO DE NOTAS
        # ====================================================

        if (
            "bloco de notas" in texto_lower
            or "notepad" in texto_lower
        ):

            sucesso = abrir_programa("bloco de notas")

            if sucesso:
                resposta = "Abrindo o bloco de notas."
            else:
                resposta = "Não consegui abrir o bloco de notas."

            falar(resposta)

            return resposta

        # ====================================================
        # HORA
        # ====================================================

        if (
            "que horas" in texto_lower
            or "qual a hora" in texto_lower
            or texto_lower == "hora"
        ):

            resposta = f"Agora são {obter_hora()}."

            falar(resposta)

            return resposta

        # ====================================================
        # DATA
        # ====================================================

        if (
            "qual a data" in texto_lower
            or "que dia é hoje" in texto_lower
            or "que dia e hoje" in texto_lower
        ):

            resposta = f"Hoje é {obter_data()}."

            falar(resposta)

            return resposta

        # ====================================================
        # STATUS DO PC
        # ====================================================

        if (
            "status do pc" in texto_lower
            or "status do computador" in texto_lower
            or "como está meu pc" in texto_lower
            or "como esta meu pc" in texto_lower
        ):

            resposta = resumo_status()

            falar(resposta)

            return resposta

        # ====================================================
        # VOLUME
        # ====================================================

        if (
            "qual o volume" in texto_lower
            or "volume atual" in texto_lower
        ):

            volume = obter_volume()

            if volume is None:
                resposta = "Não consegui consultar o volume."
            else:
                resposta = f"O volume está em {volume}%."

            falar(resposta)

            return resposta

        # ====================================================
        # ALTERAR VOLUME
        # ====================================================

        if "volume" in texto_lower:

            import re

            resultado = re.search(
                r"(\d{1,3})\s*%",
                texto_lower
            )

            if resultado:

                valor = int(resultado.group(1))

                sucesso = definir_volume(valor)

                if sucesso:
                    resposta = f"Volume ajustado para {valor}%."
                else:
                    resposta = "Não consegui alterar o volume."

                falar(resposta)

                return resposta

        # ====================================================
        # CANCELAR DESLIGAMENTO
        # ====================================================

        if (
            "cancelar desligamento" in texto_lower
            or "cancela o desligamento" in texto_lower
        ):

            sucesso = cancelar_desligamento()

            if sucesso:
                resposta = "Desligamento cancelado."
            else:
                resposta = "Não consegui cancelar o desligamento."

            falar(resposta)

            return resposta

        # ====================================================
        # DESLIGAR PC
        # ====================================================

        if (
            "desligar o pc" in texto_lower
            or "desliga o pc" in texto_lower
            or "desligar computador" in texto_lower
        ):

            sucesso = desligar_pc(3600)

            if sucesso:
                resposta = "Desligamento programado para uma hora."
            else:
                resposta = "Não consegui programar o desligamento."

            falar(resposta)

            return resposta

        # ====================================================
        # INTELIGÊNCIA ARTIFICIAL
        # ====================================================

        resposta = self.ia.perguntar(
            texto_original
        )

        falar(resposta)

        return resposta


# ============================================================
# INICIALIZAÇÃO
# ============================================================

def main():

    try:

        orion = Orion()

        orion.interface.iniciar()

    except Exception as erro:

        print()
        print("=" * 60)
        print("ERRO AO INICIAR O ORION")
        print("=" * 60)
        print(erro)
        print()

        input("Pressione ENTER para fechar...")


if __name__ == "__main__":

    main()
