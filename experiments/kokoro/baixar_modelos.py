"""Download explícito de ~120,6 MB, de releases fixas do kokoro-onnx via HTTPS."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import urllib.request

ARQUIVOS = (
    ('kokoro-v1.0.int8.onnx', 92361271,
     'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx'),
    ('voices-v1.0.bin', 28214398,
     'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin'),
)


def baixar(destino):
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    registros = []
    for nome, tamanho, url in ARQUIVOS:
        alvo = destino / nome
        if alvo.exists():
            raise FileExistsError(f'{alvo} já existe; use uma nova pasta para não sobrescrever arquivos.')
        temporario = None
        try:
            digest = hashlib.sha256()
            recebido = 0
            # A verificação TLS padrão permanece habilitada.
            with urllib.request.urlopen(url, timeout=60) as resposta, \
                 tempfile.NamedTemporaryFile(dir=destino, delete=False) as arquivo:
                temporario = Path(arquivo.name)
                while bloco := resposta.read(1024 * 1024):
                    recebido += len(bloco)
                    if recebido > tamanho:
                        raise ValueError(f'Tamanho inesperado para {nome}; download interrompido.')
                    arquivo.write(bloco)
                    digest.update(bloco)
            if recebido != tamanho:
                raise ValueError(f'Download incompleto: {nome} ({recebido}/{tamanho} bytes).')
            # 'xb' evita sobrescrita mesmo se outro processo criar o destino.
            with alvo.open('xb') as saida, temporario.open('rb') as entrada:
                while bloco := entrada.read(1024 * 1024):
                    saida.write(bloco)
            registros.append({'arquivo': nome, 'bytes': recebido, 'url': url,
                              'sha256_local': digest.hexdigest()})
        finally:
            if temporario is not None:
                temporario.unlink(missing_ok=True)
    # Hashes registram a integridade local; não são assinaturas do autor.
    with (destino / 'downloads.json').open('x', encoding='utf-8') as arquivo:
        json.dump(registros, arquivo, indent=2)
    return registros


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destino', type=Path, required=True)
    args = parser.parse_args(argv)
    print('Download: modelo INT8 92,4 MB + vozes 28,2 MB = 120,6 MB, fora das dependências.', flush=True)
    try:
        baixar(args.destino)
    except Exception as erro:
        parser.exit(1, f'Falha no download: {erro}\n')
    print('Arquivos locais preparados. Nenhum modelo foi carregado ou executado.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
