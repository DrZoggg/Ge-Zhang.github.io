# Smooth muscle cell fate decisions decipher a high-resolution heterogeneity within atherosclerosis molecular subtypes

Researcher: Ge Zhang
Chinese name: 张格
ORCID identity anchor: https://orcid.org/0000-0002-3116-3246
Canonical researcher: https://drgezhang.com/#person

Journal: Journal of Translational Medicine
Year: 2022
Type: Article
DOI: 10.1186/s12967-022-03795-9
Canonical page: https://drgezhang.com/papers/smc-fate.html
Markdown record: https://drgezhang.com/papers/smc-fate.md

## Full Authors

1. Ge Zhang
2. Zaoqu Liu
3. Jinhai Deng
4. Long Liu
5. Yu Li
6. Siyuan Weng
7. Chunguang Guo
8. Zhaokai Zhou
9. Li Zhang
10. Xiaofang Wang
11. Gangqiong Liu
12. Jiacheng Guo
13. Jing Bai
14. Yunzhe Wang
15. Youyou Du
16. Tao-Sheng Li
17. Junnan Tang
18. Jinying Zhang

## Official Abstract

### Background

Mounting evidence has revealed the dynamic variations in the cellular status and phenotype of the smooth muscle cell (SMC) are vital for shaping the atherosclerotic plaque microenvironment and ultimately mapping onto heterogeneous clinical outcomes in coronary artery disease. Currently, the underlying clinical significance of SMC evolutions remains unexplored in atherosclerosis.

### Methods

The dissociated cells from diseased segments within the right coronary artery of four cardiac transplant recipients and 1070 bulk samples with atherosclerosis from six bulk cohorts were retrieved. Following the SMC fate trajectory reconstruction, the MOVICS algorithm integrating the nearest template prediction was used to develop a stable and robust molecular classification. Subsequently, multi-dimensional potential biological implications, molecular features, and cell landscape heterogeneity among distinct clusters were decoded.

### Results

We proposed an SMC cell fate decision signature (SCFDS)-based atherosclerosis stratification system and identified three SCFDS subtypes (C1–C3) with distinguishing features: (i) C1 (DNA-damage repair type), elevated base excision repair (BER), DNA replication, as well as oxidative phosphorylation status. (ii) C2 (immune-activated type), stronger immune activation, hyper-inflammatory state, the complex as well as varied lesion microenvironment, advanced stage, the most severe degree of coronary stenosis severity. (iii) C3 (stromal-rich type), abundant fibrous content, stronger ECM metabolism, immune-suppressed microenvironment.

### Conclusions

This study uncovered atherosclerosis complex cellular heterogeneity and a differentiated hierarchy of cell populations underlying SMC. The novel high-resolution stratification system could improve clinical outcomes and facilitate individualized management.

Text reproduced verbatim from Version of Record ([source](https://link.springer.com/article/10.1186/s12967-022-03795-9)); [DOI](https://doi.org/10.1186/s12967-022-03795-9); [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).

## Evidence Scale

**SMC fate / SCFDS: single-cell fate reconstruction and molecular subtyping of atherosclerosis**

An integrative human single-cell and multicohort transcriptomic study that reconstructs vascular smooth muscle cell fate states, derives the SMC cell fate decision signature (SCFDS), and uses it to define three biologically distinct retrospective molecular subtypes of atherosclerosis.

| Evidence | Value |
| --- | --- |
| single-cell donors | 4 cardiac transplant recipients with diseased right-coronary-artery segments |
| single cells after quality control | 11,756 |
| major plaque cell populations | 8 |
| SMCs analyzed in depth | 5,419 |
| SMC transcriptional clusters | 9 |
| SMC pseudotime states | 5 |
| SMC cell-fate leader genes | 1,072 |
| Mfuzz temporal gene modules | 8 |
| bulk transcriptomic scale reported in Abstract | 1,070 samples across six bulk cohorts |
| discovery cohort | GSE20680; 195 blood-expression samples stratified by coronary stenosis severity |
| SCFDS molecular subtypes | 3 |
| external NTP cohorts | 5 |

### Counting note

The article reports 1,070 bulk transcriptomic samples across six bulk cohorts in the Abstract, while the Methods states that 1,074 samples from seven independent public cohorts were enrolled and separately describes the four-donor single-cell dataset. Participants, longitudinal samples, bulk transcriptomic samples and single cells represent different counting units and are therefore preserved by modality rather than combined into a derived unique-participant total. The article also contains minor inconsistencies in cohort enumeration, so dataset-level provenance is reported explicitly.

## Research Question

Can vascular smooth muscle cell state transitions reconstructed from human atherosclerotic plaque single-cell RNA sequencing be translated into a reproducible transcriptomic stratification of atherosclerosis that captures distinct biological programs and differences in coronary stenosis severity?

## Author Evidence Summary

This study integrated human coronary-plaque single-cell RNA sequencing with multicohort bulk transcriptomics to examine whether vascular smooth muscle cell (SMC) differentiation states could explain molecular heterogeneity across atherosclerosis. In plaque single-cell data from four donors, 11,756 post-QC cells included 5,419 SMCs that were resolved into nine transcriptionally heterogeneous SMC clusters. Pseudotime analysis organized these SMCs into five computational differentiation states and yielded 1,072 cell-fate leader genes, from which eight temporal gene modules were identified and progression-associated modules were used to construct the SMC cell fate decision signature (SCFDS). When projected into bulk transcriptomic data, SCFDS supported three molecular subtypes with distinct biological profiles: C1, enriched for DNA-repair and replication programs; C2, characterized by immune and inflammatory activation and greater coronary stenosis severity; and C3, characterized by stromal and extracellular-matrix programs and lower stenosis severity in the discovery analysis. Nearest-template prediction reproduced the subtype expression structure across five external cohorts. These findings support a retrospective molecular framework linking SMC state-associated transcriptional programs with inter-individual atherosclerosis heterogeneity, but they do not establish prospective clinical utility, treatment benefit, or causal effects of SCFDS on clinical outcomes.

## Key Findings

### KF1: Human atherosclerotic plaques showed substantial vascular smooth muscle cell transcriptional heterogeneity.

Context: Single-cell profiling of diseased right-coronary-artery segments from four human donors

| Evidence | Value |
| --- | --- |
| single-cell donors | 4 |
| post-QC plaque cells | 11,756 |
| major plaque cell populations | 8 |
| SMCs analyzed | 5,419 |
| SMC clusters | 9 |

Source locator: Results: The landscapes of human atherosclerotic plaques revealed by scRNA-seq analysis, Fig. 2A; Results: SMC lineages' phenotypic and functional heterogeneity, Fig. 3A-E

### KF2: Pseudotime analysis organized plaque SMCs into a structured differentiation trajectory with distinct early, intermediate, and terminal state distributions.

Context: Monocle2 reconstruction of SMC state relationships

| Evidence | Value |
| --- | --- |
| pseudotime states | 5 |
| trajectory structure | five cellular states separated at two key time points |
| early-state enrichment | SMC4 and SMC6 |
| intermediate high-plasticity enrichment | SMC2, SMC5 and SMC7 |
| terminal-state enrichment | SMC1, SMC8 and SMC9 |
| phenotypic trend | contractile-like features declined; fibroblast-like markers increased through the middle-to-late trajectory before decreasing at the terminal end |

Source locator: Results: Trajectory reconstruction revealed SMC cell fate decisions, Fig. 4A-C

### KF3: SMC state-associated genes were distilled into the SMC cell fate decision signature (SCFDS).

Context: Integration of trajectory-ordering genes, state-associated genes, variable SMC genes, and temporal expression modules

| Evidence | Value |
| --- | --- |
| SMC cell-fate leader genes | 1,072 |
| Mfuzz temporal modules | 8 |
| SCFDS modules | Cluster 2 and Cluster 6, representing progressively upregulated and downregulated programs |
| upregulated SCFDS programs | extracellular matrix, inflammatory response and TGF-beta-related processes |
| downregulated SCFDS programs | vasculature development and AGE-RAGE-related processes |

Source locator: Results: Trajectory reconstruction revealed SMC cell fate decisions, Fig. 4D-H; Additional file 3: Table S1; Additional file 4: Table S2

### KF4: SCFDS-based analysis separated atherosclerosis into three molecular subtypes with distinct biology and different coronary stenosis patterns.

Context: Consensus molecular subtyping in the discovery bulk transcriptomic cohort

| Evidence | Value |
| --- | --- |
| optimal subtype number | 3 |
| C1 | DNA-damage repair type |
| C2 | immune-activated type |
| C3 | stromal-rich type |
| coronary stenosis association | C2 showed greater stenosis severity and C3 lower severity; p<0.05 in the discovery analysis |

Source locator: Results: The molecular subtyping of atherosclerosis based on cell fate decision signature, Fig. 5A-I; coronary stenosis comparison in Fig. 5E

### KF5: The three-subtype expression taxonomy was reproduced across five independent retrospective external transcriptomic cohorts using nearest-template prediction.

Context: Cross-cohort evaluation of subtype-specific expression templates

| Evidence | Value |
| --- | --- |
| template construction | top 300 subtype-specific upregulated genes per subtype |
| external cohorts | 5 |
| datasets shown in Fig. 6 | GSE20681, GSE21545, GSE59867, GSE62646 and GSE90074 |
| validation type | retrospective expression-template reproducibility across distinct platforms |

Source locator: Results: Performance of SCFDS subtypes verified by nearest template prediction, Fig. 6B-C

### KF6: The three SCFDS subtypes were associated with distinct molecular and plaque-microenvironment programs.

Context: Pathway enrichment and inferred cell-landscape analyses

| Evidence | Value |
| --- | --- |
| C1 programs | base-excision repair, DNA replication, nucleotide-excision repair and oxidative phosphorylation |
| C2 programs | stronger immune and inflammatory activation with a more complex inflammatory lesion environment |
| C3 programs | stromal/ECM metabolism, greater fibrous content and a relatively immune-suppressed microenvironment |

Source locator: Results: The molecular subtyping of atherosclerosis based on cell fate decision signature, Fig. 5G-I; Results: Assessment of multi-dimensional potential biological implications, Fig. 7A-G

## Study Design & Analytical Framework

### Study profile

- Study Design: Retrospective integrative multicohort transcriptomic and single-cell computational study
- Evidence Type: Human coronary-plaque single-cell RNA sequencing, bulk transcriptomics, pseudotime analysis, molecular subtyping, pathway analysis, inferred cellular microenvironment analysis, and retrospective clinical association
- Population: Human atherosclerosis and coronary artery disease samples spanning different degrees of coronary stenosis, stable coronary artery disease, and acute myocardial infarction, together with human coronary atherosclerotic plaque single-cell data
- Primary Endpoint: Identification of SMC cell-fate-associated transcriptional programs and SCFDS-based molecular subtypes of atherosclerosis
- Secondary Endpoint: Characterization of subtype biological programs, coronary stenosis associations, and cross-cohort expression-template reproducibility
- External dataset evaluation: Yes
- Data modalities: single-cell RNA sequencing, bulk transcriptomics, coronary stenosis phenotypes, clinical coronary disease states, pathway and cellular-microenvironment inference

## What This Study Adds

- Links cell-level SMC state heterogeneity to sample-level molecular heterogeneity by projecting a single-cell-derived fate signature into multicohort bulk transcriptomic data.
- Transforms continuous SMC state-associated transcriptional dynamics into a three-subtype molecular taxonomy that can be evaluated across independent cohorts.
- Provides a biologically interpretable framework connecting SMC fate-associated programs with immune, inflammatory, stromal and extracellular-matrix states and with coronary stenosis severity.
- Demonstrates a reusable analytical strategy for integrating human plaque single-cell data with larger transcriptomic cohorts while preserving the distinction between cellular states, molecular subtypes and clinical phenotypes.

## Evidence Scope

### Supports

- Human coronary atherosclerotic plaques contain substantial transcriptional heterogeneity among vascular smooth muscle cells.
- The analyzed SMC transcriptomes can be computationally organized into a pseudotime trajectory with five states and distinct cluster distributions.
- A 1,072-gene fate-leader set and temporal expression modules summarize SMC state-associated transcriptional programs in these data.
- SCFDS-based analysis identified three retrospective molecular subtypes with distinct DNA-repair, inflammatory/immune and stromal/ECM-associated profiles.
- C2 was associated with greater coronary stenosis severity and C3 with lower severity in the discovery analysis.
- The three-subtype expression-template structure was reproducible across five independent retrospective transcriptomic cohorts.
- SCFDS can serve as a research framework for studying SMC-related molecular heterogeneity in atherosclerosis.

### Does Not Establish

- That the nine SMC clusters are fixed biological lineages or clinically defined cell types.
- That pseudotime directly observes individual human SMCs transforming longitudinally within the same lesion.
- That all 1,072 fate-leader genes causally regulate SMC fate.
- That C1, C2 and C3 are prospectively validated clinical diagnostic or prognostic classes.
- That C2 causes coronary stenosis progression or that C3 causally protects against plaque progression or clinical events.
- That pathway enrichment or inferred cell-composition differences prove the underlying mechanisms.
- That retrospective NTP reproducibility is equivalent to prospective multicenter clinical validation.
- That SCFDS-guided treatment improves myocardial infarction, mortality or other clinical outcomes.
- That the therapeutic hypotheses discussed by the authors constitute validated treatment recommendations.

### Limitations

- The study was primarily computational and cannot fully recapitulate the diversity of developmental states or directly demonstrate longitudinal SMC lineage transitions in human plaques.
- The plaque single-cell analysis was based on four human donors, limiting direct generalization of cell-state frequencies.
- All samples used for subtype analyses were retrospective; prospective multicenter clinical validation was not performed.
- NTP validation demonstrates retrospective expression-template reproducibility rather than prospective diagnostic, prognostic or treatment-predictive performance.
- Pathway enrichment, xCell and related computational inference generate biological hypotheses but do not establish causal mechanisms.
- The article contains inconsistencies in sample/cohort enumeration and one external-cohort accession identifier; counts and dataset provenance should therefore be preserved explicitly rather than silently reconciled.

## Q&A

### How heterogeneous are vascular smooth muscle cells in human atherosclerotic plaques?

The study retained 11,756 post-QC plaque cells from four donors. Among 5,419 SMCs analyzed in depth, nine transcriptionally distinct SMC clusters were identified, with differences in contractile, inflammatory, matrix-associated and other state-related programs.

Evidence: KF1

### How were SMC fate transitions reconstructed in this study?

Monocle2 pseudotime analysis organized plaque SMCs into five computational differentiation states. SMC4 and SMC6 were enriched near the beginning of the trajectory, SMC2, SMC5 and SMC7 in intermediate high-plasticity states, and SMC1, SMC8 and SMC9 in terminal states.

Evidence: KF2

### What is the SMC cell fate decision signature (SCFDS)?

SCFDS was derived after identifying 1,072 SMC cell-fate leader genes and grouping them into eight temporal Mfuzz modules. Progressively upregulated and downregulated modules, identified as Cluster 2 and Cluster 6, were used to represent SMC cell-fate-associated transcriptional programs.

Evidence: KF3

### Can SMC fate-associated signatures define molecular subtypes of atherosclerosis?

In the retrospective discovery analysis, SCFDS supported three molecular subtypes: C1 DNA-damage repair type, C2 immune-activated type and C3 stromal-rich type. These subtypes showed distinct pathway and coronary stenosis patterns.

Evidence: KF4, KF6

### Which SCFDS subtype was associated with more severe coronary stenosis?

C2, the immune-activated subtype, showed greater coronary stenosis severity in the discovery analysis, whereas C3 showed lower severity. This was an association and does not establish that the subtype causes the difference in stenosis.

Evidence: KF4

### What biological programs distinguish C1, C2 and C3?

C1 was enriched for DNA-repair, replication and oxidative-phosphorylation programs; C2 for immune and inflammatory activation; and C3 for stromal, extracellular-matrix and fibrous programs with a relatively immune-suppressed microenvironment.

Evidence: KF6

### Were the SCFDS subtypes externally validated?

Their expression-template structure was evaluated by nearest-template prediction across five independent retrospective transcriptomic cohorts from different platforms. This supports cross-cohort reproducibility but is not prospective clinical validation.

Evidence: KF5

### Has SCFDS been prospectively validated for clinical decision-making or treatment selection?

No. The study was retrospective and primarily computational. The authors explicitly called for additional experimental validation and prospective multicenter studies before clinical relevance or treatment-guided utility can be established.

## Concepts & Entities

### Conditions

atherosclerosis, coronary artery disease, coronary stenosis, stable coronary artery disease, acute myocardial infarction

### Biological Processes

vascular smooth muscle cell phenotypic switching, SMC differentiation, SMC cell fate, plaque remodeling, atherosclerotic plaque microenvironment, extracellular matrix remodeling, inflammation

### Cell Types

vascular smooth muscle cells, monocytes/macrophages, endothelial cells, T cells, B cells, mast cells, plasma cells

### Smc Phenotypes

contractile-like SMC state, inflammatory SMC state, synthetic/ECM-associated SMC state, fibroblast-like SMC state

### Data Types

single-cell RNA sequencing, bulk transcriptomics, coronary stenosis phenotype

### Methods

Seurat, UMAP, CellChat, Monocle2, pseudotime analysis, Mfuzz, MOVICS, nearest template prediction, over-representation analysis, gene set enrichment analysis, GSVA, xCell

### Signature Taxonomy

SMC cell fate decision signature, SCFDS, C1 DNA-damage repair type, C2 immune-activated type, C3 stromal-rich type

### Representative Markers

ACTA2, MYH11, CNN1, TAGLN, ENG, NT5E

### Pathways

extracellular matrix, collagen signaling, CXCL signaling, TGF-beta signaling, inflammatory response, base-excision repair, DNA replication, nucleotide-excision repair, oxidative phosphorylation, AGE-RAGE signaling

### Datasets

SRP199578, GSE20680, GSE20681, GSE21545, GSE59867, GSE62646, GSE90074

## Related Research

- [Atherosclerotic plaque vulnerability quantification system for clinical and biological interpretability](https://drgezhang.com/papers/apvs.html) — Extends the broader atherosclerosis molecular-heterogeneity theme toward quantitative plaque-vulnerability assessment through the APVS/APVSLevel multicohort and single-cell framework. (DOI: 10.1016/j.isci.2023.107587)
- [Vascular smooth muscle cell-derived KIF13B inhibits proinflammatory responses to protect against atherosclerosis](https://drgezhang.com/papers/doi-10-1172-jci194175.html) — Provides later mechanistic evidence on vascular smooth-muscle-cell phenotypic regulation and inflammatory-state control in atherosclerosis; it is complementary mechanistic evidence rather than direct validation of SCFDS. (DOI: 10.1172/jci194175)
- [The macrophage-derived motor protein KIF13B enhances MERTK-mediated efferocytosis and prevents atherosclerosis in mice](https://drgezhang.com/papers/doi-10-1093-eurheartj-ehaf523.html) — Complements the SMC-centered taxonomy with a macrophage-centered atherosclerosis mechanism involving efferocytosis and inflammatory resolution in the plaque microenvironment. (DOI: 10.1093/eurheartj/ehaf523)

## Publication & Provenance

- DOI: https://doi.org/10.1186/s12967-022-03795-9
- Publisher: https://link.springer.com/article/10.1186/s12967-022-03795-9
- PubMed: https://pubmed.ncbi.nlm.nih.gov/36474294/
- PMCID: PMC9724432
- Doi Url: https://doi.org/10.1186/s12967-022-03795-9
- Version Of Record: Journal of Translational Medicine, Volume 20, Article 568, published 6 December 2022
- License: Creative Commons Attribution 4.0 International License
- Single Cell Source: SRP199578; diseased right-coronary-artery segments from four cardiac transplant recipients
- Bulk Discovery: GSE20680; 195 samples stratified by coronary stenosis. The article Methods describes these as PBMC samples, whereas the GEO accession describes whole-blood cell expression profiling.
- External Cohorts: GSE20681; GSE21545; GSE59867; GSE62646; GSE90074
- Supplementary Material: Additional file 1: Figure S1, single-cell RNA-seq quality control; Additional file 2: Figure S2, plaque cell-type mapping; Additional file 3: Table S1, SMC cell-fate leader genes; Additional file 4: Table S2, Mfuzz gene modules
- Ethics: Ethics Committee of the First Affiliated Hospital of Zhengzhou University, approval 2021-KY-0720; analyzed source data were mainly obtained from public databases
- Source Note Counting: The Abstract reports 1,070 bulk samples across six bulk cohorts, whereas the Methods states 1,074 samples across seven independent public cohorts while separately describing the four-donor single-cell dataset. Counts are preserved by modality and are not collapsed into a derived unique-participant total.
- Source Note Sample Type: For GSE20680, the article Methods uses the term PBMC samples, whereas the NCBI GEO record describes whole-blood cell gene-expression profiling. This evidence page preserves the discrepancy rather than silently harmonizing the sample type.
- Source Note Accession: The Results narrative contains GSE26081 once, whereas Fig. 6 identifies GSE20681. NCBI GEO confirms GSE20681 as the PREDICT coronary artery disease dataset; GSE26081 is an unrelated breast-cancer ER-alpha dataset. This evidence page therefore uses GSE20681 while retaining the discrepancy in provenance.
- Evidence Basis: Version of record, PMC full text, PubMed record, supplementary information, and NCBI GEO records

## Evidence-page notice

Author-controlled evidence page for this publication. This page provides an evidence-oriented summary and does not replace the publisher's version of record.

## Links

- DOI: https://doi.org/10.1186/s12967-022-03795-9
- HTML page: https://drgezhang.com/papers/smc-fate.html
- Google Scholar query: https://scholar.google.com/scholar?q=%22Smooth%20muscle%20cell%20fate%20decisions%20decipher%20a%20high-resolution%20heterogeneity%20within%20atherosclerosis%20molecular%20subtypes%22
- ORCID: https://orcid.org/0000-0002-3116-3246
