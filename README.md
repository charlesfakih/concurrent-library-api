# Concurrent Library API

A REST API for a small library system: create books, look up their availability, borrow a copy, and return it. Built with FastAPI and PostgreSQL (via SQLAlchemy's async ORM), with particular attention to correctness under concurrency — the API guarantees a book can never be overbooked, even under simultaneous borrow requests.

## Stack
- **Language:** Python 3.14
- **Framework:** FastAPI (async)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy 2.0 (async, declarative style)
- **Driver:** asyncpg
- **Testing:** pytest, pytest-asyncio, httpx (ASGI in-process testing)

## Domain Models

In a library system, there's the concept of a book and a loan of a book. Modeling the relationship between the two, where a loan is tied to one book, had to contend with the core invariant: you can't have more borrowed copies than total existing copies of a book.

The immediate, obvious approach was to include a field on `Book` tracking the number of available copies. This would require decrementing that field on every borrow, alongside creating the loan. To verify the invariant, `available_copies` would need to never fall below 0, *and* the number of `Loan` rows for a book would need to never exceed `total_copies` — two separate sources of truth for the same invariant, both needing to be kept in sync.

The approach I went with instead was to drop `available_copies` entirely and derive it by counting `Loan` rows for a book, with a `returned` field marking which ones are still active. This way, there's a single source of truth for the invariant — a safer design that guards against forgetting to keep `loans` and `books` in sync in some future code path.

## Concurrency and Locking

To hold the invariant and protect against overbooking, the race condition has to be prevented with a lock. Since the data lives in a database that can accept connections from multiple processes, the lock has to live at the database level — a lock in the code of one process does nothing to prevent a race from a different process. Postgres provides this through `SELECT ... FOR UPDATE`, which gives row-level locking.

To borrow a book, I lock the book row with `FOR UPDATE` before checking availability. Locking the book row serializes all borrow attempts for that book, so only one can be mid check-and-insert at a time. Locking a loan instead wouldn't prevent anything, since there's no loan yet to lock at that point — another request would simply create a different loan row, and overbooking could still happen.

Contrast this with `return_copy`, where locking the book row is unnecessary. A race between a borrow and a return can produce a momentarily stale count of available copies, which is an acceptable lag, so long as the invariant itself never breaks.

**Verifying it.** My first approach was to fire a borrow request from two different terminals against the same book, with an artificial five second delay injected between lock acquisition and commit, so the second request would be fired while the first was still in flight. The second request's log timestamps showed it blocked until the first transaction committed, confirming the lock serializes access at the database level.

The more rigorous, automated version of this uses `asyncio.gather` to fire two borrow requests concurrently against a book with only one copy available. The test asserts exactly one request succeeds with `201` and the other is rejected with `409`.

## Testing Infrastructure

The challenge in testing was exercising the real routes against a real database, without polluting the dev database or letting tests interfere with each other. I used `httpx` to build a client that routes test requests directly into the actual FastAPI app, with the database dependency overridden to point at a separate test database.

Test isolation between runs meant keeping the default function scope for the fixture that sets up and tears down the database for every test. Since these are async tests making async requests, `pytest-asyncio` runs every test inside its own event loop, and every database connection is registered to whichever loop created it. I initially had the SQLAlchemy engine living at module scope, created once — so every session after the very first test was stuck trying to reuse a connection registered to an already-dead event loop.

The fix was moving engine creation inside the fixture itself, so a fresh engine (and fresh connection pool) gets created on every test, bound to whatever loop is active at that moment. As a consequence, the session also had to be built fresh per test, defined as a nested closure inside the fixture — so that `override_get_db` could reference the current `TestSessionLocal`, which no longer existed as a module-level variable.

## Running the App

**1. Clone and set up the environment**

```bash
git clone <your-repo-url>
cd concurrent-library-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Set up PostgreSQL**

Two databases are required: one for the app, one for the test suite.

```bash
sudo service postgresql start
sudo -u postgres psql
```

Inside `psql`:

```sql
CREATE DATABASE library;
CREATE USER charles WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE library TO charles;
\c library
GRANT ALL ON SCHEMA public TO charles;

CREATE DATABASE library_test;
GRANT ALL PRIVILEGES ON DATABASE library_test TO charles;
\c library_test
GRANT ALL ON SCHEMA public TO charles;
\q
```

**3. Configure the database connection**

By default the app connects using a local fallback connection string. To use your own credentials, set the `DATABASE_URL` environment variable before running:

```bash
export DATABASE_URL="postgresql+asyncpg://charles:yourpassword@localhost/library"
```

**4. Run the app**

```bash
fastapi dev main.py
```

The API is live at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`. Tables are created automatically on startup.

**5. Run the test suite**

```bash
pytest -v
```

Tests run against a separate `library_test` database, fully isolated from dev data, with all tables created fresh and torn down after each test.

## What I'd Improve

- A search endpoint by title or author. Currently a client must already know the book's id.
- The ability to update `total_copies` when new physical copies arrive. This isn't just a missing endpoint; it raises a real question about the invariant: if `total_copies` is decreased below the number of currently active loans, does the system still hold? That's a decision I'd want to make deliberately rather than bolt on.
- Input validation to guard against empty or blank titles, oversized strings, and eventually email-shaped validation if borrower identity is added.
- Error response consistency: a unified `ErrorResponse` shape across every exception handler, rather than whatever FastAPI's default happens to produce for each exception type.
- Structured logging that includes identifiers like `book_id` and `loan_id`, so a specific request's full story can be traced through the logs.
- Resilience around the database going down mid-request: should the app retry? Should there be a connection timeout, so a dead database fails fast instead of hanging requests indefinitely?
- Untested gaps: the 404 paths for a nonexistent book or nonexistent loan currently have no test coverage.
