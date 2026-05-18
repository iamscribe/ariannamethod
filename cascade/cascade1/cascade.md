# Cascade 1 — Biology

Five organisms. Sequential pipe. Each day one full cycle.

## Daily cycle

```
SEED (day 0 = genesis.txt, day 1+ = NanoJanus 12 words + yesterday's Penelope 12 words)
  ↓
Haiku → reads seed → generates one 5-7-5 haiku
  ↓
Penelope → reads haiku → generates 12 associative words (unidirectional)
  ↓ splits:
  ├─ a) saved for Haiku TOMORROW (not today)
  ├─ b) Penelope 12 words + today's haiku → go up
  ↓
Molequla → reads (Penelope 12 words + haiku) → evolves 4 elements (2x duration)
  ↓
NanoJanus → reads (haiku + Penelope 12 words + Molequla output) → 12 words bidirectional
  ↓
NanoJanus 12 words → saved as tomorrow's seed for Haiku
```

Tomorrow's Haiku input = NanoJanus 12 words + yesterday's Penelope 12 words.

## Organisms

| Order | Organism | Architecture | Params | Output |
|-------|----------|-------------|--------|--------|
| 1 | Haiku | C, Dario Equation | 0 | one 5-7-5 haiku |
| 2 | Penelope | Python, Resonance (QKV+RRPRAM) | 19.6M | 12 associative words |
| 3 | Molequla | Go/C CGO, gradient-free | 10K-10M | 4-element evolution |
| 4 | NanoJanus | Python, Resonance (QKV+RRPRAM+Janus) | 19.6M | 12 bidirectional words |

## State files

- `seed/YYYY-MM-DD.txt` — today's seed for Haiku
- `haiku-lab/YYYY-MM-DD.txt` — today's haiku
- `penelope-lab/YYYY-MM-DD.txt` — today's 12 words
- `molequla-lab/YYYY-MM-DD/` — today's evolution logs
- `nanojanus-lab/YYYY-MM-DD.txt` — today's 12 words

---

## 2026-05-16

**seed:**  extended penelope by loaded mode: master fog sand grid rudder hawk herb 

**haiku:**
ripe space flow pattern
rhythm pulse shift dance light sound voice
path resonance path

**penelope:** extended penelope by loaded mode: resonance oath sand wall moss mesh hero 

**molequla:** 

**nanojanus:** psalm awl satin garland sand oth ers bog moss ates oar sled 

---

## 2026-05-18

**seed:**  extended penelope by loaded mode: persist sentence oasis fog island moss seal 

**haiku:**
ink star murmur in
that have i it for not on
with he as you do

**penelope:** extended penelope by loaded mode: murmur mur satin pan tin oar tic 

**molequla:** 

**nanojanus:** jamb dune solar moss ner resin dew ell sand bone satin frog 
