# ORION 2.0

Assistente desktop em Python com Tkinter, Groq, memória e tarefas em JSON.

## Windows 10

1. Instale Python **3.12 de 64 bits** do python.org com Tcl/Tk e pip. Na instalação, marque a opção de adicionar Python ao PATH.
2. No PowerShell, na raiz deste repositório:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

   Não é necessário ativar o ambiente virtual nem alterar a política do PowerShell.
3. Configure a chave Groq para esta sessão (substitua o valor localmente; não compartilhe sua chave):

   ```powershell
   $env:GROQ_API_KEY = "sua-chave-groq"
   ```

   Alternativamente, configure `GROQ_API_KEY` em um arquivo `.env` local na pasta `orion 2`. Nunca versione esse arquivo. A chave é necessária para a inicialização atual de `OrionIA`.
4. Execute:

   ```powershell
   Set-Location '.\orion 2'
   ..\.venv\Scripts\python.exe main.py
   ```

   Execute sempre na mesma pasta para reutilizar memória e tarefas. O aplicativo grava os JSON nessa pasta; os arquivos pessoais existentes são preservados pela instalação.

## Voz

- **Saída principal:** `edge-tts` com `pt-BR-AntonioNeural`, velocidade `-8%` e tom `-5Hz`: voz masculina brasileira, um pouco mais lenta e grave. O texto é enviado ao serviço online de voz da Microsoft; não exige chave ElevenLabs. O MP3 temporário é reproduzido por `pygame` e removido ao terminar.
- **Fallback automático:** falha de rede, timeout, dependência ausente ou erro de reprodução aciona `pyttsx3`/SAPI5 offline. O fallback prefere uma voz brasileira masculina instalada. Instale uma voz portuguesa nas configurações de fala do Windows; nem todas as vozes do Windows ficam disponíveis no SAPI5. Se a síntese offline também falhar, a resposta permanece no chat.
- **Entrada:** clique em **VOZ** e diga “ORION” seguido do comando, por exemplo “Orion, listar tarefas”. O módulo `voz_entrada` usa SpeechRecognition/PyAudio com o microfone padrão. O reconhecimento Google exige Internet e envia o áudio capturado ao serviço; não exige chave Groq para transcrever. A escuta limita cada captura a 5 segundos de fala e 1 segundo de espera, com timeout de rede de 5 segundos. Silêncio e fala incompreensível são ignorados.
- Para encerrar a escuta, clique novamente em **VOZ** ou diga “Orion, parar”. A interface descarta resultados cancelados; uma captura/requisição já iniciada pode levar alguns segundos para retornar.
- Sem microfone, PyAudio ou conexão, a interface desativa a escuta após a falha e mantém o chat. Sem saída de áudio ou motor de síntese, a resposta permanece disponível por texto. O aplicativo não abre dispositivos de áudio durante a inicialização.
- No Windows 10, habilite o acesso de aplicativos da área de trabalho ao microfone em **Configurações → Privacidade → Microfone**.
- `ELEVENLABS_API_KEY` e os parâmetros de voz ElevenLabs legados em `config.py` não são usados pelo novo backend local; não é necessário adquirir outra chave.

## Arquitetura

`main.Orion.processar` mantém o roteamento de intenções, tarefas, comandos e Groq e chama `falar` na thread de processamento. `falar` serializa geração e reprodução online e offline com um único bloqueio. A chamada permanece síncrona na thread de trabalho existente da interface, mantendo o Tkinter livre e impedindo que a escuta reinicie enquanto a fala não terminou. O motor offline é criado/usado/encerrado na mesma thread. O download tem limite total de 20 segundos; a reprodução, de 180 segundos. O player é encerrado antes de tentar o fallback e os arquivos temporários são removidos também em falhas.

`interface.OrionInterface` cria `ReconhecedorVoz` sem acessar hardware. Ao ativar voz, chama `ouvir(evento_de_cancelamento)` em background e recebe texto/erros pela fila existente. Nenhum dos novos módulos acessa widgets Tk. Memória, tarefas, intenções e cliente Groq continuam nas implementações existentes.

## Testes sem dispositivos

Na raiz do repositório:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os testes usam motores de síntese, microfone, serviço de transcrição e interface gráfica simulados. Exercitam parâmetros da voz neural, escolha de voz offline, fallback, timeouts, limpeza de arquivos/player, serialização de chamadas simultâneas, agendamento da interface durante processamento, falhas de dispositivos/dependências/rede, silêncio, cancelamento, integração de inicialização, intenções de tarefas, persistência em arquivos temporários e encaminhamento à IA. Não enviam áudio, não chamam a API Groq nem alteram os JSON pessoais. Um teste de integração usa chave fictícia apenas para construir o cliente, sem requisições.

A execução real de áudio no Windows e a qualidade da voz precisam ser verificadas no computador de destino. A interface exige sessão gráfica: tolerar ausência de áudio não elimina a necessidade de uma tela para o Tkinter.

Os utilitários opcionais `calibrar_voz.py` e `gravar_teste.py` são independentes do fluxo principal e suas dependências não estão incluídas em `requirements.txt`. A calibração SpeechBrain não é necessária para o reconhecimento implementado.

## Ajustar e testar a identidade vocal

As opções ficam em `orion 2/config.py`. As variáveis abaixo podem ser definidas no PowerShell ou no `.env` e são lidas ao iniciar o aplicativo:

| Variável | Padrão | Significado |
| --- | --- | --- |
| `ORION_TTS_BACKEND` | `edge` | `edge` com fallback automático ou `offline` para apenas SAPI |
| `ORION_TTS_VOICE` | `pt-BR-AntonioNeural` | Nome da voz online |
| `ORION_TTS_RATE` | `-8%` | Velocidade relativa; inclua sinal e `%` |
| `ORION_TTS_PITCH` | `-5Hz` | Tom relativo; inclua sinal e `Hz` |
| `ORION_TTS_OFFLINE_VOICE` | vazio | ID de uma voz SAPI instalada; vazio seleciona português automaticamente |

`TTS_OFFLINE_RATE` em `config.py` controla a velocidade offline (165 palavras/minuto). O tom configurado para Edge não é aplicado ao SAPI: `pyttsx3` não oferece um controle portátil de pitch. A voz offline pode soar diferente da neural.

Para ouvir somente a nova voz, sem iniciar a interface nem fazer uma chamada Groq, execute a partir da raiz do repositório:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:ORION_TTS_BACKEND = "edge"
$env:ORION_TTS_VOICE = "pt-BR-AntonioNeural"
$env:ORION_TTS_RATE = "-8%"
$env:ORION_TTS_PITCH = "-5Hz"
cd "orion 2"
..\.venv\Scripts\python.exe -c "from voz import falar; print(falar('Boa noite. Todos os sistemas estão prontos. Como posso ajudar?'))"
```

`True` significa que a síntese principal **ou** o fallback terminou. Observe o aviso “Voz online indisponível” para distinguir o uso do fallback. Para testar apenas o offline, repita com `$env:ORION_TTS_BACKEND = "offline"`. Para verificar a troca automática, use `edge`, desconecte a Internet e repita: após a falha/timeout, deve tocar a voz local instalada. Sem dispositivo de áudio, a chamada pode retornar `False`, mantendo o aplicativo utilizável por texto.

Para testar na interface, execute `..\.venv\Scripts\python.exe main.py`, envie um comando por texto e confirme que a janela continua aceitando eventos durante a fala. Os parâmetros são um ponto de partida para uma identidade própria; ajuste-os conforme a qualidade percebida no seu equipamento.
