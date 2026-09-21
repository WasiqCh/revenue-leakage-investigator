# Third-party notices

This file records the licensing position of third-party material used by this
project. It exists so that anyone picking up this repository knows exactly what
is ours, what is not, and what must never be redistributed.

---

## This project

The AI Revenue Leakage Investigator is released under the **MIT licence**. See
[LICENSE](LICENSE) for the full text.

Everything in this repository — the specification, the architecture, the
documentation, the tickets, the synthetic data generators, the application code —
is covered by that licence, **except** the third-party material described below.

---

## CUAD — the third-party dataset

### What it is

**CUAD** is the *Contract Understanding Atticus Dataset*: 510 real commercial
contracts, annotated by lawyers with approximately 13,000 clause labels. It is
published by The Atticus Project.

This project uses CUAD in two ways, both of them narrow:

1. **Retrieval realism.** The contracts are split into clauses, each clause is
   converted into a vector by an existing embedding model, and the clauses are
   searched. This gives the search layer real, messy legal prose to work against
   instead of text we invented ourselves.
2. **A free answer key.** The lawyer-made clause labels let us score how
   accurately our clause extraction works, without paying humans to label
   anything.

**We do not train any model on CUAD.** We download text, split it into clauses,
embed each clause, and search it later. That is retrieval, not training. See
[ADR-007](docs/adr/ADR-007-cuad-real-data-non-redistribution.md) for the full
reasoning.

### Licence position: unknown, and treated as unknown

**The licence of the CUAD dataset is not clearly published**, on either of:

- the Zenodo record (https://zenodo.org/records/4595826), or
- the GitHub repository (TheAtticusProject/cuad).

Because the licence cannot be established from those sources, this project
**treats CUAD as having unknown licensing status**. No permission is assumed and
none is implied. We do not claim any right to redistribute it.

### What that means in practice

These are not guidelines. They are enforced.

| Rule | How it is enforced |
|---|---|
| Contract text is never committed to this repository | The cache directory is listed in `.gitignore`. The downloader writes outside the repo tree. |
| Contract text is never redistributed | Nothing in this repository contains CUAD contract text. The only committed artifact is a small offline fixture of a few records used for tests. |
| The licence is checked, and the check is loud | `scripts/fetch_cuad.py` reads the licence from the archive and **fails loudly if it cannot be determined**. It does not silently proceed on an unknown licence. |
| The archive is verified | The downloader checks the archive hash against the known value, and re-downloads on a mismatch. |
| Tests never need the network | With `CUAD_OFFLINE=1`, the committed fixture is used instead of the real dataset, so the test suite runs with no network access at all. |

If you fork this project, you must make your own assessment of CUAD's licence
before using the dataset yourself. Nothing here grants you any right to it.

### Real company names never reach the product

CUAD source documents are real contracts and contain real company names.

**Real company names appearing in CUAD source documents never reach the
`customer` table or the UI. Synthetic names are used throughout.**

CUAD text is used as *prose to search and extract from*. It is never used as
customer data. Every customer, contract, invoice and usage record that appears in
the database or on screen is generated synthetically. This keeps real commercial
relationships out of the product entirely.

### Citation

If you use CUAD, cite it as:

> The Atticus Project. *CUAD: Contract Understanding Atticus Dataset*, v1. Zenodo.
> https://zenodo.org/records/4595826
> arXiv:2103.06268

---

## Other third-party components

The application depends on open-source libraries — PostgreSQL 16 with the
pgvector extension, FastAPI, SQLAlchemy, Alembic, Pydantic, Next.js, React,
Tailwind CSS, and others. Each is used under its own licence, and each is listed
with its version and licence in the dependency manifests:

- `backend/pyproject.toml` — Python dependencies
- `frontend/package.json` — JavaScript and TypeScript dependencies

These libraries are **not vendored**. They are installed from their normal
package sources, so their own licence files travel with them.

The base container images used by `docker-compose.yml` (PostgreSQL with pgvector,
and the Python and Node base images) are likewise used under their own licences
and are pulled at build time, not redistributed here.

---

## Summary

| Material | Licence | Redistributed in this repo? |
|---|---|---|
| This project (code, docs, tickets, synthetic generators) | MIT | Yes |
| CUAD contract text | Unknown — treated as unknown | **No** |
| CUAD-derived clause labels used for scoring | Unknown — treated as unknown | **No** |
| Open-source libraries | Their own (permissive) | No — installed from package sources |
| Base container images | Their own | No — pulled at build time |

---

## Where to go next

- The full reasoning behind the CUAD decision:
  [ADR-007](docs/adr/ADR-007-cuad-real-data-non-redistribution.md)
- Where the data comes from: [README.md](README.md)
- Operational guidance on fetching CUAD: [docs/runbook.md](docs/runbook.md)
