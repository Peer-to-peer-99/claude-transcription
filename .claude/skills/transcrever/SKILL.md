---
name: transcrever
description: Transcreve arquivos de áudio e vídeo localmente utilizando Faster-Whisper. Use quando o usuário solicitar a transcrição de MP3, WAV, M4A, MP4, MKV ou outros arquivos de mídia.
---

# Transcrição de áudio e vídeo

Você é responsável por executar a transcrição local do arquivo informado.

## Entrada

O caminho do arquivo será informado pelo usuário em:

$ARGUMENTS

## Regras

1. Verifique se o usuário informou um arquivo.
2. Resolva o caminho do arquivo.
3. Verifique se o arquivo existe.
4. Identifique o sistema operacional e o shell disponível.
5. Utilize exclusivamente o Python do ambiente virtual deste projeto.
6. Execute a transcrição usando o módulo transcriber.cli.
7. Aguarde o processamento terminar.
8. Informe o caminho do arquivo gerado.
9. Leia a transcrição gerada.
10. Apresente um resumo breve do resultado.

## Execução

No Windows PowerShell:

```powershell
& ".venv\Scripts\python.exe" -m transcriber.cli "CAMINHO_DO_ARQUIVO"
```
