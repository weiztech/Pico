# Upload Search Results

Now that we have a protocol created, it’s time to run and upload all search results! This is the most involved portion of the application.

**Results are either:**

* Automatically downloaded by us
* Uploaded manually by you (uploading your search results file)

## The Search Dashboard

Run Searches screen can be accessed from the Main Menu.

<figure><img src="../.gitbook/assets/image (19).png" alt=""><figcaption></figcaption></figure>

**There are two ways to import search data:**

* Upload results files manually
* Use the AutoSearch functionality.

### Using Automated Searches

Automated searches are available for the following databases on different levels of consistency.

* PubMed (Very Consistent)
* PubMed Central (Very Consistent)
* Cochrane Library (Medium)
* [Clinicalrials.gov](http://clinicalrials.gov) (Medium)
* FDA Maude Adverse Events (Medium)

### Automated Search Protocol

Remember when you selected databases and thresholds like Max Result counts in the [‘Search Protocol’](https://citemedical.notion.site/624483282e594f7d8bb71611100fd7cc?pvs=25#e7f77717f29d4e338958feb3603922a5) section? These settings will be used when running the automated searches, so give them a double-check before continuing.

### Run an Automated Search

It only takes one click to start your automated search. Click “RUn Auto Search” for the term you want to run.

<figure><img src="../.gitbook/assets/image (20).png" alt=""><figcaption></figcaption></figure>

## Understanding Search Results and Status

### The ‘State’ of a Search

There are 3 states a search can be in, indicated by background color of the row, and the Status Column

| State     | Background Color | Description                                                   |
| --------- | ---------------- | ------------------------------------------------------------- |
| COMPLETE  | Green            | This search has been run and results imported successfully.   |
| NOT RUN   | Purple           | The search is still pending, and needs to be run or uploaded. |
| ERROR     | Red              | The search experienced an error when processing.              |
| Excluded  | Orange           | The search has been excluded (too many results, or 0).        |



Consider the five below searches. One is not run, two are excluded, one is complete, and one is an error.

<figure><img src="../.gitbook/assets/image (21).png" alt=""><figcaption></figcaption></figure>

### Understanding the Search Result Counts

You will see 4 squares with different numbers relating to a specific Search’s results.

<figure><img src="../.gitbook/assets/image (22).png" alt=""><figcaption></figcaption></figure>

<table><thead><tr><th width="152">Result Type</th><th>Description</th></tr></thead><tbody><tr><td>Expected</td><td>This is the number from the Search Terms page prediction. It is not always 100% accurate and doesn’t have to match the other fields.</td></tr><tr><td>Imported</td><td>This is the number of articles that were saved successfully into your <a href="http://citemed.io/">CiteMed.io</a> database.</td></tr><tr><td>Processed</td><td>This is the number of articles that were found in the search result file. This should match the ‘Imported’ count exactly.</td></tr><tr><td>Duplicates</td><td>These were the number of duplicate articles identified and marked during the search (we will search for duplicates across the entire project, not just a single search).</td></tr></tbody></table>

## Running Manual Searches

### What is a Manual Search?

Manual searches are when you go to a specific database to run the search yourself, and download the results for upload into [CiteMed.io](http://citemed.io/).

### Why upload searches manually?

There are two reasons to do this yourself:

* You want to use a database we don’t support automatic collection on (Like Embase)
* The automatic download function is not working for you.

### Which Databases Accept Manual Searches?

All databases except manual uploads. The following are **required for manual upload**:

* Embase

### How to Run Your Manual Searches

Instructions are provided in the application as well. But for specific examples and details of how to run, download, and upload a search you can find them here.

1. Perform the search and download the results file (see below document for Database Specific Instructions)\
   [Running Manual Searches on the CiteMed App](https://citemedical.notion.site/Running-Manual-Searches-on-the-CiteMed-App-83bfe99fb6b9408eb45c67eb13d996e0?pvs=24)
2.  Click ‘Upload Manual Search’ for your specific search term and database. This is on the ‘Upload Search Results’ Page.\
    \


    <figure><img src="../.gitbook/assets/image (23).png" alt=""><figcaption></figcaption></figure>
3.  Upload the correct filetype , and click ‘Save’.\
    \


    <figure><img src="../.gitbook/assets/image (24).png" alt=""><figcaption></figcaption></figure>

### How to Perform The Right Manual Searches

Note that performing manual searches means you’re responsible for adding the right dates and article type filters to your search.

Additionally, you need to make sure that you are exporting those results into a file format we can read. In the above example, you can see for a PubMed search, XML, and TXT formats are accepted.

### Accepted Database Export File Formats

| PubMed             | TXT, XML |
| ------------------ | -------- |
| PubMed Central     | TXT, XML |
| ClinicalTrials.gov | CSV      |
| Cochrane           | TXT      |
| Embase             | RIS      |
| FDA Maude          | CSV      |

