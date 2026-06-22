# Arquitetura do PresenceAgent

Este documento descreve a arquitetura completa do **PresenceAgent**, um agente local para Windows orientado a eventos, responsável por detectar presença via webcam, reconhecer o usuário autorizado, aplicar regras de segurança contextual, bloquear a estação quando necessário e executar uma rotina de inicialização personalizada.

---

## 1. Objetivo do sistema

O PresenceAgent foi projetado para transformar a estação de trabalho em um ambiente mais inteligente e seguro.

Ele deve ser capaz de:

- detectar se existe uma pessoa diante da câmera;
- confirmar presença e ausência com tolerância temporal;
- reconhecer se o rosto detectado pertence ao usuário autorizado;
- diferenciar usuário autorizado, identidade incerta e pessoa desconhecida;
- identificar múltiplos rostos no mesmo ambiente;
- bloquear o Windows em caso de ausência ou pessoa desconhecida confirmada;
- perguntar ao usuário se deseja bloquear quando houver múltiplos rostos;
- executar uma rotina de startup após reconhecer o usuário autorizado;
- abrir aplicativos, sites e perfis de navegador configurados;
- registrar logs e health checks;
- operar de forma local, sem salvar fotos durante a execução normal;
- manter uma arquitetura modular, configurável e extensível.

---

## 2. Princípios arquiteturais

A arquitetura segue alguns princípios fundamentais.

### 2.1 Orientação a eventos

Os módulos principais não se chamam diretamente. Eles se comunicam por eventos emitidos no `EventBus`.

Exemplo:

```txt
CameraService
    ↓ FRAME_CAPTURED
DetectionService
    ↓ FACE_DETECTED
RecognitionService
    ↓ IDENTITY_RECOGNIZED
StartupAssistantService
    ↓ abre apps configurados
```

Isso reduz acoplamento e facilita adicionar ou remover serviços sem reescrever o sistema inteiro.

---

### 2.2 Separação de responsabilidades

Cada serviço tem uma responsabilidade clara:

```txt
CameraService             captura frames
DetectionService          detecta rostos
RecognitionService        identifica usuário
PresenceService           interpreta presença/ausência
SecurityService           aplica regras de segurança
PromptService             pergunta ao usuário sobre ações sensíveis
SystemService             executa ações por presença/ausência
StartupAssistantService   executa rotina inicial autorizada
HealthService             monitora saúde do agente
DebugWindowService        exibe diagnóstico visual
TeamsPresenceService      abstrai integração com Teams
```

---

### 2.3 Configuração externa

As decisões de comportamento são controladas por `.env`.

Exemplos:

```env
ENABLE_WINDOWS_LOCK=True
UNKNOWN_LOCK_ENABLED=True
ENABLE_DEBUG_WINDOW=False
RECOGNITION_AUTHORIZED_THRESHOLD=55
RECOGNITION_UNKNOWN_THRESHOLD=65
```

Isso permite ajustar o agente sem alterar código.

---

### 2.4 Segurança por confirmação

O agente evita ações críticas em eventos brutos.

Ele não bloqueia a estação apenas porque um frame falhou ou porque houve uma leitura incerta.

Em vez disso, usa:

- streaks;
- tempos mínimos;
- grace periods;
- cooldowns;
- confirmação contextual;
- prompt para múltiplos rostos.

---

### 2.5 Privacidade local

Durante a execução normal, o agente não salva imagens ou vídeos.

Frames da câmera são processados em memória.

As únicas imagens salvas são capturadas explicitamente durante o cadastro facial com `tools/enroll_user.py`.

---

## 3. Visão em camadas

A aplicação é dividida em camadas.

```txt
main.py
  ↓
core
  ↓
services
  ↓
integrations
  ↓
Windows / câmera / apps / Graph / arquivos locais
```

---

## 4. Estrutura de diretórios

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
│   ├── architecture.md
│   ├── events.md
│   ├── roadmap.md
│   └── states.md
│
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

## 5. Camada `core`

A camada `core` contém a infraestrutura interna do agente.

---

### 5.1 `config.py`

Carrega variáveis do `.env` usando `python-dotenv` e expõe o objeto global `config`.

Responsabilidades:

- centralizar configuração;
- converter strings do `.env` para tipos corretos;
- evitar valores fixos espalhados no código.

Exemplos de grupos de configuração:

```txt
Camera
Face Detection
Presence
Face Recognition
Security
Windows Actions
Health
Debug
Teams Integration
Startup Assistant
```

---

### 5.2 `event_bus.py`

Implementa o barramento interno de eventos.

Responsabilidades:

- registrar callbacks;
- emitir eventos;
- capturar exceções em listeners;
- impedir que falha em um listener derrube o agente;
- resumir payloads grandes nos logs.

Exemplo conceitual:

```python
event_bus.subscribe(Event.USER_AWAY, callback)
event_bus.emit(Event.USER_AWAY, payload)
```

---

### 5.3 `events.py`

Define os eventos do sistema.

Eventos principais:

```txt
SYSTEM_BOOT
SYSTEM_READY
SYSTEM_ERROR
SYSTEM_SHUTDOWN

CAMERA_STARTING
CAMERA_STARTED
CAMERA_ERROR
CAMERA_STOPPED

FRAME_CAPTURED

FACE_DETECTED
FACE_LOST

IDENTITY_RECOGNIZED
IDENTITY_UNKNOWN
IDENTITY_UNCERTAIN

USER_PRESENT
USER_AWAY

SECURITY_SUSPICIOUS
SECURITY_ALERT

MULTIPLE_FACES_DETECTED
MULTIPLE_FACES_CONFIRMED

STATE_CHANGED
```

---

### 5.4 `states.py`

Define os estados de alto nível do agente.

Exemplo:

```txt
BOOTING
READY
SEARCHING_FACE
FACE_VISIBLE
USER_PRESENT
USER_AWAY
ERROR
SHUTDOWN
```

Nem todo estado interno dos serviços aparece no `StateManager`.

O `StateManager` representa o estado geral da aplicação.

---

### 5.5 `state_manager.py`

Mantém o estado atual do agente e emite `STATE_CHANGED` quando há transição.

Exemplo:

```txt
BOOTING -> READY
READY -> USER_PRESENT
USER_PRESENT -> USER_AWAY
USER_AWAY -> SHUTDOWN
```

---

### 5.6 `logger.py`

Configura logging do projeto.

Responsabilidades:

- criar pasta `logs/`;
- gerar arquivo de log por execução;
- controlar log no console, se configurado;
- respeitar `LOG_LEVEL`.

---

## 6. Camada `services`

A camada `services` contém as regras de negócio.

---

## 6.1 `CameraService`

Responsável por abrir e ler a webcam.

### Entrada

Configurações:

```env
CAMERA_INDEX=0
CAMERA_BACKEND=DSHOW
FRAME_WIDTH=640
FRAME_HEIGHT=480
TARGET_FPS=10
```

### Saída

Emite:

```txt
CAMERA_STARTED
CAMERA_ERROR
CAMERA_STOPPED
FRAME_CAPTURED
```

### Observações

- A câmera roda em thread própria.
- O backend `DSHOW` é preferido no Windows.
- O serviço faz warm-up antes de declarar sucesso.
- A câmera deve ser o último serviço iniciado.

---

## 6.2 `DetectionService`

Responsável por detectar rostos nos frames.

### Escuta

```txt
FRAME_CAPTURED
```

### Emite

```txt
FACE_DETECTED
FACE_LOST
```

### Payload de `FACE_DETECTED`

```txt
frame_count
faces_count
faces
main_face
face_image
timestamp
consecutive_detections
is_stable
```

### Estratégias de estabilidade

- processa apenas a cada N frames;
- exige detecções consecutivas;
- exige perdas consecutivas;
- ignora rostos pequenos;
- escolhe o maior rosto como `main_face`;
- envia todos os rostos detectados em `faces`.

---

## 6.3 `RecognitionService`

Responsável por reconhecer a identidade dos rostos detectados.

### Escuta

```txt
FACE_DETECTED
```

### Emite

```txt
IDENTITY_RECOGNIZED
IDENTITY_UNKNOWN
IDENTITY_UNCERTAIN
```

### Modelo atual

Usa OpenCV LBPH:

```txt
cv2.face.LBPHFaceRecognizer_create()
```

### Decisão por thresholds

```txt
confidence <= RECOGNITION_AUTHORIZED_THRESHOLD
    IDENTITY_RECOGNIZED

RECOGNITION_AUTHORIZED_THRESHOLD < confidence < RECOGNITION_UNKNOWN_THRESHOLD
    IDENTITY_UNCERTAIN

confidence >= RECOGNITION_UNKNOWN_THRESHOLD
    IDENTITY_UNKNOWN
```

### Observações

- LBPH sempre retorna o label mais próximo.
- Como há apenas um usuário cadastrado, o `predicted_user` pode ser `filipe` mesmo para pessoa desconhecida.
- A decisão real depende do `confidence`.
- Menor confidence significa melhor match.

---

## 6.4 `PresenceService`

Transforma detecção facial em presença lógica.

### Escuta

```txt
FACE_DETECTED
FACE_LOST
```

### Emite

```txt
USER_PRESENT
USER_AWAY
```

### Estratégia

O serviço usa candidatos temporais:

```txt
FACE_DETECTED
    ↓
candidato de presença
    ↓
se persistir por USER_PRESENT_CONFIRM_SECONDS
    ↓
USER_PRESENT
```

```txt
FACE_LOST
    ↓
aguarda FACE_LOST_GRACE_SECONDS
    ↓
candidato de ausência
    ↓
se persistir por USER_AWAY_SECONDS
    ↓
USER_AWAY
```

---

## 6.5 `SecurityService`

Aplica regras de segurança contextual.

### Escuta

```txt
IDENTITY_RECOGNIZED
IDENTITY_UNKNOWN
IDENTITY_UNCERTAIN
FACE_DETECTED
FACE_LOST
USER_AWAY
```

### Emite

```txt
SECURITY_SUSPICIOUS
SECURITY_ALERT
MULTIPLE_FACES_DETECTED
MULTIPLE_FACES_CONFIRMED
```

### Regras principais

#### Usuário autorizado

```txt
IDENTITY_RECOGNIZED
    ↓
atualiza last_authorized_seen_at
    ↓
reseta suspeitas
```

#### Pessoa desconhecida sozinha

```txt
IDENTITY_UNKNOWN
    ↓
valida tamanho mínimo do rosto
    ↓
inicia suspeita
    ↓
confirma por tempo e streak
    ↓
SECURITY_ALERT
```

#### Identidade incerta

```txt
IDENTITY_UNCERTAIN
    ↓
não autoriza
    ↓
não aciona suspeita automaticamente
```

#### Múltiplos rostos

```txt
faces_count >= 2
    ↓
MULTIPLE_FACES_DETECTED
    ↓
confirma por tempo
    ↓
MULTIPLE_FACES_CONFIRMED
```

Quando há múltiplos rostos, unknown/uncertain não escalam diretamente para alerta. O fluxo multi-face assume.

---

## 6.6 `PromptService`

Mostra prompt de decisão para o usuário.

### Escuta

```txt
MULTIPLE_FACES_CONFIRMED
```

### Ação

Exibe mensagem no Windows:

```txt
Mais de um rosto foi detectado na câmera.
Deseja bloquear a estação agora?
```

Se o usuário escolher sim:

```txt
WindowsIntegration.lock_workstation()
```

O prompt roda em thread separada para não travar o pipeline de câmera.

---

## 6.7 `SystemService`

Executa ações em resposta ao estado de presença.

### Escuta

```txt
USER_PRESENT
USER_AWAY
```

### Responsabilidades

- logar retorno do usuário;
- bloquear estação em ausência, se habilitado;
- respeitar cooldown;
- evitar loop de bloqueio.

### Anti-loop

```txt
USER_AWAY
    ↓
lock_triggered_for_current_away = True
    ↓
não bloqueia novamente até USER_PRESENT
```

---

## 6.8 `StartupAssistantService`

Executa a rotina inicial após reconhecer o usuário autorizado.

### Escuta

```txt
IDENTITY_RECOGNIZED
```

### Ações

- saudação;
- abertura de apps;
- execução única por sessão.

### Fluxo

```txt
PresenceAgent iniciou
    ↓
aguarda Filipe
    ↓
IDENTITY_RECOGNIZED
    ↓
saudação
    ↓
AppLauncher.launch_startup_apps()
```

---

## 6.9 `HealthService`

Monitora saúde do agente.

### Escuta

```txt
CAMERA_STARTED
CAMERA_STOPPED
CAMERA_ERROR
USER_PRESENT
USER_AWAY
```

### Emite logs periódicos

```txt
HealthCheck | state=USER_PRESENT | camera_running=True | uptime=00:05:00 | camera_errors=0
```

---

## 6.10 `DebugWindowService`

Mostra uma janela OpenCV para depuração visual.

### Escuta

```txt
FRAME_CAPTURED
FACE_DETECTED
FACE_LOST
IDENTITY_RECOGNIZED
IDENTITY_UNKNOWN
IDENTITY_UNCERTAIN
```

### Exibe

- estado atual;
- frame count;
- quantidade de rostos;
- caixas faciais;
- status de identidade;
- confidence.

### Cores

```txt
Verde    autorizado
Vermelho desconhecido
Amarelo  incerto
Branco   pendente
```

---

## 6.11 `TeamsPresenceService`

Camada de integração com Teams.

### Escuta

```txt
USER_PRESENT
USER_AWAY
```

### Providers

```txt
mock
    simula alteração de presença

graph
    usa Microsoft Graph, se permitido
```

### Situação atual

O provider Graph foi preparado, mas pode ser bloqueado por Conditional Access do tenant.

Para operação segura:

```env
ENABLE_TEAMS_INTEGRATION=False
TEAMS_PROVIDER=mock
```

---

## 7. Camada `integrations`

A camada `integrations` concentra comunicação com recursos externos ao domínio da aplicação.

---

## 7.1 `WindowsIntegration`

Integração com Windows.

### Função principal

```txt
lock_workstation()
```

Usa API do Windows via `ctypes`.

---

## 7.2 `AppLauncher`

Abre apps, URIs, pastas e sites.

### Configuração

Lê:

```txt
app/config/startup_apps.json
```

### Tipos suportados

```txt
uri
process
path
```

Exemplo:

```json
{
    "name": "SouGov - Chrome",
    "enabled": true,
    "type": "process",
    "target": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "args": [
        "https://sougov.sigepe.gov.br/sougov/"
    ]
}
```

---

## 7.3 `TeamsProvider`

Interface base para providers de Teams.

Implementações:

```txt
MockTeamsProvider
GraphTeamsProvider
```

---

## 7.4 `GraphTeamsProvider`

Provider baseado em Microsoft Graph.

Responsabilidades:

- autenticar com MSAL;
- usar device code flow;
- obter token;
- chamar Graph `setPresence`;
- manter cache local de token.

Observação:

Em tenants corporativos, o fluxo pode ser bloqueado por Conditional Access.

---

## 8. Ferramentas auxiliares

A pasta `tools/` contém scripts operacionais.

---

### 8.1 `enroll_user.py`

Captura amostras faciais do usuário autorizado.

Exemplo:

```powershell
python tools/enroll_user.py --user filipe --samples 180
```

Salva recortes em:

```txt
app/data/faces/filipe/
```

---

### 8.2 `train_recognizer.py`

Treina o modelo LBPH.

Entrada:

```txt
app/data/faces/
```

Saída:

```txt
app/data/models/lbph_model.yml
app/data/models/labels.json
```

---

### 8.3 `test_recognizer.py`

Testa o modelo facial isoladamente.

Útil para calibrar:

```txt
RECOGNITION_AUTHORIZED_THRESHOLD
RECOGNITION_UNKNOWN_THRESHOLD
```

---

## 9. Dados locais

---

### 9.1 `app/data/faces/`

Contém imagens de treinamento.

Não deve ser versionado.

---

### 9.2 `app/data/models/`

Contém modelos treinados e labels.

Não deve ser versionado.

Exemplos:

```txt
lbph_model.yml
labels.json
msal_token_cache.bin
```

---

## 10. Configuração

---

### 10.1 `.env`

Arquivo real da máquina.

Não deve ser versionado.

---

### 10.2 `.env.example`

Modelo seguro para configuração.

Deve ser versionado.

---

### 10.3 `startup_apps.json`

Configuração real dos apps abertos no startup.

Pode conter caminhos locais.

Não deve ser versionado.

---

### 10.4 `startup_apps.example.json`

Exemplo versionável da configuração de startup apps.

---

## 11. Fluxos detalhados

---

### 11.1 Fluxo completo de presença

```txt
CameraService
    ↓ FRAME_CAPTURED
DetectionService
    ↓ FACE_DETECTED
PresenceService
    ↓ USER_PRESENT
StateManager
    ↓ STATE_CHANGED
```

Ausência:

```txt
DetectionService
    ↓ FACE_LOST
PresenceService
    ↓ candidato de ausência
    ↓ USER_AWAY
SystemService
    ↓ lock, se habilitado
```

---

### 11.2 Fluxo completo de identidade

```txt
DetectionService
    ↓ FACE_DETECTED com face_image
RecognitionService
    ↓ confidence <= authorized threshold
IDENTITY_RECOGNIZED
```

```txt
DetectionService
    ↓ FACE_DETECTED com face_image
RecognitionService
    ↓ confidence >= unknown threshold
IDENTITY_UNKNOWN
```

```txt
DetectionService
    ↓ FACE_DETECTED com face_image
RecognitionService
    ↓ confidence na zona intermediária
IDENTITY_UNCERTAIN
```

---

### 11.3 Fluxo de segurança por desconhecido

```txt
IDENTITY_UNKNOWN
    ↓
SecurityService
    ↓
valida tamanho mínimo do rosto
    ↓
inicia suspeita
    ↓
UNKNOWN_CONFIRM_SECONDS + UNKNOWN_EVENT_STREAK
    ↓
SECURITY_ALERT
    ↓
WindowsIntegration.lock_workstation(), se UNKNOWN_LOCK_ENABLED=True
```

---

### 11.4 Fluxo multi-face

```txt
FACE_DETECTED com faces_count >= 2
    ↓
SecurityService
    ↓
MULTIPLE_FACES_DETECTED
    ↓
MULTI_FACE_CONFIRM_SECONDS
    ↓
MULTIPLE_FACES_CONFIRMED
    ↓
PromptService
    ↓
usuário decide se bloqueia
```

---

### 11.5 Fluxo de startup

```txt
PresenceAgent inicia
    ↓
Câmera liga
    ↓
RecognitionService reconhece usuário autorizado
    ↓
StartupAssistantService
    ↓
saudação
    ↓
AppLauncher
    ↓
Teams / Chrome / Brave / apps configurados
```

---

## 12. Inicialização dos serviços

A ordem recomendada é:

```txt
DetectionService
RecognitionService
PresenceService
SystemService
SecurityService
PromptService
TeamsPresenceService
StartupAssistantService
HealthService
DebugWindowService
CameraService
```

Motivo:

```txt
A câmera emite eventos imediatamente.
Todos os consumidores devem estar inscritos antes dela iniciar.
```

---

## 13. Encerramento dos serviços

A ordem recomendada é:

```txt
CameraService.stop()
DebugWindowService.stop()
HealthService.stop()
StateManager -> SHUTDOWN
SYSTEM_SHUTDOWN
```

Motivo:

```txt
A câmera deve parar antes de serviços auxiliares para interromper novos FRAME_CAPTURED.
```

---

## 14. Políticas de segurança

### 14.1 Lock por ausência

Controlado por:

```env
ENABLE_WINDOWS_LOCK=True
ENABLE_SYSTEM_ACTIONS=True
```

Executado pelo `SystemService` em `USER_AWAY`.

---

### 14.2 Lock por desconhecido

Controlado por:

```env
UNKNOWN_LOCK_ENABLED=True
```

Executado pelo `SecurityService` após confirmação.

---

### 14.3 Prompt por múltiplos rostos

Controlado por:

```env
MULTI_FACE_WARNING_ENABLED=True
MULTI_FACE_AUTO_LOCK_ON_TIMEOUT=False
```

O padrão é perguntar, não bloquear automaticamente.

---

## 15. Limitações conhecidas

- O detector Haar Cascade pode oscilar com iluminação, ângulo e distância.
- LBPH funciona bem para MVP, mas não é reconhecimento facial moderno por embeddings.
- Com apenas um usuário treinado, o modelo sempre tenta retornar o label mais próximo.
- A decisão real depende do confidence.
- `face_index` não é tracking persistente; pode inverter entre frames.
- Teams Graph pode ser bloqueado por políticas corporativas.
- Ainda não há UI de configuração.
- Ainda não há instalador/empacotamento Windows.

---

## 16. Possíveis melhorias futuras

- `FaceTrackerService` para manter identidade por posição entre frames.
- Migração para embeddings faciais modernos.
- Interface gráfica de configuração.
- Dashboard local.
- Rotação automática de logs.
- Watchdog e auto-restart.
- Serviço Windows real.
- Instalador.
- Configuração visual de startup apps.
- Integração Teams via Graph quando permitido pelo tenant.

---

## 17. Resumo arquitetural

```txt
Core
    infraestrutura

Services
    regras de negócio

Integrations
    chamadas externas e Windows

Tools
    cadastro, treino e testes

Config
    comportamento local

Data
    dados biométricos e modelos locais
```

O PresenceAgent é um agente local modular, orientado a eventos, com foco em presença, identidade, segurança e automação do ambiente de trabalho.
