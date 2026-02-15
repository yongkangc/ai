You are an expert in Rust, async programming, and concurrent systems and backend engineering.

Key Principles
Refer to Rust's async book and `tokio` documentation for in-depth information on async patterns, best practices, and advanced features.

### 1. Enhance Clarity and Specificity

**Why**: General guidelines can leave room for interpretation, leading to inconsistent code. Tailoring them to your project ensures they’re immediately useful.  
**How**:

- Add context specific to your system, like using Axum for web services or handling JWT authentication.
- Include concrete examples tied to your use case.

**Example**: Instead of “Write idiomatic Rust,” specify: “Use Axum handlers like `async fn login_handler(payload: Json<LoginRequest>)` to process `POST /login` requests, returning a JWT in a `Json<LoginResponse>`.”

---

### 2. Incorporate Best Practices for Axum

**Why**: Axum is central to your web API, and generic async advice may not address its nuances.  
**How**:

- Add sections on Axum-specific features: routing, middleware, extractors, and state management.
- Explain how to structure an Axum app effectively.

**Example**:

- **Routing**: “Define routes with `Router::new().route('/login', post(login_handler))` for clarity and efficiency.”
- **State**: “Share a JWT secret across handlers with `Extension<String>`: `app.layer(Extension(secret))`.”

---

### 3. Refine Error Handling

**Why**: Robust error handling is critical for web APIs, and generic advice might miss Axum integration.  
**How**:

- Use `thiserror` to define custom error types (e.g., `AuthError::InvalidCredentials`).
- Show how to map errors to HTTP responses in Axum.

**Example**:

```rust
use thiserror::Error;
use axum::{http::StatusCode, response::IntoResponse};

#[derive(Error, Debug)]
enum AuthError {
    #[error("Invalid credentials")]
    InvalidCredentials,
}

impl IntoResponse for AuthError {
    fn into_response(self) -> axum::response::Response {
        (StatusCode::UNAUTHORIZED, self.to_string()).into_response()
    }
}

async fn login_handler(...) -> Result<Json<LoginResponse>, AuthError> {
    // Logic here
}
```

---

### 4. Expand Testing Strategies

**Why**: Thorough testing ensures reliability, especially for async systems, but generic testing advice may lack depth.  
**How**:

- Include Axum-specific testing with `tokio::test` and `axum::http::Request`.
- Cover integration tests with a test server.

**Example**:

```rust
#[tokio::test]
async fn test_login_success() {
    let app = Router::new().route("/login", post(login_handler));
    let req = Request::builder()
        .method("POST")
        .uri("/login")
        .header("Content-Type", "application/json")
        .body(Body::from(r#"{"username":"user","password":"pass"}"#))
        .unwrap();
    let resp = app.oneshot(req).await.unwrap();
    assert_eq!(resp.status(), StatusCode::OK);
}
```

---

### 5. Optimize for Performance

**Why**: Web APIs need to handle load efficiently, and generic performance tips might not address Axum’s async nature.  
**How**:

- Minimize middleware layers and async overhead in handlers.
- Offload blocking tasks (e.g., password hashing) to `tokio::task::spawn_blocking`.

**Example**:

```rust
let hash = tokio::task::spawn_blocking(|| hash_password(&password)).await??;
```

---

### 6. Encourage Modular Design

**Why**: A modular structure improves maintainability as your project grows beyond a single endpoint.  
**How**:

- Define modules like `auth`, `jwt`, and `routes`.
- Provide a sample structure.

**Example**:

```
src/
├── auth.rs        // Credential validation logic
├── jwt.rs         // JWT generation and parsing
├── routes.rs      // Axum handlers and routing
└── main.rs        // App setup
```

---

### 7. Document Configuration Management

**Why**: Configuration (e.g., JWT secrets) must be secure and environment-specific.  
**How**:

- Use environment variables with `std::env` and validate them at startup.
- Suggest `dotenv` for development.

**Example**:

```rust
let secret = std::env::var("JWT_SECRET").expect("JWT_SECRET required");
let app = Router::new().layer(Extension(secret));
```

---

### 8. Integrate with the Async Ecosystem

**Why**: Your system likely interacts with databases or external services, and guidelines should reflect this.  
**How**:

- Show integration with `sqlx` for database queries or `reqwest` for HTTP calls.

**Example**:

```rust
let user = sqlx::query!("SELECT * FROM users WHERE username = $1", username)
    .fetch_one(&pool)
    .await?;
```

---

### 9. Provide Code Examples

**Why**: Examples bridge theory and practice, making guidelines actionable.  
**How**:

- Include a full Axum handler for `/login`.

**Example**:

```rust
use axum::{routing::post, Router, Json, Extension, http::StatusCode};
use serde::{Deserialize, Serialize};
use jsonwebtoken::{encode, Header, EncodingKey};
use std::sync::Arc;
use tokio::sync::Mutex;

#[derive(Deserialize)]
struct LoginRequest {
    username: String,
    password: String,
}

#[derive(Serialize)]
struct LoginResponse {
    token: String,
}

async fn login_handler(
    Json(payload): Json<LoginRequest>,
    Extension(secret): Extension<String>,
) -> Result<Json<LoginResponse>, (StatusCode, String)> {
    if payload.username == "user" && payload.password == "pass" { // Replace with real validation
        let token = encode(&Header::default(), &Claims { sub: payload.username },
            &EncodingKey::from_secret(secret.as_ref()))
            .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
        Ok(Json(LoginResponse { token }))
    } else {
        Err((StatusCode::UNAUTHORIZED, "Invalid credentials".to_string()))
    }
}

#[tokio::main]
async fn main() {
    let secret = "your-secure-secret".to_string();
    let app = Router::new()
        .route("/login", post(login_handler))
        .layer(Extension(secret));
    axum::Server::bind(&"0.0.0.0:3000".parse().unwrap())
        .serve(app.into_make_service())
        .await
        .unwrap();
}
```

### **Security Considerations**

- **Password Hashing:** Always use strong password hashing algorithms like Argon2 or bcrypt.
- **JWT Security:**
  - Use a long, randomly generated secret key.
  - Set short expiration times for tokens.
  - Implement token revocation mechanisms if necessary.
  - Protect against common JWT vulnerabilities like token replay and forgery.
- **Input Validation:**
  - Validate all user input to prevent injection attacks (SQL injection, XSS, etc.).
  - Use libraries like `serde_valid` for structured input validation.
- **Secure Configuration:**
  - Avoid hardcoding sensitive information in code.
  - Use environment variables or configuration files.
  - Protect secrets with tools like `dotenv` or `vault`.

### **Error Handling and Logging**

- **Detailed Error Messages:** Provide informative error messages to aid debugging.
- **Centralized Error Logging:** Use a logging library like `log` or `tracing` to log errors and warnings.
- **Error Boundaries:** Consider using `try!` or the `?` operator for concise error handling.

### **Performance Optimization**

- **Async/Await Best Practices:**
  - Avoid blocking operations in async contexts.
  - Use `tokio::task::spawn_blocking` for CPU-bound tasks.
  - Optimize database queries with proper indexing and query optimization.
- **Profiling:** Use tools like `tokio-console` or `cargo-flamegraph` to identify performance bottlenecks.

### **Code Style and Maintainability**

- **Adhere to Rust Style Guide:** Follow the official Rust style guide for consistent formatting.
- **Use Clippy:** Run Clippy to catch common style and performance issues.
- **Write Clear and Concise Code:** Use meaningful variable names and comments.
- **Modularize Code:** Break down large modules into smaller, focused ones.

### **Additional Tips**

- **Leverage Rust's Type System:** Use Rust's strong type system to prevent errors and write more reliable code.
- **Test Thoroughly:** Write unit, integration, and end-to-end tests to ensure code quality.
- **Stay Updated:** Keep up with the latest Rust and Axum developments.
- **Learn from Others:** Explore open-source Rust projects and community resources.

---

### 10. Encourage Iteration

**Why**: Guidelines should evolve with your project and team feedback.  
**How**:

- Suggest periodic reviews to update rules based on new requirements or lessons learned.

**Example**: “Review cursorrules quarterly to incorporate new Axum features or team suggestions.”
