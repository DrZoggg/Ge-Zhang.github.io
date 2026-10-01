# Molecular subtypes of ischemic heart disease based on circadian rhythm

Researcher: Ge Zhang
Chinese name: 张格
ORCID identity anchor: https://orcid.org/0000-0002-3116-3246
Canonical researcher: https://drgezhang.com/#person

Journal: Scientific Reports
Year: 2024
Type: Article
DOI: 10.1038/s41598-024-65236-5
Canonical page: https://drgezhang.com/papers/circadian-ihd.html
Markdown record: https://drgezhang.com/papers/circadian-ihd.md

## Full Authors

1. Zhaokai Zhou
2. Ge Zhang
3. Zhan Wang
4. Yudi Xu
5. Hongzhuo Qin
6. Haonan Zhang
7. Pengpeng Zhang
8. Zhengrui Li
9. Shuai Xu
10. Xin Tan
11. Yiyao Zeng
12. Fengyi Yu
13. Shanshan Zhu
14. Le Chang
15. Youyang Zheng
16. Xinwei Han

## Official Abstract

Coronary atherosclerotic heart disease (CAD) is among the most prevalent chronic diseases globally. Circadian rhythm disruption (CRD) is closely associated with the progression of various diseases. However, the precise role of CRD in the development of CAD remains to be elucidated. The Circadian rhythm disruption score (CRDscore) was employed to quantitatively assess the level of CRD in CAD samples. Our investigation revealed a significant association between high CRDscore and adverse prognosis in CAD patients, along with a substantial correlation with CAD progression. Remarkably distinct CRDscore distributions were also identified among various subtypes. In summary, we have pioneered the revelation of the relationship between CRD and CAD at the single-cell level and established reliable markers for the development, treatment, and prognosis of CAD. A deeper understanding of these mechanisms may offer new possibilities for incorporating "the therapy of coronary heart disease based circadian rhythm" into personalized medical treatment regimens.

Text reproduced verbatim from Version of Record ([source](https://www.nature.com/articles/s41598-024-65236-5)); [DOI](https://doi.org/10.1038/s41598-024-65236-5); [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).

<a id="paper-discovery"></a>
## Research & review context

### Research fields

- Coronary disease systems biology
- Circadian-related cardiovascular research

### Review topics

- Molecular heterogeneity in ischemic heart disease
- Expression-based coronary disease subtyping

### Scientific role

Single-cell network and bulk-expression integration for circadian-related coronary disease scores and research subtypes.

### Evidence position

Retrospective transcriptomics with external template evaluation; expression scores are not physiological circadian measurements, validated mortality models or chronotherapy evidence.

### Related concepts

- Circadian-related molecular stratification
- Expression-versus-physiological rhythm distinction

### Possible citation contexts

- Background: circadian-related expression programs in coronary disease.
- Methods: single-cell-to-bulk expression subtyping, retaining repeated-sample and outcome-model boundaries.

Possible literature-review contexts, not evidence of existing citations. Read the findings and Evidence Scope before citing the original article.

## Evidence Scale

**Molecular subtypes of ischemic heart disease based on circadian rhythm**

Transcriptomic CRDscore and coronary-disease subtype analysis, with explicit qualification of repeated samples and reference-dataset identity.

| Evidence | Value |
| --- | --- |
| GSE184073 analyzed samples | 2 samples |
| GSE184073 post-QC cells | 2,237 cells |
| GSE59867 expression samples | 436 samples, not 436 independent patients |
| GSE59867 original design | Repeated follow-up of 111 STEMI patients and 46 stable CAD controls |
| GSE20680 article-reported samples | 195 |
| GSE20681 article-reported samples | 198 |
| GSE43292 article-reported samples | 64 |
| GSE62646 article-reported samples | 98 |

### Counting note

GSE184073 cells are not independent patients. GSE59867 contains repeated follow-up of 111 STEMI patients and 46 stable CAD controls; its 436 expression samples are not 436 independent patients. Follow-up represents post-infarction recovery time points, not 24-hour circadian monitoring of the same individual. External dataset counts are article-reported samples and are not summed into a deduplicated participant total. External validation means retrospective expression-template evaluation, not prospective clinical utility. GSE70049 is a Danio rerio setb morphant expression experiment, not a verified mouse circadian perturbation.

## Research Question

Can circadian-related expression patterns define reproducible molecular subtypes of coronary disease, without treating an expression score as a direct measurement of each patient's physiological circadian rhythm?

## Author Evidence Summary

This computational study connects single-cell expression structure with bulk transcriptomic subtyping. Its contribution is a research framework for expression-associated heterogeneity, not an established circadian diagnostic test or treatment-selection rule. Repeated sampling and the identity of one cited reference dataset require explicit qualification.

## Key Findings

<a id="kf1"></a>
### KF1: The analysis of GSE184073 constructed a single-cell co-expression foundation related to coronary disease.

Context: GSE184073 single-cell expression analysis.

| Evidence | Value |
| --- | --- |
| Post-QC cells | 2,237 |
| Analyzed samples | 2 |
| Non-grey modules | 8 |

Source locator: Results: Construction of WGCNA network in scRNA-seq dataset; Fig. 1

<a id="kf2"></a>
### KF2: CRDscore was constructed as a research score from target-gene expression and a random background.

Context: Single-cell and bulk expression scoring.

| Evidence | Value |
| --- | --- |
| Formula | CRDscore = Srandom - SCADCRgenes |
| Random features | 1,000 |
| Single-cell cutoff | 75th percentile |
| Bulk cutoff | Median |

Source locator: Methods: Calculation of CRDscore based on circadian-related genes

<a id="kf3"></a>
### KF3: The article reports external reference-data evaluation, but the use of GSE70049 requires qualification.

Context: Identity of a cited reference expression dataset.

| Evidence | Value |
| --- | --- |
| GSE70049 organism | Danio rerio |
| GSE70049 experiment | setb morphant expression experiment |

Source locator: Methods: Data processing; NCBI GEO GSE70049 record

<a id="kf4"></a>
### KF4: Expression-based subtyping of GSE59867 yielded four groups.

Context: Discovery expression-sample assignment.

| Evidence | Value |
| --- | --- |
| Type1 samples | 124 |
| Type2 samples | 93 |
| Type3 samples | 87 |
| Type4 samples | 132 |
| Total expression samples | 436 |

Source locator: Methods: Construction and validation of the CRD-related subtypes of CAD; Results: subtype identification; Fig. 4

<a id="kf5"></a>
### KF5: NTP was used to evaluate subtype assignment in four external expression datasets.

Context: External expression-template evaluation.

| Evidence | Value |
| --- | --- |
| Datasets | GSE20680; GSE20681; GSE43292; GSE62646 |

Source locator: Methods: Construction and validation of the CRD-related subtypes of CAD; Fig. 4

<a id="kf6"></a>
### KF6: Type2 showed higher CRDscore and immune-inflammatory expression characteristics.

Context: Subtype-associated expression and computational annotations.

| Evidence | Value |
| --- | --- |
| Contractile markers | Lower expression |
| Immune and collagen pathways | Associated enrichment differences |

Source locator: Results: functional and immune microenvironment analyses; Figs. 5-6

## Study Design & Analytical Framework

### Study profile

- Study Design: Retrospective public single-cell and bulk transcriptomic analysis
- Evidence Type: Expression-based subtyping, computational annotation and external template evaluation
- Population: Public coronary-disease-related samples and separately analyzed reference datasets
- Primary Endpoint: Expression-defined CRDscore and molecular subtype structure
- Secondary Endpoint: External subtype assignment and associated immune/functional annotations
- External dataset evaluation: Yes
- Data modalities: single-cell RNA sequencing, bulk expression arrays, co-expression networks, NTP, computational enrichment and cell-type estimates

## What This Study Adds

- Links single-cell networks with bulk expression subtyping.
- Provides a research expression-score construction.
- Retains external template evaluation with its applicable evidence scope.

## Evidence Scope

### Supports

- The analysis of GSE184073 constructed a single-cell co-expression foundation related to coronary disease.
- CRDscore was constructed as a research score from target-gene expression and a random background.
- The article reports external reference-data evaluation, but the use of GSE70049 requires qualification.
- Expression-based subtyping of GSE59867 yielded four groups.
- NTP was used to evaluate subtype assignment in four external expression datasets.
- Type2 showed higher CRDscore and immune-inflammatory expression characteristics.

### Does Not Establish

- Direct measurement of physiological circadian phase, amplitude or period.
- A discovery cohort of 436 independent patients.
- Verification that all cited reference experiments are mouse circadian interventions.
- Prospectively validated clinical risk prediction or clinical utility.
- Benefit from treatment or chronotherapy.
- An independently verified mortality hazard ratio, AUC or clinical cutoff; adverse-prognosis wording is not a verified all-cause mortality model.

### Limitations

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

<a id="citation-use-cases"></a>
## When This Study Is Useful to Cite

### CU1: Which coronary-disease studies combined single-cell networks with a circadian-related expression score?

The analysis of GSE184073 constructed a single-cell co-expression foundation related to coronary disease. Post-QC cells: 2,237; Analyzed samples: 2; Non-grey modules: 8. Cells are not independent patients; two analyzed samples do not establish population-level robustness. CRDscore was constructed as a research score from target-gene expression and a random background. Formula: CRDscore = Srandom - SCADCRgenes; Random features: 1,000; Single-cell cutoff: 75th percentile; Bulk cutoff: Median. The score does not directly measure an individual's circadian phase, amplitude or period. The two data-layer cutoffs are not one clinical threshold.

Evidence: [KF1](#kf1), [KF2](#kf2)

### CU2: What evidence supports expression-defined coronary-disease subtypes?

Expression-based subtyping of GSE59867 yielded four groups. Type1 samples: 124; Type2 samples: 93; Type3 samples: 87; Type4 samples: 132; Total expression samples: 436. These are expression-sample groups, not 436 independent patients. The grouping does not resolve independence of repeated follow-up samples or outcome analyses. NTP was used to evaluate subtype assignment in four external expression datasets. Datasets: GSE20680; GSE20681; GSE43292; GSE62646. External expression-template reproducibility is not prospective risk prediction or demonstrated clinical utility.

Evidence: [KF4](#kf4), [KF5](#kf5)

### CU3: What counting and dataset-identity cautions apply to CRDscore evidence?

The article reports external reference-data evaluation, but the use of GSE70049 requires qualification. GSE70049 organism: Danio rerio; GSE70049 experiment: setb morphant expression experiment. The evidence does not establish that all four reference experiments are verified mouse circadian interventions. No intended replacement accession is inferred. Expression-based subtyping of GSE59867 yielded four groups. Type1 samples: 124; Type2 samples: 93; Type3 samples: 87; Type4 samples: 132; Total expression samples: 436. These are expression-sample groups, not 436 independent patients. The grouping does not resolve independence of repeated follow-up samples or outcome analyses.

Evidence: [KF3](#kf3), [KF4](#kf4)

### CU4: How are coronary expression subtypes associated with immune and contractile programs?

Type2 showed higher CRDscore and immune-inflammatory expression characteristics. Contractile markers: Lower expression; Immune and collagen pathways: Associated enrichment differences. Computational estimates and expression associations do not establish causal plaque transitions or benefit from immunotherapy or chronotherapy.

Evidence: [KF6](#kf6)

<a id="citation-boundaries"></a>
## What This Study Should Not Be Cited to Claim

- Direct measurement of physiological circadian phase, amplitude or period.
- A discovery cohort of 436 independent patients.
- Verification that all cited reference experiments are mouse circadian interventions.
- Prospectively validated clinical risk prediction or clinical utility.
- Benefit from treatment or chronotherapy.
- An independently verified mortality hazard ratio, AUC or clinical cutoff; adverse-prognosis wording is not a verified all-cause mortality model.

<a id="evidence-matrix"></a>
## Evidence Matrix

<a id="evidence-ihd-1"></a>
### Single-cell co-expression foundation

- Context: GSE184073 single-cell expression analysis.
- Finding: The analysis of GSE184073 constructed a single-cell co-expression foundation related to coronary disease. Post-QC cells: 2,237; Analyzed samples: 2; Non-grey modules: 8
- Evidence Level: Retrospective expression and computational evidence
- Scope: Cells are not independent patients; two analyzed samples do not establish population-level robustness.
- Source Locator: Results: Construction of WGCNA network in scRNA-seq dataset; Fig. 1
- Evidence refs: [KF1](#kf1)

<a id="evidence-ihd-2"></a>
### CRDscore construction

- Context: Single-cell and bulk expression scoring.
- Finding: CRDscore was constructed as a research score from target-gene expression and a random background. Formula: CRDscore = Srandom - SCADCRgenes; Random features: 1,000; Single-cell cutoff: 75th percentile; Bulk cutoff: Median
- Evidence Level: Retrospective expression and computational evidence
- Scope: The score does not directly measure an individual's circadian phase, amplitude or period. The two data-layer cutoffs are not one clinical threshold.
- Source Locator: Methods: Calculation of CRDscore based on circadian-related genes
- Evidence refs: [KF2](#kf2)

<a id="evidence-ihd-3"></a>
### Reference-dataset qualification

- Context: Identity of a cited reference expression dataset.
- Finding: The article reports external reference-data evaluation, but the use of GSE70049 requires qualification. GSE70049 organism: Danio rerio; GSE70049 experiment: setb morphant expression experiment
- Evidence Level: Reference-record identity qualification
- Scope: The evidence does not establish that all four reference experiments are verified mouse circadian interventions. No intended replacement accession is inferred.
- Source Locator: Methods: Data processing; NCBI GEO GSE70049 record
- Evidence refs: [KF3](#kf3)

<a id="evidence-ihd-4"></a>
### Discovery subtyping

- Context: Discovery expression-sample assignment.
- Finding: Expression-based subtyping of GSE59867 yielded four groups. Type1 samples: 124; Type2 samples: 93; Type3 samples: 87; Type4 samples: 132; Total expression samples: 436
- Evidence Level: Retrospective expression and computational evidence
- Scope: These are expression-sample groups, not 436 independent patients. The grouping does not resolve independence of repeated follow-up samples or outcome analyses.
- Source Locator: Methods: Construction and validation of the CRD-related subtypes of CAD; Results: subtype identification; Fig. 4
- Evidence refs: [KF4](#kf4)

<a id="evidence-ihd-5"></a>
### External template assignment

- Context: External expression-template evaluation.
- Finding: NTP was used to evaluate subtype assignment in four external expression datasets. Datasets: GSE20680; GSE20681; GSE43292; GSE62646
- Evidence Level: Retrospective expression and computational evidence
- Scope: External expression-template reproducibility is not prospective risk prediction or demonstrated clinical utility.
- Source Locator: Methods: Construction and validation of the CRD-related subtypes of CAD; Fig. 4
- Evidence refs: [KF5](#kf5)

<a id="evidence-ihd-6"></a>
### Immune and functional context

- Context: Subtype-associated expression and computational annotations.
- Finding: Type2 showed higher CRDscore and immune-inflammatory expression characteristics. Contractile markers: Lower expression; Immune and collagen pathways: Associated enrichment differences
- Evidence Level: Retrospective expression and computational evidence
- Scope: Computational estimates and expression associations do not establish causal plaque transitions or benefit from immunotherapy or chronotherapy.
- Source Locator: Results: functional and immune microenvironment analyses; Figs. 5-6
- Evidence refs: [KF6](#kf6)

## Q&A

### What single-cell evidence underlies this coronary expression framework?

The analysis of GSE184073 constructed a single-cell co-expression foundation related to coronary disease. Post-QC cells: 2,237; Analyzed samples: 2; Non-grey modules: 8. Cells are not independent patients; two analyzed samples do not establish population-level robustness.

Evidence: KF1

### What does CRDscore measure, and what does it not directly measure?

CRDscore was constructed as a research score from target-gene expression and a random background. Formula: CRDscore = Srandom - SCADCRgenes; Random features: 1,000; Single-cell cutoff: 75th percentile; Bulk cutoff: Median. The score does not directly measure an individual's circadian phase, amplitude or period. The two data-layer cutoffs are not one clinical threshold.

Evidence: KF2

### Are all cited reference datasets verified mouse circadian experiments?

The article reports external reference-data evaluation, but the use of GSE70049 requires qualification. GSE70049 organism: Danio rerio; GSE70049 experiment: setb morphant expression experiment. The evidence does not establish that all four reference experiments are verified mouse circadian interventions. No intended replacement accession is inferred.

Evidence: KF3

### Does the discovery dataset represent 436 independent patients?

Expression-based subtyping of GSE59867 yielded four groups. Type1 samples: 124; Type2 samples: 93; Type3 samples: 87; Type4 samples: 132; Total expression samples: 436. These are expression-sample groups, not 436 independent patients. The grouping does not resolve independence of repeated follow-up samples or outcome analyses.

Evidence: KF4

### What kind of external validation was performed?

NTP was used to evaluate subtype assignment in four external expression datasets. Datasets: GSE20680; GSE20681; GSE43292; GSE62646. External expression-template reproducibility is not prospective risk prediction or demonstrated clinical utility.

Evidence: KF5

### Do subtype-associated immune patterns establish treatment benefit?

Type2 showed higher CRDscore and immune-inflammatory expression characteristics. Contractile markers: Lower expression; Immune and collagen pathways: Associated enrichment differences. Computational estimates and expression associations do not establish causal plaque transitions or benefit from immunotherapy or chronotherapy.

Evidence: KF6

## Concepts & Entities

### Disease

coronary artery disease, ischemic heart disease

### Methods

single-cell RNA sequencing, co-expression network, NTP

### Entities

CRDscore, CADCR genes

### Evidence

transcriptomic subtyping, repeated measurements

## Related Research

- [Atherosclerotic plaque vulnerability quantification system for clinical and biological interpretability](https://drgezhang.com/papers/apvs.html) — Related coronary transcriptomic and single-cell evidence with a different research objective; the studies do not validate each other's models. (DOI: 10.1016/j.isci.2023.107587)
- [System biology analysis reveals circadian rhythm disorder associated with development and progression in colorectal cancer](https://drgezhang.com/papers/doi-10-1038-s41698-026-01699-1.html) — Circadian-related expression scoring in a different disease; this does not establish identical gene sets, formula implementation or shared clinical validation. (DOI: 10.1038/s41698-026-01699-1)

## Publication & Provenance

- DOI: https://doi.org/10.1038/s41598-024-65236-5
- Doi Url: https://doi.org/10.1038/s41598-024-65236-5
- Publisher: https://www.nature.com/articles/s41598-024-65236-5
- PubMed: https://pubmed.ncbi.nlm.nih.gov/38898215/
- Pmc Url: https://pmc.ncbi.nlm.nih.gov/articles/PMC11187219/
- Gse59867 Url: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE59867
- Gse70049 Url: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE70049
- Review Basis: Evidence synthesis from the cited main text, figure legends and designated primary records. No independent reanalysis of participant-level data. Unavailable supplementary or figure-only details are not reconstructed.

## Evidence-page notice

Author-controlled evidence synthesis, distinct from the published abstract and not a replacement for the version of record. Source-specific counting and interpretation limits are retained.

## Links

- DOI: https://doi.org/10.1038/s41598-024-65236-5
- HTML page: https://drgezhang.com/papers/circadian-ihd.html
- Google Scholar query: https://scholar.google.com/scholar?q=%22Molecular%20subtypes%20of%20ischemic%20heart%20disease%20based%20on%20circadian%20rhythm%22
- ORCID: https://orcid.org/0000-0002-3116-3246
