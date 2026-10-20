# ============================================================
# ORION 2.0 — HUD INTERFACE
# ============================================================

import tkinter as tk
import threading
import queue
import re
from tkinter import scrolledtext

from voz_entrada import ReconhecedorVoz

from config import (
    APP_NAME,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    BG_COLOR,
    CYAN,
    GREEN,
    WHITE,
    GRAY,
    DARK_GRAY,
)


class OrionInterface:

    def __init__(self, responder):

        self.responder = responder
        self.modo_voz = False
        self.encerrando = False
        self.eventos = queue.Queue()
        self.sessao_voz = 0
        self.escuta_ativa = False
        self.processamento_ativo = False
        self.textos_pendentes = []
        self.cancelamento_voz = threading.Event()
        self._fila_after = None

        self.root = tk.Tk()
        self.root.title("ORION 2.0 // SYSTEM CORE")
        self.root.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
        )
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(1000, 650)

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.fechar
        )

        self.reconhecedor_voz = ReconhecedorVoz()

        # ====================================================
        # VARIAVEIS DO CORE
        # ====================================================

        self.core_pulse = 0
        self.core_direction = 1

        # ====================================================
        # TOPO
        # ====================================================

        self.topo = tk.Frame(
            self.root,
            bg=BG_COLOR
        )

        self.topo.pack(
            fill="x",
            padx=25,
            pady=(15, 8)
        )

        # Logo

        logo_area = tk.Frame(
            self.topo,
            bg=BG_COLOR
        )

        logo_area.pack(
            side="left"
        )

        self.logo = tk.Label(
            logo_area,
            text="◈ ORION",
            font=("Segoe UI", 25, "bold"),
            fg=CYAN,
            bg=BG_COLOR
        )

        self.logo.pack(
            side="left"
        )

        self.sublogo = tk.Label(
            logo_area,
            text="  AI ASSISTANT // 2.0",
            font=("Consolas", 9, "bold"),
            fg=GRAY,
            bg=BG_COLOR
        )

        self.sublogo.pack(
            side="left",
            pady=(10, 0)
        )

        # Informações do sistema

        info = tk.Frame(
            self.topo,
            bg=BG_COLOR
        )

        info.pack(
            side="right"
        )

        self.cpu_top = tk.Label(
            info,
            text="CPU  --%",
            font=("Consolas", 9, "bold"),
            fg=GRAY,
            bg=BG_COLOR
        )

        self.cpu_top.pack(
            side="left",
            padx=15
        )

        self.ram_top = tk.Label(
            info,
            text="RAM  --%",
            font=("Consolas", 9, "bold"),
            fg=GRAY,
            bg=BG_COLOR
        )

        self.ram_top.pack(
            side="left",
            padx=15
        )

        self.status = tk.Label(
            info,
            text="● STANDBY",
            font=("Consolas", 10, "bold"),
            fg=GREEN,
            bg=BG_COLOR
        )

        self.status.pack(
            side="left",
            padx=15
        )

        # Linha futurista

        linha = tk.Frame(
            self.root,
            bg=CYAN,
            height=1
        )

        linha.pack(
            fill="x",
            padx=25
        )

        # ====================================================
        # AREA PRINCIPAL
        # ====================================================

        principal = tk.Frame(
            self.root,
            bg=BG_COLOR
        )

        principal.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=15
        )

        # ====================================================
        # PAINEL ESQUERDO
        # ====================================================

        esquerda = tk.Frame(
            principal,
            bg=BG_COLOR,
            width=220
        )

        esquerda.pack(
            side="left",
            fill="y",
            padx=(0, 12)
        )

        self.criar_painel(
            esquerda,
            "SYSTEM",
            [
                "CPU",
                "RAM",
                "DISCO",
                "NETWORK",
                "STATUS",
            ]
        )

        self.criar_quick_access(
            esquerda
        )

        # ====================================================
        # CENTRO
        # ====================================================

        centro = tk.Frame(
            principal,
            bg=BG_COLOR
        )

        centro.pack(
            side="left",
            fill="both",
            expand=True
        )

        # ====================================================
        # CORE CENTRAL
        # ====================================================

        area_core = tk.Frame(
            centro,
            bg=BG_COLOR
        )

        area_core.pack(
            fill="both",
            expand=True
        )

        self.core_canvas = tk.Canvas(
            area_core,
            bg=BG_COLOR,
            highlightthickness=0
        )

        self.core_canvas.pack(
            fill="both",
            expand=True
        )

        self.core_canvas.bind(
            "<Configure>",
            self.desenhar_core
        )

        # ====================================================
        # CHAT
        # ====================================================

        chat_painel = tk.Frame(
            centro,
            bg=DARK_GRAY,
            highlightbackground="#12303a",
            highlightthickness=1,
            height=185
        )

        chat_painel.pack(
            fill="x",
            pady=(8, 0)
        )

        chat_painel.pack_propagate(False)

        chat_titulo = tk.Label(
            chat_painel,
            text="  ◈ ORION CHAT // LIVE CONSOLE",
            anchor="w",
            font=("Consolas", 9, "bold"),
            fg=CYAN,
            bg=DARK_GRAY
        )

        chat_titulo.pack(
            fill="x",
            padx=8,
            pady=(7, 4)
        )

        chat_linha = tk.Frame(
            chat_painel,
            bg="#12303a",
            height=1
        )

        chat_linha.pack(
            fill="x",
            padx=8
        )

        self.chat = scrolledtext.ScrolledText(
            chat_painel,
            bg="#07111a",
            fg=WHITE,
            insertbackground=CYAN,
            font=("Consolas", 9),
            relief="flat",
            bd=0,
            wrap="word",
            state="disabled",
            padx=10,
            pady=7
        )

        self.chat.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=7
        )

        self.chat.tag_config(
            "user_name",
            foreground=CYAN,
            font=("Consolas", 9, "bold")
        )

        self.chat.tag_config(
            "user_msg",
            foreground=WHITE,
            lmargin1=12,
            lmargin2=12
        )

        self.chat.tag_config(
            "orion_name",
            foreground=GREEN,
            font=("Consolas", 9, "bold")
        )

        self.chat.tag_config(
            "orion_msg",
            foreground=WHITE,
            lmargin1=12,
            lmargin2=12
        )

        self.chat.tag_config(
            "system_name",
            foreground=GRAY,
            font=("Consolas", 9, "bold")
        )

        self.chat.tag_config(
            "system_msg",
            foreground=GRAY,
            lmargin1=12,
            lmargin2=12
        )

        # ====================================================
        # PAINEL DIREITO
        # ====================================================

        direita = tk.Frame(
            principal,
            bg=BG_COLOR,
            width=280
        )

        direita.pack(
            side="right",
            fill="y",
            padx=(12, 0)
        )

        self.criar_painel(
            direita,
            "VOICE COMMANDS",
            [
                "abrir youtube",
                "abrir google",
                "abrir spotify",
                "abrir instagram",
                "que horas sao",
                "status do pc",
                "volume 50%",
                "desligar pc",
            ]
        )

        # ====================================================
        # AREA INFERIOR
        # ====================================================

        inferior = tk.Frame(
            self.root,
            bg=BG_COLOR
        )

        inferior.pack(
            fill="x",
            padx=25,
            pady=(0, 18)
        )

        self.estado_texto = tk.Label(
            inferior,
            text="ORION CORE // AGUARDANDO COMANDO",
            font=("Consolas", 10, "bold"),
            fg=CYAN,
            bg=BG_COLOR
        )

        self.estado_texto.pack(
            side="left",
            padx=(0, 15)
        )

        self.entrada = tk.Entry(
            inferior,
            bg=DARK_GRAY,
            fg=WHITE,
            insertbackground=CYAN,
            font=("Consolas", 11),
            relief="flat"
        )

        self.entrada.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=10,
            padx=(0, 8)
        )

        self.entrada.bind(
            "<Return>",
            self.enviar
        )

        self.botao = tk.Button(
            inferior,
            text="ENVIAR",
            command=self.enviar,
            bg=CYAN,
            fg="#001018",
            activebackground=GREEN,
            activeforeground="#001018",
            font=("Consolas", 9, "bold"),
            relief="flat",
            padx=20,
            pady=9,
            cursor="hand2"
        )

        self.botao.pack(
            side="right"
        )

        self.botao_voz = tk.Button(
            inferior,
            text="VOZ",
            command=self.alternar_voz,
            bg=DARK_GRAY,
            fg=CYAN,
            activebackground=CYAN,
            activeforeground="#001018",
            font=("Consolas", 9, "bold"),
            relief="flat",
            padx=18,
            pady=9,
            cursor="hand2"
        )

        self.botao_voz.pack(
            side="right",
            padx=(0, 8)
        )

        # ====================================================
        # MONITORAMENTO
        # ====================================================

        self.atualizar_sistema()

        # ====================================================
        # MENSAGEM INICIAL
        # ====================================================

        self.adicionar_mensagem(
            "ORION",
            "SYSTEM ONLINE // Aguardando comando."
        )

        # ====================================================
        # ANIMAÇÃO
        # ====================================================

        self.animar_core()
        self.consumir_eventos()

    # ========================================================
    # QUICK ACCESS
    # ========================================================

    def criar_quick_access(self, parent):

        painel = tk.Frame(
            parent,
            bg=DARK_GRAY,
            highlightbackground="#12303a",
            highlightthickness=1
        )

        painel.pack(
            fill="x",
            pady=(0, 12)
        )

        titulo = tk.Label(
            painel,
            text="  QUICK ACCESS",
            anchor="w",
            font=("Consolas", 9, "bold"),
            fg=CYAN,
            bg=DARK_GRAY
        )

        titulo.pack(
            fill="x",
            padx=8,
            pady=(8, 5)
        )

        linha = tk.Frame(
            painel,
            bg="#12303a",
            height=1
        )

        linha.pack(
            fill="x",
            padx=8
        )

        botoes = [
            ("▶  YOUTUBE", self.abrir_youtube),
            ("◉  GOOGLE", self.abrir_google),
            ("♪  SPOTIFY", self.abrir_spotify),
            ("◎  INSTAGRAM", self.abrir_instagram),
            ("▣  STEAM", self.abrir_steam),
        ]

        for texto, comando in botoes:

            botao = tk.Button(
                painel,
                text=texto,
                command=comando,
                anchor="w",
                bg=DARK_GRAY,
                fg=GRAY,
                activebackground="#12303a",
                activeforeground=CYAN,
                font=("Consolas", 8, "bold"),
                relief="flat",
                bd=0,
                cursor="hand2"
            )

            botao.pack(
                fill="x",
                padx=8,
                pady=3
            )

        tk.Frame(
            painel,
            bg=DARK_GRAY,
            height=6
        ).pack()

    def abrir_youtube(self):

        import webbrowser

        webbrowser.open(
            "https://www.youtube.com"
        )

    def abrir_google(self):

        import webbrowser

        webbrowser.open(
            "https://www.google.com"
        )

    def abrir_spotify(self):

        from comandos import abrir_spotify

        abrir_spotify()

    def abrir_instagram(self):

        import webbrowser

        webbrowser.open(
            "https://www.instagram.com"
        )

    def abrir_steam(self):

        from comandos import abrir_programa

        abrir_programa("steam")

    # ========================================================
    # PAINÉIS
    # ========================================================

    def criar_painel(
        self,
        parent,
        titulo,
        itens
    ):

        painel = tk.Frame(
            parent,
            bg=DARK_GRAY,
            highlightbackground="#12303a",
            highlightthickness=1
        )

        painel.pack(
            fill="x",
            pady=(0, 12)
        )

        titulo_label = tk.Label(
            painel,
            text=f"  {titulo}",
            anchor="w",
            font=("Consolas", 9, "bold"),
            fg=CYAN,
            bg=DARK_GRAY
        )

        titulo_label.pack(
            fill="x",
            padx=8,
            pady=(8, 5)
        )

        linha = tk.Frame(
            painel,
            bg="#12303a",
            height=1
        )

        linha.pack(
            fill="x",
            padx=8
        )

        for item in itens:

            label = tk.Label(
                painel,
                text=f"  {item}",
                anchor="w",
                font=("Consolas", 8),
                fg=GRAY,
                bg=DARK_GRAY
            )

            label.pack(
                fill="x",
                padx=8,
                pady=4
            )

            if titulo == "SYSTEM":

                if item == "CPU":
                    self.painel_cpu = label

                elif item == "RAM":
                    self.painel_ram = label

                elif item == "DISCO":
                    self.painel_disco = label

                elif item == "NETWORK":
                    self.painel_network = label

                elif item == "STATUS":
                    self.painel_status = label

        tk.Frame(
            painel,
            bg=DARK_GRAY,
            height=6
        ).pack()

    # ========================================================
    # MONITORAMENTO
    # ========================================================

    def atualizar_sistema(self):

        try:

            import psutil

            cpu = psutil.cpu_percent(
                interval=None
            )

            ram = psutil.virtual_memory().percent

            disco = psutil.disk_usage(
                "/"
            ).percent

            try:

                conexoes = psutil.net_if_stats()

                conectado = any(
                    info.isup
                    for info in conexoes.values()
                )

            except Exception:

                conectado = False

            # TOP

            self.cpu_top.config(
                text=f"CPU  {cpu:.0f}%"
            )

            self.ram_top.config(
                text=f"RAM  {ram:.0f}%"
            )

            # SYSTEM

            self.painel_cpu.config(
                text=f"  CPU       {cpu:.0f}%"
            )

            self.painel_ram.config(
                text=f"  RAM       {ram:.0f}%"
            )

            self.painel_disco.config(
                text=f"  DISCO     {disco:.0f}%"
            )

            if conectado:

                self.painel_network.config(
                    text="  NETWORK   ONLINE",
                    fg=GREEN
                )

            else:

                self.painel_network.config(
                    text="  NETWORK   OFFLINE",
                    fg="#ff5555"
                )

            self.painel_status.config(
                text="  STATUS    ONLINE",
                fg=GREEN
            )

        except Exception as erro:

            print(
                f"[MONITOR] Erro: {erro}"
            )

        self.root.after(
            1000,
            self.atualizar_sistema
        )

    # ========================================================
    # CORE
    # ========================================================

    def desenhar_core(self, evento=None):

        canvas = self.core_canvas

        canvas.delete(
            "core"
        )

        largura = canvas.winfo_width()
        altura = canvas.winfo_height()

        if largura < 100 or altura < 100:
            return

        cx = largura // 2
        cy = altura // 2 - 15

        estado = self.status.cget(
            "text"
        )

        if "OUVINDO" in estado:

            cor = CYAN
            intensidade = 12

        elif "PROCESSANDO" in estado:

            cor = "#ffd166"
            intensidade = 20

        elif "FALANDO" in estado:

            cor = "#b388ff"
            intensidade = 16

        else:

            cor = GREEN
            intensidade = 5

        pulso = (
            self.core_pulse
            * intensidade
            / 5
        )

        # ANÉIS

        for distancia in range(
            55,
            190,
            30
        ):

            canvas.create_oval(
                cx - distancia - pulso * 0.15,
                cy - distancia - pulso * 0.15,
                cx + distancia + pulso * 0.15,
                cy + distancia + pulso * 0.15,
                outline="#12303a",
                width=1,
                tags="core"
            )

        # ANEL PRINCIPAL

        canvas.create_oval(
            cx - 145 - pulso,
            cy - 145 - pulso,
            cx + 145 + pulso,
            cy + 145 + pulso,
            outline=cor,
            width=3,
            tags="core"
        )

        # MARCADORES

        import math

        for i in range(12):

            angulo = math.radians(
                i * 30 + self.core_pulse
            )

            x1 = (
                cx
                + math.cos(angulo)
                * 155
            )

            y1 = (
                cy
                + math.sin(angulo)
                * 155
            )

            x2 = (
                cx
                + math.cos(angulo)
                * 172
            )

            y2 = (
                cy
                + math.sin(angulo)
                * 172
            )

            canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill=cor,
                width=2,
                tags="core"
            )

        # NÚCLEO

        tamanho = 70 + pulso

        canvas.create_oval(
            cx - tamanho,
            cy - tamanho,
            cx + tamanho,
            cy + tamanho,
            fill="#071822",
            outline=cor,
            width=3,
            tags="core"
        )

        # BRILHO

        brilho = 38 + pulso * 0.35

        canvas.create_oval(
            cx - brilho,
            cy - brilho,
            cx + brilho,
            cy + brilho,
            fill="#092b36",
            outline=cor,
            width=2,
            tags="core"
        )

        # SÍMBOLO

        canvas.create_text(
            cx,
            cy - 5,
            text="◈",
            font=("Segoe UI", 35, "bold"),
            fill=cor,
            tags="core"
        )

        canvas.create_text(
            cx,
            cy + 55,
            text="ORION",
            font=("Consolas", 18, "bold"),
            fill=WHITE,
            tags="core"
        )

        canvas.create_text(
            cx,
            cy + 80,
            text="AI SYSTEM CORE",
            font=("Consolas", 8, "bold"),
            fill=GRAY,
            tags="core"
        )

    def animar_core(self):

        self.core_pulse += (
            self.core_direction
        )

        if self.core_pulse >= 5:

            self.core_direction = -1

        elif self.core_pulse <= 0:

            self.core_direction = 1

        self.desenhar_core()

        self.root.after(
            50,
            self.animar_core
        )

    # ========================================================
    # ESTADO
    # ========================================================

    def definir_estado(self, estado):

        estados = {

            "standby": (
                "● STANDBY",
                GREEN,
                "ORION CORE // AGUARDANDO COMANDO"
            ),

            "ouvindo": (
                "● OUVINDO",
                CYAN,
                "ORION CORE // ESCUTANDO"
            ),

            "processando": (
                "● PROCESSANDO",
                "#ffd166",
                "ORION CORE // PROCESSANDO DADOS"
            ),

            "falando": (
                "● FALANDO",
                "#b388ff",
                "ORION CORE // TRANSMITINDO"
            ),
        }

        texto, cor, descricao = estados.get(
            estado,
            estados["standby"]
        )

        self.status.config(
            text=texto,
            fg=cor
        )

        self.estado_texto.config(
            text=descricao,
            fg=cor
        )

    # ========================================================
    # VOZ
    # ========================================================

    def consumir_eventos(self):
        """Somente a thread do Tk consome resultados dos trabalhadores."""
        if self.encerrando:
            return
        for _ in range(100):
            try:
                evento = self.eventos.get_nowait()
            except queue.Empty:
                break
            tipo, dados = evento
            if tipo == "escuta":
                sessao, texto, erro, comando = dados
                self.escuta_ativa = False
                if sessao == self.sessao_voz and self.modo_voz:
                    if erro:
                        self.adicionar_mensagem("SISTEMA", erro)
                        self.desativar_voz()
                    elif not self.textos_pendentes:
                        self.receber_voz(texto, comando)
            elif tipo == "resposta":
                self.processamento_ativo = False
                resposta, erro = dados
                if erro:
                    self.finalizar_erro()
                else:
                    self.finalizar_resposta(resposta)
        if self.textos_pendentes and not self.escuta_ativa and not self.processamento_ativo:
            texto = self.textos_pendentes.pop(0)
            self.processamento_ativo = True
            self.definir_estado("processando")
            threading.Thread(target=self.processar_em_background,
                             args=(texto,), daemon=False).start()
        elif not self.textos_pendentes:
            self.escutar_voz()
        self._fila_after = self.root.after(50, self.consumir_eventos)

    def alternar_voz(self):
        if self.modo_voz:
            self.desativar_voz()
            return
        self.sessao_voz += 1
        self.cancelamento_voz = threading.Event()
        self.modo_voz = True
        self.botao_voz.config(text="VOZ ON", bg=CYAN, fg="#001018")
        self.adicionar_mensagem("SISTEMA", 'Modo de voz ativado. Diga "ORION" para chamar.')
        self.escutar_voz()

    def desativar_voz(self):
        self.modo_voz = False
        self.sessao_voz += 1
        self.cancelamento_voz.set()
        self.botao_voz.config(text="VOZ", bg=DARK_GRAY, fg=CYAN)
        if not self.processamento_ativo:
            self.definir_estado("standby")
        self.adicionar_mensagem("SISTEMA", "Modo de voz desativado.")

    def fechar(self):
        self.encerrando = True
        self.modo_voz = False
        self.sessao_voz += 1
        self.cancelamento_voz.set()
        self.textos_pendentes.clear()
        if self._fila_after is not None:
            self.root.after_cancel(self._fila_after)
        # Sem join: uma captura/requisição já iniciada termina sem acessar o Tk.
        self.root.destroy()

    def escutar_voz(self, comando=False):
        if (self.encerrando or not self.modo_voz or self.escuta_ativa
                or self.processamento_ativo or self.textos_pendentes):
            return
        self.escuta_ativa = True
        self.definir_estado("ouvindo")
        threading.Thread(target=self._ouvir_em_background,
                         args=(self.sessao_voz, self.cancelamento_voz, comando),
                         daemon=False).start()

    def _ouvir_em_background(self, sessao, cancelamento, comando):
        texto, erro = None, None
        try:
            texto = self.reconhecedor_voz.ouvir(cancelamento)
        except Exception:
            erro = "Falha ao ouvir. Verifique o microfone ou a conexão e reative a voz."
        self.eventos.put(("escuta", (sessao, texto, erro, comando)))

    def escutar_comando(self):
        self.escutar_voz(comando=True)

    def receber_voz(self, texto, comando=False):
        if not texto:
            return
        texto = texto.strip()
        sem_prefixo = re.sub(r"^orion\b[\s,:;!?.-]*", "", texto,
                            flags=re.IGNORECASE).strip()
        parada = sem_prefixo.lower().rstrip(".!?")
        if parada in ("parar", "pare", "pode parar", "volta a dormir",
                      "volte a dormir", "desativar voz"):
            self.desativar_voz()
            return
        if not comando:
            if not re.match(r"^orion\b", texto, flags=re.IGNORECASE):
                return
            texto = sem_prefixo
            if not texto:
                self.adicionar_mensagem("SISTEMA", "Estou ouvindo...")
                self.escutar_comando()
                return
        self.processar_voz(texto)

    def processar_voz(self, texto):
        self.adicionar_mensagem("VOCE", texto)
        self.definir_estado("processando")
        self.processar(texto)

    # ========================================================
    # CHAT
    # ========================================================
    def adicionar_mensagem(
        self,
        autor,
        mensagem
    ):

        print(
            f"[{autor}] {mensagem}"
        )

        def atualizar_chat():

            try:

                self.chat.config(
                    state="normal"
                )

                autor_normalizado = (
                    autor.upper()
                )

                if autor_normalizado in (
                    "VOCE",
                    "VOCÊ",
                    "USER"
                ):

                    nome_tag = "user_name"
                    msg_tag = "user_msg"
                    nome = "VOCÊ  //  USER"

                elif autor_normalizado == "ORION":

                    nome_tag = "orion_name"
                    msg_tag = "orion_msg"
                    nome = "ORION  //  AI CORE"

                else:

                    nome_tag = "system_name"
                    msg_tag = "system_msg"

                    nome = (
                        f"{autor_normalizado}"
                        "  //  SYSTEM"
                    )

                self.chat.insert(
                    "end",
                    f"{nome}\n",
                    nome_tag
                )

                self.chat.insert(
                    "end",
                    f"{mensagem}\n",
                    msg_tag
                )

                self.chat.insert(
                    "end",
                    "\n"
                )

                self.chat.see(
                    "end"
                )

                self.chat.config(
                    state="disabled"
                )

            except Exception as erro:

                print(
                    f"[CHAT] Erro: {erro}"
                )

        self.root.after(
            0,
            atualizar_chat
        )

    # ========================================================
    # ENVIAR
    # ========================================================

    def enviar(self, evento=None):

        texto = self.entrada.get().strip()

        if not texto:
            return

        self.entrada.delete(
            0,
            "end"
        )

        self.adicionar_mensagem(
            "VOCE",
            texto
        )

        self.definir_estado(
            "processando"
        )

        self.botao.config(
            state="disabled",
            text="..."
        )

        self.processar(
            texto
        )

    # ========================================================
    # PROCESSAR
    # ========================================================

    def processar(self, texto):
        if self.encerrando:
            return
        # Invalida uma escuta em andamento ao receber também um comando digitado.
        self.sessao_voz += 1
        self.cancelamento_voz.set()
        self.cancelamento_voz = threading.Event()
        self.textos_pendentes.append(texto)
        self.botao.config(state="disabled", text="...")

    def processar_em_background(self, texto):
        try:
            # O callback só retorna depois de main concluir também falar().
            resposta = self.responder(texto) or "Nao consegui responder."
            self.eventos.put(("resposta", (resposta, False)))
        except Exception:
            self.eventos.put(("resposta", (None, True)))

    def finalizar_resposta(self, resposta):
        self.definir_estado("standby")
        self.adicionar_mensagem("ORION", resposta)
        self.botao.config(state="normal", text="ENVIAR")
        self.entrada.focus()

    def finalizar_erro(self):
        self.definir_estado("standby")
        self.adicionar_mensagem("SISTEMA", "Não consegui processar o comando.")
        self.botao.config(state="normal", text="ENVIAR")
        self.entrada.focus()
    # ========================================================
    # INICIAR
    # ========================================================

    def iniciar(self):

        self.entrada.focus()

        self.root.mainloop()
