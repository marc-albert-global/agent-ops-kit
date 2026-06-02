---
name: churn-analysis
description: Analyze customer and revenue churn, retention, and the difference between gross and net
triggers: [churn, retention, attrition, logo, gross, net, nrr, grr, dollar]
---

When analyzing churn and retention:

1. Distinguish **logo churn** (count of accounts lost) from **revenue churn**
   (MRR lost). They diverge sharply when churn concentrates in small or large
   accounts, always say which one the number refers to.
2. Report **Gross Revenue Retention (GRR)** and **Net Revenue Retention (NRR)**
   together. GRR = (starting MRR - contraction - churn) / starting MRR, capped
   at 100%. NRR adds expansion back in and can exceed 100%. NRR alone can mask
   a churn problem that expansion is papering over.
3. Use a consistent cohort window (typically trailing 12 months) and state it.
4. Flag whether churn is voluntary (cancellation) or involuntary (failed
   payment) when the data allows, the remediation is completely different.
