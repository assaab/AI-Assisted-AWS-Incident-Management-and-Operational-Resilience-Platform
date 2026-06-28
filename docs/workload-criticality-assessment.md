# Workload Criticality Assessment

| Attribute | Checkout Workload |
| --- | --- |
| Business capability | Customer checkout and order capture |
| Criticality | Mission-critical |
| Availability target | 99.9% for demo scope |
| RTO | 15 minutes |
| RPO | 5 minutes |
| Primary dependency | Payments API |
| Secondary dependencies | Inventory API, orders database |
| Customer impact | Failed purchases and revenue loss |
| Severity mapping | `sev2` for sustained elevated checkout errors |

## Key Signals

Error rate, p95 latency, deployment revision, payment timeout logs, and checkout health status.
