# ADR-009: Cloudflare AI Search is not the product's retrieval path

**Status:** Accepted — 2026-09-21

## What this means

**Retrieval** is how the system finds the right few paragraphs of a contract to show the AI, instead of dumping the whole document into the prompt. Cloudflare AI Search — formerly called AutoRAG — is a managed service that does retrieval for you: you upload documents, it indexes them, and you query it. "Managed" means Cloudflare runs the indexing, the search and the storage, so we operate none of it. It is genuinely capable: it offers automatic indexing, hybrid keyword-plus-meaning search, filtering on **metadata** (the labels attached to a document), and an **MCP endpoint**, a standard way for AI tools to call it. It would work here. **We are rejecting it for the product path anyway.** First, the retrieval pipeline is a headline capability this project exists to demonstrate, and outsourcing it means the thing we claim to have built is a service someone else built. Second, evidence integrity: a citation must point at an immutable row tied to a specific case, contract and amendment, re-verifiable against our own database at any time, which a black box does not give us. Third, the specification requires measuring retrieval precision, recall and citation accuracy, and you cannot measure those honestly against a system whose internals you cannot inspect. We accept it in one narrow place: an **optional comparison baseline** in the evaluation suite (TICKET-048), which scores our retrieval against Cloudflare's on the same questions and **skips when credentials are absent**, so the normal test run never depends on it.

## Context

The choice was attractive and deserves an honest account of why. Retrieval is hard to get right — chunking, embedding, hybrid ranking, metadata filters, re-ranking — and a managed service removes all of it, including the operational burden. If the goal were to ship a product quickly, this decision would go the other way. But the goal is also to demonstrate the capability: the brief is explicit that the retrieval and evidence layer is what is being shown, and the evaluation targets are stated in terms of retrieval precision, recall and citation accuracy. Those are claims about our pipeline, and a managed service would turn them into claims about Cloudflare's that we cannot substantiate. Evidence integrity is the harder argument. This product tells a Finance reviewer that a specific clause in a specific contract version supports a specific money claim. That citation must be re-checkable months later, after the contract has been amended, against the same text the case was built from — so the retrieved passage must be an immutable stored row with provenance we control: which contract, which version, which amendment, which ingest run, which embedding model. A hosted index that re-chunks or re-embeds on its own schedule breaks that chain, and we would have no way to detect the change.

## Decision

**Cloudflare AI Search (formerly AutoRAG) is rejected for the product path. Retrieval is implemented in-house against our own Postgres and pgvector index. It is accepted only as an optional, skippable comparison baseline in the evaluation suite.**

- Clauses are chunked, embedded with a chosen model, stored in Postgres via pgvector, and searched with hybrid keyword-plus-vector ranking and metadata filters.
- Every retrieved passage is persisted as an immutable evidence row carrying contract, version, amendment, ingest run, embedding model and a content hash.
- The Verifier re-checks each citation against the database at report time, per [ADR-004](ADR-004-read-only-role-guardrail.md).
- TICKET-048 adds an optional baseline that queries Cloudflare AI Search with the same evaluation questions, gated on credentials being present; when they are absent the comparison is skipped with a clear message and the suite still passes.
- Nothing in the product's runtime depends on Cloudflare, and `make test` never reaches the network.

## Alternatives considered

- **Adopt Cloudflare AI Search as the retrieval path.** Rejected for the three reasons above. It would work technically, but it hollows out the thing being demonstrated and makes our evaluation claims unsubstantiable.
- **Adopt it for ingestion while keeping our own evidence store.** Rejected. It splits retrieval across two systems: we would still own the evidence and the verification, while the actual ranking happens somewhere we cannot inspect or tune. We would pay the integration cost and keep most of the work.
- **A self-hosted vector database (Qdrant, Weaviate, Milvus).** Rejected. The same capability pgvector already gives us inside the database we must run anyway, at the cost of a second stateful service — contrary to ADR-002 and ADR-005.
- **A hosted vector service (Pinecone and similar).** Rejected. The same argument as Cloudflare, plus it puts contract text in a third party's index and adds a network dependency to the demo.
- **Pure keyword search (Postgres full-text) with no embeddings.** Rejected as the only method. It is a useful half of hybrid search and we keep it, but it cannot match a paraphrase — a question about "seat count" will not find a clause that says "number of authorised users".
- **Cloudflare AI Search as the only evaluation baseline.** Rejected. A single external baseline would make our headline numbers depend on someone else's availability. The internal golden set is the primary measure.

## Consequences

**Easier.** We own the ranking, so we can tune it, explain it, and report precision and recall that mean something. Evidence rows are immutable and re-verifiable, so citations survive contract amendments and months of elapsed time. There is one fewer external dependency and credential in the product path, and the evaluation suite runs offline by default, which keeps `make test` honest.

**Harder.** We implement chunking, embedding, hybrid ranking and metadata filtering ourselves, and we operate the index — re-embedding when the model changes, re-indexing when chunking changes, and tracking which ingest run produced which evidence. That is real work a managed service would have absorbed, and reaching good retrieval quality will take longer.

**Negative.** We will probably be worse at retrieval than Cloudflare for a while, and a reviewer is entitled to ask why we did not use the better tool. The answer only holds while the comparison baseline exists and is actually run, which means the baseline is optional in CI but not optional in spirit. There is also a maintenance liability: an in-house index is ours to keep working, and a future maintainer may reasonably conclude the opposite of this ADR.

## How to reverse it

Switching to Cloudflare AI Search means replacing the retriever behind its existing interface, migrating evidence rows to reference hosted document identifiers instead of content hashes, and giving up the local re-verification guarantee — which would require revising the citation-accuracy target in `docs/evaluation.md` and the evidence-integrity claims in `docs/TRD.md`.
