# Atherosclerotic plaque vulnerability quantification system for clinical and biological interpretability

Researcher: Ge Zhang
Chinese name: 张格
ORCID identity anchor: https://orcid.org/0000-0002-3116-3246
Canonical researcher: https://drgezhang.com/#person

Journal: iScience
Year: 2023
Type: Article
DOI: 10.1016/j.isci.2023.107587
Canonical page: https://drgezhang.com/papers/apvs.html
Markdown record: https://drgezhang.com/papers/apvs.md

## Full Authors

1. Ge Zhang
2. Xiaolin Cui
3. Zhen Qin
4. Zeyu Wang
5. Yongzheng Lu
6. Yanyan Xu
7. Shuai Xu
8. Laiyi Tang
9. Li Zhang
10. Gangqiong Liu
11. Xiaofang Wang
12. Jinying Zhang
13. Junnan Tang

## Evidence Scale

**APVS / APVSLevel: machine-learning and single-cell quantification of atherosclerotic plaque vulnerability**

A multicohort transcriptomic and single-cell framework that derives a 14-gene machine-learning signature and APVSLevel system for classification, quantification, and biological interpretation of atherosclerotic plaque vulnerability.

| Evidence | Value |
| --- | --- |
| bulk transcriptomic cohorts | 22 |
| bulk samples reported in Summary | 2,235 |
| single-cell cohorts | 2 |
| single-cell samples reported in Summary | 14 |
| GSE159677 single-cell scale | 43,964 cells from 3 atherosclerotic cores and 3 adjacent normal tissues |
| GSE184073 single-cell scale | 2,237 cells from plaques of 3 STEMI and 4 CCS patients |

### Counting note

The publication reports 2,235 samples from 22 bulk cohorts and 14 samples from two single-cell cohorts in the Summary, while detailed single-cell analyses describe 3 atherosclerotic cores plus 3 adjacent normal tissues and plaques from 3 STEMI plus 4 CCS patients. These modality-specific counts are preserved as reported and are not combined into a derived unique-participant total.

## Research Question

Can an integrative machine-learning and transcriptomic framework identify a robust molecular signature of atherosclerotic plaque vulnerability and quantify the transition from stable to unstable disease across bulk and single-cell resolution?

## Author Evidence Summary

APVS is a transcriptome-based molecular signature developed to characterize atherosclerotic plaque vulnerability across multiple stages of coronary artery disease. The study integrated 22 bulk transcriptomic cohorts with two single-cell RNA-sequencing cohorts and used a nine-learner machine-learning framework to reduce 96 dysregulated co-expression pattern genes to a 14-gene atherosclerotic plaque vulnerability signature. The APVS classifier discriminated clinically and pathologically distinct states, including STEMI versus chronic coronary syndrome, advanced versus early atherosclerotic plaque, and ruptured versus stable plaque, across multiple independent datasets. To extend classification toward biological and clinical interpretation, the study developed APVSLevel, a continuous quantification system associated with coronary stenosis, major adverse cardiovascular events, plaque inflammatory activity, and cellular remodeling. Single-cell analyses linked higher APVSLevel to vulnerable plaque states, inflammatory macrophage programs, and altered macrophage-myofibroblast communication. These results support APVS/APVSLevel as a research framework for molecular characterization and risk stratification of plaque vulnerability; prospective clinical validation remains necessary before routine clinical use.

## Key Findings

### KF1: The integrative machine-learning program reduced 96 dysregulated co-expression pattern genes to a 14-gene APVS signature.

Context: APVS generation and model selection across nine classical machine-learning learners

| Evidence | Value |
| --- | --- |
| candidate DCPGs | 96 |
| machine-learning learners | 9 |
| selected APVS genes | 14 |
| optimal learners | random forest and backpropagation neural network |
| learner evaluation | 10-fold cross-validation with 100 repetitions |
| feature selection | RF-RFE with 10-fold, 10-repeated cross-validation |

Source locator: Results: Machine learning-based integrative program generates APVS; Fig. 2A-E; Methods: APVS generated from an integrative program

### KF2: The APVS classifier showed strong discrimination across independent datasets spanning clinical and pathological atherosclerotic states.

Context: Independent external validation of STEMI/CCS, plaque-stage, plaque-rupture, and STEMI/healthy comparisons

| Evidence | Value |
| --- | --- |
| GSE59867 STEMI vs CCS AUC | 0.985 |
| GSE62646 STEMI vs CCS AUC | 0.997 |
| GSE28829 advanced vs early plaque AUC | 0.952 |
| GSE41571 ruptured vs stable plaque AUC | 0.972 |
| GSE48060 STEMI vs healthy AUC | 0.871 |
| GSE60993 STEMI vs healthy AUC | 0.916 |
| GSE141512 STEMI vs healthy AUC | 1.000 |

Source locator: Results: Robust performance of APVS-based classifier; Fig. S2B and Fig. 3A-B

### KF3: Higher APVSLevel was associated with worse cardiovascular prognosis and greater coronary atherosclerotic severity.

Context: Clinical interpretability analyses across MACE and coronary stenosis datasets

| Evidence | Value |
| --- | --- |
| MACE association | HR 3.819; p<0.01 |
| high vs low APVSLevel MACE incidence | log-rank p<0.01 |
| APVSLevel vs coronary stenosis degree | p<0.001 |
| APVSLevel vs Duke CAD Index | p<0.01 |

Source locator: Results: The clinical interpretability underlying APVSLevel; Fig. 4A-D and Fig. 4J

### KF4: APVSLevel reproduced plaque-vulnerability differences at single-cell resolution.

Context: Two single-cell RNA-sequencing cohorts comparing atherosclerotic core with adjacent normal tissue and vulnerable STEMI plaques with stable CCS plaques

| Evidence | Value |
| --- | --- |
| GSE159677 cells | 43,964 |
| atherosclerotic core vs adjacent normal APVSLevel | higher in atherosclerotic core; p<0.0001 |
| GSE184073 cells | 2,237 |
| vulnerable STEMI vs stable CCS plaque APVSLevel | higher in vulnerable STEMI plaques; p<0.0001 |

Source locator: Results: Single-cell resolution interpretation of the biological significance of APVSLevel; Fig. 7A-B and Fig. S13A

### KF5: High plaque vulnerability was linked to inflammatory macrophage states and loss of plaque-stabilizing fibrotic macrophage phenotypes.

Context: Single-cell macrophage-state analysis in vulnerable STEMI versus stable CCS plaques

| Evidence | Value |
| --- | --- |
| CXCL3+/IL1B+ inflammatory macrophages | higher APVSLevel in STEMI plaques |
| C1Q+ fibrotic macrophages | lower APVSLevel in STEMI plaques |
| APVSLevel-high atherosclerotic core | more monocyte/macrophage and endothelial cells; fewer myofibroblast and SMC populations |

Source locator: Results: Single-cell resolution interpretation; Fig. 7C-E and Fig. S14

### KF6: APVSLevel-high plaques showed a more inflammatory, procoagulant, and matrix-destabilizing molecular state, whereas APVSLevel-low plaques were relatively stromal-rich and fibrotic.

Context: Bulk and single-cell pathway-level biological interpretation

| Evidence | Value |
| --- | --- |
| APVSLevel-high pathways | coagulation cascade, collagen degradation, Notch signaling, TLR signaling |
| APVSLevel-high cell programs | inflammatory response, granulocyte activation, macrophage M1 polarization |
| APVSLevel-low phenotype | stromal-rich, fibroblast migration, fibrous content, relative immune suppression |
| single-cell high-vulnerability programs | coagulation, hypoxia, TNF signaling, heme metabolism, oxidative stress, senescence, DNA damage |

Source locator: Results: The biological implications underlying APVSLevel; Fig. 5, Fig. S6-S8, Fig. 7E, and Fig. S14D-E

### KF7: Plaque vulnerability was accompanied by remodeling of macrophage-myofibroblast communication networks.

Context: CellChat and NicheNet analyses of APVSLevel-high versus APVSLevel-low atherosclerotic core states

| Evidence | Value |
| --- | --- |
| pro-inflammatory signaling | MIF and VCAM strengthened in APVSLevel-high states |
| profibrogenic signaling | SPP1 and FN1 reduced in APVSLevel-high states |
| Mono/Mac-directed ligand-target axes | IL34/CTSK; IL6/SOCS3; AGT/SPP1; APOE/SPP1 |
| myofibroblast-directed ligand-target axes | CXCL2/CDKN1A; ADM/CCL2; NRG1/FOS; ITGB2/CCL2 |

Source locator: Results: Intercellular crosstalk within the atherosclerotic core was remodeled by APVS; Fig. 7F-K and Fig. S15-S16

## Study Design & Model Development

### Study profile

- Study Design: Retrospective multicohort computational systems biology study
- Evidence Type: Bulk transcriptomics, single-cell RNA sequencing, machine learning, and clinical association analyses
- Population: Atherosclerotic and coronary artery disease samples spanning stable and unstable clinical and pathological states
- Primary Endpoint: Discrimination of atherosclerotic and coronary pathological states using the APVS classifier
- Secondary Endpoint: Clinical and biological quantification of plaque vulnerability using APVSLevel
- External dataset evaluation: Yes
- Data modalities: bulk transcriptomics, single-cell RNA sequencing, clinical outcomes, coronary stenosis phenotypes

### Model development

- Candidate Dcpgs: 96
- Algorithms: 9
- Learner Evaluation: 10-fold cross-validation with 100 repetitions
- Optimal Learners: random forest, backpropagation neural network
- Feature selection: Random-forest recursive feature elimination with Gini-based importance and 10-fold, 10-repeated cross-validation
- Signature Size: 14
- Classifier: Backpropagation neural network
- Quantification System: APVSLevel
- Quantification Basis: APVS expression profile combined with principal-coordinate information

## What This Study Adds

- A molecular plaque-vulnerability framework derived from transcriptomic disease states rather than relying only on conventional epidemiological risk factors.
- Cross-condition validation across STEMI versus CCS, advanced versus early plaque, ruptured versus stable plaque, and STEMI versus healthy comparisons.
- A transition from binary classification with APVS to continuous biological and clinical quantification with APVSLevel.
- Bulk-to-single-cell interpretation linking the same vulnerability framework to plaque microenvironment and cellular-state remodeling.
- Mechanistic hypothesis generation through pathway, immune-landscape, and cell-cell communication analyses.

## Evidence Scope

### Supports

- APVS discriminates several studied coronary and plaque pathological states in retrospective transcriptomic datasets.
- APVSLevel is associated with plaque vulnerability, coronary stenosis severity, and MACE risk in the studied cohorts.
- APVSLevel-high states exhibit stronger inflammatory, immune, procoagulant, and plaque-destabilizing molecular programs.
- Single-cell datasets support APVSLevel as a molecular descriptor of vulnerable plaque biology and cellular-state remodeling.
- APVS/APVSLevel can serve as a research framework for molecular stratification and mechanistic exploration of atherosclerotic plaque vulnerability.

### Does Not Establish

- That APVS is a clinically approved diagnostic test for plaque vulnerability.
- That the 14 APVS genes are causal drivers of plaque rupture.
- That APVSLevel-guided treatment reduces myocardial infarction, mortality, or other clinical events.
- That transcriptomic APVS/APVSLevel can replace coronary imaging, cardiac biomarkers, or standard clinical assessment.
- That retrospective public-dataset validation is equivalent to prospective multicenter clinical validation.
- That drug-response or signature-reversal analyses constitute therapeutic recommendations.

### Limitations

- The study was based predominantly on retrospective public high-throughput datasets.
- Prospective multicenter studies are required to confirm the biological and clinical interpretability of APVSLevel.
- The APVS classifier requires further direct comparison with established clinical biomarkers.
- The functions of many APVS-related molecules remain incompletely established and require additional in vivo and in vitro validation.
- Incomplete clinical and molecular traits in source datasets may obscure associations between APVS and some relevant factors.

## Q&A

### What is APVS?

APVS is a 14-gene atherosclerotic plaque vulnerability signature derived from 96 dysregulated co-expression pattern genes using an integrative nine-learner machine-learning framework.

Evidence: KF1

### Can APVS distinguish STEMI from chronic coronary syndrome?

Yes. The APVS classifier achieved AUCs of 0.985 in GSE59867 and 0.997 in GSE62646 for STEMI versus chronic coronary syndrome classification.

Evidence: KF2

### Can APVS distinguish ruptured from stable atherosclerotic plaques?

Yes. In GSE41571, the APVS classifier achieved an AUC of 0.972 for ruptured versus stable plaque classification.

Evidence: KF2

### Can APVS distinguish advanced from early atherosclerotic plaques?

Yes. In GSE28829, the APVS classifier achieved an AUC of 0.952 for advanced versus early-stage plaque classification.

Evidence: KF2

### What is APVSLevel?

APVSLevel is a continuous molecular quantification system derived from the APVS expression profile and principal-coordinate information to represent atherosclerosis severity and plaque vulnerability.

Evidence: KF3, KF4

### Is APVSLevel associated with cardiovascular outcomes and disease severity?

Yes. Higher APVSLevel was associated with increased MACE risk (HR 3.819, p<0.01), greater coronary stenosis (p<0.001), and a higher Duke Coronary Artery Disease Index (p<0.01).

Evidence: KF3

### What single-cell states are associated with high atherosclerotic plaque vulnerability?

Higher APVSLevel was associated with vulnerable plaque microenvironments enriched in inflammatory monocyte/macrophage programs, including CXCL3+/IL1B+ macrophage states, while C1Q+ fibrotic plaque-stabilizing macrophage phenotypes showed lower APVSLevel in STEMI plaques.

Evidence: KF4, KF5

### Is APVS or APVSLevel ready to replace clinical plaque assessment?

No. The evidence is primarily retrospective and transcriptomics-based. Prospective multicenter validation, direct comparison with established clinical biomarkers, and additional experimental validation are required before clinical translation.

## Concepts & Entities

### Conditions

atherosclerosis, coronary artery disease, acute myocardial infarction, ST-elevation myocardial infarction, chronic coronary syndrome, acute coronary syndrome

### Plaque Phenotypes

atherosclerotic plaque vulnerability, stable plaque, ruptured plaque, early-stage plaque, advanced plaque, atherosclerotic core, fibrous plaque

### Outcomes

major adverse cardiovascular events, coronary stenosis, plaque rupture, restenosis after PCI

### Methods

machine learning, random forest, backpropagation neural network, recursive feature elimination, weighted gene co-expression network analysis, principal coordinates analysis, single-cell RNA sequencing, gene set enrichment analysis, gene set variation analysis, DIRAC, VissE, xCell, CellChat, NicheNet, Subclass Mapping

### Models & Tools

APVS, APVS classifier, APVSLevel

### Cell Types

monocyte/macrophage, vascular smooth muscle cell, myofibroblast, endothelial cell, B cell, plasma cell, mast cell, neutrophil, foam cell

### Pathways Processes

inflammation, coagulation, extracellular matrix degradation, fibrosis, oxidative stress, cellular senescence, DNA damage, Notch signaling, TLR signaling, TNF signaling, heme metabolism, cholesterol homeostasis

### Mechanistic Entities

CXCL3, IL1B, C1Q, IL34, CTSK, IL6, SOCS3, AGT, SPP1, APOE, CXCL2, CDKN1A, ADM, CCL2, NRG1, FOS, ITGB2, FN1, MIF, VCAM

### Datasets & Cohorts

GSE59867, GSE62646, GSE28829, GSE41571, GSE48060, GSE60993, GSE141512, GSE21545, GSE159677, GSE184073

## Related Research

- [Smooth muscle cell fate decisions decipher a high-resolution heterogeneity within atherosclerosis molecular subtypes](https://drgezhang.com/papers/smc-fate.html) — Complementary single-cell and transcriptomic evidence for vascular smooth-muscle-cell fate and molecular heterogeneity in atherosclerosis (DOI: 10.1186/s12967-022-03795-9)
- [Vascular smooth muscle cell-derived KIF13B inhibits proinflammatory responses to protect against atherosclerosis](https://drgezhang.com/papers/doi-10-1172-jci194175.html) — Mechanistic evidence linking vascular smooth-muscle-cell KIF13B to inflammatory control and protection from atherosclerosis (DOI: 10.1172/jci194175)
- [The macrophage-derived motor protein KIF13B enhances MERTK-mediated efferocytosis and prevents atherosclerosis in mice](https://drgezhang.com/papers/doi-10-1093-eurheartj-ehaf523.html) — Mechanistic evidence linking macrophage KIF13B, MERTK-mediated efferocytosis, and plaque protection (DOI: 10.1093/eurheartj/ehaf523)
- [A redox-responsive reversible photoacoustic molecular probe for visualizing atherosclerotic plaque redox status in vivo](https://drgezhang.com/papers/doi-10-1007-s11426-026-3629-x.html) — Complementary in-vivo molecular imaging of atherosclerotic plaque redox state (DOI: 10.1007/s11426-026-3629-x)

## Publication & Provenance

- DOI: https://doi.org/10.1016/j.isci.2023.107587
- Publisher: https://www.cell.com/iscience/fulltext/S2589-0042(23)01664-4
- PubMed: https://pubmed.ncbi.nlm.nih.gov/37664595/
- PMCID: PMC10470306
- Code: https://github.com/DrZoggg/APVS
- Evidence Basis: Version of record and PMC full text

## Evidence-page notice

Author-controlled evidence page for this publication. This page provides an evidence-oriented summary and does not replace the publisher's version of record.

## Links

- DOI: https://doi.org/10.1016/j.isci.2023.107587
- HTML page: https://drgezhang.com/papers/apvs.html
- Google Scholar query: https://scholar.google.com/scholar?q=%22Atherosclerotic%20plaque%20vulnerability%20quantification%20system%20for%20clinical%20and%20biological%20interpretability%22
- ORCID: https://orcid.org/0000-0002-3116-3246
