# Prompt Library & Engineering Suites

This directory contains all versioned prompt engineering suites developed for the **AI Lecture Notes to Smart Study Pack Generator** (Course: SCSE4041, Problem Pool: C2).

---

## Directory Structure

- [`v1/`](v1/): **Baseline Zero-Shot Suite** (6 prompts) – Direct instructions and target JSON shapes without persona framing or negative constraints.
- [`v2/`](v2/): **Role & Negative Constraints Suite** (6 prompts) – Persona framing (`"experienced university lecturer"`), explicit undergraduate audience, numbered negative rules, and standardized relation taxonomies.
- [`v3/`](v3/): **Grounded Few-Shot & Self-Checking Suite** (6 prompts) – Explicit grounding rules (G1–G5), contrastive few-shot worked examples (*Good vs. Bad*), anti-bias question drafting rules, and pre-response mental self-checklists.
- [`final/`](final/): **Final Production Suite** (6 prompts) – Deployed production prompts (derived from V3) used by the active study pack generation pipeline.

---

## Summary of Prompt Counts

| Metric | Count | Form Reference |
| :--- | :---: | :--- |
| **Number of Final Prompts** | **`6`** | Microsoft Form **Q10** |
| **Number of Prompt Versions** | **`3`** (`v1`, `v2`, `v3`) | Microsoft Form **Q18** |
| **Total Prompt Files** | **`24`** (`6` stages × `4` folders) | All 6 stages replicated across V1, V2, V3, and Final |
