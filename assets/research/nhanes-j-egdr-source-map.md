# NHANES 2017-2018 source map for eGDR, hyperuricemia and gout

A source-linked core-variable lookup for one survey cycle inside the study's 2007-2018 period. Use it to find files and definitions before planning a new analysis. It is not an analysis-ready dataset or a reproduction of the pooled study.

The source study relates eGDR to prevalent hyperuricemia and gout. This map connects its definitions to the **2017-2018 J-cycle** codebooks; the two outcomes use the same study sample.

## Locate the inputs

| Use | File and variable | Unit or coding |
| --- | --- | --- |
| Join key | [`DEMO_J.xpt`: `SEQN`](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DEMO_J.htm) | Identifier; no physical unit |
| eGDR waist input | [`BMX_J.xpt`: `BMXWAIST`](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/BMX_J.htm) | cm; numeric missing is . |
| eGDR HbA1c input | [`GHB_J.xpt`: `LBXGH`](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/GHB_J.htm) | %; numeric missing is . |
| Hypertension diagnosis component | [`BPQ_J.xpt`: `BPQ020`](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/BPQ_J.htm) | 1 Yes;2 No;7 Refused;9 Don't know |
| Hypertension current-medication component | [`BPQ_J.xpt`: `BPQ050A`](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/BPQ_J.htm) | 1 Yes;2 No;7 Refused;9 Don't know; . may reflect questionnaire routing |
| Hypertension measured-BP component | [`BPX_J.xpt`: `BPXSY1`, `BPXSY2`, `BPXSY3`, `BPXSY4`, `BPXDI1`, `BPXDI2`, `BPXDI3`, `BPXDI4`](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/BPX_J.htm) | mmHg; . missing; recorded diastolic0 is possible |
| Hyperuricemia laboratory input | [`BIOPRO_J.xpt`: `LBXSUA`](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/BIOPRO_J.htm) | mg/dL; . missing |
| Gout outcome | [`MCQ_J.xpt`: `MCQ160n`](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/MCQ_J.htm) | 1 Yes; 2 No; 7 Refused; 9 Do not know; . Missing |
| Age eligibility | [`DEMO_J.xpt`: `RIDAGEYR`](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DEMO_J.htm) | years;80+ top-coded80 |
| Recorded-sex threshold selector | [`DEMO_J.xpt`: `RIAGENDR`](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DEMO_J.htm) | 1 Male; 2 Female; . Missing |
| Pregnancy exclusion source | [`DEMO_J.xpt`: `RIDEXPRG`](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DEMO_J.htm) | 1 Pregnant by test or self-report; 2 Not pregnant at exam; 3 Cannot ascertain; . Missing. Released for females aged 20-44. |
| Exam weighting | [`DEMO_J.xpt`: `WTMEC2YR`](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DEMO_J.htm) | Full-sample 2-year MEC exam weight; 0 indicates not MEC examined |
| Variance design | [`DEMO_J.xpt`: `SDMVSTRA`, `SDMVPSU`](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DEMO_J.htm) | Masked variance stratum; masked pseudo-PSU |

Join the selected component files by **SEQN**, rather than row order. The linked codebooks document each field; the accompanying [JSON source map](https://drgezhang.com/assets/research/nhanes-j-egdr-source-map.json) retains exact source locators and the decisions to document.

## Apply the reported definitions

- **eGDR (mg/kg/min)** = 21.158 - 0.09 × waist circumference (cm) - 3.407 × hypertension (1 yes, 0 no) - 0.551 × HbA1c (%). HbA1c in mmol/mol needs conversion before using this percent-based formula.
- **Hypertension:** the paper names reported physician diagnosis, current antihypertensive medication or average blood pressure at its 140/90 mmHg threshold. BPQ020 alone is not the full definition. BPQ050A asks about current use; BPQ040A asks about being advised to take medication.
- **Hyperuricemia:** serum urate strictly greater than 7.0 mg/dL for recorded male participants, or 6.0 mg/dL for recorded female participants. Use LBXSUA in mg/dL; LBDSUASI is the SI-unit field. Missing urate or category is not a negative outcome.
- **Gout:** MCQ160n records prior diagnosis by a doctor or another health professional. Code 1 is Yes and 2 is No; 7, 9 and missing are not negative responses.

## Decide these before estimating

1. **Blood-pressure summary and routing.** BPX_J provides repeated readings; the article does not give its precise averaging/valid-reading rule or full missing-input logic. BPQ050A also has questionnaire routing. Document a defensible rule for the new analysis rather than silently labelling it the original implementation.
2. **Eligibility.** The study includes adults aged at least 20 and excludes pregnancy. RIDEXPRG is publicly released for females aged 20-44, including a Cannot ascertain category. Missing/out-of-scope records are not automatically confirmed nonpregnant and should not all be dropped without considering the variable's release population.
3. **Weights and variance.** Retain SDMVSTRA and SDMVPSU with the linked records. WTMEC2YR is the two-year MEC exam weight; zero denotes not MEC examined. The paper does not name its exact pooled weight construction. This J-cycle lookup does not supply a six-cycle estimator.
4. **Laboratory comparability.** BIOPRO_J documents 2017-2018 instrument/method changes and bridging guidance for combining with earlier cycles or examining trends. Consult those notes before pooling; this map applies no adjustment and does not establish how the paper handled it.
5. **Full models.** Additional covariates, their supplemental definitions, imputation and sensitivity analyses require separate choices and sources. They are not supplied by this core-variable map.

## Sources and use

Formal study: [Association between higher estimated glucose disposal rate and reduced prevalence of hyperuricemia and gout](https://doi.org/10.3389/fnut.2025.1658286). Read Methods 2.2 for the formula and hypertension, 2.3 for outcomes and 2.5 for statistical methods in the [published full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC12501789/). Cite the paper for its reported study and definitions, and the linked CDC codebooks for dataset fields.

Author-prepared research planning resource, 15 November 2026. Field names follow the published codebooks; inspect imported XPT columns before use. The resource supplies linked definitions and planning decisions; it reports no new association or model-performance result.
