---
title: Hypothesis Testing
topic: Data Analysis
status: draft
description: Hypothesis testing involves setting up a null hypothesis and an alternative hypothesis to determine if there is enough evidence to reject the null.
source_files:
- Data and Decisions Lectures.md
source_passages:
- Data and Decisions Lectures.md#22
- Data and Decisions Lectures.md#23
- Data and Decisions Lectures.md#39
- Data and Decisions Lectures.md#25
generated_by: gemma4:e2b (Q4_K_M)
generated_at: '2026-09-27'
fingerprint: 28538396e7593062199523b90ce7b7bd8d39f6cdc9c507ab6e885b3ec4e0da93
body_sha256: d43c045503969db16db484d8c35b54d9873bdf906ad94dabb45ee9813302e3cd
---

# Hypothesis Testing

Hypothesis testing involves setting up a null hypothesis and an alternative hypothesis to determine if there is enough evidence to reject the null. This process relies on calculating a test statistic and comparing its resulting p-value to a chosen significance level to make a decision.

## Key points

- The null hypothesis (H0) is the default, status-quo course of action (mean weight of 29.7 or more); the alternative (Ha) contradicts it and supports change (mean below 29.7). ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 5]])
- The significance level alpha (typically 0.05 or 0.01) is the maximum tolerated Type I error. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 5]])
- A statistic is statistically significant if its p-value is below alpha. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 5]])
- The p-value is how likely you would be to get this result, or a more extreme one, if the null were true; it is the probability of a Type I error if you set the rejection threshold at your current estimate. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 5]])
- To test H0: slope = 0 use t = b1 divided by its standard error, with n - 2 degrees of freedom; likewise for the intercept. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 8]])
- A two-sided test has H0: mean equals the value and its p-value is twice the one-sided p-value, so it is more conservative. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 6]])

## Related notes

- [[Confidence Intervals]] - Confidence intervals are related because a pilot sample gives a confidence interval for the population mean, and confidence intervals for coefficients are calculated using t critical values.
- [[Type I and Type II Errors]] - The concept of Type I and Type II errors is central to hypothesis testing, as the process involves calculating the probabilities of these error types.
- [[Decision Trees]] - No clear connection is established between hypothesis testing and decision trees based on the provided passages.

## Sources

- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 5: Confidence Intervals and Hypothesis Testing (lines 189-194)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 5: Confidence Intervals and Hypothesis Testing (lines 196-207)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 6: Comparing Means and A/B Testing (lines 219-226)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 8: Regression with One X Variable and Inference (lines 341-347)
