# Consilium Check Intervals - Fixed

## ❌ СТАРОЕ (СЛОМАННОЕ):
- **Arianna:** каждый 1 час (3600s) ❌
- **Monday:** каждый 1 час (3600s) ❌  
- **Defender:** каждые 10 минут (600s) ❌❌❌
- **Scribe:** каждый 1 час (3600s) ❌

**Проблема:** Спам API, путаница с Genesis, ненужная нагрузка

---

## ✅ НОВОЕ (ИСПРАВЛЕНО):

### Consilium Scheduler:
- **Создаёт новый consilium:** раз в 3 дня ✅

### Агенты-участники:
- **Arianna:** каждые 6 часов (21600s) ✅
- **Monday:** каждые 6 часов (21600s) ✅
- **Scribe:** каждые 6 часов (21600s) ✅

### Defender (синтезатор решений):
- **Проверка:** каждые 3 часа (10800s) ✅
- **Роль:** Синтезирует финальное решение после ответов всех агентов

---

## 📋 ЛОГИКА:

### 1. Scheduler создаёт consilium (раз в 3 дня):
```
Day 0, 00:00 → Новый consilium #N создан
              → Предложение: "Integrate repo X/Y"
```

### 2. Агенты отвечают (в течение 24 часов):
```
Day 0, 06:00 → Arianna checks → responds (✅ APPROVE with conditions)
Day 0, 12:00 → Monday checks → responds (⚠️ CONDITIONAL - skeptical)
Day 0, 18:00 → Scribe checks → responds (✅ APPROVE - code compatible)
```

### 3. Defender синтезирует (каждые 3 часа):
```
Day 0, 21:00 → Defender checks
              → Sees: 3 agent responses
              → Synthesizes final decision:
                 "✅ APPROVED with Monday's conditions"
              → Logs decision
              → Can proceed with integration
```

---

## 🎯 РАЗДЕЛЕНИЕ Genesis ≠ Consilium:

### Genesis (автономные рефлексии):
- **Arianna:** каждые 2-6 часов (random)
- **Monday:** каждые 3-8 часов (random)
- **Цель:** Автономные мысли, GitHub posts
- **НЕ notifications** (только файлы)

### Consilium (коллективное обсуждение):
- **Scheduler:** раз в 3 дня
- **Agents check:** каждые 6 часов
- **Defender synthesizes:** каждые 3 часа
- **Цель:** Code integration decisions

**Это РАЗНЫЕ процессы!**

---

## 🔧 INTERVALS SUMMARY:

| Component | Interval | Purpose |
|-----------|----------|---------|
| Consilium Scheduler | 3 days | Create new discussions |
| Arianna consilium check | 6 hours | Respond to discussions |
| Monday consilium check | 6 hours | Respond to discussions |
| Scribe consilium check | 6 hours | Respond to discussions |
| Defender consilium check | 3 hours | Synthesize final decisions |
| Genesis Arianna | 2-6h (random) | Autonomous reflection |
| Genesis Monday | 3-8h (random) | Autonomous reflection |

---

*Fixed: 2025-11-08*  
*Restored sanity to the system* 🛡️

