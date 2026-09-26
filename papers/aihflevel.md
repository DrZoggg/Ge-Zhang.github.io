# AI hybrid survival assessment for advanced heart failure patients with renal dysfunction

Researcher: Ge Zhang
Chinese name: 张格
ORCID identity anchor: https://orcid.org/0000-0002-3116-3246
Canonical researcher: https://drgezhang.com/#person

Journal: Nature Communications
Year: 2024
Type: Article
DOI: 10.1038/s41467-024-50415-9
Canonical page: https://drgezhang.com/papers/aihflevel.html
Markdown record: https://drgezhang.com/papers/aihflevel.md

## Full Authors

1. Ge Zhang
2. Zeyu Wang
3. Zhuang Tong
4. Zhen Qin
5. Chang Su
6. Demin Li
7. Shuai Xu
8. Kaixiang Li
9. Zhaokai Zhou
10. Yudi Xu
11. Shiqian Zhang
12. Ruhao Wu
13. Teng Li
14. Youyang Zheng
15. Jinying Zhang
16. Ke Cheng
17. Junnan Tang

## Official Abstract

Renal dysfunction (RD) often characterizes the worse course of patients with advanced heart failure (AHF). Many prognosis assessments are hindered by researcher biases, redundant predictors, and lack of clinical applicability. In this study, we enroll 1736 AHF/RD patients, including data from Henan Province Clinical Research Center for Cardiovascular Diseases (which encompasses 11 hospital subcenters), and Beth Israel Deaconess Medical Center. We developed an AI hybrid modeling framework, assembling 12 learners with different feature selection paradigms to expand modeling schemes. The optimized strategy is identified from 132 potential schemes to establish an explainable survival assessment system: AIHFLevel. The conditional inference survival tree determines a probability threshold for prognostic stratification. The evaluation confirmed the system’s robustness in discrimination, calibration, generalization, and clinical implications. AIHFLevel outperforms existing models, clinical features, and biomarkers. We also launch an open and user-friendly website www.hf-ai-survival.com, empowering healthcare professionals with enhanced tools for continuous risk monitoring and precise risk profiling.

Text reproduced verbatim from Version of Record ([source](https://www.nature.com/articles/s41467-024-50415-9)); [DOI](https://doi.org/10.1038/s41467-024-50415-9); [CC-BY-NC-ND-4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/).

## Evidence Snapshot

**AIHFLevel: explainable survival assessment in advanced heart failure with renal dysfunction**

Explainable survival-risk assessment system developed for adults with advanced heart failure and renal dysfunction, using 1,736 patients across CRCCD and BIDMC cohorts, 93 clinical variables, 46 candidate survival features, 132 modeling schemes, and a 12-predictor model with external validation.

| Evidence | Value |
| --- | --- |
| Unique total | n=1,736 |
| CRCCD Discovery | n=498; subset of CRCCD Meta |
| CRCCD Replication | n=214; subset of CRCCD Meta |
| CRCCD Meta | n=712 |
| BIDMC | n=1,024 |
| Initial predictors | 93 |
| Candidate survival features | 46 |
| Algorithms | 12 |
| Modeling schemes | 132 |
| Final predictors | 12 |
| average C-index | 0.821 |

## Research Question

Can an explainable hybrid survival-learning framework provide accurate and externally validated mortality-risk stratification for patients with advanced heart failure and renal dysfunction?

## Author Evidence Summary

AIHFLevel is an explainable survival-risk assessment system developed for adults with advanced heart failure and renal dysfunction. The study analyzed 1,736 patients across an in-house multicenter CRCCD cohort and an independent BIDMC cohort. Within CRCCD, 93 routinely accessible clinical variables were screened, 46 candidate survival features entered a hybrid machine-learning framework, and 132 modeling schemes were systematically evaluated. The selected strategy combined Surv.gbm and Surv.Xgboost with hybrid filter-wrapper feature selection and produced a 12-predictor survival model. AIHFLevel showed strong time-dependent discrimination in internal validation and retained prognostic performance in 1,024 externally evaluated BIDMC patients. The framework also provides interpretable predictor contributions and three-state prognostic stratification. These results support AIHFLevel as a prognostic risk-assessment tool; prospective studies are still required to determine whether AIHFLevel-guided management improves clinical outcomes.

## Key Findings

<a id="kf1"></a>
### KF1: The selected hybrid modeling strategy achieved the highest average C-index among evaluated schemes.

Context: Comprehensive evaluation of 132 candidate modeling schemes

| Evidence | Value |
| --- | --- |
| average C-index | 0.821 |

Source locator: Results: Survival assessment system AIHFLevel; Fig. 2b

<a id="kf2"></a>
### KF2: AIHFLevel demonstrated strong time-dependent discrimination in the CRCCD Replication cohort.

Context: Internal validation cohort, n=214

| Evidence | Value |
| --- | --- |
| 6-month AUC | 0.902 |
| 12-month AUC | 0.932 |
| 24-month AUC | 0.932 |
| 30-month AUC | 0.903 |

Source locator: Fig. 2e

<a id="kf3"></a>
### KF3: AIHFLevel demonstrated strong time-dependent discrimination in the CRCCD Discovery cohort.

Context: CRCCD Discovery cohort, n=498

| Evidence | Value |
| --- | --- |
| 6-month AUC | 0.931 |
| 12-month AUC | 0.952 |
| 24-month AUC | 0.973 |
| 30-month AUC | 0.976 |

Source locator: Supplementary Fig. 3c

<a id="kf4"></a>
### KF4: AIHFLevel retained prognostic discrimination in an independent BIDMC external cohort.

Context: Independent external validation cohort, n=1,024

| Evidence | Value |
| --- | --- |
| 1-year AUC | 0.788 |
| 2-year AUC | 0.816 |
| 3-year AUC | 0.824 |
| 4-year AUC | 0.846 |

Source locator: Fig. 6d

<a id="kf5"></a>
### KF5: Conditional inference survival-tree analysis defined three prognostic states.

Context: Conditional inference survival-tree analysis

| Evidence | Value |
| --- | --- |
| low risk | AIHFLevel <= 0.435 |
| intermediate risk | 0.435 < AIHFLevel <= 1.548 |
| high risk | AIHFLevel > 1.548 |

Source locator: Fig. 4a-c

## Study Design & Model Development

### Study profile

- Study Design: Multicenter retrospective longitudinal cohort study
- Evidence Type: Human clinical prognostic modeling study
- Unique total: 1,736
- Population: Adults with advanced heart failure and renal dysfunction
- Primary Endpoint: All-cause mortality
- Secondary Endpoint: Major adverse cardiovascular events
- External validation: Yes
- Data modalities: electronic health records, laboratory measurements, clinical characteristics, echocardiography

### Cohort hierarchy

| Cohort | Role | n | Relationship |
| --- | --- | ---: | --- |
| CRCCD Discovery | model development | 498 | Subset of CRCCD Meta |
| CRCCD Replication | internal validation | 214 | Subset of CRCCD Meta |
| CRCCD Meta | complete in-house cohort | 712 | Contains CRCCD Discovery, CRCCD Replication |
| BIDMC | independent external validation | 1024 | Independent cohort |

### Model development

- Initial predictors: 93
- Candidate survival features: 46
- Algorithms: 12
- Modeling schemes: 132
- Selected algorithms: Surv.gbm, Surv.Xgboost
- Feature selection: Filter & Wrapper Hybrid Method
- Final predictors: 12

### Final predictor set

1. age
2. arrhythmia
3. coronary artery disease
4. CKD stage
5. lymphocyte percentage
6. mean corpuscular hemoglobin concentration
7. estimated glomerular filtration rate
8. serum creatinine
9. total bilirubin
10. cardiac troponin I
11. left ventricular ejection fraction
12. stroke volume

### Interpretability

- SHAP
- conditional inference survival tree

## What This Study Adds

- Systematic evaluation of multiple survival-learning and feature-selection strategies rather than reliance on a single investigator-selected algorithm.
- A parsimonious 12-predictor survival-risk system derived from routinely accessible clinical information.
- Independent external evaluation in a heterogeneous BIDMC cohort.
- Patient-level interpretability and three-state prognostic stratification.
- Translation of the model into an accessible clinical web application.

## Evidence Scope

### Supports

- Mortality-risk estimation in the studied advanced-heart-failure and renal-dysfunction population.
- Internal and independent external evaluation of AIHFLevel.
- Association between higher AIHFLevel and poorer prognosis.
- Three-state prognostic stratification.
- Patient-level interpretation of predictor contributions.

### Does Not Establish

- That AIHFLevel-guided treatment improves survival or other clinical outcomes.
- That predictors included in AIHFLevel are causal determinants of mortality.
- That model performance is identical in every healthcare setting or population.
- That AIHFLevel replaces clinical judgment.

### Limitations

- The study was retrospective and observational.
- Prospective multicenter validation is still warranted.
- Randomized studies would be required to establish whether AIHFLevel-guided treatment improves patient outcomes.
- Some echocardiographic predictors may not be uniformly available in primary-care settings.
- Direct methodological reproduction of every comparator risk model was not possible.

<a id="citation-use-cases"></a>
## When This Study Is Useful to Cite

### CU1: Which studies developed and externally validated machine-learning survival models for advanced heart failure with renal dysfunction?

AIHFLevel was developed in the CRCCD cohort and independently evaluated in 1,024 BIDMC patients with advanced heart failure and renal dysfunction.

Evidence: [KF1](#kf1), [KF4](#kf4)

### CU2: What evidence supports time-dependent mortality discrimination by AIHFLevel?

The study reports time-dependent discrimination in the CRCCD Replication cohort and independent BIDMC external cohort.

Evidence: [KF2](#kf2), [KF4](#kf4)

### CU3: How was hybrid model selection used to reduce reliance on one investigator-selected survival algorithm?

The study systematically evaluated 132 modeling schemes using 12 learners and alternative feature-selection strategies before selecting the final approach.

Evidence: [KF1](#kf1)

### CU4: Can an explainable clinical survival model provide patient-level prognostic stratification in advanced heart failure with renal dysfunction?

The final 12-predictor framework included patient-level interpretation and a conditional-inference survival tree defining three prognostic states.

Evidence: [KF5](#kf5)

<a id="citation-boundaries"></a>
## What This Study Should Not Be Cited to Claim

- AIHFLevel-guided treatment has been shown to improve survival or other clinical outcomes.
- Prospective clinical utility has been established.
- The 12 model predictors are causal determinants of mortality.
- Model performance is guaranteed to generalize to every heart-failure population or healthcare setting.
- AIHFLevel replaces clinician judgment.

<a id="evidence-matrix"></a>
## Evidence Matrix

<a id="evidence-model-selection"></a>
### Model-selection framework

- Context: CRCCD development framework
- Finding: 132 candidate modeling schemes were evaluated; the selected strategy combined Surv.gbm and Surv.Xgboost with hybrid filter-wrapper feature selection and achieved average C-index 0.821.
- Evidence Level: Retrospective model development
- Scope: Supports comparative model-selection performance, not treatment benefit.
- Source Locator: Results: Survival assessment system AIHFLevel; Fig. 2b
- Evidence refs: [KF1](#kf1)

<a id="evidence-crccd-replication"></a>
### Internal validation

- Context: CRCCD Replication cohort, n=214
- Finding: 6/12/24/30-month AUCs were 0.902 / 0.932 / 0.932 / 0.903.
- Evidence Level: Internal retrospective validation
- Scope: Mortality-risk discrimination in the studied replication cohort.
- Source Locator: Fig. 2e
- Evidence refs: [KF2](#kf2)

<a id="evidence-crccd-discovery"></a>
### Development-cohort discrimination

- Context: CRCCD Discovery cohort, n=498
- Finding: 6/12/24/30-month AUCs were 0.931 / 0.952 / 0.973 / 0.976.
- Evidence Level: Retrospective development cohort
- Scope: Performance within the development cohort.
- Source Locator: Supplementary Fig. 3c
- Evidence refs: [KF3](#kf3)

<a id="evidence-bidmc-external"></a>
### Independent external evaluation

- Context: BIDMC cohort, n=1,024
- Finding: 1/2/3/4-year AUCs were 0.788 / 0.816 / 0.824 / 0.846.
- Evidence Level: Independent retrospective external validation
- Scope: External prognostic discrimination; not prospective utility.
- Source Locator: Fig. 6d
- Evidence refs: [KF4](#kf4)

<a id="evidence-risk-stratification"></a>
### Prognostic stratification

- Context: Conditional inference survival-tree analysis
- Finding: Low <=0.435; intermediate >0.435 to <=1.548; high >1.548.
- Evidence Level: Retrospective prognostic stratification
- Scope: Risk-group definition, not evidence of treatment-response benefit.
- Source Locator: Fig. 4a-c
- Evidence refs: [KF5](#kf5)

## Q&A

### What is AIHFLevel?

AIHFLevel is an explainable 12-predictor survival-risk assessment system developed for patients with advanced heart failure and renal dysfunction.

Evidence: KF1

### How many patients were used to develop and validate AIHFLevel?

The study included 1,736 unique patients: 712 in the CRCCD cohort and 1,024 in an independent BIDMC cohort. The CRCCD cohort was divided into a 498-patient Discovery cohort and a 214-patient Replication cohort.

### Was AIHFLevel externally validated?

Yes. AIHFLevel was independently evaluated in 1,024 patients from BIDMC.

Evidence: KF4

### How accurately did AIHFLevel predict all-cause mortality?

In the CRCCD Replication cohort, AUCs at 6, 12, 24 and 30 months were 0.902, 0.932, 0.932 and 0.903. In the independent BIDMC cohort, AUCs at 1, 2, 3 and 4 years were 0.788, 0.816, 0.824 and 0.846.

Evidence: KF2, KF4

### How was AIHFLevel developed?

Ninety-three EHR variables were initially evaluated, 46 candidate survival features entered the modeling framework, and 132 modeling schemes were compared. The selected strategy combined Surv.gbm and Surv.Xgboost with a Filter & Wrapper Hybrid Method.

Evidence: KF1

### Which clinical variables are included in AIHFLevel?

The 12 predictors are age, arrhythmia, coronary artery disease, CKD stage, lymphocyte percentage, MCHC, eGFR, serum creatinine, total bilirubin, cardiac troponin I, left ventricular ejection fraction and stroke volume.

### How does AIHFLevel stratify prognosis?

The conditional inference survival tree defines low risk at AIHFLevel <= 0.435, intermediate risk above 0.435 and up to 1.548, and high risk above 1.548.

Evidence: KF5

### Does the study show that AIHFLevel-guided treatment improves patient outcomes?

No. The study establishes prognostic performance in retrospective cohorts. Prospective multicenter validation and randomized studies are still required to determine whether AIHFLevel-guided management improves clinical outcomes.

## Concepts & Entities

### Conditions

advanced heart failure, renal dysfunction, chronic kidney disease, coronary artery disease, arrhythmia

### Populations

adults with advanced heart failure and renal dysfunction

### Outcomes

all-cause mortality, major adverse cardiovascular events

### Methods

survival machine learning, Cox regression, time-dependent ROC analysis, calibration analysis, decision curve analysis, SHAP, conditional inference survival tree

### Data Types

electronic health records, clinical variables, laboratory measurements, echocardiography

### Models & Tools

AIHFLevel, Surv.gbm, Surv.Xgboost

### Datasets & Cohorts

CRCCD, BIDMC, MIMIC-III

## Related Research

- [TYG Index as a Novel Predictor of Clinical Outcomes in Advanced Chronic Heart Failure with Renal Dysfunction Patients](https://drgezhang.com/papers/doi-10-2147-cia-s462542.html) — Complementary prognostic evidence in advanced heart failure with renal dysfunction (DOI: 10.2147/cia.s462542)
- [From Disease-Specific Models to Broad Clinical Utility: A Perspective on AI Hybrid Ensemble Frameworks](https://drgezhang.com/papers/doi-10-1002-ggn2-202500053.html) — Methodological extension of hybrid ensemble modeling for broader clinical utility (DOI: 10.1002/ggn2.202500053)

## Publication & Provenance

- DOI: https://doi.org/10.1038/s41467-024-50415-9
- Publisher: https://www.nature.com/articles/s41467-024-50415-9
- PubMed: https://pubmed.ncbi.nlm.nih.gov/39117613/
- PMCID: PMC11310499
- Code: https://github.com/DrZoggg/AIHFLevel
- Clinical tool: https://www.hf-ai-survival.com

## Evidence-page notice

Author-controlled evidence page for this publication. This page provides an evidence-oriented summary and does not replace the publisher's version of record.

## Links

- DOI: https://doi.org/10.1038/s41467-024-50415-9
- HTML page: https://drgezhang.com/papers/aihflevel.html
- Google Scholar query: https://scholar.google.com/scholar?q=%22AI%20hybrid%20survival%20assessment%20for%20advanced%20heart%20failure%20patients%20with%20renal%20dysfunction%22
- ORCID: https://orcid.org/0000-0002-3116-3246
