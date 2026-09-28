---
title: Sampling Methods
topic: Data Analysis
status: draft
description: Sampling methods involve selecting items from a larger list called the sampling frame to create a sample.
source_files:
- Data and Decisions Lectures.md
source_passages:
- Data and Decisions Lectures.md#9
- Data and Decisions Lectures.md#10
- Data and Decisions Lectures.md#12
generated_by: gemma4:e2b (Q4_K_M)
generated_at: '2026-09-27'
fingerprint: efe03c0ae998adc5ecd98368977a99640e0d78bde580735d84555014e2acedd5
body_sha256: 22eea048775394d3048cc26bc8a9ba43de32b3b4e7ac796e5dc19f5fe7852f8e
---

# Sampling Methods

Sampling methods involve selecting items from a larger list called the sampling frame to create a sample. Different methods exist, such as simple random sampling, stratified sampling, and cluster sampling, which are used to ensure the sample is representative. Understanding these methods is crucial for obtaining unbiased samples and making valid inferences.

## Key points

- A simple random sample (SRS) chooses n items randomly from the frame and is the gold standard; a random number generator can assign each item a uniform number in [0, 1] and select the lowest n (or all below 0.05 for a 5% sample). ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 2]])
- Stratified sampling divides the frame into strata (for example Porsche owners) and does SRS within each. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 2]])
- Cluster sampling divides the frame into geographic clusters, randomly selects some clusters and does SRS within them; it is useful when the area is large and the clusters are similar, and it can save substantial cost. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 2]])
- SRS, stratified and cluster sampling are how we sample to make inferences; the how matters because it is the only way to get representative, unbiased samples. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 2]])
- Sampling bias comes in Lecture 3. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 2]])
- Sampling frame bias: the list you draw from does not match the target population. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 3]])

## Related notes

- [[Sampling Bias]] - This note discusses the systematic error in selecting a sample, which is a key concept related to the methods used in sampling.

## Sources

- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 2: Sampling and Standard Error (lines 74-82)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 2: Sampling and Standard Error (lines 84-86)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 3: Sampling Bias (lines 96-111)
