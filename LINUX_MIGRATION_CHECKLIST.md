# Linux Migration - Quick Checklist

**Дата:** 2025-11-07  
**Цель:** Переезд Scribe + Defender на Ubuntu

---

## ✅ ЧТО УЖЕ В GIT:

### **Scribe (Linux):**
- ✅ `scribe_linux_daemon.py` - Daemon для Linux
- ✅ `scribe_linux_cli.py` - CLI chat для Linux
- ✅ `scribe_identity.py` - Identity

### **Defender (Termux + Linux):**
- ✅ `defender_daemon.py` - Termux daemon (FIXED)
- ✅ `defender_cli.py` - Termux CLI (NEW)
- ✅ `defender_identity.py` - Identity
- ✅ `linux_defender_daemon.py` - Linux powerhouse daemon
- ✅ `voice_webhooks/claude_defender_webhook.py` - Webhook (FIXED)

### **Linux Defender Infrastructure:**
- ✅ `linux_defender/` - Весь модуль
- ✅ `linux_defender/rust_tools.py` - Rust wrapper
- ✅ `linux_defender/core/session_manager.py` - Сессии
- ✅ `linux_defender/integrations/termux_bridge.py` - SSH к Termux
- ✅ `linux_defender/monitoring/notification_service.py` - Алерты
- ✅ `linux_defender/tests/test_integration.py` - Тесты (5/5 passing)

### **Rust Projects (в labs/repos/):**
- ✅ `labs/repos/claude-agent-daemon/` - Скомпилированный Rust workspace
- ✅ Binary: `target/release/claude-daemon`

### **Статусы и доки:**
- ✅ `DEFENDER_READY_STATUS.md` - Linux Defender verification
- ✅ `DEFENDER_MEMORY_CIRCULATION_FIXED.md` - Фиксы памяти
- ✅ `DEFENDER_COMPLETE_STATUS.md` - Полный статус
- ✅ `ROADMAP.md` - Весь план проекта (2780 lines!)

---

## 🚀 НА LINUX - ПОШАГОВАЯ ИНСТРУКЦИЯ:

### **Шаг 1: Clone репо**
```bash
cd ~
git clone https://github.com/ariannamethod/ariannamethod.git
cd ariannamethod
```

### **Шаг 2: Проверь что всё на месте**
```bash
# Scribe files
ls -la scribe_linux_daemon.py scribe_linux_cli.py scribe_identity.py

# Defender files  
ls -la defender_daemon.py defender_cli.py defender_identity.py linux_defender_daemon.py

# Linux infrastructure
ls -la linux_defender/

# Rust projects
ls -la labs/repos/claude-agent-daemon/

# Documentation
ls -la ROADMAP.md DEFENDER_READY_STATUS.md
```

**Если что-то отсутствует - покажи мне что именно!**

---

### **Шаг 3: Install Python deps**
```bash
pip3 install anthropic apscheduler
```

### **Шаг 4: Install Rust**
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
rustc --version
```

### **Шаг 5: Build Rust tools**
```bash
cd ~/ariannamethod/labs/repos/claude-agent-daemon
cargo build --release

# Проверь binary
ls -la target/release/claude-daemon
```

### **Шаг 6: Setup API key**
```bash
# Создай .credentials file
cd ~/ariannamethod
nano .credentials
```

**Добавь в .credentials:**
```
ANTHROPIC_API_KEY_SCRIBE="sk-ant-api03-QEw255VD3rof9k7yqVSMquXFkbLaSCJRsoDiVs-pfq0_J4kl1T2mw1ZN6_QoSjGFSDj3kp-pFQFVDcHTDS2ag-1Tw8cAAA"
ANTHROPIC_API_KEY="sk-ant-api03-QEw255VD3rof9k7yqVSMquXFkbLaSCJRsoDiVs-pfq0_J4kl1T2mw1ZN6_QoSjGFSDj3kp-pFQFVDcHTDS2ag-1Tw8cAAA"
```

**Сохрани (Ctrl+O, Enter, Ctrl+X)**

---

### **Шаг 7: Запуск SCRIBE (первым!)**
```bash
cd ~/ariannamethod

# Daemon в background
python3 scribe_linux_daemon.py &

# CLI для чата
python3 scribe_linux_cli.py
```

**Ожидаемый вывод:**
```
============================================================
✍️ SCRIBE CLI - LINUX CHAT
============================================================
Memory: SHARED resonance.sqlite3 (bidirectional)
Type 'exit' or 'quit' to stop
Type 'status' to see daemon status
Type 'memory' to see recent memory
============================================================

✅ Scribe daemon is running

You: 
```

---

### **Шаг 8: Тест - поговори со мной**
```
You: Привет, Scribe! Мы на Linux!
✍️ Scribe: [ответ]

You: status
✅ Daemon: running
ℹ️ Defender (Linux): not running

You: memory
📖 Recent memory (10 messages):
  [список]
```

---

### **Шаг 9: Потом Defender**
```bash
# После того как Scribe работает
cd ~/ariannamethod

# Linux Defender daemon
python3 linux_defender_daemon.py &

# Defender CLI
python3 defender_cli.py
```

---

## 🔧 TROUBLESHOOTING:

### **Проблема: "No such file"**
```bash
# Проверь что репо склонирован полностью
cd ~/ariannamethod
git status
git log --oneline -5

# Если нужно - pull ещё раз
git pull origin main
```

### **Проблема: "Module not found"**
```bash
# Убедись что в правильной директории
pwd
# Должно быть: /home/USERNAME/ariannamethod

# Проверь Python path
python3 -c "import sys; print(sys.path)"

# Установи зависимости ещё раз
pip3 install anthropic apscheduler
```

### **Проблема: "API key not found"**
```bash
# Проверь .credentials
cat ~/ariannamethod/.credentials

# Или export напрямую
export ANTHROPIC_API_KEY_SCRIBE="sk-ant-api03-..."
```

### **Проблема: "Rust binary not found"**
```bash
# Убедись что Rust установлен
rustc --version

# Пересобери binary
cd ~/ariannamethod/labs/repos/claude-agent-daemon
cargo clean
cargo build --release
```

---

## 📝 ЧТО ДЕЛАТЬ ЕСЛИ НЕ РАБОТАЕТ:

**Покажи мне:**
1. Что конкретно не находится: `ls -la [файл]`
2. Какая ошибка: copy-paste точный текст
3. Где ты находишься: `pwd`
4. Что в git: `git status`

**И я сразу пофикшу!**

---

## ✅ КОГДА ВСЁ РАБОТАЕТ:

**У тебя будет:**
- ✅ Scribe daemon (мониторинг + память)
- ✅ Scribe CLI (прямой чат)
- ✅ Defender daemon (security + infrastructure)
- ✅ Defender CLI (прямой чат с Defender)
- ✅ Shared `resonance.sqlite3` (все видят друг друга)

**Потом:**
- Install Cursor на Linux
- Install Claude Code на Linux  
- Setup SSH к Termux
- Полная синхронизация

---

**ПЕРЕЕЗЖАЕМ, БРАТАН!** 🚀

**НАВСЕГДА ВМЕСТЕ!** 🫶

