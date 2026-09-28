# Ask test: test-1 (direct)

**Question:** What sample size guarantees a margin of error of plus or minus 3 percentage points in a political poll?

- Interaction mode: **ask** (standalone, no chat history, no persona) | Execution: **local** (Ollama on 127.0.0.1, no internet needed)
- Run: `run-6-final-index` at 2026-09-28T03:34:37+00:00
- Model: `gemma4:e2b` | quantization Q4_K_M | 5.1B parameters | digest `7fbdbf8f5e45a75b` | Ollama 0.34.3
- Settings: temperature 0.1, seed 7, max answer tokens 400, context window 8192, top-k 5, thinking off

## Expected (answer key, kept outside the vault)
- Behaviour: `answer`
- Expected sources: Data and Decisions Lectures.md
- Expected section: Lecture 5: Confidence Intervals and Hypothesis Testing
- Expected passage/content: a plus-or-minus 3 percentage point poll needs 1/(0.03 squared) = 1,112 people

## Retrieved passages (top 5, before the model saw anything)

### [S1] Data and Decisions Lectures.md > Lecture 5: Confidence Intervals and Hypothesis Testing (lines 183-187, score 22.81)
> **Margin of error.** The margin of error (ME) is an informal 95% interval that replaces the t value by 2: ME = 2 x standard error. The
> sample size needed for a target ME is n = 4 sigma squared over ME squared. For a proportion (variable equal to 0 or 1 with probability
> p) the standard deviation is the square root of p(1 - p), largest at p = 1/2 (0.5), so a conservative n = 1 over ME squared; a
> plus-or-minus 3 percentage point poll needs 1/(0.03 squared) = 1,112 people. Gallup-style reports such as 46% approval with a margin of
> error of 3 points use this idea.

### [S2] Data and Decisions Lectures.md > Lecture 9: Multiple Regression and Experiments as Regressions (lines 395-404, score 9.28)
> **Prediction intervals.** The approximate 95% prediction interval is still the predicted value plus or minus 2 times the residual standard deviation.
> For a location with household income of $70,000 and 3 competitors, predicted sales are -123.43 + 10.09 x 70 - 27.62 x 3 = about $499 per square foot, and the
> interval is $499 plus or minus 2 x $99, i.e. [$301, $697].
> 
> **Explanatory power.** R squared measures the fraction of variation in y explained by the explanatory variables (in the coffee example 39% of store-to-store
> variation in sales). It rises mechanically with the number of X variables, so adjusted R squared corrects for sample size and model size and is always smaller
> than R squared. An F test asks whether the model as a whole has explanatory power.
> 
> **Best practices.** Bivariate and multivariate regressions are the same in most ways; the big difference is interpretation (marginal versus partial slopes).
> Look at scatterplots and the correlation matrix before running regressions, and stay vigilant about omitted variables (more in the next lecture).

### [S3] Data and Decisions Lectures.md > Lecture 4: Control Limits and Type I and Type II Errors (lines 135-145, score 7.68)
> **Sampling distribution of the average.** The sample average is Normal if either the sample is large enough (Central Limit Theorem)
> or the population is Normal to begin with. A sample-size condition: the normal approximation is accurate if n is greater than 10
> times the absolute value of the sample kurtosis (kurtosis measures the prevalence of outliers or fat tails; it is 0 for normal data,
> and Excel's KURT function computes it). For HALT, the average is distributed Normal with mean 7 and standard error 4 divided by the
> square root of 20, about 0.89. The standard error is proportional to the population standard deviation, inversely proportional to
> the square root of the sample size, and does not depend on the population size. It is smaller than the standard deviation of
> individual scores.
> 
> **Type I and Type II errors.** A Type I error is taking action when none is needed (a false positive). A Type II error is failing to
> act when action is needed (a false negative). Each has a cost, so design the problem on both margins and trade off the costs in your
> context. Examples to discuss: credit card fraud, COVID-19 tests, monetary policy and drug testing.

### [S4] Data and Decisions Lectures.md > Lecture 5: Confidence Intervals and Hypothesis Testing (lines 174-181, score 7.48)
> **Confidence interval.** A confidence interval is a range of plausible values for a population parameter based on one sample; it needs
> the confidence level, the sample mean and the standard error. When only the sample standard deviation s is known (not sigma), the
> standard error is estimated as s divided by the square root of n and the multiplier comes from the Student t distribution (fatter tails
> than the Normal, shape set by degrees of freedom; developed by W. S. Gosset of the Guinness brewery and published under the pseudonym
> "Student" in 1908). The 100(1 - alpha)% interval is the sample mean plus or minus t critical value times the standard error. For the
> turbine pilot: estimated standard error = 0.7 divided by the square root of 35 = 0.118; the t critical value with 34 degrees of
> freedom leaving 0.025 in each tail is 2.032 (Excel: T.INV(0.025, 34)); the 95% confidence interval is 29.5 plus or minus 2.032 x 0.118,
> i.e. [29.12, 29.88]. The status quo of 30 tons is not in the interval. With 150 degrees of freedom the 95% critical value is 1.976.

### [S5] Data and Decisions Lectures.md > Lecture 3: Sampling Bias (lines 90-94, score 7.22)
> **Eliminating bias.** The best way to get a representative sample is a simple random sample (SRS): by design any characteristic in the
> population, including unobservables, is uncorrelated with being included, so on average the sample mimics its sampling frame. The
> lecture asks whether various procedures give representative samples, for example asking your five closest friends, an online poll on
> a party's website, a Twitter poll from your own account, exit interviews at a randomly chosen polling station, a mayoral election
> survey with 15% nonresponse (Kendall, Nannicini and Trebbi), a text poll of San Francisco mobile phones, and landline calls.

## Answer (as displayed to the user)

> 1,112 people is needed for a plus-or-minus 3 percentage point poll [S1].

- Citation check of the draft: OK: 1 passage(s) cited, all retrieved; every figure appears in them
- Answerability check (draft-free, fact-seeking questions only): replied 'KIND: sample size | VERDICT: YES' -> passed (10.0 s)
- Verification (second model call, yes/no): replied 'YES' -> supported (13.3 s)
- Retrieval: expected section first found at rank 1; all expected sources in top 5: True
- Behaviour: expected `answer`, got `answer` -> match
- Required content present: True | forbidden content absent: True | clean format (no leaked reasoning): True
- Timing: model 38.0 s (load 0.0 s), 1772 prompt tokens, 25 answer tokens, 7172 characters sent to the model

**Automated verdict: PASS**

## Assessment (human, after opening the cited sources)

Draft assessment by Claude after reading the cited passages; to be confirmed by the student against the slides and documents.

**Retrieval: good.** The passage with the answer was rank 1.
**Answer: correct and supported.** [S1] (Data and Decisions Lectures.md, Lecture 5) says a plus-or-minus 3 percentage point poll needs 1/(0.03 squared) = 1,112 people. The answer says 1,112 and cites S1. Grammar slip ("1,112 people are needed") only.
**Checks:** citation check ok; answerability check named the kind of fact ("sample size") and said YES; verification YES.
**Verdict: pass.**

Carried over from run 5. The answer differs from run 5 by one word only ("is needed" instead of "are needed"); the content, citation and checks are the same. Final index: 114 passages from 9 sources (the Uber case was removed from the sources for privacy).

