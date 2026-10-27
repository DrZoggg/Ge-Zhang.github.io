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

## About this record

This is an author-controlled publication record in the Ge Zhang Academic Hub. It identifies this work as part of Ge Zhang’s publication record via ORCID; the publisher version remains the version of record.

<a id="limited-evidence"></a>
## Research context and source limits

Limited evidence note. Only the source material identified below has been reviewed; this is not a complete Paper GEO V2 assessment.

The complete 11-page publisher advance article and three official supplementary files have been reviewed. A conflict over the actual GWAS analysis input prevents full V2 certification; the verified source context and bounded expression observations are recorded below.

### Publication version and material reviewed

The acquired document is the publisher-typeset advance article first published on 18 December 2024, with 10 authors and DOI 10.1093/hmg/ddae189. The publisher subsequently assigned volume 34, issue 5, pages 381–391 in 2025. The complete article, supplementary figures, supplementary tables and STROBE-MR checklist are available for this review. These publication stages do not justify changing the existing bibliographic identity.

Source: [Publisher article header, author list and publication history; acquired advance-article PDF p. 1; Supplementary data: supplementary_figure_ddae189.docx, supplementary_table_ddae189.xlsx and supplementary_materials_ddae189.docx.](https://academic.oup.com/hmg/article/34/5/381/7926367)

### Blood and brain expression context

The study reports separate transcriptomic comparisons using blood dataset GSE63061 (139 Alzheimer’s disease cases and 134 controls) and brain dataset GSE33000 (310 cases and 157 controls). It constructs a senescence-related expression score from upregulated and downregulated gene sets, then integrates expression and methylation QTL with GWAS summary data. An expression-based score is not a direct count of senescent cells; these retrospective comparisons do not establish a treatment effect.

Source: [Advance-article PDF pp. 2–3, Results: Analysis of cellular senescence features in AD; p. 8, Materials and methods: Data collection and Processing; supplementary_table_ddae189.xlsx, Supplementary Table 9 gene sets and Supplementary Table 10 rows 3–5.](https://academic.oup.com/hmg/article/34/5/381/7926367)

### Unresolved analysis-input version

The article Methods and Supplementary Table 10 identify FinnGen R9 G6_ALZHEIMER and report 9,301 cases with 367,976 controls. The official R9 Risteys endpoint independently confirms 9,301 cases after genotype quality control. However, STROBE-MR item 4d reports 7,759 cases and 334,740 controls under the same R9 label. The available materials do not identify the exact outcome input file used in the reported MR runs. The official R9 case count is known; the unresolved issue is which input generated this paper’s estimates. No disputed denominator is selected and no full V2 genetic conclusion is certified.

Source: [PDF p. 8, GWAS data for Alzheimer’s disease; supplementary_table_ddae189.xlsx, Supplementary Table 10 row 6; supplementary_materials_ddae189.docx, STROBE-MR item 4d. Official cross-check: R9 Risteys G6_ALZHEIMER, Case counts → Remove individuals based on genotype QC (linked in Provenance).](https://academic.oup.com/hmg/article/34/5/381/7926367#supplementary-data)

### Cell-line follow-up and its limits

The Methods describe PC12 cells exposed to 7 μM Aβ1–42 for 12 hours. Figure 4E–G and the supplementary expression records report higher CDKN2B and ITGAV expression in treated cells than in controls. This is a cell-line expression comparison, not evidence from human Alzheimer’s disease neurons or a demonstration of therapeutic benefit. Because the plotted qPCR scale and supplementary values are inconsistent, this note does not certify an exact fold change or plotted significance value.

Source: [PDF p. 9, Cell culture and Aβ1–42-induced AD modeling and RNA isolation, reverse transcription, and quantitative real-time PCR; Figure 4E–G; supplementary_table_ddae189.xlsx, sheets labelled Supplemenatry Table 7 (B3:C6, B9:C12) and Supplemenatry Table 8; Supplementary Figures 5–6.](https://academic.oup.com/hmg/article/34/5/381/7926367#supplementary-data)

### Evidence limits

- Full V2 remains on hold until an exact archived GWAS input filename/release and checksum, linked to the analysis code or run record, or a formal author clarification resolves which dataset generated the MR estimates. Agreement between the main Methods and the official R9 case count does not establish the analysis input used.
- The source contains unresolved mediation annotations: Figure 1 labels an EXOSC9 probe differently from Table 1/Figure 3C, and Figure 3 coefficients differ from the MR tables, including a SLFN12 sign discrepancy. This note neither corrects the labels nor certifies the proposed mediation chains.
- The qPCR supplement lists four values per group per target and the immunoblot supplement lists three entries per group; biological independence is not specified. The qPCR plot/table scale discrepancy remains unresolved, so no exact fold change, effective biological sample size or plotted P value is certified.
- MR depends on instrument relevance, independence and exclusion restriction. The reported sensitivity checks do not prove all assumptions, and the supplement reports significant SLFN12 heterogeneity. Gene-target causality is not established by this limited note.
- The PC12 experiments measure expression after an amyloid-peptide challenge. They do not test gene knockdown or rescue, animal disease modification, patient outcomes, or the safety and efficacy of a treatment. An ambiguous CDKN2B primer character and absent GAPDH primer sequence in Supplementary Table 11 also limit reproducibility.

### Provenance

- [Official publisher article and publication history](https://academic.oup.com/hmg/article/34/5/381/7926367) — Publisher HTML and complete 11-page publisher-typeset advance-article PDF obtained through the authorized author account. DOI 10.1093/hmg/ddae189; advance publication 18 December 2024; final issue 34(5), 381–391 (2025). Main Figures 1–4, Table 1 and Methods were reviewed.
- [Official publisher supplementary data](https://academic.oup.com/hmg/article/34/5/381/7926367#supplementary-data) — Three unique files: two DOCX files and one XLSX workbook, acquired 27 October 2026. supplementary_figure_ddae189.docx: Figures 1–6; supplementary_table_ddae189.xlsx: Tables 1–11; supplementary_materials_ddae189.docx: STROBE-MR checklist, especially item 4d. These materials have been obtained and inspected.
- [FinnGen R9 official Alzheimer endpoint](https://r9.risteys.finngen.fi/endpoints/G6_ALZHEIMER) — Official Risteys endpoint HTML, retrieved 27 October 2026. G6_ALZHEIMER: Case counts → Remove individuals based on genotype QC, 9,301 cases. Control definition is all non-cases; this page does not independently supply the paper’s exact control total or identify its actual analysis input.

Source review: 2026-10-27.

## Links

- DOI: https://doi.org/10.1093/hmg/ddae189
- HTML page: https://drgezhang.com/papers/doi-10-1093-hmg-ddae189.html
- Google Scholar query: https://scholar.google.com/scholar?q=%22Integrated%20multi-omics%20analysis%20revealed%20the%20molecular%20networks%20and%20potential%20targets%20of%20cellular%20senescence%20in%20Alzheimer%E2%80%99s%20disease%22
- ORCID: https://orcid.org/0000-0002-3116-3246
