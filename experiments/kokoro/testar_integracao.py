"""Executa o pipeline real de voz do ORION sem abrir GUI ou chamar Groq."""
import argparse
import logging
from pathlib import Path
import sys
import time


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--texto', default=(
        'Boa noite. Estou pronto para ajudar. Podemos organizar suas tarefas e analisar '
        'as informações com calma. Diga qual assunto deseja explorar primeiro.'))
    parser.add_argument('--repeticoes', type=int, default=2)
    args = parser.parse_args(argv)
    if not args.texto.strip() or not 1 <= args.repeticoes <= 10:
        parser.error('Informe texto não vazio e 1 a 10 repetições.')
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'orion 2'))
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    from voz import falar, cancelar_fala
    import config
    print(f'Backend configurado: {config.TTS_BACKEND}. Observe avisos de fallback.', flush=True)
    try:
        for rodada in range(1, args.repeticoes + 1):
            print(f'Rodada {rodada}: iniciando falar().', flush=True)
            inicio = time.perf_counter()
            sucesso = falar(args.texto)
            print(f'Tempo total (geração + reprodução): {time.perf_counter() - inicio:.2f} s. '
                  f'Sucesso: {sucesso}', flush=True)
            if not sucesso:
                return 1
    except KeyboardInterrupt:
        cancelar_fala()
        return 130
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
