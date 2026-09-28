---
title: Linear Regression
topic: Data Analysis
status: reviewed
description: Linear regression uses ordinary least squares to find the line that minimizes the sum of squared residuals between the data and the fitted line.
source_files:
- AuraTech Case.docx
- Data and Decisions Lectures.md
source_passages:
- AuraTech Case.docx#2
- Data and Decisions Lectures.md#33
- Data and Decisions Lectures.md#35
- Data and Decisions Lectures.md#46
generated_by: gemma4:e2b (Q4_K_M)
generated_at: '2026-09-27'
fingerprint: ae87528149f6f9c584864a91200c049654abe3bd7be8602c8539d198d9baa7db
body_sha256: c53c677efacfcf4e445a5f5fd9491c89e70a3f46f241faad62d33ca06bd053f9
---

# Linear Regression

Linear regression uses ordinary least squares to find the line that minimizes the sum of squared residuals between the data and the fitted line. The slope and intercept are calculated based on the data, and residuals represent the vertical deviations from the data points to the fitted line. The model's explanatory power is measured by R squared, and prediction intervals can be calculated using the residual standard deviation.

## Key points

- Estimated price = b0 + b1 weight. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 7]])
- The OLS line is the line that minimizes the sum of squared residuals. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 7]])
- The slope equals the correlation r times the standard deviation of y over the standard deviation of x, and the intercept equals the mean of y minus the slope times the mean of x. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 7]])
- The approximate 95% prediction interval is still the predicted value plus or minus 2 times the residual standard deviation. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 9]])
- R squared measures the fraction of variation in y explained by the explanatory variables. ([[raw/Data and Decisions Lectures|Data and Decisions Lectures, Lecture 9]])
- The slope: 2.53 ([[raw/AuraTech Case.docx|AuraTech Case]])

## Related notes

- [[AuraTech Case]] - This note provides specific calculations for the intercept and slope derived from a case example.
- [[Standard Error]] - The standard error is related to the standard error of the regression and the standard deviation of the residuals.

## Sources

- [[raw/AuraTech Case.docx|AuraTech Case]] - AuraTech Case (lines 9-13)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 7: Basics of Linear Models (Regression) (lines 288-294)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 7: Basics of Linear Models (Regression) (lines 303-311)
- [[raw/Data and Decisions Lectures|Data and Decisions Lectures]] - Lecture 9: Multiple Regression and Experiments as Regressions (lines 395-404)
