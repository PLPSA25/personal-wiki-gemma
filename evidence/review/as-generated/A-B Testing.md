---
title: A-B Testing
topic: Data Analysis
status: draft
description: A-B testing involves randomizing treatment and control status to determine causation.
source_files:
- Data and Decisions Lectures.md
source_passages:
- Data and Decisions Lectures.md#26
- Data and Decisions Lectures.md#28
- Data and Decisions Lectures.md#51
- Data and Decisions Lectures.md#42
generated_by: gemma4:e2b (Q4_K_M)
generated_at: '2026-09-27'
fingerprint: 3606d7df24a7aae29388ecba171357aa4fbde9a513e1d7aa15638a9a325ba507
body_sha256: ce299a43a27192e905dcfc62903353ac4169fd712e5dcce407c06ae7cf6e3a58
---

# A-B Testing

A-B testing involves randomizing treatment and control status to determine causation. This method is motivated by causal inference, aiming to establish whether a specific action causes a particular outcome. Randomization helps ensure that the treatment and control groups are identical, which minimizes bias.

## Key points

- An experiment (randomized controlled trial, RCT) randomizes treatment and control status to produce data that reveal causation. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 6]])
- Randomization makes treatment and control groups identical in everything except the treatment (the same logic as why an SRS is representative), so an RCT has no bias, though watch for attrition (do you observe outcomes for everyone?); it is also transparent and highly credible. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 6]])
- Internal validity: have you identified the causal effect of the treatment (are treatment and control different only in the treatment)? ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 6]])
- External validity: can you generalize to other contexts? ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 6]])
- Randomization eliminates confounding factors; selection into treatments is the main worry in observational studies. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 10]])
- The A/B data can be put into a regression with a 0/1 variable: B_group = 1 for Design B (the treatment) and 0 for Design A (the control). ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 9]])

## Related notes

- [[Causal Inference]] - A-B testing is motivated by the goal of causal inference, which is to determine if one action causes another.
- [[Omitted Variable Bias]] - Randomization is used to eliminate bias, which is a key concern when dealing with omitted variables.

## Sources

- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 6: Comparing Means and A/B Testing (lines 228-237)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 6: Comparing Means and A/B Testing (lines 239-253)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 9: Multiple Regression and Experiments as Regressions (lines 362-370)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 10: Omitted Variables, Causal versus Predictive Questions (lines 435-437)
