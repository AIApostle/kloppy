# Kloppy Product Requirements Document

## Product Summary

Kloppy is an AI Marketing Officer for businesses that need to understand
their audience, develop a marketing strategy, create a complete campaign,
coordinate execution, and learn from performance in one workspace.

Kloppy should connect work that is normally fragmented across market research,
strategy, copywriting, graphic design, presentation creation, publishing, and
analytics. It should produce useful campaign deliverables without requiring
the business owner to act as the project manager between separate tools.

## Problem

Businesses often lack the budget or expertise to hire marketing strategists,
designers, copywriters, and campaign managers. Existing AI tools can generate
individual pieces of content, but they do not reliably connect audience
evidence, campaign strategy, consistent creative production, distribution,
approval, and measurement.

As a result, campaigns are frequently:

- Built on assumptions rather than evidence.
- Inconsistent across graphics, copy, slides, landing pages, and social posts.
- Difficult to launch because assets and publishing workflows are disconnected.
- Difficult to evaluate because performance data is not connected back to the
  original strategy and creative decisions.

## Target Users

The primary user is a business owner, founder, or small marketing team that
needs to launch and improve campaigns without a full in-house marketing
department.

The user may provide:

- Product or service details and value proposition.
- Business goals such as awareness, leads, or sales.
- Target location, market, and price range.
- Brand identity, existing assets, tone of voice, and guidelines.
- Budget, campaign duration, constraints, and approval requirements.

Kloppy should ask focused follow-up questions when essential information is
missing rather than silently inventing business facts.

## Product Vision

Kloppy should take a business from a grounded brief to an approved,
coherent, and measurable marketing campaign:

1. Understand the business and campaign goal.
2. Develop audience hypotheses using available evidence.
3. Produce an evidence-linked marketing strategy.
4. Generate a coordinated campaign pack across formats.
5. Prepare or execute approved campaign actions through connected platforms.
6. Measure results and recommend the next optimization.

## MVP Goals and Non-Goals

### Goals

- Make Qloo-powered audience intelligence visibly influence the marketing
  plan.
- Turn a product brief into a clear, actionable campaign plan.
- Generate campaign messaging and creative directions for distinct audiences.
- Enable a real or clearly labelled demo-mode ad-execution workflow through
  one initial platform.
- Track campaign metrics or representative demo results and use them to
  suggest next actions.
- Show the chain from insight to action to feedback in a judge-friendly demo.

### Non-Goals

- Replacing every marketing role with fully autonomous automation.
- Supporting every advertising network and marketing channel in the MVP.
- Training a proprietary foundation model.
- Claiming Qloo predicts purchases.
- Allowing unrestricted spending or publication without authorization.
- Building a complete CRM, ecommerce platform, or enterprise marketing data
  warehouse.
- Guaranteeing revenue, conversions, or a specific marketing outcome.

## Core Requirements

### 1. Business and campaign brief

Users must be able to create a business profile and campaign brief containing
business, audience, brand, budget, timeline, channel, and constraint
information. The brief must be retained as campaign context and reusable
brand memory.

### 2. Audience intelligence

Kloppy should support Qloo as an audience-intelligence integration when
credentials and access are available. Qloo outputs should be presented as
cultural-affinity signals and audience hypotheses, not as proof of purchase
intent or guaranteed audience membership.

Audience insights should retain their source and influence on downstream
strategy or creative decisions.

### 3. Marketing strategy

Kloppy must generate a reviewable campaign strategy containing:

- Audience hypotheses and supporting evidence.
- Positioning and value proposition.
- Campaign concept and core message.
- Content themes and calls to action.
- Recommended channels.
- Proposed budget allocation and publishing schedule.
- Success metrics and testing strategy.

The user must be able to revise and approve the strategy before creative
production begins.

### 4. Complete campaign production

After strategy approval, Kloppy should coordinate a campaign pack that can
include:

- Advertising graphics, banners, flyers, and platform-specific variations.
- Social posts, carousels, captions, stories, and content calendars.
- Presentation or pitch-deck content.
- Landing-page copy and supporting content.
- Email campaign content.
- Ad headlines, descriptions, product descriptions, and creative briefs.

All outputs must inherit the approved campaign strategy, brand guidelines,
audience insights, and visual identity. The system should support multiple
creative variations for testing different messages, formats, and calls to
action.

Where the connected service permits it, assets should be exportable or
editable rather than preview-only.

### 5. Campaign execution

Kloppy should support approval-gated execution through connected publishing,
advertising, email, or landing-page platforms. The initial implementation
should target one execution platform rather than attempting to integrate
every channel.

The interface must clearly distinguish:

- Generated asset.
- Approved asset.
- Scheduled campaign.
- Successfully published campaign or advertisement.
- Simulated or demonstration action.

Publishing, spending, and material campaign changes must require explicit user
authorization.

### 6. Measurement and optimization

Where analytics integrations are available, Kloppy should collect metrics such
as impressions, clicks, conversions, spend, cost per acquisition, and return
on ad spend.

Kloppy should compare creative and message variations, explain observed
performance, and recommend changes. Automatic adjustments must be limited by
user-defined authorization and predefined safety or budget boundaries.

### 7. Audience segment recommendations

Kloppy must return a manageable shortlist of distinct audience segments
rather than an unranked list of interests. Each segment should include a
description, rationale, relevant signals, likely message angle, uncertainties,
and a suggested test. Users must be able to select a segment or request a
revised shortlist.

Kloppy must not fabricate audience sizes, unsupported demographic precision, or
individual-level audience attributes.

### 8. Research provenance and uncertainty

Recommendations must identify whether they are based on Qloo, user-provided
facts, campaign metrics, approved external research, or model-generated
hypotheses. Missing evidence and uncertainty must be visible. The system must
not invent citations, API results, metrics, or audience attributes.

### 9. Campaign history and audit trail

The campaign workspace must record important decisions, approvals, tool
actions, timestamps, execution status, and available results. Users must be
able to distinguish proposed, approved, executing, completed, failed, and
simulated actions. Retries must be visible and should not create duplicate
campaigns without a deliberate recovery decision.

### 10. Brand and business memory

Approved brand voice, product facts, prohibited claims, and campaign learnings
should be reviewable and editable. Uncertain inferences must not silently
become permanent business facts. Users must be able to remove stored
information and understand what Kloppy retains.

## Integration Principles

Kloppy should orchestrate specialist services instead of attempting to rebuild
every creative capability internally:

- LLM provider for reasoning, copy, and strategy.
- Qloo for cultural-affinity intelligence.
- Image-generation or design-platform service for graphics.
- Presentation-generation service for slides and decks.
- One publishing or advertising platform for initial execution.
- Connected analytics and conversion events for measurement.
- Database and object storage for profiles, campaign state, assets, and history.

Each integration remains subject to API availability, credentials, pricing,
quality, licensing, data handling, and export constraints.

## Resource Connections and Access

Kloppy should provide a central connection area where a business owner can
connect, inspect, test, and disconnect services. Each connection should show
its status, account or workspace, granted permissions, and last successful
check.

Connections may include:

- Qloo and approved research sources.
- The selected MVP advertising or publishing platform.
- Creative and content generation or storage services.
- Product pages, landing pages, conversion events, catalogs, and analytics.

Credentials and tokens must remain in secure server-side storage and must
never appear in the browser, generated content, logs, or source control.
Connections should request least-privilege scopes and support revocation.
Missing, expired, or insufficient access must be shown explicitly, along with
the affected feature.

## Agent Behavior and Tool Boundaries

| Action | Default policy |
| --- | --- |
| Read briefs, query approved research APIs, summarize metrics | May run automatically within configured permissions |
| Draft strategy, copy, creative directions, and campaign configuration | May run automatically; user can edit |
| Create an advertising-platform draft | Requires a connected account and explicit draft permission |
| Publish ads, materially change targeting, or increase spend | Requires explicit approval unless narrowly pre-authorized |
| Increase budget beyond a cap or change account permissions | Blocked; requires user action or is out of scope |
| Retry failed actions | Must be idempotent where possible and visible to the user |

## Core Screens

The MVP should include:

- **Workspace / campaign home:** campaign list, activity, objectives,
  statuses, and start-campaign action.
- **Product brief:** product facts, objectives, geography, budget, timing, and
  brand guidance.
- **Audience intelligence:** Qloo signals, candidate segments, rationales,
  source labels, and uncertainties.
- **Strategy workspace:** positioning, message pillars, channels, timeline,
  budget, and success metrics.
- **Creative studio:** audience-specific variations, editing, preview, and
  approval status.
- **Campaign review and launch:** platform account, configuration, assets,
  spend ceiling, schedule, destination, warnings, and explicit approval.
- **Performance and optimization:** metrics, objective progress, evidence-based
  observations, recommendations, and approval controls.
- **Activity / audit log:** research summaries, approvals, tool outcomes,
  errors, and campaign changes.

## Initial Scope and Success Criteria

The first complete workflow should demonstrate one realistic campaign from
brief to measurable or clearly simulated execution:

1. Capture a campaign for a real business scenario.
2. Generate Qloo-informed audience hypotheses.
3. Show how the evidence changes strategy decisions.
4. Approve a strategy.
5. Generate a coherent campaign pack containing copy, graphics, variations,
   and a presentation or campaign brief.
6. Prepare one execution path, using a labelled simulation if live access is
   unavailable.
7. Import or simulate performance data and produce an optimization
   recommendation without misrepresenting simulated results as real outcomes.

## Functional Acceptance Criteria

The MVP is complete when:

- A user can save and resume a product brief with required validation.
- The interface distinguishes user-provided facts from AI assumptions.
- Supported Qloo requests return source-linked insights or an explicit
  limitation when results are empty, invalid, or unavailable.
- The system produces distinct audience segments with rationale and
  uncertainty.
- The strategy connects recommendations to audience evidence and business
  constraints.
- At least two meaningfully different creative/message variations are
  generated, edited, and approved before execution.
- One advertising or publishing platform is supported, or the fallback is
  clearly labelled as demo mode.
- Execution shows account, objective, audience, creative, destination,
  schedule, and maximum spend before approval.
- Unavailable metrics are marked unavailable rather than treated as zero.
- Optimization recommendations explain observations, uncertainty, and next
  actions without overstating causation.
- The audit trail records approvals, tool actions, outcomes, and retries.

## Non-Goals for the First Release

- Integrating every social, advertising, email, and analytics platform.
- Building a full graphic-design editor, slide editor, or video editor.
- Claiming that audience-affinity data proves purchase intent.
- Publishing or spending money without explicit authorization.
- Presenting mocked or simulated campaign results as live performance.

## Technical Context

The current project uses a React/Vite frontend and a Python 3.11 FastAPI
backend. The backend already includes HTTP, validation, settings, Supabase,
and ASGI dependencies suitable for the first integration layer.

The implementation should introduce explicit workflow states, typed request
and response models, server-side secrets, permission checks, audit events, and
object-storage references for generated assets.

## Non-Functional Requirements

- **Reliability:** show loading, success, partial-success, and failure states
  for long-running research and campaign operations.
- **Security:** keep API keys and advertising credentials server-side and
  exclude secrets from logs, prompts, generated assets, and source control.
- **Privacy:** collect only information required for the product experience and
  do not infer or target sensitive personal traits.
- **Transparency:** distinguish sourced evidence, AI hypotheses, simulated
  data, and confirmed platform actions.
- **Recoverability:** preserve drafts and completed work if a later workflow
  step fails.
- **Usability:** a first-time user can reach a reviewable plan without
  understanding Qloo's API.
- **Responsiveness:** show progress for research and generation jobs.
- **Accessibility:** provide readable contrast, keyboard-accessible controls,
  and meaningful labels for status and actions.

## MVP Success Metrics

- A user completes the product brief → Qloo insight → segment → strategy →
  creative → approved execution/demo → feedback journey.
- At least one Qloo-derived signal visibly supports or changes an audience
  recommendation and its message.
- The strategy specifies a segment, creative direction, channel, budget cap,
  and measurable objective.
- At least one campaign operation is performed through a connected platform,
  or the fallback is clearly simulated.
- No spend or publication occurs outside configured authorization.
- Actual or clearly labelled demo metrics produce a concrete optimization
  recommendation.
- A reviewer can understand the path from cultural insight to marketing action
  and observed result without verbal explanation of every transition.

## Product Principles

1. **Evidence before confidence:** distinguish facts, hypotheses, and
   recommendations.
2. **One campaign context:** strategy and assets must stay connected.

## Source and MVP Context

This PRD incorporates the requirements in `Kloppy_PRD.docx`, version 1.0,
prepared for the Qloo Agentic Hackathon. The primary integration is the Qloo
taste and cultural-intelligence API. The MVP is a standalone web application
demonstrating one end-to-end campaign workflow with measurable or clearly
labelled demo feedback.

Marketing starts with understanding people. Kloppy combines cultural and
taste intelligence with business context, then turns those insights into
marketing decisions, campaign actions, and measurable learning.
3. **Approval before action:** generation can be automated; publishing and
   spending require authorization.
4. **Honest system state:** live, pending, failed, and simulated actions must
   be visibly different.
5. **Orchestrate, do not overbuild:** use specialist services where they
   provide better quality or capability.

## MVP Prioritization

### P0 — Must build

Product brief, Qloo integration, audience insights, segment selection,
campaign strategy, two creative variations, one ad-platform workflow,
approval gate, performance display, optimization recommendation, audit trail,
and demo mode.

### P1 — Build if time permits

Persistent brand memory, multiple campaigns, richer external research,
additional creative formats, a second channel, and more sophisticated
experiment comparisons.

### Future or out of scope

Multi-channel orchestration across every platform, enterprise permissions,
full CRM, automated sales operations, autonomous budget expansion, and a
custom foundation model.

## Risks and Mitigations

- **Weak Qloo signals:** show relevance and uncertainty, combine signals with
  product context, and let users revise research questions.
- **Affinity mistaken for purchase intent:** label insights as hypotheses and
  validate them with campaign outcomes or additional customer evidence.
- **Delayed ad API access:** validate access early and maintain a clearly
  separated demo mode.
- **Creative inconsistency:** pass versioned strategy and brand constraints
  into every generation job.
- **Unauthorized action:** enforce explicit approvals, permission scopes, and
  budget limits.
