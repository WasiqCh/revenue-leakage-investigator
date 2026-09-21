# TICKET-041 - Next.js scaffold, API client and role switcher

- **Status:** TODO
- **Phase:** 8 - Frontend
- **Effort:** 1.0 day
- **Depends on:** TICKET-037

## Goal

App Router, Tailwind, shadcn/ui, a typed API client and a role switcher.

## What this means

The website shell and a way to switch between the pretend user types so the demo can show permissions working.

## Context

The API client is typed against the generated OpenAPI schema - no `any`.

## Deliverables

- `frontend/app/layout.tsx`
- `frontend/lib/api.ts`
- `frontend/components/role-switcher.tsx`

## Acceptance criteria

- [ ] `next build` succeeds
- [ ] the client is typed against the OpenAPI schema
- [ ] switching roles visibly changes available actions
- [ ] zero `any` types in lib/api.ts

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
