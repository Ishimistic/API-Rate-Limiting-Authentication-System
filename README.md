#  API Rate Limiting & Authentication System

A production-inspired backend system built with Django and Redis that provides **secure API key authentication, rate limiting, and abuse protection** using a sliding window algorithm.



##  Overview

This project implements a **stateless API security layer** that controls access to APIs using:

- API key-based authentication
- Redis-powered rate limiting
- Temporary ban system for abusive clients
- Secure API key lifecycle management (generation, rotation, expiry)



##  Key Features

###  API Key Authentication
- Secure API key generation using `secrets.token_hex`
- API keys stored as **hashed values (SHA-256)** for security
- Stateless authentication via `X-API-KEY` header
- API key rotation on login
- API key regeneration endpoint


###  Rate Limiting (Sliding Window)
- Uses Redis Sorted Sets (`ZSET`) to track requests
- Implements **sliding window algorithm** for accurate limiting
- Per-user (API key) and fallback IP-based limiting


###  Abuse Detection & Ban System
- Strike-based violation tracking
- Temporary ban after repeated limit breaches
- Automatic expiry of strike counters



###  API Key Lifecycle Management
- **Signup** → generates API key (shown once)
- **Login** → rotates API key (new key issued)
- **Logout** → deactivates API key
- **Regenerate** → creates new key from existing one
- **Expiry** → keys expire automatically after 24 hours


###  Security Features
- API keys stored as hashes (not plain text)
- Stateless request validation
- Expiring credentials
- Ban system for abuse prevention
- Middleware-based enforcement

---

##  Architecture
Client Request
↓
RateLimitMiddleware
↓
├── API Key Validation
├── Expiry Check
├── Ban Check
├── Rate Limiting (Redis)
↓
View Execution
↓
Response + Rate Limit Headers




##  Tech Stack

- **Backend:** Django
- **Cache / Rate Limiting:** Redis
- **Authentication:** Custom API Key System
- **Algorithm:** Sliding Window Rate Limiting


##  API Endpoints

| Endpoint | Description |
|--------|------------|
| `/signup/` | Create user & API key |
| `/login/` | Authenticate & rotate API key |
| `/logout/` | Deactivate API key |
| `/regenerate-key/` | Generate new API key |
| `/test/` | Protected API endpoint |



##  Example Request

```http
GET /test/
X-API-KEY: your_api_key_here
```
## Rate Limit Response Headers
```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
```


## Future Improvements
- Redis atomic operations (Lua scripts)
- Distributed rate limiting
- Tier-based API plans (Free / Pro)
- HMAC request signing
- Usage analytics dashboard


