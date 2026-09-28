---
title: Confidence Intervals
topic: Data Analysis
status: draft
description: A confidence interval provides a range of plausible values for a population parameter based on a sample.
source_files:
- Data and Decisions Lectures.md
source_passages:
- Data and Decisions Lectures.md#20
- Data and Decisions Lectures.md#21
- Data and Decisions Lectures.md#24
- Data and Decisions Lectures.md#22
generated_by: gemma4:e2b (Q4_K_M)
generated_at: '2026-09-27'
fingerprint: 56821bd049bfec70a4aa57bfae4d8ed69169bcf70558393dd1daba70ad09cfb6
body_sha256: b44818973fda8a319bd32deb34d120e10359ca17921aa2c7b8cfaee320dc3e0d
---

# Confidence Intervals

A confidence interval provides a range of plausible values for a population parameter based on a sample. Confidence intervals require the confidence level, the sample mean, and the standard error. Hypothesis testing involves using these intervals to test a null hypothesis, where the significance level relates to the risk of making a Type I or Type II error.

## Key points

- A confidence interval is a range of plausible values for a population parameter based on one sample; it needs the confidence level, the sample mean and the standard error. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 5]])
- The 100(1 - alpha)% interval is the sample mean plus or minus t critical value times the standard error. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 5]])
- The margin of error (ME) is an informal 95% interval that replaces the t value by 2: ME = 2 x standard error. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 5]])
- The sample size needed for a target ME is n = 4 sigma squared over ME squared. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 5]])
- The probability of a Type II error depends on the alternative and is generally smaller when the truth is far from the null. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 5]])
- The significance level alpha (typically 0.05 or 0.01) is the maximum tolerated Type I error. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 5]])

## Related notes

- [[Hypothesis Testing]] - Confidence intervals are used in conjunction with hypothesis testing to make decisions about population parameters.
- [[Standard Error]] - The calculation of a confidence interval requires the standard error of the sample mean.
- [[Type I and Type II Errors]] - The concept of Type I and Type II errors is central to understanding the risks associated with making decisions based on sample data.
- [[Control Limits]] - The text mentions control limits in the context of checking whether a production process is broken, which relates to setting boundaries for data.

## Sources

- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 5: Confidence Intervals and Hypothesis Testing (lines 174-181)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 5: Confidence Intervals and Hypothesis Testing (lines 183-187)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 5: Confidence Intervals and Hypothesis Testing (lines 189-194)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 5: Confidence Intervals and Hypothesis Testing (lines 209-215)
