# ORION: Kokoro pm_alex persistente e progressivo

Nesta integração, `ORION_TTS_BACKEND=kokoro` é o padrão. A síntese usa `pm_alex`, modelo INT8 e CPU com 2 threads. AntonioNeural (`edge-tts`) é a segunda opção; `pyttsx3`/SAPI é a última alternativa offline. Se os arquivos ou bibliotecas Kokoro faltarem, a inicialização gráfica continua funcionando e o fallback ocorre na hora de falar. Nenhum modelo é baixado automaticamente.

## O que mudou

- `orion 2/voz_kokoro.py` carrega ONNX Runtime na primeira solicitação e guarda a sessão para todo o processo. Voz e velocidade podem mudar sem recarregar o modelo; caminho dos modelos ou número de threads diferente cria outra sessão. Reiniciar o ORION exige carregar novamente. O modelo permanece em RAM enquanto o processo estiver aberto.
- A primeira parte tem alvo de até 80 caracteres e as demais até 160. A divisão prefere frases e vírgulas, preservando palavras inteiras (uma palavra excepcionalmente longa pode ultrapassar o alvo). Isso reduz o trabalho necessário antes de começar a falar, sem prometer redução do custo total da síntese. Frases muito pequenas podem alterar a prosódia; avalie ouvindo no seu computador.
- Um produtor gera um trecho à frente enquanto o player reproduz o atual. Há uma única inferência ativa e, no máximo, um trecho antecipado. WAVs circulam em memória; não são escritos no HD. Apenas Edge ainda utiliza um MP3 temporário, removido ao terminar.
- Um bloqueio abrange todos os backends: não há duas falas simultâneas. O executor de geração encerra ao fim da resposta; não fica fazendo polling quando o ORION está ocioso. O ONNX usa `allow_spinning=0` para evitar threads ocupadas aguardando trabalho. A RAM do modelo persistente é intencional.
- O Tkinter continua com sua fila e threads existentes. O botão **PARAR FALA** apenas sinaliza um evento, sem manipular dispositivos na thread gráfica. Fechar a janela também cancela a fala. Memória, tarefas, comandos, reconhecimento de voz e cliente Groq não foram substituídos.

## Cancelamento e falhas

**PARAR FALA** interrompe a reprodução corrente e descarta os próximos trechos. Se pressionado durante a resposta Groq, suprime a fala dessa resposta quando ela estiver pronta; não cancela a requisição Groq. O texto continua disponível no chat após o callback retornar. O botão não desativa o modo de escuta: use **VOZ** para isso.

Uma chamada nativa ONNX já iniciada não pode ser encerrada à força com segurança. Ela termina em background e o áudio é descartado. Enquanto isso, o player já parou e a janela continua responsiva; o worker precisa esperar a inferência encerrar antes de liberar completamente os buffers e aceitar a próxima resposta. O mesmo vale para uma operação nativa de dispositivo que demore a retornar. Cancelamento não dispara fallback. Na saída, buffers e player são liberados, e o pyttsx3 é parado/finalizado na mesma thread em que foi criado.

Se Kokoro falhar, Edge recebe somente os trechos ainda não concluídos. Se a reprodução falhar no meio do trecho atual, esse trecho pode ser repetido; os anteriores não. Se Edge falhar, o pyttsx3 tenta o mesmo texto restante. Se todos falharem, o chat continua. Edge envia o texto ao serviço Microsoft e exige Internet; Kokoro e pyttsx3 são locais. Modelos ausentes podem, portanto, levar a envio do texto pelo fallback online. Para impedir isso, escolha explicitamente `pyttsx3`.

O pyttsx3 usa um loop externo cooperativo na thread de trabalho, permitindo verificar cancelamento e um limite de 180 segundos. Nenhum motor deve ser chamado diretamente na thread Tk; a interface já chama `Orion.processar` em background.

## Instalação Windows 10 / Python 3.12 x64

Os arquivos desta integração precisam estar na sua cópia local. A integração está na branch `feat/kokoro-integracao` do GitHub. O envio foi solicitado explicitamente; não há merge com `main` ou deploy. Para obter os arquivos no Windows, na raiz da cópia local execute `git fetch origin` e `git switch --track origin/feat/kokoro-integracao` (ou `git switch feat/kokoro-integracao` se a branch local já existir). Preserve alterações locais antes de trocar de branch.

Comece no PowerShell na **raiz do repositório**. Crie um ambiente **novo**, sem alterar `.venv` ou `.venv-kokoro`:

```powershell
py -3.12 -m venv .venv-orion-kokoro
.\.venv-orion-kokoro\Scripts\python.exe -m pip install -r .\requirements-kokoro.txt
.\.venv-orion-kokoro\Scripts\python.exe -m pip check
```

O requirements adicional combina as dependências do ORION e do experimento, sem alterar `requirements.txt`. A instalação duplica bibliotecas no ambiente novo (dezenas de MB de download, mais espaço instalado/cache), mas não exige baixar novamente modelos existentes. Reserva recomendada: pelo menos 1 GB livre. Não instala PyTorch/CUDA, nem usa a RX 470.

Reutilize os modelos do experimento em `experiments/kokoro/modelos/`. Caso estejam em outro local, configure os caminhos abaixo. **Somente se ainda não tiver os arquivos**, o download explícito tem ~120,6 MB: modelo INT8 de 92,4 MB + vozes de 28,2 MB; não baixa o modelo FP32 de 325,5 MB.

```powershell
# Execute apenas se ainda não tiver os dois modelos locais:
.\.venv-orion-kokoro\Scripts\python.exe .\experiments\kokoro\baixar_modelos.py --destino .\experiments\kokoro\modelos
```

Não execute esse downloader sobre arquivos existentes. Ele recusa sobrescrita.

Configuração padrão, opcionalmente explícita para esta sessão do PowerShell:

```powershell
$env:ORION_TTS_BACKEND = "kokoro"
$env:ORION_KOKORO_VOICE = "pm_alex"
$env:ORION_KOKORO_THREADS = "2"
$env:ORION_KOKORO_SPEED = "0.95"

# Só se os modelos estiverem em outra pasta (substitua os caminhos):
# $env:ORION_KOKORO_MODEL = "D:\Modelos\kokoro-v1.0.int8.onnx"
# $env:ORION_KOKORO_VOICES = "D:\Modelos\voices-v1.0.bin"
```

Para o aplicativo, mantenha sua chave Groq existente no ambiente ou `.env` local (não a compartilhe). Partindo da raiz:

```powershell
Set-Location '.\orion 2'
..\.venv-orion-kokoro\Scripts\python.exe main.py
```

O diretório de trabalho mantém a localização usual dos seus JSON pessoais; a instalação não os sobrescreve. Faça seus testes de tarefas conscientemente, pois comandos normais do aplicativo continuam salvando alterações como antes.

Para forçar outra voz/backend, defina **antes de iniciar**:

```powershell
$env:ORION_TTS_BACKEND = "edge"       # AntonioNeural, com fallback pyttsx3
# ou:
$env:ORION_TTS_BACKEND = "pyttsx3"    # Apenas offline; "offline" também é aceito
```

AntonioNeural continua configurado por `ORION_TTS_VOICE`, `ORION_TTS_RATE` e `ORION_TTS_PITCH`. Kokoro usa `ORION_KOKORO_VOICE`, `ORION_KOKORO_SPEED` e `ORION_KOKORO_THREADS`. Os limites de caracteres estão em `KOKORO_FIRST_CHARS` e `KOKORO_CHUNK_CHARS`, em `config.py`. Alterações de variáveis são lidas ao reiniciar o processo. Diminuir trechos pode antecipar a primeira fala, mas aumentar pausas e reduzir naturalidade. Não mude a velocidade para mascarar medições: use a mesma configuração ao comparar.

## Medir o tempo até a primeira fala

Na raiz do repositório, sem abrir GUI nem chamar Groq:

```powershell
$env:ORION_TTS_BACKEND = "kokoro"
.\.venv-orion-kokoro\Scripts\python.exe .\experiments\kokoro\testar_integracao.py --repeticoes 2
```

O script **reproduz áudio real**. Procure estas linhas:

- `Kokoro: primeiro trecho pronto em ... s`: tempo desde o início do pipeline Kokoro até o primeiro WAV em memória. Inclui importações e carga na primeira rodada.
- `TTS: primeira reprodução iniciada em ... s desde falar()`: tempo até o retorno de `mixer.music.play()`, incluindo a preparação do player. É uma aproximação do início da fala; não mede a latência acústica do alto-falante/driver.
- `Tempo total (geração + reprodução)`: termina depois de toda a fala; não é a mesma métrica de latência inicial ou de geração pura do benchmark anterior.

A primeira rodada carrega o modelo. A segunda reutiliza a mesma instância; o custo de carga do HD fica fora das respostas seguintes. Observe avisos de fallback: não compare um resultado Edge com Kokoro. Estes tempos começam em `falar()` e **não incluem** a espera pelo Groq. Para a experiência completa da interface, meça também o intervalo entre enviar a mensagem e ouvir a primeira palavra, que inclui o tempo de resposta da IA.

Para comparar uma resposta maior:

```powershell
.\.venv-orion-kokoro\Scripts\python.exe .\experiments\kokoro\testar_integracao.py --repeticoes 2 --texto "Boa noite. Analisei as informações disponíveis e preparei um resumo para você. Podemos começar pelas tarefas mais importantes e depois organizar os próximos passos. Se surgir alguma dúvida, explicarei cada etapa com calma e clareza. Meu objetivo é ajudar você a tomar decisões com segurança, sem perder tempo com detalhes desnecessários. Quando estiver pronto, diga qual assunto deseja explorar primeiro."
```

Os resultados enviados pelo usuário (1,77 s para frase curta aquecida; 14,24 s para gerar 22,59 s de áudio maior) mediam a geração completa. A nova divisão busca reduzir a espera inicial, não promete tornar toda a geração proporcionalmente mais rápida. Pode haver pequenas pausas entre trechos se a CPU não gerar o próximo a tempo. Comece com 2 threads; teste 4 em execução separada se necessário. Não há medição nova no i3-9100F nesta tarefa.

## Validação

```powershell
# Na raiz, no ambiente integrado:
.\.venv-orion-kokoro\Scripts\python.exe -m unittest discover -s tests -v
```

56 testes passaram na máquina de desenvolvimento, sem áudio físico, incluindo sessão única, CPU, divisão, prefetch limitado, liberação de buffers, cancelamento antes e durante geração/reprodução, download Edge cancelado, parada pyttsx3, fallback parcial e preservação das integrações existentes. Também foi validado WAV em RAM com o player pygame e driver SDL simulado. A síntese real em CPU confirmou uma sessão compartilhada por duas respostas e geração progressiva de seis trechos para a resposta maior; a reprodução física foi substituída durante essa verificação. SAPI5 e janela Windows reais precisam de validação no seu computador.

Não houve download de modelos nesta integração: foram usados os arquivos já existentes da fase experimental. Modelos, áudios e credenciais não estão incluídos no código ou em commits desta tarefa.
