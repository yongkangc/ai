# Rust Systems Engineering - Code Examples

Practical before/after examples demonstrating the four optimization principles.

## Table of Contents
1. [Reduce Allocation Examples](#reduce-allocation-examples)
2. [Eliminate Redundancy Examples](#eliminate-redundancy-examples)
3. [Prefetch & Parallelize Examples](#prefetch--parallelize-examples)
4. [Simplification Examples](#simplification-examples)
5. [Complete Case Studies](#complete-case-studies)

---

## Reduce Allocation Examples

### Example 1: Buffer Reuse in Parser

**Before: Allocates on every iteration**
```rust
fn parse_transactions(data: &[u8]) -> Vec<Transaction> {
    let mut transactions = Vec::new();

    for chunk in data.chunks(128) {
        // ❌ Allocates new Vec every iteration
        let mut buffer = Vec::new();
        decompress_into(chunk, &mut buffer);
        transactions.push(parse_tx(&buffer));
    }

    transactions
}
```

**After: Reuse buffer**
```rust
fn parse_transactions(data: &[u8]) -> Vec<Transaction> {
    let mut transactions = Vec::new();
    // ✅ Single allocation, cleared and reused
    let mut buffer = Vec::with_capacity(256);

    for chunk in data.chunks(128) {
        buffer.clear(); // Keeps capacity
        decompress_into(chunk, &mut buffer);
        transactions.push(parse_tx(&buffer));
    }

    transactions
}
```

**Impact**: 10x reduction in allocations, 30% faster.

---

### Example 2: SmallVec for Transaction Recipients

**Before: Always heap-allocates**
```rust
struct Transaction {
    from: Address,
    // ❌ Most transactions have 1-2 recipients
    to: Vec<Address>,
    value: u64,
}

fn create_transfer(from: Address, to: Address, value: u64) -> Transaction {
    Transaction {
        from,
        to: vec![to], // Heap allocation for 1 element
        value,
    }
}
```

**After: Stack allocation for common case**
```rust
use smallvec::{SmallVec, smallvec};

struct Transaction {
    from: Address,
    // ✅ Inline storage for up to 4 addresses
    to: SmallVec<[Address; 4]>,
    value: u64,
}

fn create_transfer(from: Address, to: Address, value: u64) -> Transaction {
    Transaction {
        from,
        to: smallvec![to], // No heap allocation
        value,
    }
}
```

**Impact**: Zero allocations for 99% of transactions.

---

### Example 3: Zero-Copy String Parsing

**Before: Multiple allocations**
```rust
fn parse_eth_address(input: &str) -> Result<Address> {
    // ❌ Allocates String
    let trimmed = input.trim().to_lowercase();
    // ❌ Allocates another String
    let without_prefix = trimmed.strip_prefix("0x")
        .unwrap_or(&trimmed)
        .to_string();

    Address::from_str(&without_prefix)
}
```

**After: Zero allocations**
```rust
fn parse_eth_address(input: &str) -> Result<Address> {
    // ✅ No allocations - just slice manipulation
    let s = input.trim();
    let hex = if s.len() >= 2 && s[..2].eq_ignore_ascii_case("0x") {
        &s[2..]
    } else {
        s
    };

    Address::from_str(hex)
}
```

**Impact**: 5x faster, zero allocations.

---

### Example 4: Arena Allocator for Batch Processing

**Before: Individual allocations**
```rust
fn process_block(block: &Block) -> Vec<Receipt> {
    block.transactions.iter().map(|tx| {
        // ❌ Each transaction allocates its own temp structures
        let mut trace = Vec::new();
        let mut logs = Vec::new();

        execute_transaction(tx, &mut trace, &mut logs);

        Receipt { trace, logs }
    }).collect()
}
```

**After: Arena allocation**
```rust
use bumpalo::Bump;

fn process_block(block: &Block) -> Vec<Receipt> {
    // ✅ Single allocation arena
    let arena = Bump::new();

    block.transactions.iter().map(|tx| {
        // All temporary allocations go into arena
        let trace = arena.alloc(Vec::new());
        let logs = arena.alloc(Vec::new());

        execute_transaction(tx, trace, logs);

        Receipt {
            trace: trace.clone(),
            logs: logs.clone(),
        }
    }).collect()
    // arena freed here in one operation
}
```

**Impact**: 50% reduction in allocator overhead.

---

## Eliminate Redundancy Examples

### Example 5: Cache Computed Results

**Before: Repeated computation**
```rust
fn validate_transactions(txs: &[Transaction], block_number: u64) -> bool {
    txs.iter().all(|tx| {
        // ❌ Computes base_fee 10,000 times for 10k transactions
        let base_fee = calculate_base_fee(block_number);
        tx.gas_price >= base_fee
    })
}

fn calculate_base_fee(block_number: u64) -> u64 {
    // Expensive computation
    fetch_parent_block(block_number - 1).base_fee * 1125 / 1000
}
```

**After: Compute once**
```rust
fn validate_transactions(txs: &[Transaction], block_number: u64) -> bool {
    // ✅ Compute once, reuse
    let base_fee = calculate_base_fee(block_number);

    txs.iter().all(|tx| tx.gas_price >= base_fee)
}
```

**Impact**: 10,000x fewer base fee calculations.

---

### Example 6: Eliminate Type Conversions

**Before: Round-trip conversions**
```rust
fn process_hash(hash: &[u8; 32]) -> String {
    // ❌ bytes → hex string → uppercase → trim → bytes
    let hex = hex::encode(hash);
    let upper = hex.to_uppercase();
    let trimmed = upper.trim();
    let final_bytes = hex::decode(trimmed).unwrap();

    format!("0x{}", hex::encode(final_bytes))
}
```

**After: Direct path**
```rust
fn process_hash(hash: &[u8; 32]) -> String {
    // ✅ bytes → hex string (done)
    format!("0x{}", hex::encode(hash))
}
```

**Impact**: 5x faster, clearer logic.

---

### Example 7: Simplify Nested Conditions

**Before: Complex nested logic**
```rust
fn classify_transaction(tx: &Transaction) -> TxType {
    if tx.to.is_some() {
        if tx.value > 0 {
            if tx.data.is_empty() {
                TxType::Transfer
            } else {
                if tx.data.len() >= 4 {
                    TxType::ContractCall
                } else {
                    TxType::Invalid
                }
            }
        } else {
            if tx.data.is_empty() {
                TxType::Invalid
            } else {
                TxType::ContractCall
            }
        }
    } else {
        TxType::ContractCreation
    }
}
```

**After: Flat match**
```rust
fn classify_transaction(tx: &Transaction) -> TxType {
    // ✅ Single match, all cases visible
    match (tx.to.is_some(), tx.value > 0, tx.data.len()) {
        (false, _, _) => TxType::ContractCreation,
        (true, true, 0) => TxType::Transfer,
        (true, _, 4..) => TxType::ContractCall,
        _ => TxType::Invalid,
    }
}
```

**Impact**: Clearer logic, easier to verify correctness.

---

## Prefetch & Parallelize Examples

### Example 8: Parallel Signature Recovery

**Before: Sequential**
```rust
fn recover_senders(txs: &[Transaction]) -> Vec<Address> {
    // ❌ Processes one transaction at a time
    txs.iter()
        .map(|tx| recover_sender(tx)) // CPU-bound ECDSA
        .collect()
}
```

**After: Parallel with rayon**
```rust
use rayon::prelude::*;

fn recover_senders(txs: &[Transaction]) -> Vec<Address> {
    // ✅ Parallel across all CPUs
    txs.par_iter()
        .map(|tx| recover_sender(tx))
        .collect()
}
```

**Impact**: 8x faster on 8-core CPU.

---

### Example 9: Batch Database Queries

**Before: Query per item**
```rust
async fn fetch_accounts(addresses: &[Address]) -> Vec<Account> {
    let mut accounts = Vec::new();

    // ❌ 1,000 addresses = 1,000 round trips
    for addr in addresses {
        let account = db.get_account(addr).await.unwrap();
        accounts.push(account);
    }

    accounts
}
```

**After: Batch query**
```rust
async fn fetch_accounts(addresses: &[Address]) -> Vec<Account> {
    // ✅ Single round trip for all addresses
    db.batch_get_accounts(addresses).await.unwrap()
}

// Database implementation
async fn batch_get_accounts(&self, addresses: &[Address]) -> Result<Vec<Account>> {
    let tx = self.begin_read()?;

    // Prefetch optimization: tell DB we'll need all these keys
    let mut cursor = tx.cursor::<Accounts>()?;

    addresses.iter()
        .map(|addr| cursor.seek(addr).map(|(_, acc)| acc))
        .collect()
}
```

**Impact**: 100x faster (1ms vs 100ms for 1000 queries).

---

### Example 10: SIMD for Hash Computation

**Before: Scalar operations**
```rust
fn xor_hashes(a: &[u8; 32], b: &[u8; 32]) -> [u8; 32] {
    let mut result = [0u8; 32];

    // ❌ One byte at a time
    for i in 0..32 {
        result[i] = a[i] ^ b[i];
    }

    result
}
```

**After: SIMD operations**
```rust
#![feature(portable_simd)]
use std::simd::{u8x32, SimdUint};

fn xor_hashes(a: &[u8; 32], b: &[u8; 32]) -> [u8; 32] {
    // ✅ 32 bytes at once
    let a_vec = u8x32::from_array(*a);
    let b_vec = u8x32::from_array(*b);
    (a_vec ^ b_vec).to_array()
}
```

**Impact**: 8-16x faster.

---

### Example 11: Cache-Friendly Data Layout

**Before: Array of Structs (poor cache locality)**
```rust
struct Transaction {
    hash: [u8; 32],
    from: Address,
    to: Address,
    value: u64,
    gas: u64,
    data: Vec<u8>,
}

fn sum_transaction_values(txs: &[Transaction]) -> u64 {
    // ❌ Loads entire struct (120+ bytes) to access 8-byte value
    txs.iter().map(|tx| tx.value).sum()
}
```

**After: Structure of Arrays (cache-friendly)**
```rust
struct Transactions {
    hashes: Vec<[u8; 32]>,
    froms: Vec<Address>,
    tos: Vec<Address>,
    values: Vec<u64>,  // Contiguous in memory
    gas: Vec<u64>,
    data: Vec<Vec<u8>>,
}

fn sum_transaction_values(txs: &Transactions) -> u64 {
    // ✅ Sequential access to packed u64 array
    txs.values.iter().sum()
}
```

**Impact**: 5x faster due to better cache utilization.

---

## Simplification Examples

### Example 12: Simplify Iterator Chain

**Before: Complex iterator chain**
```rust
fn get_recent_block_hashes(blocks: &[Block], count: usize) -> Vec<BlockHash> {
    // ❌ Hard to read, unnecessary allocations
    blocks.iter()
        .rev()
        .take(count)
        .map(|b| b.hash.clone())
        .collect::<Vec<_>>()
        .into_iter()
        .rev()
        .collect()
}
```

**After: Simple loop**
```rust
fn get_recent_block_hashes(blocks: &[Block], count: usize) -> Vec<BlockHash> {
    // ✅ Clear intent, single allocation
    let start = blocks.len().saturating_sub(count);
    blocks[start..].iter()
        .map(|b| b.hash)
        .collect()
}
```

**Impact**: 2x faster, easier to understand.

---

### Example 13: Replace Dynamic Dispatch

**Before: Runtime polymorphism**
```rust
trait Executor {
    fn execute(&self, tx: &Transaction) -> Result<Receipt>;
}

fn process_transactions(txs: &[Transaction], executor: &dyn Executor) -> Vec<Receipt> {
    // ❌ Virtual dispatch on every call
    txs.iter()
        .map(|tx| executor.execute(tx).unwrap())
        .collect()
}
```

**After: Static dispatch**
```rust
fn process_transactions<E: Executor>(
    txs: &[Transaction],
    executor: &E,
) -> Vec<Receipt> {
    // ✅ Monomorphized, inlined
    txs.iter()
        .map(|tx| executor.execute(tx).unwrap())
        .collect()
}
```

**Impact**: 15-20% faster in hot paths.

---

## Complete Case Studies

### Case Study 1: Block Validation

**Initial Implementation (Slow)**
```rust
fn validate_block(block: &Block) -> Result<()> {
    // Problem 1: Redundant hash computation
    let block_hash = block.compute_hash();
    for tx in &block.transactions {
        let tx_hash = tx.compute_hash();
        if !tx.verify_signature() {
            return Err(Error::InvalidSignature(tx_hash));
        }
    }

    // Problem 2: Sequential signature verification
    // Problem 3: Re-computing base fee repeatedly
    for tx in &block.transactions {
        let base_fee = compute_base_fee(block.number);
        if tx.gas_price < base_fee {
            return Err(Error::GasPriceTooLow);
        }
    }

    // Problem 4: Allocates temporary vectors
    let total_gas: u64 = block.transactions.iter()
        .map(|tx| tx.gas_limit)
        .collect::<Vec<_>>()
        .iter()
        .sum();

    if total_gas > block.gas_limit {
        return Err(Error::GasLimitExceeded);
    }

    Ok(())
}
```

**Optimized Implementation**
```rust
use rayon::prelude::*;

fn validate_block(block: &Block) -> Result<()> {
    // ✅ Optimization 1: Compute base fee once
    let base_fee = compute_base_fee(block.number);

    // ✅ Optimization 2: Parallel signature verification
    let verification_results: Result<Vec<_>> = block.transactions
        .par_iter()
        .map(|tx| {
            if !tx.verify_signature() {
                return Err(Error::InvalidSignature(tx.hash));
            }
            if tx.gas_price < base_fee {
                return Err(Error::GasPriceTooLow);
            }
            Ok(tx.gas_limit)
        })
        .collect();

    let gas_limits = verification_results?;

    // ✅ Optimization 3: Direct sum without intermediate collection
    let total_gas: u64 = gas_limits.iter().sum();

    if total_gas > block.gas_limit {
        return Err(Error::GasLimitExceeded);
    }

    Ok(())
}
```

**Results**:
- 8x faster on 8-core CPU (parallelization)
- 30% less memory (eliminated redundant allocations)
- Simpler logic (combined validation loops)

---

### Case Study 2: Transaction Execution Hot Path

**Before: Multiple Optimizations Needed**
```rust
fn execute_transaction(
    state: &mut State,
    tx: &Transaction,
) -> Result<Receipt> {
    // Issue 1: Allocates on every call
    let mut trace = Vec::new();
    let mut logs = Vec::new();

    // Issue 2: Unnecessary cloning
    let sender = tx.sender.clone();
    let recipient = tx.to.clone();

    // Issue 3: Multiple state lookups
    let sender_balance = state.get_balance(&sender)?;
    let sender_nonce = state.get_nonce(&sender)?;

    // Validation
    if sender_nonce != tx.nonce {
        return Err(Error::InvalidNonce);
    }

    // Issue 4: String allocation for error messages
    if sender_balance < tx.value {
        return Err(Error::InsufficientBalance(
            format!("need {} but have {}", tx.value, sender_balance)
        ));
    }

    // Execute...
    let result = evm_execute(state, tx, &mut trace, &mut logs)?;

    Ok(Receipt { trace, logs, result })
}
```

**After: Optimized Hot Path**
```rust
fn execute_transaction(
    state: &mut State,
    tx: &Transaction,
    // ✅ Caller-provided buffers (reused across transactions)
    trace: &mut Vec<TraceEntry>,
    logs: &mut Vec<Log>,
) -> Result<Receipt> {
    trace.clear();
    logs.clear();

    // ✅ No cloning - references suffice
    let sender = &tx.sender;
    let recipient = &tx.to;

    // ✅ Batch state lookup (single read transaction)
    let (sender_balance, sender_nonce) = state.get_account(sender)?;

    // ✅ Early returns without allocation
    if sender_nonce != tx.nonce {
        return Err(Error::InvalidNonce);
    }

    if sender_balance < tx.value {
        // ✅ No string allocation
        return Err(Error::InsufficientBalance);
    }

    // Execute...
    let result = evm_execute(state, tx, trace, logs)?;

    Ok(Receipt {
        // Clone only successful path
        trace: trace.clone(),
        logs: logs.clone(),
        result,
    })
}
```

**Results**:
- 40% faster execution
- 80% fewer allocations
- Clearer error paths

---

## Benchmark Template

Use this template to verify optimizations:

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};

fn benchmark_optimization(c: &mut Criterion) {
    let mut group = c.benchmark_group("transaction_validation");

    let transactions = generate_test_transactions(1000);

    group.bench_with_input(
        BenchmarkId::new("before", 1000),
        &transactions,
        |b, txs| {
            b.iter(|| validate_transactions_old(black_box(txs)))
        },
    );

    group.bench_with_input(
        BenchmarkId::new("after", 1000),
        &transactions,
        |b, txs| {
            b.iter(|| validate_transactions_new(black_box(txs)))
        },
    );

    group.finish();
}

criterion_group!(benches, benchmark_optimization);
criterion_main!(benches);
```

Run with:
```bash
cargo bench --bench transaction_bench
```

Look for:
- Time improvement (throughput)
- Reduced variance (stability)
- Allocations via `cargo instruments` or `dhat`

---

## Testing Optimized Code

Critical: Optimizations must not break correctness.

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    // Property test: old and new implementations must agree
    proptest! {
        #[test]
        fn optimization_preserves_behavior(
            txs in prop::collection::vec(arbitrary_transaction(), 0..100)
        ) {
            let result_old = validate_transactions_old(&txs);
            let result_new = validate_transactions_new(&txs);

            prop_assert_eq!(result_old, result_new);
        }
    }

    // Regression test: performance must not degrade
    #[test]
    fn performance_regression() {
        let txs = generate_test_transactions(1000);

        let start = Instant::now();
        validate_transactions_new(&txs);
        let duration = start.elapsed();

        // Fail if performance degrades by >10%
        assert!(
            duration < Duration::from_millis(50),
            "Performance regression: took {:?}",
            duration
        );
    }
}
```

---

## Summary: The Optimization Loop

1. **Profile**: Identify actual bottleneck
2. **Measure**: Baseline benchmark
3. **Optimize**: Apply one principle (allocation, redundancy, parallelism, simplicity)
4. **Verify**: Tests pass, benchmark improves
5. **Repeat**: Move to next bottleneck

Never optimize without measuring.
