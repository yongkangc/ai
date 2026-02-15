# Rust Systems Engineering - Technical Reference

Deep technical reference for high-performance Rust systems programming with Reth patterns.

## Table of Contents
1. [Memory Optimization Techniques](#memory-optimization-techniques)
2. [Reth Architecture Deep Dive](#reth-architecture-deep-dive)
3. [Async Runtime Optimization](#async-runtime-optimization)
4. [Lock-Free Programming](#lock-free-programming)
5. [SIMD & Vectorization](#simd--vectorization)
6. [Cache Optimization](#cache-optimization)
7. [Profiling Workflows](#profiling-workflows)
8. [Production Readiness](#production-readiness)

---

## Memory Optimization Techniques

### Arena Allocators

Arena allocators (bump allocators) provide near-zero-cost allocation for objects with the same lifetime:

```rust
use bumpalo::Bump;

fn process_batch(items: &[Input]) -> Vec<Output> {
    let arena = Bump::new();

    // All allocations in this arena are freed together
    items.iter().map(|item| {
        let temp = arena.alloc(expensive_intermediate(item));
        process(temp)
    }).collect()
    // arena dropped here - all memory freed at once
}
```

**When to use**: Processing batches where intermediate allocations share a lifetime.

**Trade-offs**: Cannot free individual objects; memory grows monotonically until arena is dropped.

### SmallVec for Small Collections

`SmallVec` stores small collections inline, avoiding heap allocation:

```rust
use smallvec::{SmallVec, smallvec};

// Stack-allocates up to 8 elements
type FastVec<T> = SmallVec<[T; 8]>;

fn collect_recent_blocks(count: usize) -> FastVec<BlockHash> {
    // Most queries are < 8 blocks, so this typically stays on stack
    let mut hashes = smallvec![];
    for i in 0..count.min(8) {
        hashes.push(get_block_hash(i));
    }
    hashes
}
```

**Rule of thumb**: Use `SmallVec` when:
- Typical size ≤ 8-16 elements
- T is small (< 64 bytes)
- Collection is short-lived

### Copy-on-Write with Cow

Delay cloning until mutation is required:

```rust
use std::borrow::Cow;

fn normalize_address(addr: &str) -> Cow<str> {
    if addr.starts_with("0x") {
        Cow::Borrowed(addr) // No allocation
    } else {
        Cow::Owned(format!("0x{}", addr)) // Allocate only when needed
    }
}
```

### Object Pooling

Reuse expensive objects instead of allocating:

```rust
use once_cell::sync::Lazy;
use std::sync::Mutex;

static BUFFER_POOL: Lazy<Mutex<Vec<Vec<u8>>>> =
    Lazy::new(|| Mutex::new(Vec::new()));

fn get_buffer() -> Vec<u8> {
    BUFFER_POOL.lock().unwrap().pop()
        .unwrap_or_else(|| Vec::with_capacity(4096))
}

fn return_buffer(mut buf: Vec<u8>) {
    buf.clear();
    BUFFER_POOL.lock().unwrap().push(buf);
}
```

### Zero-Copy Parsing

Parse without allocating intermediate strings:

```rust
// Bad: allocates String
fn parse_hex_bad(s: &str) -> u64 {
    let stripped = s.trim_start_matches("0x"); // No allocation (string slice)
    u64::from_str_radix(stripped, 16).unwrap()
}

// Good: zero-copy
fn parse_hex_good(s: &str) -> u64 {
    let bytes = s.as_bytes();
    let start = if bytes.starts_with(b"0x") { 2 } else { 0 };
    u64::from_str_radix(&s[start..], 16).unwrap()
}
```

---

## Reth Architecture Deep Dive

### Staged-Sync Implementation

Reth's staged-sync breaks blockchain synchronization into independent stages:

**Stage 1: Headers Download**
- Download block headers from network
- Verify proof-of-work / proof-of-stake
- Build header chain skeleton

**Stage 2: Bodies Download**
- Fetch transaction bodies for verified headers
- Validate transaction list against header roots
- Store bodies in database

**Stage 3: Sender Recovery**
- Recover sender addresses from transaction signatures
- Computationally expensive (ECDSA verification)
- Parallelizable across transactions

**Stage 4: Execution**
- Execute transactions in EVM
- Update state trie
- Verify state roots

**Stage 5: Pruning & Indexing**
- Remove historical data based on pruning rules
- Build secondary indexes for RPC queries

**Key advantages**:
- Each stage optimized independently
- Parallelization opportunities at stage and within-stage level
- Graceful interruption and resumption
- Clear metrics per stage

### MDBX Database Patterns

**Read Patterns**:
```rust
// Sequential reads with cursor
let mut cursor = tx.cursor::<Table>()?;
while let Some((key, value)) = cursor.next()? {
    process(key, value);
}

// Random reads
let value = tx.get::<Table>(key)?;
```

**Write Patterns**:
```rust
// Batch writes in transaction
let tx = db.begin_write()?;
for (key, value) in batch {
    tx.put::<Table>(key, value)?;
}
tx.commit()?;
```

**Schema Design Principles**:
1. **Denormalization**: Store data in query-optimized form
2. **Key ordering**: Design keys for range scans
3. **Table splitting**: Separate hot and cold data
4. **Compression**: Use compact encodings for large values

**Example: Block Storage**
```rust
// Separate tables for different access patterns
struct BlockHeader;  // Table: BlockNumber -> Header
struct BlockBody;    // Table: BlockNumber -> Transactions
struct TxIndex;      // Table: TxHash -> (BlockNumber, TxIndex)

// Hot path: latest blocks
// Cold path: historical data (can be on slower storage)
```

### Component Isolation

Each Reth component is designed for standalone use:

**Primitives**:
```rust
// reth-primitives: Core types with no I/O
pub struct Block {
    pub header: Header,
    pub body: Vec<Transaction>,
}

// Serialization formats
impl Block {
    pub fn encode(&self) -> Vec<u8>;
    pub fn decode(data: &[u8]) -> Result<Self>;
}
```

**Database Abstraction**:
```rust
// reth-db: Database traits, not tied to MDBX
pub trait Database {
    fn get(&self, key: &[u8]) -> Result<Option<Vec<u8>>>;
    fn put(&mut self, key: &[u8], value: &[u8]) -> Result<()>;
}

// Implementations: MDBX, in-memory, test doubles
```

---

## Async Runtime Optimization

### Tokio Tuning

**Worker Thread Configuration**:
```rust
use tokio::runtime::Builder;

let runtime = Builder::new_multi_thread()
    .worker_threads(num_cpus::get())  // Match CPU cores
    .thread_name("reth-worker")
    .enable_all()
    .build()?;
```

**Task Spawning Strategy**:
```rust
// CPU-bound work: use spawn_blocking
let hash = tokio::task::spawn_blocking(|| {
    expensive_hash_computation(data)
}).await?;

// I/O-bound work: regular spawn
tokio::spawn(async move {
    fetch_from_network(peer).await
});
```

**Work-Stealing Efficiency**:
- Keep tasks small (< 100ms)
- Avoid blocking operations in async contexts
- Use channels for communication between tasks

### Async Batching

Amortize per-request overhead:

```rust
use tokio::sync::mpsc;

async fn batch_processor(mut rx: mpsc::Receiver<Request>) {
    let mut batch = Vec::new();

    loop {
        // Collect up to 100 items or wait 10ms
        tokio::select! {
            Some(req) = rx.recv() => {
                batch.push(req);
                if batch.len() >= 100 {
                    process_batch(&batch).await;
                    batch.clear();
                }
            }
            _ = tokio::time::sleep(Duration::from_millis(10)) => {
                if !batch.is_empty() {
                    process_batch(&batch).await;
                    batch.clear();
                }
            }
        }
    }
}
```

---

## Lock-Free Programming

### Atomic Operations

Use atomics instead of mutexes for simple counters:

```rust
use std::sync::atomic::{AtomicU64, Ordering};

struct Metrics {
    requests: AtomicU64,
    errors: AtomicU64,
}

impl Metrics {
    fn record_request(&self) {
        self.requests.fetch_add(1, Ordering::Relaxed);
    }

    fn record_error(&self) {
        self.errors.fetch_add(1, Ordering::Relaxed);
    }
}
```

**Ordering guidelines**:
- `Relaxed`: Counters, statistics (no ordering guarantees)
- `Acquire/Release`: Lock-free data structures
- `SeqCst`: When in doubt (strongest guarantees, slowest)

### Lock-Free Data Structures

Use `crossbeam` for production-grade lock-free structures:

```rust
use crossbeam::queue::ArrayQueue;

// Bounded lock-free queue
let queue = ArrayQueue::new(1000);

// Producer (no locks)
queue.push(item).ok();

// Consumer (no locks)
if let Some(item) = queue.pop() {
    process(item);
}
```

**Trade-offs**:
- Faster than mutexes under contention
- More complex to reason about
- May waste CPU on spinning
- Use when profiling shows lock contention

---

## SIMD & Vectorization

### Explicit SIMD with std::simd

```rust
#![feature(portable_simd)]
use std::simd::{u32x8, SimdUint};

fn sum_array_simd(data: &[u32]) -> u32 {
    let (chunks, remainder) = data.as_chunks::<8>();

    let mut sum = u32x8::splat(0);
    for chunk in chunks {
        sum += u32x8::from_array(*chunk);
    }

    sum.reduce_sum() + remainder.iter().sum::<u32>()
}
```

**When to use SIMD**:
- Operating on large arrays of numeric data
- Operations are data-parallel (no dependencies)
- Data is contiguous in memory
- Profiling shows computation bottleneck

### Auto-Vectorization

Help LLVM auto-vectorize:

```rust
// Good: LLVM can vectorize
fn scale_slice(data: &mut [f32], factor: f32) {
    for x in data.iter_mut() {
        *x *= factor;
    }
}

// Bad: bounds checks prevent vectorization
fn scale_slice_bad(data: &mut Vec<f32>, factor: f32) {
    for i in 0..data.len() {
        data[i] *= factor;  // Bounds check on each iteration
    }
}
```

---

## Cache Optimization

### Cache Line Awareness

Modern CPUs have 64-byte cache lines. Avoid false sharing:

```rust
use std::sync::atomic::AtomicU64;

// Bad: false sharing (both on same cache line)
struct CountersBad {
    counter_a: AtomicU64,
    counter_b: AtomicU64,
}

// Good: separate cache lines
#[repr(align(64))]
struct CachePadded<T>(T);

struct CountersGood {
    counter_a: CachePadded<AtomicU64>,
    counter_b: CachePadded<AtomicU64>,
}
```

### Structure of Arrays (SoA)

Improve cache locality for columnar access:

```rust
// Array of Structs (AoS): poor cache locality
struct Transaction {
    hash: [u8; 32],
    from: Address,
    to: Address,
    value: u64,
}
let txs: Vec<Transaction> = ...;

// Structure of Arrays (SoA): better cache locality
struct Transactions {
    hashes: Vec<[u8; 32]>,
    froms: Vec<Address>,
    tos: Vec<Address>,
    values: Vec<u64>,
}

// Iterating over values is cache-friendly
for value in &txs.values {
    process(value);
}
```

**Use SoA when**: Frequently iterating over subset of fields.

---

## Profiling Workflows

### Step 1: Identify Hotspots

```bash
# CPU flamegraph
cargo flamegraph --bin my-app -- --workload large

# Look for:
# - Wide bars (time-consuming functions)
# - Tall stacks (deep call chains to inline)
# - Unexpected functions (allocation, locking)
```

### Step 2: Measure Allocations

```bash
# Linux: heaptrack
heaptrack ./target/release/my-app
heaptrack_gui heaptrack.my-app.*.gz

# macOS: Instruments
cargo instruments --release --bin my-app --template alloc
```

**Look for**: Unexpected allocations in hot paths.

### Step 3: Cache Analysis

```bash
# Perf stat
perf stat -e cache-references,cache-misses,cycles,instructions \
    ./target/release/my-app

# Look for:
# - Cache miss rate > 10% (investigate memory layout)
# - IPC < 1.0 (instruction stalls, consider algorithmic changes)
```

### Step 4: Benchmark Changes

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn benchmark_parse(c: &mut Criterion) {
    let input = "0x1234567890abcdef";

    c.bench_function("parse_hex", |b| {
        b.iter(|| parse_hex(black_box(input)))
    });
}

criterion_group!(benches, benchmark_parse);
criterion_main!(benches);
```

**Key metrics**: Median time, standard deviation, throughput.

---

## Production Readiness

### Monitoring Checklist

- [ ] **Metrics**: Latency (p50, p99, p999), throughput, error rate
- [ ] **Logging**: Structured logs with request IDs for tracing
- [ ] **Tracing**: Distributed tracing for cross-service requests
- [ ] **Health checks**: Liveness and readiness endpoints
- [ ] **Resource limits**: Memory, file descriptors, connection pools

### Graceful Shutdown

```rust
use tokio::signal;

async fn run_server() -> Result<()> {
    let (tx, mut rx) = tokio::sync::oneshot::channel();

    // Spawn signal handler
    tokio::spawn(async move {
        signal::ctrl_c().await.ok();
        tx.send(()).ok();
    });

    // Run server
    tokio::select! {
        _ = server.run() => {},
        _ = rx => {
            info!("Shutting down gracefully...");
            server.shutdown().await?;
        }
    }

    Ok(())
}
```

### Error Budget & Circuit Breakers

```rust
use std::sync::atomic::{AtomicU64, Ordering};

struct CircuitBreaker {
    failures: AtomicU64,
    threshold: u64,
}

impl CircuitBreaker {
    async fn call<F, T>(&self, f: F) -> Result<T>
    where
        F: FnOnce() -> Result<T>,
    {
        if self.failures.load(Ordering::Relaxed) > self.threshold {
            return Err(Error::CircuitOpen);
        }

        match f() {
            Ok(v) => {
                self.failures.store(0, Ordering::Relaxed);
                Ok(v)
            }
            Err(e) => {
                self.failures.fetch_add(1, Ordering::Relaxed);
                Err(e)
            }
        }
    }
}
```

### Performance Testing

```rust
// Load test with configurable concurrency
#[tokio::test]
async fn load_test_rpc() {
    let concurrency = 100;
    let requests_per_client = 1000;

    let mut handles = vec![];

    for _ in 0..concurrency {
        handles.push(tokio::spawn(async move {
            let client = RpcClient::new();
            let start = Instant::now();

            for _ in 0..requests_per_client {
                client.get_block(123).await.unwrap();
            }

            start.elapsed()
        }));
    }

    let durations: Vec<_> = futures::future::join_all(handles)
        .await
        .into_iter()
        .map(|r| r.unwrap())
        .collect();

    let total_requests = concurrency * requests_per_client;
    let total_time = durations.iter().max().unwrap();
    let throughput = total_requests as f64 / total_time.as_secs_f64();

    println!("Throughput: {:.0} req/s", throughput);
}
```

---

## Quick Reference: Optimization Decision Tree

```
Is it slow?
├─ No → Don't optimize
└─ Yes → Profile to find hotspot
    ├─ Allocations in hot path?
    │   ├─ Reuse buffers
    │   ├─ Use SmallVec
    │   ├─ Arena allocators
    │   └─ Zero-copy parsing
    ├─ Redundant work?
    │   ├─ Cache results
    │   ├─ Simplify algorithm
    │   └─ Remove unnecessary checks
    ├─ Sequential bottleneck?
    │   ├─ Parallelize with rayon
    │   ├─ Use async batching
    │   └─ Consider SIMD
    └─ Still slow?
        ├─ Check cache misses (data layout)
        ├─ Reduce branches (predictability)
        └─ Consider algorithmic change
```

Always measure before and after each optimization.
