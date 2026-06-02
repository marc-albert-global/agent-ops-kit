---
name: metric-definitions
description: Canonical definitions of core SaaS metrics used across all analyses
keywords: [mrr, arr, nrr, grr, churn, cac, ltv, definition, formula, payback]
---

Canonical metric definitions. Use these exact formulas; do not improvise
variants.

- **MRR**: Monthly Recurring Revenue. Sum of normalized monthly subscription
  value of all active accounts at period end. Exclude one-time fees.
- **ARR**: MRR x 12 (run-rate). Booked ARR is contract value and is tracked
  separately; never combine the two in one figure.
- **Net New MRR** = New + Expansion - Contraction - Churned MRR.
- **GRR** (Gross Revenue Retention) = (Start MRR - Contraction - Churn) / Start
  MRR. Capped at 100%.
- **NRR** (Net Revenue Retention) = (Start MRR - Contraction - Churn +
  Expansion) / Start MRR. Can exceed 100%.
- **Logo churn rate** = accounts lost in period / accounts at period start.
- **CAC** = fully-loaded sales & marketing spend / new customers acquired, same
  period.
- **LTV** = (ARPA x gross margin) / revenue churn rate.
- **CAC payback (months)** = CAC / (ARPA x gross margin).

Every reported figure must carry its measurement period and comparison base.
