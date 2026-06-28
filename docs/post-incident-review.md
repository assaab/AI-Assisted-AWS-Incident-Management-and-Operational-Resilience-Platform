# Post-Incident Review

## Incident

Checkout deployment regression in revision `checkout-r43`.

## Impact

Elevated checkout latency and payment timeout errors.

## Root Cause

The most recent deployment introduced an application-level regression.

## Recovery

Rollback to revision `checkout-r42`, followed by business metric verification.

## Follow-Up Actions

| Action | Owner | Priority | Status | Verification |
| --- | --- | --- | --- | --- |
| Add canary deployment gate | Checkout owner | High | Open | Canary blocks synthetic regression |
| Add rollback approval drill | Operations manager | Medium | Open | Quarterly game day evidence |
| Add AWS ECS dry-run contract tests | Platform owner | Medium | Planned | CI contract test |
