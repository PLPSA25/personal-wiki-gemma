---
title: Causal Inference
topic: Data Analysis
status: draft
description: Causal inference is the process of determining if an action causes an outcome, which is distinct from mere prediction based on association.
source_files:
- Data and Decisions Lectures.md
source_passages:
- Data and Decisions Lectures.md#26
- Data and Decisions Lectures.md#52
- Data and Decisions Lectures.md#49
- Data and Decisions Lectures.md#51
generated_by: gemma4:e2b (Q4_K_M)
generated_at: '2026-09-27'
fingerprint: 1a4371bcdd9e1cdc327f31af0e940b60fed0b523a9f9a1aa9a9cf86c2b11caa8
body_sha256: 80c92cb4570064dcd762ac34db14c01048e67d87a8b788a864d32b97d00d9e1f
---

# Causal Inference

Causal inference is the process of determining if an action causes an outcome, which is distinct from mere prediction based on association. Experiments, particularly randomized controlled trials, are a method used to establish causation by controlling for confounding variables. Omitted variable bias occurs when relevant variables are left out of a model, leading to biased estimates of causal effects.

## Key points

- An experiment (randomized controlled trial, RCT) randomizes treatment and control status to produce data that reveal causation. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 6]])
- Causal impact is prescriptive: there is a counterfactual absent the action (the change in sales with and without a change in advertising, holding everything else constant; in an experiment the counterfactual comes from the control group). ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 10]])
- Observational comparisons suffer from omitted or "lurking" variables (bacon eaters might also smoke more and exercise less); observational relationships are rarely causal, and correlation is not causation. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 6]])
- Whenever a variable left out of the model is correlated with both (1) a variable we control for and (2) the outcome, the estimates for the included variables are biased: the marginal slope differs from the partial slope. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 10]])
- If the omitted variable has a positive effect and is positively correlated with the included variable (or both are negative), the bivariate coefficient is biased upward; if the signs are opposite it is biased downward. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 10]])
- Randomization eliminates bias. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 10]])

## Related notes

- [[Omitted Variable Bias]] - This note is relevant because it directly addresses the problem of bias that arises when variables are left out of a model, which is a key concern in causal inference.
- [[A-B Testing]] - This note is relevant because randomized controlled trials, which are central to establishing causation, rely on randomization.

## Sources

- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 6: Comparing Means and A/B Testing (lines 228-237)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 10: Omitted Variables, Causal versus Predictive Questions (lines 419-423)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 10: Omitted Variables, Causal versus Predictive Questions (lines 435-437)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 10: Omitted Variables, Causal versus Predictive Questions (lines 439-444)
