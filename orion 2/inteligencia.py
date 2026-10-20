# ============================================================
# ORION 2.0 — INTELIGÊNCIA + MEMÓRIA AUTOMÁTICA
# ============================================================

from groq import Groq

from config import GROQ_API_KEY, MODEL, MAX_HISTORY

from memoria import (
    carregar_memoria,
    adicionar_memoria,
    salvar_memoria,
    limpar_memoria
)


class OrionIA:

    def __init__(self):

        self.historico = []

        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY não foi encontrada no arquivo .env"
            )

        self.cliente = Groq(
            api_key=GROQ_API_KEY
        )

        self.system_prompt = """
Você é ORION, um assistente pessoal avançado.

Seu objetivo é ajudar o usuário de maneira natural,
inteligente, objetiva e amigável.

Você fala português do Brasil por padrão.

Características:
- Respostas naturais e humanas.
- Não seja excessivamente formal.
- Entenda contexto entre mensagens.
- Evite repetir informações desnecessariamente.
- Quando o usuário pedir algo simples, responda de forma simples.
- Quando o assunto exigir explicação, explique passo a passo.
- Se não souber algo, diga claramente que não sabe.
- Nunca invente informações.
- Você é um assistente pessoal chamado ORION.

O usuário pode falar de maneira informal.
Entenda abreviações, gírias e erros comuns de digitação
quando o significado estiver claro.

MEMÓRIA:
Você possui acesso às memórias salvas do usuário.

Use as memórias somente quando forem relevantes.
Nunca invente uma memória.
"""

    # ========================================================
    # HISTÓRICO
    # ========================================================

    def limpar_historico(self):

        self.historico.clear()


    def adicionar_mensagem(self, role, conteudo):

        self.historico.append({
            "role": role,
            "content": conteudo
        })

        if len(self.historico) > MAX_HISTORY:

            self.historico = self.historico[-MAX_HISTORY:]


    # ========================================================
    # MEMÓRIA
    # ========================================================

    def obter_memoria(self):

        memoria = carregar_memoria()

        if not memoria:
            return "Nenhuma memória salva."

        return "\n".join(
            f"- {item}"
            for item in memoria
        )


    # ========================================================
    # MEMÓRIA AUTOMÁTICA
    # ========================================================

    def detectar_memoria_automatica(self, texto):

        texto_original = texto.strip()

        if not texto_original:
            return None

        texto_lower = texto_original.lower()

        # ====================================================
        # MEMÓRIAS QUE PODEM SER ATUALIZADAS
        # ====================================================

        categorias = {

            "nome": [
                "meu nome é ",
                "meu nome e "
            ],

            "jogo_favorito": [
                "meu jogo favorito é ",
                "meu jogo favorito e "
            ],

            "comida_favorita": [
                "minha comida favorita é ",
                "minha comida favorita e "
            ],

            "cor_favorita": [
                "minha cor favorita é ",
                "minha cor favorita e "
            ],

            "filme_favorito": [
                "meu filme favorito é ",
                "meu filme favorito e "
            ],

            "serie_favorita": [
                "minha série favorita é ",
                "minha série favorita e ",
                "minha serie favorita é ",
                "minha serie favorita e "
            ],

            "objetivo": [
                "meu objetivo é ",
                "meu objetivo e "
            ]
        }

        # ====================================================
        # VERIFICAR CADA CATEGORIA
        # ====================================================

        for categoria, gatilhos in categorias.items():

            for gatilho in gatilhos:

                if texto_lower.startswith(gatilho):

                    informacao = texto_original[
                        len(gatilho):
                    ].strip()

                    if not informacao:
                        return None

                    memoria = carregar_memoria()

                    # =========================================
                    # PROCURAR MEMÓRIA ANTIGA DA MESMA CATEGORIA
                    # =========================================

                    memoria_nova = []

                    for item in memoria:

                        item_lower = item.lower()

                        pertence_categoria = False

                        for outro_gatilho in gatilhos:

                            if item_lower.startswith(
                                outro_gatilho
                            ):
                                pertence_categoria = True
                                break

                        if not pertence_categoria:

                            memoria_nova.append(item)

                    # =========================================
                    # ADICIONAR NOVA INFORMAÇÃO
                    # =========================================

                    memoria_nova.append(texto_original)

                    salvar_memoria(memoria_nova)

                    print(
                        f"[MEMÓRIA ATUALIZADA] "
                        f"{texto_original}"
                    )

                    return texto_original

        # ====================================================
        # OUTRAS MEMÓRIAS
        # ====================================================

        gatilhos = [

            "eu gosto de ",
            "eu gosto muito de ",

            "eu amo ",

            "eu odeio ",

            "eu estudo em ",

            "eu moro em ",

            "eu prefiro ",

            "eu tenho ",

            "eu quero ",

            "eu sou ",

            "eu trabalho com ",

            "eu estou aprendendo ",

            "eu estou estudando "
        ]

        for gatilho in gatilhos:

            if texto_lower.startswith(gatilho):

                informacao = texto_original[
                    len(gatilho):
                ].strip()

                if not informacao:
                    return None

                memoria = carregar_memoria()

                # Evita duplicação
                for item in memoria:

                    if item.lower() == texto_lower:
                        return None

                adicionar_memoria(texto_original)

                print(
                    f"[MEMÓRIA AUTOMÁTICA] "
                    f"{texto_original}"
                )

                return texto_original

        return None


    # ========================================================
    # COMANDOS EXPLÍCITOS DE MEMÓRIA
    # ========================================================

    def processar_memoria(self, texto):

        texto_original = texto.strip()

        texto_lower = texto_original.lower()

        # ----------------------------------------------------
        # SALVAR MANUALMENTE
        # ----------------------------------------------------

        gatilhos_salvar = [

            "lembre que",
            "lembra que",
            "guarde que",
            "guarda que",
            "memorize que",
            "memoriza que"
        ]

        for gatilho in gatilhos_salvar:

            if texto_lower.startswith(gatilho):

                conteudo = texto_original[
                    len(gatilho):
                ].strip()

                if not conteudo:

                    return (
                        "O que você quer que eu lembre?"
                    )

                memoria = carregar_memoria()

                for item in memoria:

                    if item.lower() == conteudo.lower():

                        return (
                            "Isso já está salvo na minha memória."
                        )

                adicionar_memoria(conteudo)

                return (
                    f"Entendido. Vou lembrar disso: {conteudo}"
                )

        # ----------------------------------------------------
        # CONSULTAR
        # ----------------------------------------------------

        gatilhos_consulta = [

            "o que você lembra",
            "o que voce lembra",

            "o que você sabe sobre mim",
            "o que voce sabe sobre mim",

            "quais são minhas memórias",
            "quais sao minhas memorias",

            "minhas memórias",
            "minhas memorias"
        ]

        for gatilho in gatilhos_consulta:

            if gatilho in texto_lower:

                memoria = carregar_memoria()

                if not memoria:

                    return (
                        "Ainda não tenho nenhuma memória salva."
                    )

                resposta = (
                    "Estas são as coisas que eu lembro:\n\n"
                )

                for numero, item in enumerate(
                    memoria,
                    start=1
                ):

                    resposta += (
                        f"{numero}. {item}\n"
                    )

                return resposta.strip()

        # ----------------------------------------------------
        # APAGAR TODAS
        # ----------------------------------------------------

        gatilhos_limpar = [

            "apague todas as memórias",
            "apaga todas as memórias",

            "apague todas as memorias",
            "apaga todas as memorias",

            "esqueça tudo",
            "esqueca tudo",

            "limpe minha memória",
            "limpa minha memória",

            "limpe minha memoria",
            "limpa minha memoria"
        ]

        for gatilho in gatilhos_limpar:

            if gatilho in texto_lower:

                limpar_memoria()

                return (
                    "Todas as minhas memórias foram apagadas."
                )

        # ----------------------------------------------------
        # ESQUECER UMA MEMÓRIA
        # ----------------------------------------------------

        gatilhos_esquecer = [

            "esqueça que",
            "esqueca que",

            "esqueça",
            "esqueca"
        ]

        for gatilho in gatilhos_esquecer:

            if texto_lower.startswith(gatilho):

                conteudo = texto_original[
                    len(gatilho):
                ].strip()

                if not conteudo:

                    return (
                        "O que você quer que eu esqueça?"
                    )

                memoria = carregar_memoria()

                memoria_nova = [

                    item for item in memoria

                    if conteudo.lower()
                    not in item.lower()
                ]

                if len(memoria_nova) == len(memoria):

                    return (
                        "Não encontrei uma memória "
                        "correspondente."
                    )

                salvar_memoria(memoria_nova)

                return (
                    f"Entendido. Esqueci a informação "
                    f"relacionada a: {conteudo}"
                )

        return None


    # ========================================================
    # PERGUNTAR À IA
    # ========================================================

    def perguntar(self, texto):

        if not texto or not texto.strip():

            return "Pode falar."

        texto = texto.strip()

        # ====================================================
        # COMANDOS EXPLÍCITOS DE MEMÓRIA
        # ====================================================

        resposta_memoria = self.processar_memoria(
            texto
        )

        if resposta_memoria is not None:

            self.adicionar_mensagem(
                "user",
                texto
            )

            self.adicionar_mensagem(
                "assistant",
                resposta_memoria
            )

            return resposta_memoria

        # ====================================================
        # MEMÓRIA AUTOMÁTICA
        # ====================================================

        memoria_detectada = (
            self.detectar_memoria_automatica(texto)
        )

        if memoria_detectada:

            print(
                "[ORION] Informação importante "
                "detectada e armazenada."
            )

        # ====================================================
        # MEMÓRIA ATUAL
        # ====================================================

        memoria_atual = self.obter_memoria()

        contexto_memoria = f"""
MEMÓRIAS SALVAS DO USUÁRIO:

{memoria_atual}

Use essas informações somente quando forem
relevantes para a conversa.
"""

        # ====================================================
        # HISTÓRICO
        # ====================================================

        self.adicionar_mensagem(
            "user",
            texto
        )

        mensagens = [

            {
                "role": "system",
                "content": (
                    self.system_prompt
                    + "\n\n"
                    + contexto_memoria
                )
            }

        ]

        mensagens.extend(
            self.historico
        )

        # ====================================================
        # GROQ
        # ====================================================

        try:

            resposta = (
                self.cliente.chat.completions.create(

                    model=MODEL,

                    messages=mensagens,

                    temperature=0.7,

                    max_tokens=1200
                )
            )

            conteudo = (
                resposta
                .choices[0]
                .message
                .content
            )

            if not conteudo:

                return (
                    "Não consegui gerar uma resposta."
                )

            conteudo = conteudo.strip()

            self.adicionar_mensagem(
                "assistant",
                conteudo
            )

            return conteudo

        except Exception as erro:

            print(
                f"[IA] Erro: {erro}"
            )

            return (
                "Tive um problema ao acessar meu sistema "
                "de inteligência agora."
            )


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":

    orion = OrionIA()

    print()
    print("========================================")
    print(" ORION 2.0 — AUTO MEMORY")
    print("========================================")
    print()

    testes = [

        "Meu nome é Miguel",

        "Meu jogo favorito é Minecraft",

        "Eu gosto de futebol",

        "Qual é meu jogo favorito?"
    ]

    for teste in testes:

        print(f"VOCÊ: {teste}")

        resposta = orion.perguntar(teste)

        print(f"ORION: {resposta}")

        print("----------------------------------------")