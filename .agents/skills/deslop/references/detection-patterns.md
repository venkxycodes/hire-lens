# Deslop detection patterns

## Certainty levels

| Level | Meaning | Default action |
|-------|---------|----------------|
| HIGH | Definitely slop; safe to remove | Auto-fix in apply mode |
| MEDIUM | Likely slop; needs context | Report; fix only when obvious |
| LOW | Possible slop | Report only |

## HIGH (auto-fix when safe)

| Pattern | Examples |
|---------|----------|
| Debug statements | `console.log`, `print()`, `dbg!()` left from debugging |
| Placeholder text | `TODO: implement`, `Lorem ipsum`, stub return values |
| Empty error handling | `except: pass`, `catch {}` with no comment |
| Trailing whitespace / mixed indentation | Formatting-only |
| Unused debug imports | `import pdb`, unused `logging` setup |

## MEDIUM (review required)

| Pattern | Examples |
|---------|----------|
| Excessive comments | Comment-to-code ratio > 2:1 explaining obvious code |
| Stub functions | Returns `None`, `pass`, or `""` as only body |
| Dead code | Unreachable after `return` / `raise` |
| Over-defensive checks | Redundant null guards on typed/internal paths |
| Duplicate logic | Same 5+ lines copied without domain reason |
| Infrastructure without use | DB/client objects created but never used |

## LOW (flag only)

| Pattern | Examples |
|---------|----------|
| Over-engineering | Factory-for-one-case, unnecessary abstraction layers |
| Buzzword inflation | Comments claiming "robust" without concrete behavior |
| Shotgun surgery smell | Many files changed for a one-concept fix |

## False positives (never auto-fix)

Reject repo-intel `orphan-export` findings for:

- Django `AppConfig`, `Migration`, management `Command` classes
- Framework entrypoints (`wsgi.py`, `asgi.py`, `manage.py`)
- Test functions and pytest fixtures (`test_*`, `make_*` helpers in `tests/`)
- GraphQL schema types registered by framework convention
- `__init__.py` re-exports

Reject `slop-fixes` that would delete required framework wiring.

## Languages

| Layer | Languages |
|-------|-----------|
| Regex (always) | Python, TypeScript/JavaScript |
| AST (with repo-intel) | Python, TypeScript/JavaScript |
