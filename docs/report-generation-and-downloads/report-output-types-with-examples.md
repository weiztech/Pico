# Report Output Types (With Examples)

## CiteMed Report Output Types

***

After completing your review many output types can be generated. They come in various forms:

* Word Document
* Excel Sheet
* Zip File (of article PDFs, or Audit Trail for example)

***



## Search Protocol Generation

***

### Search Term Summary



**Formats:** Excel, Word

**Contents:**

This is an excel sheet containing all search terms and which databases each term is scheduled to be run on. You can use it for a quick sanity check to make sure your terms are set up properly.

Example File

{% file src="../.gitbook/assets/search_terms_summary.xlsx" %}

<figure><img src="../.gitbook/assets/image (39).png" alt=""><figcaption></figcaption></figure>

***

### Search Protocol



**Formats:** Word

**Contents:** The protocol contains the contains key information about the Literature Review that will be conducted such as product info and descriptions, which databases will be searched, process for abstract review and full text review. This template can be used or modified to suit, but was designed for compliance with Meddev 2.7.1 rev4 and subsequent EU MDR.

**Key Sections**

<details>

<summary>Overview and Background</summary>

* Device Basics & Classification
* Intended Use & Target Application
* Performance & Safety Claims
* Comparative Devices

</details>

<details>

<summary>Search Methodology</summary>

* Search Scope & Date Range
* Qualified Search Personnel
* Scientific Database Coverage
* Adverse Event Database Coverage

</details>

<details>

<summary>Search Strategy</summary>

* Systematic Review Approach
* Search Term Development
* Database-Specific Techniques
* Boolean Search Parameters

</details>

<details>

<summary>Selection and Review Process</summary>

* Abstract Review Methodology
* Inclusion/Exclusion Criteria
* Full-Text Review Process
* Duplicate Management

</details>

<details>

<summary>Extraction and Appraisal Criteria</summary>

* State-of-the-Art Assessment Criteria
* Suitability & Data Contribution Scoring
* Evidence Quality Grading System
* Clinical Relevance Analysis

</details>

**Example File**

{% file src="../.gitbook/assets/protocol.docx" %}

**Images**

<div><figure><img src="../.gitbook/assets/image (40).png" alt=""><figcaption></figcaption></figure> <figure><img src="../.gitbook/assets/Selection_387.png" alt=""><figcaption></figcaption></figure> <figure><img src="../.gitbook/assets/Selection_388.png" alt=""><figcaption></figcaption></figure> <figure><img src="../.gitbook/assets/Selection_389.png" alt=""><figcaption></figcaption></figure></div>

***



## Literature Review Report Outputs

***

### Full Review Output



**Formats: Excel, Word**



**Contents(Excel):** Contains the List of articles processed during the first pass with their details. Columns Include the below:

<details>

<summary>Columns for Excel Output</summary>

* Article Title

- Abstract

* Citation

- Search Term/Database queried to get the result

* Review State (Unclassified, Retained, Excluded, Duplicate)

- Article Tags&#x20;

* Exclusion Reason

- Relevancy Score (CiteMed Calculated)

* All Extraction Fields (these are custom to your review)
  * Multi-Arm Trials Tracked Individually

- PubMed or FT Link if freely available

</details>



**Contents(Word)**:&#x20;

This is the submission-ready report template containing your entire systematic review. It will include:

<details>

<summary>Overview and Methodology</summary>

* Background ,description etc.

- Search Methodology and and Selection Criteria

* Search Methodology Summaries and Prisma Flow Chart

</details>

<details>

<summary>Search Result Summaries</summary>

Tables showing all output of both (separate) State of the Art and Subject Device Searches

Example:

<table><thead><tr><th width="120.4000244140625">Database</th><th width="137.20001220703125">Search Term</th><th>Result Count</th><th width="100">Included</th><th width="100.7999267578125">Excluded</th><th>Duplicate</th></tr></thead><tbody><tr><td>PubMed</td><td>Catheter</td><td>10</td><td>2</td><td>8</td><td>0</td></tr><tr><td>PubMed</td><td>Catether Flow Rate</td><td>25</td><td>5</td><td>12</td><td>8</td></tr></tbody></table>

</details>

<details>

<summary>Search Results (Full Review Results)</summary>

Every abstract/citation and it's state of the review (Included, Excluded with Reason, Duplicate etc.)

</details>

<details>

<summary>Data Extraction and Clinical Appraisal</summary>

Data extraction tables show per your configuration

</details>

<details>

<summary>References for Included Citations</summary>

List of references for all retained/included citations

</details>

<details>

<summary>Adverse Event Results</summary>

* Adverse event search strategy
* Adverse event results (tables summarized by incident severeity and source)
* Discussion/Commentary

</details>

<details>

<summary>Search Verification</summary>

Documented process about how searches are validated and results can be trusted.

</details>



**Images**

<div><figure><img src="../.gitbook/assets/Selection_406.png" alt=""><figcaption></figcaption></figure> <figure><img src="../.gitbook/assets/Selection_402.png" alt=""><figcaption></figcaption></figure> <figure><img src="../.gitbook/assets/Selection_414.png" alt=""><figcaption></figcaption></figure> <figure><img src="../.gitbook/assets/Selection_412.png" alt=""><figcaption></figcaption></figure> <figure><img src="../.gitbook/assets/Selection_410.png" alt=""><figcaption></figcaption></figure> <figure><img src="../.gitbook/assets/Selection_414 (1).png" alt=""><figcaption></figcaption></figure> <figure><img src="../.gitbook/assets/Selection_415.png" alt=""><figcaption></figcaption></figure> <figure><img src="../.gitbook/assets/Selection_416.png" alt=""><figcaption></figcaption></figure></div>

<figure><img src="../.gitbook/assets/Selection_394.png" alt=""><figcaption></figcaption></figure>

**Example File:**

{% file src="../.gitbook/assets/full_review_data_to_excel_example.xlsx" %}

{% file src="../.gitbook/assets/Full_LITR_2024-04-15_V1.8.docx" %}

***



### Second Pass Extraction Articles

**Formats: Word, Excel**

**Contents: C**ontains the List of included articles processed during the second pass with their appraisal details only.



**Images:**

<div><figure><img src="../.gitbook/assets/Selection_402.png" alt=""><figcaption></figcaption></figure> <figure><img src="../.gitbook/assets/Selection_400.png" alt=""><figcaption></figcaption></figure> <figure><img src="../.gitbook/assets/Selection_396.png" alt=""><figcaption></figcaption></figure> <figure><img src="../.gitbook/assets/Selection_404.png" alt=""><figcaption></figcaption></figure></div>



**Example Files:**

{% file src="../.gitbook/assets/Exctracted_Articles_Example.docx" %}

{% file src="../.gitbook/assets/Second_Pass_Articles_V2.0.xlsx" %}

***

### Prisma Diagram



**Formats**: Zip, Excel, DOCX

**Contents:** Prisma contains the Flow Chart + Table represent the different stages of the review conducting with how many articles were included, excluded, marked as duplicate ...etc

Images

<div><figure><img src="../.gitbook/assets/Selection_406.png" alt=""><figcaption></figcaption></figure> <figure><img src="../.gitbook/assets/Selection_408.png" alt=""><figcaption></figcaption></figure></div>

**Examples:**

{% file src="../.gitbook/assets/Prisma Chart.docx" %}

{% file src="../.gitbook/assets/Prisma Summary.xlsx" %}

***

### Excluded/Duplicates Summary: Excel

{% file src="../.gitbook/assets/Excluded Articles Summary.xlsx" %}

Article Tags Summary: Tags applied to articles for additional sorting: Excel

{% file src="../.gitbook/assets/Article Tags Summary.xlsx" %}

***



### Full Text Article PDFs



**Formats**: Zip

**Contents**: Contains the List of Included Articles Full Text PDFs

**Examples**:

{% file src="../.gitbook/assets/fulltexts.zip" %}

***

### Condensed Report



**Formats**: Zip of word docs

**Contents**: This is the real ‘meat’ of your report. Containing all significant sections with **only** discussion and review of the Retained literature. If you are planning to just copy out the data extraction tables into your own report template, the condensed report makes this much easier.

**Examples**:

{% file src="../.gitbook/assets/NCircle Stone Extractor (Completed Review)_Cook Medical_Condensed_LITR_2024-04-15 V1.1.docx" %}

***



### Search Validation Zip

**Formats**: Zip of several filetypes

**Contents**: The search validation zip file is for your auditors. It contains the exact search file from every single search performed directly on the associated database. This is the ultimate justification for getting a reproducible search.

**Examples**:

{% file src="../.gitbook/assets/search_verification.zip" %}

***



### Appendix E2 (Adverse Events) Report

**Formats**: Word, Excel

**Contents**: Appendix E2 contains all Maude processed events and any associated summary commentary.

**Examples:**

{% file src="../.gitbook/assets/AppendixE2_V1.1_2024-04-1.docx" %}

{% file src="../.gitbook/assets/Appendix_E2_V1.2_2024-04-.xlsx" %}

