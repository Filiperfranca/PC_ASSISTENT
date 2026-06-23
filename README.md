# PresenceAgent — MCOM

> Agente local de presença, reconhecimento facial e segurança contextual para estações Windows do Ministério das Comunicações.

Este repositório documenta o **PresenceAgent**, uma solução local em validação no âmbito do **Ministério das Comunicações (MCOM)** para apoio à segurança da estação de trabalho, automação de início de expediente e controle contextual de presença.

Este documento é direcionado à **equipe de TI, suporte técnico, segurança da informação e gestores responsáveis pela avaliação institucional da solução**.

Ele não é um guia para alteração de código-fonte. O código da aplicação já possui uma estrutura funcional. As orientações abaixo tratam de **entendimento, operação, cadastro, treinamento, segurança, dados tratados, procedimentos e próximos passos institucionais**.

---

## 1. Visão geral

O **PresenceAgent** é executado localmente na estação Windows do usuário autorizado. Ele utiliza a webcam da estação para detectar presença, reconhecer o usuário autorizado e executar ações locais de acordo com regras configuradas.

Em termos práticos, o agente permite:

- identificar se há uma pessoa diante da estação;
- reconhecer se essa pessoa é o usuário autorizado;
- classificar leituras como autorizado, incerto ou desconhecido;
- abrir aplicativos institucionais após reconhecimento do usuário autorizado;
- bloquear a estação em cenários configurados de ausência ou risco;
- registrar logs operacionais para diagnóstico;
- permitir cadastro, retreinamento e limpeza de dados biométricos por meio de menu administrativo.

A solução foi construída para funcionar **localmente**, sem depender de serviço externo para o reconhecimento facial.

---

## 2. Escopo atual no MCOM

O PresenceAgent, no estado atual, deve ser tratado como:

```txt
MVP técnico funcional
POC institucional controlada
base para avaliação de segurança, LGPD e operação de TI
```

Ele ainda não deve ser considerado uma solução institucional final para distribuição ampla sem as próximas etapas de governança, proteção de armazenamento, criptografia, ACL, auditoria e validação formal.

### Estado atual

```txt
Reconhecimento facial local: funcional
Cadastro facial local: funcional
Treinamento local: funcional
Menu administrativo: funcional
Execução automática no Windows: funcional via Agendador de Tarefas
Startup Assistant: funcional
Apagamento de imagens brutas pós-treinamento: disponível via menu
Logs operacionais: funcionais
Criptografia do modelo biométrico: planejada
Armazenamento em ProgramData com ACL institucional: planejado
Auditoria administrativa em SQLite: planejada
Homologação LGPD institucional: pendente
```

---

## 3. O que o agente faz

### 3.1 Detecção de presença

O agente monitora a webcam para identificar se existe um rosto diante da estação.

A presença física é tratada separadamente da identidade. Isso significa que o sistema pode detectar que existe alguém na frente da máquina sem necessariamente considerar essa pessoa como usuário autorizado.

### 3.2 Reconhecimento do usuário autorizado

O reconhecimento facial atual utiliza OpenCV LBPH.

O sistema trabalha com três faixas:

```txt
Verde / autorizado
    leitura compatível com o usuário autorizado

Amarelo / incerto
    leitura insuficiente para autorizar e insuficiente para acusar desconhecido

Vermelho / desconhecido
    leitura considerada incompatível com o usuário autorizado
```

No modelo LBPH, quanto menor o valor de `confidence`, melhor a correspondência.

Configuração validada após retreinamento recente:

```env
RECOGNITION_AUTHORIZED_THRESHOLD=55
RECOGNITION_UNKNOWN_THRESHOLD=65
```

Interpretação operacional:

```txt
confidence <= 55
    usuário autorizado

56 <= confidence <= 64
    identidade incerta

confidence >= 65
    desconhecido
```

A identidade incerta é neutra: não autoriza o usuário e não gera bloqueio automaticamente.

### 3.3 Startup Assistant

Após reconhecer o usuário autorizado, o agente pode abrir aplicativos definidos pela configuração local, como Teams, navegador, sistemas internos ou páginas institucionais.

Esse fluxo roda uma vez por sessão, conforme configuração.

### 3.4 Bloqueio da estação

O agente pode bloquear a estação Windows quando:

- o usuário é considerado ausente por tempo configurado;
- uma pessoa desconhecida é detectada de forma persistente;
- há múltiplos rostos e o usuário confirma o bloqueio, quando aplicável.

O bloqueio por desconhecido só deve permanecer habilitado após calibração adequada do modelo facial.

---

## 4. O que o agente não faz

O PresenceAgent, no estado atual:

- não envia imagens faciais para nuvem;
- não utiliza serviço externo para reconhecimento facial;
- não grava vídeo;
- não salva frames durante a execução normal;
- não substitui política institucional de segurança;
- não substitui controles de acesso do Windows;
- não é, sozinho, uma solução completa de conformidade LGPD;
- não deve ser administrado por usuário comum.

---

## 5. Execução no Windows

O agente principal é executado por:

```txt
main.py
```

No ambiente MCOM atual, a inicialização automática é feita pelo **Agendador de Tarefas do Windows**, executando:

```txt
.venv\Scripts\pythonw.exe main.py
```

O uso de `pythonw.exe` permite execução em segundo plano, sem janela de terminal.

### Observação sobre dois processos pythonw.exe

Em ambiente virtual Python no Windows, pode aparecer uma cadeia de processos semelhante a:

```txt
.venv\Scripts\pythonw.exe
    ↓
Python314\pythonw.exe
```

Isso não significa, necessariamente, duas instâncias reais do PresenceAgent. O critério correto de validação é o log: deve existir apenas uma sequência real de inicialização do agente.

O agente possui proteção de instância única via mutex do Windows:

```txt
Single instance mutex adquirido com sucesso: Local\PresenceAgent
```

---

## 6. Menu administrativo

O menu administrativo fica em:

```txt
tools/admin_menu.py
```

Ele é destinado à TI ou suporte autorizado.

Executar:

```powershell
python tools/admin_menu.py
```

O menu não inicia com o Windows e não é utilizado pelo usuário comum.

### Funções disponíveis

```txt
1. Ver status do ambiente
2. Cadastrar / atualizar rosto do usuário
3. Treinar modelo facial
4. Testar reconhecedor facial
5. Validar startup_apps.json
6. Abrir pasta de logs
7. Abrir log mais recente
8. Encerrar PresenceAgent em execução
9. Remover amostras faciais de um usuário
10. Apagar TODOS os dados biométricos locais
11. Exibir relatório de prontidão LGPD
```

### Identificador do usuário

O cadastro facial deve utilizar um identificador institucional, por exemplo:

```txt
login institucional
matrícula
identificador interno definido pela TI
```

Evitar uso de nome completo no caminho dos arquivos.

Exemplo:

```txt
filipe.franca
joao.silva
matricula123456
```

Após o cadastro, o menu pode atualizar o valor `AUTHORIZED_USER` no `.env` para garantir que o agente reconheça o identificador correto.

---

## 7. Cadastro facial

O cadastro é feito pela TI por meio do menu administrativo ou, quando necessário, por script operacional já existente.

### Pelo menu

```powershell
python tools/admin_menu.py
```

Selecionar:

```txt
2. Cadastrar / atualizar rosto do usuário
```

Informar o identificador institucional do usuário autorizado.

Quantidade recomendada de amostras:

```txt
300 imagens
```

### Orientações para captura

A qualidade do cadastro influencia diretamente a segurança do sistema.

Capturar:

```txt
rosto de frente
meio de lado
olhando à esquerda
olhando à direita
olhando levemente para baixo
olhando levemente para cima
iluminação real da estação
expressões naturais
mão próxima ao rosto, sem cobrir completamente
variações reais de uso diário
```

Evitar:

```txt
imagem muito escura
imagem borrada
rosto cortado
rosto muito pequeno
mão cobrindo metade do rosto
outras pessoas no enquadramento
```

### Resultado esperado após bom treinamento

Com treinamento adequado, o comportamento esperado é:

```txt
Usuário autorizado em diferentes ângulos: confidence abaixo de 55
Pessoa desconhecida: confidence acima de 65
```

---

## 8. Treinamento do modelo

O treinamento gera o modelo usado pelo agente para reconhecer o usuário autorizado.

Arquivos gerados atualmente:

```txt
app/data/models/lbph_model.yml
app/data/models/labels.json
```

Após o treinamento, o menu administrativo oferece a opção de apagar as imagens faciais brutas.

Essa limpeza é recomendada como prática de segurança.

Fluxo recomendado:

```txt
1. Cadastrar rosto
2. Treinar modelo
3. Testar reconhecimento
4. Validar comportamento
5. Apagar imagens brutas
6. Manter apenas o modelo treinado
```

---

## 9. Dados tratados

### 9.1 Imagens faciais brutas

Durante o cadastro, imagens faciais são salvas temporariamente em:

```txt
app/data/faces/<identificador>/
```

Essas imagens são sensíveis e devem ser removidas após o treinamento e validação do modelo.

### 9.2 Modelo facial treinado

O modelo treinado fica em:

```txt
app/data/models/lbph_model.yml
app/data/models/labels.json
```

O modelo não é uma fotografia visualizável do rosto, mas é derivado biométrico e deve continuar sendo tratado como dado sensível.

### 9.3 Logs

Logs ficam em:

```txt
logs/
```

Eles podem conter:

```txt
horário de execução
estado do agente
eventos de presença
eventos de reconhecimento
valores de confidence
eventos de segurança
erros técnicos
```

Logs não devem conter:

```txt
fotos
frames
vídeos
imagens da webcam
```

---

## 10. Segurança e LGPD

O PresenceAgent utiliza reconhecimento facial e, portanto, trata dados biométricos.

Para uso institucional, isso exige avaliação de:

```txt
finalidade
necessidade
proporcionalidade
base legal
controle de acesso
retenção
exclusão
transparência
auditoria
procedimento de incidente
```

### Situação atual

```txt
Processamento local: sim
Envio para nuvem: não, por padrão
Imagens brutas pós-treino: podem ser apagadas pelo menu
Modelo criptografado: ainda não
ACL institucional automatizada: ainda não
Auditoria administrativa persistente: ainda não
```

### Evolução planejada

```txt
Mover dados para C:\ProgramData\PresenceAgent
Aplicar ACL restrita
Criptografar modelo com DPAPI
Manter somente arquivos .enc
Registrar ações administrativas em audit.sqlite
Separar logs operacionais e logs sensíveis
Definir política de retenção
Formalizar documentação LGPD
```

---

## 11. Armazenamento atual

No MVP atual, os dados ficam dentro da pasta do projeto:

```txt
app/data/faces/
app/data/models/
app/data/runtime/
logs/
```

Para avaliação institucional ampla, a proposta futura é migrar para:

```txt
C:\ProgramData\PresenceAgent\
```

Estrutura futura prevista:

```txt
C:\ProgramData\PresenceAgent\
├── config\
├── models\
├── logs\
├── runtime\
├── audit\
└── temp\
```

---

## 12. Apagamento de imagens brutas

O menu administrativo já permite apagar imagens brutas após treinamento.

Essa ação remove:

```txt
app/data/faces/<usuario>/*.jpg
```

E mantém:

```txt
app/data/models/lbph_model.yml
app/data/models/labels.json
```

Isso reduz a exposição dos dados mais diretamente identificáveis.

Importante: o modelo treinado ainda deve ser protegido.

---

## 13. Inicialização automática

A inicialização automática deve ser configurada pela TI no Agendador de Tarefas.

Configuração recomendada:

```txt
Nome da tarefa:
PresenceAgent

Disparador:
Ao fazer logon do usuário autorizado

Programa:
<PASTA_DO_PROJETO>\.venv\Scripts\pythonw.exe

Argumentos:
main.py

Iniciar em:
<PASTA_DO_PROJETO>

Regra de múltiplas instâncias:
Não iniciar uma nova instância
```

A tarefa deve ser configurada para o usuário específico da estação, não para todos os usuários.

---

## 14. Operação diária

### Usuário final

O usuário final não deve executar comandos manualmente.

Fluxo esperado:

```txt
Usuário faz logon no Windows
↓
Agendador inicia PresenceAgent
↓
Agente reconhece usuário autorizado
↓
Startup Assistant abre aplicativos configurados
↓
Agente monitora presença e segurança
```

### TI / suporte autorizado

A TI utiliza o menu administrativo quando precisar:

```txt
cadastrar usuário
recadastrar rosto
treinar modelo
testar reconhecimento
limpar imagens brutas
apagar dados biométricos locais
consultar logs
encerrar agente em execução
```

---

## 15. Procedimentos operacionais

### 15.1 Recadastro de rosto

```txt
1. Abrir menu administrativo
2. Cadastrar / atualizar rosto do usuário
3. Treinar modelo facial
4. Testar reconhecedor
5. Validar confidence do usuário e de pessoa não autorizada
6. Apagar imagens brutas após validação
7. Reiniciar PresenceAgent
```

### 15.2 Troca de computador

Procedimento recomendado:

```txt
1. Apagar dados biométricos locais no computador antigo
2. Instalar/configurar PresenceAgent no novo computador
3. Cadastrar novamente o usuário autorizado
4. Treinar novo modelo local
5. Apagar imagens brutas
6. Configurar Agendador de Tarefas
```

Evitar copiar modelos biométricos entre computadores sem procedimento institucional aprovado.

### 15.3 Desativação

```txt
1. Encerrar PresenceAgent
2. Apagar dados biométricos locais pelo menu
3. Remover tarefa do Agendador, se aplicável
4. Registrar ação conforme procedimento institucional
```

---

## 16. Configurações principais

Arquivo:

```txt
.env
```

Principais chaves:

```env
AUTHORIZED_USER=identificador.institucional

ENABLE_FACE_RECOGNITION=True
RECOGNITION_AUTHORIZED_THRESHOLD=55
RECOGNITION_UNKNOWN_THRESHOLD=65
MIN_AUTHORIZED_FACE_WIDTH=150

ENABLE_SECURITY_SERVICE=True
UNKNOWN_LOCK_ENABLED=True
UNKNOWN_CONFIRM_SECONDS=3
UNKNOWN_EVENT_STREAK=3
AUTHORIZED_GRACE_SECONDS=10

ENABLE_WINDOWS_LOCK=True
ENABLE_STARTUP_ASSISTANT=True
ENABLE_DEBUG_WINDOW=False
LOG_LEVEL=INFO
```

Durante calibração, a TI pode manter:

```env
UNKNOWN_LOCK_ENABLED=False
ENABLE_DEBUG_WINDOW=True
```

Para uso normal:

```env
UNKNOWN_LOCK_ENABLED=True
ENABLE_DEBUG_WINDOW=False
```

---

## 17. Logs e diagnóstico

Abrir menu:

```powershell
python tools/admin_menu.py
```

Opções úteis:

```txt
6. Abrir pasta de logs
7. Abrir log mais recente
```

Verificar no log:

```txt
Single instance mutex adquirido com sucesso
CameraService iniciado com sucesso
RecognitionService iniciado com sucesso
PresenceAgent rodando
```

Eventos de interesse:

```txt
IDENTITY_RECOGNIZED
IDENTITY_UNCERTAIN
IDENTITY_UNKNOWN
SECURITY_SUSPICIOUS
SECURITY_ALERT
USER_PRESENT
USER_AWAY
```

---

## 18. Boas práticas antes de push no Git

Nunca enviar para o repositório:

```txt
.env
logs/
app/data/faces/
app/data/models/
app/data/runtime/
app/config/startup_apps.json
```

Esses itens podem conter configuração local, logs ou dados biométricos.

O repositório deve conter apenas exemplos e código:

```txt
.env.example
app/config/startup_apps.example.json
README.md
docs/
app/
tools/
```

Verificar antes de push:

```powershell
git status
```

---

## 19. Troubleshooting

### Agente não inicia

Verificar:

```txt
Agendador de Tarefas
Programa pythonw.exe
Argumento main.py
Campo Iniciar em
Logs
```

### Câmera não abre

Verificar:

```txt
CAMERA_INDEX
CAMERA_BACKEND=DSHOW
outro aplicativo usando webcam
permissão de câmera do Windows
```

### Usuário autorizado aparece como incerto

Ação recomendada:

```txt
recadastrar com mais ângulos
retreinar modelo
validar threshold
```

### Pessoa desconhecida não vira vermelho

Ação recomendada:

```txt
validar treinamento
verificar RECOGNITION_UNKNOWN_THRESHOLD
realizar teste com pessoa não autorizada
```

### Bloqueio indevido

Durante calibração:

```env
UNKNOWN_LOCK_ENABLED=False
```

Depois validar logs e ajustar treinamento.

### Erro `_reset_unknown_tracking`

Se aparecer:

```txt
SecurityService object has no attribute _reset_unknown_tracking
```

Corrigir chamada antiga no `SecurityService` para:

```python
self._reset_unknown_suspicion("Usuário autorizado reconhecido")
```

---

## 20. Limitações atuais

- Reconhecimento atual baseado em LBPH.
- Foco atual em uma estação com um usuário autorizado principal.
- Modelo ainda não criptografado em repouso.
- Dados ainda não migrados para ProgramData.
- ACL institucional ainda não automatizada.
- Auditoria administrativa ainda não persistida em SQLite.
- Menu administrativo ainda depende de execução manual autorizada.
- Homologação LGPD institucional ainda pendente.

---

## 21. Próximas evoluções

### Segurança de dados

```txt
Mover dados para ProgramData
Aplicar ACL restrita
Criptografar modelo com DPAPI
Apagar modelo puro após criptografia
```

### Auditoria

```txt
Criar audit.sqlite
Registrar ações administrativas
Registrar recadastro
Registrar treino
Registrar exclusão de biometria
```

### Administração

```txt
Melhorar menu administrativo
Criar modo institucional
Criar documentação de operação
Criar procedimento de incidente
```

### Reconhecimento

```txt
Avaliar migração de LBPH para embeddings faciais
Melhorar separação autorizado/desconhecido
Reduzir falsos positivos
```

---

## 22. Conclusão

O PresenceAgent já possui uma base funcional para uso controlado no MCOM como MVP técnico.

Ele entrega:

```txt
detecção de presença
reconhecimento facial local
startup assistido
bloqueio contextual
menu administrativo
apagamento de imagens brutas
execução automática local
```

Para evolução institucional, os próximos passos devem priorizar:

```txt
proteção de armazenamento
criptografia
auditoria
ACL
governança LGPD
documentação operacional formal
```

Este README deve ser usado como documento inicial de entendimento e operação para a equipe técnica do MCOM.
