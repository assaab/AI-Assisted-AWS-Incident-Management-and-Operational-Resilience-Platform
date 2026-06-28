# Well-Architected Gap Review

| Pillar | Current Evidence | Gap | Priority |
| --- | --- | --- | --- |
| Operational Excellence | Runbook, game day, audit trail | Add AWS deployment pipeline evidence | Medium |
| Security | Approval token, policy allowlists, dry-run defaults | Replace demo auth with OIDC | High |
| Reliability | Recovery verification and idempotency | Add worker restart resilience tests | Medium |
| Performance Efficiency | p95 latency tracked | Add load-test evidence | Medium |
| Cost Optimization | Local demo is low-cost | Add AWS cost guardrails for optional deployment | Low |
| Sustainability | Right-sized local stack | Add resource cleanup automation for AWS mode | Low |
