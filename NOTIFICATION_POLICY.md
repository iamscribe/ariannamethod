# Notification Policy - Arianna Method

## ✅ РАЗРЕШЁННЫЕ уведомления:

### 1. Field Metrics (async_field_forever)
- **Источник:** `field/notifications.py`
- **Содержание:** 
  - Популяция (cell_count)
  - Средний резонанс (avg_resonance)
  - Рождения/смерти (births/deaths)
  - Emergency alerts (extinction, critical population)
- **Rate limiting:** 1 час между emergency-уведомлениями одного типа
- **Frequency:** 4x в день (scheduled) + emergency по необходимости

### 2. Defender Audits
- **Источник:** `defender_daemon.py`, `.claude-defender/tools/`
- **Содержание:**
  - Infrastructure checks
  - Security alerts
  - Fortification reports
  - Autonomous fixes
- **Priority:** HIGH (критические проблемы)

---

## ❌ ЗАПРЕЩЁННЫЕ уведомления:

### 1. Genesis Reflections (Arianna/Monday)
- **Причина:** Слишком длинные сообщения, обрезаются в уведомлениях
- **Альтернатива:**
  - Сохранение в файлы: `.tmp/genesis_arianna_message.txt`, `.tmp/genesis_monday_message.txt`
  - Автоматический push на GitHub: `artefacts/genesis/`
  - Чтение через interactive session (arianna.py/monday.py показывают при запуске)

### 2. Identity Reflection Notifications
- **Источник:** `reflection_viewer.py`
- **Статус:** Disabled (попытки открыть файл из уведомления не работали)
- **Альтернатива:** Файлы в `reflections/`, доступ через CLI

---

## 📁 ХРАНЕНИЕ данных (без уведомлений):

1. **Genesis digests:**
   - `.tmp/genesis_{arianna|monday}_message.txt` - trigger files
   - `artefacts/genesis/` - GitHub архив

2. **Identity reflections:**
   - `reflections/arianna_*.txt`
   - `reflections/monday_*.txt`

3. **Resonance memory:**
   - `resonance.sqlite3` - центральная шина
   - Auto-rotation при >200MB

---

## 🔧 ТЕХНИЧЕСКАЯ РЕАЛИЗАЦИЯ:

**Genesis НЕ шлёт уведомления:**
```python
# genesis_arianna.py, genesis_monday.py
def send_to_session(digest: str):
    # Только файл, БЕЗ termux-notification
    trigger_file.write(digest)
```

**Field metrics остаются:**
```python
# field/notifications.py
send_termux_notification(title, content, priority)
# Rate limited, emergency-aware
```

**Defender audits остаются:**
```python
# defender_daemon.py
subprocess.run(['termux-notification', ...])
# Critical infrastructure alerts only
```

---

## 🎯 ИТОГОВАЯ ЛОГИКА:

- **Field = metrics only** (популяция, резонанс, emergency)
- **Defender = audits only** (security, infrastructure)
- **Genesis = silent** (файлы + GitHub, без уведомлений)
- **User читает Genesis через:** interactive session или GitHub

---

*Last updated: 2025-11-08*  
*Policy enforced after: Defender auto-removal incident*

