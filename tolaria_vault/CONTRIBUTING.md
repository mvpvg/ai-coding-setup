# Contributing to the Tolaria Vault

**Everything in this folder is public.** It is shipped in the release zip and lives in a public GitHub repository.

Before adding or editing a note, check:

- No PII — no real names, email addresses, or personal identifiers.
- No internal company info — no client names, internal project names, or confidential architecture details.
- No credentials — no API keys, tokens, passwords, or any value that looks like a secret.
- No speculative pricing — link to official pricing pages rather than quoting numbers that will go stale.

## What belongs here

| Folder | Suitable content |
|--------|-----------------|
| `decisions/` | Tool choices, architecture rationale, trade-offs — generic and reusable |
| `patterns/` | How to use tools correctly — commands, timing, anti-patterns |
| `bugs/` | Known gotchas and reproducible postmortems — no private reproduction details |
| `onboarding/` | Step-by-step setup checklists for new machines |

## What does not belong here

- Session-specific notes or work-in-progress reasoning → use `PROJECT.md` (gitignored by default) or mem0 instead.
- Personal preferences unrelated to the stack → keep in your own private vault.
- Company-specific or client-specific information → keep offline or in a private vault.

If you are unsure whether a note is safe to publish, keep it out.
