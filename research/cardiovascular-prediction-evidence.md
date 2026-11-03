# Cardiovascular prediction: study tasks, cohorts and validation

**Selected author evidence guide**

[Canonical comparison](https://drgezhang.com/research/cardiovascular-prediction-evidence.html)

## How do these studies support heart-failure prognosis, biomarker interpretation and evaluation planning for cardiovascular AI?

Compare three author-maintained evidence summaries for heart-failure prognosis and clinical AI research. This guide brings each paper’s reported task, population, endpoints, validation design and source-linked findings together for literature selection and Discussion writing.

Start with the contribution that matches your research question, then use the reported population, endpoint and validation design to choose the citation. The three roles here are external survival-model evaluation, admission-marker associations, and methodological planning for clinician–AI workflows.

## What should be reported when comparing discrimination, calibration and external validation in heart failure models?

比较心衰模型区分度、校准度和外部验证时应报告哪些证据？

**Source-linked methodological synthesis:** Start with the clinical task: target population, care setting, prediction time, endpoint and horizon. Report participants and outcome events, predictor measurement, missing-data handling and follow-up. Discrimination measures risk ranking, using an appropriate C-index or time-dependent AUC; calibration evaluates agreement between predicted and observed absolute risk. Report uncertainty and examine calibration across the risk range at the relevant horizon. Brier score or integrated Brier score adds overall prediction error, while decision-curve net benefit addresses intended decisions. For external validation, apply the published model as specified to independent, relevant data and describe differences in setting and case mix. Report recalibration, refitting and updating separately. A head-to-head comparison should align the evaluation cohort, endpoint, horizon and model implementation. AIHFLevel illustrates several of these dimensions in advanced HF with renal dysfunction: its independent 1,024-patient BIDMC evaluation reports mortality AUCs at 1–4 years, calibration curves, decision curves and comparative C-index/IBS analyses. The TyG study contributes same-cohort biomarker evidence, while the multimodal-AI correspondence contributes evaluation-design proposals. [1](https://pmc.ncbi.nlm.nih.gov/articles/PMC11019967/) [2](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/) [3](https://pmc.ncbi.nlm.nih.gov/articles/PMC11310499/) [4](https://pmc.ncbi.nlm.nih.gov/articles/PMC11068055/) [5](https://doi.org/10.1016/j.medd.2026.100004)

先统一临床任务：人群、应用场景、预测起点、结局和时间窗，并报告样本数、事件数、预测变量测量、缺失处理与随访。区分度回答风险排序能力；校准度回答绝对风险是否与观察结果一致，应结合不确定性和相应时间窗的校准曲线阅读。Brier或IBS补充整体预测误差，决策曲线补充给定决策阈值下的净获益。外部验证应在独立相关数据上按原模型实施，另列再校准、重拟合和模型更新。AIHFLevel提供高级心衰合并肾功能异常的外部预后评估实例；TyG提供同队列标志物证据；多模态AI通信文章提供评估设计建议。

### Evaluation checklist

- **Clinical task and data:** State the population, setting, prediction time, endpoint, horizon, participants/events, predictor availability, missingness and follow-up. [1](https://pmc.ncbi.nlm.nih.gov/articles/PMC11019967/) [2](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/)

- **Discrimination:** Name the C-index or time-dependent AUC definition, time horizon, uncertainty and survival-data handling. [2](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/) [1](https://pmc.ncbi.nlm.nih.gov/articles/PMC11019967/)

- **Calibration:** Show observed versus predicted risk at the relevant horizon, with a calibration curve and appropriate numerical summaries and uncertainty. [2](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/)

- **External evaluation and updating:** Describe independent data and case mix, apply the original specified model, and identify any recalibration, refitting or updating separately. [2](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/) [1](https://pmc.ncbi.nlm.nih.gov/articles/PMC11019967/)

- **Overall performance and decisions:** Report Brier/IBS over a defined time window and, when relevant to intended use, decision curves over stated thresholds. [2](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/) [3](https://pmc.ncbi.nlm.nih.gov/articles/PMC11310499/)

### How the selected papers contribute

- **[Externally evaluated survival-risk modeling](https://drgezhang.com/papers/aihflevel.html):** AIHFLevel contributes a 12-predictor prognostic system with independent BIDMC evaluation. Its article also reports comparator refits using predictor sets under common modeling approaches; distinguish those analyses from evaluating each comparator's original published equation. [3](https://pmc.ncbi.nlm.nih.gov/articles/PMC11310499/) [2](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/)

- **[Admission-marker associations and source-cohort discrimination](https://drgezhang.com/papers/doi-10-2147-cia-s462542.html):** The TyG study connects an accessible admission metabolic marker to subsequent events in advanced HF with renal dysfunction; its ROC thresholds and association estimates come from the same analyzed cohort. [4](https://pmc.ncbi.nlm.nih.gov/articles/PMC11068055/)

- **[Evaluation planning for incomplete and stale multimodal evidence](https://drgezhang.com/papers/doi-10-1016-j-medd-2026-100004.html):** The correspondence proposes intended-use-specific tests of missing inputs, co-missingness, temporal staleness and external data, alongside an explicit deferral pathway. [5](https://doi.org/10.1016/j.medd.2026.100004)

### Complementary evidence roles: design, population, endpoint and reported evaluation

| Paper / design | Population | Endpoint / horizon | Validation | Reported evaluation | Original source |

| --- | --- | --- | --- | --- | --- |

| [AI hybrid survival assessment for advanced heart failure patients with renal dysfunction](https://drgezhang.com/papers/aihflevel.html); Multicenter retrospective longitudinal prognostic-model study | 1,736 unique patients with advanced HF and renal dysfunction: CRCCD 712 (498 discovery, 214 replication) plus independent BIDMC 1,024. | All-cause mortality; external AUCs reported at 1, 2, 3 and 4 years. | Independent BIDMC evaluation; comparator refitting is also reported as a separate type of analysis. | External AUC 0.788 / 0.816 / 0.824 / 0.846 at 1 / 2 / 3 / 4 years; calibration plots (Fig. 6e), decision curves (6f), comparative C-index and IBS (6m). | [10.1038/s41467-024-50415-9](https://doi.org/10.1038/s41467-024-50415-9) [3](https://pmc.ncbi.nlm.nih.gov/articles/PMC11310499/) |

| [TYG Index as a Novel Predictor of Clinical Outcomes in Advanced Chronic Heart Failure with Renal Dysfunction Patients](https://drgezhang.com/papers/doi-10-2147-cia-s462542.html); Retrospective single-center observational biomarker study | 717 analyzed adults with advanced chronic HF, study-defined renal dysfunction and repeated HF hospitalization; 815 initially included, 98 lost to follow-up. | Study-defined broad MACEs and all-cause mortality; median follow-up 21.58 months. | ROC thresholds and associations estimated in the same analyzed cohort. | Source-cohort ROC AUC 0.759 for broad MACEs and 0.700 for all-cause mortality. | [10.2147/cia.s462542](https://doi.org/10.2147/cia.s462542) [4](https://pmc.ncbi.nlm.nih.gov/articles/PMC11068055/) |

| [Multimodal AI for cardiovascular care must learn when not to predict](https://drgezhang.com/papers/doi-10-1016-j-medd-2026-100004.html); Conceptual correspondence on cardiovascular AI evaluation | Methodological cardiovascular-AI context; no new empirical cohort. | Evidence adequacy and prediction/deferral decisions under intended use. | Five proposed evaluation conditions include incomplete inputs, natural co-missingness, staleness and external data. | Evaluation-design proposal rather than a new model-performance estimate. | [10.1016/j.medd.2026.100004](https://doi.org/10.1016/j.medd.2026.100004) [5](https://doi.org/10.1016/j.medd.2026.100004) |

Read the rows by their stated research role. Head-to-head model ranking requires aligned data, endpoints, horizons and implementations; predictive or decision-curve performance and clinical impact are different evaluations. [2](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/) [1](https://pmc.ncbi.nlm.nih.gov/articles/PMC11019967/) [3](https://pmc.ncbi.nlm.nih.gov/articles/PMC11310499/)

### Research applications

- **Methods and research design:** Use the checklist to specify the target setting, independent evaluation data, calibration/discrimination measures, prediction-error summary and any model updating before analysis. [2](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/) [1](https://pmc.ncbi.nlm.nih.gov/articles/PMC11019967/)

- **Discussion and evidence selection:** Use AIHFLevel for an external prognostic-evaluation example, TyG for admission-marker associations, and the correspondence for missingness/staleness evaluation planning, with each formal DOI tied to its actual contribution. [3](https://pmc.ncbi.nlm.nih.gov/articles/PMC11310499/) [4](https://pmc.ncbi.nlm.nih.gov/articles/PMC11068055/) [5](https://doi.org/10.1016/j.medd.2026.100004)

### Sources and locators

- [TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11019967/) · DOI: [10.1136/bmj-2023-078378](https://doi.org/10.1136/bmj-2023-078378) — Table 2: data and participants (items 5–6), outcome/predictors (8–9), analysis (12), model specification (22), performance with uncertainty (23), model updating (24).

- [Evaluation of clinical prediction models (part 2): how to undertake an external validation study](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/) · DOI: [10.1136/bmj-2023-074820](https://doi.org/10.1136/bmj-2023-074820) — What do we mean by external validation?; Steps 2–4; calibration plots, calibration measures, discrimination and clinical usefulness; Table 1.

- [AI hybrid survival assessment for advanced heart failure patients with renal dysfunction](https://pmc.ncbi.nlm.nih.gov/articles/PMC11310499/) · DOI: [10.1038/s41467-024-50415-9](https://doi.org/10.1038/s41467-024-50415-9) — Figure 6d: external time-dependent AUC; Figure 6e: calibration; Figure 6f: decision curves; Figure 6m: comparative C-index/IBS. Methods: performance evaluation; Discussion: comparator predictor-set refitting.

- [TYG Index as a Novel Predictor of Clinical Outcomes in Advanced Chronic Heart Failure with Renal Dysfunction Patients](https://pmc.ncbi.nlm.nih.gov/articles/PMC11068055/) · DOI: [10.2147/cia.s462542](https://doi.org/10.2147/cia.s462542) — Methods: Study and Population, Follow-Up and Statistical Analysis; Figures 1–3; Tables 5–6. Existing reviewed KF1–KF4 and Q&A.

- [Multimodal AI for cardiovascular care must learn when not to predict](https://doi.org/10.1016/j.medd.2026.100004) · DOI: [10.1016/j.medd.2026.100004](https://doi.org/10.1016/j.medd.2026.100004) — Existing reviewed KF1–KF3; corrected proof pp. 2–3 and Figure 1; paragraph beginning Evaluation should be defined by intended use.

## Externally evaluated HF survival-risk assessment

### AI hybrid survival assessment for advanced heart failure patients with renal dysfunction

**Authors:** Ge Zhang; Zeyu Wang; Zhuang Tong; Zhen Qin; Chang Su; Demin Li; Shuai Xu; Kaixiang Li; Zhaokai Zhou; Yudi Xu; Shiqian Zhang; Ruhao Wu; Teng Li; Youyang Zheng; Jinying Zhang; Ke Cheng; Junnan Tang

**Year:** 2024 · **Journal:** Nature Communications · **Publication type:** Article

[Author evidence page](https://drgezhang.com/papers/aihflevel.html) · [Formal publication DOI](https://doi.org/10.1038/s41467-024-50415-9) · [BibTeX](https://drgezhang.com/citations/aihflevel.bib) · [RIS](https://drgezhang.com/citations/aihflevel.ris) · [CSL JSON](https://drgezhang.com/citations/aihflevel.csl.json)

### What is AIHFLevel?

AIHFLevel is an explainable 12-predictor survival-risk assessment system developed for patients with advanced heart failure and renal dysfunction.

[Unchanged reviewed answer](https://drgezhang.com/papers/aihflevel.html#qa-1)

- [KF1](https://drgezhang.com/papers/aihflevel.html#kf1) — Results: Survival assessment system AIHFLevel; Fig. 2b

### Was AIHFLevel externally validated?

Yes. AIHFLevel was independently evaluated in 1,024 patients from BIDMC.

[Unchanged reviewed answer](https://drgezhang.com/papers/aihflevel.html#qa-3)

- [KF4](https://drgezhang.com/papers/aihflevel.html#kf4) — Fig. 6d

### Reviewed study profile

- **profile type:**
  clinical_cohort
- **study design:**
  Multicenter retrospective longitudinal cohort study
- **evidence type:**
  Human clinical prognostic modeling study
- **unique total n:**
  1736
- **population:**
  Adults with advanced heart failure and renal dysfunction
- **primary endpoint:**
  All-cause mortality
- **secondary endpoint:**
  Major adverse cardiovascular events
- **data modalities:**
  - electronic health records
  - laboratory measurements
  - clinical characteristics
  - echocardiography
- **external validation:**
  true
- **cohorts:**
  - - **name:**
      CRCCD Discovery
    - **role:**
      model development
    - **n:**
      498
    - **subset of:**
      CRCCD Meta
  - - **name:**
      CRCCD Replication
    - **role:**
      internal validation
    - **n:**
      214
    - **subset of:**
      CRCCD Meta
  - - **name:**
      CRCCD Meta
    - **role:**
      complete in-house cohort
    - **n:**
      712
    - **contains:**
      - CRCCD Discovery
      - CRCCD Replication
  - - **name:**
      BIDMC
    - **role:**
      independent external validation
    - **n:**
      1024

### Complete reviewed evidence scope

- **supports:**
  - Mortality-risk estimation in the studied advanced-heart-failure and renal-dysfunction population.
  - Internal and independent external evaluation of AIHFLevel.
  - Association between higher AIHFLevel and poorer prognosis.
  - Three-state prognostic stratification.
  - Patient-level interpretation of predictor contributions.
- **does not establish:**
  - That AIHFLevel-guided treatment improves survival or other clinical outcomes.
  - That predictors included in AIHFLevel are causal determinants of mortality.
  - That model performance is identical in every healthcare setting or population.
  - That AIHFLevel replaces clinical judgment.

### Complete reviewed limitations

- The study was retrospective and observational.
- Prospective multicenter validation is still warranted.
- Randomized studies would be required to establish whether AIHFLevel-guided treatment improves patient outcomes.
- Some echocardiographic predictors may not be uniformly available in primary-care settings.
- Direct methodological reproduction of every comparator risk model was not possible.

## Admission TyG and subsequent HF outcomes

### TYG Index as a Novel Predictor of Clinical Outcomes in Advanced Chronic Heart Failure with Renal Dysfunction Patients

**Authors:** Chang Su; Zeyu Wang; Zhen Qin; Yan Lv; Yachen Hou; Ge Zhang; Mengdie Cheng; Xinyue Cui; Zhiyu Liu; Pengchong Du; Tianding Liu; Peiyu Yuan; Junnan Tang; Jinying Zhang

**Year:** 2024 · **Journal:** Clinical Interventions in Aging · **Publication type:** Article

[Author evidence page](https://drgezhang.com/papers/doi-10-2147-cia-s462542.html) · [Formal publication DOI](https://doi.org/10.2147/cia.s462542) · [BibTeX](https://drgezhang.com/citations/doi-10-2147-cia-s462542.bib) · [RIS](https://drgezhang.com/citations/doi-10-2147-cia-s462542.ris) · [CSL JSON](https://drgezhang.com/citations/doi-10-2147-cia-s462542.csl.json)

### What was the reported MACEs association?

High versus low TyG at the 8.48 threshold had an adjusted hazard ratio of 5.402 (95% CI 3.771–7.739). This is a relative hazard association, not an absolute event rate.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-2147-cia-s462542.html#qa-3)

- [KF2](https://drgezhang.com/papers/doi-10-2147-cia-s462542.html#kf2) — PMC11068055: Results — Baseline Characteristics; Figure 2; Table 1 (Clinical and Laboratory Characteristics According to the TyG (MACEs), anchor t0001).

- [KF3](https://drgezhang.com/papers/doi-10-2147-cia-s462542.html#kf3) — PMC11068055: Table 5 — Multivariate Cox Regression Analysis Results for MACEs, TyG row (anchor t0005); Results — Relationship Between TyG and MACEs. The narrative cross-reference points to Table 4, but the verified result is in Table 5.

### Who was included in the analyzed cohort?

The analysis included 717 adults with advanced chronic HF, study-defined renal dysfunction and repeated HF hospitalization at one center. The 815 initially included patients also contained 98 who were lost to follow-up.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-2147-cia-s462542.html#qa-1)

- [KF1](https://drgezhang.com/papers/doi-10-2147-cia-s462542.html#kf1) — PMC11068055: Method — Study and Population, Inclusion Criteria, Exclusion Criteria, and Follow-Up; Figure 1; Results — Baseline Characteristics.

### Were the MACEs and mortality groups independent cohorts?

No. The two outcome-specific cutoffs regrouped the same 717 analyzed patients. Their group sizes must not be added together as independent participants.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-2147-cia-s462542.html#qa-2)

- [KF1](https://drgezhang.com/papers/doi-10-2147-cia-s462542.html#kf1) — PMC11068055: Method — Study and Population, Inclusion Criteria, Exclusion Criteria, and Follow-Up; Figure 1; Results — Baseline Characteristics.

- [KF2](https://drgezhang.com/papers/doi-10-2147-cia-s462542.html#kf2) — PMC11068055: Results — Baseline Characteristics; Figure 2; Table 1 (Clinical and Laboratory Characteristics According to the TyG (MACEs), anchor t0001).

- [KF4](https://drgezhang.com/papers/doi-10-2147-cia-s462542.html#kf4) — PMC11068055: Results — Baseline Characteristics and Relationship Between TyG and ACM; Figure 3; Table 2 (anchor t0002); Table 6 — Multivariate Cox Regression Analysis Results for ACM, TyG row (anchor t0006).

### Was the composite limited to cardiovascular death, infarction and stroke?

No. The Methods define a broad composite including non-cardiovascular death, worsening-HF rehospitalization, transplantation, circulatory support and other events. Interpretation should preserve that study-specific definition.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-2147-cia-s462542.html#qa-4)

- [KF1](https://drgezhang.com/papers/doi-10-2147-cia-s462542.html#kf1) — PMC11068055: Method — Study and Population, Inclusion Criteria, Exclusion Criteria, and Follow-Up; Figure 1; Results — Baseline Characteristics.

- [KF3](https://drgezhang.com/papers/doi-10-2147-cia-s462542.html#kf3) — PMC11068055: Table 5 — Multivariate Cox Regression Analysis Results for MACEs, TyG row (anchor t0005); Results — Relationship Between TyG and MACEs. The narrative cross-reference points to Table 4, but the verified result is in Table 5.

### Reviewed study profile

- **profile type:**
  clinical_cohort
- **study design:**
  Retrospective single-center observational cohort; admissions from September 2019 through December 2020, with follow-up completed in March 2022
- **evidence type:**
  Admission laboratory biomarker association with longitudinal outcomes, using outcome-derived ROC thresholds, Cox regression and Kaplan-Meier analyses
- **population:**
  Adults with advanced chronic heart failure, eGFR below 90 mL/min/1.73 m², and at least two heart-failure hospitalizations at the First Affiliated Hospital of Zhengzhou University; 717 analyzed after 98 losses among 815 initially included
- **primary endpoint:**
  Reported MACEs composite: cardiovascular or non-cardiovascular death, worsening-HF rehospitalization, heart transplantation, mechanical circulatory support, malignant arrhythmia, myocardial infarction, or unstable-angina rehospitalization; this is broader than a conventional three-point MACE endpoint
- **secondary endpoint:**
  All-cause mortality during follow-up; reported median follow-up 21.58 months (interquartile range 17.98–25.39)
- **data modalities:**
  - Retrospective inpatient and outpatient records
  - Admission fasting triglyceride and glucose measurements
  - Telephone and clinic follow-up
  - Clinical laboratory values and medication history
- **external validation:**
  false
- **unique total n:**
  717
- **cohorts:**
  - - **name:**
      Analyzed single-center cohort
    - **n:**
      717
    - **role:**
      Same cohort used for threshold selection, association estimation and outcome assessment

### Complete reviewed evidence scope

- **supports:**
  - A prognostic association between admission TyG and subsequent outcomes in this selected retrospective cohort.
  - Outcome-specific discrimination and hazard-ratio estimates under the study definitions and modeling choices.
- **does not establish:**
  - Causality between insulin resistance and the observed events.
  - That lowering triglyceride, glucose or TyG reduces mortality or rehospitalization.
  - External validity of the same thresholds, prospective clinical utility, or superiority to a validated clinical decision pathway.
  - A conventional three-point MACE endpoint: the study composite explicitly includes non-cardiovascular death and multiple HF-related outcomes.

### Complete reviewed limitations

- Single-center retrospective selection and residual confounding restrict causal and transportability claims.
- Thresholds were selected using the outcomes in the same dataset; no independent external validation was reported.
- Ninety-eight initially included patients were lost to follow-up, which may introduce attrition bias.
- The broad study-specific composite should not be treated as interchangeable with a standard three-point MACE outcome.
- Some narrative table cross-references do not match the displayed table captions. This page locates adjusted MACEs and ACM estimates by the actual Table 5 and Table 6 titles and anchors.
- A hazard ratio does not provide an absolute probability or demonstrate benefit from changing TyG.

## Multimodal cardiovascular AI evaluation and deferral

### Multimodal AI for cardiovascular care must learn when not to predict

**Authors:** Yahui Han; Qiang Li; Taiqi Zhao; Shanshan Cai; Biyun Li; Kaisaierjiang Kadier; Tianshu Gu; Zhonghua Sun; Pengyuan Xu; Dezhi Liu; Moyan Li; Xufeng Huang; Qian Guo; Yuan Cheng; Honglin Zheng; Ge Zhang

**Year:** 2026 · **Journal:** Medicine Discovery · **Publication type:** Correspondence

[Author evidence page](https://drgezhang.com/papers/doi-10-1016-j-medd-2026-100004.html) · [Formal publication DOI](https://doi.org/10.1016/j.medd.2026.100004) · [BibTeX](https://drgezhang.com/citations/doi-10-1016-j-medd-2026-100004.bib) · [RIS](https://drgezhang.com/citations/doi-10-1016-j-medd-2026-100004.ris) · [CSL JSON](https://drgezhang.com/citations/doi-10-1016-j-medd-2026-100004.csl.json)

### What problem does this correspondence address?

It addresses when multimodal cardiovascular AI has enough current and clinically relevant evidence to predict, and when it should defer.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1016-j-medd-2026-100004.html#qa-1)

- [KF1](https://drgezhang.com/papers/doi-10-1016-j-medd-2026-100004.html#kf1) — Corrected proof p. 1, opening paragraph

- [KF2](https://drgezhang.com/papers/doi-10-1016-j-medd-2026-100004.html#kf2) — Corrected proof pp. 2-3; Fig. 1 caption and paragraphs on abstention/deferral

### Which evaluation conditions does it propose?

Five candidate conditions are complete inputs, a critical modality missing, natural co-missingness, temporal staleness and geographically or temporally external data.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1016-j-medd-2026-100004.html#qa-3)

- [KF3](https://drgezhang.com/papers/doi-10-1016-j-medd-2026-100004.html#kf3) — Corrected proof p. 3, paragraph beginning Evaluation should be defined by intended use

### Does it report new model accuracy or a clinical trial?

No. It is a correspondence presenting conceptual proposals, with no new dataset or validated performance result.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1016-j-medd-2026-100004.html#qa-4)

- [KF1](https://drgezhang.com/papers/doi-10-1016-j-medd-2026-100004.html#kf1) — Corrected proof p. 1, opening paragraph

- [KF3](https://drgezhang.com/papers/doi-10-1016-j-medd-2026-100004.html#kf3) — Corrected proof p. 3, paragraph beginning Evaluation should be defined by intended use

### Reviewed study profile

- **profile type:**
  narrative_review
- **narrative genre:**
  correspondence
- **study design:**
  Conceptual correspondence on clinical AI evaluation
- **evidence type:**
  Author perspective and methodological proposal
- **translation scope:**
  Intended-use-specific research and evaluation considerations; not a consensus standard or validated tool
- **evidence domains:**
  - multimodal representation
  - missing data mechanisms
  - temporal validity
  - selective prediction
  - clinical workflow and equity
- **diseases covered:**
  - cardiovascular disease
- **scale metrics:**
  - - **label:**
      distinguished problem categories
    - **value:**
      5
  - - **label:**
      principles in Fig. 1
    - **value:**
      6
  - - **label:**
      candidate evaluation conditions
    - **value:**
      5
  - - **label:**
      new empirical dataset
    - **value:**
      None
- **counting note:**
  Numbers describe the conceptual framework, not patients, external cohorts, performance estimates or trial evidence.

### Complete reviewed evidence scope

- **supports:**
  - Attribution of the stated evaluation and deferral proposal to this correspondence.
  - Literature discussion of missingness, temporal context and prospective evaluation needs.
- **does not establish:**
  - Empirical improvement in discrimination, safety, equity or patient outcomes.
  - A validated AI algorithm or universal abstention threshold.
  - A consensus guideline, clinical standard or independent external validation cohort.

### Complete reviewed limitations

- Conceptual proposal without empirical validation.
- Evidence locators refer to the archived publisher corrected proof. The reviewed passages and Figure 1 caption match the current issue-assigned publisher HTML after removal of proof page headers and formatting; the current publisher PDF was not independently inspected.
- The five evaluation conditions are candidate recommendations, not consensus criteria.
