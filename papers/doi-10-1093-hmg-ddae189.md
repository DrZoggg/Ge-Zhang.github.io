# Integrated multi-omics analysis revealed the molecular networks and potential targets of cellular senescence in Alzheimer’s disease

Researcher: Ge Zhang
Chinese name: 张格
ORCID identity anchor: https://orcid.org/0000-0002-3116-3246
Canonical researcher: https://drgezhang.com/#person

Journal: Human Molecular Genetics
Year: 2024
Type: Article
DOI: 10.1093/hmg/ddae189
Canonical page: https://drgezhang.com/papers/doi-10-1093-hmg-ddae189.html
Markdown record: https://drgezhang.com/papers/doi-10-1093-hmg-ddae189.md

## Full Authors

1. Yudi Xu
2. Shutong Liu
3. Zhaokai Zhou
4. Hongzhuo Qin
5. Yuyuan Zhang
6. Ge Zhang
7. Hongxuan Ma
8. Xinwei Han
9. Huimin Liu
10. Zaoqu Liu

<a id="limited-evidence"></a>

<a id="paper-discovery"></a>
## Research & review context

### Research fields

- Alzheimer’s disease biology
- Genetic target prioritization

### Review topics

- Senescence-related blood and brain expression
- Cis-QTL evidence and cell-line follow-up

### Scientific role

Original integrative study combining public expression screens, genetic association prioritization and PC12 expression measurements.

### Evidence position

Retrospective human expression, summary-level genetic estimates and a rat cell-line expression assay. Source-specific denominator and mediation disagreements are locatable.

### Related concepts

- CDKN2B
- ITGAV
- Instrument validity

### Possible citation contexts

- Discussion of tissue-specific senescence-related AD candidate genes with MR and colocalization qualifications.
- Evidence reviews distinguishing genetic prioritization and cellular expression changes from validated clinical targets.

Possible literature-review contexts, not evidence of existing citations. Read the findings and Evidence Scope before citing the original article.

## Evidence Scale

**Integrated multi-omics analysis revealed the molecular networks and potential targets of cellular senescence in Alzheimer’s disease**

Separate blood and brain expression screens and cis-QTL analyses prioritized senescence-related Alzheimer’s disease candidates. The authors highlighted five blood-expression genes and two brain-expression genes. CDKN2B and ITGAV expression also rose in an amyloid-β-exposed PC12 cell comparison. The source reports two different denominators under the same FinnGen R9 label, so the genetic estimates are attributed to their specific figures and tables.

| Evidence | Value |
| --- | --- |
| Blood expression dataset | GSE63061: 139 AD and 134 controls |
| Brain expression dataset | GSE33000: 310 AD and 157 controls |
| Supporting blood score comparison | GSE63060: 145 AD and 104 controls, reported in Table S10/Figure S1 |
| QTL resources | Blood eQTLGen 31,684; blood mQTL 1,980; brain eQTL 1,194; brain mQTL 1,160, as reported in Table S10 |
| GWAS denominator | FinnGen G6_ALZHEIMER, labelled R9. Methods/Table S10 report 9,301 cases and 367,976 controls. STROBE-MR item 4d reports 7,759 cases and 334,740 controls. The actual analyzed input remains unidentified. |
| Experimental setting | PC12 cells, 7 μM Aβ1-42, 12 hours |

### Counting note

Expression subsets, QTL source samples, version-labelled GWAS counts and laboratory measurements describe separate evidence units. The expression screens’ 113/410 candidates precede the supplementary eQTL test rows. The cell-assay workbook does not specify biological independence.

## Research Question

Which senescence-related genes show convergent expression and genetic-association signals in Alzheimer’s disease, and how far do the accompanying PC12 expression experiments support those candidates?

## Author Evidence Summary

The study integrates public blood and postmortem cortex transcriptomics, summary-level genetic associations, colocalization and a focused PC12 expression experiment. CENPW, SLFN12 and CDKN2B met the paper’s PPH4 > 0.5 colocalization threshold in their expression analyses, and SLFN12 also showed instrument heterogeneity. CDKN2B and ITGAV were followed up in the cell model. Conflicting FinnGen denominators and proposed mediation annotations are identified at their original source locations.

## Key Findings

<a id="kf1"></a>
### KF1: Separate blood and brain expression screens identified 113 and 410 direction-concordant senescence-related candidates.

Context: Candidate expression changes were aligned with the labelled CellAge signature. A GSVA difference score compares the up- and down-regulated signature sets. Figure S1 shows the blood comparisons in GSE63060 and GSE63061.

| Evidence | Value |
| --- | --- |
| Senescence signature | 1,259 genes: 525 labelled up and 734 labelled down |
| Blood expression screen | GSE63061: 139 AD and 134 controls; 113 direction-consistent candidates |
| Brain expression screen | GSE33000: 310 AD and 157 controls; 410 direction-consistent candidates |
| Supporting blood score comparison | Figure S1 plots higher AD scores in GSE63060 (145 AD and 104 controls, P=1.6×10⁻⁸) and GSE63061 (139 AD and 134 controls, P=5.5×10⁻⁵). |

Source locator: Publisher advance-article PDF pp. 2 and 5 (Differentially expressed CS genes from blood/brain), pp. 8-9 (Data source and processing; Cellular senescence score calculation); Figures 1, 2A and 4A; supplementary_table_ddae189.xlsx, Supplementary Tables 9-10; supplementary_figure_ddae189.docx, Figure S1.

<a id="kf2"></a>
### KF2: The blood eQTL analysis highlighted five direction-concordant genes with different colocalization results.

Context: Figure 2C and Table S1 report estimates from the study’s summary-level MR analysis. The five highlighted genes also meet its expression-direction criterion. SLFN12 has a significant IVW Cochran Q result even though its colocalization posterior exceeds the authors’ cutoff.

| Evidence | Value |
| --- | --- |
| Lower-odds estimates | CENPW OR 0.56 (95% CI 0.41-0.75); EXOSC9 0.89 (0.84-0.95); HSPB11 0.71 (0.55-0.91) |
| Higher-odds estimates | SLC44A2 OR 1.09 (1.04-1.13); SLFN12 1.13 (1.04-1.24) |
| Colocalization qualification | At the authors' PPH4 > 0.5 threshold, CENPW 0.554 and SLFN12 0.876 pass; EXOSC9 0.023, HSPB11 0.034 and SLC44A2 0.047 do not |
| Heterogeneity qualification | SLFN12 IVW Cochran Q P = 4.29e-5 in Table S2; it is not a uniformly consistent set of instruments |
| Tested rows and FDR | Table S1 lists 94 tested gene rows, with 13 adjusted P values below 0.05. Figure 2 highlights five direction-concordant genes. |

Source locator: Publisher advance-article PDF p. 2 (Integration analysis from blood), p. 4 Figure 2C-I; supplementary_table_ddae189.xlsx, Supplementary Table 1 rows 15, 42, 49, 83 and 93 and Supplementary Table 2 rows 3-11; Table 9 supplies the expression-direction categories.

<a id="kf3"></a>
### KF3: The brain eQTL analysis highlighted CDKN2B and ITGAV, with stronger reported colocalization for CDKN2B.

Context: Figure 4C and Table S4 report higher AD odds estimates for both genes. CDKN2B uses a single-SNP Wald ratio. ITGAV uses a five-SNP IVW estimate. Figure S5 shows higher expression for both genes in the same GSE33000 brain dataset.

| Evidence | Value |
| --- | --- |
| CDKN2B | OR 1.28 (95% CI 1.10-1.48); FDR 0.0459; Wald ratio using rs490005; PPH4 0.607 |
| ITGAV | OR 1.09 (1.04-1.14); FDR 0.0284; IVW using 5 SNPs; PPH4 0.452 |
| Tested rows and FDR | Table S4 lists 170 tested gene rows and four adjusted P values below 0.05. The Results report 179 genes after instrument selection and highlight two direction-concordant genes. The source does not explain the difference between 179 and 170. |

Source locator: Publisher advance-article PDF p. 5 (Integration analysis from brain), p. 7 Figure 4C; supplementary_table_ddae189.xlsx, Supplementary Table 4 rows 22 and 71 and Supplementary Table 5 rows 3-4; Table 9 supplies the expression-direction categories. Supplementary Figure S5 records the display from GSE33000.

<a id="kf4"></a>
### KF4: Separate blood and brain methylation screens identified candidate probes, and the reported blood mediation annotations disagree across figures.

Context: The three-step analysis links methylation, expression and AD in the authors’ proposed blood pathways. The directly reported probe associations can be used with their table locators. Specific EXOSC9/SLFN12 mediation coefficients remain unresolved.

| Evidence | Value |
| --- | --- |
| Blood methylation results | 18 FDR-positive probes across 7 genes in Table 1 and Table S3 |
| Brain methylation results | 15 FDR-positive probes across 6 genes in Table S6; no corresponding expression/methylation intersection reported for step 3 |
| EXOSC9 probe identity | Figure 1 labels cg25588844 on the arrow into the candidate group containing EXOSC9. Table 1, Figure 3C and Figure S3 label the EXOSC9 probe cg06713675. |
| Expression-to-AD coefficients | EXOSC9 β is −0.01 in the p. 3 narrative/Figure 3C, −0.11 in Figure 2C and −0.112 in Table S1. Figure 3D labels the SLFN12 link −0.01, while Figure 2C and Table S1 show +0.12 and +0.125 respectively. |

Source locator: Publisher advance-article PDF pp. 2 and 5 (blood/brain cis-mQTL analyses), p. 5 Table 1, pp. 6-7 Figures 3B and 4D; supplementary_table_ddae189.xlsx, Supplementary Tables 3 and 6; supplementary_figure_ddae189.docx, Figures S2-S4. Figures 1 and 3C-D contain unresolved mediation annotations.

<a id="kf5"></a>
### KF5: The cell experiments reported increased CDKN2B and ITGAV expression after amyloid-beta exposure in PC12 cells.

Context: Methods and Figure 4 identify PC12 cells. The Results wording refers to AD neurons. The recorded measurements support the direction of change, and the ITGAV qPCR fold scale differs between Supplementary Table S7 and Figure 4F.

| Evidence | Value |
| --- | --- |
| Exposure | Aβ1-42 at 7 μM for 12 hours |
| Readouts | qPCR for CDKN2B and ITGAV; Western blots normalized to β-actin |
| Recorded measurements | Table S7 lists 4 values per group for each qPCR target; Table S8 lists 3 labelled entries per group for protein quantification; independence of biological repeats is not specified |
| Reported direction and scale | CDKN2B and ITGAV mRNA and protein signals were higher in the exposed PC12 group. The ITGAV qPCR plot and worksheet have different fold scales, so use the direction with its assay locator. |

Source locator: Publisher advance-article PDF p. 5 (Validation of the target genes expression), p. 7 Figure 4E-G, p. 9 (PC12 cell culture; qPCR; Western blot); supplementary_table_ddae189.xlsx, Supplementary Table 7 rows 2-12 and Supplementary Table 8 rows 2-26; supplementary_figure_ddae189.docx, Figures S5-S6.

<a id="kf6"></a>
### KF6: The Methods and the STROBE-MR supplement report different AD GWAS denominators under the same FinnGen R9 label.

Context: The official R9 endpoint independently lists the Methods case count after genotype quality control. The endpoint page does not identify the exact summary-statistic input used in this paper or give the matching control total.

| Evidence | Value |
| --- | --- |
| Article Methods and Supplementary Table S10 | FinnGen R9 G6_ALZHEIMER, 9,301 cases and 367,976 controls. |
| Supplementary STROBE-MR checklist item 4d | finngen_R9_G6_ALZHEIMER, 7,759 cases and 334,740 controls. |
| Official R9 endpoint documentation | G6_ALZHEIMER lists 9,301 cases. The analyzed input file and denominator remain unresolved. |

Source locator: Publisher advance-article PDF p. 8, GWAS data for Alzheimer’s disease; Supplementary Table S10, FinnGen AD outcome row; supplementary_materials_ddae189.docx, STROBE-MR item 4d; FinnGen R9 Risteys endpoint G6_ALZHEIMER.

## Study Design & Analytical Framework

### Study profile

- Study Design: Retrospective public transcriptomic screening with cis-eQTL/cis-mQTL two-sample Mendelian randomization, colocalization and a PC12 expression experiment.
- Evidence Type: Human observational expression data, summary-level genetic prioritization and nonclinical cellular expression measurements.
- Population: Public blood and postmortem prefrontal cortex AD/control datasets; predominantly European-ancestry QTL and FinnGen outcome resources; PC12 rat pheochromocytoma-derived cells for the laboratory comparison.
- Primary Endpoint: Association of genetically instrumented gene expression or methylation with the AD GWAS outcome.
- Secondary Endpoint: Senescence-related expression screening, colocalization, and CDKN2B/ITGAV mRNA and protein expression after Aβ1-42 exposure.
- External dataset evaluation: No
- Data modalities: Blood and brain expression microarrays, cis-eQTL and cis-mQTL summary associations, FinnGen AD GWAS summary associations, Bayesian colocalization and instrument heterogeneity assessment, PC12 qPCR and Western-blot expression measurements

## What This Study Adds

- Tissue-specific target prioritization that relates a labelled senescence signature to human blood and postmortem brain expression changes.
- Gene-level comparisons of cis-QTL estimates, likelihood of colocalization and instrument heterogeneity.
- Cellular follow-up for two brain candidates, measuring expression under a specified amyloid-β exposure.

## Evidence Scope

### Supports

- Reported case-control expression patterns in the named blood and brain datasets.
- Source-attributed estimates for the highlighted eQTL and methylation candidates.
- CDKN2B and ITGAV expression observations from the specified PC12 model.

### Does Not Establish

- Exact identity of the GWAS run input or complete EXOSC9/SLFN12 mediation chains.
- Prospective diagnostic performance, human treatment benefit or target-specific functional rescue.

### Limitations

- MR interpretation depends on instrument relevance, independence and exclusion restriction, plus LD and ancestry assumptions. Colocalization and Cochran Q describe properties of the reported analyses.
- The FinnGen denominator, certain mediation annotations and the ITGAV qPCR fold scale disagree across original sources. Each affected finding identifies the competing sources.
- The PC12 assay measures expression. Supplementary Tables S7–S8 do not identify independent biological repeats; Supplementary Table S11 does not list the stated GAPDH reference primer and the printed CDKN2B reverse-primer sequence includes an ambiguous character.

<a id="citation-use-cases"></a>
## When This Study Is Useful to Cite

### CU1: Which senescence-related genes were highlighted by the blood and brain AD analyses?

The direction-concordant candidate subsets, with their published MR and colocalization qualifications.

Evidence: [KF1](#kf1), [KF2](#kf2), [KF3](#kf3)

### CU2: What supports the proposed methylation mechanisms?

Use the blood and brain methylation screens with their specific probe or table locator. Conflicting mediation annotations remain unresolved.

Evidence: [KF4](#kf4)

### CU3: What experimental follow-up was performed for CDKN2B and ITGAV?

Cite the direction of CDKN2B/ITGAV mRNA and protein expression in the Aβ1–42-exposed PC12 comparison.

Evidence: [KF5](#kf5)

### CU4: Which FinnGen Alzheimer’s disease denominator can be cited for this study?

Report the source-specific counts and retain the analyzed-input uncertainty.

Evidence: [KF6](#kf6)

<a id="citation-boundaries"></a>
## What This Study Should Not Be Cited to Claim

- An exact reconstructed FinnGen input, a settled EXOSC9/SLFN12 mediation pathway or an exact ITGAV qPCR fold effect.
- A clinical diagnostic test, intervention effect or evidence of neuronal rescue.

<a id="evidence-matrix"></a>
## Evidence Matrix

<a id="evidence-hmg-senescence-1"></a>
### Separate blood and brain expression screens identified 113 and 410 direction-concordant senescence-related candidates.

- Context: Candidate expression changes were aligned with the labelled CellAge signature. A GSVA difference score compares the up- and down-regulated signature sets. Figure S1 shows the blood comparisons in GSE63060 and GSE63061.
- Finding: Senescence signature: 1,259 genes: 525 labelled up and 734 labelled down; Blood expression screen: GSE63061: 139 AD and 134 controls; 113 direction-consistent candidates; Brain expression screen: GSE33000: 310 AD and 157 controls; 410 direction-consistent candidates; Supporting blood score comparison: Figure S1 plots higher AD scores in GSE63060 (145 AD and 104 controls, P=1.6×10⁻⁸) and GSE63061 (139 AD and 134 controls, P=5.5×10⁻⁵).
- Evidence Level: Retrospective expression and summary-level genetic evidence
- Scope: Candidate expression changes were aligned with the labelled CellAge signature. A GSVA difference score compares the up- and down-regulated signature sets. Figure S1 shows the blood comparisons in GSE63060 and GSE63061.
- Source Locator: Publisher advance-article PDF pp. 2 and 5 (Differentially expressed CS genes from blood/brain), pp. 8-9 (Data source and processing; Cellular senescence score calculation); Figures 1, 2A and 4A; supplementary_table_ddae189.xlsx, Supplementary Tables 9-10; supplementary_figure_ddae189.docx, Figure S1.
- Evidence refs: [KF1](#kf1)

<a id="evidence-hmg-senescence-2"></a>
### The blood eQTL analysis highlighted five direction-concordant genes with different colocalization results.

- Context: Figure 2C and Table S1 report estimates from the study’s summary-level MR analysis. The five highlighted genes also meet its expression-direction criterion. SLFN12 has a significant IVW Cochran Q result even though its colocalization posterior exceeds the authors’ cutoff.
- Finding: Lower-odds estimates: CENPW OR 0.56 (95% CI 0.41-0.75); EXOSC9 0.89 (0.84-0.95); HSPB11 0.71 (0.55-0.91); Higher-odds estimates: SLC44A2 OR 1.09 (1.04-1.13); SLFN12 1.13 (1.04-1.24); Colocalization qualification: At the authors' PPH4 > 0.5 threshold, CENPW 0.554 and SLFN12 0.876 pass; EXOSC9 0.023, HSPB11 0.034 and SLC44A2 0.047 do not; Heterogeneity qualification: SLFN12 IVW Cochran Q P = 4.29e-5 in Table S2; it is not a uniformly consistent set of instruments; Tested rows and FDR: Table S1 lists 94 tested gene rows, with 13 adjusted P values below 0.05. Figure 2 highlights five direction-concordant genes.
- Evidence Level: Retrospective expression and summary-level genetic evidence
- Scope: Figure 2C and Table S1 report estimates from the study’s summary-level MR analysis. The five highlighted genes also meet its expression-direction criterion. SLFN12 has a significant IVW Cochran Q result even though its colocalization posterior exceeds the authors’ cutoff.
- Source Locator: Publisher advance-article PDF p. 2 (Integration analysis from blood), p. 4 Figure 2C-I; supplementary_table_ddae189.xlsx, Supplementary Table 1 rows 15, 42, 49, 83 and 93 and Supplementary Table 2 rows 3-11; Table 9 supplies the expression-direction categories.
- Evidence refs: [KF2](#kf2)

<a id="evidence-hmg-senescence-3"></a>
### The brain eQTL analysis highlighted CDKN2B and ITGAV, with stronger reported colocalization for CDKN2B.

- Context: Figure 4C and Table S4 report higher AD odds estimates for both genes. CDKN2B uses a single-SNP Wald ratio. ITGAV uses a five-SNP IVW estimate. Figure S5 shows higher expression for both genes in the same GSE33000 brain dataset.
- Finding: CDKN2B: OR 1.28 (95% CI 1.10-1.48); FDR 0.0459; Wald ratio using rs490005; PPH4 0.607; ITGAV: OR 1.09 (1.04-1.14); FDR 0.0284; IVW using 5 SNPs; PPH4 0.452; Tested rows and FDR: Table S4 lists 170 tested gene rows and four adjusted P values below 0.05. The Results report 179 genes after instrument selection and highlight two direction-concordant genes. The source does not explain the difference between 179 and 170.
- Evidence Level: Retrospective expression and summary-level genetic evidence
- Scope: Figure 4C and Table S4 report higher AD odds estimates for both genes. CDKN2B uses a single-SNP Wald ratio. ITGAV uses a five-SNP IVW estimate. Figure S5 shows higher expression for both genes in the same GSE33000 brain dataset.
- Source Locator: Publisher advance-article PDF p. 5 (Integration analysis from brain), p. 7 Figure 4C; supplementary_table_ddae189.xlsx, Supplementary Table 4 rows 22 and 71 and Supplementary Table 5 rows 3-4; Table 9 supplies the expression-direction categories. Supplementary Figure S5 records the display from GSE33000.
- Evidence refs: [KF3](#kf3)

<a id="evidence-hmg-senescence-4"></a>
### Separate blood and brain methylation screens identified candidate probes, and the reported blood mediation annotations disagree across figures.

- Context: The three-step analysis links methylation, expression and AD in the authors’ proposed blood pathways. The directly reported probe associations can be used with their table locators. Specific EXOSC9/SLFN12 mediation coefficients remain unresolved.
- Finding: Blood methylation results: 18 FDR-positive probes across 7 genes in Table 1 and Table S3; Brain methylation results: 15 FDR-positive probes across 6 genes in Table S6; no corresponding expression/methylation intersection reported for step 3; EXOSC9 probe identity: Figure 1 labels cg25588844 on the arrow into the candidate group containing EXOSC9. Table 1, Figure 3C and Figure S3 label the EXOSC9 probe cg06713675.; Expression-to-AD coefficients: EXOSC9 β is −0.01 in the p. 3 narrative/Figure 3C, −0.11 in Figure 2C and −0.112 in Table S1. Figure 3D labels the SLFN12 link −0.01, while Figure 2C and Table S1 show +0.12 and +0.125 respectively.
- Evidence Level: Retrospective expression and summary-level genetic evidence
- Scope: The three-step analysis links methylation, expression and AD in the authors’ proposed blood pathways. The directly reported probe associations can be used with their table locators. Specific EXOSC9/SLFN12 mediation coefficients remain unresolved.
- Source Locator: Publisher advance-article PDF pp. 2 and 5 (blood/brain cis-mQTL analyses), p. 5 Table 1, pp. 6-7 Figures 3B and 4D; supplementary_table_ddae189.xlsx, Supplementary Tables 3 and 6; supplementary_figure_ddae189.docx, Figures S2-S4. Figures 1 and 3C-D contain unresolved mediation annotations.
- Evidence refs: [KF4](#kf4)

<a id="evidence-hmg-senescence-5"></a>
### The cell experiments reported increased CDKN2B and ITGAV expression after amyloid-beta exposure in PC12 cells.

- Context: Methods and Figure 4 identify PC12 cells. The Results wording refers to AD neurons. The recorded measurements support the direction of change, and the ITGAV qPCR fold scale differs between Supplementary Table S7 and Figure 4F.
- Finding: Exposure: Aβ1-42 at 7 μM for 12 hours; Readouts: qPCR for CDKN2B and ITGAV; Western blots normalized to β-actin; Recorded measurements: Table S7 lists 4 values per group for each qPCR target; Table S8 lists 3 labelled entries per group for protein quantification; independence of biological repeats is not specified; Reported direction and scale: CDKN2B and ITGAV mRNA and protein signals were higher in the exposed PC12 group. The ITGAV qPCR plot and worksheet have different fold scales, so use the direction with its assay locator.
- Evidence Level: Nonclinical expression assay
- Scope: Methods and Figure 4 identify PC12 cells. The Results wording refers to AD neurons. The recorded measurements support the direction of change, and the ITGAV qPCR fold scale differs between Supplementary Table S7 and Figure 4F.
- Source Locator: Publisher advance-article PDF p. 5 (Validation of the target genes expression), p. 7 Figure 4E-G, p. 9 (PC12 cell culture; qPCR; Western blot); supplementary_table_ddae189.xlsx, Supplementary Table 7 rows 2-12 and Supplementary Table 8 rows 2-26; supplementary_figure_ddae189.docx, Figures S5-S6.
- Evidence refs: [KF5](#kf5)

<a id="evidence-hmg-senescence-6"></a>
### The Methods and the STROBE-MR supplement report different AD GWAS denominators under the same FinnGen R9 label.

- Context: The official R9 endpoint independently lists the Methods case count after genotype quality control. The endpoint page does not identify the exact summary-statistic input used in this paper or give the matching control total.
- Finding: Article Methods and Supplementary Table S10: FinnGen R9 G6_ALZHEIMER, 9,301 cases and 367,976 controls.; Supplementary STROBE-MR checklist item 4d: finngen_R9_G6_ALZHEIMER, 7,759 cases and 334,740 controls.; Official R9 endpoint documentation: G6_ALZHEIMER lists 9,301 cases. The analyzed input file and denominator remain unresolved.
- Evidence Level: Source-specific input documentation
- Scope: The official R9 endpoint independently lists the Methods case count after genotype quality control. The endpoint page does not identify the exact summary-statistic input used in this paper or give the matching control total.
- Source Locator: Publisher advance-article PDF p. 8, GWAS data for Alzheimer’s disease; Supplementary Table S10, FinnGen AD outcome row; supplementary_materials_ddae189.docx, STROBE-MR item 4d; FinnGen R9 Risteys endpoint G6_ALZHEIMER.
- Evidence refs: [KF6](#kf6)

## Q&A

### How do the five blood and two brain candidates relate to the eQTL test tables?

Table S1 has 94 tested rows and 13 adjusted P values below 0.05. Table S4 has 170 tested rows and four below 0.05. The Results report 179 brain genes after instrument selection and do not explain the difference from the table. The article highlights the five blood and two brain expression candidates with concordant directions.

Evidence: KF2, KF3

Source locator: supplementary_table_ddae189.xlsx: Supplementary Tables 1, 4 and 9; main Figures 2C and 4C.

### Which blood genes are highlighted?

Figure 2C reports ORs below one for CENPW, EXOSC9 and HSPB11, and above one for SLC44A2 and SLFN12. CENPW (PPH4 0.554) and SLFN12 (0.876) cross the study cutoff. SLFN12 also shows significant IVW heterogeneity (Table S2, Q P=4.29×10⁻⁵).

Evidence: KF2

Source locator: Publisher advance-article PDF p. 2 (Integration analysis from blood), p. 4 Figure 2C-I; supplementary_table_ddae189.xlsx, Supplementary Table 1 rows 15, 42, 49, 83 and 93 and Supplementary Table 2 rows 3-11; Table 9 supplies the expression-direction categories.

### How do CDKN2B and ITGAV differ genetically?

Reported ORs are 1.28 for CDKN2B and 1.09 for ITGAV. CDKN2B uses the rs490005 Wald ratio and has PPH4 0.607. ITGAV uses a five-SNP IVW model and has PPH4 0.452. The latter is below the study’s colocalization cutoff of 0.5.

Evidence: KF3

Source locator: Publisher advance-article PDF p. 5 (Integration analysis from brain), p. 7 Figure 4C; supplementary_table_ddae189.xlsx, Supplementary Table 4 rows 22 and 71 and Supplementary Table 5 rows 3-4; Table 9 supplies the expression-direction categories.

### How were the gene expression MR and colocalization estimates produced?

The Methods specify TwoSampleMR, a Wald ratio for one instrument and inverse-variance weighting for multiple instruments, plus coloc for region-level colocalization. The instrument criteria include P < 5×10⁻⁶ and LD clumping at r² < 0.1. The SMR resource provides QTL data.

Evidence: KF2, KF3

Source locator: Publisher PDF p. 9, Mendelian randomization analysis and Colocalization analysis; p. 10, Data availability; Table S10.

### What supports the methylation analysis, and where do the annotations disagree?

The reported methylation screens contain 18 blood probes across seven genes and 15 brain probes across six. The EXOSC9 probe identity and EXOSC9/SLFN12 expression-to-AD coefficients differ across Figures 1, 2C and 3C–D, Table 1, Table S1 and Figure S3. These discrepancies limit mechanistic interpretation of the proposed mediation paths.

Evidence: KF4

Source locator: Publisher advance-article PDF pp. 2 and 5 (blood/brain cis-mQTL analyses), p. 5 Table 1, pp. 6-7 Figures 3B and 4D; supplementary_table_ddae189.xlsx, Supplementary Tables 3 and 6; supplementary_figure_ddae189.docx, Figures S2-S4. Figures 1 and 3C-D contain unresolved mediation annotations.

### Which cell model was used to examine CDKN2B and ITGAV?

The Methods and Figure 4 identify rat-derived PC12 cells treated with 7 μM Aβ1–42 for 12 hours. The source’s reference to AD neurons in the Results does not identify another human cell experiment.

Evidence: KF5

Source locator: Publisher advance-article PDF p. 5 (Validation of the target genes expression), p. 7 Figure 4E-G, p. 9 (PC12 cell culture; qPCR; Western blot); supplementary_table_ddae189.xlsx, Supplementary Table 7 rows 2-12 and Supplementary Table 8 rows 2-26; supplementary_figure_ddae189.docx, Figures S5-S6.

### What changed in the PC12 expression comparison?

CDKN2B and ITGAV mRNA and protein signals were higher after Aβ1–42 exposure. The qPCR table records four measurements per group and target. The protein sheet records three labelled measurements per group. The biological independence of those measurements is unspecified. Figure 4F and Table S7 disagree on the ITGAV qPCR fold scale.

Evidence: KF5

Source locator: Publisher advance-article PDF p. 5 (Validation of the target genes expression), p. 7 Figure 4E-G, p. 9 (PC12 cell culture; qPCR; Western blot); supplementary_table_ddae189.xlsx, Supplementary Table 7 rows 2-12 and Supplementary Table 8 rows 2-26; supplementary_figure_ddae189.docx, Figures S5-S6.

### Which denominator is documented for the FinnGen AD outcome?

Methods and Table S10 give 9,301 cases and 367,976 controls. STROBE-MR item 4d gives 7,759 and 334,740 under the same R9 label. Official R9 Risteys lists 9,301 cases. It does not identify the file analyzed in the paper.

Evidence: KF6

Source locator: Publisher advance-article PDF p. 8, GWAS data for Alzheimer’s disease; Supplementary Table S10, FinnGen AD outcome row; supplementary_materials_ddae189.docx, STROBE-MR item 4d; FinnGen R9 Risteys endpoint G6_ALZHEIMER.

### How can these results inform Alzheimer’s disease research?

They provide tissue-specific candidates for studying relationships among senescence-associated expression, genetic associations and Aβ1–42 exposure. Report the relevant tissue and assay and distinguish the candidate association from clinical validation. Cite the original study for its results and use the linked figure or table for the specific observation.

Evidence: KF1, KF2, KF3, KF5

Source locator: Publisher PDF pp. 8-9, Discussion limitations and Materials and Methods; Figures 2 and 4.

## Concepts & Entities

### Disease And Process

Alzheimer’s disease, Cellular senescence, Blood and brain expression

### Genetic Methods

cis-QTL Mendelian randomization, Colocalization, Instrument heterogeneity

### Experimental Context

PC12 cells, Aβ1-42 exposure, CDKN2B and ITGAV expression

## Related Research

- [ABCA1 acts as a protective modulator in amyotrophic lateral sclerosis](https://drgezhang.com/papers/doi-10-1016-j-isci-2025-114320.html) — An independent neurodegeneration study combining transcriptomic analysis with genetic prioritization; its ALS/ABCA1 evidence does not validate AD candidate mechanisms. (DOI: 10.1016/j.isci.2025.114320)

## Publication & Provenance

- DOI: https://doi.org/10.1093/hmg/ddae189
- Doi Url: https://doi.org/10.1093/hmg/ddae189
- Publisher: https://academic.oup.com/hmg/article/34/5/381/7926367
- PubMed: https://pubmed.ncbi.nlm.nih.gov/39690817/
- Supplementary Data Url: https://academic.oup.com/hmg/article/34/5/381/7926367#supplementary-data
- Finngen R9 Alzheimer Endpoint Url: https://r9.risteys.finngen.fi/endpoints/G6_ALZHEIMER
- Blood Expression Geo Url: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE63061
- Brain Expression Geo Url: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE33000
- Author Itgav Planning Record Url: https://drgezhang.com/assets/research/ad-itgav-experiment-record.md
- Separate Published Methods Use Url: https://pmc.ncbi.nlm.nih.gov/articles/PMC13714348/
- Source Roles: The OUP article and its supplements are the original scientific sources. The FinnGen and GEO entries document input resource identities. The ITGAV worked example and the separate published methods use are contextual links.
- Formal Publication: Human Molecular Genetics. First published 18 December 2024. Volume 34, issue 5, March 2025, pages 381–391.
- Source Rights: Oxford University Press, all rights reserved. Source links accompany original explanatory material.

## Evidence-page notice

Source-linked account of this study’s tissue-specific expression screens, genetic target prioritization and PC12 expression measurements.

## Links

- DOI: https://doi.org/10.1093/hmg/ddae189
- HTML page: https://drgezhang.com/papers/doi-10-1093-hmg-ddae189.html
- Google Scholar query: https://scholar.google.com/scholar?q=%22Integrated%20multi-omics%20analysis%20revealed%20the%20molecular%20networks%20and%20potential%20targets%20of%20cellular%20senescence%20in%20Alzheimer%E2%80%99s%20disease%22
- ORCID: https://orcid.org/0000-0002-3116-3246
