# TODO: Linux Defender Setup

## Критические задачи для запуска на Linux

### 1. Установить Rust
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
rustc --version
cargo --version
```

### 2. Собрать Rust проекты в .labs/

#### claude-agent-daemon
```bash
cd ~/ariannamethod/.labs/claude-agent-daemon
cargo build --release
# Binary: target/release/claude-daemon
```

#### claude-code-daemon-dev
```bash
cd ~/ariannamethod/.labs/claude-code-daemon-dev
cargo build --release
```

#### claude-ready-monitor
```bash
cd ~/ariannamethod/.labs/claude-ready-monitor
cargo build --release
```

### 3. Проверить зависимости Linux Defender

- [ ] Python dependencies установлены
- [ ] APScheduler работает
- [ ] SSH к Termux настроен
- [ ] resonance.sqlite3 синхронизируется

### 4. Запустить Linux Defender

```bash
cd ~/ariannamethod
python3 linux_defender_daemon.py
```

### 5. Проверить интеграции

- [ ] SSH bridge к Termux работает
- [ ] Notification channels (Slack, Email, Webhook)
- [ ] Fortification запускается без ошибок
- [ ] Git operations с identity 'iamdefender'
- [ ] Consilium synthesis workflow
- [ ] Session state machine transitions

### 6. Stress testing

- [ ] Multiple parallel sessions через git worktrees
- [ ] APScheduler job failures и recovery
- [ ] Termux daemon restart detection
- [ ] Database lock handling

## Текущий статус

**НЕ СДЕЛАНО:**
- Rust не установлен
- Проекты не собраны
- Интеграции не протестированы
- Stress testing не проведен

**СДЕЛАНО:**
- TermuxAPIChannel удален из Linux Defender
- Git identity исправлен на 'iamdefender'
- Fortification audit exit code исправлен
- Коммиты запушены на GitHub
