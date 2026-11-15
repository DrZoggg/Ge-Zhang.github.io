# Cancer omics: subtype transfer, prognosis and network-state evidence

**Selected author evidence guide**

[Canonical comparison](https://drgezhang.com/research/cancer-omics-validation.html)

## How should a new cancer cohort be used for molecular subtyping, prognostic scoring, network-state analysis or immunotherapy-response assessment?

A source-linked worked comparison and reusable reporting worksheet for choosing analyses in a new cancer cohort. Six examples separate molecular subtyping, survival prognosis, stage-associated network states and treatment-response evidence, using reviewed study facts and identified methodological guidance.

Start with the intended output, cohort and observation unit. Then identify the model/template/network object, its implementation and updating, independent evaluation data, endpoint/time and response measurements. Keep the separate analyses of one publication in separate worksheet rows and cite the original DOI for study findings.

## Which analysis and evidence should be carried into a new external cancer cohort?

为新的外部癌症队列选择分析时，应迁移什么对象，怎样报告其验证证据？

**Source-linked methodological synthesis:** Define the output first. HCCcrds provides a molecular-subtype and cohort-role example; the thyroid study separates a stage-associated DNB state from a compact subtype classifier; LPAS contributes a retrospective survival-score example; the TNBC work distinguishes molecular-state profiling, a mixed-cancer response-model pipeline and target-cancer proxy analyses. ConsensusClusterPlus can assess resampling stability, and SubMap can assess molecular correspondence across independently defined subclasses. For prediction models, record unchanged implementation versus updating/refitting. For treatment claims, identify actual outcome-linked response data separately from molecular proxies. The worksheet makes these choices explicit before a new-cohort analysis. [1](https://doi.org/10.1016/j.joim.2025.06.003) [2](https://doi.org/10.3389/fonc.2025.1538574) [3](https://doi.org/10.1002/mdr2.70004) [4](https://doi.org/10.1111/jcmm.18408) [5](https://pmc.ncbi.nlm.nih.gov/articles/PMC2881355/) [6](https://pmc.ncbi.nlm.nih.gov/articles/PMC2065909/) [7](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/)

先确定所需输出。HCCcrds提供分子亚型及队列用途的实例；甲状腺研究区分分期相关DNB网络状态与紧凑亚型分类器；LPAS提供回顾性生存风险评分实例；TNBC研究则需分开分子状态、混合癌种响应模型和目标癌种中的预测proxy。ConsensusClusterPlus可评估重采样下的聚类稳定性，SubMap可评估独立数据中既定亚类的分子对应。对预测模型，记录是否原样应用、更新或重拟合；对治疗主张，另列真实结局关联响应数据。工作表用于在新队列分析前明确这些选择。

### Evaluation checklist

- **Output, cohort and unit:** Record the intended molecular label, survival endpoint, network-state output or treatment response; identify independent patients/specimens and development/model-selection overlap. [1](https://doi.org/10.1016/j.joim.2025.06.003) [2](https://doi.org/10.3389/fonc.2025.1538574) [3](https://doi.org/10.1002/mdr2.70004) [4](https://doi.org/10.1111/jcmm.18408)

- **Stability and molecular correspondence:** Use consensus stability to inspect robustness under subsampling and subclass mapping to inspect cross-dataset correspondence. Report the data, labels/features and method settings for the task actually performed. [5](https://pmc.ncbi.nlm.nih.gov/articles/PMC2881355/) [6](https://pmc.ncbi.nlm.nih.gov/articles/PMC2065909/)

- **Prediction-model implementation:** For a prognostic or response model, retain the model version, features/weights, preprocessing and any change or refit. Record assessment on data separate from development and selection. [7](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/) [4](https://doi.org/10.1111/jcmm.18408) [2](https://doi.org/10.3389/fonc.2025.1538574)

- **Endpoint and time:** For survival, state endpoint, time origin, horizon, follow-up and censoring. For stage/network analysis, state the stage/reference groups and whether observations are cross-sectional or longitudinal. [7](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/) [4](https://doi.org/10.1111/jcmm.18408) [3](https://doi.org/10.1002/mdr2.70004)

- **Observed response or proxy:** Name the cancer, treatment, sampling time and response definition when measured. Otherwise report the named immune score, expression mapping or predicted group, and keep it separate from observed benefit. [2](https://doi.org/10.3389/fonc.2025.1538574) [1](https://doi.org/10.1016/j.joim.2025.06.003) [3](https://doi.org/10.1002/mdr2.70004) [4](https://doi.org/10.1111/jcmm.18408) [6](https://pmc.ncbi.nlm.nih.gov/articles/PMC2065909/)

- **Reusable cohort-role source:** Use the existing HCC worked example and five-dataset CSV for Fig.5A/B membership. This comparison adds output/implementation/reporting roles rather than another accession roster. [9](https://github.com/DrZoggg/ClockProCRC/blob/main/docs/hcc-cohort-comparison.md) [1](https://doi.org/10.1016/j.joim.2025.06.003)

### Choose and report an analysis for a new external cancer cohort

Use one row per analysis, cohort, model version and endpoint. Record the output before selecting a method. Split subtype assignment, survival prognosis, network state and treatment response into their actual roles. NR means unresolved in this extraction, not that the original paper omitted a detail. For a new cohort, report the artifact, preprocessing, every adaptation/refit, independence, endpoint/time and available treatment labels; use the blank CSV to retain those decisions.

[Download completed worksheet (CSV)](https://drgezhang.com/research/cancer-omics-validation.worksheet.csv) · [Download blank worksheet (CSV)](https://drgezhang.com/research/cancer-omics-validation.blank.csv)

| Reported analysis | Output and research task | Application / refit status | Time reference and endpoint | Evaluation actually supported | Immunotherapy evidence role | Claim to report | Sources |

| --- | --- | --- | --- | --- | --- | --- | --- |

| HCCcrds external subtype evaluation | Molecular subtype assignment, not an individual survival-risk model | External expression/classification evaluation is reported. Whether every preprocessing/template element was frozen is NR here; do not relabel fresh clustering as unchanged classifier application | Expression-defined CS-H/CS-L/CS-M labels; not measured physiological circadian phase | Retrospective cross-dataset subtype evaluation. Reuse the linked cohort-role worksheet rather than copying its accession inventory | Separate CIBERSORT/IPS analyses are inferred immune properties, not observed ICI response | Report external subtype assignment/reproducibility with the actual implementation status; keep subtype labels separate from survival prediction | [1](https://doi.org/10.1016/j.joim.2025.06.003) [9](https://github.com/DrZoggg/ClockProCRC/blob/main/docs/hcc-cohort-comparison.md) |

| LPAS retrospective LUAD survival-score evaluation | Prognostic expression score associated with overall survival | Retrospective external dataset evaluation is reported. Applying an unchanged score and re-estimating coefficients/cutoffs in the new cohort are different analyses | Overall survival; retain time origin, horizon, censoring and the exact metric definition in each analysis row | Retrospective external survival evaluation; no prospective LPAS-guided clinical decision validation | TIDE/SubMap and heterogeneous treatment-cohort associations are separate from an observed response study in the intended new LUAD population | Report the actual score implementation and retrospective prognosis task. Do not rank its survival AUC against subtype accuracy or ICI-response AUC | [4](https://doi.org/10.1111/jcmm.18408) |

| ISG15-related classifier in mixed-cancer ICI source data | Retrospective treated-response classification, distinct from TNBC molecular-state profiling | The reported evaluation is within a pooled source-data pipeline, not independent treated-TNBC external validation | ICI response label in the source treatment cohorts; label definition and pretreatment timing must be verified for reuse | Modest retrospective response discrimination in other-cancer source data; source cohorts being external to the TNBC atlas does not make the internal split independent TNBC validation | Response-labeled treated source data are a different evidence role from TIDE or a predicted-response group in an untreated/unclear-treatment cohort | Name the pooled/internal evaluation and its cancer context. Do not report a validated TNBC treatment-selection test | [2](https://doi.org/10.3389/fonc.2025.1538574) |

| ISG15 predicted-response groups in TNBC-related application analyses | Predicted group, immune-signature or survival association; not observed ICI response in treated TNBC | Application/association layer; do not treat a new grouping or retrospective survival contrast as independent response-model validation | Predicted-response group, immune estimate and overall survival are separate endpoints | Target-TNBC computational proxy analyses and a nonsignificant TCGA TNBC survival comparison; source-data response-model evaluation is recorded in its separate row | TIDE dysfunction/exclusion and predicted-response labels are computational proxies; they are not measured clinical response | State predicted-response/immune-association results at their actual scope, without claiming treatment benefit | [2](https://doi.org/10.3389/fonc.2025.1538574) |

| Thyroid DNB stage-associated network state | Cross-sectional stage-associated network instability, not longitudinal individual transition prediction | Reconstructing a network/state calculation in new data is a distinct analysis from applying the separate miniPC subtype classifier | Reported Stage II instability peak across stage groups; no observed within-person time-to-transition clock | Stage-associated molecular evidence. It does not establish when a new patient's disease will deteriorate | IPS/CMap are computational immune/drug hypotheses; no observed immunotherapy-response trial is established | Report a stage-associated network-state analysis and its grouping assumptions; do not call it prospective dynamic-risk validation | [3](https://doi.org/10.1002/mdr2.70004) |

| Thyroid miniPC external molecular-subtype classification | Compact classifier of consensus subtype labels, separate from the DNB-state analysis and TCPSLevel survival associations | Externally reported subtype-classifier evaluation. Training a new network or changing the label-generating clustering is a separate fit | Subtype assignment; neither a treatment-response label nor an individual transition time | Retrospective expression-template/classifier evaluation; internal cluster stability is not external clinical validation | Separate IPS/CMap results remain hypotheses rather than measured patient response | Report subtype classification at its actual evaluation scope. Do not call miniPC a validated survival model | [3](https://doi.org/10.1002/mdr2.70004) |

#### Decisions from the comparison

- **Define the output and unit:** Choose molecular subtype, prognostic risk, a group/network state or observed response before evaluating a new dataset. State the observation unit, reference labels and the particular analysis supported by each cohort. [1](https://doi.org/10.1016/j.joim.2025.06.003) [2](https://doi.org/10.3389/fonc.2025.1538574) [3](https://doi.org/10.1002/mdr2.70004) [4](https://doi.org/10.1111/jcmm.18408)

- **Use stability and correspondence for their positive tasks:** ConsensusClusterPlus supplies repeated-subsampling stability and membership evidence. SubMap tests correspondence between previously defined subclasses across independently generated datasets. The reporting inference is that a stability plot or molecular association matrix alone does not supply clinical outcomes that were not measured; the original SubMap paper also includes separate prediction and survival analyses. [5](https://pmc.ncbi.nlm.nih.gov/articles/PMC2881355/) [6](https://pmc.ncbi.nlm.nih.gov/articles/PMC2065909/)

- **Separate prediction-model application from updating:** For a prognostic or response predictor, identify the original model/feature/weight artifact and document any recalibration, coefficient/cutoff refit or retraining, with its development and assessment data. This prediction-model guidance is not used to judge unsupervised clustering as though it were a fixed clinical risk model. [7](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/) [4](https://doi.org/10.1111/jcmm.18408) [2](https://doi.org/10.3389/fonc.2025.1538574)

- **Keep stage-associated states separate from patient time:** The thyroid DNB comparison is cross-sectional and stage-associated. Reconstructing its network/state output and applying miniPC subtype labels are distinct analyses; neither supplies an observed within-patient transition time merely from stage membership. [3](https://doi.org/10.1002/mdr2.70004)

- **Identify the response evidence actually present:** Record treatment, pretreatment sampling, cancer and measured response when available. Distinguish mixed-cancer source-data evaluation from a new cancer-specific response cohort. IPS/TIDE, predicted-response groups and SubMap molecular correspondence retain their actual computational roles. [2](https://doi.org/10.3389/fonc.2025.1538574) [1](https://doi.org/10.1016/j.joim.2025.06.003) [3](https://doi.org/10.1002/mdr2.70004) [4](https://doi.org/10.1111/jcmm.18408) [6](https://pmc.ncbi.nlm.nih.gov/articles/PMC2065909/)

- **Reuse the existing HCC cohort-role table:** For HCC Fig.5A subtype versus Fig.5B survival membership, follow the existing worked example and CSV. Do not recreate its dataset list in this resource. Keep cross-study metric ranking unset when tasks, endpoint/time definitions or implementations differ. [1](https://doi.org/10.1016/j.joim.2025.06.003) [9](https://github.com/DrZoggg/ClockProCRC/blob/main/docs/hcc-cohort-comparison.md) [7](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/)

### How the selected papers contribute

- **[Molecular-subtype transfer and analysis-specific cohort roles](https://drgezhang.com/papers/doi-10-1016-j-joim-2025-06-003.html):** HCCcrds connects subtype assignment to retrospective outcome and immune analyses. Its external subtype and survival sets overlap but differ; the linked cohort-role worksheet supplies their membership. [1](https://doi.org/10.1016/j.joim.2025.06.003) [9](https://github.com/DrZoggg/ClockProCRC/blob/main/docs/hcc-cohort-comparison.md)

- **[TME molecular association and mixed-cancer response modeling](https://drgezhang.com/papers/doi-10-3389-fonc-2025-1538574.html):** The study contributes TNBC molecular-state comparisons and a separate retrospective ICI-response classifier pipeline. Its mixed-cancer pooled internal evaluation and TNBC proxy/association analyses retain distinct roles. [2](https://doi.org/10.3389/fonc.2025.1538574)

- **[Stage-associated network state and separate subtype classifier](https://drgezhang.com/papers/doi-10-1002-mdr2-70004.html):** DNB instability across stage groups, TCPSLevel associations and miniPC subtype classification are distinct outputs within one study. The stage-associated analysis supplies no observed individual transition time. [3](https://doi.org/10.1002/mdr2.70004)

- **[Retrospective survival-risk-signature evaluation](https://drgezhang.com/papers/doi-10-1111-jcmm-18408.html):** LPAS contributes a prognosis task with additional survival-series evaluation. Its immune/treatment associations and cell-functional experiments are separate from unchanged-score survival evaluation or model updating. [4](https://doi.org/10.1111/jcmm.18408)

### Choose the analysis by its output, evaluation unit and source evidence

| Paper / design | Population | Endpoint / horizon | Validation | Reported evaluation | Original source |

| --- | --- | --- | --- | --- | --- |

| [Integrated-omics analysis defines subtypes of hepatocellular carcinoma based on circadian rhythm](https://drgezhang.com/papers/doi-10-1016-j-joim-2025-06-003.html); Retrospective single-cell/bulk integration and HCC subtype evaluation | HCC expression cohorts, with separate circadian reference experiments | Molecular subtype assignment; subtype-survival comparisons in separately designated datasets | External expression/classification and retrospective outcome comparisons; use the linked cohort-role table to select the relevant analysis set | Subtype and survival analyses have different cohort roles; do not add the overlapping Fig.5A/B sets into an independent-cohort total | [10.1016/j.joim.2025.06.003](https://doi.org/10.1016/j.joim.2025.06.003) [1](https://doi.org/10.1016/j.joim.2025.06.003) [9](https://github.com/DrZoggg/ClockProCRC/blob/main/docs/hcc-cohort-comparison.md) |

| [Resolving tumor microenvironment heterogeneity to forecast immunotherapy response in triple-negative breast cancer through multi-scale analysis](https://drgezhang.com/papers/doi-10-3389-fonc-2025-1538574.html); TNBC multi-modal association plus secondary mixed-cancer ICI-response classifier development | BRCA1-defined TNBC specimens and separately pooled treated cohorts from other cancers | TME molecular states; response classification in the mixed-cancer source data; separate target-cohort predicted-group associations | Within-pooled-source development/evaluation; the study explicitly lacks an independent treated-TNBC response cohort | Retrospective KNN discrimination is distinct from TIDE estimates, predicted-response groups and survival associations | [10.3389/fonc.2025.1538574](https://doi.org/10.3389/fonc.2025.1538574) [2](https://doi.org/10.3389/fonc.2025.1538574) |

| [Optimized Dynamic Network Biomarker Deciphers a High-Resolution Heterogeneity Within Thyroid Cancer Molecular Subtypes](https://drgezhang.com/papers/doi-10-1002-mdr2-70004.html); Stage-associated network analysis, molecular subtyping and compact subtype-classifier evaluation | Public thyroid-cancer expression cohorts; single-cell and tissue/cell follow-up remain separate evidence layers | DNB network instability, TCPSLevel and miniPC subtype assignment are distinct outputs | Cross-sectional stage-associated DNB evidence; separate retrospective external template/classifier evaluation | A stage-associated instability peak is not an individual transition-time forecast; miniPC classification is not a survival-benefit evaluation | [10.1002/mdr2.70004](https://doi.org/10.1002/mdr2.70004) [3](https://doi.org/10.1002/mdr2.70004) |

| [Deciphering lung adenocarcinoma evolution: Integrative single-cell genomics identifies the prognostic lung progression associated signature](https://drgezhang.com/papers/doi-10-1111-jcmm-18408.html); Retrospective transcriptomic survival modeling with separate cell-functional and immune analyses | TCGA development and additional GEO LUAD survival series; other analytic layers are kept separate | LPAS-associated overall survival; immune/treatment associations have their own definitions | Additional retrospective survival-series evaluation; any new-cohort refitting must be reported separately from unchanged-score application | Use horizon-specific survival evidence and the actual implementation; immune matching or cell perturbation is a different evaluation | [10.1111/jcmm.18408](https://doi.org/10.1111/jcmm.18408) [4](https://doi.org/10.1111/jcmm.18408) [7](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/) |

Use these rows for applicability and reporting, rather than to rank unlike performance measures. The original methods establish resampling stability and cross-dataset subclass correspondence as positive capabilities. Requiring measured outcome-linked evidence for a clinical or response claim is this resource's task-based inference, not a statement that those method authors reject clinical applications. External-validation guidance is applied here to prediction models, not as a universal clustering criterion. [5](https://pmc.ncbi.nlm.nih.gov/articles/PMC2881355/) [6](https://pmc.ncbi.nlm.nih.gov/articles/PMC2065909/) [7](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/) [1](https://doi.org/10.1016/j.joim.2025.06.003) [2](https://doi.org/10.3389/fonc.2025.1538574) [3](https://doi.org/10.1002/mdr2.70004) [4](https://doi.org/10.1111/jcmm.18408)

### Research applications

- **Plan a new external-cohort analysis:** Select the intended output and fill one blank row for each cohort/model/endpoint. Identify the original artifact and distinguish unchanged application, adaptation/refit, new clustering/network construction and observed-response assessment before running the analysis. [7](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/) [5](https://pmc.ncbi.nlm.nih.gov/articles/PMC2881355/) [6](https://pmc.ncbi.nlm.nih.gov/articles/PMC2065909/) [1](https://doi.org/10.1016/j.joim.2025.06.003) [3](https://doi.org/10.1002/mdr2.70004) [4](https://doi.org/10.1111/jcmm.18408) [2](https://doi.org/10.3389/fonc.2025.1538574)

- **Report Methods and Discussion:** Carry the source version, exact locator, actual data role, implementation changes and unresolved details into the manuscript. Use the omics review for narrative methodological context and the primary studies for their empirical claims; this new comparison does not imply the older review cited the later studies. [8](https://doi.org/10.1007/s13402-023-00912-8) [1](https://doi.org/10.1016/j.joim.2025.06.003) [2](https://doi.org/10.3389/fonc.2025.1538574) [3](https://doi.org/10.1002/mdr2.70004) [4](https://doi.org/10.1111/jcmm.18408)

### Sources and locators

- [Integrated-omics analysis defines subtypes of hepatocellular carcinoma based on circadian rhythm](https://doi.org/10.1016/j.joim.2025.06.003) · DOI: [10.1016/j.joim.2025.06.003](https://doi.org/10.1016/j.joim.2025.06.003) — Author-deposited Results 3.3-3.7, Figures 4-6. Detailed figure locators use the ahead-of-print copy; final typeset figure equivalence has not been rechecked.

- [Resolving tumor microenvironment heterogeneity to forecast immunotherapy response in triple-negative breast cancer through multi-scale analysis](https://doi.org/10.3389/fonc.2025.1538574) · DOI: [10.3389/fonc.2025.1538574](https://doi.org/10.3389/fonc.2025.1538574) — PMC12401915 Methods s2_10, Results s3_9, Figure 8D-K and Discussion s4.

- [Optimized Dynamic Network Biomarker Deciphers a High-Resolution Heterogeneity Within Thyroid Cancer Molecular Subtypes](https://doi.org/10.1002/mdr2.70004) · DOI: [10.1002/mdr2.70004](https://doi.org/10.1002/mdr2.70004) — Methods 2.2/2.6-2.8; Results 3.1/3.3-3.4; Figures 1/3-4. Immune hypotheses: Methods 2.10/2.20, Results 3.5/3.9.

- [Deciphering lung adenocarcinoma evolution: Integrative single-cell genomics identifies the prognostic lung progression associated signature](https://doi.org/10.1111/jcmm.18408) · DOI: [10.1111/jcmm.18408](https://doi.org/10.1111/jcmm.18408) — PMC11149493 Methods 2.8 (jcmm18408-sec-0010), Results 3.3-3.4 (sec-0026/0027), Figures 4-5; immune/treatment analyses Results 3.5/3.7/3.9, Figures 6/8/10.

- [ConsensusClusterPlus: a class discovery tool with confidence assessments and item tracking](https://pmc.ncbi.nlm.nih.gov/articles/PMC2881355/) · DOI: [10.1093/bioinformatics/btq170](https://doi.org/10.1093/bioinformatics/btq170) — Introduction SEC1/p[1]; Software Features SEC2/p[1]; Example Application SEC3/p[1]. Repeated subsampling, consensus stability and item tracking; same-input software comparison is described as an integrity check.

- [Subclass Mapping: Identifying Common Subtypes in Independent Disease Data Sets](https://pmc.ncbi.nlm.nih.gov/articles/PMC2065909/) · DOI: [10.1371/journal.pone.0001195](https://doi.org/10.1371/journal.pone.0001195) — Materials and Methods s4b1 candidate subclasses; s4b2-s4b4 mutual marker enrichment and subclass-association matrix. The paper separately describes prediction (s4c) and survival (s4d) analyses.

- [Evaluation of clinical prediction models (part 2): how to undertake an external validation study](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788734/) · DOI: [10.1136/bmj-2023-074820](https://doi.org/10.1136/bmj-2023-074820) — What do we mean by external validation?; Steps 2-4; Table 1 and performance/calibration sections. Applied here to clinical prediction-model implementation and updating, not as a rule for unsupervised clustering.

- [Omics-based molecular classifications empowering in precision oncology](https://doi.org/10.1007/s13402-023-00912-8) · DOI: [10.1007/s13402-023-00912-8](https://doi.org/10.1007/s13402-023-00912-8) — Sections 3.1.4-3.1.5, 5.1-5.2 and 6. Narrative molecular-classification and translation context; later primary examples in this author-maintained resource are separately sourced.

- [Worked example: select HCC cohorts by analysis purpose](https://github.com/DrZoggg/ClockProCRC/blob/main/docs/hcc-cohort-comparison.md) · DOI: [10.1016/j.joim.2025.06.003](https://doi.org/10.1016/j.joim.2025.06.003) — Author-maintained cohort-role worksheet and linked data/hcc-cohort-roles.csv, derived from HCCcrds Results 3.5/Figure 5A-B for that same study.

## HCC molecular-subtype assignment and cohort-specific outcome comparisons

### Integrated-omics analysis defines subtypes of hepatocellular carcinoma based on circadian rhythm

**Authors:** Xiao-jie Li; Le Chang; Yang Mi; Ge Zhang; Shan-shan Zhu; Yue-xiao Zhang; Hao-yu Wang; Yi-shuang Lu; Ye-xuan Ping; Peng-yuan Zheng; Xia Xue

**Year:** 2025 · **Journal:** Journal of Integrative Medicine · **Publication type:** Article

[Author evidence page](https://drgezhang.com/papers/doi-10-1016-j-joim-2025-06-003.html) · [Formal publication DOI](https://doi.org/10.1016/j.joim.2025.06.003) · [BibTeX](https://drgezhang.com/citations/doi-10-1016-j-joim-2025-06-003.bib) · [RIS](https://drgezhang.com/citations/doi-10-1016-j-joim-2025-06-003.ris) · [CSL JSON](https://drgezhang.com/citations/doi-10-1016-j-joim-2025-06-003.csl.json)

### Which HCC subtypes were associated with clinical outcomes?

TCGA-LIHC analysis identified CS-H, CS-L and CS-M, with poorer outcomes associated with CS-H. TCGA-LIHC n: 369; Subtypes: CS-H; CS-L; CS-M. Association does not establish that circadian disruption causes liver cancer or constitute a validated clinical decision rule.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1016-j-joim-2025-06-003.html#qa-3)

- [KF3](https://drgezhang.com/papers/doi-10-1016-j-joim-2025-06-003.html#kf3) — Author-deposited full text: Results 3.3-3.4; Fig. 4

### Were external classification and survival analyses performed in identical cohorts?

External subtype and survival analyses used overlapping but different cohort sets. Fig. 5A datasets: ICGC_LIRI; GSE14520; GSE54236; GSE104580; Fig. 5B datasets: ICGC_LIRI; GSE14520; GSE54236; GSE27150. Do not claim that all five cohorts validated survival, or add the two four-cohort analyses as eight independent cohorts.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1016-j-joim-2025-06-003.html#qa-4)

- [KF4](https://drgezhang.com/papers/doi-10-1016-j-joim-2025-06-003.html#kf4) — Author-deposited full text: Results 3.5; Fig. 5 legend

### Do the immune analyses demonstrate immunotherapy benefit?

Subtypes differed in proliferation/metabolic programs and inferred immune characteristics. Analyses: Expression enrichment; CIBERSORT; IPS. IPS and immune deconvolution are not an observed immunotherapy-response trial.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1016-j-joim-2025-06-003.html#qa-5)

- [KF5](https://drgezhang.com/papers/doi-10-1016-j-joim-2025-06-003.html#kf5) — Author-deposited full text: Results 3.6-3.7; Fig. 6

### Reviewed study profile

- **profile type:**
  multicohort_omics
- **study design:**
  Public single-cell and bulk transcriptomic integration with retrospective subtype evaluation
- **evidence type:**
  Human molecular association and cross-dataset classification analysis
- **population:**
  HCC expression cohorts, with separate circadian reference experiments
- **primary endpoint:**
  HCCcrds-associated molecular subtype structure
- **secondary endpoint:**
  Retrospective outcome associations and computational biological annotations
- **data modalities:**
  - single-cell RNA sequencing
  - bulk transcriptomics
  - co-expression analysis
  - LRA clustering/NTP
  - immune deconvolution
- **external validation:**
  true
- **scale metrics:**
  - - **label:**
      TCGA-LIHC
    - **value:**
      369 samples in the reported analysis
  - - **label:**
      GSE149614 analyzed cells
    - **value:**
      11,383 cells
  - - **label:**
      External datasets
    - **value:**
      5 datasets with different analytical roles
- **counting note:**
  Cell counts, candidate genes, HCC cohort samples and separate circadian reference experiments are different units. No complete unique-participant total is inferred. The five external datasets have different analytical uses: the four Fig. 5A and four Fig. 5B sets overlap but are not identical and must not be added as eight independent cohorts. External validation means retrospective cross-dataset expression/classification evaluation, not prospective clinical utility or direct physiological rhythm measurement in HCC patients.

### Complete reviewed evidence scope

- **supports:**
  - Single-cell modules supplied the HCCcrds gene set.
  - The score was evaluated in separate clock, feeding and sleep-reference data.
  - TCGA-LIHC analysis identified CS-H, CS-L and CS-M, with poorer outcomes associated with CS-H.
  - External subtype and survival analyses used overlapping but different cohort sets.
  - Subtypes differed in proliferation/metabolic programs and inferred immune characteristics.
  - NNMT and MARCKSL1 were among subtype-associated candidate genes.
- **does not establish:**
  - Prospective diagnostic or prognostic clinical utility.
  - Direct individual measurement of physiological circadian phase or amplitude.
  - Circadian disruption as a demonstrated cause of cancer.
  - Clinical benefit from score-guided treatment.
  - IPS as measured response in patients receiving immunotherapy.
  - Therapeutic validation of the candidate genes.
  - Completed page-by-page equivalence checking between the author-deposited text and final typeset version.
  - Unprovided AUCs, hazard ratios, participant totals or additional omics modalities.

### Complete reviewed limitations

- Cell counts, candidate genes, HCC cohort samples and separate circadian reference experiments are different units. No complete unique-participant total is inferred. The five external datasets have different analytical uses: the four Fig. 5A and four Fig. 5B sets overlap but are not identical and must not be added as eight independent cohorts. External validation means retrospective cross-dataset expression/classification evaluation, not prospective clinical utility or direct physiological rhythm measurement in HCC patients.
- Cells and candidate genes are not patient counts or demonstrated causal regulators.
- Reference-experiment evaluation does not mean HCC patients underwent longitudinal physiological circadian measurements.
- Association does not establish that circadian disruption causes liver cancer or constitute a validated clinical decision rule.
- Do not claim that all five cohorts validated survival, or add the two four-cohort analyses as eight independent cohorts.
- IPS and immune deconvolution are not an observed immunotherapy-response trial.
- This evidence synthesis does not claim independent causal intervention or therapeutic validation of these genes.
- Prospective diagnostic or prognostic clinical utility.
- Direct individual measurement of physiological circadian phase or amplitude.
- Circadian disruption as a demonstrated cause of cancer.
- Clinical benefit from score-guided treatment.
- IPS as measured response in patients receiving immunotherapy.
- Therapeutic validation of the candidate genes.
- Completed page-by-page equivalence checking between the author-deposited text and final typeset version.
- Unprovided AUCs, hazard ratios, participant totals or additional omics modalities.
- Bibliographic identity was checked against the final PubMed/publisher record. Detailed evidence locators refer to the author-deposited full text; final typeset figure-level equivalence was not independently re-established.

## TNBC TME associations and cross-cancer ICI-response modeling

### Resolving tumor microenvironment heterogeneity to forecast immunotherapy response in triple-negative breast cancer through multi-scale analysis

**Authors:** Shihao Sun; Shuang Chen; Kaiyuan Li; Ge Zhang; Nan Wang; Yijia Xu; Xinxing Wang; Jiangrui Chi; Lin Li; Yi Sun

**Year:** 2025 · **Journal:** Frontiers in Oncology · **Publication type:** Article

[Author evidence page](https://drgezhang.com/papers/doi-10-3389-fonc-2025-1538574.html) · [Formal publication DOI](https://doi.org/10.3389/fonc.2025.1538574) · [BibTeX](https://drgezhang.com/citations/doi-10-3389-fonc-2025-1538574.bib) · [RIS](https://drgezhang.com/citations/doi-10-3389-fonc-2025-1538574.ris) · [CSL JSON](https://drgezhang.com/citations/doi-10-3389-fonc-2025-1538574.csl.json)

### How well did the ICI response model discriminate?

The selected KNN classifier reported AUC 0.60 (95% CI 0.51–0.69) for validation and 0.61 (95% CI 0.51–0.71) for testing in the external-treatment source data.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-3389-fonc-2025-1538574.html#qa-4)

- [KF4](https://drgezhang.com/papers/doi-10-3389-fonc-2025-1538574.html#kf4) — PMC12401915: Methods Reconstruction of the ICI response predictor (s2_10); Results Construction of an ISG15-driven predictive system (s3_9); Figure 8D–G. Paper text inconsistency: Methods mentions 13 cohorts (n=829); Results mentions 12.

### Was the ICI model validated in treated TNBC patients?

No. The Discussion explicitly identifies the lack of validation in ICI-treated TNBC cohorts; it is inappropriate to claim established TNBC treatment selection.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-3389-fonc-2025-1538574.html#qa-5)

- [KF4](https://drgezhang.com/papers/doi-10-3389-fonc-2025-1538574.html#kf4) — PMC12401915: Methods Reconstruction of the ICI response predictor (s2_10); Results Construction of an ISG15-driven predictive system (s3_9); Figure 8D–G. Paper text inconsistency: Methods mentions 13 cohorts (n=829); Results mentions 12.

- [KF5](https://drgezhang.com/papers/doi-10-3389-fonc-2025-1538574.html#kf5) — PMC12401915: Results Construction of an ISG15-driven predictive system for ICI response (s3_9); Figure 8H–K; Discussion (s4), paragraph explicitly stating no ICI-treated TNBC validation.

### How many ICI cohorts did the authors use?

The article is inconsistent: Methods describes 13 pretreatment ICI cohorts (829 records) whereas Results mentions 12 cohorts. Four cohorts pooled as 661 records for the principal development split can be identified; the other cohort count is not silently harmonized.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-3389-fonc-2025-1538574.html#qa-7)

- [KF4](https://drgezhang.com/papers/doi-10-3389-fonc-2025-1538574.html#kf4) — PMC12401915: Methods Reconstruction of the ICI response predictor (s2_10); Results Construction of an ISG15-driven predictive system (s3_9); Figure 8D–G. Paper text inconsistency: Methods mentions 13 cohorts (n=829); Results mentions 12.

### Reviewed study profile

- **profile type:**
  multicohort_omics
- **study design:**
  Retrospective single-cell TNBC group comparison, spatial reference mapping, bulk expression/network prioritization, paired in-house tissue proteomics and secondary immunotherapy-response classifier development.
- **evidence type:**
  Human multi-modal observational molecular association with a mixed-cancer retrospective treatment-response model; no experimental causal gene perturbation.
- **population:**
  Eight BRCA1-defined TNBC single-cell specimens; four BRCA1-WT TNBC spatial samples; independently collected 9 paired breast tumor/adjacent tissues; mixed-cancer ICI-response expression cohorts for model training/testing.
- **primary endpoint:**
  Differences in single-cell and spatially inferred tumor immune/stromal programs across BRCA1 status.
- **secondary endpoint:**
  ISG15/myCAF association and retrospective response-model discrimination in cross-cancer ICI cohorts.
- **data modalities:**
  - TNBC single-cell RNA sequencing
  - Spatial RNA expression reference mapping
  - Bulk expression, coexpression and pathway analysis
  - Paired tissue label-free proteomics
  - Cross-cancer ICI transcriptomic response modeling
- **external validation:**
  false
- **scale metrics:**
  - - **label:**
      TNBC single-cell donors
    - **value:**
      8 specimens: 4 BRCA1-mutant and 4 BRCA1 wild-type
  - - **label:**
      Cells after QC
    - **value:**
      32,386; 18,182 BRCA1-mutant and 14,204 BRCA1 wild-type
  - - **label:**
      Spatial specimens
    - **value:**
      4 BRCA1-WT TNBC spatial samples; no matched BRCA1-MT spatial series in this analysis
  - - **label:**
      Paired proteomics
    - **value:**
      9 tumor samples and 9 corresponding para-tumor specimens; nine pairs, not 18 independent patients
  - - **label:**
      ICI model pooled subset
    - **value:**
      Four external treatment cohorts pooled to 661 records and divided 80:20 internally
  - - **label:**
      KNN classifier discrimination
    - **value:**
      Reported validation AUC 0.60 (95% CI 0.51–0.69); testing AUC 0.61 (95% CI 0.51–0.71)
- **counting note:**
  Cell profiles, donor tumor specimens, spatial samples, paired proteomic tissues and external cross-cancer treated cohorts are distinct counting units and may involve overlaps or subsets. The article inconsistently describes 13 ICI pre-treatment cohorts (829 records) in Methods versus 12 in Results; no unsupported sum or cohort count is promoted.

### Complete reviewed evidence scope

- **supports:**
  - Cell-state and CAF-associated transcriptomic differences between the eight sampled BRCA1 groups.
  - Spatially associated ISG15 and myCAF signals within the four BRCA1-WT spatial specimens.
  - Retrospective mixed-cancer ICI response model discrimination near AUC 0.60–0.61 under the described analysis.
- **does not establish:**
  - Causal BRCA1 control of CAF differentiation or a verified ISG15 immune-response mechanism from the multi-omics associations.
  - Independently validated or clinically useful ICI prediction specifically for treated TNBC patients.
  - Excellent predictive discrimination, proven chemotherapy/ICI treatment efficacy or a validated treatment-selection cut-off.
  - A statistically significant TCGA TNBC overall-survival contrast (reported P=0.182).
  - A verified universal count of distinct participants across cell, spatial, paired protein and ICI cohorts.

### Complete reviewed limitations

- The main BRCA1 genotype comparison is only 4 versus 4 tissue donors; cells are not independent participant replicates.
- Spatial transcriptome mapping used four BRCA1-WT cases and therefore is not a genotype-balanced spatial replication.
- ICI cohort descriptions conflict (13 cohorts n=829 in Methods vs 12 in Results), requiring scope-limited cohort reporting.
- The selected KNN internal validation/test AUCs are approximately 0.60–0.61, not high discrimination; use and model selection on validation data constrain performance interpretation.
- No ICI-treated TNBC response cohort directly validates this cross-cancer model.
- The article reports TCGA TNBC overall-survival P=0.182; this comparison is nonsignificant.

## Thyroid stage-associated DNB states and separate miniPC subtype classification

### Optimized Dynamic Network Biomarker Deciphers a High-Resolution Heterogeneity Within Thyroid Cancer Molecular Subtypes

**Authors:** Haonan Zhang; Ge Zhang; Pengyuan Xu; Fengyi Yu; Liwen Li; Runzhi Huang; Pengpeng Zhang; Kaisaierjiang Kadier; Yuanyuan Wang; Qiqi Gu; Yalei Ding; Tianshu Gu; Hao Chi; Shiqian Zhang; Ruhao Wu; Yudi Xu; Shanshan Zhu; Honglin Zheng; Taiqi Zhao; Qi He; Xinguang Qiu

**Year:** 2025 · **Journal:** Med Research · **Publication type:** Article

[Author evidence page](https://drgezhang.com/papers/doi-10-1002-mdr2-70004.html) · [Formal publication DOI](https://doi.org/10.1002/mdr2.70004) · [BibTeX](https://drgezhang.com/citations/doi-10-1002-mdr2-70004.bib) · [RIS](https://drgezhang.com/citations/doi-10-1002-mdr2-70004.ris) · [CSL JSON](https://drgezhang.com/citations/doi-10-1002-mdr2-70004.csl.json)

### What does the Stage II DNB signal establish?

Stage II had the highest reported network instability signal. DNB genes: 36. Cross-sectional stage comparisons do not establish longitudinal prediction of each patient's future deterioration time.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1002-mdr2-70004.html#qa-1)

- [KF1](https://drgezhang.com/papers/doi-10-1002-mdr2-70004.html#kf1) — Methods 2.2; Results 3.1; Fig. 1

### How were the thyroid molecular subtypes evaluated externally?

The ensemble analysis yielded three molecular subtypes. Candidate combinations: 20; Selected combination: CV-PAM; Reported external NTP datasets: 6. Methods 2.6 prints GSE333630 whereas other locations use GSE33630. These are not silently rewritten as a fully verified accession inventory.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1002-mdr2-70004.html#qa-3)

- [KF3](https://drgezhang.com/papers/doi-10-1002-mdr2-70004.html#kf3) — Methods 2.6-2.7; Results 3.3; Fig. 3

### Does miniPC classify subtypes or directly prove improved survival?

miniPC classified the consensus subtype labels using a compact gene set. Candidate genes: 296; Final genes: 12; Final classifier: Neural network; External classifier cohorts: 5. This is subtype classification, not prospective individual survival-benefit validation. Unverified figure-only accuracy or AUC values are not reconstructed.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1002-mdr2-70004.html#qa-4)

- [KF4](https://drgezhang.com/papers/doi-10-1002-mdr2-70004.html#kf4) — Methods 2.8; Results 3.4; Fig. 4

### Were CMap-nominated compounds shown to benefit patients?

IPS and CMap supplied candidate immune/drug-response hypotheses. Evidence: Computational scoring and signature matching. Predicted compounds are not proven effective treatments. IPS is not an observed outcome in patients receiving immunotherapy.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1002-mdr2-70004.html#qa-7)

- [KF7](https://drgezhang.com/papers/doi-10-1002-mdr2-70004.html#kf7) — Methods 2.10 and 2.20; Results 3.5 and 3.9; Figure 7G-I; Discussion

### Reviewed study profile

- **profile type:**
  multicohort_omics
- **study design:**
  Public bulk/single-cell analysis with human tissue assessment and cell experiments
- **evidence type:**
  Retrospective molecular subtyping with experimental candidate follow-up
- **population:**
  Thyroid-cancer datasets and tissue specimens, with separate cultured-cell experiments
- **primary endpoint:**
  DNB-associated expression structure and molecular subtype assignment
- **secondary endpoint:**
  Retrospective outcome associations and ASPH-related experimental readouts
- **data modalities:**
  - bulk transcriptomics
  - single-cell RNA sequencing
  - network/classifier analysis
  - human immunohistochemistry
  - in-vitro gene perturbation
- **external validation:**
  true
- **scale metrics:**
  - - **label:**
      GEO microarray cohorts
    - **value:**
      21 cohorts, plus TCGA
  - - **label:**
      TCGA count in Methods
    - **value:**
      544
  - - **label:**
      TCGA count in GRN analysis
    - **value:**
      484
  - - **label:**
      scRNA cells in Methods
    - **value:**
      17,709
  - - **label:**
      scRNA cells in Results
    - **value:**
      17,518
  - - **label:**
      Reported single-cell donors
    - **value:**
      1
  - - **label:**
      Human tissue specimens
    - **value:**
      48 tumor and 48 adjacent specimens
- **counting note:**
  TCGA counts of 544 in Methods and 484 in GRN analysis describe different reported analytical stages; no reason for excluding the numerical difference is inferred. Methods reports 17,709 cells and Results 17,518, without a reconstructed QC-exclusion process. One reported donor is not a large participant cohort; 48 tumor and 48 adjacent specimens do not mean 96 independent patients. Cohorts, cells, paired specimens and cultured-cell experiments are not added into a unique-participant total. External validation means retrospective expression-template/classifier evaluation, not prospective clinical utility.

### Complete reviewed evidence scope

- **supports:**
  - Stage II had the highest reported network instability signal.
  - TCPSLevel was associated with clinical and outcome differences.
  - The ensemble analysis yielded three molecular subtypes.
  - miniPC classified the consensus subtype labels using a compact gene set.
  - Single-cell analysis localized expression patterns across cellular compartments.
  - ASPH was evaluated in human tissues and through TPC-1 silencing.
  - IPS and CMap supplied candidate immune/drug-response hypotheses.
- **does not establish:**
  - Longitudinal prediction of an individual patient's transition time.
  - Clinical intervention benefit.
  - miniPC as an established survival model rather than a subtype classifier.
  - Cell counts as patient counts or paired-specimen counts as independent participants.
  - Complete demonstration of direct ASCL2 regulation or binding.
  - Clinical efficacy of CMap-nominated compounds.
  - Classification of this study as a physiological circadian-rhythm experiment.
  - Resolution of all Methods/Results counts or accession differences.

### Complete reviewed limitations

- TCGA counts of 544 in Methods and 484 in GRN analysis describe different reported analytical stages; no reason for excluding the numerical difference is inferred. Methods reports 17,709 cells and Results 17,518, without a reconstructed QC-exclusion process. One reported donor is not a large participant cohort; 48 tumor and 48 adjacent specimens do not mean 96 independent patients. Cohorts, cells, paired specimens and cultured-cell experiments are not added into a unique-participant total. External validation means retrospective expression-template/classifier evaluation, not prospective clinical utility.
- Cross-sectional stage comparisons do not establish longitudinal prediction of each patient's future deterioration time.
- The reported cutoff is not a cross-cohort locked clinical threshold. Grouping rules used in other analyses are not automatically equivalent.
- Methods 2.6 prints GSE333630 whereas other locations use GSE33630. These are not silently rewritten as a fully verified accession inventory.
- This is subtype classification, not prospective individual survival-benefit validation. Unverified figure-only accuracy or AUC values are not reconstructed.
- A single donor and a large cell count do not establish large-population replication. No explanation for the count difference is invented.
- Paired tissues are not 96 independent patients. ASCL2-ASPH network inference is not direct binding validation, and cell effects do not establish human targeted-treatment efficacy.
- Predicted compounds are not proven effective treatments. IPS is not an observed outcome in patients receiving immunotherapy.
- Longitudinal prediction of an individual patient's transition time.
- Clinical intervention benefit.
- miniPC as an established survival model rather than a subtype classifier.
- Cell counts as patient counts or paired-specimen counts as independent participants.
- Complete demonstration of direct ASCL2 regulation or binding.
- Clinical efficacy of CMap-nominated compounds.
- Classification of this study as a physiological circadian-rhythm experiment.
- Resolution of all Methods/Results counts or accession differences.

## LUAD LPAS survival-score evaluation and separate immune/treatment associations

### Deciphering lung adenocarcinoma evolution: Integrative single-cell genomics identifies the prognostic lung progression associated signature

**Authors:** Pengpeng Zhang; Zijun Yang; Zuo Liu; Ge Zhang; Lianmin Zhang; Zhenfa Zhang; Jun Fan

**Year:** 2024 · **Journal:** Journal of Cellular and Molecular Medicine · **Publication type:** Article

[Author evidence page](https://drgezhang.com/papers/doi-10-1111-jcmm-18408.html) · [Formal publication DOI](https://doi.org/10.1111/jcmm.18408) · [BibTeX](https://drgezhang.com/citations/doi-10-1111-jcmm-18408.bib) · [RIS](https://drgezhang.com/citations/doi-10-1111-jcmm-18408.ris) · [CSL JSON](https://drgezhang.com/citations/doi-10-1111-jcmm-18408.csl.json)

### What is the nine-gene LPAS model?

LPAS is a retrospective expression-based LUAD survival score containing nine selected genes, including PSMB1. It was developed from TCGA data and evaluated in five additional GEO survival series.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1111-jcmm-18408.html#qa-2)

- [KF3](https://drgezhang.com/papers/doi-10-1111-jcmm-18408.html#kf3) — PMC11149493: Methods §2.8 (jcmm18408-sec-0010); Results §§3.3–3.4 (jcmm18408-sec-0026, jcmm18408-sec-0027); Figures 4B–G and 5A–F.

### Was LPAS externally evaluated?

Five additional GEO LUAD survival datasets were evaluated, with differing reported AUCs and follow-up horizons. This is retrospective external dataset evaluation, not a prospective treatment-impact trial.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1111-jcmm-18408.html#qa-3)

- [KF3](https://drgezhang.com/papers/doi-10-1111-jcmm-18408.html#kf3) — PMC11149493: Methods §2.8 (jcmm18408-sec-0010); Results §§3.3–3.4 (jcmm18408-sec-0026, jcmm18408-sec-0027); Figures 4B–G and 5A–F.

### Can low LPAS identify patients who will benefit from immunotherapy?

The article reports in-silico immune scores and SubMap/TIDE comparisons plus treatment-cohort associations, but no prospective LPAS-guided treatment study establishes patient-level clinical benefit.

[Unchanged reviewed answer](https://drgezhang.com/papers/doi-10-1111-jcmm-18408.html#qa-5)

- [KF4](https://drgezhang.com/papers/doi-10-1111-jcmm-18408.html#kf4) — PMC11149493: Results §§3.5, 3.7, 3.9 (jcmm18408-sec-0028, jcmm18408-sec-0030, jcmm18408-sec-0032); Figures 6A–C, 8D–G, 10A–L.

### Reviewed study profile

- **profile type:**
  multicohort_omics
- **study design:**
  Secondary integration of human LUAD single-cell and bulk expression cohorts with retrospective survival modeling, computational immune/drug-response inference and in-vitro PSMB1 perturbation.
- **evidence type:**
  Human transcriptomic association, retrospective model evaluation and LUAD cell-line functional assays.
- **population:**
  Early pathological LUAD tissue samples across AIS, MIA and IAC; independent retrospective GEO/TCGA LUAD survival cohorts and additional tumor-treatment series from heterogeneous cancers.
- **primary endpoint:**
  Association of the LPAS expression score with overall survival in retrospective LUAD series.
- **secondary endpoint:**
  Single-cell state contrasts across pathological stages; immune/stromal signature associations; computational immunotherapy/drug-response hypotheses; PSMB1 knockdown cell phenotypes.
- **data modalities:**
  - Two publicly available LUAD scRNA-seq series
  - TCGA and GEO transcriptomic and clinical survival data
  - Exploratory external treatment-response expression datasets
  - Local LUAD RNA sequencing
  - A549 and H1299 siRNA perturbation assays
- **external validation:**
  true
- **scale metrics:**
  - - **label:**
      Single-cell specimen scale
    - **value:**
      GSE189357 and GSE150938: 4 AIS, 8 MIA and 9 IAC specimens (21 reported across pathology groups)
  - - **label:**
      Independent survival-series list
    - **value:**
      GSE13213 (119), GSE29016 (39), GSE30219 (86), GSE31210 (227) and GSE68465 (443) as reported analyzed series
  - - **label:**
      Model discovery
    - **value:**
      TCGA-LUAD; cohort n not inferred from unspecified filtering
  - - **label:**
      Local stage-associated RNA sequencing
    - **value:**
      14 LUAD surgical specimens (reported)
  - - **label:**
      LPAS signature
    - **value:**
      9 genes
- **counting note:**
  The 21 scRNA-seq specimens, 14 local RNA-seq specimens, TCGA cases, five survival cohorts and mixed-cancer immunotherapy datasets represent distinct analytic layers; neither cross-dataset independence nor a synthetic unique-patient total is inferred.

### Complete reviewed evidence scope

- **supports:**
  - Cluster 6 and LPAS show reproducible associations in the reported transcriptomic cohorts.
  - Higher LPAS corresponds to less favorable retrospective LUAD survival in the evaluated cohorts.
  - PSMB1 silencing reduces selected proliferation and movement phenotypes in A549/H1299 assays.
- **does not establish:**
  - A directly traced longitudinal path from an AIS cell to an IAC cell or a causal origin of Cluster 6.
  - Independent prospective diagnostic, treatment selection, or outcome improvement from LPAS.
  - Clinical benefit from PSMB1 inhibition, LPAS-guided immunotherapy or computationally prioritized compounds.
  - Unique participant counts aggregated across partially overlapping or heterogeneous public datasets.

### Complete reviewed limitations

- Early stages and bulk outcome datasets are distinct study populations; pseudotime is not lineage tracing.
- Source dataset descriptions include heterogeneous immunotherapy studies, and the article uses different counting contexts rather than a single combined n.
- Single-cell immune estimates and simulated drug sensitivity are not direct measurements of clinical response.
- PSMB1 siRNA provides selected in-vitro evidence, not an in-vivo drug efficacy or clinical trial.
