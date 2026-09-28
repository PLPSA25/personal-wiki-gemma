---
title: Control Limits
topic: Data Analysis
status: draft
description: Control limits are thresholds that form a decision rule, typically a symmetric interval around the mean based on the mean plus or minus a multiple of the standard error.
source_files:
- Data and Decisions Lectures.md
source_passages:
- Data and Decisions Lectures.md#16
- Data and Decisions Lectures.md#17
generated_by: gemma4:e2b (Q4_K_M)
generated_at: '2026-09-27'
fingerprint: f3deaac49fb80b3598a081aebf103f4162290af106e84fb1c7146c404e48b41b
body_sha256: f89334e26a39a09e53323ef4ba9f66174381de02fe5e9aedc2a619a2bac01946
---

# Control Limits

Control limits are thresholds that form a decision rule, typically a symmetric interval around the mean based on the mean plus or minus a multiple of the standard error. These limits are used to determine whether a sample average indicates a random variation or a change in the process. Balancing the control limits involves a trade-off between Type I and Type II errors.

## Key points

- Control limits are thresholds forming a decision rule: a symmetric interval around the mean, mu plus or minus k times the standard error. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 4]])
- If the sample average falls outside the bars, stop the machines; if inside, keep going. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 4]])
- The Type I error probability is typically set at 5% or 1%. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 4]])
- Wide control limits reduce Type I error (you stop only for ultra-bad outcomes) but raise Type II error; narrow limits reduce Type II error (you almost always stop when there is a real problem) but you stop more often for nothing. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 4]])
- The standard error is proportional to the population standard deviation, inversely proportional to the square root of the sample size, and does not depend on the population size. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 4]])
- The sample average is Normal if either the sample is large enough (Central Limit Theorem) or the population is Normal to begin with. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 4]])

## Related notes

- [[Type I and Type II Errors]] - Control limits are used in conjunction with understanding the probabilities of Type I and Type II errors when setting the decision rule.
- [[Standard Error]] - Control limits are defined in terms of the mean and the standard error.
- [[Confidence Intervals]] - The concept of control limits is related to the use of confidence intervals for determining process status.

## Sources

- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 4: Control Limits and Type I and Type II Errors (lines 135-145)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 4: Control Limits and Type I and Type II Errors (lines 147-155)
