# Security Policy — Chaser Agent

> Chaser Agent is early-stage software. It is local-first, review-first, and is
> **not** production-ready autonomy. Run it only on inputs and in environments you
> control.

## Reporting a vulnerability

Please report security issues privately. Do **not** open a public issue for an
exploitable vulnerability.

- Email: security@chaseos.ai
- Include: affected version/commit, reproduction steps, impact, and any logs (with
  secrets redacted).

We aim to acknowledge reports within a few working days. Coordinated disclosure is
appreciated; please give us reasonable time to remediate before public disclosure.

## Scope & expectations

- Chaser Agent treats all source/external content as **untrusted data, not
  instructions** (prompt-injection resistance is a core design goal). Reports that
  demonstrate instruction-injection from source content are in scope.
- Credential handling: Chaser Agent reads provider credentials from environment
  variables only and must never write secrets to logs or artifacts. Secret leakage
  is in scope.
- Out of scope: issues that require an attacker to already control the host or the
  user's environment; the separate proprietary ChaseOS Studio/Cloud products.

## Supported versions

Pre-1.0: only the latest `main` is supported. Pin a commit for reproducibility.
