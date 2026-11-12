## Instalação no Windows

### 1. Baixe o projeto

Baixe o repositório como arquivo ZIP e extraia o conteúdo em uma pasta do seu computador.

### 2. Abra o PowerShell

Abra o PowerShell dentro da pasta extraída, onde está localizado o arquivo `install.ps1`.

### 3. Permita a execução de scripts

Execute o comando abaixo para permitir a execução do instalador durante a sessão atual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 4. Execute o instalador

```powershell
.\install.ps1
```

O instalador configurará automaticamente:

- Python 3.12;
- Ambiente virtual Python;
- Faster-Whisper e suas dependências;
- Modelo Whisper padrão;
- Claude Code, caso ainda não esteja instalado;
- Skills de transcrição e análise de audiências.

### 5. Inicie o Claude Code

Após a conclusão da instalação, execute:

```powershell
claude
```

Se solicitado, faça a autenticação com sua conta Anthropic.

### 6. Transcreva um arquivo de áudio ou vídeo

Dentro do Claude Code, execute:

```text
/transcrever "C:\Users\SeuUsuario\Downloads\audiencia.mp4"
```

A transcrição será processada localmente pelo Faster-Whisper.

O arquivo `.txt` gerado será salvo na pasta `transcriptions` do projeto.

### 7. Analise uma audiência

Após concluir a transcrição, execute:

```text
/analisar-audiencia
```

O Claude Code utilizará a transcrição gerada para realizar a análise conforme as instruções definidas no projeto.

### Observações

- Inicie o Claude Code dentro da pasta do projeto para que ele reconheça as Skills.
- A primeira instalação requer conexão com a internet para baixar as dependências e o modelo Whisper.
- A transcrição de áudio e vídeo é realizada localmente.
- A análise com Claude Code requer conexão com a internet e envia o conteúdo da transcrição à Anthropic para processamento.
