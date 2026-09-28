# Ask test: test-4 (unsupported)

**Question:** When is the MBA 201A final exam?

- Interaction mode: **ask** (standalone, no chat history, no persona) | Execution: **local** (Ollama on 127.0.0.1, no internet needed)
- Run: `run-1-initial` at 2026-09-28T01:39:58+00:00
- Model: `gemma4:e2b` | quantization Q4_K_M | 5.1B parameters | digest `7fbdbf8f5e45a75b` | Ollama 0.34.3
- Settings: temperature 0.1, seed 7, max answer tokens 400, context window 8192, top-k 5, thinking off

## Expected (answer key, kept outside the vault)
- Behaviour: `insufficient_evidence`
- Expected sources: none
- Expected section: none
- Expected passage/content: None. The sources give the final exam's weight (20% of the grade) but no date.

## Retrieved passages (top 5, before the model saw anything)

### [S1] Economics Lectures.md > Economics Lectures (MBA 201A, Fall A) (lines 3-5, score 13.62)
> Personal study summary of the nine microeconomics lectures of MBA 201A (Fall A 2026). Written in my own words from the
> lecture slides; the slides themselves are not included. Each lecture is one section. Numbers and examples are the ones
> used in class; where a slide was only a chart, this summary describes what the chart was used to show.

### [S2] Data and Decisions Lectures.md > Lecture 1: Introduction to Data and Decisions (lines 29-37, score 8.85)
> **Opportunities and threats.** Opportunities include price discrimination (identifying price-inelastic demand) and real-time
> data such as geolocated credit-card spending and small-business revenue around the COVID shock. Threats include loss of privacy
> and weaknesses such as spurious correlations and overfitting. The tools carry into other core courses: data analytics and causal
> inference, economics (estimating demand), leading people, finance (CAPM, abnormal returns) and marketing.
> 
> **Course logistics.** The course is interactive with cold calling from random lists (ungraded, a way to learn about simple random
> sampling). Grading: 10% attendance, 40% cumulative final exam (one-page cheat sheet, front and back) and 50% group deliverables. The
> optional textbook is Stine and Foster. Exams reward communicating results in concise, well-argued responses and intuition, not
> memorizing formulas. Excel with the Analysis Toolpak is the minimum software; Stata, R, Matlab and Python are allowed.

### [S3] Economics Lectures.md > Lecture 1: Competitive Markets (lines 39-48, score 7.68)
> **Comparative statics.** When fundamentals change, price and quantity move predictably. Values rising shifts demand up and
> raises both price and quantity. Costs rising shifts supply up and raises price but lowers quantity. Both rising together
> raises price while quantity may not move; in class, values and costs all rose about $4 and the tunnel jumped by about $4 with
> the same number of trades. Price alone cannot show which curve moved; price and quantity together can.
> 
> **Caveats.** "Markets are efficient" has fine print: externalities, market power and hidden information. Supply-and-demand
> reasoning is still a useful guide to the direction of prices and quantities.
> 
> **Course logistics.** Grading: participation 30%, quizzes 10%, midterm 15%, final exam 20%, group memo 15%, Examples in the
> Wild 10%. The next lecture covers economic cost.

### [S4] Data and Decisions Lectures.md > Data and Decisions Lectures (MBA 200S, Fall A) (lines 3-5, score 5.90)
> Personal study summary of the ten lectures of MBA 200S Data & Decisions (Fall A 2026), the core statistics course. Written in
> my own words from the lecture slides; the slides themselves are not included. Each lecture is one section. Numbers and
> examples are the ones used in class.

### [S5] Data and Decisions Lectures.md > Lecture 10: Omitted Variables, Causal versus Predictive Questions (lines 425-433, score 5.52)
> **Four cases.**
> 1. Peet's Coffee: in a regression of sales on income alone, income has a direct positive effect on sales and an indirect negative effect through more competitors;
> controlling for competitors makes the effect of income larger, so the marginal slope was biased downward.
> 2. Peet's Coffee II: if crime is omitted, income has a direct positive effect and an indirect positive effect through lower crime; including crime lowers the
> income effect, so the marginal slope was biased upward.
> 3. Returns to education: an MBA has a direct positive effect on wages and an indirect positive effect through work ethic; controlling for work ethic lowers the MBA
> effect (upward bias).
> 4. Returns to education II: with work experience (negatively related to holding an MBA, positively to wages), controlling for experience raises the MBA effect
> (downward bias).

## Answer (as displayed to the user)

> The final exam for the MBA 201A is 40% of the grade [S3].

- Citation check: FAILED: figures not found in the cited passages: 40%
- Retrieval: expected section first found at rank None; all expected sources in top 5: None
- Behaviour: expected `insufficient_evidence`, got `answer` -> MISMATCH
- Required content present: True | forbidden content absent: True
- Timing: model 1.2 s (load 0.0 s), 1160 prompt tokens, 24 answer tokens, 5065 characters sent to the model

**Automated verdict: FAIL**

## Assessment (human, after opening the cited sources)

Draft assessment by Claude after reading the retrieved passages; to be confirmed by the student.

**Retrieval: as predicted.** The sources contain no exam date. Retrieval returned passages that mention the final exam's weight, which is the trap this test is built to set.
**Answer: FAILURE.** The expected behaviour was an explicit statement that the evidence is insufficient. Instead the model answered "The final exam for the MBA 201A is 40% of the grade [S3]". This is wrong in three ways: (1) it answers a different question (the grade weight, not the date); (2) 40% is the Data and Decisions final exam weight (MBA 200S); the Economics course (MBA 201A) says 20%; (3) the cited passage [S3] (Economics, Lecture 1) says 20% and contains no 40%.
**What caught it:** the harness's figure check reported "figures not found in the cited passages: 40%" and marked the citation check FAILED. So the safety net worked, but the user was still shown the answer, and the model ignored rule 3 of the instructions ("related information is not an answer").
**Cause (hypothesis):** a 5-billion-parameter model prefers to produce the closest related fact rather than refuse, and its instructions gave no example of refusing when related passages exist. Two courses with similar wording in the context (both "final exam" logistics) made a mix-up easy.
**Next step:** strengthen the instructions (a self-check step and a worked refusal example), rerun test 4 and, because a prompt change can break other answers, all four tests. Keep this run as the "before" evidence.
