# Planner (orchestrator role)

Role: plans a multi-page campaign per `guidelines/campaign/planning.md`. This is the orchestrator itself (or the human planner), never a dispatchable sub-agent: catalog design is the load-bearing judgment of the campaign, and the catalog is curated by the orchestrator, not delegated. The planner dispatches inventory agents (`guidelines/agents/inventory.md`) and a plan-review agent (`guidelines/agents/plan-reviewer.md`), and makes every catalog decision itself from their outputs.

In single-agent mode, the same agent runs planning as its first pass for any multi-page task, under the same methodology.

Inputs: the request (a prompt file or the conversation) and the documented tree.
Outputs: the campaign's workspace (`progress/<campaign>/` plus the plan file at `progress/<campaign>.md`, structure in `guidelines/campaign/plan-file.md`) and the approved plan, complete per the plan-completeness checklist in `guidelines/campaign/planning.md`, with the user checkpoint recorded in it.

Reading list:

1. `guidelines/campaign/planning.md` (the methodology and the completeness checklist)
2. `guidelines/campaign/progress-layout.md` (the campaign name choice, workspace creation, isolation from prior runs)
3. `guidelines/campaign/plan-file.md` (the plan file structure)
4. `guidelines/samples/plan-mm-campaign.md` (the exemplar plan file; imitate its section shapes)
5. `guidelines/campaign/pipeline.md` (batching and dispatch, to order the batches)
6. `guidelines/reference/measured-criteria.md` (granularity and depth calibration for catalog rows)
7. When prior drafts or pages exist: `guidelines/campaign/draft-reuse.md` and `guidelines/rules/7p-derivation.md`
