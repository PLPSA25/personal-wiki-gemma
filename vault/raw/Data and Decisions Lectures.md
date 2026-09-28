# Data and Decisions Lectures (MBA 200S, Fall A)

Personal study summary of the ten lectures of MBA 200S Data & Decisions (Fall A 2026), the core statistics course. Written in
my own words from the lecture slides; the slides themselves are not included. Each lecture is one section. Numbers and
examples are the ones used in class.

## Lecture 1: Introduction to Data and Decisions

**Why the course exists.** Data & Decisions is a required core course because quantitative fluency is now fundamental to an MBA
("quants versus soon-to-be quants," not quants versus poets). AI produces speed and a first draft, not a finished analysis: it takes
business training and data fluency to catch statistical errors you did not produce, which makes you a complement to AI tools
rather than a substitute.

**Example 1: decisions with data (Enterprise AI).** Seats cost $50 per person per month and training plus rollout adds $70; at $30
per hour of staff time the tool must save 4 hours per person per month. A 4-person pilot averaged 4.4 hours saved. Is 4.4 > 4
enough? Two samples with the same mean of 4.4, [0.4, 13, 0.8, 3.4] and [4.1, 4.2, 4.5, 4.8], suggest different decisions because the
spread differs, and 40 person-months of data would give more confidence than 4.

**Example 2: StubHub.** Online sellers often show mandatory fees late in the purchase process. StubHub controls the purchase
process, so it could run a randomized controlled trial (A/B test) on whether showing all fees upfront reduces revenue (an actual
experiment run with a Haas marketing professor, published 2021).

**Application: eBay and search engine marketing (SEM).** A paid link for the brand keyword sits above the natural link. Naively, the
people who click paid ads buy a lot, so returns look huge. The field experiment by Blake, Nosko and Tadelis (2015) tested it
properly: search clicks and latent purchasing intentions are positively correlated (omitted variable bias), and once that is
removed the return on brand-keyword SEM went from hugely positive to about -100%, so tens of millions of dollars of spending were
at stake. Getting the statistics right can save millions.

**Opportunities and threats.** Opportunities include price discrimination (identifying price-inelastic demand) and real-time
data such as geolocated credit-card spending and small-business revenue around the COVID shock. Threats include loss of privacy
and weaknesses such as spurious correlations and overfitting. The tools carry into other core courses: data analytics and causal
inference, economics (estimating demand), leading people, finance (CAPM, abnormal returns) and marketing.

**Course logistics.** The course is interactive with cold calling from random lists (ungraded, a way to learn about simple random
sampling). Grading: 10% attendance, 40% cumulative final exam (one-page cheat sheet, front and back) and 50% group deliverables. The
optional textbook is Stine and Foster. Exams reward communicating results in concise, well-argued responses and intuition, not
memorizing formulas. Excel with the Analysis Toolpak is the minimum software; Stata, R, Matlab and Python are allowed.

**Short review of chapters 1 to 12.** Time series and scatterplots; a random variable is a correspondence between outcomes and
probabilities, and real data are a sample from a population, from which we compute statistics such as the sample mean and standard
deviation. The Central Limit Theorem says the distribution of a sum (or average) of independent, identically distributed random
variables approaches a normal distribution as n grows, whatever the original distribution; the sample mean is approximately
Normal(mu, sigma squared over n). For a coin flip (Bernoulli) with probability p, the mean is p and the variance is p(1 - p); the sum
of n flips has mean np and variance np(1 - p). This is why we can say where a sample average is likely to fall (confidence
intervals, chapter 15), spot a weird sample, and check whether a production process is broken (control limits, chapter 14). The next
lecture covers sampling and data quality.

## Lecture 2: Sampling and Standard Error

**Inference basics.** A sample is your data (size n) and is only a signal about the truth, the population. The Enterprise AI
samples again: Sample A = [0.4, 13, 0.8, 3.4] has mean 4.4 hours and standard deviation 5.89; Sample B = [4.1, 4.2, 4.5, 4.8] has the
same mean 4.4 but a standard deviation of only 0.32; Sample C (n = 8, mean 4.5, standard deviation 0.24) has more data and less
spread. A statistic is a characteristic of the sample (for example the sample mean); a parameter is a characteristic of the
population (for example the true mean hours saved, or the fraction of 18 to 55 year-olds aware of the Camper shoe brand).
Inference or estimation uses a statistic to learn about a parameter. Sampling error is the error caused by a sample not being the
exact population; different samples give slightly different answers, though by the Law of Large Numbers the sample mean falls around
the population mean.

**Standard error.** The standard error is the dispersion of a statistic from sample to sample, a measure of the uncertainty of your
answer. For the sample mean it equals sigma divided by the square root of n (the "square root rule"). Small samples and more
uncertain problems (large sigma) mean a higher chance of being far from the truth. Standard error is the unavoidable price of using a
sample: there is one population but many possible samples. Summary for a sample mean: its sampling distribution has the population
mean as its mean (Law of Large Numbers), a standard deviation of sigma over root n (the standard error), and is Normal (Central Limit
Theorem). It depends on the sample size, not the population size, so for all practical purposes think of the population as infinite.
Weird samples can happen.

**Surveys and definitions.** Population (the true collection of interest), census (a survey of the whole population), sample,
survey, representative (mirrors the population's mix) and bias (systematic error in selecting the sample or in a statistic). J.D.
Power's Vehicle Dependability Study surveys about 34,000 original owners of 2023 model-year vehicles after three years, measuring
problems per 100 vehicles (lower is better) across 184 problems in 9 categories. Because it uses a proprietary sampling frame (a list
sourced from dealers) and stratified sampling, and because owners with problems may be more or less likely to respond (nonresponse
bias), representativeness has to be checked.

**How to sample.** A sampling frame is the list you draw from. A simple random sample (SRS) chooses n items randomly from the
frame and is the gold standard; a random number generator can assign each item a uniform number in [0, 1] and select the lowest n
(or all below 0.05 for a 5% sample). Do large populations require large samples? No: it is the sample size that matters for standard
errors. Stratified sampling divides the frame into strata (for example Porsche owners) and does SRS within each. Cluster sampling
divides the frame into geographic clusters, randomly selects some clusters and does SRS within them; it is useful when the area is
large and the clusters are similar, and it can save substantial cost.

**Tesla survey application.** Tesla has a software update for its newest Model 3. How should it deliver it (in-store tune-up or
automatic download) and should it charge? Design a sample or survey to find out from current and potential customers.

**Conclusions.** We sample to make inferences; SRS, stratified and cluster sampling are how; the how matters because it is the
only way to get representative, unbiased samples. Sampling bias comes in Lecture 3. Bonus refresher: sample mean, variance, standard
deviation, covariance, correlation, slope and the z-score.

## Lecture 3: Sampling Bias

**Eliminating bias.** The best way to get a representative sample is a simple random sample (SRS): by design any characteristic in the
population, including unobservables, is uncorrelated with being included, so on average the sample mimics its sampling frame. The
lecture asks whether various procedures give representative samples, for example asking your five closest friends, an online poll on
a party's website, a Twitter poll from your own account, exit interviews at a randomly chosen polling station, a mayoral election
survey with 15% nonresponse (Kendall, Nannicini and Trebbi), a text poll of San Francisco mobile phones, and landline calls.

**Five forms of bias in data production.**
1. Sampling frame bias: the list you draw from does not match the target population. The 1948 "Dewey Defeats Truman" headline came
from a phone survey when telephones were a luxury, so Truman voters were missing from the frame. Mobile users, a social platform's
users and Google Trends searchers each represent only their own frame. Asking generative AI to simulate survey answers for a
profile ("would a male economics professor in his 40s in Berkeley prefer a Tesla Model Y or a Ferrari?") has no defined population
or sampling frame; do not do this.
2. Self-selection or voluntary response bias: samples of volunteers, such as Twitter polls (bias comes from who visits the site and
from the link between answering and being positively disposed).
3. Survivorship bias: analysis based only on the subset that clears a hurdle. In the WWII bomber example, armor should go where the
returning planes were not hit, because planes hit there did not return. If a risky management practice produces either big gains or
big losses, observing only firms still in business makes it look like it produces big gains. Venture capitalists, who see many
failures, are less prone to this; be careful in a successful, established market.
4. Convenience sampling bias: individuals easily accessible to the surveyor; social networks are not random (homophily).
5. Measurement bias: measured value = true value + systematic error (bias) + random error (imprecision). A result can be unbiased and
precise (accurate), biased and precise, unbiased and imprecise, or biased and imprecise. The experimenter demand effect is people
answering to please the surveyor; firms may also misreport in government surveys.

**Key questions.** Who is left in my sample and who is left out? If the two sets differ you are in trouble; if the same, you are
fine. That is why random samples on the correct frame are so valuable.

**Mitigation.** (1) Professional consumer panels. (2) Recruitment techniques, such as online panels that recruit people by random-digit
calls and pay them per survey (the RAND American Life Panel pays $10 to $20), IVR (robocalls) and live phone interviews. (3) A poll of
polls to average out individual polls' quirks (e.g. midterm election forecasts). (4) Bias correction by reweighting (down-weighting
oversampled groups) under assumptions about how bad selection is, followed by sensitivity analysis: if conclusions do not change much,
you are fine; if they do, the results cannot be trusted.

**Best practices.** As a data producer: randomize, match the sampling frame to the target population and reduce nonresponse. As a
data consumer: understand how the sample was selected, be skeptical of low response rates, ask hard questions, and never use data whose
origin you do not understand.

## Lecture 4: Control Limits and Type I and Type II Errors

**Application: quality control with HALT.** A chip manufacturer selects samples for Highly Accelerated Life Testing (HALT); the
case is a large semiconductor maker. There are 16 quality tests, and a chip's HALT score is the number passed (0 to 16, treated as
continuous). Even when the process works, scores vary randomly: when working properly chips pass on average mu = 7 tests with a
standard deviation of sigma = 4 (known from the CTO). The whole population cannot be tested because testing destroys chips, so each
day the manager draws a random sample of n = 20 chips and computes the average score. The question is whether a deviation is random
variation or a change in the process, and when to stop the assembly line.

**Sampling distribution of the average.** The sample average is Normal if either the sample is large enough (Central Limit Theorem)
or the population is Normal to begin with. A sample-size condition: the normal approximation is accurate if n is greater than 10
times the absolute value of the sample kurtosis (kurtosis measures the prevalence of outliers or fat tails; it is 0 for normal data,
and Excel's KURT function computes it). For HALT, the average is distributed Normal with mean 7 and standard error 4 divided by the
square root of 20, about 0.89. The standard error is proportional to the population standard deviation, inversely proportional to
the square root of the sample size, and does not depend on the population size. It is smaller than the standard deviation of
individual scores.

**Type I and Type II errors.** A Type I error is taking action when none is needed (a false positive). A Type II error is failing to
act when action is needed (a false negative). Each has a cost, so design the problem on both margins and trade off the costs in your
context. Examples to discuss: credit card fraud, COVID-19 tests, monetary policy and drug testing.

**Control limits.** Control limits are thresholds forming a decision rule: a symmetric interval around the mean, mu plus or minus
k times the standard error. If the sample average falls outside the bars, stop the machines; if inside, keep going. Example: with a
standard error of about 0.89, shutting production down when the average is below 6 or above 8 gives a Type I error probability
(stopping although everything is fine) of about 0.27, from P(below 6) + P(above 8) using z-scores of about -1.12 and +1.12. Common
z-score cutoffs: 1.96 for a 5% Type I error, 2.58 for 1%, and 3.00 for 0.27% (0.0027).

**Balancing the errors.** The Type I error probability is typically set at 5% or 1%. Wide control limits reduce Type I error (you
stop only for ultra-bad outcomes) but raise Type II error; narrow limits reduce Type II error (you almost always stop when there is
a real problem) but you stop more often for nothing. You cannot reduce both at once.

**Conclusions.** Think hard about which attribute of the process to monitor, do not focus on one error while ignoring the other, do
not assume the process has failed just because a value falls outside the limits, and avoid confusing the two error types.

## Lecture 5: Confidence Intervals and Hypothesis Testing

**Warm-up application: muni fund.** A municipal bond fund has mean daily returns of $15M with a standard deviation of $4.6M, monitored
with monthly samples of 20 business days. Questions posed: control limits at a 5% Type I error, whether to stop trading if a
month averages $14.1M or $13.2M, what partners worry about when lowering alpha to 1%, and what to do if the sample kurtosis is 5.6.

**Intuition.** A confidence interval answers: based on my data, what range of values for my problem can I be 95% confident about? A
hypothesis test answers: is the evidence significantly more in favor of a change (a costly alternative) or of sticking to the status
quo?

**Business setting: wind turbines.** A wind turbine maker is piloting carbon fiber blades instead of fiberglass: more costly but lighter,
more efficient blades. The current process produces blades averaging 30 tons with a standard deviation of 0.5 tons. A controlled pilot
of n = 35 carbon-fiber blades has a sample mean of 29.5 tons and a standard deviation of 0.7.

**Confidence interval.** A confidence interval is a range of plausible values for a population parameter based on one sample; it needs
the confidence level, the sample mean and the standard error. When only the sample standard deviation s is known (not sigma), the
standard error is estimated as s divided by the square root of n and the multiplier comes from the Student t distribution (fatter tails
than the Normal, shape set by degrees of freedom; developed by W. S. Gosset of the Guinness brewery and published under the pseudonym
"Student" in 1908). The 100(1 - alpha)% interval is the sample mean plus or minus t critical value times the standard error. For the
turbine pilot: estimated standard error = 0.7 divided by the square root of 35 = 0.118; the t critical value with 34 degrees of
freedom leaving 0.025 in each tail is 2.032 (Excel: T.INV(0.025, 34)); the 95% confidence interval is 29.5 plus or minus 2.032 x 0.118,
i.e. [29.12, 29.88]. The status quo of 30 tons is not in the interval. With 150 degrees of freedom the 95% critical value is 1.976.

**Margin of error.** The margin of error (ME) is an informal 95% interval that replaces the t value by 2: ME = 2 x standard error. The
sample size needed for a target ME is n = 4 sigma squared over ME squared. For a proportion (variable equal to 0 or 1 with probability
p) the standard deviation is the square root of p(1 - p), largest at p = 1/2 (0.5), so a conservative n = 1 over ME squared; a
plus-or-minus 3 percentage point poll needs 1/(0.03 squared) = 1,112 people. Gallup-style reports such as 46% approval with a margin of
error of 3 points use this idea.

**Hypothesis test setup.** The finance team says the switch is profitable if the mean blade weight is below 29.7 tons. The null
hypothesis (H0) is the default, status-quo course of action (mean weight of 29.7 or more); the alternative (Ha) contradicts it and
supports change (mean below 29.7). This one-sided test is a decision rule: is the evidence strong enough to reject H0 and justify the
change? There is always a risk of the wrong decision: rejecting a true H0 is a Type I error (a false positive: taking action when you
should stay put) and retaining a false H0 is a Type II error (a false negative). The significance level alpha (typically 0.05 or 0.01)
is the maximum tolerated Type I error; a statistic is statistically significant if its p-value is below alpha.

**Steps.** (1) Choose alpha. (2) Compute the t statistic (sample mean minus the null value, divided by the standard error). (3) Find the
p-value. (4) Reject H0 if the p-value is below alpha. For 0/1 variables the standard error under the null is the square root of p0(1 -
p0) divided by n, where p0 is the proportion specified by the null (not the p-value). Turbine test: t = (29.5 - 29.7)/0.118 = -1.6949
with 34 degrees of freedom; p-value = 0.04961 (Excel: T.DIST(-1.6949, 34, TRUE)), which is below 0.05, so reject the null and adopt
the new process.

**What the p-value means.** It is how likely you would be to get this result, or a more extreme one, if the null were true; it is the
probability of a Type I error if you set the rejection threshold at your current estimate. If the p-value is at least alpha, you fail to
reject the null and keep the status quo because the sample could happen often enough under the null.

**Two-sided tests.** To test whether something is different from the old value (H0: mean equals the value; Ha: mean differs), the math is
the same but reject only if the two-sided p-value (twice the one-sided p-value) is below alpha, which is more conservative.

**Type II error and power.** The probability of a Type II error depends on the alternative and is generally smaller when the truth is
far from the null. Pilots should be designed so that, under alternatives you think are reasonable, you have a specific chance of
rejecting the null (power calculations).

**Conclusions.** A pilot sample gives a confidence interval for the population mean; a decision rule turns a sample into a decision;
there is always a chance of the wrong decision, but you can calculate the probabilities of the error types and design pilots to reduce
them.

## Lecture 6: Comparing Means and A/B Testing

**Recap of Lecture 5.** A one-sided test sets H0 as the status quo value and Ha as the change; the t statistic is the distance of the sample
mean from the null value in standard errors, and its p-value shows whether the sample is far enough from the null. Cookbook: choose alpha,
compute the t statistic (with the null value), find the p-value with n - 1 degrees of freedom, reject H0 if the p-value is below alpha (a
high t statistic implies a low p-value). A two-sided test has H0: mean equals the value and its p-value is twice the one-sided p-value, so
it is more conservative.

**From one sample to two.** Last class: deciding whether a decision beats the status quo. Today: deciding between two options and whether
differences are "noise" or "real", using A/B testing and the two-sample t-test.

**Experiment terminology.** An experiment (randomized controlled trial, RCT) randomizes treatment and control status to produce data that
reveal causation. The treatment is something done to an experimental unit (typically a variable that is 1 if treated and 0 if control); the
response is where we look for an effect. The motivation is causal inference: to say "if I do X then Y will happen." Observational comparisons
suffer from omitted or "lurking" variables (bacon eaters might also smoke more and exercise less); observational relationships are rarely
causal, and correlation is not causation.

**Benefits and costs of randomization.** Randomization makes treatment and control groups identical in everything except the treatment (the same
logic as why an SRS is representative), so an RCT has no bias, though watch for attrition (do you observe outcomes for everyone?); it is also
transparent and highly credible. Costs: RCTs can be expensive, are sometimes ethically not viable (the 2014 Facebook news feed experiment on
emotions), and require replication to validate.

**Application: website A/B test.** A startup measures engagement as seconds spent on the landing page for visitors arriving via a social link.
Design A requires more back-end support and Design B is cheaper, so A is retained only if it beats B by at least 2 seconds (B is the default
absent evidence): H0: mean of A minus mean of B is at most 2; Ha: it is greater than 2. Data: Design A has mean 16.19, standard deviation 4.91,
n = 33; Design B has mean 12.43, standard deviation 5.07, n = 30. Because both samples vary, single-sample confidence intervals will not do.
The two-sample t statistic is (mean A minus mean B minus the break-even value) divided by the standard error of the difference, which is the
square root of (s_A squared over n_A plus s_B squared over n_B); the degrees of freedom are n_A + n_B - 2 in the equal-variance case (a bit
lower for unequal variances, Welch). Software does the calculation. Here the t statistic is 1.39 and the p-value is above alpha = 5% (one-sided
and two-sided), so you fail to reject the null: A is not sufficiently more engaging than B to warrant it, and the decision is to use B. The
two-sample t-test is general and works for any two random samples, not only experiments.

**Internal and external validity.** Internal validity: have you identified the causal effect of the treatment (are treatment and control
different only in the treatment)? Randomization eliminates confounding factors; selection into treatments is the main worry in observational
studies. External validity: can you generalize to other contexts? Examples of failure: Yahoo's observational estimate that ads raised brand
searches by 871% to 1,198% versus 5.4% in a proper experiment (ads were targeted at users already searching). Post hoc ergo propter hoc ("because
Y follows X, X caused Y"): a professor's papers rejected after a vacation, or Christmas cards "causing" Christmas.

**Five frequent A/B testing failures.**
1. P-hacking: an executive rewarded for successful A/B tests runs 20 nearly identical experiments and picks the lowest p-value; a good
experiment is wrong 1 time in 20 (5%). Solution: do not fool yourself.
2. Trust but verify: keep adding users until a result is barely significant, then stop and declare success. Twyman's Law: any figure that looks
interesting or different is usually wrong; if an experiment looks too good to be true, run it again (a Bing color experiment was run several
times before implementation). Solution: replication, even a replication task force that tries to kill significant results, as quant hedge
funds do.
3. Giving up: only about 10% to 20% of experiments at Google and Bing generate positive results, and at Microsoft one-third are effective, one-third
neutral and one-third negative. Solution: stay the course.
4. Bugs in code: about 80% of Microsoft's changes are experimentally validated; run A/A tests repeatedly, which should reject equality about 5% of
the time, no more and no less.
5. Outliers and heterogeneity: subpopulations such as bots, or Amazon library accounts placing massive book orders. Solution: always look at and
plot your data.

**Conclusions.** Observational studies usually suffer from confounding and omitted variables; experiments reveal causal relationships; RCTs
ensure internal validity; use two-sample t-tests to compare means; even in A/B tests, execution matters.

## Lecture 7: Basics of Linear Models (Regression)

**Toolbox so far.** Sampling techniques and their failures; control limits (does sample data conform to the population, e.g. is product quality
OK); confidence intervals (a range of values supported by the data); the one-sample t-test (change or stay put); the two-sample t-test (choose one
of two options for A/B testing). The second half of the course is regression models, which can analyze A/B tests and allow more sophisticated
comparisons. Roadmap: Lecture 7 basics of linear models, 8 regression with one X variable, 9 with two or more X variables, 10 comparing regression
models, 11 categorical X variables.

**Linear versus non-linear relationships.** A linear model is y = b0 + b1 x: a one-unit change in x is associated with the same b1 change in y at all
levels of x, because the slope is constant. In a non-linear relationship the slope changes, so the same change in x induces different changes in y at
different levels of x.

**Application: predicting diamond prices.** Diamond prices depend on the four Cs: carat (size), clarity, cut and color. A sample of several
hundred emerald-cut, slightly "included" diamonds (714 diamonds) is used to ask about the relationship between price and weight and the average
price of a 0.4 or 0.5 carat stone.

**Ordinary least squares (OLS).** Estimated price = b0 + b1 weight. Many lines can be drawn through a cloud of data; a good one is not systematically
wrong in one direction and has predictions as close to actual prices as possible. Residuals are the vertical deviations from the data points to the
fitted line (actual minus predicted). The OLS line is the line that minimizes the sum of squared residuals. The slope equals the correlation r times
the standard deviation of y over the standard deviation of x, and the intercept equals the mean of y minus the slope times the mean of x; software
does the calculation. Diamond example: mean price $1,119.6 with standard deviation $205.5, mean weight 0.4094 carat with standard deviation 0.05434, and
correlation 0.7131 give a slope of 0.7131 x 205.5273 / 0.05434 = about 2,697 and an intercept of 1,119.6 - 2,697 x 0.4094 = about 15. The fitted equation
is price = 15 + 2,697 x weight.

**Interpreting the coefficients.** The intercept is the average response when x = 0 (like a fixed cost of $15 per diamond) but is an extrapolation here
because the sample has no diamonds near zero weight, so be cautious. The slope is the predicted change in y for a one-unit change in x: a diamond
that weighs 1 carat more is predicted to cost $2,697 more, and one weighing 0.2 carat more costs 0.2 x 2,697 = about $539 more. It is tempting to
call it marginal cost, but it is incorrect to say the slope is the change in y caused by a unit change in x; say "associated with." Causal language
is appropriate only if x is as good as randomly assigned (are there other differences between 0.4 and 0.5 carat diamonds, such as a harder cut?).
Predictions: a 0.4 carat diamond is predicted to cost 15 + 2,697 x 0.4 = about $1,094, and a 0.5 carat one about $269.7 more (2,697 x 0.1).

**Residuals and diagnostics.** Residuals show the variation left unexplained. Plot residuals against x: if a linear model is appropriate, the
plot should stretch out horizontally with consistent vertical scatter, like snowfall (white noise), with no other patterns. The standard deviation of
the residuals (called the standard error of the regression in Excel, and root MSE in Stata) is about 145 dollars in the diamond example.

**R-squared.** R squared is the fraction of the variation in the dependent variable accounted for by the regression line, the square of the correlation
coefficient in the one-variable case. For the diamonds, R squared = 0.509, so the fitted line explains 50.9% of the variation in prices. Be careful: is
the linear fit appropriate, and is the relation causal? R squared is a measure of how much variation you explain, not a test that a linear model is right
or that the relationship is causal. Anscombe's Quartet (four data sets with nearly identical summary statistics but very different plots) shows the need to
plot your data.

**Checklist.** Always look at the data; check that the relationship is linear with a scatterplot; check that residual variation is random; describe the
intercept and slope in the units of the data; limit predictions to the observed range (limit extrapolation); be careful of causal language; use context to
think about other explanatory variables; remember what R squared is and is not.

## Lecture 8: Regression with One X Variable and Inference

**Regression everywhere.** Examples of one-variable regressions across jobs: HR (job performance on interview score), marketing (revenue on ad
spending), consulting (bank deposits per zip code on bank competition), finance (share price on quarterly sales), education (test scores on math
curriculum), politics (vote share on campaign spending), and others. The lecture also lists an application to Uber.

**Application: locating a new UNIQLO store.** You are asked to find the relationship between local traffic levels (independent variable) and sales
(dependent variable) using one month of sales data from n = 80 stores. Location models in real life are more complex and include spatial
dimensions; the OLS framework here is a simplification. The slope describes the average increase in sales for a unit increase in traffic; the
question is what sales to expect at a location with 50,000 drive-bys per day.

**The simple (bivariate) regression model.** In the population, y = beta0 + beta1 x + epsilon, where the error (also called noise, shock or
innovation) can be positive or negative but has a zero average. In the sample we see estimates b0 and b1, and the estimated error is the residual.
Three assumptions about the errors let us infer population facts from a sample: they are independent of one another, normally distributed, and have
identical variance sigma squared. Under these assumptions the sampling distributions of the intercept and slope estimates are t distributions
centered on the true values with n - 2 degrees of freedom.

**Standard error of the slope.** It describes sample-to-sample variability of b1 (software reports it). It rises with the standard deviation of the
residuals, falls with sample size, and falls with a larger standard deviation of x.

**Before inference, check five questions on your sample.** Is the association linear? Does the residual plot look patternless? Are the residual
variances similar? Are the residuals approximately normal? For causal inference, is this an experiment? Modest deviations from the assumptions are
acceptable.

**Hypothesis tests on coefficients.** To test H0: slope = 0 use t = b1 divided by its standard error, with n - 2 degrees of freedom; likewise for the
intercept. UNIQLO: the slope t statistic is 143.3 / 22.34 = 6.42 with a p-value below 0.0001, so there is a significant relationship between sales and
cars driving by. The intercept t statistic is 0.43 with a p-value of 0.67, so we cannot reject that sales are zero when there are no drive-bys. All
are two-sided tests.

**Confidence intervals for coefficients.** The 95% interval is the estimate plus or minus the t critical value (1.992 with 78 degrees of freedom) times
the standard error. UNIQLO slope: 143.3 plus or minus 1.992 x 22.34, i.e. [98.8, 187.8].

**Prediction intervals.** The best guess for sales at 50,000 cars a day is 143.36 + 143.31 x 50, about $7,308 per day (with traffic measured in
thousands of cars). But could sales be as high as 9,000 or as low as 5,000? A prediction interval is designed to hold a fraction (usually 95%) of
the values of the response for a given x; unlike a confidence interval, it makes a statement about a new out-of-sample observation, not about a
population parameter. A simple approximation for a 95% interval is the predicted value plus or minus 2 times the standard deviation of the residuals
(the regression standard error, here 547): 7,308 plus or minus 2 x 547, approximately $6,214 to $8,402 per day. The exact formula for the standard
error of prediction includes an extra term that grows as x moves away from its mean, which is why extrapolation is risky (the diamonds data show the
risk at high carat weights). Prediction intervals are reliable within the observed range and sensitive to the constant-variance and normality assumptions.

**Best practices.** Always check the model conditions, but know that modest deviations are OK; rely on software for standard errors; use prediction
intervals to predict for particular observations; be careful when extrapolating.

## Lecture 9: Multiple Regression and Experiments as Regressions

**Midcourse feedback.** Most students found the pace well matched; the instructors planned more in-class applications ("check as you go"), more
business examples, more intuitive explanations and a targeted final review session, and asked students to use office hours, sections and the course
site.

**Analyzing an experiment with a regression (Bing A/B application).** The A/B data can be put into a regression with a 0/1 variable: B_group = 1
for Design B (the treatment) and 0 for Design A (the control). The regression is engagement = b0 + b1 B_group + error. The intercept gives the mean in
the control group (Design A), and the slope gives the difference in means between treatment and control. To test whether there is a difference between
groups, run a t-test on the slope. In the example the intercept is 12.06 million clicks (t of 224.2) and the B_group slope is 0.43 with a standard error
of 0.081, a t statistic of 5.30 and a p-value of about 0.0000001, so Design B raised engagement.

**Regression module roadmap.** Lecture 7 basics, Lecture 8 one X, Lecture 9 two or more X variables, Lecture 10 comparing regression models, Lecture 11
categorical variables. Today's goals: run regressions with multiple X variables, interpret their coefficients, check conditions, and judge explanatory power.

**The general regression model.** Observed values of y are linearly and simultaneously related to x1, x2, ..., xk: y = beta0 + beta1 x1 + ... + betak xk +
error. The errors are assumed to be independent of each other and of the X's, to have equal variance around the regression line, and to be normally
distributed. Lecture 8 was the special case k = 1. The model is a linear central tendency plus errors drawn independently from the same normal
distribution with mean zero.

**Application: where to locate a coffee shop.** Business question: is it better to be in a high-income area with more competitors, or a lower-income area
with fewer? The dependent variable is annual sales per square foot at Peet's outlets; the independent variables are median household income in the area
(in $1,000) and the number of competing stores within a fixed radius. Income and competitors have positive covariance (richer areas attract competitors).
Estimated sales = -123.43 + 10.09 x Income - 27.62 x Competitors.

**Partial versus marginal slopes.** A partial slope is the slope of an explanatory variable in a multivariate regression that statistically controls for
the other X variables: the change in y associated with a one-unit increase in that x, holding all other x's constant. A marginal slope is the slope in a
bivariate regression, which combines the partial slope with all other correlated channels of influence (omitted variables and indirect effects). They are
the same only when the explanatory variables are uncorrelated (orthogonal). Interpretation: the partial slope of 10.09 for income means a store in a
location with $10,000 more median household income sells on average $100.90 more per square foot than a store with the same number of competitors; the
partial slope of -27.62 means each additional competitor is associated with $27.62 lower average sales per square foot among equally affluent locations.

**Checking conditions.** Use the fitted model to verify that residuals are independent, have equal variance and are approximately normal: plot residuals
against predicted values and against each independent variable, and plot a histogram of the residuals.

**Prediction intervals.** The approximate 95% prediction interval is still the predicted value plus or minus 2 times the residual standard deviation.
For a location with household income of $70,000 and 3 competitors, predicted sales are -123.43 + 10.09 x 70 - 27.62 x 3 = about $499 per square foot, and the
interval is $499 plus or minus 2 x $99, i.e. [$301, $697].

**Explanatory power.** R squared measures the fraction of variation in y explained by the explanatory variables (in the coffee example 39% of store-to-store
variation in sales). It rises mechanically with the number of X variables, so adjusted R squared corrects for sample size and model size and is always smaller
than R squared. An F test asks whether the model as a whole has explanatory power.

**Best practices.** Bivariate and multivariate regressions are the same in most ways; the big difference is interpretation (marginal versus partial slopes).
Look at scatterplots and the correlation matrix before running regressions, and stay vigilant about omitted variables (more in the next lecture).

## Lecture 10: Omitted Variables, Causal versus Predictive Questions

**Learning goals.** Review Lecture 9, adjusted R squared and the F statistic, path diagrams for omitted variables, how experiments side-step omitted variables,
the difference between causal and predictive questions, and an application to San Francisco real estate pricing.

**F statistic and reading regressions.** For the intercept or a specific slope use t tests; the F statistic measures the overall explanatory power of the
regression by testing whether all slopes are zero (null: every slope equals zero; alternative: at least one slope is not zero). Software reports its p-value:
if it is high, the model is weak given the number of explanatory variables; check that the p-value is below 5% before going ahead with the regression. In the
Peet's example the F p-value is small (the covariates are not junk), yet only one slope is statistically significant at the 5% level, and R squared is
slightly higher than adjusted R squared because of the second covariate. How to read a multiple regression: (1) check the overall F-stat p-value, (2) check
adjusted R squared for fit, (3) check each coefficient for statistical significance (an absolute t statistic above about 2 and a p-value below 0.05) and for
economic significance (a small change in x correlated with a large change in y, usually judged relative to the standard deviation of y).

**Omitted variable bias.** Whenever a variable left out of the model is correlated with both (1) a variable we control for and (2) the outcome, the estimates for
the included variables are biased: the marginal slope differs from the partial slope. When we care about causal effects this is a problem. The direction can
often be inferred: marginal slope of x1 = partial slope of x1 + (partial slope of the omitted variable x2) times (strength of the association between x1 and x2).
If the omitted variable has a positive effect and is positively correlated with the included variable (or both are negative), the bivariate coefficient is biased
upward; if the signs are opposite it is biased downward. Directed acyclic graphs (DAGs, path diagrams; Pearl, 2000) show the cases.

**Four cases.**
1. Peet's Coffee: in a regression of sales on income alone, income has a direct positive effect on sales and an indirect negative effect through more competitors;
controlling for competitors makes the effect of income larger, so the marginal slope was biased downward.
2. Peet's Coffee II: if crime is omitted, income has a direct positive effect and an indirect positive effect through lower crime; including crime lowers the
income effect, so the marginal slope was biased upward.
3. Returns to education: an MBA has a direct positive effect on wages and an indirect positive effect through work ethic; controlling for work ethic lowers the MBA
effect (upward bias).
4. Returns to education II: with work experience (negatively related to holding an MBA, positively to wages), controlling for experience raises the MBA effect
(downward bias).

**Randomization eliminates bias.** If advertising is randomized, it is uncorrelated with income, so the estimated effect of ads on sales is the same whether or
not income is included. An iClicker question asks which statements are false: that a valid experiment needs equal numbers of treatment and control observations,
that you always need controls for background characteristics, and that larger populations require larger experiments.

**Causal versus predictive questions.** Causal impact is prescriptive: there is a counterfactual absent the action (the change in sales with and without a change in
advertising, holding everything else constant; in an experiment the counterfactual comes from the control group). Prediction is descriptive: the level of sales
you would most likely observe, such as conversion rates or vote shares. To make a decision, causal evidence is often the relevant evidence; a predictive exercise
only describes the association. Examples: a manager deciding whether to change prices or tech support to raise retention is asking a causal question, while
predicting retention among groups of users is predictive; a campaign manager deciding whether to use an ad is causal, while forecasting election results from
demographics and economic fundamentals is predictive.

**Take-aways.** DAG path diagrams help analyze the direction of bias; you will face both causal and predictive questions at work; analyzing experiments with a
regression is simple. The lecture also introduces a real estate application (predicting San Francisco home prices) and bonus material showing that the omitted
variable bias in a slope depends on the omitted variable's direct effect times its relationship with the included variable.
