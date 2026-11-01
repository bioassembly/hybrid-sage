# High-Leverage Career & Engineering Playbooks

Your hardware + cloud fleet (**Local RTX 3090 running `Qwen 3.8 Flash Next` on Strata `:8080`** + **Google AI Pro `Gemini 3.8 Flash` & `Gemini 4 Argon` in Antigravity**) gives you an asymmetric advantage that <1% of engineers and bioinformaticians have: **zero-marginal-cost local throughput + frontier cloud reasoning + cross-family verification**.

Here are the 5 daily playbooks designed to multiply your research output, software quality, and career trajectory.

---

## Playbook 1: Zero-Window-Switching Cloud → Local Delegation (`sage local`)

You don't even have to leave your **Antigravity** session (`Gemini 3.8 Flash` or `Gemini 4 Argon`) to use your local RTX 3090 (`Qwen 3.8 Flash Next`). Because Antigravity has terminal tool access, you (or the agent itself) can delegate token-heavy tasks directly to Strata via `sage local`:

```bash
# 1. Generate unit tests locally for $0 cloud quota:
sage local -m test -f src/parser.py "Write comprehensive pytest unit tests covering edge cases" > tests/test_parser.py

# 2. Get an instant cross-family code review from Qwen 3.8 Flash Next on a git diff:
git diff | sage local -m review "Audit this diff for bugs, silent failures, and edge cases"

# 3. Inspect a private gel image, sequencing QC plot, or clinical PDF screenshot locally:
sage local --image results/qc_plot.png "Check this QC distribution for batch effects or adapter dimers"
```

**Why this upgrades your workflow**: You stay in a single interface while your local GPU absorbs 70–80% of the heavy token generation and provides an independent second opinion from a completely different model family (Alibaba Qwen vs. Google Gemini).

---

## Playbook 2: Top-1% Bioinformatics & Nextflow Pipeline Shipping

When building or troubleshooting production genomics pipelines (`metagenomics-tk-ont`, `pacbio_somatic_variant`, `complete_genome_profile`, `mitongs`):

1. **Architecture & Statistical Rigor (`Gemini 4 Argon`)**:
   - Use **Gemini 4 Argon** with `/red-team` (`skeptic`) and `first-principles-explainer` to validate statistical assumptions (e.g., rarefaction normalization, somatic allele frequency thresholds, ONT long-read chimera filtering).
   - Export the module specification to `NOTES.md`:
     ```bash
     sage handoff plan
     ```
2. **Stub-Run & `nf-test` Grinding (`Qwen 3.8 Flash Next` on Strata)**:
   - Delegate the Nextflow DSL2 module scaffolding, `nextflow_schema.json` parameter definitions, and `-stub-run` loop to your local workhorse:
     ```bash
     sage handoff exec
     ```
3. **FAIR Compliance & Public Release Polish (`Gemini 3.8 Flash`)**:
   - Use **Gemini 3.8 Flash** with `fair-data-principles` and `github-repo-best-practices` to add `CITATION.cff`, `CITATIONS.md`, Frictionless schemas, and a 30-second quickstart README so every internal pipeline you build can be published as a citable software artifact.

---

## Playbook 3: Privacy-Airgapped Clinical Reporting & LIMS Engineering

When working with hospital LIMS data, patient identifiers (NIK / MRN), or internal clinical Quarto reports (`_New_reporting`, `_Report_Automation`, `LIMS`):

1. **Hard Privacy Gate (`sage route`)**:
   - `sage route` automatically scans referenced files for `.vcf`, `.bam`, `.fastq`, `.env`, and 16-digit NIK patterns. Any sensitive file is **hard-locked** to `local-workhorse` (local OpenCode harness) and will **never** fail over to the cloud even if the local server is stopped.
2. **Sanitize Locally, Architect Globally**:
   - Have `Qwen 3.8 Flash Next` generate a synthetic/mock schema (`--mock`) from the real clinical table:
     ```bash
     sage local -f raw_clinical_sample.csv "Generate a 5-row synthetic mock CSV with identical column types and zero real patient data" > mock_sample.csv
     ```
   - Now you can safely pass `mock_sample.csv` to **Gemini 4 Argon** (`security-audit` / `statistical-data-visualization`) to design OWASP-hardened LIMS endpoints or publication-grade Quarto visualizations!

---

## Playbook 4: The "2-Strike" Debugging Accelerator

Never spend 2 hours fighting a subtle race condition, Nextflow channel deadlock, or C++/CUDA build issue on a single model:

- **Strike 1 & 2 (Local Workhorse)**: Let `Qwen 3.8 Flash Next` attempt up to 2 fast fixes against the failing test or compiler trace.
- **Immediate Escalation on Strike 2**:
  ```bash
  sage handoff review
  ```
  Switch to **Gemini 4 Argon (High Thinking)** (or invoke `/boost`). Because `NOTES.md` already captures the exact failing command and what `Qwen` tried twice, `Gemini 4 Argon` skips the obvious dead-ends and goes straight to the root cause.

---

## Playbook 5: Compounding Institutional & Personal Memory (`sage memory`)

Every architectural breakthrough, tricky bioconda dependency fix, or UGM HPC/network convention you solve is stored in `~/.config/opencode/memory.json` (shared between OpenCode and Antigravity).

```bash
# Search your accumulated engineering knowledge graph anytime:
sage memory search "Nextflow"
sage memory list

# Create an atomic, flock-protected backup before major upgrades:
sage memory backup
```

Over months, your local and cloud agents accumulate a permanent, searchable institutional memory of your entire engineering career.
