# Chaser Agent social publishing harness direction

**Status:** seeded architecture and roadmap direction; no autonomous public publishing enabled.

## Purpose

Extend Chaser Agent's governed harness model to support public-safe social research, draft generation, human review, media quality checks, publication proof, and analytics learning for ChaseOS-operated brands.

This is a reusable Chaser Agent capability. ChaseOS X is the first pilot, not a hard-coded product identity.

## Current pilot truth

- Browser binding: `chaseos_x`.
- Windows Chrome profile: `Profile 11` / `ChaseOS X`.
- Expected X identity: `@chaseos_ai`.
- Bound launcher opened `https://x.com/home` successfully on 2026-07-11.
- Chrome window title observed: `x.com/home - Google Chrome`.
- CDP port `9231` did not respond from WSL during this inspection. This matches the known limitation that recent Chrome builds may ignore useful remote debugging on the normal user-data root.
- The current screenshot captured the foreground Discord window rather than the background Chrome window, so logged-in account identity and profile contents remain unverified.
- No X composer, profile setting, draft, post, like, follow, or other engagement action was invoked.

## Harness stages

1. **Public-safe source intake**
   - Accept only declared public repository, documentation, website, release, and approved community inputs.
   - Reject private vault, credentials, customer/payment, approval-queue, audit/debug, and unsupported product claims.

2. **Evidence card**
   - Store source URL/path, timestamp, public-safety class, extracted facts, uncertainty, and freshness.
   - Stay silent when no meaningful evidence exists.

3. **Content candidate generation**
   - Generate account-native post variants within the standard account limit.
   - Use a humanizer/voice pass that removes AI boilerplate without inventing personal anecdotes or facts.
   - Bind every draft to a target account and evidence-card IDs.

4. **Media preparation**
   - Capture only an approved public surface.
   - Crop before review and publication.
   - Run deterministic border/edge, blank-area, clipping, minimum-resolution, aspect-ratio, and legibility checks.
   - Reject screenshots containing private tabs, tokens, local paths, Discord private lanes, notifications, or unrelated desktop content.
   - Require a visual readback after crop. A file existing is not proof of acceptable composition.

5. **Private review packet**
   - Show exact copy, character count, links, media preview, source evidence, duplicate score, and proposed target.
   - Decisions: `approve_post`, `approve_draft_save`, `revise`, `reject`.
   - Approval binds exact copy, exact media hash, exact account, and one action.

6. **Browser preflight**
   - Open only the named browser binding.
   - Verify expected profile and logged-in account before touching the composer.
   - Stop on login, password, 2FA, CAPTCHA, suspicious-login prompt, account mismatch, or unavailable background-safe control.

7. **Action and proof**
   - `approve_draft_save` must verify the candidate exists in X Drafts.
   - `approve_post` must publish exactly once and capture the post URL/readback.
   - Missing outcome evidence yields `attempted_unverified`, never `complete`.

8. **Analytics observation**
   - Record available post-level views/impressions, likes, replies, reposts, bookmarks when visible, profile visits/follows when available, link clicks where measurable, and Discord invite joins through an attributed invite or website redirect.
   - Treat analytics as observations, not a reward signal that can self-authorize posting or engagement.
   - Keep raw metric snapshots immutable and separate from strategy recommendations.

9. **Learning proposal**
   - Compare content theme, format, media presence, posting time, CTA, and outcome.
   - Produce a review-only strategy proposal.
   - Never mutate posting policy, voice, frequency, or authority from metrics without approval.

## Voice and engagement policy

- Write like a builder reporting real work, not a corporate announcement generator.
- Prefer concrete shipped behavior, constraints, lessons, and screenshots over vague claims.
- Vary sentence rhythm and avoid repetitive templates.
- Do not manufacture first-person experience, customer demand, adoption, benchmarks, or urgency.
- No engagement bait, mass replies, auto-DMs, follow/unfollow loops, or autonomous likes/reposts.
- Replies and quote posts are separate public actions and require their own bounded policy.

## Media quality contract

Every candidate image should carry a `media_proof.v1` record:

- source capture path and hash;
- crop rectangle and output dimensions;
- target aspect ratio;
- border/edge occupancy scores;
- clipping and blank-margin verdicts;
- OCR/legibility check where text is central;
- private-content scan result;
- final visual-review status;
- exact media hash bound to approval.

Initial image test matrix:

- no accidental black/white border thicker than a configured threshold;
- no clipped title, logo, chart axis, CTA, or primary UI panel;
- no unrelated browser chrome unless intentionally framed;
- no notification badges/private Discord messages;
- minimum useful resolution after crop;
- preview at X feed width before approval;
- final attachment readback after upload.

## Discord operating lanes

Reuse existing lanes before creating duplicates:

- `#chaseos-social-ops` (`1518390727095095479`) - workflow policy, calendar, source selection, and operating decisions.
- `#chaseos-social-drafts` (`1518390731658760263`) - early copy and media candidates.
- `#x-post-approvals` (`1518744738944122971`) - exact-copy/account/media approval and publish/draft-save decision.
- `#content-approvals` (`1517895837047328949`) - cross-platform community content coordination.
- `#public-post-review` (`1517902266332348490`) - final Discord public-post review, not implicit X approval.

Recommended additions only if the existing ops lane becomes noisy:

- `#chaseos-social-analytics` - immutable metric snapshots and weekly growth review.
- `#chaseos-social-media-proof` - cropped screenshots, crop-test verdicts, post URLs, and visual proof.
- `#chaseos-social-moderation` - reply-risk triage and brand-safety review; no autonomous moderation/engagement.

## Initial cadence

- Evidence scan: weekdays, once daily.
- Candidate cap: one meaningful ChaseOS X draft per scan.
- Analytics capture: 24 hours and 7 days after a verified post when metrics are available.
- Weekly review: compare results and propose one bounded experiment.
- Public posting: human-approved only.

## Required implementation before activation

- deterministic source allowlist and private-content deny tests;
- candidate schema and exact-copy hash binding;
- character-count and URL validation;
- media crop/edge-quality evaluator with fixture tests;
- account identity preflight;
- draft-save and publish desired-outcome verification;
- deduplication and one-post idempotency key;
- immutable analytics snapshots;
- emergency pause and replay-safe state;
- Discord review cards with clickable review destinations.

## Explicitly out of scope

- X API spend or credential setup;
- unattended public posting;
- autonomous likes, follows, reposts, replies, quote posts, or DMs;
- creating or rotating a permanent Discord invite without approval;
- editing the X bio, website field, or pinned post without exact-copy approval;
- using StrikeZone browser profiles for ChaseOS social publishing;
- treating analytics optimization as permission to weaken governance.
