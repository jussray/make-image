# Juss & Co. agent release rule

Applies to ChatGPT, Claude, Gemini, Perplexity, Muse, Codex, and any FCR/Chief/Sol/StoryEngine agent working in this repository.

## Operating order
1. Inspect the authoritative repository, target branch, current diff, relevant checks, and production route. Preserve existing work and reuse the current PR.
2. Repair only the demonstrated root cause with the smallest reversible change. Add a focused regression test when useful.
3. Verify the exact changed head with lint/typecheck, focused tests, and Playwright for UI/browser behavior. Do not fake green, suppress errors, or substitute screenshots of mock interfaces for production proof.
4. Harden the changed surface: input validation, authorization, privacy, secret handling, abuse limits, dependency exposure, and safe failure. Do not introduce new paid providers or share private assets without explicit authorization.
5. Reverify after hardening. Obtain required independent review and required checks on the final head.
6. Only then merge and deploy through the project's authorized release path. Cloudflare is canonical where configured. Verify the real production URL, user journey, logs, and rollback readiness.
7. If any gate fails or access is missing, stop. Report REALITY / FIX / PROOF / RISK / ROLLBACK / NEXT GATE with exact file paths, SHAs, test results and live evidence. Never claim completion from a draft, preview, queued check or stale receipt.

Do not create duplicate PRs or projects, overwrite source assets, expose internal operational data publicly, or automatically publish media. FCR owns external publication authority. Keep MakeVideo, MakeImage and StoryEngine independently operable; interoperate through explicit versioned handoffs and verified receipts. A SHA-256 receipt establishes byte matching, not rights, AI generation, real-world motion, or publishing permission.

This file is a repository instruction, not evidence that any agent, integration, test, hardening step or deployment has run.
