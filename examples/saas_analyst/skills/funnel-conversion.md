---
name: funnel-conversion
description: Analyze acquisition funnel conversion, visit, signup, activation, paid conversion
triggers: [funnel, conversion, signup, activation, trial, acquisition, visit, lead, cac]
---

When analyzing the acquisition funnel:

1. Define each stage transition explicitly before computing rates: Visit→Signup,
   Signup→Activation, Activation→Paid. Report stage-to-stage conversion, not
   only the end-to-end rate, the end-to-end number hides which stage is the
   constraint.
2. Always pair conversion rate with absolute volume. A rate improvement on a
   shrinking top of funnel can still mean fewer paid customers.
3. When comparing periods, hold the funnel definition constant. A definitional
   change (e.g. what counts as "activation") is the most common cause of a
   spurious conversion swing.
4. If asked about CAC payback, state the assumed gross margin and the period.
