# Estados do PresenceAgent

Este documento descreve os estados usados pelo **PresenceAgent**, sua finalidade, transições esperadas, eventos relacionados e a diferença entre o estado global do agente e os estados internos dos serviços.

---

## 1. Visão geral

O PresenceAgent possui um estado global de alto nível controlado pelo `StateManager`.

Esse estado representa a situação geral do agente, e não todos os detalhes internos de cada serviço.

Exemplo de fluxo geral:

```txt
BOOTING
  ↓
READY
  ↓
USER_PRESENT
  ↓
USER_AWAY
  ↓
USER_PRESENT
  ↓
SHUTDOWN
```

O estado global é usado para:

- registrar transições importantes;
- permitir health checks;
- facilitar auditoria;
- representar a condição geral do agente;
- evitar que cada serviço precise manter uma visão própria do sistema inteiro.

---

## 2. Onde os estados são definidos

Os estados ficam definidos em:

```txt
app/core/states.py
```

O gerenciamento de estado fica em:

```txt
app/core/state_manager.py
```

O `StateManager` é responsável por:

- armazenar o estado atual;
- registrar mudança de estado;
- emitir `STATE_CHANGED` quando há transição;
- centralizar a razão da mudança.

---

## 3. Estado global versus estados internos

É importante diferenciar dois conceitos:

```txt
Estado global do agente
    controlado pelo StateManager

Estado interno de serviço
    controlado individualmente por cada service
```

Exemplo:

```txt
StateManager
    USER_PRESENT

SecurityService
    pode estar em suspeita interna de unknown

StartupAssistantService
    pode já ter concluído a sequência de startup

CameraService
    pode estar running
```

Ou seja, o estado global não representa todos os subestados internos.

Ele representa apenas o estado geral mais relevante do agente.

---

## 4. Estados globais atuais

Os estados principais do agente são:

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

Nem todos precisam aparecer em todos os fluxos atuais. Alguns existem para expansão, rastreabilidade ou compatibilidade arquitetural.

---

## 5. `BOOTING`

### Descrição

Estado inicial do agente.

Indica que o sistema ainda está subindo seus componentes principais.

### Quando ocorre

Logo após a criação do `StateManager`.

### Responsável

```txt
StateManager
```

### Entrada típica

```txt
Processo Python iniciou
↓
main.py criou EventBus e StateManager
↓
Estado inicial: BOOTING
```

### Saídas esperadas

```txt
BOOTING -> READY
BOOTING -> ERROR
BOOTING -> SHUTDOWN
```

### Exemplo de log

```txt
Estado inicial: BOOTING
```

### Observações

Nenhuma ação crítica deve acontecer enquanto o sistema está em `BOOTING`.

A câmera ainda pode não estar pronta, os serviços ainda podem não ter se inscrito no `EventBus` e o modelo facial pode ainda não ter sido carregado.

---

## 6. `READY`

### Descrição

Indica que o core do agente foi inicializado com sucesso.

O sistema está pronto para começar a operar, mas ainda não necessariamente confirmou presença de usuário.

### Quando ocorre

Depois de:

- criar `EventBus`;
- criar `StateManager`;
- registrar listeners principais;
- emitir `SYSTEM_BOOT`;
- inicializar o core com sucesso.

### Transição típica

```txt
BOOTING -> READY
```

### Responsável pela transição

```txt
main.py
```

### Exemplo de chamada

```python
state_manager.set_state(
    State.READY,
    reason="Core inicializado com sucesso",
)
```

### Saídas esperadas

```txt
READY -> USER_PRESENT
READY -> USER_AWAY
READY -> ERROR
READY -> SHUTDOWN
```

### Exemplo de log

```txt
Estado alterado: BOOTING -> READY | Motivo: Core inicializado com sucesso
```

### Observações

`READY` não significa que a câmera já detectou alguém.

Significa apenas que o agente está apto para iniciar sua operação normal.

---

## 7. `SEARCHING_FACE`

### Descrição

Estado conceitual para representar que o agente está procurando um rosto.

### Situação atual

Este estado pode existir no enum, mas o fluxo atual geralmente transita de `READY` diretamente para `USER_PRESENT` ou permanece em `READY` até a presença ser confirmada.

### Quando poderia ser usado

Futuramente, pode ser usado quando:

```txt
câmera está ativa
modelo carregado
nenhum rosto estável detectado ainda
```

### Transições possíveis

```txt
READY -> SEARCHING_FACE
SEARCHING_FACE -> FACE_VISIBLE
SEARCHING_FACE -> USER_PRESENT
SEARCHING_FACE -> USER_AWAY
SEARCHING_FACE -> ERROR
SEARCHING_FACE -> SHUTDOWN
```

### Observações

Este estado é útil se o projeto evoluir para uma UI ou dashboard que mostre explicitamente:

```txt
Aguardando rosto...
```

---

## 8. `FACE_VISIBLE`

### Descrição

Estado conceitual para representar que um rosto está visível, mas a presença ainda não foi confirmada.

### Situação atual

O comportamento atual é controlado principalmente pelo `PresenceService` com candidatos temporais:

```txt
FACE_DETECTED
    ↓
Candidato de presença
    ↓
USER_PRESENT após confirmação
```

Por isso, o estado global `FACE_VISIBLE` pode não ser usado diretamente em todas as execuções.

### Quando poderia ser usado

Futuramente, pode representar:

```txt
rosto detectado
mas ainda aguardando USER_PRESENT_CONFIRM_SECONDS
```

### Transições possíveis

```txt
SEARCHING_FACE -> FACE_VISIBLE
READY -> FACE_VISIBLE
FACE_VISIBLE -> USER_PRESENT
FACE_VISIBLE -> SEARCHING_FACE
FACE_VISIBLE -> USER_AWAY
FACE_VISIBLE -> SHUTDOWN
```

### Observações

Esse estado é útil para interfaces visuais, mas o projeto atual já possui logs e debug window que mostram essa condição sem depender do estado global.

---

## 9. `USER_PRESENT`

### Descrição

Indica que o usuário foi considerado presente pelo `PresenceService`.

Este é um dos estados principais do agente.

### Quando ocorre

Quando o `PresenceService` confirma presença por tempo suficiente.

Fluxo:

```txt
FACE_DETECTED
    ↓
Sinal facial voltou
    ↓
Candidato de presença iniciado
    ↓
Presença confirmada
    ↓
USER_PRESENT
```

### Evento relacionado

```txt
USER_PRESENT
```

### Emitido por

```txt
PresenceService
```

### Consumido por

```txt
main.py
SystemService
TeamsPresenceService
HealthService
```

### Transição típica

```txt
READY -> USER_PRESENT
USER_AWAY -> USER_PRESENT
```

### Exemplo de payload

```json
{
    "timestamp": 1782150000.0,
    "reason": "Presença confirmada por 3.1s"
}
```

### Exemplo de log

```txt
Usuário PRESENTE. Presença confirmada por 3.1s
Estado alterado: READY -> USER_PRESENT | Motivo: Presença confirmada por 3.1s
```

### Ações relacionadas

Quando o sistema entra em `USER_PRESENT`, podem ocorrer:

- reset de lock por ausência no `SystemService`;
- atualização de health state;
- possível mock/update de Teams;
- continuidade do monitoramento;
- nenhuma ação de desbloqueio automático.

### Observações

`USER_PRESENT` significa que há presença facial confirmada, não necessariamente que a identidade já foi autorizada.

A identidade é tratada separadamente por eventos como:

```txt
IDENTITY_RECOGNIZED
IDENTITY_UNKNOWN
IDENTITY_UNCERTAIN
```

---

## 10. `USER_AWAY`

### Descrição

Indica que o usuário foi considerado ausente.

Este estado é usado para ações como bloqueio da estação.

### Quando ocorre

Quando o `PresenceService` confirma ausência após tolerância temporal.

Fluxo:

```txt
FACE_LOST
    ↓
aguarda FACE_LOST_GRACE_SECONDS
    ↓
Candidato de ausência iniciado
    ↓
Ausência confirmada por USER_AWAY_SECONDS
    ↓
USER_AWAY
```

### Evento relacionado

```txt
USER_AWAY
```

### Emitido por

```txt
PresenceService
```

### Consumido por

```txt
main.py
SystemService
SecurityService
TeamsPresenceService
HealthService
```

### Transição típica

```txt
USER_PRESENT -> USER_AWAY
READY -> USER_AWAY
```

### Exemplo de payload

```json
{
    "timestamp": 1782150000.0,
    "reason": "Ausência confirmada por 30.1s"
}
```

### Exemplo de log

```txt
Usuário AUSENTE. Ausência confirmada por 30.1s
Estado alterado: USER_PRESENT -> USER_AWAY | Motivo: Ausência confirmada por 30.1s
```

### Ações relacionadas

Quando o sistema entra em `USER_AWAY`, podem ocorrer:

- lock do Windows via `SystemService`, se habilitado;
- reset de tracking de suspeita no `SecurityService`;
- update/mock de presença Teams;
- atualização do health check.

### Observações

`USER_AWAY` é um evento de negócio e deve ser usado para ações críticas.

Não se deve bloquear a estação diretamente por `FACE_LOST`.

---

## 11. `ERROR`

### Descrição

Estado reservado para falhas críticas.

### Quando pode ocorrer

Exemplos:

- câmera indisponível;
- modelo facial ausente;
- erro irrecuperável em serviço essencial;
- falha crítica de configuração.

### Transições possíveis

```txt
BOOTING -> ERROR
READY -> ERROR
USER_PRESENT -> ERROR
USER_AWAY -> ERROR
ERROR -> SHUTDOWN
```

### Evento relacionado

```txt
SYSTEM_ERROR
```

### Payload sugerido

```json
{
    "source": "CameraService",
    "error": "Não foi possível abrir câmera",
    "timestamp": 1782150000.0
}
```

### Observações

O projeto atual prioriza logs e tratamento local de exceções nos serviços.

O uso formal de `ERROR` pode ser expandido no futuro com:

- watchdog;
- auto-recovery;
- notificação local;
- painel de status.

---

## 12. `SHUTDOWN`

### Descrição

Estado final do agente.

Indica encerramento solicitado ou finalização controlada.

### Quando ocorre

Normalmente após:

```txt
CTRL+C
SIGINT
SIGTERM
encerramento solicitado pelo Windows
```

### Transição típica

```txt
USER_PRESENT -> SHUTDOWN
USER_AWAY -> SHUTDOWN
READY -> SHUTDOWN
ERROR -> SHUTDOWN
```

### Responsável

```txt
main.py
```

### Fluxo de encerramento

```txt
Encerrando PresenceAgent
    ↓
CameraService.stop()
    ↓
DebugWindowService.stop()
    ↓
HealthService.stop()
    ↓
StateManager -> SHUTDOWN
    ↓
SYSTEM_SHUTDOWN
```

### Exemplo de log

```txt
Estado alterado: USER_PRESENT -> SHUTDOWN | Motivo: Encerramento solicitado
PresenceAgent encerrado.
```

---

## 13. Transições principais

### 13.1 Boot normal

```txt
BOOTING -> READY
```

Motivo:

```txt
Core inicializado com sucesso
```

---

### 13.2 Primeira presença

```txt
READY -> USER_PRESENT
```

Motivo:

```txt
Presença confirmada por X segundos
```

---

### 13.3 Ausência

```txt
USER_PRESENT -> USER_AWAY
```

Motivo:

```txt
Ausência confirmada por X segundos
```

---

### 13.4 Retorno

```txt
USER_AWAY -> USER_PRESENT
```

Motivo:

```txt
Presença confirmada por X segundos
```

---

### 13.5 Encerramento

```txt
READY -> SHUTDOWN
USER_PRESENT -> SHUTDOWN
USER_AWAY -> SHUTDOWN
ERROR -> SHUTDOWN
```

Motivo:

```txt
Encerramento solicitado
```

---

## 14. Estados internos dos serviços

Além do estado global, alguns serviços mantêm estados internos.

Esses estados não aparecem necessariamente no `StateManager`.

---

## 14.1 Estados internos do `DetectionService`

Variáveis relevantes:

```txt
face_currently_visible
consecutive_detections
consecutive_losses
last_main_face
```

Uso:

```txt
controlar estabilidade da detecção facial
```

Fluxo interno:

```txt
face_currently_visible = False
    ↓
detecções consecutivas >= FACE_DETECTED_STREAK
    ↓
face_currently_visible = True
```

```txt
face_currently_visible = True
    ↓
perdas consecutivas >= FACE_LOST_STREAK
    ↓
face_currently_visible = False
```

---

## 14.2 Estados internos do `PresenceService`

Conceitos:

```txt
last_face_seen_at
presence_candidate_started_at
away_candidate_started_at
is_user_present
```

Uso:

```txt
transformar FACE_DETECTED/FACE_LOST em USER_PRESENT/USER_AWAY
```

---

## 14.3 Estados internos do `RecognitionService`

Variáveis relevantes:

```txt
recognizer
labels
processed_events
```

Uso:

```txt
controlar modelo facial carregado e frequência de processamento
```

---

## 14.4 Estados internos do `SecurityService`

Variáveis relevantes:

```txt
last_authorized_seen_at
unknown_started_at
unknown_streak
unknown_alert_triggered
multi_face_started_at
last_multi_face_prompt_at
multi_face_confirmed_for_current_event
```

Estados conceituais:

```txt
idle
trusted user recently seen
unknown suspicion started
unknown confirmed
multi-face detected
multi-face confirmed
alert triggered
```

Regras:

```txt
IDENTITY_RECOGNIZED
    reseta unknown tracking

IDENTITY_UNKNOWN
    inicia ou continua suspeita

MULTI_FACE
    usa fluxo separado
```

---

## 14.5 Estados internos do `SystemService`

Variáveis relevantes:

```txt
last_lock_attempt_at
lock_triggered_for_current_away
```

Uso:

```txt
evitar loop de lock
respeitar cooldown
```

Fluxo:

```txt
USER_AWAY
    ↓
se ainda não bloqueou nesta ausência
    ↓
bloqueia
    ↓
lock_triggered_for_current_away = True
```

```txt
USER_PRESENT
    ↓
lock_triggered_for_current_away = False
```

---

## 14.6 Estados internos do `StartupAssistantService`

Variáveis relevantes:

```txt
sequence_started
sequence_completed
```

Uso:

```txt
garantir que a rotina de startup rode uma vez por sessão
```

Fluxo:

```txt
aguardando usuário autorizado
    ↓
IDENTITY_RECOGNIZED
    ↓
sequence_started = True
    ↓
abre apps
    ↓
sequence_completed = True
```

---

## 14.7 Estados internos do `PromptService`

Variáveis relevantes:

```txt
prompt_active
```

Uso:

```txt
evitar múltiplos prompts simultâneos
```

---

## 14.8 Estados internos do `HealthService`

Variáveis relevantes:

```txt
is_running
camera_running
camera_errors
user_present_events
user_away_events
started_at
```

Uso:

```txt
relatórios periódicos de saúde
```

---

## 14.9 Estados internos do `DebugWindowService`

Variáveis relevantes:

```txt
latest_frame
latest_faces
latest_identities
last_face_detected_at
is_running
```

Uso:

```txt
renderizar janela visual de debug
```

---

## 15. Relação entre estados e eventos

| Estado global | Evento que geralmente causa | Serviço principal |
|---|---|---|
| `BOOTING` | criação do `StateManager` | `StateManager` |
| `READY` | inicialização do core | `main.py` |
| `USER_PRESENT` | `USER_PRESENT` | `PresenceService` |
| `USER_AWAY` | `USER_AWAY` | `PresenceService` |
| `ERROR` | `SYSTEM_ERROR` | serviços diversos |
| `SHUTDOWN` | encerramento solicitado | `main.py` |

---

## 16. Regras importantes

### 16.1 Não confundir presença com identidade

`USER_PRESENT` significa:

```txt
há uma presença facial confirmada
```

Não significa necessariamente:

```txt
é o Filipe
```

A identidade é determinada por:

```txt
IDENTITY_RECOGNIZED
IDENTITY_UNKNOWN
IDENTITY_UNCERTAIN
```

---

### 16.2 Não bloquear por eventos técnicos

Não usar diretamente:

```txt
FACE_LOST
```

para bloquear.

Usar:

```txt
USER_AWAY
SECURITY_ALERT
```

---

### 16.3 `IDENTITY_UNCERTAIN` é neutro

Identidade incerta não deve:

```txt
autorizar startup
acionar lock imediato
acionar suspeita automaticamente
```

Ela deve apenas indicar que o sistema não teve confiança suficiente.

---

### 16.4 Multi-face tem fluxo próprio

Quando há múltiplos rostos:

```txt
faces_count >= 2
```

O fluxo correto é:

```txt
MULTIPLE_FACES_DETECTED
    ↓
MULTIPLE_FACES_CONFIRMED
    ↓
PromptService
```

Unknown em cenário multi-face não deve virar lock direto.

---

## 17. Estado recomendado em produção

Para uso diário, normalmente o agente deve alternar entre:

```txt
READY
USER_PRESENT
USER_AWAY
SHUTDOWN
```

Estados como `SEARCHING_FACE`, `FACE_VISIBLE` e `ERROR` são úteis para expansão, dashboard ou diagnóstico.

---

## 18. Exemplos reais de fluxo

### 18.1 Usuário inicia o agente e é reconhecido

```txt
BOOTING
  ↓
READY
  ↓
USER_PRESENT
```

Em paralelo:

```txt
IDENTITY_RECOGNIZED
  ↓
StartupAssistantService executa rotina inicial
```

---

### 18.2 Usuário sai da frente da câmera

```txt
USER_PRESENT
  ↓
FACE_LOST técnico
  ↓
Grace period
  ↓
USER_AWAY
  ↓
SystemService pode bloquear o Windows
```

---

### 18.3 Pessoa desconhecida aparece sozinha

Estado global pode continuar:

```txt
USER_PRESENT
```

Mas o fluxo de segurança ocorre em paralelo:

```txt
IDENTITY_UNKNOWN
  ↓
SECURITY_SUSPICIOUS
  ↓
SECURITY_ALERT
  ↓
lock, se habilitado
```

---

### 18.4 Duas pessoas aparecem

Estado global pode continuar:

```txt
USER_PRESENT
```

Mas o fluxo multi-face ocorre:

```txt
MULTIPLE_FACES_DETECTED
  ↓
MULTIPLE_FACES_CONFIRMED
  ↓
PromptService pergunta se deseja bloquear
```

---

## 19. Evolução futura dos estados

Possíveis estados futuros:

```txt
STARTUP_WAITING_USER
STARTUP_RUNNING
STARTUP_COMPLETED
SECURITY_SUSPICIOUS
SECURITY_LOCKED
CAMERA_RECOVERING
DEGRADED
```

Esses estados poderiam ser adicionados se o projeto evoluir para dashboard, UI ou serviço Windows completo.

---

## 20. Resumo

O estado global do PresenceAgent é simples por design.

Ele responde à pergunta:

```txt
Qual é a condição geral do agente agora?
```

Enquanto os estados internos dos serviços respondem perguntas específicas:

```txt
A câmera está rodando?
O usuário foi visto recentemente?
Existe suspeita em andamento?
O startup já rodou?
O prompt está ativo?
```

Essa separação mantém o sistema simples, extensível e seguro.
