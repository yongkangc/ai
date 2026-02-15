# Coding Guidelines

Core principles for writing clean, maintainable code.

## Simplicity Over Abstraction

**Don't write functions for code one can write inline as a simple expression using well-known operations.**

It's much easier to read code that uses a small number of common primitives than to remember 1000's of helper functions.

### Examples

#### ❌ Avoid
```javascript
// Unnecessary abstraction
function addOne(x) {
  return x + 1;
}

function isPositive(num) {
  return num > 0;
}

function getFirstElement(arr) {
  return arr[0];
}

// Usage
const result = addOne(value);
const check = isPositive(number);
const first = getFirstElement(items);
```

#### ✅ Prefer
```javascript
// Direct, clear expressions
const result = value + 1;
const check = number > 0;
const first = items[0];
```

### When to Create Functions

Create functions when:
- Logic is complex and needs documentation
- Code is reused multiple times (DRY principle)
- Abstraction provides meaningful semantic value
- Testing isolation is needed
- The operation isn't immediately obvious

### Good Function Examples

```javascript
// Complex business logic
function calculateCompoundInterest(principal, rate, time, n) {
  return principal * Math.pow((1 + rate/n), n * time);
}

// Reusable validation with multiple checks
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return email && emailRegex.test(email) && email.length <= 254;
}

// Domain-specific operation
function convertCelsiusToFahrenheit(celsius) {
  return (celsius * 9/5) + 32;
}
```

## Related Principles

### Use Standard Library Functions
Prefer well-known standard library functions over custom implementations:

```javascript
// Use standard methods
const sorted = items.sort((a, b) => a - b);
const filtered = items.filter(x => x > 0);
const sum = numbers.reduce((a, b) => a + b, 0);

// Not custom helpers for simple operations
```

### Inline Simple Conditionals
For simple conditions, inline ternary operators or logical operators are clearer:

```javascript
// Clear and concise
const status = isActive ? 'active' : 'inactive';
const name = user.name || 'Anonymous';
const items = list?.length > 0 ? list : [];

// Rather than wrapping in functions
```

### Avoid Premature Abstraction
Don't create abstractions until patterns emerge clearly:

1. Write the code directly first
2. Identify actual repetition (not imagined)
3. Extract only when the abstraction is obvious and valuable

## Benefits

- **Lower cognitive load**: Readers don't need to jump between definitions
- **Clearer intent**: Direct operations are self-documenting
- **Easier debugging**: Less indirection means clearer stack traces
- **Better performance**: Fewer function calls (though modern compilers optimize this)
- **Reduced complexity**: Fewer moving parts to maintain

## Summary

Keep code simple and direct. Use inline expressions for simple operations. Create functions only when they provide real value through complexity management, reusability, or domain modeling.