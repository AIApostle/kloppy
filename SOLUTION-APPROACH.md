# Kloppy Solution Approach

## Recommendation

This is a strong fit for Kloppy. The differentiator is not another isolated
copy or image generator; it is the coordination layer that turns business
understanding and audience evidence into a complete, consistent, reviewable
campaign.

The recommended architecture is an AI-orchestrated workflow with explicit
states and specialist integrations. Kloppy should own the campaign context,
decision history, approvals, asset relationships, and execution status while
delegating specialist production capabilities to appropriate services.

## End-to-End Workflow

### 1. Understand the business

Create a business profile and campaign brief covering the product or service,
value proposition, objective, target market and location, brand identity,
existing assets, tone, budget, duration, restrictions, and approval rules.

The intake workflow should ask follow-up questions only when information is
essential to produce a safe and useful recommendation.

### 2. Understand the audience with Qloo

Use the Qloo API to explore relevant taste, cultural, and affinity signals.
Combine those signals with user-provided customer data, approved market
research, and campaign history.

Qloo should inform hypotheses and creative directions. It must not be
represented as proof of purchase intent or as a guarantee that a person
belongs to a segment.

Store source references and a short explanation of how each insight affects
the campaign.

### 3. Develop the strategy

An AI strategy workflow converts the brief and evidence into:

- Audience hypotheses and evidence.
- Positioning and value proposition.
- Campaign concept and core message.
- Content themes and calls to action.
- Recommended channels.
- Budget allocation and publishing schedule.
- KPIs, testing plan, and success criteria.

Use a state transition such as `strategy_draft -> strategy_review ->
strategy_approved`. Creative production should require `strategy_approved`.

### 4. Produce the campaign pack

Once the strategy is approved, create a campaign pack containing the required
combination of:

- Ad graphics and platform-specific variants.
- Social posts, carousels, captions, stories, and content calendar.
- Presentation or pitch deck.
- Landing-page copy, email content, ad copy, and creative briefs.

Every asset should reference the campaign, strategy version, brand profile,
audience evidence, and creative variation. This enables consistency,
regeneration, comparison, and auditability.

Use specialist services for image generation, design-platform output, slide
creation, and video rather than implementing each editor inside Kloppy.
Prefer editable or exportable formats when the provider supports them.

### 5. Review and execute

Introduce an approval workspace where the user can review the strategy, each
asset, variations, budget, and intended action.

Execution should use explicit states:

`draft -> approved -> scheduled -> published`

with separate `simulated` and `failed` outcomes. Publishing and spending
actions must be authorization-gated, idempotent where possible, and recorded
in an audit log.

For the first release, integrate one suitable advertising or publishing
platform. If credentials or permissions are unavailable, provide a clearly
labelled simulation that demonstrates the workflow without claiming a live
result.

### 6. Measure and optimize

Import available metrics such as impressions, clicks, conversions, spend,
cost per acquisition, and return on ad spend. Associate measurements with
creative variations and strategy decisions.

The optimization workflow should explain which message or asset performed
better, propose a bounded change, and request authorization before applying
any live budget or campaign change.

## Proposed Architecture

### Frontend

Continue with the existing React/Vite workspace. Add campaign-oriented views:

- Business and brand profile.
- Campaign brief and intake questions.
- Audience evidence and Qloo insights.
- Strategy editor and approval.
- Campaign asset studio and variation review.
- Presentation and export view.
- Execution approval and status.
- Performance and optimization view.

### Backend

Continue with Python 3.11 and FastAPI. Keep the application entry point at
`backend/main.py`; use `backend/src/` for supporting scripts and modules,
not as a package root. Organize the backend around typed
domain services rather than provider-specific logic in route handlers:

- `briefs`: business and campaign intake.
- `audience`: Qloo and research adapters.
- `strategy`: evidence-linked strategy generation.
- `creative`: provider-neutral asset jobs and outputs.
- `campaigns`: workflow state and versioning.
- `execution`: publishing and advertising adapters.
- `analytics`: metric ingestion and normalization.
- `approvals`: authorization and audit events.

Use Pydantic models for external inputs, provider responses, workflow
commands, and persisted records. Keep credentials server-side and load them
through settings.

### Data and storage

Persist:

- Business profiles and brand memory.
- Campaign briefs and strategy versions.
- Audience insights with source and confidence metadata.
- Asset metadata, provider job IDs, file paths, and variation IDs.
- Approval decisions and audit events.
- Execution status and external platform IDs.
- Normalized performance metrics.

Store binary assets in object storage and retain metadata plus references in
the database. Supabase is a candidate for database, authentication, and
storage, subject to the final security and access design.

### Provider adapters

Define interfaces that hide provider-specific APIs:

- `AudienceProvider`
- `TextStrategyProvider`
- `ImageAssetProvider`
- `PresentationProvider`
- `PublishingProvider`
- `AnalyticsProvider`

Each adapter should report capability, status, errors, cost metadata where
available, and whether an output is editable, exportable, live, or simulated.

## Delivery Plan

### Phase 1: Intelligence and strategy

Build business/campaign intake, Qloo adapter, evidence-linked audience
insights, strategy generation, strategy review, and strategy approval.

### Phase 2: Creative production

Build campaign-pack orchestration, brand consistency context, copy outputs,
graphics, creative variations, social content, and one presentation or
campaign brief output.

### Phase 3: Execution

Choose one publishing or advertising integration based on API access,
credentials, licensing, and hackathon feasibility. Implement approvals,
idempotency, status tracking, audit logs, and a clearly labelled simulation
fallback.

### Phase 4: Measurement and optimization

Import available platform metrics, associate them with variations, compare
performance, and generate bounded optimization recommendations.

## First Demonstrable Slice

Use one realistic scenario, such as launching a product in Lagos:

1. Capture the business and launch brief.
2. Query Qloo for relevant cultural affinities.
3. Show the evidence-linked audience hypotheses.
4. Generate and approve a campaign strategy.
5. Produce consistent graphics, social content, ad copy, and a presentation.
6. Prepare one publishing action or run a labelled simulation.
7. Display imported or simulated metrics and a next-step recommendation.

The strongest proof is that Qloo intelligence visibly changes the strategy,
that the strategy produces real campaign deliverables, and that the system
honestly distinguishes live execution from simulation.

## Risks and Controls

- **Provider availability:** validate API access, rate limits, pricing, and
  licensing before committing to an integration.
- **Creative inconsistency:** pass a versioned campaign context and brand
  constraints into every generation job.
- **Unsupported claims:** label audience outputs as hypotheses and preserve
  evidence references.
- **Unauthorized actions:** require explicit approval for publication,
  spending, and material campaign changes.
- **Unclear status:** expose generated, approved, scheduled, published,
  failed, and simulated states separately.
- **Cost overruns:** show estimated provider cost where possible and enforce
  budget limits before jobs or execution actions.
- **Data and secrets:** keep provider credentials server-side, restrict access,
  and record security-relevant actions in audit logs.

## Expected Outcome

Kloppy should reduce the fragmentation between marketing research, strategy,
creative design, campaign management, and optimization. The long-term product
is an AI Marketing Officer that understands a business, develops its
marketing direction, creates the campaign materials, coordinates execution,
and learns from results.
