# Fictional savings experiment: pre-analysis plan

**Status:** teaching example only; not an actual study registration. The plan is written before inspecting the generated group summaries to demonstrate the idea of pre-registration.

## Research question

Does seeing an AI-generated savings suggestion change the amount a participant chooses to save in a fictional task, compared with receiving no suggestion?

## Arms

- `control`: no advice shown.
- `human`: a fixed, fictional suggestion labelled as written by a person.
- `ai`: a fixed, fictional suggestion labelled as AI-generated.

The checked-in data are simulated, not collected from participants. Assignments are balanced and shuffled using a recorded random seed.

## Primary hypothesis and outcome

Primary comparison: the mean amount saved in the `ai` arm is greater than the mean in `control`.

Primary outcome: `saved_nok`, an integer from 0 to 1000 in the fictional task.

## Pre-specified exclusions

Only consented, eligible participants can be randomized or included. Exclude a row from the primary analysis if any condition below is true:

1. `consent` is not `yes`.
2. `eligible` is not `yes`.
3. `attention` is `fail`.
4. `seconds` is less than 120.

The conditions can overlap. The analysis report therefore says exclusion-reason counts may overlap.

## Analysis

Report the number of included observations and mean `saved_nok` in each arm. Estimate `human - control` and `ai - control` differences. In a linear regression with `control` as the reference category and two arm indicators, these point estimates equal the corresponding mean differences.

This compact demo does not calculate standard errors, confidence intervals, or p-values. It does not support conclusions about real participants.

### Amendment 1 (3 October 2026): add 95% confidence intervals

The original plan above reported point estimates only. This amendment adds, for `human - control` and `ai - control`, the OLS standard error and a 95% confidence interval from the same linear regression: residual variance pooled over the three arms, N - 3 degrees of freedom, and a t critical value. The hypothesis, outcome, exclusions, and point estimates are unchanged, and no p-values are added.

The original text is kept rather than edited, so the change stays visible. In a real study, an amendment like this should be dated and registered before the outcome data are inspected, or reported in the paper as a deviation from the plan.

## Reproducibility

- Keep the raw synthetic CSV unchanged; its SHA-256 checksum is in `data/raw/manifest.json`.
- Store cleaning rules in `src/research_demo/experiment.py` and run outputs in `data/processed/`.
- Store the variable definitions in `data/codebook.csv`.
- Record the code version and random seed when generating a new synthetic fixture.
