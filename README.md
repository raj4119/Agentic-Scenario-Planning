# Agentic-Scenario-Planning
Transforming Supply Chain using Agentic AI 


# CASCI — Composable Agentic Supply Chain Intelligence
## Master Product Requirements Document

**Version:** 1.0
**Status:** Active — POC #1 In Progress
**Last Updated:** 2026-05-02
**Owner:** Product Management
**Contributors:** PM, Data Science, Engineering, Demand Planning SME, IT/Security, Supply Chain Manager
**Related Docs:** [Architecture](AGENT_ARCHITECTURE.md) · [Production Readiness](PRODUCTION_READINESS.md)

---

## Table of Contents

1. [What is CASCI](#1-what-is-casci)
2. [Platform Vision & Strategy](#2-platform-vision--strategy)
3. [Platform Architecture Overview](#3-platform-architecture-overview)
4. [Autonomy Ladder](#4-autonomy-ladder)
5. [Six-Layer Memory System](#5-six-layer-memory-system)
6. [CASCI Use Case Roadmap](#6-casci-use-case-roadmap)
7. [POC #1: Promotional Event Scenario Planning](#7-poc-1-promotional-event-scenario-planning)
   - 7.1 [Problem Statement](#71-problem-statement)
   - 7.2 [Goals & Success Metrics](#72-goals--success-metrics)
   - 7.3 [User Personas](#73-user-personas)
   - 7.4 [Use Case Detail](#74-use-case-detail)
   - 7.5 [Functional Requirements](#75-functional-requirements)
   - 7.6 [AI Evaluation Criteria](#76-ai-evaluation-criteria)
   - 7.7 [AI Guardrails & Safety](#77-ai-guardrails--safety)
   - 7.8 [Non-Functional Requirements](#78-non-functional-requirements)
8. [Model Governance](#8-model-governance)
9. [Rollout Strategy](#9-rollout-strategy)
10. [Out of Scope](#10-out-of-scope)
11. [Open Questions](#11-open-questions)
12. [POC #1 Delivery Plan](#12-poc-1-delivery-plan)

---

## 1. What is CASCI

**CASCI (Composable Agentic Supply Chain Intelligence)** is Blue Ridge's platform for deploying AI agents that actively monitor, reason about, and act on supply chain data — with configurable autonomy, explainable decisions, and a layered memory system that learns from history and understands relationships between entities.

CASCI is **not** a chatbot. A chatbot answers questions. CASCI agents take actions: they detect events, run analyses, generate recommendations, and — when autonomy is configured — execute decisions on behalf of planners.

The fundamental design principle: **supply chain intelligence should be composable.** Each use case (scenario planning, supplier risk, replenishment) is built as a set of agents and tools that share the same underlying platform — the same data connectors, the same memory system, the same orchestration framework, the same model governance. Building the second use case should take a fraction of the time and cost of building the first.

### CASCI vs. BLU

| | BLU (Conversational AI) | CASCI (Agentic AI) |
|---|---|---|
| Core capability | Answer questions about documents | Take multi-step autonomous actions |
| Data access | Documents and knowledge base | Databases, APIs, algorithms, knowledge graph |
| Reasoning depth | Single-hop lookup | Multi-hop traversal, counterfactual simulation |
| Can simulate scenarios? | No | Yes |
| Takes actions? | No | Yes, with configurable autonomy |
| Audit trail? | No | Yes — full decision provenance |
| Memory | Session only | Six-layer persistent memory |

Both BLU and CASCI are valuable. BLU handles "help me understand X." CASCI handles "do something about X."

---

## 2. Platform Vision & Strategy

### The Problem CASCI Solves at Platform Level

Supply chain planners at Blue Ridge's customers face a repeating pattern: **they have access to data, but not to intelligence at the moment of decision.** When a promotional event is announced, when a supplier signals a disruption, when inventory positions drift toward risk — the planner must manually pull data from multiple sources, build scenarios in spreadsheets, and make a decision under time pressure with incomplete information.

Blue Ridge's rule-based inventory optimization engine is exceptional at steady-state management. It was not designed to handle high-variance, event-driven scenarios that require multi-source reasoning, pattern matching across history, and fast scenario generation. CASCI fills this gap.

### Why Now

Three capabilities are now production-ready that were not available 18 months ago:

1. **MCP (Model Context Protocol)** — A standardized protocol for connecting LLMs to external tools and data sources. Blue Ridge already has an MCP server operational. This is the connective tissue of the platform.
2. **LangGraph** — A mature Python framework for building stateful, multi-step agent workflows with conditional routing, parallel execution, and human-in-the-loop checkpoints. Production-grade agent orchestration without custom boilerplate.
3. **LLMs capable of structured reasoning** — Claude Sonnet/Opus can reliably generate structured JSON outputs, reason about supply chain constraints, and produce narrative explanations grounded in provided evidence — all critical capabilities for a production planning tool.

The combination of these three makes CASCI achievable today in a way it was not before.

### Platform Strategy: POC First, Platform Second

The correct build sequence is:
1. **POC #1 (Scenario Planning):** Prove the core pattern works against one real use case with measurable outcomes. Do not build platform abstractions prematurely.
2. **POC #1 to Production:** Make Scenario Planning production-ready, including eval pipeline, guardrails, monitoring, and human-in-the-loop enforcement.
3. **Platform Extraction:** Once two or three use cases exist, extract the shared platform components (agent templates, shared tools, memory system, KG ETL) into reusable infrastructure.
4. **Use Case Expansion:** Each subsequent use case is built on the platform and takes progressively less time.

This sequence prevents premature abstraction while still building toward the CASCI platform vision.

---

## 3. Platform Architecture Overview

CASCI is built on three layers. Each layer has a distinct responsibility and can evolve independently.

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: ORCHESTRATION (LangGraph)                         │
│  What steps, in what order, with what branching logic?      │
│  Manages agent state, parallel execution, human checkpoints │
└─────────────────────────────┬───────────────────────────────┘
                              │ agents call tools via
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: TOOL CONNECTIVITY (MCP)                           │
│  Standardized interface to all external tools and data      │
│  SQL queries, API calls, algorithm invocations              │
│  "Everything is an MCP tool"                                │
└──────────────────┬──────────────────────┬───────────────────┘
                   │                      │
          ┌────────▼───────┐    ┌─────────▼────────┐
          │  RELATIONAL DB │    │  KNOWLEDGE GRAPH  │
          │  (TenantDB)    │    │  (Neo4j)          │
          │  Quantities    │    │  Relationships    │
          │  Time series   │    │  Entity graph     │
          │  Costs         │    │  Multi-hop queries│
          └────────────────┘    └──────────────────┘
```

**Layer 1 — LangGraph (Orchestration):** Defines the agent's decision flow as a graph of steps (nodes) and transitions (edges). Controls what happens in what order, handles conditional branching (e.g., "if no historical comparables found, route to low-confidence path"), manages state across all steps, and enforces human-in-the-loop checkpoints. See [Architecture Doc](AGENT_ARCHITECTURE.md) for full graph definitions.

**Layer 2 — MCP (Tool Connectivity):** Every data source, algorithm, and external API the agents need is registered as an MCP tool. The LangGraph agents call these tools without needing to know their implementation. This means adding a new data source to the platform requires only registering a new MCP tool — no changes to the agent logic.

**Relational DB (TenantDB):** Owns quantitative, time-series data — demand history, inventory positions, costs, order quantities, supplier lead times. Agents query this via read-only SQL tools.

**Knowledge Graph (Neo4j):** Owns relationship data — which supplier supplies which product, which product is stored at which location, which products are substitutes for each other, which suppliers share raw materials. The KG enables multi-hop traversal queries that are impractical in SQL (e.g., "if Supplier A fails, which customers are affected, through which products, at which locations?"). KG is populated via ETL from TenantDB and is the key capability gap being built in CASCI Phase 2.

### Six-Layer Memory System

Each CASCI agent has access to a six-layer memory stack that gives it context beyond the current query:

| Layer | Type | What it stores | Built? |
|-------|------|----------------|--------|
| L1 | Instruction Memory | Rules the agent must always follow (tenant configuration, compliance constraints) | Phase 1 |
| L2 | Short-Term Memory | Context from the current session (what the planner is working on, prior queries this session) | Phase 1 |
| L3 | Episodic/Knowledge Memory | Specific past agent decisions and their outcomes ("last time scenario C was selected for this SKU, actual demand was 2.8x") | Phase 2 |
| L4 | Profile Memory | User and tenant preferences (preferred scenario naming, risk tolerance settings, approval thresholds) | Phase 2 |
| L5 | Graph Memory | The Knowledge Graph — entity relationships and multi-hop traversal | Phase 3 |
| L6 | Semantic Vector Memory | RAG layer — similarity search over documents, historical event patterns, supplier notes | Phase 1 (existing) |

For POC #1, L1, L2, and L6 are sufficient. L3–L5 are built as CASCI matures.

---

## 4. Autonomy Ladder

CASCI uses a four-level autonomy model that governs how much authority each agent has to act without human intervention. Trust is earned over time — agents start at Level 1 and advance only when accuracy and reliability are demonstrated.

```
LEVEL 1 — SHADOW
Agent runs in background. Outputs are logged but not shown to planners.
Used during: internal pilot phase, new use case validation
"Here is what I would have recommended — for your awareness only."

LEVEL 2 — RECOMMENDATION  ← POC #1 Target
Agent surfaces recommendations to planners. Planners decide whether to act.
No action taken without explicit planner selection.
"I recommend Scenario B. You select and I execute on your approval."

LEVEL 3 — SUPERVISED AUTONOMY
Agent acts, but within a time-bounded review window.
Planner can override within N hours; after that, the action is confirmed.
"I've applied the replenishment policy. Override window: 4 hours."

LEVEL 4 — FULL AUTONOMY
Agent acts without human checkpoint, for pre-qualified event types.
Reserved for high-confidence, low-risk, high-frequency decisions.
Full audit trail always maintained.
"Order submitted. See audit log for parameters."
```

**POC #1 (Scenario Planning) will operate at Level 2.** No autonomous action. Planners review and select. The system never writes back to Blue Ridge without an explicit planner action. Advancing to Level 3 or 4 requires demonstrating accuracy over a minimum of 12 months of production use and formal governance sign-off.

---

## 5. Six-Layer Memory System

This section details how the memory layers function and what data they hold. Memory is what distinguishes CASCI from a stateless LLM call — it enables the agent to learn from history, respect user preferences, and understand relationships.

### L1 — Instruction Memory
Hard-coded rules injected into every agent prompt. These are tenant-configurable and represent compliance constraints, business rules, and safety guardrails. Examples:
- "Never recommend a scenario that requires an order exceeding the supplier's max_order_qty"
- "For events with projected revenue > $50K, always flag for manager review"
- "When confidence score < 0.5, always require planner acknowledgment before submission"

L1 is configured in `enterprise_settings` and loaded at agent initialization. It cannot be overridden by the LLM — it is injected before the LLM's reasoning begins.

### L2 — Short-Term Memory
State accumulated within the current session. In LangGraph terms, this is the `ScenarioPlanningState` TypedDict — every field written by every agent during a single pipeline run. Cleared when the session ends. Enables agents downstream in the pipeline to reference decisions made by agents upstream without re-querying.

### L3 — Episodic/Knowledge Memory
Persistent store of past agent decisions and outcomes. Example records:
- "For SKU PROT-500-CHO, agent recommended Moderate scenario on 2026-01-15. Planner selected Conservative. Actual demand was 2.1x (between Conservative and Moderate). Agent's Moderate recommendation was correct."
- "Post-event review on 2026-02-20: actual MAPE for this event was 14%. Confidence score at generation was 0.72."

L3 is stored in AuditDB and is queried by agents when they need to reason about their own past performance or look up what happened last time a similar decision was made. Not built in POC #1 — introduced in CASCI Phase 2.

### L4 — Profile Memory
Persistent preferences per user and per tenant. Examples:
- User Sarah prefers conservative scenarios for new SKUs (override applied automatically)
- Tenant ABC has a hard rule: never recommend pre-stage quantities > 3 months of supply
- User preferences for output format (weekly vs. daily granularity, USD vs. local currency)

L4 makes CASCI feel personalized. Not built in POC #1 — introduced in CASCI Phase 2.

### L5 — Graph Memory (Knowledge Graph)
The Neo4j knowledge graph. Stores the supply chain entity graph:
- `(:Supplier)-[:SUPPLIES]->(:Product)`
- `(:Product)-[:STORED_AT]->(:Location)`
- `(:Location)-[:SERVES]->(:Customer)`
- `(:Product)-[:SUBSTITUTES_FOR {weight}]->(:Product)`
- `(:Supplier)-[:SHARES_MATERIAL_WITH]->(:Supplier)`

L5 is what enables multi-hop reasoning: "which customers are affected if Supplier X fails?" This traversal is impossible with SQL joins at scale. Not built in POC #1 (agents use SQL for relationship queries) — introduced in CASCI Phase 3 to unlock Scenario Planning V2 and the Supplier Risk use case.

### L6 — Semantic Vector Memory (RAG)
The existing RAG pipeline — already operational at Blue Ridge. Stores embeddings of historical event records, supplier documents, product notes. Enables similarity search: "find the 3 most similar past promotional events to this one." Used by the Demand Decomposition Agent in POC #1 to find historical comparables. This is the only memory layer active in POC #1.

---

## 6. CASCI Use Case Roadmap

Each use case is implemented as a set of LangGraph agents registered on the CASCI platform. Use cases share the data layer (TenantDB + KG), the MCP tool registry, and the memory system — only the agent logic and prompts differ.

| # | Use Case | Platform Dependency | Autonomy Target | Phase |
|---|----------|--------------------|--------------------|-------|
| UC-01 | **Promotional Event Scenario Planning** | L6 (RAG) | Level 2 (Recommendation) | **POC #1 — Now** |
| UC-02 | **Supplier Risk Intelligence** | L5 (KG) + L6 | Level 2 | Phase 3 |
| UC-03 | **Replenishment Optimization** | L3 (Episodic) + L5 | Level 3 (Supervised) | Phase 3 |
| UC-04 | **Demand Signal Anomaly Detection** | L6 | Level 3 | Phase 2 |
| UC-05 | **Multi-Sourcing Scenario Planning** | L5 (KG) | Level 2 | Phase 3 |
| UC-06 | **Exception Triage & Prioritization** | L3 + L4 | Level 3 | Phase 4 |
| UC-07 | **Post-Promotional Learning Feed** | L3 | Level 4 (Full) | Phase 4 |
| UC-08 | **Order Policy Optimization** | L3 + L5 | Level 2 | Phase 5 |

### Use Case Interdependencies

```
UC-01 (Scenario Planning)
    └── Produces: historical event outcomes for L3 (episodic memory)
    └── Requires: L6 (RAG over historical events) — EXISTING

UC-04 (Anomaly Detection)
    └── Feeds: anomaly signals into UC-01 and UC-03
    └── Requires: L6 — EXISTING

UC-02 (Supplier Risk)
    └── Feeds: supplier risk context into UC-01 supply constraint assessment
    └── Requires: L5 (KG) — Phase 3

UC-03 (Replenishment)
    └── Benefits from: UC-01 promotional demand adjustments
    └── Requires: L3 (episodic) — Phase 2; L5 (KG) — Phase 3

UC-05 (Multi-Sourcing Scenarios)
    └── Extends: UC-01 supply constraint assessment for multi-PSN events
    └── Requires: L5 (KG for supplier network traversal) — Phase 3
```

The POC #1 (UC-01) is deliberately chosen as the first use case because it:
1. Has a clear, measurable outcome (MAPE, financial accuracy)
2. Has existing data (event_prod_loc_cust_uplift, demand_history)
3. Requires only L6 memory (existing RAG) — no KG needed
4. Delivers direct planner value (2–3 days → 30 minutes)
5. Produces episodic memory records that feed future use cases

---

## 7. POC #1: Promotional Event Scenario Planning

### 7.1 Problem Statement

When a major promotional event is announced, demand planners have no system to model multiple possible inventory futures before the event starts. They manually build scenarios in spreadsheets over 2–3 days — consuming most of the available response window — and make a single binary decision (adjust or don't adjust) with no quantified view of the financial risk in either direction.

The result is a repeating cycle of either under-stocking promoted SKUs (stockouts, lost revenue, service failures) or over-ordering in post-promotional recovery (excess carrying cost, markdown risk). Both outcomes are expensive and entirely preventable with the right information at the right time.

#### Root Causes

**1. Statistical forecast lag (2–4 weeks)**
Blue Ridge's exponential smoothing models are parameterized for stable, recurring demand. Promotional demand spikes are treated as noise and smoothed away. The forecast only adapts after 2–4 weeks of sustained elevated demand — at which point most of the promotional window has passed.

**2. No cross-SKU reasoning (cannibalization not modeled)**
A 30% discount on Product A suppresses demand on close substitutes. The current system models each SKU independently. Planners have no automated visibility into cannibalization effects.

**3. No institutional memory of past promotions**
Historical events in `event_prod_loc_cust_uplift` contain rich signal — how much did demand lift for a similar SKU, with a similar discount, for a similar customer segment? This data exists but is not surfaced to planners or used by the engine.

**4. Manual scenario building (2–3 days, error-prone)**
Opening a spreadsheet, pulling history manually, applying judgment-based multipliers. Takes 2–3 days when lead time may be 3–4 weeks — consuming most of the available response window.

**5. Binary policy decisions rather than scenario-based choices**
The output is a single adjusted demand figure. There is no structured comparison of outcomes under different demand realizations, no explicit service level trade-off, and no pre-computed fallback position.

**6. No quantified risk/reward trade-off at decision time**
Planners make promotional inventory decisions without a clear view of the financial consequences of getting it wrong in either direction.

#### Why Now

The `event_prod_loc_cust_uplift` table exists and is populated — uplift data is being captured but not used to inform pre-event planning. Demand history (156 weekly periods per SKU) is available and rich enough to support historical pattern matching. The MCP server is operational. LangGraph is available. The three missing pieces are: the agent logic, the orchestration, and the evaluation framework. CASCI POC #1 provides all three.

---

### 7.2 Goals & Success Metrics

#### POC Goals

- Generate 3 realistic scenarios for a single promotional event that planners independently assess as credible (planner realism score ≥ 4/5)
- Financial projections within ±15% of actuals when validated against a completed historical promotional event
- Planner can review and select in under 30 minutes (vs. 2–3 day manual process)

#### Production Goals

- Cover 100% of planned promotional events detected ≥ 2 weeks before start date
- Reduce promotional stockout rate by 20% relative to pre-system baseline
- Reduce post-promotional overstock carrying cost by 15% relative to baseline
- Planner adoption rate > 70% (scenarios generated by system are selected through system, not overridden by spreadsheet)

#### KPI Tracking

**Business KPIs**

| KPI | Baseline | Target | Measurement |
|-----|----------|--------|-------------|
| Stockout rate during promotional periods | TBD from historical data | -20% vs. baseline | COSA `shortage_in_units` during event windows |
| Post-promo overstock carrying cost | TBD from historical data | -15% vs. baseline | `carrying_cost_rate × excess_units × weeks_held` |
| Scenario generation time | 2–3 days (manual) | < 5 minutes | System timestamp: event detection → scenarios ready |
| Planner adoption rate | 0% (no system) | > 70% | Scenarios executed via system / total scenarios generated |
| Planner override rate | N/A | < 30% | Scenarios where planner changed AI parameters before submitting |

**AI Quality KPIs**

| KPI | POC Target | Production Target | Measurement |
|-----|-----------|------------------|-------------|
| Demand forecast MAPE (moderate scenario) | < 20% | < 15% | Actual vs. projected demand per event, post-event |
| Financial projection accuracy | ±15% of actuals | ±10% of actuals | Actual vs. projected net financial impact |
| Scenario recommendation correctness | ≥ 80% of eval cases | ≥ 85% of eval cases | System-recommended scenario matches best-in-hindsight |
| LLM-as-judge scenario quality score | ≥ 4.0 / 5.0 | ≥ 4.2 / 5.0 | Automated judge on differentiation, plausibility, coverage, narrative |
| Agent confidence calibration | Directionally correct | Pearson r > 0.7 | Correlation between confidence score and actual MAPE |
| Guardrail trigger rate | N/A (establish baseline) | < 10% of runs | % of runs where output validation rejects and retries |

---

### 7.3 User Personas

#### Primary: Demand Planner
The demand planner reviews AI-generated scenarios, selects the one that best matches their business judgment, and optionally overrides specific parameters before submitting for execution.

**Needs:** Clear rationale in supply chain language (not AI jargon). Financial impact in KPIs they already track. Ability to override specific assumptions. Confidence in data sources.

**Pain today:** Spends 2–3 days manually constructing scenarios. No confidence interval on promotional forecasts. Cannot easily compare trade-offs across inventory policies.

#### Secondary: Supply Chain Manager
Reviews and approves scenario selections for high-value or high-risk events. Does not build scenarios but needs to quickly assess whether the planner's selection is defensible.

**Needs:** Executive summary view. Clear visibility into downside risk. Comparative financial risk exposure.

**Pain today:** Visibility into promotional inventory decisions typically arrives only after a stockout or overstock event has already occurred.

#### Tertiary: IT / Data Engineering
Maintains integration between the AI system and Blue Ridge. Must be able to maintain, troubleshoot, and extend the system.

**Needs:** Clear API contracts. Observable agent behavior. Minimal ongoing maintenance. Confidence the system cannot corrupt production data.

---

### 7.4 Use Case Detail

#### Trigger
A promotional event is detected in the Blue Ridge pricing database with `start_date ≥ T + 14 days`. Detection runs as a scheduled daily job.

#### Scope

| Dimension | POC Scope | Phase 2 Expansion |
|-----------|-----------|-------------------|
| Events | Single promotional event | Multiple simultaneous events |
| SKUs | Single SKU | Product group (all SKUs in product class) |
| Customers | Single customer | Customer segment |
| Locations | Single DC/store | Multi-location distribution |
| Horizons | Pre-event, during, post-event recovery (6 weeks) | Real-time mid-event adjustment |

#### Happy Path

| Step | Detail |
|------|--------|
| Event | 4-week, 30% promotional discount on SKU PROT-500-CHO at Customer Y |
| Historical match | 2 similar completed promotions: same product class, 25–35% discount, comparable customer segment |
| Lift scenarios | Conservative: 2.0x baseline; Moderate: 2.5x; Aggressive: 3.0x |
| Supply assessment | On-hand: 1,200 units; lead time: 10 days; Moderate feasible; Aggressive requires order within 3 days |
| Financial comparison | Conservative: +$42K net / 94% SL; Moderate: +$67K / 97%; Aggressive: +$71K / 99% (higher carrying cost risk) |
| Planner action | Selects Moderate; overrides service level from 97% to 95% to reduce pre-stage quantity |
| System action | Updates safety stock and reorder point in Blue Ridge; creates audit record |

#### Edge Cases

**Zero-history SKU:** Confidence score 0.3 (LOW). Scenarios generated using category-level benchmarks. Prominent LOW CONFIDENCE flag. Planner must check acknowledgment before submission.

**Last-minute deal (< 14 days):** Supply Constraint Agent detects: "Lead time = 10 days, event start = 8 days away. Pre-stage order not fulfillable." Scenarios reflect available-to-promise only. Constraint banner displayed.

---

### 7.5 Functional Requirements

#### FR-01: Event Detection
- Detect new deals where `start_date ≥ current_date + 14 days`
- Extract: affected SKUs, customer(s), location(s), event duration, discount percentage
- Query historical data to identify similar past promotions (same product group, discount ±10%, similar customer segment)
- Events already processed must not re-trigger unless material parameters change

#### FR-02: Demand Decomposition
- Decompose expected demand into: **baseline** (pre-event rolling average), **promotional lift** (based on historical comparable matching), **post-promotional dip** (recovery factor)
- Estimate cannibalization impact on substitute SKUs within same product class
- Generate week-by-week demand forecasts for all three scenario horizons for each lift scenario
- `demand_history` serves as foundation; `event_prod_loc_cust_uplift` applied as adjustment layer
- Include confidence score based on quality and quantity of historical similar events found

#### FR-03: Supply Constraint Assessment
- Calculate current inventory position: `on-hand − committed + on-order`
- Retrieve supplier lead time, MOQ, and max order quantity from sourcing data
- Assess DC storage capacity at relevant locations
- Determine whether pre-stage quantity implied by each scenario is physically fulfillable
- Constraint violations surfaced to planner with plain-language explanations

#### FR-04: Scenario Generation
- Generate exactly **3 named scenarios**: Conservative, Moderate, Aggressive
- Each scenario: pre-stage order quantity, order placement timing, service level target, post-event rundown plan, week-by-week demand projection
- Each scenario includes **narrative rationale** (LLM-generated) explaining demand assumptions and key risks
- Scenarios **meaningfully differentiated by underlying demand assumptions** — not merely ±10% variations on one parameter
- Infeasible scenarios clearly marked, not silently omitted

#### FR-05: Financial Impact Quantification
- Per scenario: projected revenue, carrying cost, expected stockout cost, net financial impact
- All calculations use current unit cost, carrying cost rate, and customer margin from system data
- **Confidence interval** (±X%) on each projection derived from demand forecast uncertainty
- Rank scenarios by net financial impact; highlight top recommendation

#### FR-06: Planner Interface
- **Side-by-side comparison view** with summary card and financial comparison table per scenario
- Planner can **override** lift assumption, service level target, and order placement timing per scenario
- **Approval workflow**: planner selects → (optional) manager approval for high-value events → system executes
- **Exportable summary** (PDF or Excel) suitable for stakeholder review
- Supply chain terminology throughout — no AI/ML jargon in user-facing text

#### FR-07: Write-back & Execution
- Upon approval, update **safety stock, reorder point, and order quantities** in Blue Ridge via existing approved APIs
- Create complete **audit trail**: planner identity, scenario selected, parameters applied, timestamp, approval chain
- **Schedule post-event review** task for 6 weeks after event end date
- No direct writes to TenantDB — all changes flow through Blue Ridge change management APIs

#### FR-08: Post-Event Learning
- Compare actual demand vs. projected demand for each scenario horizon post-event
- Flag deviations > 20% for data science review
- Store outcome data for future similar event matching
- Learning not applied automatically — flagged outcomes require human review before influencing future generation

---

### 7.6 AI Evaluation Criteria

Evaluation is a first-class requirement. The system must be measurably accurate before planners can trust it.

#### Three Layers of Evaluation

| Layer | What it tests | Method |
|-------|--------------|--------|
| **Deterministic** | Math correctness: inventory position, financial calculations | Exact-match unit tests |
| **Structured accuracy** | LLM output accuracy: lift assumptions, quantities, service levels | Numeric comparison against historical actuals |
| **Qualitative** | LLM output quality: narratives, differentiation, planner-readiness | LLM-as-judge with calibrated rubric |

All three layers required. Passing only unit tests validates infrastructure, not output quality.

#### Eval Dataset

- **POC:** 5–10 completed promotional events from last 12–18 months with known outcomes
- **Production:** 20+ events spanning multiple product categories, customer segments, outcome types
- Include events where things went wrong. Include at least one zero-comparable case. Do not cherry-pick successes.

#### Per-Agent Evaluation Criteria

**Demand Decomposition Agent**

| Metric | POC Pass | Production Pass |
|--------|----------|----------------|
| MAPE on moderate lift scenario | < 20% | < 15% |
| Correct historical comparable identified | ≥ 70% of cases | ≥ 85% of cases |
| Post-promo dip factor direction correct | ≥ 80% of cases | ≥ 90% of cases |
| Confidence score calibration | Directionally correct | Pearson r > 0.7 with actual MAPE |

Fail condition: MAPE > 30% on any single eval case without a low-confidence flag.

**Supply Constraint Agent** (deterministic — exact-match eval)

| Metric | Pass Threshold |
|--------|--------------|
| Available-to-promise calculation | Within ±1 unit |
| Fulfillability flag correctness | 100% — binary decision with direct operational impact |
| Storage capacity correctly applied | Constraint flagged when DC utilization > 85% |

Fail condition: Any fulfillability flag mismatch.

**Scenario Generator Agent — LLM-as-Judge (1–5 rubric)**

| Criterion | 5 (Pass) | 1 (Fail) |
|-----------|----------|----------|
| Differentiation | 3 scenarios based on clearly different demand beliefs | Scenarios feel like same assumption with different numbers |
| Plausibility | All grounded in realistic reasoning and historical context | One or more contradicts historical data or is physically impossible |
| Coverage | Spans genuinely risk-averse to genuinely risk-tolerant | All scenarios cluster around same risk level |
| Narrative clarity | Explains what, why, and key risk; non-technical planner can relay it | Generic, could apply to any promotion |

Pass threshold: Overall average ≥ 4.0. No individual criterion below 3.0.

**Financial Impact Agent**

| Metric | POC Pass | Production Pass |
|--------|----------|----------------|
| Net financial impact accuracy | ±15% of actuals | ±10% of actuals |
| Carrying cost calculation | Exact match | Exact match |
| Confidence interval coverage | Actual falls within CI in ≥ 70% cases | ≥ 80% of cases |
| Recommendation ranking correctness | ≥ 70% of eval cases | ≥ 80% of eval cases |

#### Evaluation as a CI/CD Gate

All eval functions run automatically on every PR to `main`. A PR is blocked if:
- Any agent's eval score drops by more than 5% relative to previous passing run
- Any previously passing eval case now fails
- New eval cases cannot lower overall scores below thresholds

#### LLM-as-Judge Calibration

1. Collect 10–15 scenario sets already scored by demand planners
2. Run judge prompt against same sets
3. Compute agreement rate: judge score within ±0.5 of human score
4. **Calibration passes if agreement rate ≥ 80%**
5. Re-calibrate every 6 months or when judge model version changes

#### Online Evaluation (Post-Launch)

- **Trigger:** 6 weeks after every promotional event end date
- **Process:** Pull actual demand history, compare to scenario projections at generation time, compute MAPE and financial accuracy, log to AuditDB
- **Alerts:** Rolling MAPE > 25% → model review; Adoption rate < 60% → planner experience review

---

### 7.7 AI Guardrails & Safety

#### Output Validation Guardrails

All LLM outputs validated against strict schemas before passing downstream. Validation failures trigger one retry; on second failure, graceful degradation.

| Validation Check | Rule | Action on Failure |
|-----------------|------|------------------|
| Scenario count | Exactly 3 scenarios | Retry with explicit instruction |
| Lift assumption range | `1.0 ≤ lift ≤ 6.0` | Reject and retry |
| Scenario differentiation | Max lift − min lift ≥ 0.5x | Retry with differentiation instruction |
| Service level range | `0.85 ≤ SL ≤ 1.0` | Reject and retry |
| Pre-stage quantity | Positive; not exceeding max_order_qty | Reject and retry |
| Narrative minimum length | ≥ 50 characters per scenario | Reject and retry |
| Feasibility consistency | `is_feasible: False` scenario must not be top recommendation | Correct deterministically |

#### Confidence-Based Escalation

| Confidence Score | Condition | System Behaviour |
|-----------------|-----------|-----------------|
| 0.7 – 1.0 | ≥ 3 similar historical events | Standard presentation, no warning |
| 0.4 – 0.69 | 1–2 similar events | Amber indicator: "Limited comparables — review carefully" |
| 0.1 – 0.39 | 0 comparables; category defaults used | Red LOW CONFIDENCE banner; acknowledgment checkbox required |
| < 0.1 | No data; agent failure | Scenarios not presented; auto-escalate to manual review task |

#### Human-in-the-Loop Guardrails (Non-Negotiable)

| Guardrail | Mechanism | Enforcement |
|-----------|-----------|-------------|
| No autonomous write-back | Write-back API requires valid `approved_by` token | Server-side — API returns 403 without token |
| Manager co-approval for high-value events | Revenue impact > configurable threshold requires manager | Approval workflow in API layer |
| Override audit | Non-recommended scenario selection requires reason (min 10 chars) | Required field in submission API |
| Double-submission prevention | Write-back checks existing policy before applying | Server-side before any DB write |
| Session timeout | Scenario selections expire after 4 hours | Token expiry enforced in API |

#### Prompt Injection Defense

- All string fields inserted into prompts stripped of `<`, `>`, newline characters, prompt-structural keywords
- Maximum field length enforced at insertion (deal name truncated to 200 chars)
- Sensitive fields replaced with opaque IDs before any LLM call
- No LLM-generated SQL — all DB queries written by engineers

#### Hallucination Prevention

| Risk | Mitigation |
|------|-----------|
| LLM inventing historical events | Post-generation check: any deal_id cited in narrative must exist in `demand_decomposition.historical_similar_events` |
| LLM generating financial figures | Financial Impact Agent is fully deterministic — LLM used only to format narrative around pre-computed figures |
| LLM generating supply constraints | Supply Constraint Agent is fully deterministic — LLM generates only plain-language summary |

#### Graceful Degradation

| Failure | System Response |
|---------|----------------|
| Single agent fails | Present partial results with clear flag; allow manual entry for missing parameter |
| All agents fail | "Automated generation unavailable. Enter scenarios manually using the form below." |
| LLM API unavailable | Retry with exponential backoff; fall back to deterministic scenarios with default lift multipliers |
| DB connection lost | Abort; notify planner; do not generate on stale data |
| Write-back API fails | Log failure; display parameters for manual entry; require planner re-confirmation before retry |

---

### 7.8 Non-Functional Requirements

**Performance**
- End-to-end scenario generation < **5 minutes** (event detection → scenarios ready)
- Supports up to **50 simultaneous active promotions** without degradation

**Reliability**
- Agent failure must not block planner workflow — fallback path always available
- Retry logic with exponential backoff on LLM API failures and DB connection errors
- Circuit breaker pattern prevents cascading failures

**Observability**
- All agent reasoning steps logged with timestamps in queryable trace store (LangSmith)
- All financial calculations traceable to source data
- Agent confidence scores surfaced in planner interface (not hidden in logs)
- Alerting: > 10 minutes generation time or > 5% agent error rate in rolling 24h window

**Security**
- No PII in LLM prompts — customer names replaced with anonymized IDs
- Audit trail for all policy changes retained minimum 3 years (SOX compliance — confirm with legal)
- LLM API keys managed via AWS Secrets Manager — never in code or config files

**Integration**
- Read-only connection to TenantDB — no agent writes directly to any DB table
- Policy write-back exclusively via existing approved Blue Ridge APIs
- No changes required to Blue Ridge data model or database schema
- Compatible with existing ECR-based deployment pipeline

**Cost Management**
- Expected LLM cost per scenario generation run: < $0.25
- Monthly budget cap in Anthropic console; alert at 80%, hard stop at 100%
- Cost anomaly alert: single run exceeding 3× expected token count
- Use Claude Haiku for low-reasoning steps (orchestrator, narration), Sonnet for scenario generation

---

## 8. Model Governance

### 8.1 Model Version Pinning

- LLM model version pinned to exact identifier (`claude-sonnet-4-6`) — never an alias
- Model version treated as a dependency: changes require PR, full eval run, engineering sign-off
- Anthropic deprecation notices monitored; 90-day migration window built into release calendar
- Any model version change triggers full eval suite as CI gate

### 8.2 Prompt Versioning

- All prompts stored in version-controlled files under `src/scenario_planning/prompts/` — not Python strings
- Semantic versioning: major = structural redesign, minor = significant wording change, patch = typo/clarity fix
- Active prompt version declared in `settings.py` and logged with every trace
- **Any prompt change requires full eval run before merging**
- Peer review: at least one domain SME (demand planning) and one engineer must approve

### 8.3 Drift Detection

| Signal | Detection Method | Threshold | Response |
|--------|-----------------|-----------|----------|
| Demand forecast drift | Rolling 30-day MAPE from online eval | MAPE > 25% | Schedule model/prompt review within 2 weeks |
| Financial accuracy drift | Rolling 30-day financial error | Error > 20% | Audit financial tool data sources |
| Input distribution shift | Monitor distribution of discount_pct, event duration, product_group | Statistically significant shift | Flag for eval dataset expansion |
| LLM behaviour drift | Monthly canary prompts with known expected outputs | Any canary fails | Immediate engineering investigation |
| Judge score drift | Rolling 30-day judge scores | Overall score < 3.8 | Re-calibrate judge; review scenario generator prompt |

### 8.4 Improvement Triggers

**Triggers:**
- Rolling MAPE > 25% for 2 consecutive months
- Planner adoption rate < 50% with output quality as root cause
- New product category or customer segment not in eval dataset
- Prompt regression: previously passing eval case fails without code change
- Post-event review reveals systematic bias

**Improvement cycle process:**
1. Root cause analysis: which agent and which input type is driving degradation
2. Update eval dataset with representative failure mode cases
3. Revise prompt or agent logic
4. Run full eval suite — improvement must be demonstrated before deploying
5. Shadow mode: deploy new version alongside current for 2 weeks
6. Switch traffic if shadow mode shows improvement

### 8.5 Governance Roles

| Role | Responsibility |
|------|---------------|
| PM | Owns eval threshold definitions and business acceptance criteria |
| Data Science | Owns prompt design, eval function implementation, judge calibration |
| Engineering | Owns CI/CD eval gates, online eval pipeline, drift detection infrastructure |
| Demand Planning SME | Reviews scenario quality; participates in judge calibration |
| IT / Security | Reviews security implications of prompt changes; conducts penetration tests |

---

## 9. Rollout Strategy

### 9.1 POC #1 → Production

| Phase | Audience | Duration | Purpose |
|-------|----------|----------|---------|
| **POC** | Dev team + 2 demand planners | 6 weeks | Validate core AI concept against 1 historical event |
| **Internal Pilot (Shadow Mode)** | Dev team monitoring only | 2–4 weeks | Run agents on live events; log outputs but don't show planners |
| **Controlled Beta** | 1–2 planners, lowest-value events | 4–6 weeks | First real planner interactions; collect feedback |
| **Expanded Beta** | All planners, one product category | 4–6 weeks | Validate at scale; enable approval workflow |
| **Production** | All planners, all qualifying events | Ongoing | Full deployment with monitoring and governance |

### 9.2 Exit Criteria

**POC → Internal Pilot**
- [ ] MAPE < 20% on moderate scenario across all eval cases
- [ ] Financial accuracy within ±15% for closest-to-actual scenario
- [ ] Scenario judge score ≥ 4.0 / 5.0 average
- [ ] End-to-end generation time < 5 minutes (p95)
- [ ] At least 2 planners have reviewed scenarios and rated realism ≥ 4/5
- [ ] All guardrails implemented and tested
- [ ] LangSmith tracing enabled and agent traces reviewed
- [ ] Security review complete (prompt injection, PII audit, secrets management)

**Internal Pilot → Controlled Beta**
- [ ] Shadow mode run for minimum 10 live promotional events without agent failures
- [ ] Agent failure rate < 5% across shadow mode runs
- [ ] No systematic biases identified in shadow mode output
- [ ] Planner interface implemented and UX signed off
- [ ] Approval workflow implemented and tested end-to-end
- [ ] Write-back to Blue Ridge tested in staging environment
- [ ] Rollback plan documented and tested

**Controlled Beta → Expanded Beta**
- [ ] At least 5 scenarios reviewed and selected by planners through the system
- [ ] Planner adoption rate ≥ 50% within beta cohort
- [ ] Zero unintended write-backs to Blue Ridge
- [ ] Post-event review completed for at least 2 full-cycle events
- [ ] Online eval pipeline operational
- [ ] Planner NPS ≥ 30 from beta feedback session

**Expanded Beta → Production**
- [ ] Rolling MAPE < 20% over 30-day window
- [ ] Planner adoption rate > 70% in expanded beta cohort
- [ ] No P0 or P1 incidents in previous 30 days
- [ ] All operational runbooks written and reviewed by on-call team
- [ ] Cost per run confirmed < $0.25
- [ ] Compliance sign-off: audit trail retention, data residency, SOX applicability

### 9.3 CASCI Platform Expansion (Post-Production)

After Scenario Planning is stable in production:

**Phase 2 — Platform Extraction (Weeks 1–8 post-production)**
- Extract shared agent templates, common MCP tool registry, and eval framework into `casci-platform/` module
- Build L3 (Episodic Memory): AuditDB schema for agent decision outcomes
- Build L4 (Profile Memory): tenant and user preference store
- Begin UC-04 (Anomaly Detection) design — lowest KG dependency

**Phase 3 — Knowledge Graph (Weeks 9–24 post-production)**
- Deploy Neo4j in AWS
- Build ETL pipeline: TenantDB → Neo4j for product/supplier/location/customer entity graph
- Wrap graph traversal queries as MCP tools
- Upgrade `get_product_substitutes()` tool in Scenario Planning to use KG
- Begin UC-02 (Supplier Risk Intelligence) — KG is the core dependency

**Phase 4 — Multi-Agent Use Cases (Post Phase 3)**
- UC-03 (Replenishment Optimization)
- UC-05 (Multi-Sourcing Scenario Planning)
- Agent Builder UI (admin interface for configuring agents without code changes)

### 9.4 Rollback Plan

The system is wrapped in a feature flag. Rollback at any phase:
1. Disable feature flag (immediate, no redeploy required)
2. Planners revert to manual spreadsheet process
3. No data migration required — write-back requires human approval, so no automated changes to undo
4. Notify planners: "AI scenario planning is temporarily unavailable."

Rollback must be executable in under 5 minutes by on-call engineer.

### 9.5 Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Planners don't trust AI scenarios | Medium | High | Shadow mode validation before beta; transparent confidence scores |
| LLM produces scenario causing costly stockout/overstock | Low | Very High | Human-in-the-loop mandatory; guardrails validate all outputs |
| Anthropic API outage during peak planning period | Low | Medium | Graceful degradation to deterministic scenarios; manual entry fallback |
| TenantDB schema change breaks agent tools | Medium | Medium | Contract tests in CI catch schema changes on next deploy |
| Data residency violation: demand data sent to Anthropic | Low | High | Legal review before launch; option to use Anthropic AWS Bedrock endpoint |
| Eval scores look good on historical data but fail on future (overfit) | Medium | Medium | Diverse eval dataset construction; online eval catches post-launch |
| KG ETL gets out of sync with TenantDB | Medium | Medium | Incremental sync with staleness detection; KG tools report data freshness |

---

## 10. Out of Scope

| Out-of-Scope Item | Rationale |
|-------------------|-----------|
| Multi-event overlapping scenario planning | Adds state complexity; single-event POC validates core logic first |
| Automatic trigger and execution without planner review | Hard requirement for POC; automation gates require trust built over production cycles |
| External competitive intelligence (social media, competitor pricing) | External data sourcing is a separate integration workstream |
| Mobile interface | Web interface sufficient for POC |
| ERP purchase order creation | PO creation involves ERP systems outside Blue Ridge scope |
| Real-time mid-event plan adjustment | In-flight replanning requires near-real-time data pipelines not yet in place |
| Knowledge Graph (Neo4j) | POC uses SQL for relationship queries; KG is Phase 3 |
| L3/L4 Memory Layers | Episodic and profile memory are Phase 2 |
| Agent Builder UI | Admin UI for no-code agent configuration is Phase 4 |

---

## 11. Open Questions

| # | Question | Owner | Priority | Status |
|---|----------|-------|----------|--------|
| 1 | What is the minimum qualifying lead time before an event for scenario generation? (14 days assumed) | PM | High | Open |
| 2 | Who approves scenario selection — planner alone, or manager sign-off? For events above what financial threshold? | Business | High | Open |
| 3 | How is "similar historical promotion" formally defined? Same product group + ±10% discount + same customer segment — confirm with Data Science | Data Science | High | Open |
| 4 | Does write-back to Blue Ridge require existing IT change management process or API-level permission? | IT | Medium | Open |
| 5 | What is the authoritative source for the promotional calendar? Pricing DB `deal` table assumed — confirm with Business | Business | Medium | Open |
| 6 | Should POC scenarios model single aggregated location or DC vs. store level? | Business | Medium | Open |
| 7 | What confidence threshold triggers human escalation vs. low-confidence scenario presentation? | PM | Low | Open |
| 8 | What is the financial threshold above which manager co-approval is required? | Business | High | Open |
| 9 | Does sending demand and cost data to Anthropic API violate data residency or contractual requirements? Use Bedrock? | Legal / IT | High | Open |
| 10 | What is the SOX applicability of inventory policy changes through this system? | Legal / Finance | Medium | Open |
| 11 | Who owns the eval dataset long-term? Who expands it when new categories are introduced? | Data Science / PM | Medium | Open |
| 12 | For CASCI platform expansion: what is the prioritization order for UC-02 through UC-06? | PM | Medium | Open |
| 13 | For KG ETL: full daily reload or incremental CDC? What is acceptable staleness for the graph? | Engineering | Medium | Open |
| 14 | Should the CASCI platform be a separate microservice or deployed within the existing Blue Ridge service boundary? | Engineering | High | Open |

---

## 12. POC #1 Delivery Plan

### Phase 0 — Setup (Week 1)

**Goal:** Establish ground-truth test case and development environment before building any agents.

- [ ] Identify one completed promotional event (last 12 months): clean `deal` record, complete demand history, measurable stockout or overstock outcome
- [ ] Extract `demand_history` and `event_prod_loc_cust_uplift` data snapshotted at `event_start - 14 days` (simulate forward-looking)
- [ ] Set up LangGraph project skeleton: state schema, graph definition stub, Claude API access
- [ ] Confirm database read access to TenantDB from development environment
- [ ] Define pass criteria: MAPE < 20%, financial accuracy ±15%, planner score ≥ 4/5
- [ ] Set up LangSmith project and confirm tracing works end-to-end

### Phase 1 — Core Agents (Weeks 2–3)

**Goal:** Build three agents that form the analytical core.

- [ ] **Demand Decomposition Agent:** Baseline demand, similar event lookup, Conservative/Moderate/Aggressive lift scenarios, post-promo dip, cannibalization candidates
- [ ] **Supply Constraint Agent:** Inventory position, lead time, MOQ, max order qty, storage capacity, fulfillability flag
- [ ] **Scenario Generator Agent:** Synthesize both agents into 3 meaningfully differentiated scenarios with structured JSON + narrative
- [ ] Unit test each agent against Phase 0 ground-truth data

### Phase 2 — Financial Layer (Week 4)

**Goal:** Add financial quantification and wire all agents under orchestration.

- [ ] **Financial Impact Agent:** Revenue, carrying cost, stockout cost per scenario; confidence intervals; ranked recommendation
- [ ] **Orchestrator Agent:** LangGraph graph with parallel execution of analysis agents; error handling and fallback
- [ ] End-to-end integration test: run full graph on ground-truth test case

### Phase 3 — Planner Review (Week 5)

**Goal:** Validate output quality with real planners.

- [ ] Build comparison output layer (human-readable markdown table or simple web view)
- [ ] Structured review session with 2 demand planners:
  - Present 3 scenarios without revealing actual outcome
  - Planner rates scenario realism (1–5) and indicates which they would have chosen
  - Reveal actual outcome; compare planner selections to actual demand realization
- [ ] Measure: financial projections within ±15% of actual historical outcome?
- [ ] Document gaps, failure modes, planner feedback

### Phase 4 — Iteration & Handoff (Week 6)

**Goal:** Incorporate feedback, document findings, prepare stakeholder demo.

- [ ] Incorporate top 3 planner feedback items into agent prompts or calculation logic
- [ ] Document all gaps identified during validation
- [ ] Draft CASCI Phase 2 roadmap based on POC learnings
- [ ] Prepare stakeholder demo: end-to-end walkthrough of ground-truth test case (before/after)
- [ ] Produce POC findings report: pass/fail against each criterion, lessons learned, CASCI expansion recommendation

---

*Document Status: v1.0 — CASCI Master PRD. Incorporates Scenario Planning POC #1 (v0.2) as the first CASCI use case. Adds CASCI platform vision, Autonomy Ladder, Six-Layer Memory System, and Use Case Roadmap.*
