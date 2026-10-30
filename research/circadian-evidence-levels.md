# Circadian evidence: expression scores, cell perturbation and clinical timing

**Selected evidence comparison — not a research article**

[Canonical comparison](https://drgezhang.com/research/circadian-evidence-levels.html)

## What do these circadian studies measure, how are they evaluated, and which clinical claims do they not establish?

A selective comparison of three works in this author-maintained collection, using unchanged reviewed study profiles, answers and evidence boundaries. This is not a systematic review, a new study, a pooled effect estimate or a clinical dosing recommendation.

Compare the research tasks and validation units, not the sizes of unrelated metrics. Do not add cells, tissue samples, repeated expression samples or bibliography entries into a combined participant total. A publication and its author evidence page represent the same work, not independent evidence.

## Coronary expression subtyping

### Molecular subtypes of ischemic heart disease based on circadian rhythm

[Author evidence page](https://drgezhang.com/papers/circadian-ihd.html) · [Formal publication DOI](https://doi.org/10.1038/s41598-024-65236-5) · [BibTeX](https://drgezhang.com/citations/circadian-ihd.bib) · [RIS](https://drgezhang.com/citations/circadian-ihd.ris) · [CSL JSON](https://drgezhang.com/citations/circadian-ihd.csl.json)

### Reviewed study profile

- **profile type:**
  multicohort_omics
- **study design:**
  Retrospective public single-cell and bulk transcriptomic analysis
- **evidence type:**
  Expression-based subtyping, computational annotation and external template evaluation
- **population:**
  Public coronary-disease-related samples and separately analyzed reference datasets
- **primary endpoint:**
  Expression-defined CRDscore and molecular subtype structure
- **secondary endpoint:**
  External subtype assignment and associated immune/functional annotations
- **data modalities:**
  - single-cell RNA sequencing
  - bulk expression arrays
  - co-expression networks
  - NTP
  - computational enrichment and cell-type estimates
- **external validation:**
  true
- **scale metrics:**
  - - **label:**
      GSE184073 analyzed samples
    - **value:**
      2 samples
  - - **label:**
      GSE184073 post-QC cells
    - **value:**
      2,237 cells
  - - **label:**
      GSE59867 expression samples
    - **value:**
      436 samples, not 436 independent patients
  - - **label:**
      GSE59867 original design
    - **value:**
      Repeated follow-up of 111 STEMI patients and 46 stable CAD controls
  - - **label:**
      GSE20680 article-reported samples
    - **value:**
      195
  - - **label:**
      GSE20681 article-reported samples
    - **value:**
      198
  - - **label:**
      GSE43292 article-reported samples
    - **value:**
      64
  - - **label:**
      GSE62646 article-reported samples
    - **value:**
      98
- **counting note:**
  GSE184073 cells are not independent patients. GSE59867 contains repeated follow-up of 111 STEMI patients and 46 stable CAD controls; its 436 expression samples are not 436 independent patients. Follow-up represents post-infarction recovery time points, not 24-hour circadian monitoring of the same individual. External dataset counts are article-reported samples and are not summed into a deduplicated participant total. External validation means retrospective expression-template evaluation, not prospective clinical utility. GSE70049 is a Danio rerio setb morphant expression experiment, not a verified mouse circadian perturbation.

### What does CRDscore measure, and what does it not directly measure?

CRDscore was constructed as a research score from target-gene expression and a random background. Formula: CRDscore = Srandom - SCADCRgenes; Random features: 1,000; Single-cell cutoff: 75th percentile; Bulk cutoff: Median. The score does not directly measure an individual's circadian phase, amplitude or period. The two data-layer cutoffs are not one clinical threshold.

[Unchanged reviewed answer](https://drgezhang.com/papers/circadian-ihd.html#qa-2)

- [KF2](https://drgezhang.com/papers/circadian-ihd.html#kf2) — Methods: Calculation of CRDscore based on circadian-related genes

### What kind of external validation was performed?

NTP was used to evaluate subtype assignment in four external expression datasets. Datasets: GSE20680; GSE20681; GSE43292; GSE62646. External expression-template reproducibility is not prospective risk prediction or demonstrated clinical utility.

[Unchanged reviewed answer](https://drgezhang.com/papers/circadian-ihd.html#qa-5)

- [KF5](https://drgezhang.com/papers/circadian-ihd.html#kf5) — Methods: Construction and validation of the CRD-related subtypes of CAD; Fig. 4

### Do subtype-associated immune patterns establish treatment benefit?

Type2 showed higher CRDscore and immune-inflammatory expression characteristics. Contractile markers: Lower expression; Immune and collagen pathways: Associated enrichment differences. Computational estimates and expression associations do not establish causal plaque transitions or benefit from immunotherapy or chronotherapy.

[Unchanged reviewed answer](https://drgezhang.com/papers/circadian-ihd.html#qa-6)

- [KF6](https://drgezhang.com/papers/circadian-ihd.html#kf6) — Results: functional and immune microenvironment analyses; Figs. 5-6

### Complete reviewed evidence scope

- **supports:**
  - The analysis of GSE184073 constructed a single-cell co-expression foundation related to coronary disease.
  - CRDscore was constructed as a research score from target-gene expression and a random background.
  - The article reports external reference-data evaluation, but the use of GSE70049 requires qualification.
  - Expression-based subtyping of GSE59867 yielded four groups.
  - NTP was used to evaluate subtype assignment in four external expression datasets.
  - Type2 showed higher CRDscore and immune-inflammatory expression characteristics.
- **does not establish:**
  - Direct measurement of physiological circadian phase, amplitude or period.
  - A discovery cohort of 436 independent patients.
  - Verification that all cited reference experiments are mouse circadian interventions.
  - Prospectively validated clinical risk prediction or clinical utility.
  - Benefit from treatment or chronotherapy.
  - An independently verified mortality hazard ratio, AUC or clinical cutoff; adverse-prognosis wording is not a verified all-cause mortality model.

### Complete reviewed limitations

- GSE184073 cells are not independent patients. GSE59867 contains repeated follow-up of 111 STEMI patients and 46 stable CAD controls; its 436 expression samples are not 436 independent patients. Follow-up represents post-infarction recovery time points, not 24-hour circadian monitoring of the same individual. External dataset counts are article-reported samples and are not summed into a deduplicated participant total. External validation means retrospective expression-template evaluation, not prospective clinical utility. GSE70049 is a Danio rerio setb morphant expression experiment, not a verified mouse circadian perturbation.
- Cells are not independent patients; two analyzed samples do not establish population-level robustness.
- The score does not directly measure an individual's circadian phase, amplitude or period. The two data-layer cutoffs are not one clinical threshold.
- The evidence does not establish that all four reference experiments are verified mouse circadian interventions. No intended replacement accession is inferred.
- These are expression-sample groups, not 436 independent patients. The grouping does not resolve independence of repeated follow-up samples or outcome analyses.
- External expression-template reproducibility is not prospective risk prediction or demonstrated clinical utility.
- Computational estimates and expression associations do not establish causal plaque transitions or benefit from immunotherapy or chronotherapy.
- Direct measurement of physiological circadian phase, amplitude or period.
- A discovery cohort of 436 independent patients.
- Verification that all cited reference experiments are mouse circadian interventions.
- Prospectively validated clinical risk prediction or clinical utility.
- Benefit from treatment or chronotherapy.
- An independently verified mortality hazard ratio, AUC or clinical cutoff; adverse-prognosis wording is not a verified all-cause mortality model.

## Colorectal expression scoring and cell perturbation

### System biology analysis reveals circadian rhythm disorder associated with development and progression in colorectal cancer

[Author evidence page](https://drgezhang.com/papers/doi-10-1038-s41698-026-01699-1.html) · [Formal publication DOI](https://doi.org/10.1038/s41698-026-01699-1) · [BibTeX](https://drgezhang.com/citations/doi-10-1038-s41698-026-01699-1.bib) · [RIS](https://drgezhang.com/citations/doi-10-1038-s41698-026-01699-1.ris) · [CSL JSON](https://drgezhang.com/citations/doi-10-1038-s41698-026-01699-1.csl.json)

### Reviewed study profile

- **profile type:**
  multicohort_omics
- **study design:**
  Multicohort systems-biology study integrating public bulk transcriptomics, microarrays, single-cell RNA sequencing, cross-species circadian perturbation datasets, gene-regulatory-network analysis, and in-vitro CRC-cell perturbation experiments
- **evidence type:**
  Public transcriptomic and single-cell cohort analysis, expression-matched circadian scoring, cross-species rhythmicity evaluation, survival and clinical-association analysis, single-cell cell-state and ligand-receptor analysis, gene-regulatory-network analysis, and in-vitro functional perturbation
- **population:**
  Public human colorectal-cancer and normal-mucosal datasets, public human/mouse/non-human-primate circadian time-series and perturbation datasets, and HCT116/SW480 colorectal-cancer cell models
- **primary endpoint:**
  Development and multicohort evaluation of ClockProCRC as a transcriptomic measure of endogenous circadian misalignment
- **secondary endpoint:**
  Association of ClockProCRC with CRC progression, survival and tumor-microenvironment states, plus prioritization and functional testing of SYNE1 as a circadian-associated CRC regulator
- **data modalities:**
  - single-cell RNA sequencing
  - bulk RNA sequencing
  - microarray expression profiling
  - cross-species circadian time-series transcriptomics
  - gene-regulatory-network analysis
  - CRC-cell perturbation RNA sequencing
  - qRT-PCR
  - Transwell and wound-healing assays
  - colony-formation assays
  - Western blotting
- **external validation:**
  true
- **scale metrics:**
  - - **label:**
      article-reported aggregate
    - **value:**
      3,758 samples across 35 public GEO datasets
  - - **label:**
      abstract-reported additional cohort layer
    - **value:**
      3,733 samples from 34 additional public bulk RNA, microarray and single-cell cohorts, alongside the 25-sample primary single-cell cohort
  - - **label:**
      primary CRC single-cell cohort
    - **value:**
      GSE166555; 25 tissue samples: 13 CRC and 12 normal mucosal samples
  - - **label:**
      post-QC single cells
    - **value:**
      94,683
  - - **label:**
      single-cell structure
    - **value:**
      19 clusters and 9 major cell types
  - - **label:**
      initial colon circadian reference
    - **value:**
      906 genes; maSigPro-derived temporal genes with FDR <0.01 and goodness-of-fit R² ≥0.7
  - - **label:**
      circadian co-expression network
    - **value:**
      9 modules after meta-cell network construction
  - - **label:**
      CRC-associated CTD signature
    - **value:**
      4 modules (M1, M3, M4 and M6), totaling 559 genes
  - - **label:**
      ClockProCRC random-background model
    - **value:**
      100 expression bins and 1,000 expression-matched random samplings
  - - **label:**
      article-reported circadian robustness evaluation
    - **value:**
      16 independent public datasets spanning human, mouse and non-human-primate circadian contexts
  - - **label:**
      CRC cross-cohort robustness layer
    - **value:**
      >1,400 CRC samples across 10 independent cohorts
  - - **label:**
      functional CRC cell models
    - **value:**
      HCT116 and SW480
- **counting note:**
  The article reports heterogeneous evidence units. The 25 tissue samples in the primary GSE166555 single-cell cohort yielded 94,683 post-QC cells and must not be conflated with participant counts. The Methods reports an aggregate 3,758 samples across 35 public datasets, while the Abstract describes the primary 25-sample single-cell cohort plus 3,733 samples from 34 additional cohorts. These figures are preserved as article-reported dataset/sample counts and are not interpreted as 3,758 unique human participants.

### What is ClockProCRC and how was it constructed?

ClockProCRC is a transcriptomic circadian-misalignment scoring framework. The study began with a 906-gene colon circadian reference and separately used CRC single-cell co-expression analysis to derive nine modules and a 559-gene four-module CTD signature. The ClockProCRC scoring Methods then applied expression-matched random-background correction to circadian rhythm disorder genes using 100 expression bins and 1,000 random samplings. The reviewed manuscript text does not establish that the 559 CTD genes are identical to the final scoring gene set.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1038-s41698-026-01699-1.html#qa-1)

- [KF1](https://drgezhang.com/papers/doi-10-1038-s41698-026-01699-1.html#kf1) — Results: single-cell CRC landscape and high-dimensional circadian co-expression network, Fig. 1A-I and Supplementary Fig. 2; Methods: Single-cell RNA sequencing, Bulk RNA sequencing, and microarray chip cohort processing; Expression of the circadian gene set in the colorectum; High-dimensional co-expression network analysis; Supplementary Tables 2-3

- [KF2](https://drgezhang.com/papers/doi-10-1038-s41698-026-01699-1.html#kf2) — Results: ClockProCRC score detection and quantification of endogenous circadian disorder states, Fig. 2B-I and Supplementary Fig. 3A; Methods: Development of ClockProCRC scoring system; Detection of the biological clock rhythm of the ClockProCRC score; Assessment of Cross-species Rhythmic Module Concordance

### How did CLOCK knockdown, melatonin and the reported SYNE1 AUC relate to the circadian perturbation experiment?

CLOCK knockdown increased ClockProCRC and disrupted SYNE1 rhythmicity; melatonin partially restored the ClockProCRC-defined state and SYNE1 rhythmicity in CRC-cell experiments. The reported SYNE1 AUC of 0.915 refers specifically to discrimination of CLOCK-knockdown experimental conditions, not to CRC diagnosis or patient-level prediction.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1038-s41698-026-01699-1.html#qa-7)

- [KF6](https://drgezhang.com/papers/doi-10-1038-s41698-026-01699-1.html#kf6) — Results: SYNE1 functional and circadian-perturbation experiments, Fig. 6A-N and related supplementary figures; Methods: Cell lines; Cell transfection with siRNA and plasmids; Bulk RNA-seq; qRT-PCR; Transwell assay and scratch assay; Western blot analysis; Cell cloning formation experiment

### Are ClockProCRC or SYNE1 clinically validated for diagnosis, prognosis or treatment selection?

No. ClockProCRC has multicohort analytical and retrospective association evidence but lacks large prospective multicenter clinical validation and a universal clinical cutoff. SYNE1 has computational and in-vitro functional evidence but no SYNE1-directed animal efficacy or patient-treatment validation.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1038-s41698-026-01699-1.html#qa-8)

- [KF2](https://drgezhang.com/papers/doi-10-1038-s41698-026-01699-1.html#kf2) — Results: ClockProCRC score detection and quantification of endogenous circadian disorder states, Fig. 2B-I and Supplementary Fig. 3A; Methods: Development of ClockProCRC scoring system; Detection of the biological clock rhythm of the ClockProCRC score; Assessment of Cross-species Rhythmic Module Concordance

- [KF3](https://drgezhang.com/papers/doi-10-1038-s41698-026-01699-1.html#kf3) — Results: Analysis of clinical significance of ClockProCRC score, Fig. 3A-I; Methods: Analysis of the evaluation and clinical correlation of circadian rhythm disorder scores

- [KF5](https://drgezhang.com/papers/doi-10-1038-s41698-026-01699-1.html#kf5) — Results: Key circadian and night regulatory genes screening and their effects on circadian rhythm disorder in colorectal cancer, Fig. 5A-G and Supplementary Figs. 3F, 4A-E, 5F-G; Methods: Construction of the circadian rhythm gene regulation network (GRN)

- [KF6](https://drgezhang.com/papers/doi-10-1038-s41698-026-01699-1.html#kf6) — Results: SYNE1 functional and circadian-perturbation experiments, Fig. 6A-N and related supplementary figures; Methods: Cell lines; Cell transfection with siRNA and plasmids; Bulk RNA-seq; qRT-PCR; Transwell assay and scratch assay; Western blot analysis; Cell cloning formation experiment

### Complete reviewed evidence scope

- **supports:**
  - The article defines a 906-gene colon circadian reference and derives CRC-associated circadian co-expression structure from a 94,683-cell single-cell dataset.
  - ClockProCRC uses expression-matched random-background correction and varies in expected directions across multiple experimentally or behaviorally perturbed circadian datasets.
  - Higher ClockProCRC values are associated with CRC progression-related states and poorer overall survival in the analyzed retrospective/public cohorts.
  - ClockProCRC-defined states are associated with distinct CRC single-cell composition and intercellular-communication patterns.
  - SYNE1 is prioritized by gene-regulatory-network analysis and shows circadian perturbation-associated expression/rhythmicity changes across independent datasets.
  - SYNE1 knockdown in HCT116 and SW480 cells reduces migration, invasion and colony formation and shifts E-cadherin, ZO-1 and N-cadherin expression.
  - CLOCK knockdown and melatonin rescue conditions alter ClockProCRC and SYNE1 rhythmicity in CRC-cell experiments.
- **does not establish:**
  - That ClockProCRC has been prospectively validated in a multicenter clinical cohort.
  - That ClockProCRC is a clinically approved diagnostic, prognostic, screening or treatment-selection test.
  - That the cohort-specific median or single-cell 75th-percentile grouping rules define a universal clinical cutoff.
  - That higher ClockProCRC causally drives CRC progression in humans; most clinical and tumor-microenvironment evidence is observational or retrospective.
  - That ClockProCRC adds incremental clinical utility over established CRC staging, molecular markers or treatment-response assessment.
  - That SYNE1 is a validated therapeutic target in patients with CRC.
  - That SYNE1 inhibition improves tumor control, metastasis or survival in vivo; the study reports cell-line perturbation but no SYNE1-directed animal efficacy experiment.
  - That melatonin treatment is effective for CRC patients; melatonin was used as a molecular rescue condition in cell experiments.
  - That AUC=0.915 represents CRC diagnosis or patient-level prediction; it refers to discrimination of CLOCK-knockdown experimental conditions by SYNE1 expression.
  - That single-cell ligand-receptor and pathway analyses prove causal tumor-microenvironment remodeling.

### Complete reviewed limitations

- Most human clinical evidence derives from retrospective/public transcriptomic datasets rather than a prospectively enrolled multicenter clinical validation cohort.
- The study integrates heterogeneous evidence units across human, mouse and non-human-primate datasets; sample, tissue, cohort and cell counts are not interchangeable.
- ClockProCRC grouping uses data-context-specific thresholds (75th percentile for single-cell analyses and commonly the cohort median for bulk cohorts), not a universal clinical cutoff.
- The manuscript distinguishes the 906-gene colon circadian reference from the 559-gene four-module CTD signature. The ClockProCRC scoring Methods refers to circadian rhythm disorder genes (CRGs), so this evidence page does not infer that the 559 CTD genes are identical to the final score-input gene set.
- The Results text contains the accession GSE200977, whereas the Methods and Figure 4 legend identify the CRC single-cell cohort as GSE200997; the evidence page uses GSE200997 and records the Results-text accession as a manuscript typo.
- The manuscript contains several wording/locator inconsistencies, including knockdown described once as knockout, Transwell language that conflates proliferation with migration/invasion, and a scratch-assay timing inconsistency; the evidence page follows the experimental Methods and figure legends.
- The public ClockProCRC GitHub repository is an associated code resource but does not exactly mirror the accepted manuscript: the README reports an earlier 32-cohort/3,075-sample configuration, the current scoring script defaults to 50 bins rather than the manuscript's 100 bins, and DiffCircadian.R contains a placeholder scoring function.
- SYNE1 functional evidence is in vitro; no SYNE1-directed animal efficacy experiment or human therapeutic study is reported.
- The publisher currently labels the article as an early peer-reviewed accepted version that may undergo further editing before the final Version of Record.

## Cardiovascular chronotherapy narrative synthesis

### Circadian Immunity and Vascular Inflammation in Cardiovascular Disease Chronotherapy Windows: Time for a Re-Assessment

[Author evidence page](https://drgezhang.com/papers/doi-10-1002-mdr2-70052.html) · [Formal publication DOI](https://doi.org/10.1002/mdr2.70052) · [BibTeX](https://drgezhang.com/citations/doi-10-1002-mdr2-70052.bib) · [RIS](https://drgezhang.com/citations/doi-10-1002-mdr2-70052.ris) · [CSL JSON](https://drgezhang.com/citations/doi-10-1002-mdr2-70052.csl.json)

### Reviewed study profile

- **profile type:**
  narrative_review
- **study design:**
  Narrative evidence synthesis integrating molecular, cellular, animal, epidemiological and clinical chronotherapy literature. The article does not report a PRISMA-style systematic-search or study-selection workflow, quantitative meta-analysis, or a newly generated dataset.
- **evidence type:**
  Narrative synthesis of heterogeneous preclinical, mechanistic, epidemiological and clinical evidence; no new dataset and no pooled meta-analytic effect estimate.
- **evidence domains:**
  - Molecular circadian clock
  - Redox and epigenetic regulation
  - PRR / NF-kB / NLRP3 inflammatory signaling
  - Cytokine, chemokine and adhesion-molecule rhythmicity
  - Immune-cell trafficking and function
  - Cardiovascular disease mechanisms
  - Preclinical chronotherapy
  - Clinical chronotherapy and translation
- **diseases covered:**
  - Atherosclerosis
  - Stroke
  - Ischemic heart disease
  - Myocardial infarction
  - Heart failure
  - Hypertension and blood-pressure chronotherapy where relevant
- **translation scope:**
  Mechanistic rationale and preclinical chronotherapy are substantially stronger than the clinical evidence for universal time-specific dosing.
- **scale metrics:**
  - - **label:**
      Article type
    - **value:**
      Review Article
  - - **label:**
      Bibliography
    - **value:**
      392 references
  - - **label:**
      Tables
    - **value:**
      5 synthesis tables
  - - **label:**
      Figures
    - **value:**
      9 figures
  - - **label:**
      New data
    - **value:**
      None created or analyzed
- **counting note:**
  This is a narrative review. The 392 bibliography entries include heterogeneous evidence types and are not a systematic count of independent studies, experiments, animals or participants. Study-level denominators must not be summed into a synthetic n. The review reports no newly generated or newly analyzed dataset.

### What type of article is this?

It is a narrative Review Article synthesizing prior evidence. It reports no new experimental or clinical dataset, systematic study-selection workflow or pooled meta-analysis.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1002-mdr2-70052.html#qa-1)

- [KF1](https://drgezhang.com/papers/doi-10-1002-mdr2-70052.html#kf1) — Sections 2.1-2.4; Figures 1-2; Tables 1-2.

- [KF7](https://drgezhang.com/papers/doi-10-1002-mdr2-70052.html#kf7) — Sections 8.1-8.4.

### Should all antihypertensive medications be taken at bedtime?

No. Clinical evidence conflicts: Hygia and related studies reported bedtime-dosing benefits, while BedMed did not reproduce a cardiovascular-event benefit. The review does not support a universal bedtime recommendation.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1002-mdr2-70052.html#qa-7)

- [KF6](https://drgezhang.com/papers/doi-10-1002-mdr2-70052.html#kf6) — Section 7.2; Table 5.

- [KF8](https://drgezhang.com/papers/doi-10-1002-mdr2-70052.html#kf8) — Section 7.2; Table 5; Sections 8.1-8.4.

### Is this a systematic review or meta-analysis?

No. The article reports no explicit systematic-search strategy, PRISMA study-selection workflow or quantitative meta-analysis; its 392 references are bibliography entries, not a systematic count of independent studies.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1002-mdr2-70052.html#qa-10)

- [KF7](https://drgezhang.com/papers/doi-10-1002-mdr2-70052.html#kf7) — Sections 8.1-8.4.

### Complete reviewed evidence scope

- **supports:**
  - Prior evidence links circadian clock networks with immune and vascular processes, inflammatory and redox pathways.
  - Immune-cell number, trafficking and functional state can vary with circadian timing across experimental contexts.
  - Experimental circadian disruption can alter cardiovascular inflammatory phenotypes, while cardiovascular physiology and events exhibit time-of-day patterns.
  - Preclinical evidence provides a mechanistic rationale for chronotherapy; some cardiovascular drugs show dosing-time-dependent physiological effects.
  - Clinical chronotherapy remains an active and unresolved translational field.
- **does not establish:**
  - A new patient cohort, new experimental data or a newly analyzed dataset.
  - A systematic review, meta-analysis or pooled quantitative effect size.
  - One universally causal circadian pathway across all cardiovascular diseases.
  - Human cardiovascular treatment efficacy of REV-ERB agonists or time-targeted NLRP3 or NF-kB inhibition.
  - Universal superiority of bedtime antihypertensive dosing or a dosing schedule suitable for every patient.
  - Reduced myocardial infarction or stroke outcomes from bedtime aspirin.
  - Established optimal dosing for SGLT2 inhibitors, colchicine, mineralocorticoid receptor antagonists or ARNI.
  - A guideline-level recommendation to change cardiovascular medication timing.

### Complete reviewed limitations

- This is a narrative, non-systematic evidence synthesis with no new dataset or pooled effect estimate.
- Species, tissues, disease models and evidence levels are heterogeneous; causal animal or cell findings cannot automatically be generalized to human cardiovascular disease.
- Constitutive and inducible clock-gene knockout models may yield different findings.
- Treatment-timing evidence is uneven across cardiovascular drug classes and many proposed chronotherapy windows remain theoretical or preclinical.
- Clinical antihypertensive timing evidence is conflicting, including Hygia-versus-BedMed differences.
- No universal dosing recommendation is established; high-quality circadian-aware randomized clinical trials are needed.
