# Eventos do PresenceAgent

Este documento descreve os eventos usados pelo **PresenceAgent**, incluindo objetivo, origem, consumidores e payloads esperados.

O projeto é orientado a eventos: os serviços não dependem diretamente uns dos outros sempre que a comunicação pode ser feita por publicação e assinatura de eventos.

---

## 1. Visão geral

O `EventBus` é o mecanismo central de comunicação entre os serviços.

Fluxo conceitual:

```python
event_bus.subscribe(Event.USER_AWAY, callback)
event_bus.emit(Event.USER_AWAY, payload)
```

A arquitetura usa eventos para manter baixo acoplamento entre módulos.

Exemplo simplificado:

```txt
CameraService
    ↓ FRAME_CAPTURED
DetectionService
    ↓ FACE_DETECTED / FACE_LOST
RecognitionService
    ↓ IDENTITY_RECOGNIZED / IDENTITY_UNKNOWN / IDENTITY_UNCERTAIN
PresenceService
    ↓ USER_PRESENT / USER_AWAY
SecurityService / SystemService / StartupAssistantService
    ↓ ações locais
```

---

## 2. Categorias de eventos

Os eventos atuais podem ser agrupados em:

```txt
Sistema
Câmera
Frames
Face
Identidade
Presença
Segurança
Multi-face
Estado
```

---

## 3. Lista geral de eventos

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

## 4. Eventos de sistema

---

### 4.1 `SYSTEM_BOOT`

Indica que o agente iniciou o processo de boot.

#### Emitido por

```txt
main.py
```

#### Consumido por

Atualmente pode ser usado por serviços de auditoria, health check ou extensões futuras.

#### Payload típico

```json
{
    "message": "Sistema inicializado"
}
```

#### Observações

Este evento representa o início lógico do agente, antes da câmera começar a emitir frames.

---

### 4.2 `SYSTEM_READY`

Indica que o sistema está pronto.

#### Emitido por

Pode ser emitido pelo bootstrap ou por algum serviço de inicialização futura.

#### Consumido por

Atualmente não é evento central do fluxo, pois o estado `READY` é controlado pelo `StateManager`.

#### Payload sugerido

```json
{
    "message": "Sistema pronto"
}
```

#### Observações

O projeto atualmente usa principalmente `STATE_CHANGED` para comunicar transições para `READY`.

---

### 4.3 `SYSTEM_ERROR`

Indica erro sistêmico.

#### Emitido por

Qualquer serviço que deseje sinalizar uma falha crítica.

#### Consumido por

Pode ser usado futuramente por:

```txt
HealthService
Watchdog
Notificação local
```

#### Payload sugerido

```json
{
    "source": "CameraService",
    "error": "Descrição do erro",
    "timestamp": 1782150000.0
}
```

---

### 4.4 `SYSTEM_SHUTDOWN`

Indica encerramento lógico do agente.

#### Emitido por

```txt
main.py
```

#### Consumido por

Pode ser usado por serviços de auditoria, limpeza ou telemetria local.

#### Payload típico

```json
{
    "message": "Sistema encerrado"
}
```

---

## 5. Eventos de câmera

---

### 5.1 `CAMERA_STARTING`

Indica que a câmera começou o processo de inicialização.

#### Emitido por

```txt
CameraService
```

#### Consumido por

Pode ser usado por:

```txt
HealthService
DebugWindowService
Logs/auditoria
```

#### Payload sugerido

```json
{
    "camera_index": 0,
    "camera_backend": "DSHOW"
}
```

---

### 5.2 `CAMERA_STARTED`

Indica que a câmera abriu e respondeu com sucesso.

#### Emitido por

```txt
CameraService
```

#### Consumido por

```txt
main.py
HealthService
```

#### Payload típico

```json
{
    "camera_index": 0,
    "camera_backend": "DSHOW",
    "frame_width": 640,
    "frame_height": 480,
    "target_fps": 10
}
```

#### Observações

Esse evento deve ser emitido depois do warm-up da câmera.

---

### 5.3 `CAMERA_ERROR`

Indica erro de câmera.

#### Emitido por

```txt
CameraService
```

#### Consumido por

```txt
main.py
HealthService
```

#### Payload típico

```json
{
    "message": "Não foi possível abrir câmera",
    "camera_index": 0,
    "timestamp": 1782150000.0
}
```

#### Observações

Erros de câmera devem aparecer no log e podem futuramente acionar recovery automático.

---

### 5.4 `CAMERA_STOPPED`

Indica que a câmera foi encerrada.

#### Emitido por

```txt
CameraService
```

#### Consumido por

```txt
HealthService
```

#### Payload sugerido

```json
{
    "timestamp": 1782150000.0
}
```

---

## 6. Evento de frame

---

### 6.1 `FRAME_CAPTURED`

Evento emitido a cada frame capturado pela câmera.

#### Emitido por

```txt
CameraService
```

#### Consumido por

```txt
DetectionService
DebugWindowService
```

#### Payload típico

```python
{
    "frame": frame,
    "frame_count": 123,
    "timestamp": 1782150000.0
}
```

#### Observações

O campo `frame` contém uma imagem OpenCV/Numpy em memória.

Esse payload não deve ser impresso integralmente nos logs. O `EventBus` deve resumir esse campo.

---

## 7. Eventos de face

---

### 7.1 `FACE_DETECTED`

Indica que um ou mais rostos foram detectados em um frame processado.

#### Emitido por

```txt
DetectionService
```

#### Consumido por

```txt
PresenceService
RecognitionService
SecurityService
DebugWindowService
```

#### Payload típico

```python
{
    "frame_count": 123,
    "faces_count": 2,
    "faces": [
        {
            "box": {
                "x": 100,
                "y": 120,
                "width": 180,
                "height": 180
            },
            "face_image": face_image,
            "area": 32400
        },
        {
            "box": {
                "x": 330,
                "y": 130,
                "width": 160,
                "height": 160
            },
            "face_image": face_image,
            "area": 25600
        }
    ],
    "main_face": {
        "x": 100,
        "y": 120,
        "width": 180,
        "height": 180
    },
    "face_image": face_image,
    "timestamp": 1782150000.0,
    "consecutive_detections": 4,
    "is_stable": true
}
```

#### Campos importantes

```txt
faces_count
    quantidade de rostos detectados

faces
    lista de rostos detectados

main_face
    maior rosto detectado

face_image
    imagem normalizada do rosto principal

is_stable
    indica se a detecção atingiu o streak mínimo
```

#### Observações

- `RecognitionService` deve preferir a lista `faces` para reconhecer todos os rostos.
- `PresenceService` pode usar esse evento para confirmar presença.
- `SecurityService` usa `faces_count` para identificar cenário multi-face.

---

### 7.2 `FACE_LOST`

Indica que nenhum rosto foi detectado em um frame processado.

#### Emitido por

```txt
DetectionService
```

#### Consumido por

```txt
PresenceService
SecurityService
DebugWindowService
```

#### Payload típico

```json
{
    "frame_count": 456,
    "timestamp": 1782150000.0,
    "consecutive_losses": 9
}
```

#### Observações

`FACE_LOST` é um evento técnico de baixo nível.

Ações importantes não devem ser tomadas diretamente a partir dele.

A ausência real deve ser decidida pelo `PresenceService` via `USER_AWAY`.

---

## 8. Eventos de identidade

---

### 8.1 `IDENTITY_RECOGNIZED`

Indica que o rosto foi reconhecido como usuário autorizado.

#### Emitido por

```txt
RecognitionService
```

#### Consumido por

```txt
SecurityService
StartupAssistantService
DebugWindowService
main.py, opcionalmente em debug
```

#### Payload típico

```json
{
    "face_index": 0,
    "faces_count": 1,
    "predicted_user": "filipe",
    "authorized_user": "filipe",
    "confidence": 42.5,
    "authorized_threshold": 55.0,
    "unknown_threshold": 65.0,
    "frame_count": 123,
    "main_face": {
        "x": 180,
        "y": 130,
        "width": 220,
        "height": 220
    }
}
```

#### Observações

Este evento só deve ser emitido quando:

```txt
predicted_user == authorized_user
confidence <= RECOGNITION_AUTHORIZED_THRESHOLD
face_width >= MIN_AUTHORIZED_FACE_WIDTH
```

---

### 8.2 `IDENTITY_UNKNOWN`

Indica que o rosto foi classificado como desconhecido.

#### Emitido por

```txt
RecognitionService
```

#### Consumido por

```txt
SecurityService
DebugWindowService
main.py, opcionalmente em debug
```

#### Payload típico

```json
{
    "face_index": 0,
    "faces_count": 1,
    "predicted_user": "filipe",
    "authorized_user": "filipe",
    "confidence": 78.4,
    "authorized_threshold": 55.0,
    "unknown_threshold": 65.0,
    "frame_count": 123,
    "main_face": {
        "x": 230,
        "y": 150,
        "width": 180,
        "height": 180
    }
}
```

#### Observações

Como o modelo LBPH pode ter apenas o usuário autorizado cadastrado, `predicted_user` pode ser `filipe` mesmo para outra pessoa.

A decisão de desconhecido depende principalmente de `confidence`.

---

### 8.3 `IDENTITY_UNCERTAIN`

Indica que o rosto caiu na zona intermediária.

#### Emitido por

```txt
RecognitionService
```

#### Consumido por

```txt
SecurityService
DebugWindowService
main.py, opcionalmente em debug
```

#### Payload típico

```json
{
    "face_index": 0,
    "faces_count": 1,
    "predicted_user": "filipe",
    "authorized_user": "filipe",
    "confidence": 59.2,
    "authorized_threshold": 55.0,
    "unknown_threshold": 65.0,
    "frame_count": 123,
    "main_face": {
        "x": 180,
        "y": 140,
        "width": 210,
        "height": 210
    }
}
```

#### Observações

Identidade incerta:

```txt
não autoriza usuário
não aciona suspeita automaticamente
```

Esse evento é importante para evitar falsos positivos.

---

## 9. Eventos de presença

---

### 9.1 `USER_PRESENT`

Indica que o usuário foi considerado presente.

#### Emitido por

```txt
PresenceService
```

#### Consumido por

```txt
main.py
StateManager
SystemService
TeamsPresenceService
HealthService
```

#### Payload típico

```json
{
    "timestamp": 1782150000.0,
    "reason": "Presença confirmada por 3.1s"
}
```

#### Observações

Esse é um evento de negócio, mais confiável que `FACE_DETECTED`.

Ações importantes devem usar `USER_PRESENT`, não `FACE_DETECTED` bruto.

---

### 9.2 `USER_AWAY`

Indica que o usuário foi considerado ausente.

#### Emitido por

```txt
PresenceService
```

#### Consumido por

```txt
main.py
StateManager
SystemService
SecurityService
TeamsPresenceService
HealthService
```

#### Payload típico

```json
{
    "timestamp": 1782150000.0,
    "reason": "Ausência confirmada por 30.1s"
}
```

#### Observações

Esse evento pode acionar lock por ausência via `SystemService`, se configurado.

---

## 10. Eventos de segurança

---

### 10.1 `SECURITY_SUSPICIOUS`

Indica início de um cenário suspeito.

#### Emitido por

```txt
SecurityService
```

#### Consumido por

```txt
main.py
logs/auditoria
futuras notificações
```

#### Payload típico

```json
{
    "timestamp": 1782150000.0,
    "reason": "UNKNOWN_PERSON_STARTED",
    "recognition": {
        "face_index": 0,
        "confidence": 78.4,
        "main_face": {
            "x": 200,
            "y": 140,
            "width": 180,
            "height": 180
        }
    }
}
```

#### Observações

Esse evento não significa necessariamente que uma ação crítica já ocorreu.

Ele representa o início de confirmação.

---

### 10.2 `SECURITY_ALERT`

Indica confirmação de um cenário de segurança.

#### Emitido por

```txt
SecurityService
```

#### Consumido por

```txt
main.py
logs/auditoria
```

#### Payload típico

```json
{
    "timestamp": 1782150000.0,
    "reason": "UNKNOWN_PERSON_CONFIRMED",
    "unknown_duration": 3.2,
    "unknown_streak": 4,
    "recognition": {
        "face_index": 0,
        "confidence": 82.3,
        "main_face": {
            "x": 210,
            "y": 130,
            "width": 190,
            "height": 190
        }
    }
}
```

#### Observações

Se `UNKNOWN_LOCK_ENABLED=True`, esse evento pode resultar em bloqueio da estação.

---

## 11. Eventos multi-face

---

### 11.1 `MULTIPLE_FACES_DETECTED`

Indica que mais de um rosto foi detectado.

#### Emitido por

```txt
SecurityService
```

#### Consumido por

```txt
main.py
logs/auditoria
```

#### Payload típico

```json
{
    "timestamp": 1782150000.0,
    "faces_count": 2,
    "main_face": {
        "x": 100,
        "y": 120,
        "width": 220,
        "height": 220
    }
}
```

#### Observações

Esse evento indica início do fluxo multi-face, mas ainda não significa confirmação.

---

### 11.2 `MULTIPLE_FACES_CONFIRMED`

Indica que múltiplos rostos foram confirmados por tempo suficiente.

#### Emitido por

```txt
SecurityService
```

#### Consumido por

```txt
PromptService
main.py
logs/auditoria
```

#### Payload típico

```json
{
    "timestamp": 1782150000.0,
    "reason": "MULTIPLE_FACES_CONFIRMED",
    "faces_count": 2,
    "duration": 3.1,
    "main_face": {
        "x": 120,
        "y": 130,
        "width": 210,
        "height": 210
    }
}
```

#### Observações

Esse evento aciona o `PromptService`.

O comportamento padrão é perguntar ao usuário se deseja bloquear.

---

## 12. Evento de estado

---

### 12.1 `STATE_CHANGED`

Indica que o estado de alto nível do agente mudou.

#### Emitido por

```txt
StateManager
```

#### Consumido por

```txt
main.py
HealthService, se necessário
logs/auditoria
```

#### Payload típico

```json
{
    "old_state": "READY",
    "new_state": "USER_PRESENT",
    "reason": "Presença confirmada por 3.1s",
    "timestamp": 1782150000.0
}
```

#### Observações

Esse evento representa estado geral, não estados internos de cada serviço.

---

## 13. Regras de uso dos eventos

---

### 13.1 Eventos técnicos versus eventos de negócio

Eventos técnicos:

```txt
FRAME_CAPTURED
FACE_DETECTED
FACE_LOST
```

Eventos de negócio:

```txt
USER_PRESENT
USER_AWAY
IDENTITY_RECOGNIZED
IDENTITY_UNKNOWN
SECURITY_ALERT
```

Ações críticas devem preferir eventos de negócio.

Exemplo correto:

```txt
USER_AWAY
    ↓
SystemService bloqueia estação
```

Evitar:

```txt
FACE_LOST
    ↓
bloqueia estação imediatamente
```

---

### 13.2 `FACE_LOST` não deve gerar lock direto

`FACE_LOST` é instável por natureza.

Pode ocorrer por:

- virada de rosto;
- iluminação ruim;
- oclusão temporária;
- falha do detector;
- movimento rápido.

O lock deve ocorrer a partir de:

```txt
USER_AWAY
```

ou:

```txt
SECURITY_ALERT
```

---

### 13.3 `IDENTITY_UNCERTAIN` é neutro

`IDENTITY_UNCERTAIN` não deve autorizar usuário nem acionar suspeita automaticamente.

Esse evento existe para cobrir a faixa de dúvida.

---

### 13.4 Multi-face assume o fluxo quando `faces_count >= 2`

Quando há múltiplos rostos:

```txt
IDENTITY_UNKNOWN
IDENTITY_UNCERTAIN
```

não devem escalar diretamente para lock.

O fluxo correto é:

```txt
MULTIPLE_FACES_DETECTED
    ↓
MULTIPLE_FACES_CONFIRMED
    ↓
PromptService
```

---

## 14. Mapa resumido de produtores e consumidores

```txt
CameraService
    emits: CAMERA_STARTED, CAMERA_ERROR, CAMERA_STOPPED, FRAME_CAPTURED

DetectionService
    listens: FRAME_CAPTURED
    emits: FACE_DETECTED, FACE_LOST

RecognitionService
    listens: FACE_DETECTED
    emits: IDENTITY_RECOGNIZED, IDENTITY_UNKNOWN, IDENTITY_UNCERTAIN

PresenceService
    listens: FACE_DETECTED, FACE_LOST
    emits: USER_PRESENT, USER_AWAY

SecurityService
    listens: IDENTITY_RECOGNIZED, IDENTITY_UNKNOWN, IDENTITY_UNCERTAIN, FACE_DETECTED, FACE_LOST, USER_AWAY
    emits: SECURITY_SUSPICIOUS, SECURITY_ALERT, MULTIPLE_FACES_DETECTED, MULTIPLE_FACES_CONFIRMED

PromptService
    listens: MULTIPLE_FACES_CONFIRMED
    action: prompt + optional lock

SystemService
    listens: USER_PRESENT, USER_AWAY
    action: optional Windows lock

StartupAssistantService
    listens: IDENTITY_RECOGNIZED
    action: greeting + launch apps

HealthService
    listens: CAMERA_STARTED, CAMERA_STOPPED, CAMERA_ERROR, USER_PRESENT, USER_AWAY
    action: health logs

DebugWindowService
    listens: FRAME_CAPTURED, FACE_DETECTED, FACE_LOST, IDENTITY_RECOGNIZED, IDENTITY_UNKNOWN, IDENTITY_UNCERTAIN
    action: visual debug overlay

TeamsPresenceService
    listens: USER_PRESENT, USER_AWAY
    action: mock/Graph presence update

StateManager
    emits: STATE_CHANGED
```

---

## 15. Payloads grandes e logs

Alguns eventos carregam imagens em memória:

```txt
FRAME_CAPTURED.frame
FACE_DETECTED.face_image
FACE_DETECTED.faces[].face_image
```

Esses campos não devem ser impressos integralmente nos logs.

O `EventBus` deve resumir esses valores, por exemplo:

```txt
<image shape=(200, 200)>
```

---

## 16. Eventos futuros possíveis

Eventos que podem ser adicionados futuramente:

```txt
APP_LAUNCHED
APP_LAUNCH_FAILED
STARTUP_SEQUENCE_STARTED
STARTUP_SEQUENCE_COMPLETED
LOCK_TRIGGERED
LOCK_FAILED
CAMERA_RECOVERY_STARTED
CAMERA_RECOVERY_COMPLETED
FACE_TRACK_STARTED
FACE_TRACK_UPDATED
FACE_TRACK_LOST
```

Esses eventos podem melhorar auditoria, dashboard e suporte operacional.
