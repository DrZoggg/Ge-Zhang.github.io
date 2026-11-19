# GSE59867 sample and follow-up map

Use this [436-row CSV](https://drgezhang.com/assets/research/gse59867-sample-followup-map.csv) to connect expression-sample accessions to the public patient labels and collection times in GEO before planning a repeated-sample analysis. It preserves the original sample titles and metadata alongside a label extracted directly from each title.

## Available samples

The public metadata contains **436 unique GSM accessions and 157 distinct title-derived labels**: 111 longitudinal Patient labels account for 390 samples, and 46 Control patient labels account for one sample each. GEO's study design describes the former as STEMI patients and the controls as stable coronary artery disease patients without a history of myocardial infarction.

| Collection recorded by GEO | Samples |
| --- | ---: |
| First day of MI, admission | 111 |
| 4-6 days after MI, discharge | 101 |
| One month after MI | 95 |
| Six months after MI | 83 |
| N/A, control samples | 46 |

Among the 111 longitudinal labels, 3 have one recorded sample, 10 have two, 25 have three and 73 have four. Missing follow-up samples are not filled in. These are post-infarction collection times, rather than measurements across a 24-hour circadian cycle.

## Use the map

1. Join expression data to this table by **GSM accession**, checking that each accession matches once. The CSV follows GEO's metadata column order, but joining by identifier is safer than assuming row order.
2. For a new patient-separated train/test split or resampling analysis, group by **GSE59867 plus `public_patient_label`**, keeping repeated samples with that source label together. This is a label copied from this series' public sample titles, not a verified identifier for matching people across datasets.
3. Select collection times from `original_collection`. Preserve the title's sampling number as context; the table does not invent missing visits or collection dates.
4. Keep the heart-failure field as recorded. **326 rows contain `hf progression: N/A`**. The other values are HF in 34 rows, non-HF in 30 and stable CAD in 46. No outcome label has been carried from one visit to another, and N/A is not a negative outcome.

The six CSV columns are `GSM`, `original_title`, `public_patient_label`, `original_collection`, `original_hf_progression` and `original_cell_type`. All 436 rows retain GEO's PBMC cell-type field. Patient labels are the exact text before `,sampling N`; control labels preserve the entire original title. No suffix removal, fuzzy matching or cross-dataset identity matching is applied.

## Sources and related research

The source is [GSE59867 in GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE59867), specifically the sample metadata before the expression table in the [official series-matrix file](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE59nnn/GSE59867/matrix/GSE59867_series_matrix.txt.gz), retrieved on 15 November 2026. Source fields are `!Sample_geo_accession`, `!Sample_title` and the collection, HF-progression and cell-type rows of `!Sample_characteristics_ch1`. GEO links the original dataset publication, [PMID 25984239](https://pubmed.ncbi.nlm.nih.gov/25984239/), and [BioProject PRJNA256954](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA256954).

### Published analyses using GSE59867

These papers analyze the archived series for different questions. Cite the original study and GEO record for the samples, and the relevant paper for its analysis.

- [Plaque-vulnerability signature development](https://doi.org/10.1016/j.isci.2023.107587). The APVS study used GSE59867 for STEMI versus chronic coronary syndrome gene filtering and included it in its development and internal test split (STAR Methods and Fig. S1B–C).
- [Molecular subtype assignment](https://doi.org/10.1186/s12967-022-03795-9). The smooth muscle cell fate study applied discovery-derived subtype templates to GSE59867 PBMC profiles (nearest-template prediction and Fig. 6C).
- [Circadian-related expression subtyping](https://doi.org/10.1038/s41598-024-65236-5). The ischemic heart disease study reused this series for retrospective molecular subtyping. The GEO collection fields record time since infarction.
- [Admission-only diagnostic comparison](https://doi.org/10.3389/fcvm.2026.1904246). A cross-cohort study compared 111 STEMI admission samples with 46 stable coronary artery disease samples and excluded repeated visits from its diagnostic training comparison (Methods §§2.1 and 2.4).
- [Longitudinal expression analysis](https://doi.org/10.1371/journal.pone.0358983). A recovery-trajectory study analyzed serial samples from 81 eligible STEMI participants. Its recovery grouping was defined from gene expression (Methods and Figs. 1–3).

See the [circadian-IHD study evidence and formal citation](https://drgezhang.com/papers/circadian-ihd.html). This author-prepared metadata lookup supports new analysis planning; it supplies no expression values and does not reconstruct the secondary studies’ original splits or results.
