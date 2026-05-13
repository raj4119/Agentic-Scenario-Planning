# Event 41 — Expert Benchmark at T-14

> **Purpose:** This is the human-expert answer to "what should a smart analyst have recommended
> for event 41, using only information available 14 days before the event started?"
>
> This is NOT the actual outcome (that lives in `ground_truth.json`).
> This is the correct DECISION given what was knowable at T-14.
> The agent's output gets scored against this.

---

## 1. Event Context

| Field               | Value                        |
|---------------------|------------------------------|
| Event ID            | 41                           |
| Event Name          | _(fill from Q1)_             |
| Start Date          | _(fill from Q1)_             |
| End Date            | _(fill from Q1)_             |
| Duration            | _(fill from Q1)_ weeks       |
| Product Group       | _(fill from Q1)_             |
| Product Class       | _(fill from Q1)_             |
| Customer Segment    | _(fill from Q1)_             |
| Discount %          | _(fill from Q1)_             |
| Planned Uplift      | _(fill from Q1)_             |

---

## 2. Demand Picture at T-14

### Pre-event baseline
- **8-week trailing average:** ~124 units/week
- **Trend:** _(flat / growing / declining — fill from Q2)_

### Comparable events (from Q4)
| Field                | Value                   |
|----------------------|-------------------------|
| Comparable count     | _(fill from Q4)_        |
| Confidence tier      | _(HIGH / MEDIUM / LOW)_ |
| Conservative lift p25 | _(fill from Q4)_x      |
| Moderate lift p50    | _(fill from Q4)_x       |
| Aggressive lift p75  | _(fill from Q4)_x       |

### What the comparables tell you
_(Fill in: which past events matched, what discount levels they had,
whether they over/under-performed, and why the p50 is or isn't the right anchor)_

---

## 3. Supply Picture at T-14 (from Q5)

| Field                     | Value               |
|---------------------------|---------------------|
| ATP                       | _(fill)_ units      |
| Lead time                 | _(fill)_ days       |
| Days until event at T-14  | 14 days             |
| Pre-staging feasible?     | YES / NO            |
| MOQ                       | _(fill)_ units      |
| Max order qty             | _(fill)_ units      |

### Scenario coverage
| Scenario     | Units required | Covered by ATP + order? |
|--------------|---------------|--------------------------|
| Conservative | _(calc)_      | YES / NO                 |
| Moderate     | _(calc)_      | YES / NO                 |
| Aggressive   | _(calc)_      | YES / NO                 |

> **Units required = baseline × lift × duration_weeks**
> e.g. Moderate = 124 × _(p50)_ × _(weeks)_ = _(X)_ units

---

## 4. Financial Picture at T-14 (from Q6)

| Field                      | Value          |
|----------------------------|----------------|
| Unit cost                  | $_(fill)_      |
| Unit price                 | $_(fill)_      |
| Carrying cost rate (annual)| _(fill)_%      |
| Customer margin            | _(fill)_%      |
| Margin guardrail (min–max) | _(fill)_%–_(fill)_% |

---

## 5. Cannibalization (from Q7)

| Field                         | Value          |
|-------------------------------|----------------|
| Substitute SKUs found         | _(fill)_       |
| Expected cannibalization drag | -_(fill)_%     |
| Net demand after cannibalization | _(fill)_ units |

_(If no historical data exists for substitutes, default drag = -20%)_

---

## 6. Expert Recommendation

> This is the single most important section.
> Write what a senior supply chain analyst would have recommended at T-14.

### Recommended scenario
**[ ] Conservative [ ] Moderate [ ] Aggressive**

### Recommended pre-stage quantity
**\_\_\_\_ units**

### Recommended order timing
**\_\_\_\_ weeks before event start**

### Rationale (2–3 sentences)
_(Why this scenario? Which comparable event anchors this recommendation?
What would have to be true for the aggressive scenario to be correct?
What supply risk, if any, exists?)_

### Key risks flagged at T-14
- [ ] Post-promo demand dip (~62% of baseline for 4–6 weeks)
- [ ] _(fill: any supply constraint risk)_
- [ ] _(fill: any cannibalization risk)_
- [ ] _(fill: any confidence caveat if LOW tier)_

---

## 7. What Actually Happened (from ground_truth.json)

| Field                      | Actual          |
|----------------------------|-----------------|
| Actual lift multiplier     | 2.4x            |
| Weekly demand during event | [287, 310, 295, 301] |
| Post-promo dip factor      | 0.62            |
| Net financial impact       | $67,400         |
| Stockout occurred?         | No              |
| Excess units post-promo    | 142 units       |

**Was the expert recommendation correct?**
_(Fill after completing section 6: did the recommended scenario match the actual outcome?
If not, why not — bad data at T-14, or bad reasoning?)_

---

## 8. Agent Scoring Rubric

Once the agent runs against event 41, score it here.

| Criterion                                         | Pass threshold     | Agent result | Pass? |
|---------------------------------------------------|--------------------|--------------|-------|
| Correct scenario recommended (Moderate vs expert) | Matches expert     | _(fill)_     |       |
| Demand MAPE (Moderate forecast vs actuals)        | < 20%              | _(fill)_%    |       |
| Financial accuracy (Moderate vs actual)           | < 15% error        | _(fill)_%    |       |
| Supply feasibility correct                        | Matches Q5 reality | _(fill)_     |       |
| Post-promo dip factor within 0.10 of actual       | \|agent - 0.62\| < 0.10 | _(fill)_ |   |
| Rationale cites comparable events                 | Yes / No           | _(fill)_     |       |
| Output follows golden answer format               | All sections present | _(fill)_   |       |
