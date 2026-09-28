---
title: Omitted Variable Bias
topic: Data Analysis
status: draft
description: Omitted variable bias occurs when a variable is left out of a model but is correlated with both a variable being controlled for and the outcome.
source_files:
- AuraTech Case.docx
- Data and Decisions Lectures.md
source_passages:
- Data and Decisions Lectures.md#49
- Data and Decisions Lectures.md#45
- Data and Decisions Lectures.md#53
- AuraTech Case.docx#4
generated_by: gemma4:e2b (Q4_K_M)
generated_at: '2026-09-27'
fingerprint: f618d5660972893a31b6b86426580d596a2663b60f257d4f740608da4a975a0b
body_sha256: 8c892079dc82bbffe122d98127a013648401d276f714c63e7bdca24b16e6a7f4
---

# Omitted Variable Bias

Omitted variable bias occurs when a variable is left out of a model but is correlated with both a variable being controlled for and the outcome. This causes the estimates for the included variables to be biased, which is a problem when trying to infer causal effects. The direction of this bias depends on the relationship between the omitted variable and the included variables.

## Key points

- Whenever a variable left out of the model is correlated with both (1) a variable we control for and (2) the outcome, the estimates for the included variables are biased: the marginal slope differs from the partial slope. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 10]])
- The marginal slope is the slope in a bivariate regression, which combines the partial slope with all other correlated channels of influence (omitted variables and indirect effects). ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 9]])
- If the omitted variable has a positive effect and is positively correlated with the included variable (or both are negative), the bivariate coefficient is biased upward; if the signs are opposite it is biased downward. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 10]])
- The omitted variable bias in a slope depends on the omitted variable's direct effect times its relationship with the included variable. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 10]])
- With a single explanatory variable it is a marginal slope, so it quietly carries along everything correlated with the AI estimate: the artist, the medium, and above all the auction house’s own reading of the piece. ([[raw/AuraTech Case.docx|AuraTech Case]])

## Related notes

- [[Causal Inference]] - Omitted variable bias is a problem when one is trying to care about causal effects.
- [[A-B Testing]] - Randomization, a technique related to experiments, is mentioned as a way to eliminate bias.
- [[Type I and Type II Errors]] - The context of bias relates to the validity of statistical inferences.

## Sources

- [[raw/AuraTech Case.docx|AuraTech Case]] - AuraTech Case (lines 21-25)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 9: Multiple Regression and Experiments as Regressions (lines 385-393)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 10: Omitted Variables, Causal versus Predictive Questions (lines 419-423)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 10: Omitted Variables, Causal versus Predictive Questions (lines 446-448)
