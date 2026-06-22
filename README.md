# PresenceAgent

Agente local de presença, segurança e inicialização inteligente para Windows.

O **PresenceAgent** usa a webcam do computador para detectar presença, reconhecer o usuário autorizado, reagir a pessoas desconhecidas, bloquear a estação quando necessário e executar uma rotina inicial personalizada quando o usuário autorizado é reconhecido.

> Projeto desenvolvido para uso local/corporativo, com foco em privacidade: o processamento ocorre na máquina e os dados faciais/modelos ficam armazenados localmente.

---

## Visão geral

O PresenceAgent foi criado para transformar o PC em uma estação mais inteligente:

- Detecta se existe rosto na câmera.
- Identifica se o rosto é do usuário autorizado.
- Diferencia usuário autorizado, rosto desconhecido e identidade incerta.
- Detecta múltiplos rostos e pode perguntar se deseja bloquear a estação.
- Bloqueia o Windows automaticamente em cenários configurados.
- Executa uma rotina de inicialização após reconhecer o usuário autorizado.
- Abre aplicativos e sites configurados.
- Mantém logs e health checks.
- Possui janela de debug opcional.
- Possui integração Teams preparada por provider, mas Graph pode depender de políticas do tenant.

---

## Funcionalidades principais

### Presença

O agente detecta presença com base no rosto visível na webcam.

Eventos principais:

- `USER_PRESENT`: usuário presente.
- `USER_AWAY`: usuário ausente.

A ausência não é marcada imediatamente. O sistema usa tempos de tolerância para evitar falso positivo quando o usuário apenas olha para o lado, abaixa a cabeça ou a câmera perde o rosto por alguns segundos.

---

### Reconhecimento facial

O reconhecimento usa OpenCV LBPH via `opencv-contrib-python`.

O sistema trabalha com três faixas:

```txt
confidence <= RECOGNITION_AUTHORIZED_THRESHOLD
    usuário autorizado

RECOGNITION_AUTHORIZED_THRESHOLD < confidence < RECOGNITION_UNKNOWN_THRESHOLD
    identidade incerta

confidence >= RECOGNITION_UNKNOWN_THRESHOLD
    desconhecido
```

Importante: no LBPH, **quanto menor o valor de confidence, melhor o match**.

---

### Segurança

O SecurityService lida com situações como:

- pessoa desconhecida sozinha na câmera;
- múltiplos rostos;
- identidade incerta;
- confirmação antes de ação crítica;
- bloqueio do Windows por pessoa desconhecida, se habilitado.

Fluxo simplificado:

```txt
Pessoa desconhecida confirmada
        ↓
SECURITY_ALERT
        ↓
Lock do Windows, se UNKNOWN_LOCK_ENABLED=True
```

Para múltiplos rostos:

```txt
Mais de um rosto detectado
        ↓
Confirma por alguns segundos
        ↓
Pergunta se deseja bloquear a estação
```

---

### Startup Assistant

Quando o PresenceAgent inicia, ele espera reconhecer o usuário autorizado.

Depois disso, ele pode:

- dar uma saudação;
- abrir Teams;
- abrir SouGov no Chrome;
- abrir Brave com perfil MCOM;
- abrir Brave com perfil Pessoal;
- abrir outros apps/sites configurados.

Esse fluxo roda uma vez por sessão, se configurado.

---

### Integração Teams

O projeto possui uma camada de integração com Teams baseada em providers:

- `mock`: apenas simula/loga a alteração de presença.
- `graph`: usa Microsoft Graph para presença, quando permitido pelo tenant.

A integração oficial por Microsoft Graph exige permissões como `Presence.ReadWrite` e pode ser bloqueada por políticas de Conditional Access do tenant. O método oficial `presence: setPresence` usa uma sessão da aplicação com `sessionId`, `availability`, `activity` e `expirationDuration`, e pode demorar alguns minutos para refletir no cliente Teams por causa do polling do Teams. citeturn58search1turn58search2

No ambiente atual, caso o Graph seja bloqueado por Conditional Access, use:

```env
ENABLE_TEAMS_INTEGRATION=False
TEAMS_PROVIDER=mock
```

---

## Estrutura do projeto

```txt
SISTEMA_RECONHECIMENTO_MCOM/
│
├── app/
│   ├── core/
│   │   ├── config.py
│   │   ├── event_bus.py
│   │   ├── events.py
│   │   ├── logger.py
│   │   ├── state_manager.py
│   │   └── states.py
│   │
│   ├── services/
│   │   ├── camera_service.py
│   │   ├── debug_window_service.py
│   │   ├── detection_service.py
│   │   ├── health_service.py
│   │   ├── presence_service.py
│   │   ├── prompt_service.py
│   │   ├── recognition_service.py
│   │   ├── security_service.py
│   │   ├── startup_assistant_service.py
│   │   ├── system_service.py
│   │   └── teams_presence_service.py
│   │
│   ├── integrations/
│   │   ├── app_launcher.py
│   │   ├── graph_teams_provider.py
│   │   ├── mock_teams_provider.py
│   │   ├── teams_provider.py
│   │   └── windows_integration.py
│   │
│   ├── config/
│   │   ├── startup_apps.example.json
│   │   └── startup_apps.json
│   │
│   └── data/
│       ├── faces/
│       └── models/
│
├── docs/
├── logs/
├── scripts/
├── tests/
├── tools/
│   ├── enroll_user.py
│   ├── train_recognizer.py
│   └── test_recognizer.py
│
├── .env
├── .env.example
├── .gitignore
├── main.py
├── README.md
└── requirements.txt
```

---

## Requisitos

- Windows 10 ou superior.
- Webcam funcional.
- Python instalado.
- Git opcional, mas recomendado.
- Permissão local para acessar a câmera.
- Para reconhecimento facial LBPH: `opencv-contrib-python`.

---

## Instalação

### 1. Clonar ou baixar o projeto

Com Git:

```powershell
git clone <URL_DO_REPOSITORIO>
cd SISTEMA_RECONHECIMENTO_MCOM
```

Ou baixe o ZIP do projeto, extraia e abra a pasta no terminal.

---

### 2. Criar ambiente virtual

```powershell
py -m venv .venv
```

Ativar:

```powershell
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear execução de script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

---

### 3. Instalar dependências

```powershell
pip install -r requirements.txt
```

Se estiver montando do zero, as dependências principais são:

```powershell
pip install opencv-contrib-python python-dotenv pytest msal requests
```

---

### 4. Criar `.env`

Copie o exemplo:

```powershell
Copy-Item .env.example .env
```

Depois ajuste o arquivo `.env` conforme o ambiente local.

---

## Configuração essencial

### Câmera

```env
CAMERA_INDEX=0
CAMERA_BACKEND=DSHOW
FRAME_WIDTH=640
FRAME_HEIGHT=480
TARGET_FPS=10
```

No Windows, `DSHOW` costuma ser mais estável que o backend padrão do OpenCV.

---

### Presença

```env
FACE_LOST_GRACE_SECONDS=12
USER_AWAY_SECONDS=30
USER_PRESENT_CONFIRM_SECONDS=3
```

Significado:

- `FACE_LOST_GRACE_SECONDS`: tolerância para perda temporária do rosto.
- `USER_AWAY_SECONDS`: tempo sem rosto para marcar ausência.
- `USER_PRESENT_CONFIRM_SECONDS`: tempo com rosto para confirmar presença.

---

### Reconhecimento facial

```env
ENABLE_FACE_RECOGNITION=True
AUTHORIZED_USER=filipe
RECOGNITION_AUTHORIZED_THRESHOLD=55
RECOGNITION_UNKNOWN_THRESHOLD=65
RECOGNITION_PROCESS_EVERY_N_EVENTS=1
MIN_AUTHORIZED_FACE_WIDTH=150
```

Faixa recomendada atual:

```txt
<= 55  autorizado
56–64  incerto
>= 65  desconhecido
```

Esses valores devem ser recalibrados se mudar câmera, iluminação ou dataset.

---

### Segurança

```env
ENABLE_SECURITY_SERVICE=True
UNKNOWN_LOCK_ENABLED=True
UNKNOWN_CONFIRM_SECONDS=2
UNKNOWN_EVENT_STREAK=2
MIN_SECURITY_FACE_WIDTH=150
AUTHORIZED_GRACE_SECONDS=5
```

Para testar sem bloquear o Windows, use:

```env
UNKNOWN_LOCK_ENABLED=False
```

---

### Lock do Windows

```env
ENABLE_SYSTEM_ACTIONS=True
ENABLE_WINDOWS_LOCK=True
WINDOWS_LOCK_COOLDOWN_SECONDS=120
```

O lock usa a API do Windows para bloquear a estação. O desbloqueio continua sendo manual, por PIN/senha/Windows Hello.

---

### Debug visual

Para uso diário:

```env
ENABLE_DEBUG_WINDOW=False
DEBUG_MODE=False
LOG_LEVEL=INFO
```

Para depuração:

```env
ENABLE_DEBUG_WINDOW=True
DEBUG_MODE=True
LOG_LEVEL=INFO
```

---

### Startup Assistant

```env
ENABLE_STARTUP_ASSISTANT=True
STARTUP_REQUIRE_AUTHORIZED_USER=True
STARTUP_RUN_ONCE_PER_SESSION=True
STARTUP_GREETING_ENABLED=True
STARTUP_GREETING_MODE=log
STARTUP_GREETING_MESSAGE=Olá Filipe, bem-vindo de volta.
STARTUP_OPEN_APPS_ENABLED=True
STARTUP_APPS_CONFIG=app/config/startup_apps.json
STARTUP_APP_DELAY_SECONDS=1.5
```

---

## Configuração dos apps de inicialização

Arquivo real:

```txt
app/config/startup_apps.json
```

Exemplo:

```json
[
    {
        "name": "Microsoft Teams",
        "enabled": true,
        "type": "uri",
        "target": "msteams:"
    },
    {
        "name": "SouGov - Chrome",
        "enabled": true,
        "type": "process",
        "target": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "args": [
            "https://sougov.sigepe.gov.br/sougov/"
        ]
    },
    {
        "name": "Brave - Perfil MCOM",
        "enabled": true,
        "type": "process",
        "target": "C:\\Users\\filipe.franca\\AppData\\Local\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
        "args": [
            "--profile-directory=Default"
        ]
    },
    {
        "name": "Brave - Perfil Pessoal",
        "enabled": true,
        "type": "process",
        "target": "C:\\Users\\filipe.franca\\AppData\\Local\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
        "args": [
            "--profile-directory=Profile 1"
        ]
    }
]
```

Tipos suportados:

- `uri`: abre protocolo do Windows, como `msteams:`.
- `process`: abre executável com argumentos.
- `path`: abre pasta ou arquivo.

---

## Cadastro facial do usuário autorizado

### 1. Capturar imagens

```powershell
python tools/enroll_user.py --user filipe --samples 180
```

Durante a captura:

- fique de frente;
- olhe levemente para esquerda e direita;
- varie a distância;
- use iluminação semelhante ao uso real;
- evite imagens borradas ou muito escuras.

As imagens são salvas em:

```txt
app/data/faces/filipe/
```

Esses dados são biométricos e não devem ser versionados.

---

### 2. Treinar o modelo

```powershell
python tools/train_recognizer.py
```

Isso gera:

```txt
app/data/models/lbph_model.yml
app/data/models/labels.json
```

---

### 3. Testar reconhecimento

```powershell
python tools/test_recognizer.py
```

Observe os valores de confidence:

```txt
Filipe de frente: idealmente baixo
Filipe de lado: um pouco maior
Pessoa desconhecida: maior que o threshold de unknown
```

Lembrete:

```txt
No LBPH, menor confidence = melhor match.
```

---

## Execução manual

Com a venv ativa:

```powershell
python main.py
```

Encerrar:

```txt
CTRL+C
```

---

## Execução com o Windows

### 1. Criar script de inicialização

Crie:

```txt
scripts/start_agent.ps1
```

Conteúdo:

```powershell
Set-Location "C:\Users\filipe.franca\Dev\Pessoal\SISTEMA_RECONHECIMENTO_MCOM"

.\.venv\Scripts\python.exe main.py
```

Teste:

```powershell
powershell.exe -ExecutionPolicy Bypass -File ".\scripts\start_agent.ps1"
```

---

### 2. Criar tarefa agendada

```powershell
$ProjectPath = "C:\Users\filipe.franca\Dev\Pessoal\SISTEMA_RECONHECIMENTO_MCOM"
$ScriptPath = "$ProjectPath\scripts\start_agent.ps1"

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`"" `
    -WorkingDirectory $ProjectPath

$Trigger = New-ScheduledTaskTrigger -AtLogOn

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName "PresenceAgent" `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Inicia o PresenceAgent ao fazer logon no Windows." `
    -Force
```

O Windows também permite configurar apps de inicialização pelo `shell:startup`, mas o Agendador de Tarefas é mais controlável para esse projeto. citeturn76search38turn76search32

---

### 3. Testar tarefa

```powershell
Start-ScheduledTask -TaskName "PresenceAgent"
```

Ver status:

```powershell
Get-ScheduledTask -TaskName "PresenceAgent"
Get-ScheduledTaskInfo -TaskName "PresenceAgent"
```

Parar:

```powershell
Stop-ScheduledTask -TaskName "PresenceAgent"
```

Remover:

```powershell
Unregister-ScheduledTask -TaskName "PresenceAgent" -Confirm:$false
```

---

## Logs

Os logs são salvos em:

```txt
logs/
```

Exemplo de eventos:

```txt
USER_PRESENT
USER_AWAY
SECURITY_ALERT
MULTIPLE_FACES_CONFIRMED
HealthCheck
CameraService iniciado
StartupAssistant concluído
```

O sistema não salva fotos ou vídeos durante o uso normal. Imagens só são salvas durante o processo explícito de cadastro facial.

---

## Privacidade e segurança

- O processamento é local.
- Os frames da webcam ficam em memória durante o uso normal.
- O sistema não grava vídeo.
- O sistema não salva fotos durante execução normal.
- Dados faciais e modelos ficam em `app/data/`.
- `app/data/faces/` e `app/data/models/` devem ficar no `.gitignore`.
- O `.env` não deve ser versionado.

---

## `.gitignore` recomendado

```gitignore
# Python
__pycache__/
*.pyc
*.pyo

# Virtual environments
venv/
.venv/

# Environment
.env

# Logs
logs/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Biometric/local data
app/data/faces/
app/data/models/

# Local app config
app/config/startup_apps.json
```

---

## Troubleshooting

### Webcam abre, mas não captura frame

Use:

```env
CAMERA_BACKEND=DSHOW
```

No Windows, isso costuma resolver problemas do backend MSMF.

---

### Chrome/Brave não abrem

Use caminho completo do `.exe` no `startup_apps.json`.

Teste:

```powershell
Test-Path "C:\Program Files\Google\Chrome\Application\chrome.exe"
Test-Path "C:\Users\filipe.franca\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"
```

---

### Pessoa desconhecida sendo reconhecida como Filipe

Ajuste:

```env
RECOGNITION_AUTHORIZED_THRESHOLD=55
RECOGNITION_UNKNOWN_THRESHOLD=65
```

Se ainda ocorrer, reduza o authorized threshold:

```env
RECOGNITION_AUTHORIZED_THRESHOLD=50
```

Depois recapture e retreine o dataset facial.

---

### Usuário autorizado caindo como incerto

Aumente levemente:

```env
RECOGNITION_AUTHORIZED_THRESHOLD=58
```

Ou capture mais imagens do usuário autorizado com variações realistas.

---

### Graph/Teams bloqueado

Se aparecer erro de Conditional Access, use:

```env
ENABLE_TEAMS_INTEGRATION=False
TEAMS_PROVIDER=mock
```

O erro AADSTS/53003 indica que o login foi aceito, mas a política de Conditional Access bloqueou a emissão do token. citeturn65search23turn65search28

---

## Roadmap

Possíveis evoluções:

- Interface de configuração.
- Empacotamento como app Windows.
- Watchdog e auto-restart.
- Rotação automática de logs.
- Migração de LBPH para embeddings faciais modernos.
- Dashboard local.
- Integração Teams via Graph, caso o tenant permita.
- Configuração visual de apps de startup.

---

## Status atual

```txt
MVP operacional
Presença: OK
Reconhecimento facial: OK
Segurança contextual: OK
Startup Assistant: OK
Teams Graph: bloqueado por política do tenant
```
