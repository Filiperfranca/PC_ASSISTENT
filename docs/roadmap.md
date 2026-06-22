# Roadmap do PresenceAgent

Este documento descreve a evolução planejada do **PresenceAgent**, organizando o que já foi entregue, o que está em validação, o que ficou bloqueado por dependências externas e quais são os próximos passos recomendados para transformar o projeto em uma solução mais robusta, operável e apresentável.

O roadmap não é apenas uma lista de tarefas. Ele serve como referência para:

- apresentar o projeto;
- orientar desenvolvimento futuro;
- priorizar melhorias;
- separar MVP, produção e evolução;
- documentar decisões técnicas;
- apoiar manutenção por TI ou outros desenvolvedores.

---

## 1. Visão geral do produto

O PresenceAgent é um agente local para Windows que usa visão computacional e eventos internos para automatizar segurança e inicialização da estação de trabalho.

A proposta principal é:

```txt
Reconhecer presença real
    ↓
Identificar o usuário autorizado
    ↓
Aplicar segurança contextual
    ↓
Executar ações locais de forma segura
```

O sistema atualmente cobre:

- captura de câmera;
- detecção facial;
- reconhecimento facial local;
- identificação de presença e ausência;
- lock automático do Windows;
- detecção de pessoas desconhecidas;
- detecção de múltiplos rostos;
- prompt de segurança;
- startup assistant;
- abertura automática de apps;
- health check;
- debug visual;
- logs;
- integração Teams preparada por provider.

---

## 2. Status atual resumido

```txt
MVP funcional: Sim
Uso local diário: Quase pronto
Reconhecimento facial: Funcional com calibração atual
Lock por ausência: Funcional
Lock por desconhecido: Funcional, se habilitado
Multi-face prompt: Funcional
Startup Assistant: Funcional
Teams Graph: Implementado parcialmente, bloqueado por política do tenant
Interface gráfica de configuração: Não implementada
Empacotamento como app: Não implementado
Serviço Windows: Não implementado
```

---

## 3. Marcos do projeto

### 3.1 Marco 1 — Core event-driven

Status:

```txt
Concluído
```

Entregas:

- `EventBus`;
- enum de eventos;
- `StateManager`;
- enum de estados;
- logger básico;
- configuração via `.env`.

Objetivo alcançado:

```txt
Criar uma base modular para comunicação entre serviços.
```

Resultado:

```txt
O projeto deixou de ser procedural e passou a ser orientado a eventos.
```

---

### 3.2 Marco 2 — Captura de câmera

Status:

```txt
Concluído
```

Entregas:

- `CameraService`;
- abertura da webcam com OpenCV;
- suporte a backend `DSHOW`;
- configuração de resolução;
- configuração de FPS;
- warm-up da câmera;
- emissão de `FRAME_CAPTURED`;
- encerramento limpo.

Objetivo alcançado:

```txt
Capturar frames continuamente e distribuir para os demais serviços.
```

---

### 3.3 Marco 3 — Detecção facial

Status:

```txt
Concluído
```

Entregas:

- `DetectionService`;
- Haar Cascade do OpenCV;
- detecção de face principal;
- detecção de múltiplos rostos;
- recorte e normalização de faces;
- envio de `face_image` para reconhecimento;
- envio de lista `faces`;
- streaks de estabilidade;
- emissão de `FACE_DETECTED` e `FACE_LOST`.

Objetivo alcançado:

```txt
Detectar rostos de forma suficientemente estável para presença e reconhecimento.
```

Limitação conhecida:

```txt
Haar Cascade pode oscilar com iluminação, distância e ângulo.
```

---

### 3.4 Marco 4 — Presença e ausência

Status:

```txt
Concluído
```

Entregas:

- `PresenceService`;
- candidato de presença;
- candidato de ausência;
- grace period;
- confirmação temporal;
- emissão de `USER_PRESENT`;
- emissão de `USER_AWAY`.

Objetivo alcançado:

```txt
Evitar que oscilações rápidas da câmera gerem ausência falsa.
```

Configuração atual recomendada:

```env
FACE_LOST_GRACE_SECONDS=12
USER_AWAY_SECONDS=30
USER_PRESENT_CONFIRM_SECONDS=3
```

---

### 3.5 Marco 5 — Lock do Windows

Status:

```txt
Concluído
```

Entregas:

- `WindowsIntegration`;
- lock via Windows API com `ctypes`;
- `SystemService`;
- lock por `USER_AWAY`;
- cooldown;
- proteção anti-loop por ausência.

Objetivo alcançado:

```txt
Bloquear a estação quando o usuário se ausenta, sem entrar em loop.
```

Configuração principal:

```env
ENABLE_WINDOWS_LOCK=True
WINDOWS_LOCK_COOLDOWN_SECONDS=120
```

---

### 3.6 Marco 6 — Health check

Status:

```txt
Concluído
```

Entregas:

- `HealthService`;
- monitoramento de estado;
- monitoramento de câmera;
- contadores de eventos;
- uptime;
- logs periódicos.

Objetivo alcançado:

```txt
Permitir observabilidade mínima do agente em execução.
```

Configuração principal:

```env
ENABLE_HEALTH_SERVICE=True
HEALTH_CHECK_INTERVAL_SECONDS=30
```

---

### 3.7 Marco 7 — Debug visual

Status:

```txt
Concluído
```

Entregas:

- `DebugWindowService`;
- janela OpenCV opcional;
- desenho de múltiplos rostos;
- labels por face;
- status de identidade;
- confidence;
- estado atual;
- quantidade de faces.

Objetivo alcançado:

```txt
Permitir calibração visual e inspeção do comportamento do agente.
```

Uso recomendado:

```env
ENABLE_DEBUG_WINDOW=True
```

apenas em desenvolvimento ou calibração.

Uso diário:

```env
ENABLE_DEBUG_WINDOW=False
```

---

### 3.8 Marco 8 — Cadastro e treino facial

Status:

```txt
Concluído
```

Entregas:

- `tools/enroll_user.py`;
- `tools/train_recognizer.py`;
- `tools/test_recognizer.py`;
- suporte a OpenCV LBPH;
- armazenamento local de imagens de treino;
- geração de modelo `lbph_model.yml`;
- geração de `labels.json`.

Objetivo alcançado:

```txt
Cadastrar o usuário autorizado e treinar um modelo local.
```

Observação importante:

```txt
Dados faciais são biométricos e não devem ser versionados.
```

Pastas protegidas:

```txt
app/data/faces/
app/data/models/
```

---

### 3.9 Marco 9 — Reconhecimento facial

Status:

```txt
Concluído
```

Entregas:

- `RecognitionService`;
- reconhecimento de todos os rostos detectados;
- classificação em autorizado, incerto e desconhecido;
- thresholds separados;
- validação de largura mínima do rosto autorizado;
- emissão de eventos de identidade.

Configuração calibrada atual:

```env
RECOGNITION_AUTHORIZED_THRESHOLD=55
RECOGNITION_UNKNOWN_THRESHOLD=65
MIN_AUTHORIZED_FACE_WIDTH=150
```

Objetivo alcançado:

```txt
Evitar aceitar pessoas desconhecidas como usuário autorizado.
```

Decisão arquitetural importante:

```txt
IDENTITY_UNCERTAIN não autoriza e não aciona suspeita automaticamente.
```

---

### 3.10 Marco 10 — Segurança contextual

Status:

```txt
Concluído
```

Entregas:

- `SecurityService`;
- detecção de desconhecido persistente;
- `SECURITY_SUSPICIOUS`;
- `SECURITY_ALERT`;
- fluxo multi-face separado;
- cooldown de prompt multi-face;
- neutralidade para identidade incerta;
- proteção contra lock indevido em cenário multi-face.

Objetivo alcançado:

```txt
Reagir a risco real sem bloquear por ruído ou incerteza.
```

Configuração principal:

```env
UNKNOWN_LOCK_ENABLED=True
UNKNOWN_CONFIRM_SECONDS=2
UNKNOWN_EVENT_STREAK=2
MIN_SECURITY_FACE_WIDTH=150
AUTHORIZED_GRACE_SECONDS=5
```

---

### 3.11 Marco 11 — Prompt multi-face

Status:

```txt
Concluído
```

Entregas:

- `PromptService`;
- prompt nativo do Windows;
- pergunta ao detectar múltiplos rostos confirmados;
- opção de bloquear a estação;
- execução em thread separada.

Objetivo alcançado:

```txt
Não bloquear automaticamente quando há mais de uma pessoa com o usuário autorizado.
```

Fluxo:

```txt
MULTIPLE_FACES_CONFIRMED
    ↓
PromptService
    ↓
Usuário decide se bloqueia
```

---

### 3.12 Marco 12 — Startup Assistant

Status:

```txt
Concluído
```

Entregas:

- `StartupAssistantService`;
- saudação configurável;
- execução única por sessão;
- abertura de apps após reconhecimento do usuário autorizado;
- `AppLauncher`;
- `startup_apps.json`.

Objetivo alcançado:

```txt
Ao iniciar o agente, reconhecer Filipe e abrir o ambiente de trabalho.
```

Apps configurados atualmente:

```txt
Microsoft Teams
SouGov no Chrome
Brave perfil MCOM
Brave perfil Pessoal
```

---

### 3.13 Marco 13 — Integração Teams

Status:

```txt
Parcial / bloqueado por política externa
```

Entregas:

- `TeamsPresenceService`;
- `TeamsProvider`;
- `MockTeamsProvider`;
- `GraphTeamsProvider`;
- estrutura para Microsoft Graph;
- teste de autenticação Graph.

Resultado:

```txt
Código preparado, mas token bloqueado por Conditional Access do tenant.
```

Decisão atual:

```env
ENABLE_TEAMS_INTEGRATION=False
TEAMS_PROVIDER=mock
```

Motivo:

```txt
Sem liberação administrativa, não há como usar Graph oficialmente.
```

Decisão de segurança:

```txt
Não usar APIs internas/não documentadas do Teams.
```

---

### 3.14 Marco 14 — Documentação inicial

Status:

```txt
Em andamento
```

Entregas já feitas:

- `README.md`;
- `docs/architecture.md`;
- `docs/events.md`;
- `docs/states.md`.

Em andamento:

- `docs/roadmap.md`.

Próximos possíveis documentos:

```txt
docs/setup.md
docs/operations.md
docs/configuration.md
docs/security.md
docs/face-recognition.md
docs/startup-assistant.md
```

---

## 4. Estado atual por área

---

## 4.1 Core

Status:

```txt
Estável
```

Componentes:

```txt
EventBus
StateManager
Config
Logger
Events
States
```

Prioridade futura:

```txt
Baixa
```

Possíveis melhorias:

- tipagem mais rígida de payloads;
- testes unitários por evento;
- event tracing opcional;
- métricas internas.

---

## 4.2 Câmera

Status:

```txt
Funcional
```

Prioridade futura:

```txt
Média
```

Possíveis melhorias:

- auto-recovery da câmera;
- fallback de backend;
- fallback de resolução;
- detecção de câmera em uso por outro app;
- evento de degradação.

---

## 4.3 Detecção facial

Status:

```txt
Funcional para MVP
```

Prioridade futura:

```txt
Média
```

Limitações:

- Haar Cascade oscila;
- pode perder rosto com ângulo/luz;
- pode detectar falso positivo;
- não possui tracking persistente.

Possíveis melhorias:

- trocar detector por modelo mais moderno;
- adicionar `FaceTrackerService`;
- melhorar seleção de rosto principal;
- aplicar suavização temporal por bounding box.

---

## 4.4 Reconhecimento facial

Status:

```txt
Funcional e calibrado
```

Prioridade futura:

```txt
Alta para robustez futura
```

Limitações:

- LBPH é simples;
- depende bastante da iluminação;
- pode confundir pessoas se thresholds estiverem largos;
- modelo com apenas um usuário sempre retorna o label mais próximo.

Possíveis melhorias:

- aumentar dataset controladamente;
- criar ferramenta de avaliação de threshold;
- gerar relatório de confidence;
- migrar para embeddings faciais modernos;
- cadastrar exemplos negativos, se abordagem futura permitir;
- criar modo de recalibração assistida.

---

## 4.5 Presença

Status:

```txt
Estável
```

Prioridade futura:

```txt
Baixa/Média
```

Possíveis melhorias:

- perfis de sensibilidade;
- modo reunião;
- modo apresentação;
- pausas temporárias;
- configuração via UI.

---

## 4.6 Segurança

Status:

```txt
Funcional
```

Prioridade futura:

```txt
Alta
```

Possíveis melhorias:

- logs mais estruturados de incidentes;
- histórico de alertas;
- exportação de eventos de segurança;
- política diferente para horário de trabalho;
- confirmação adicional antes de lock por unknown;
- integração com notificação local.

---

## 4.7 Startup Assistant

Status:

```txt
Funcional
```

Prioridade futura:

```txt
Média
```

Possíveis melhorias:

- UI para editar apps de startup;
- checar se app já está aberto;
- abrir grupos de apps por perfil;
- delays por app;
- condições por horário;
- saudação por voz mais natural;
- modo silencioso.

---

## 4.8 Teams

Status:

```txt
Mock funcional / Graph bloqueado
```

Prioridade futura:

```txt
Baixa enquanto tenant bloquear
```

Possíveis melhorias:

- manter provider Graph documentado;
- adicionar provider local para abrir Teams;
- não tentar endpoints internos;
- retomar Graph apenas se houver liberação formal.

---

## 4.9 Operação em produção

Status:

```txt
Parcial
```

Já existe:

- execução manual;
- logs;
- startup assistant;
- orientação para Task Scheduler.

Falta consolidar:

- script `start_agent.ps1` definitivo;
- criação automática da tarefa agendada;
- modo produção no `.env`;
- documentação operacional;
- log rotation.

---

## 5. Próximas prioridades recomendadas

---

## Prioridade 1 — Fechamento de produção local

Status:

```txt
Próximo passo recomendado
```

Objetivo:

```txt
Permitir que o agente rode diariamente sem intervenção manual.
```

Tarefas:

- desligar janela debug no `.env`;
- habilitar lock por unknown;
- habilitar lock por ausência;
- garantir logs em arquivo;
- criar `scripts/start_agent.ps1`;
- criar tarefa agendada no Windows;
- testar início no logon;
- documentar como parar/remover tarefa.

Configuração esperada:

```env
ENABLE_DEBUG_WINDOW=False
DEBUG_MODE=False
LOG_LEVEL=INFO
ENABLE_WINDOWS_LOCK=True
UNKNOWN_LOCK_ENABLED=True
STARTUP_OPEN_APPS_ENABLED=True
```

Critério de aceite:

```txt
Ao fazer logon no Windows, o agente inicia, reconhece Filipe, abre os apps e monitora presença sem janela de debug.
```

---

## Prioridade 2 — Limpeza e redução de ruído de logs

Status:

```txt
Recomendado após produção local
```

Objetivo:

```txt
Manter logs úteis sem excesso de mensagens repetitivas.
```

Tarefas:

- mover logs frequentes de reconhecimento para `DEBUG`;
- manter em `INFO` apenas transições relevantes;
- registrar incidentes de segurança em `WARNING`/`ERROR`;
- criar log de health periódico;
- adicionar rotação de logs.

Exemplo de mudança:

```txt
Identidade reconhecida frame a frame
    INFO -> DEBUG

SECURITY_ALERT
    permanece ERROR

USER_AWAY / USER_PRESENT
    permanece INFO
```

Critério de aceite:

```txt
Log diário legível, sem milhares de linhas desnecessárias por hora.
```

---

## Prioridade 3 — Documentação operacional

Status:

```txt
Recomendado
```

Objetivo:

```txt
Permitir que outra pessoa configure, opere e mantenha o agente.
```

Documentos sugeridos:

```txt
docs/setup.md
docs/configuration.md
docs/operations.md
docs/security.md
docs/face-recognition.md
```

Conteúdos:

- instalação;
- cadastro facial;
- treino;
- thresholds;
- uso diário;
- resolução de problemas;
- logs;
- Task Scheduler;
- privacidade;
- rollback seguro.

Critério de aceite:

```txt
Uma pessoa de TI consegue instalar e configurar o PresenceAgent seguindo a documentação.
```

---

## Prioridade 4 — Watchdog e resiliência

Status:

```txt
Futuro próximo
```

Objetivo:

```txt
Evitar que o agente pare silenciosamente.
```

Tarefas:

- detectar câmera travada;
- tentar reiniciar CameraService;
- criar evento `CAMERA_RECOVERY_STARTED`;
- criar evento `CAMERA_RECOVERY_COMPLETED`;
- reiniciar processo via Task Scheduler se morrer;
- registrar falha crítica.

Critério de aceite:

```txt
Se a câmera falhar temporariamente, o agente tenta se recuperar ou registra erro claro.
```

---

## Prioridade 5 — Face tracking

Status:

```txt
Futuro
```

Objetivo:

```txt
Manter identidade associada ao mesmo rosto entre frames.
```

Problema atual:

```txt
face_index pode inverter entre frames
```

Tarefas:

- criar `FaceTrackerService`;
- associar rostos por proximidade de bounding boxes;
- manter `track_id`;
- estabilizar labels no debug;
- melhorar fluxo multi-face.

Eventos futuros possíveis:

```txt
FACE_TRACK_STARTED
FACE_TRACK_UPDATED
FACE_TRACK_LOST
```

Critério de aceite:

```txt
Em cenário com duas pessoas, o sistema mantém identidade visual consistente por rosto.
```

---

## Prioridade 6 — Interface de configuração

Status:

```txt
Futuro
```

Objetivo:

```txt
Reduzir dependência de edição manual do .env.
```

Opções possíveis:

- interface web local;
- app desktop simples;
- painel React;
- CLI interativa.

Configurações úteis na UI:

- thresholds;
- câmera;
- debug window;
- lock por unknown;
- startup apps;
- delay de apps;
- modo produção/desenvolvimento.

Critério de aceite:

```txt
Usuário/TI consegue alterar configurações principais sem editar arquivos manualmente.
```

---

## Prioridade 7 — Empacotamento como app

Status:

```txt
Futuro
```

Objetivo:

```txt
Facilitar instalação e execução em ambiente Windows.
```

Possíveis caminhos:

- PyInstaller;
- instalador MSI;
- serviço Windows;
- aplicação com tray icon.

Tarefas:

- empacotar dependências;
- definir pasta de dados local;
- definir pasta de logs;
- lidar com atualização;
- criar atalho/startup automático;
- assinar binário, se necessário.

Critério de aceite:

```txt
PresenceAgent pode ser instalado e iniciado sem abrir terminal manualmente.
```

---

## Prioridade 8 — Melhorias de reconhecimento facial

Status:

```txt
Futuro avançado
```

Objetivo:

```txt
Melhorar precisão e reduzir dependência de thresholds manuais.
```

Possíveis caminhos:

- embeddings faciais modernos;
- ONNX Runtime;
- InsightFace ou alternativa;
- comparação vetorial;
- cadastro de múltiplos usuários autorizados;
- exemplos negativos;
- avaliação automática de threshold.

Critério de aceite:

```txt
Menos falsos positivos e falsos negativos em condições variadas.
```

---

## Prioridade 9 — Dashboard local

Status:

```txt
Futuro
```

Objetivo:

```txt
Permitir visualização clara do estado do agente.
```

Possíveis informações:

- estado atual;
- câmera online/offline;
- usuário presente/ausente;
- última identidade reconhecida;
- último alerta;
- uptime;
- erros recentes;
- config ativa;
- botão de pausar segurança.

Critério de aceite:

```txt
Usuário consegue ver rapidamente se o agente está saudável e o que ele está fazendo.
```

---

## 6. Backlog técnico

Itens técnicos sem prioridade imediata:

```txt
- adicionar testes unitários para EventBus
- testar StateManager
- testar RecognitionService com imagens fixture
- criar fixtures sintéticas para eventos
- padronizar payloads com TypedDict ou dataclasses
- adicionar mypy ou pyright
- adicionar lint/formatter
- criar Makefile ou task runner
- validar .env na inicialização
- validar startup_apps.json na inicialização
- melhorar tratamento de exceção global
- adicionar rotação de logs
- adicionar compactação/limpeza de logs antigos
```

---

## 7. Backlog de segurança

Itens relacionados a segurança:

```txt
- revisar default seguro do .env.example
- garantir UNKNOWN_LOCK_ENABLED=False no exemplo
- garantir ENABLE_WINDOWS_LOCK=False no exemplo
- não versionar dados biométricos
- não versionar cache MSAL
- documentar retenção de dados
- criar modo privacy review
- permitir apagar dados faciais localmente
- criar comando de reset de modelo
```

---

## 8. Backlog de operação

Itens para uso diário:

```txt
- start_agent.ps1 definitivo
- install_task.ps1
- uninstall_task.ps1
- status_task.ps1
- script para abrir último log
- script para acompanhar log em tempo real
- script para retreinar modelo
- script para backup local de config
```

---

## 9. Backlog de documentação

Documentos sugeridos:

```txt
README.md
    visão geral e instalação rápida

architecture.md
    arquitetura técnica

events.md
    eventos e payloads

states.md
    estados globais e internos

roadmap.md
    evolução planejada

setup.md
    instalação passo a passo

configuration.md
    explicação completa do .env

operations.md
    uso diário, logs, start/stop

security.md
    modelo de segurança e privacidade

face-recognition.md
    cadastro, treino e calibração

startup-assistant.md
    abertura de apps e rotina inicial

teams-integration.md
    providers mock/graph e limitações
```

---

## 10. Riscos conhecidos

### 10.1 Falso positivo de reconhecimento

Risco:

```txt
pessoa desconhecida ser aceita como autorizada
```

Mitigações atuais:

- threshold autorizado baixo;
- zona incerta;
- tamanho mínimo de rosto autorizado;
- unknown threshold separado;
- debug visual.

Melhorias futuras:

- modelo por embeddings;
- exemplos negativos;
- avaliação automática.

---

### 10.2 Falso lock

Risco:

```txt
sistema bloquear indevidamente
```

Mitigações atuais:

- grace period;
- confirmação por tempo;
- streaks;
- cooldown;
- anti-loop;
- prompt em multi-face;
- `UNKNOWN_LOCK_ENABLED` configurável.

---

### 10.3 Câmera indisponível

Risco:

```txt
outro app usar câmera ou driver falhar
```

Mitigações atuais:

- logs de erro;
- health check;
- backend DSHOW.

Melhorias futuras:

- auto-recovery;
- fallback de backend;
- notificação local.

---

### 10.4 Teams Graph bloqueado

Risco:

```txt
integração oficial com Teams não funcionar
```

Situação atual:

```txt
bloqueado por Conditional Access do tenant
```

Mitigação:

```txt
usar provider mock e manter código Graph preparado
```

---

### 10.5 Dados biométricos versionados por acidente

Risco:

```txt
subir imagens/modelos para Git
```

Mitigação:

```gitignore
app/data/faces/
app/data/models/
```

---

## 11. Critérios para considerar v1.0

O PresenceAgent pode ser considerado `v1.0` quando cumprir:

```txt
- inicia automaticamente com Windows
- roda sem terminal visível ou com log adequado
- debug window desligada por padrão
- lock por ausência validado
- lock por desconhecido validado
- startup assistant validado
- logs funcionais
- documentação mínima completa
- scripts de instalação/remoção da tarefa agendada
- .env.example seguro
- dados biométricos protegidos por .gitignore
```

---

## 12. Versões sugeridas

### v0.1 — Core

```txt
EventBus
StateManager
Logger
Config
```

Status:

```txt
Concluído
```

---

### v0.2 — Presença

```txt
CameraService
DetectionService
PresenceService
USER_PRESENT
USER_AWAY
```

Status:

```txt
Concluído
```

---

### v0.3 — Segurança básica

```txt
Windows lock
HealthService
DebugWindow
SystemService
```

Status:

```txt
Concluído
```

---

### v0.4 — Identidade

```txt
Enrollment
Training
RecognitionService
Authorized/Unknown/Uncertain
```

Status:

```txt
Concluído
```

---

### v0.5 — Segurança contextual

```txt
SecurityService
Multi-face
PromptService
Unknown lock
```

Status:

```txt
Concluído
```

---

### v0.6 — Startup Assistant

```txt
Greeting
AppLauncher
startup_apps.json
Abertura de apps após reconhecimento
```

Status:

```txt
Concluído
```

---

### v0.7 — Operação local

```txt
Task Scheduler
produção local
logs internos
sem debug window
scripts operacionais
```

Status:

```txt
Em andamento / próximo
```

---

### v0.8 — Documentação e suporte

```txt
README
docs técnicos
docs operacionais
troubleshooting
```

Status:

```txt
Em andamento
```

---

### v1.0 — Release operacional

```txt
instalação documentada
execução automática
segurança validada
logs confiáveis
configuração segura
```

Status:

```txt
Futuro próximo
```

---

## 13. Próximo plano de execução recomendado

Ordem sugerida:

```txt
1. Finalizar docs principais
   - architecture.md
   - events.md
   - states.md
   - roadmap.md

2. Ajustar modo produção
   - ENABLE_DEBUG_WINDOW=False
   - UNKNOWN_LOCK_ENABLED=True
   - ENABLE_WINDOWS_LOCK=True
   - DEBUG_MODE=False

3. Criar scripts operacionais
   - start_agent.ps1
   - install_task.ps1
   - uninstall_task.ps1

4. Configurar Task Scheduler
   - iniciar no logon
   - testar start/stop

5. Reduzir ruído de logs
   - reconhecimento frame a frame para DEBUG
   - manter eventos importantes em INFO/WARNING/ERROR

6. Criar documentação operacional
   - setup.md
   - operations.md
   - configuration.md

7. Rodar por alguns dias em uso real
   - ajustar thresholds
   - ajustar tempos
   - validar falsos positivos
```

---

## 14. Conclusão

O PresenceAgent já atingiu um MVP avançado.

A maior parte das funcionalidades centrais está implementada:

```txt
presença
identidade
segurança contextual
startup assistant
lock local
health/debug
```

O foco agora deve sair de criação de funcionalidades grandes e ir para:

```txt
operação
robustez
documentação
instalação
manutenção
```

A próxima grande etapa é transformar o projeto de um agente funcional em um agente confiável para uso diário.
