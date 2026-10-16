# Novel post-translational modification learning signature reveals B4GALT2 as an immune exclusion regulator in lung adenocarcinoma

Researcher: Ge Zhang
Chinese name: 张格
ORCID identity anchor: https://orcid.org/0000-0002-3116-3246
Canonical researcher: https://drgezhang.com/#person

Journal: Journal for ImmunoTherapy of Cancer
Year: 2025
Type: Article
DOI: 10.1136/jitc-2024-010787
Canonical page: https://drgezhang.com/papers/b4galt2.html
Markdown record: https://drgezhang.com/papers/b4galt2.md

## Full Authors

1. Pengpeng Zhang
2. Dingli Wang
3. Guangyao Zhou
4. Shuai Jiang
5. Ge Zhang
6. Lianmin Zhang
7. Zhenfa Zhang

<a id="paper-discovery"></a>
## Research & review context

### Research fields

- Lung adenocarcinoma immunology
- Molecular prognostic modeling

### Review topics

- B4GALT2 and immune exclusion
- Post-translational modification signatures

### Scientific role

Retrospective PTM-expression signature research with LUAD tissue immune phenotyping and mouse B4GALT2 perturbation.

### Evidence position

Retrospective human association and preclinical intervention; no established human anti-PD-1 treatment benefit.

### Related concepts

- Immune-desert CD8 phenotype
- PTMLS
- Correction to Figure 2

### Possible citation contexts

- Reviews separating tissue immune-exclusion associations from preclinical gene-suppression and anti-PD-1 experiments.
- Methods reviews of PTM-related LUAD signatures with explicit attention to the published correction.

Possible literature-review contexts, not evidence of existing citations. Read the findings and Evidence Scope before citing the original article.

## Evidence Scale

**Novel post-translational modification learning signature reveals B4GALT2 as an immune exclusion regulator in lung adenocarcinoma**

This study integrated LUAD expression cohorts, retrospective treatment-response datasets, a 171-case institutional tissue series and cellular/mouse experiments to associate a post-translational modification learning signature (PTMLS) and B4GALT2 with tumor immune contexture. Knockdown of B4GALT2 enhanced anti-PD-1-associated antitumor readouts in a mouse model, but clinical benefit in humans remains unproven.

| Evidence | Value |
| --- | --- |
| Discovery/validation | TCGA-LUAD plus six GEO LUAD series |
| Independent institutional tissue series | 171 archived LUAD patients in Figure 7 cohort |
| Single-cell data | GSE207422 reported 15 specimens |
| Signature feature context | 31 prognostic PTM-related genes considered in model construction |
| Intervention species | LLC-cell mouse tumor model with anti-PD-1 treatment |

### Counting note

TCGA, GEO, treatment cohorts, single-cell specimens, 171 institutional patients and mice are distinct scales and not combined into a unique-patient total. Methods and Figure 8 caption report incompatible LLC inoculation cell numbers; neither is promoted as a verified dose.

## Research Question

How do post-translational modification-associated transcriptomic signatures relate to LUAD prognosis and immune exclusion, and what experimental evidence implicates B4GALT2 in antitumor immune response?

## Author Evidence Summary

The investigators selected PTM-related transcripts, trained a survival-learning score, evaluated independent LUAD and mixed-cancer treatment cohorts, examined CD8 distribution in a 171-case tissue series and perturbed B4GALT2 in cell and mouse experiments. The published Figure 2 differential-gene heatmap was subsequently corrected; only the corrected figure should be used for figure-specific interpretation.

## Key Findings

<a id="kf1"></a>
### KF1: A PTM-related expression score stratified retrospective LUAD prognosis across discovery and GEO cohorts.

Context: TCGA discovery and six GEO retrospective reapplications; selecting models by validation-set C-index may yield optimistic model ranking.

| Evidence | Value |
| --- | --- |
| Development | TCGA-LUAD |
| GEO prognosis evaluation | 6 cohorts |
| Algorithm selection | Stepcox (both) + SuperPC; mean C-index across evaluated cohorts |
| Feature discovery | 31 survival-associated PTM-related genes |

Source locator: PMC11865799: Methods Multi-source data integration (s2-1), Identification and evaluation of a PTMLS (s2-2); Results PTMLS development (s3-2) and Clinical validation (s3-3); Figures 3–4. Figure 2 interpretation must use correction DOI 10.1136/jitc-2024-010787corr1.

<a id="kf2"></a>
### KF2: Lower PTMLS scores were associated with immune-signature and retrospectively observed treatment-response patterns.

Context: Computational immune deconvolution and heterogeneous treatment cohorts do not establish a treatment-selection assay or prospective response prediction.

| Evidence | Value |
| --- | --- |
| LUAD immunotherapy series described | OAK, POPLAR and NG |
| Immune-score trend | Lower PTMLS generally showed higher estimated lymphocyte and immune-score signatures |
| Clinical boundary | Retrospective association across heterogeneous regimens and cancers |

Source locator: PMC11865799: Results PTMLS: a novel prognostic and immunotherapy response predictor (s3-2); PTMLS as a determinant of tumor immune landscape (s3-6); Figures 3I–T, 5A–F; supplemental Figure S1.

<a id="kf3"></a>
### KF3: B4GALT2 expression correlated with the PTMLS and unfavorable retrospective prognostic patterns.

Context: Correlation and reported Kaplan–Meier analyses are observational, not a multivariable causal effect or proof of direct immunosuppression.

| Evidence | Value |
| --- | --- |
| B4GALT2–PTMLS correlation | Reported r=0.82 |
| Reported survival association | HR 1.62, 95% CI 1.36–1.92 in the article-reported analysis |
| Immune marker association | Inverse associations with CD8A expression |

Source locator: PMC11865799: Results B4GALT2: a key determinant in LUAD progression and immune response (s3-7); Figure 6A–Q.

<a id="kf4"></a>
### KF4: The institutional tissue cohort associated high B4GALT2 expression with an immune-desert CD8 distribution phenotype.

Context: Archival observational immunohistochemistry measures spatial phenotype and survival association; it does not prove that high B4GALT2 causes human immune exclusion.

| Evidence | Value |
| --- | --- |
| Tissue series | 171 LUAD patient specimens |
| CD8 spatial classes | Desert, Excluded and Inflamed |
| Reported B4GALT2-high survival comparison | Log-rank p=0.033 |

Source locator: PMC11865799: Methods Construction of an in-house LUAD cohort (s2-9), Multiplexed immunohistochemistry (s2-10); Results B4GALT2 and CD8+ T cell distribution (s3-8); Figure 7A–G.

<a id="kf5"></a>
### KF5: B4GALT2 silencing was associated with reduced LUAD cell growth and increased anti-PD-1 activity in an experimental mouse model.

Context: Direct perturbation supports a preclinical functional contribution; mouse LLC tumor-cell dosing is inconsistent between Methods and Figure 8H legend and should not be repeated.

| Evidence | Value |
| --- | --- |
| Human cell systems | A549/H1299 B4GALT2 knockdown growth assays |
| In-vivo system | C57BL/6 mice bearing LLC tumors with anti-PD-1 or isotype treatment |
| Immune readouts | CD8 effector-marker flow cytometry; CD44/CD69/GZMB |

Source locator: PMC11865799: Methods Cell Culture and Lentiviral Transfection (s2-7), Mouse model for immune response assessment (s2-11); Results B4GALT2 role in immune regulation (s3-9), B4GALT2 inhibition potentiates anti-PD-1 (s3-10); Figures 8C–J and 9A–B.

## Study Design & Model Development

### Study profile

- Study Design: Retrospective multi-series expression modeling with computational immunotherapy associations, institutional LUAD tissue immune phenotyping and in-vitro/in-vivo B4GALT2 perturbation.
- Evidence Type: Human retrospective transcriptomic and pathological association plus mouse and cell-line intervention experiments.
- Population: TCGA LUAD discovery; six GEO LUAD prognosis series; additional mixed-cancer immunotherapy cohorts; 171 institutional LUAD archival tumor specimens; GSE207422 single-cell specimens.
- Primary Endpoint: Association between PTMLS expression score and retrospective LUAD survival across cohorts.
- Secondary Endpoint: Immune-cell distribution and B4GALT2 expression associations; treatment-response dataset analyses; proliferation and anti-PD-1 readouts in experimental systems.
- External dataset evaluation: Yes
- Data modalities: Bulk LUAD expression and survival series, Clinical immunotherapy cohorts across tumor types, LUAD FFPE multiplex tissue imaging, Single-cell transcriptomic data, LUAD cell-line growth assays, Immunocompetent mouse tumor studies and flow cytometry

### Model development

- Model Name: Post-translational modification learning signature (PTMLS)
- Algorithm Selection: Stepcox (both) + SuperPC, selected by the reported mean validation-set C-index
- Development: TCGA-LUAD retrospective expression and survival
- Evaluation: Six GEO LUAD survival datasets and separate mixed-cancer treatment series
- Clinical Boundary: No prospective score-guided immune checkpoint therapy trial or independently validated clinical deployment.

## What This Study Adds

- Integrates prognosis-associated PTM gene modeling with human immune spatial patterns and experimental B4GALT2 perturbation.
- Shows different evidence strengths for computational therapy prediction, observational CD8 phenotypes and mouse anti-PD-1 combination experiments.

## Evidence Scope

### Supports

- Retrospective PTMLS/B4GALT2 associations with LUAD survival and tumor immune patterns.
- An association between B4GALT2 staining and CD8 spatial phenotypes in institutional tissue specimens.
- Preclinical effects of B4GALT2 knockdown and anti-PD-1 treatment in the described experimental mouse model.

### Does Not Establish

- Prospective clinical response prediction or better human patient outcomes from using PTMLS.
- Causal mediation of immune exclusion in human LUAD from observational staining patterns.
- Proven clinical efficacy or safety of inhibiting B4GALT2 alongside immune checkpoint blockade.
- A definitive LLC inoculum count because Methods and Figure 8 legend disagree.
- Original uncorrected Figure 2 heatmap as a current scientific source.

### Limitations

- A published correction replaced the original Figure 2 differential-gene heatmap. Do not reproduce or interpret the old version as the corrected source.
- Human tissue and mixed-cancer immunotherapy cohorts do not establish prospective predictive efficacy in LUAD.
- The published LLC inoculation cell number differs between Methods (2×10^5) and Figure 8H caption (1×10^6); no value is silently chosen.
- Cell and mouse interventions are not human trials; treatment benefit, optimal dosing, safety and validated target engagement remain unknown.
- A coauthor ORCID differs from another article; preserve the existing site bibliographic source until formally resolved.

<a id="citation-use-cases"></a>
## When This Study Is Useful to Cite

### CU1: What human evidence links B4GALT2 to LUAD immune exclusion?

Archival tissue CD8-pattern associations, without causal assignment.

Evidence: [KF3](#kf3), [KF4](#kf4)

### CU2: Does B4GALT2 inhibition improve anti-PD-1 response?

Experimental mouse evidence only; not a clinical effectiveness claim.

Evidence: [KF5](#kf5)

### CU3: What correction affects the published evidence?

Figure 2 replaced; ensure corrected source provenance.

Evidence: [KF1](#kf1)

<a id="citation-boundaries"></a>
## What This Study Should Not Be Cited to Claim

- Prospective clinical response prediction or better human patient outcomes from using PTMLS.
- Causal mediation of immune exclusion in human LUAD from observational staining patterns.
- Proven clinical efficacy or safety of inhibiting B4GALT2 alongside immune checkpoint blockade.
- A definitive LLC inoculum count because Methods and Figure 8 legend disagree.
- Original uncorrected Figure 2 heatmap as a current scientific source.

<a id="evidence-matrix"></a>
## Evidence Matrix

<a id="evidence-b2-b4galt2-1"></a>
### KF1: A PTM-related expression score stratified retrospective LUAD prognosis across discovery and GEO cohorts.

- Context: TCGA discovery and six GEO retrospective reapplications; selecting models by validation-set C-index may yield optimistic model ranking.
- Finding: A PTM-related expression score stratified retrospective LUAD prognosis across discovery and GEO cohorts. Development: TCGA-LUAD; GEO prognosis evaluation: 6 cohorts; Algorithm selection: Stepcox (both) + SuperPC; mean C-index across evaluated cohorts; Feature discovery: 31 survival-associated PTM-related genes
- Evidence Level: TCGA discovery and six GEO retrospective reapplications; selecting models by validation-set C-index may yield optimistic model ranking.
- Scope: TCGA discovery and six GEO retrospective reapplications; selecting models by validation-set C-index may yield optimistic model ranking.
- Source Locator: PMC11865799: Methods Multi-source data integration (s2-1), Identification and evaluation of a PTMLS (s2-2); Results PTMLS development (s3-2) and Clinical validation (s3-3); Figures 3–4. Figure 2 interpretation must use correction DOI 10.1136/jitc-2024-010787corr1.
- Evidence refs: [KF1](#kf1)

<a id="evidence-b2-b4galt2-2"></a>
### KF2: Lower PTMLS scores were associated with immune-signature and retrospectively observed treatment-response patterns.

- Context: Computational immune deconvolution and heterogeneous treatment cohorts do not establish a treatment-selection assay or prospective response prediction.
- Finding: Lower PTMLS scores were associated with immune-signature and retrospectively observed treatment-response patterns. LUAD immunotherapy series described: OAK, POPLAR and NG; Immune-score trend: Lower PTMLS generally showed higher estimated lymphocyte and immune-score signatures; Clinical boundary: Retrospective association across heterogeneous regimens and cancers
- Evidence Level: Computational immune deconvolution and heterogeneous treatment cohorts do not establish a treatment-selection assay or prospective response prediction.
- Scope: Computational immune deconvolution and heterogeneous treatment cohorts do not establish a treatment-selection assay or prospective response prediction.
- Source Locator: PMC11865799: Results PTMLS: a novel prognostic and immunotherapy response predictor (s3-2); PTMLS as a determinant of tumor immune landscape (s3-6); Figures 3I–T, 5A–F; supplemental Figure S1.
- Evidence refs: [KF2](#kf2)

<a id="evidence-b2-b4galt2-3"></a>
### KF3: B4GALT2 expression correlated with the PTMLS and unfavorable retrospective prognostic patterns.

- Context: Correlation and reported Kaplan–Meier analyses are observational, not a multivariable causal effect or proof of direct immunosuppression.
- Finding: B4GALT2 expression correlated with the PTMLS and unfavorable retrospective prognostic patterns. B4GALT2–PTMLS correlation: Reported r=0.82; Reported survival association: HR 1.62, 95% CI 1.36–1.92 in the article-reported analysis; Immune marker association: Inverse associations with CD8A expression
- Evidence Level: Correlation and reported Kaplan–Meier analyses are observational, not a multivariable causal effect or proof of direct immunosuppression.
- Scope: Correlation and reported Kaplan–Meier analyses are observational, not a multivariable causal effect or proof of direct immunosuppression.
- Source Locator: PMC11865799: Results B4GALT2: a key determinant in LUAD progression and immune response (s3-7); Figure 6A–Q.
- Evidence refs: [KF3](#kf3)

<a id="evidence-b2-b4galt2-4"></a>
### KF4: The institutional tissue cohort associated high B4GALT2 expression with an immune-desert CD8 distribution phenotype.

- Context: Archival observational immunohistochemistry measures spatial phenotype and survival association; it does not prove that high B4GALT2 causes human immune exclusion.
- Finding: The institutional tissue cohort associated high B4GALT2 expression with an immune-desert CD8 distribution phenotype. Tissue series: 171 LUAD patient specimens; CD8 spatial classes: Desert, Excluded and Inflamed; Reported B4GALT2-high survival comparison: Log-rank p=0.033
- Evidence Level: Archival observational immunohistochemistry measures spatial phenotype and survival association; it does not prove that high B4GALT2 causes human immune exclusion.
- Scope: Archival observational immunohistochemistry measures spatial phenotype and survival association; it does not prove that high B4GALT2 causes human immune exclusion.
- Source Locator: PMC11865799: Methods Construction of an in-house LUAD cohort (s2-9), Multiplexed immunohistochemistry (s2-10); Results B4GALT2 and CD8+ T cell distribution (s3-8); Figure 7A–G.
- Evidence refs: [KF4](#kf4)

<a id="evidence-b2-b4galt2-5"></a>
### KF5: B4GALT2 silencing was associated with reduced LUAD cell growth and increased anti-PD-1 activity in an experimental mouse model.

- Context: Direct perturbation supports a preclinical functional contribution; mouse LLC tumor-cell dosing is inconsistent between Methods and Figure 8H legend and should not be repeated.
- Finding: B4GALT2 silencing was associated with reduced LUAD cell growth and increased anti-PD-1 activity in an experimental mouse model. Human cell systems: A549/H1299 B4GALT2 knockdown growth assays; In-vivo system: C57BL/6 mice bearing LLC tumors with anti-PD-1 or isotype treatment; Immune readouts: CD8 effector-marker flow cytometry; CD44/CD69/GZMB
- Evidence Level: Direct perturbation supports a preclinical functional contribution; mouse LLC tumor-cell dosing is inconsistent between Methods and Figure 8H legend and should not be repeated.
- Scope: Direct perturbation supports a preclinical functional contribution; mouse LLC tumor-cell dosing is inconsistent between Methods and Figure 8H legend and should not be repeated.
- Source Locator: PMC11865799: Methods Cell Culture and Lentiviral Transfection (s2-7), Mouse model for immune response assessment (s2-11); Results B4GALT2 role in immune regulation (s3-9), B4GALT2 inhibition potentiates anti-PD-1 (s3-10); Figures 8C–J and 9A–B.
- Evidence refs: [KF5](#kf5)

## Q&A

### What is PTMLS in this study?

PTMLS is an expression-based post-translational modification learning signature, developed in TCGA-LUAD and evaluated across six GEO survival cohorts using algorithm selection that includes validation-set comparisons.

Evidence: KF1

### Was the prognostic model tested outside the discovery cohort?

The article applied it to six GEO LUAD datasets. These are retrospective datasets and not evidence that clinical decisions based on the score improve outcomes.

Evidence: KF1

### Which tumor immune phenotype is linked with high B4GALT2 in patient tissue?

In a 171-case institutional LUAD tissue series, higher B4GALT2 expression was associated with CD8-low/desert-like patterns and less favorable survival, without causal assignment.

Evidence: KF4

### What does the B4GALT2 knockdown experiment add?

It adds culture-based and mouse-tumor perturbation evidence, including increased CD8 effector readouts with anti-PD-1 combination in mice. This does not establish human treatment efficacy.

Evidence: KF5

### Was Figure 2 corrected after publication?

Yes. The original differential-gene heatmap was corrected in an official June 2025 notice (DOI 10.1136/jitc-2024-010787corr1). Use the corrected figure for specific PTM-gene claims.

Evidence: KF1

### Is the mouse inoculation cell count unambiguous?

No. Methods reports 2×10^5 cells while the Figure 8H caption reports 1×10^6 cells; the evidence summary does not choose between these conflicting numbers.

Evidence: KF5

## Concepts & Entities

### Disease And Immunity

Lung adenocarcinoma, CD8 spatial exclusion, Immune-desert phenotype

### Molecular And Models

B4GALT2, Post-translational modification signature, Stepcox and SuperPC

### Evidence And Intervention

Archival pathology cohort, Mouse anti-PD-1 combination, Published Figure 2 correction

## Related Research

- [Deciphering lung adenocarcinoma evolution: Integrative single-cell genomics identifies the prognostic lung progression associated signature](https://drgezhang.com/papers/doi-10-1111-jcmm-18408.html) — Another retrospective LUAD transcriptomic survival signature (LPAS) with PSMB1 culture work; not an external validation of PTMLS. (DOI: 10.1111/jcmm.18408)
- [Advancing predictive markers in lung adenocarcinoma: A machine learning-based immunotherapy prognostic prediction signature](https://drgezhang.com/papers/doi-10-1002-tox-24284.html) — Related LUAD immunotherapy-outcome prediction research with different signatures and no established treatment equivalence. (DOI: 10.1002/tox.24284)

## Publication & Provenance

- DOI: https://doi.org/10.1136/jitc-2024-010787
- Doi Url: https://doi.org/10.1136/jitc-2024-010787
- Publisher: https://jitc.bmj.com/content/13/2/e010787
- Pmc Url: https://pmc.ncbi.nlm.nih.gov/articles/PMC11865799/
- PMCID: PMC11865799
- Correction Doi Url: https://doi.org/10.1136/jitc-2024-010787corr1
- Correction Pmc Url: https://pmc.ncbi.nlm.nih.gov/articles/PMC12164647/
- License: Main article CC BY-NC 4.0. Official correction notice has separate restrictive re-use terms; corrected figures are referenced rather than republished.
- License Url: https://creativecommons.org/licenses/by-nc/4.0/
- Source Of Truth: Journal for ImmunoTherapy of Cancer 2025;13(2):e010787; main PMC11865799 VOR JATS and Figure 2 official correction DOI 10.1136/jitc-2024-010787corr1 (12 June 2025).
- Source Record Notes: Original/revised Figure 2 and official correction HTML supplied privately. The evidence page does not reproduce protected correction figure assets.
- Identity Note: Existing bibliography is preserved. The Ge Zhang coauthor is not to be conflated with the initials GZ used for another equal-contributing author; coauthor ORCID across two papers remains inconsistent.
- Numerical Discrepancy: Mouse LLC inoculum is 2×10^5 in Methods versus 1×10^6 in Figure 8H caption; not harmonized.

## Evidence-page notice

This evidence page uses the official correction-aware version of record. Model comparisons, human associations and mouse interventions have different evidential meanings. Cite the original article and its correction where Figure 2 is material.

## Links

- DOI: https://doi.org/10.1136/jitc-2024-010787
- HTML page: https://drgezhang.com/papers/b4galt2.html
- Google Scholar query: https://scholar.google.com/scholar?q=%22Novel%20post-translational%20modification%20learning%20signature%20reveals%20B4GALT2%20as%20an%20immune%20exclusion%20regulator%20in%20lung%20adenocarcinoma%22
- ORCID: https://orcid.org/0000-0002-3116-3246
