# Resilience Game Day

## Scenario

Inject a checkout deployment regression and validate that the platform detects, diagnoses, rolls back, verifies, and reports the recovery.

## Command

```powershell
make demo
make scenario-checkout-failure
```

## Success Criteria

| Check | Expected Result |
| --- | --- |
| Failure injection | Checkout error rate rises above 1% |
| Incident creation | New `checkout-service` incident appears |
| Plan | Rollback deployment action is proposed |
| Approval | Tokenized approval is attached to the action |
| Execution | Local workload revision returns to `checkout-r42` |
| Verification | Healthy metrics are recorded |
| Reporting | PIR and executive summary are generated |

## Stop Conditions

Stop the test if the service cannot be reset, verification is unavailable, or an action would target a non-demo environment.
