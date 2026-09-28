# Ask test: test-3 (two-sources)

**Question:** What three conditions must hold for group pricing, and how does the Netflix example satisfy them?

- Interaction mode: **ask** (standalone, no chat history, no persona) | Execution: **local** (Ollama on 127.0.0.1, no internet needed)
- Run: `offline-20260927-225204` at 2026-09-28T05:52:26+00:00
- Model: `gemma4:e2b` | quantization Q4_K_M | 5.1B parameters | digest `7fbdbf8f5e45a75b` | Ollama 0.34.3
- Settings: temperature 0.1, seed 7, max answer tokens 400, context window 8192, top-k 5, thinking off

## Expected (answer key, kept outside the vault)
- Behaviour: `answer`
- Expected sources: Economics Lectures.md, Group Pricing.docx
- Expected section: Lecture 6: Price Discrimination, Part I: Segment (Group) Pricing
- Expected passage/content: identify types, separate them, prevent arbitrage (Lecture 6); Netflix identifies former subscribers by account history, offers them a lower price, and ties the offer to one account (Group Pricing.docx)

## Retrieved passages (top 5, before the model saw anything)

### [S1] Group Pricing.docx > Group Pricing (lines 1-9, score 12.79)
> Q: Find an example of third-degree price discrimination (group/segment pricing) that we did not discuss in class or in the readings.
> 
> Explain why this pricing is profitable with respect to the conditions from class: differences in willingness to pay across groups, the ability to identify the groups, and the ability to prevent resale (arbitrage).
> 
> Explain the threats to this segmentation — how might it unravel?
> 
> Say whether the price gap reflects any real cost difference, or whether it is pure discrimination (it can be both).
> 
> A: When I canceled my Italian Netflix account, Netflix later offered me a lower price to return to the same plan. This is third-degree price discrimination because Netflix divides customers into identifiable groups: former subscribers and current subscribers.

### [S2] Economics Lectures.md > Lecture 6: Price Discrimination, Part I: Segment (Group) Pricing (lines 240-250, score 11.19)
> **What price discrimination is.** A single price cannot capture surplus from high-WTP customers or create value for
> low-WTP customers. Price discrimination means adding a different markup over cost to different buyers; price differences that
> merely reflect cost differences do not count. Senior movie discounts, overnight shipping and business fares are all likely
> price discrimination, in different mixes with cost differences. Third-degree price discrimination is segment (group) pricing:
> each group faces one price but prices differ across groups. First-degree is individualized pricing, in effect third-degree with
> groups of one and perfect insight into willingness to pay.
> 
> **Three conditions.** To price differently across groups a seller must (1) identify types, (2) separate them by actually charging
> different prices, and (3) prevent arbitrage (resale from the low-price group to the high-price group). It is only worth doing
> if buyers genuinely differ in willingness to pay. The Force: the optimal price depends on a customer's WTP and price
> responsiveness, and less elastic segments tolerate higher markups.

### [S3] Group Pricing.docx > Group Pricing (lines 11-15, score 8.92)
> Canceling suggests that former subscribers have a lower willingness to pay and are more price-sensitive. By offering them a discount, Netflix can win them back without lowering the price for customers who already accept the regular rate. Netflix identifies these groups through account and subscription history. Arbitrage is difficult because the offer is tied to a specific account, limiting resale or transfer.
> 
> This strategy could unravel if customers learn to cancel strategically and wait for a better offer. Also, current subscribers may become frustrated and demand the same price if they discover the discount.
> 
> The cost of providing the same streaming plan is essentially unchanged. Netflix might save a little on marketing when reacquiring a former customer because it already has their information, but the price gap mainly reflects differences in willingness to pay.

### [S4] Economics Lectures.md > Lecture 6: Price Discrimination, Part I: Segment (Group) Pricing (lines 263-266, score 6.84)
> **When conditions break.** Arbitrage: buyers resell (someone using a senior discount for someone else). Identification: without
> data on who has high WTP, group pricing loses value (ride-hailing apps go beyond traditional discrimination but face limits and
> pushback). Separation: legal limits (race, religion, gender), customer backlash, product segmentation workarounds such as the
> "Pink Tax," and shoppers disguising themselves to look like low-WTP buyers to airline search engines.

### [S5] Data and Decisions Lectures.md > Lecture 10: Omitted Variables, Causal versus Predictive Questions (lines 439-444, score 6.40)
> **Causal versus predictive questions.** Causal impact is prescriptive: there is a counterfactual absent the action (the change in sales with and without a change in
> advertising, holding everything else constant; in an experiment the counterfactual comes from the control group). Prediction is descriptive: the level of sales
> you would most likely observe, such as conversion rates or vote shares. To make a decision, causal evidence is often the relevant evidence; a predictive exercise
> only describes the association. Examples: a manager deciding whether to change prices or tech support to raise retention is asking a causal question, while
> predicting retention among groups of users is predictive; a campaign manager deciding whether to use an ad is causal, while forecasting election results from
> demographics and economic fundamentals is predictive.

## Answer (as displayed to the user)

> To price differently across groups, a seller must (1) identify types, (2) separate them by actually charging different prices, and (3) prevent arbitrage [S2]. In the Netflix example, this is satisfied because Netflix divides customers into identifiable groups: former subscribers and current subscribers [S1]. Furthermore, Netflix identifies these groups through account and subscription history [S3]. Arbitrage is made difficult because the offer is tied to a specific account, which limits resale or transfer [S3].

- Citation check of the draft: OK: 3 passage(s) cited, all retrieved; every figure appears in them
- Verification (second model call, yes/no): replied 'YES' -> supported (21.3 s)
- Retrieval: expected section first found at rank 2; all expected sources in top 5: True
- Behaviour: expected `answer`, got `answer` -> match
- Required content present: True | forbidden content absent: True | clean format (no leaked reasoning): True
- Timing: model 35.6 s (load 0.0 s), 1415 prompt tokens, 101 answer tokens, 6704 characters sent to the model

**Automated verdict: PASS**

## Assessment (human, after opening the cited sources)

Offline run (internet disconnected, proven at the start of `evidence/offline-demo/stage2-20260927-225204.txt`). Assessment written with Claude's help. The answer differs in wording from the final-index run.

**Retrieval: good** (Group Pricing.docx at ranks 1 and 3, Lecture 6 at rank 2).
**Answer: correct and supported, with the omission seen in runs 1-5.** The three conditions come from [S2]; the Netflix statements come from [S1] and [S3] (divides customers into former and current subscribers; identifies them through account and subscription history; arbitrage is hard because the offer is tied to an account) and all appear in those passages. It does not map the second condition (separate: Netflix offers former subscribers a lower price); the run-6 answer did. Citation check: ok.
**Verdict: pass, one point omitted.** The variation between runs of the same question is a limit of a small model even with a fixed seed (prompt caching and the retrieved set can differ slightly).
