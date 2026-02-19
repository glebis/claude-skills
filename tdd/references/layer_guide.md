# DDD / Onion Layer Reference

Compact reference for layer-aware TDD. Not a DDD textbook — just enough for agents to enforce dependency direction and choose the right test strategy.

## Why This Matters (Research-Backed)

- **AI-generated code without architectural constraints produces 80% dependency violation rates** in hexagonal architecture (arXiv:2512.04273, 2025). Layer constraints in agent prompts directly counteract this.
- **Static tools detect only ~77% of dependency violations** on average (Pruijt et al., 2017). Our refactorer supplements tooling by checking imports + transitive deps during code review.
- **Test-driven prompting improves LLM code generation accuracy by 38-45%** (Naik et al., 2024). RED-first with focused prompts is empirically better than spec-first.
- **TDD alone doesn't automatically improve design** (Turhan et al., 2017). The REFACTOR phase with dependency checks is essential, not optional — it's where architectural quality emerges.

## Layer Definitions (Inside → Outside)

### Domain Model (Core)
- Entities, Value Objects, Aggregates, Domain Events
- ZERO external dependencies (no ORM, no HTTP, no frameworks)
- Test with: direct construction, no mocks
- Example: `User` entity with email validation, `Money` value object with currency math

### Domain Services
- Complex operations spanning multiple aggregates
- Depends on: Domain Model only (+ interfaces for ports it needs)
- Test with: real domain objects, in-memory fakes for repository interfaces
- Example: `RegistrationService` checking uniqueness via a repository interface

### Application Services (Use Cases)
- Orchestrate domain logic, handle transactions, coordinate side effects
- Depends on: Domain Model + Domain Services
- Defines port interfaces that infrastructure will implement
- Test with: in-memory fakes for all ports/repositories
- Example: `RegisterUserUseCase` coordinating validation, persistence, email notification

### Infrastructure & Presentation
- DB access, external APIs, controllers, CLI handlers, adapters
- Depends on: all inner layers (implements their interfaces)
- Test with: integration tests, may use real dependencies or test containers
- Example: `PostgresUserRepository` implementing `UserRepository` interface

## Port Interface Placement

Ports (interfaces that abstract external dependencies) are defined by **the layer that consumes them**, not the layer that implements them:

- A `UserRepository` interface consumed by a domain service lives in `domain/ports/` or `domain-service/ports/`
- A `NotificationService` interface consumed by an application use case lives in `application/ports/`
- Infrastructure implements these interfaces but never defines them

Rule: **the consumer defines the contract; the provider fulfills it**. This is the Dependency Inversion Principle.

## Dependency Rule

Dependencies flow INWARD only. Inner layers define interfaces (ports); outer layers implement them (adapters).

```
Infrastructure → Application → Domain Services → Domain Model
     ↓               ↓               ↓                ↓
  implements     orchestrates     uses real        pure logic
  interfaces     via ports        domain objects   no imports
```

Violation example: `domain/user.py` importing `from infrastructure.db import Session` — domain must never import infrastructure.

## Layer Detection Heuristics

When classifying a slice, ask:
1. Does it involve only business rules with no I/O? → **domain**
2. Does it coordinate multiple domain objects but still no I/O? → **domain-service**
3. Does it orchestrate a workflow (validate, persist, notify)? → **application**
4. Does it talk to a database, HTTP API, file system, or framework? → **infrastructure**

## Test Strategy by Layer

| Layer | Mocks/Fakes | Framework imports | I/O allowed |
|-------|-------------|-------------------|-------------|
| domain | None | None | No |
| domain-service | In-memory fakes for ports | None | No |
| application | In-memory fakes for all ports | Minimal (DI container) | No |
| infrastructure | Optional (real deps or test containers) | Yes | Yes |
