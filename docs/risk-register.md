# Risk Register

| Risk | Owner | Priority | Status | Verification Method |
| --- | --- | --- | --- | --- |
| Bad deployment reaches all checkout traffic | Checkout owner | High | Open | Canary and rollback game day |
| Approval path is unavailable during incident | Operations manager | High | Mitigated | Demo approval and expiry test |
| Recovery signal is too weak | SRE lead | High | Mitigated | Error rate and p95 latency verification |
| Duplicate execution after retry | Platform owner | High | Mitigated | Durable idempotency key table |
| Database outage hides audit records | Platform owner | Medium | Mitigated | Non-demo readiness fails closed |
| AWS adapter accidentally executes real action | Platform owner | High | Mitigated | AWS profile dry-run default |
