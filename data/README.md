# Data dictionary: FunnelLens exports

Each folder under `raw/` is one export, named after its export month. It holds four CSV files and an
`export.json` with the period, the sampling rate and a SHA-256 of every file. The data is **synthetic**
(made by `scripts/generate_data.py` with a fixed seed) but has the defects of real exports on purpose.
Never "fix" a raw file by hand: the cleaning rules in `contract/questions.md` §2 do that, and count it.

```bash
python3 scripts/generate_data.py --check   # every committed file is byte-identical to a fresh generation
```

| Export | Period | Sample | Notes |
|---|---|---|---|
| `2026-06` | 2026-01-01 to 2026-06-30 | 1 in 20 sessions | the export of the brief (v1.0) |
| `2026-08` | 2026-01-01 to 2026-08-31 | 1 in 20 sessions | the refresh (v1.1): new channel `referral`, a `payment_method` column, and the broken tracking week 2026-W31 (see `docs/postmortem-2026-W31.md`) |

## `users.csv`
| Column | Type (after cleaning) | Notes |
|---|---|---|
| `user_id` | integer | unique |
| `signup_date` | date `YYYY-MM-DD` | not used by the v1 questions |
| `signup_channel` | text or missing | ~9 % empty |
| `city` | text | mixed case, stray spaces and old names (`Bangalore`, `bombay`): see `cleaning.city_aliases` |

## `sessions.csv`
| Column | Type | Notes |
|---|---|---|
| `session_id` | text `S000001` | exact duplicate rows, and a few ids that appear with different content |
| `user_id` | integer | a few point to no user |
| `device` | `desktop` / `mobile` | mixed case |
| `channel` | `email` / `organic` / `paid_social` / `referral` (from July 2026) / unknown | `""`, `(not set)` and `unknown` all mean unknown |
| `started_at` | timestamp | `2026-01-05 14:03:00` **or** `05/01/2026 14:03` (day first); a few are unparseable or outside the period |

## `events.csv`
| Column | Type | Notes |
|---|---|---|
| `session_id` | text | some point to no session |
| `event_name` | `view` / `cart` / `checkout` | mixed case; a few unknown names; repeated steps; some steps logged out of order |
| `event_at` | timestamp | same two formats |

## `orders.csv`
| Column | Type | Notes |
|---|---|---|
| `order_id` | text `O000001` | a few exact duplicates |
| `session_id` | text | the session the order was placed in; a few point to no session; a few have no checkout event |
| `amount` | text → integer paise | `₹1,299.00`, `1299`, `Rs. 1,299`, refunds as `-₹499.00`, a few unparseable |

| `payment_method` | `upi` / `card` / `cod` / `netbanking` / empty | **2026-08 and later only** (an additive column: older exports do not have it) |

A purchase is a session with an order (`contract/questions.md` §3); there is no purchase event.
