# Rust Binary Tools for Mac/Linux Daemon

## What's This?

Real compiled Rust binaries for high-performance file operations.

**NO Python fallbacks. NO placeholders. REAL RUST ONLY.**

## Binaries

- `file-search/` - Fuzzy file search using nucleo-matcher (same as ripgrep uses)

## Building on New System

### 1. Install Rust

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env
```

### 2. Compile file-search

```bash
cd mac_daemon/rust_bins/file-search
cargo build --release
```

Binary will be at: `target/release/codex-file-search`

### 3. Test

```bash
cd mac_daemon
python3 test_rust_tools.py
```

**Must pass 10/10 tests.**

## Source

Original source: `postcodex/codex-rs/file-search/`

Copied as standalone package to avoid broken workspace dependencies.

## Why Not Python?

Python's `rglob()` is slow. Rust's `ignore` crate (from ripgrep) + `nucleo-matcher` is **10-100x faster** on large repos.

Real performance, real tools, no theatre.

