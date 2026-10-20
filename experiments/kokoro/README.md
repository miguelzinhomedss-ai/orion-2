# Experimento Kokoro: pm_alex e pm_santa

Comparação independente de duas vozes masculinas portuguesas do Kokoro-82M. O ORION continua usando AntonioNeural e seu fallback pyttsx3. Nenhum módulo do aplicativo, configuração de voz ou dependência principal é alterado por este experimento. Não há integração automática ao botão VOZ: os scripts apenas geram arquivos para avaliação.

## Escolha e fontes

Usamos `kokoro-onnx==0.6.1`, implementação comunitária do Kokoro com ONNX Runtime CPU, sem PyTorch, CUDA, conta ou API paga. A licença da implementação é MIT; a licença informada para o modelo Kokoro é Apache 2.0. O projeto original é hexgrad/Kokoro-82M; o export ONNX vem das releases do mantenedor de kokoro-onnx. Não se trata de um cliente de API ou clonagem de voz de ator.

Fontes consultadas:

- [Projeto, documentação, requisitos e licenças](https://github.com/thewh1teagle/kokoro-onnx)
- [Metadados da versão 0.6.1 no PyPI](https://pypi.org/project/kokoro-onnx/0.6.1/)
- [Modelo original Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
- [Export INT8, release model-files-v1.0](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0)
- [Pacote de vozes, release model-files-v1.1](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1)

As duas vozes foram encontradas no pacote e usadas em uma execução real. O idioma passado ao fonemizador é `pt-br`. A qualidade, pronúncia e preferência entre Alex e Santa precisam de avaliação auditiva; quantização pode alterar a qualidade em relação ao modelo completo.

## Tamanho e impacto antes de instalar

| Item | Download |
| --- | ---: |
| `kokoro-v1.0.int8.onnx` | 92.361.271 bytes (~92,4 MB) |
| `voices-v1.0.bin` | 28.214.398 bytes (~28,2 MB) |
| Total de modelo e vozes | ~120,6 MB |
| Bibliotecas Windows x64 / Python 3.12 verificadas | ~39,4 MB adicionais |

O modelo completo FP32 teria ~325,5 MB e **não é baixado** pelo script. O pacote `.bin` inclui outras vozes, mas somente `pm_alex` e `pm_santa` são geradas no teste. Reserve pelo menos 1 GB livre para ambiente, caches, modelos e resultados; o tamanho instalado difere do tamanho baixado. WAV mono PCM16 em 24 kHz ocupa cerca de 48 KB por segundo de fala.

Para o i3-9100F, RX 470 4 GB e 16 GB de RAM: use Python 3.12 x64 e CPU. A RX 470 não é utilizada; não instale `onnxruntime-gpu`, CUDA ou PyTorch para este teste. O padrão é 2 threads de inferência e 1 de coordenação, para deixar margem ao Windows. Compare `--threads 1`, `2` e `4` se desejar. Não há garantia de tempo real ou de latência no seu hardware. O processo ocupa memória além do tamanho do modelo em disco; feche programas pesados para comparar com consistência.

Após instalar bibliotecas e baixar os dois arquivos, a síntese funciona localmente sem Internet. A frase não é enviada a um serviço externo. Os scripts não tocam microfone, não reproduzem áudio e não acessam Groq.

## Windows 10: ambiente separado

Use PowerShell **na raiz do repositório**, com Python 3.12 de 64 bits instalado. Não ative nem reutilize o `.venv` principal do ORION:

```powershell
py -3.12 -m venv .venv-kokoro
.\.venv-kokoro\Scripts\python.exe -m pip install -r experiments\kokoro\requirements.txt
.\.venv-kokoro\Scripts\python.exe -m pip check
```

A resolução das dependências foi verificada com pacotes binários para Python 3.12 / Windows x64, mas a execução real nesta tarefa ocorreu em Linux. `espeakng-loader` fornece a biblioteca e os dados de fonemização; não é necessário preparar manualmente o eSpeak no fluxo esperado. Se uma DLL nativa falhar no Windows, confira a arquitetura 64 bits e o Microsoft Visual C++ Redistributable x64 conforme a documentação do ONNX Runtime, sem instalar bibliotecas no ambiente principal.

### Baixar explicitamente os modelos

**Este comando baixa ~120,6 MB.** Nenhum script de comparação baixa modelos por conta própria:

```powershell
.\.venv-kokoro\Scripts\python.exe experiments\kokoro\baixar_modelos.py --destino experiments\kokoro\modelos
```

O download usa URLs HTTPS de releases fixas, valida os tamanhos e registra SHA-256 local e origem em `downloads.json`. Esses hashes são registros locais, não assinaturas publicadas pelo autor. Não são usados pickle ou carregamento de código remoto. O script recusa sobrescrever arquivos existentes; após download parcial, escolha outra pasta ou remova somente os arquivos incompletos deste experimento antes de repetir.

### Gerar a mesma frase nas duas vozes

```powershell
.\.venv-kokoro\Scripts\python.exe experiments\kokoro\comparar_vozes.py --modelo experiments\kokoro\modelos\kokoro-v1.0.int8.onnx --vozes experiments\kokoro\modelos\voices-v1.0.bin
```

O script gera uma pasta nova em `experiments/kokoro/resultados/comparacao-.../` com:

- `pm_alex.wav`
- `pm_santa.wav`
- `comparacao.json`: frase, velocidade, threads, taxa de amostragem, duração dos áudios, tempo de carga e geração de cada voz.

Abra cada WAV pelo Explorador de Arquivos para ouvir em sequência. A velocidade padrão é `0.95`, um pouco mais lenta. Para outra frase ou velocidade:

```powershell
.\.venv-kokoro\Scripts\python.exe experiments\kokoro\comparar_vozes.py --modelo experiments\kokoro\modelos\kokoro-v1.0.int8.onnx --vozes experiments\kokoro\modelos\voices-v1.0.bin --texto "Boa noite. Como posso ajudar?" --velocidade 0.92 --threads 2
```

A pasta de cada execução é exclusiva; resultados anteriores são preservados. Se uma voz falhar, o processo termina com erro e registra `status: falhou`, preservando o resultado parcial sem anunciar sucesso. O JSON contém a frase: mantenha resultados locais caso use texto privado. Modelos, resultados e o ambiente padrão do experimento estão no `.gitignore`.

O campo `rtf` é o tempo de geração dividido pela duração do áudio: abaixo de 1 indica geração mais rápida que a duração da fala, sem incluir carga inicial. Alex é gerado primeiro; Santa pode aproveitar aquecimento do runtime. Compare também execuções repetidas; o teste é para avaliação prática, não um benchmark rigoroso.

## Testes e validação realizados

Teste isolado, sem modelo, rede, dispositivos ou dependências Kokoro:

```powershell
py -3.12 -m unittest discover -s experiments/kokoro/tests -p test_kokoro.py -v
```

Os 10 testes iniciais usam mocks para: duas vozes com frase idêntica, provider CPU, limites de parâmetros, arquivos ausentes, voz ausente, áudio inválido, resultados parciais, preservação de arquivos, download truncado e registro de hash. A suíte completa do ORION passou com **36 testes**.

Também houve síntese real com Python 3.12.14, Kokoro ONNX INT8 e 2 threads na máquina em nuvem:

| Voz | Duração do WAV | Tempo de geração |
| --- | ---: | ---: |
| pm_alex | 5,78 s | 2,65 s |
| pm_santa | 5,89 s | 2,62 s |

Ambos os WAVs foram verificados como mono, 24 kHz, com amostras finitas e sinal não silencioso. Isso confirma geração de áudio, não uma avaliação auditiva da naturalidade. Esses tempos **não são previsão para o i3-9100F**. Nenhuma janela Windows ou saída física de áudio foi usada na validação.

Este experimento é distribuído na branch `feat/kokoro-benchmark`, sem merge com `main`, publicação ou deploy do aplicativo.

## Desempenho local da pm_alex: frase curta e resposta maior

O script `testar_desempenho.py` usa exclusivamente `pm_alex`, CPU e os modelos locais já preparados. Não instala nada, não baixa modelos, não reproduz som e não altera o ORION. Duas rodadas são executadas por padrão: curta, maior, curta, maior. O modelo fica carregado entre elas. Não há aquecimento oculto: a primeira frase inclui o custo de inicialização tardia do fonemizador/inferência. A resposta maior tem aproximadamente 70 palavras.

Para obter os arquivos no Windows sem alterar a `main`, na raiz da sua cópia local execute:

```powershell
git fetch origin
git switch --track origin/feat/kokoro-benchmark
```

Se a branch local já existir, use `git switch feat/kokoro-benchmark`. Preserve alterações locais antes de trocar de branch; não use `reset --hard` nem descarte arquivos para prosseguir. Depois confira os arquivos com `Test-Path` conforme abaixo.

No PowerShell, **começando na raiz do repositório** (não entre em `orion 2`):

```powershell
# Deve retornar True antes de prosseguir.
Test-Path .\experiments\kokoro\testar_desempenho.py

# Somente se ainda não existir o ambiente separado:
if (-not (Test-Path .\.venv-kokoro\Scripts\python.exe)) {
    py -3.12 -m venv .venv-kokoro
    if ($LASTEXITCODE -ne 0) { throw "Não foi possível criar o ambiente Python 3.12." }
}
.\.venv-kokoro\Scripts\python.exe -m pip install -r .\experiments\kokoro\requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar as dependências do experimento." }
.\.venv-kokoro\Scripts\python.exe -m pip check
if ($LASTEXITCODE -ne 0) { throw "Há conflito de dependências no ambiente separado." }
```

Se **ainda não baixou** os modelos, o comando abaixo baixa os ~120,6 MB descritos anteriormente. Se os dois arquivos já existem, pule este comando; o downloader protege arquivos existentes contra sobrescrita. Não copie os modelos para dentro da pasta do ambiente virtual.

```powershell
.\.venv-kokoro\Scripts\python.exe .\experiments\kokoro\baixar_modelos.py --destino .\experiments\kokoro\modelos
```

Execute o teste (uma linha):

```powershell
.\.venv-kokoro\Scripts\python.exe .\experiments\kokoro\testar_desempenho.py --modelo .\experiments\kokoro\modelos\kokoro-v1.0.int8.onnx --vozes .\experiments\kokoro\modelos\voices-v1.0.bin --threads 2 --repeticoes 2
```

Interpretação da saída:

- **Bibliotecas:** tempo de importação das dependências opcionais.
- **Carga do modelo/vozes:** abertura dos arquivos e preparação da sessão, incluindo leitura dos dados. No HD, o cache de arquivos do Windows pode reduzir esse tempo nas próximas execuções; não é uma medição de disco isolada.
- **Gerar(s):** tempo para produzir o áudio completo em memória; inclui fonemização. Não inclui gravação do WAV ou reprodução. Este script não mede streaming ou tempo até o primeiro fragmento de áudio.
- **Gravar(s):** tempo para gravar/fechar o WAV. O Windows pode manter dados em cache, então não representa escrita física sincronizada no HD.
- **Áudio(s):** duração da fala gerada, não o tempo de processamento.
- **RTF:** geração dividida pela duração da fala. Exemplo: 6 segundos para produzir 12 segundos de áudio resulta em RTF 0,5. Abaixo de 1 é mais rápido que a duração da fala; acima de 1 é mais lento.

O script informa uma pasta nova `experiments/kokoro/resultados/desempenho-alex-.../`. Ela contém os quatro WAVs e `desempenho.json`, com medidas individuais, medianas de geração (incluindo a primeira execução), textos, configurações e identificação do sistema/Python. As medições não incluem o tempo de inicialização do próprio interpretador. Nenhum resultado anterior é sobrescrito. Em falha após o início das gerações, o JSON fica marcado como `falhou`, com resultados parciais.

No i3-9100F, comece com 2 threads e feche programas pesados. A RX 470 não será usada. Para verificar se os 4 núcleos ajudam, repita o comando trocando apenas `--threads 2` por `--threads 4`. Não compare com downloads ou atualizações em andamento. Registre tanto a primeira execução quanto as repetições: o HD, o cache do Windows e o aquecimento do runtime influenciam os resultados. Os tempos da nuvem não são previsão para o seu computador.

Para executar somente os testes com mocks, sem baixar modelos:

```powershell
py -3.12 -m unittest discover -s experiments/kokoro/tests -p test_kokoro.py -v
```

O teste de desempenho foi exercitado com modelos reais em CPU na nuvem; os testes automatizados também verificam voz, frases, número de execuções, configuração CPU, parâmetros inválidos e registro de falhas parciais. A suíte completa passou com 40 testes. A execução no seu Windows continua sendo necessária para medir seu hardware.
