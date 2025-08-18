# Product Requirements Document: PICO Category Labeling for Literature Searches

## 1. Introduction/Overview

This document outlines the requirements for a new feature that allows regulatory affairs specialists to assign PICO category labels to literature searches within their literature reviews. The goal is to enhance the organization and clarity of search methodology, aligning with regulatory standards for systematic reviews. This feature will introduce an optional `pico_category` field to each literature search, enabling users to categorize them as **P**opulation, **I**ntervention, **C**omparator, or **O**utcome.

## 2. Goals

*   To provide users with the ability to categorize literature searches according to the PICO framework.
*   To improve the structure and documentation of search strategies within the platform.
*   To enable easier review and management of literature searches through filtering and clear visual cues.
*   To implement this functionality for single and multiple (bulk) literature searches.

## 3. User Stories

*   **As a regulatory affairs specialist,** I want to assign a PICO category to each literature search so that I can clearly document my search methodology.
*   **As a regulatory affairs specialist,** I want to see the PICO category for each search in my literature search list so I can quickly assess the balance of my search strategy.
*   **As a regulatory affairs specialist,** I want to bulk-assign a PICO category to multiple literature searches at once to save time.
*   **As a regulatory affairs specialist,** I want to filter my literature searches by PICO category to focus on specific aspects of my search strategy during review.

## 4. Functional Requirements

1.  **Database Schema:**
    *   File to modify: `lit_reviews/models.py`
    *   The `lit_reviews_literaturesearch` table must be updated with a new optional field named `pico_category`.
    *   This field should store a value from a predefined set of choices (Enum): `POPULATION`, `INTERVENTION`, `COMPARATOR`, `OUTCOME`.
    *   The field can be `NULL`.

2.  **PICO Category Enum:**
    *   File to modify: `lit_reviews/models.py`
    *   A `PicoCategoryEnum` shall be created to define the available categories.
    *   The `pico_category` field is optional and will be `NULL` by default for all existing and newly created literature searches.

3.  **API Updates:**
    *   Files to modify:
        *   `lit_reviews/api/search_terms/serializers.py`
        *   `lit_reviews/api/search_terms/views.py`
    *   The `CreateNewSearchTermSerializer` and `UpdateSearchTermSerializer` must be updated to accept an optional `pico_category` parameter.
    *   The `SearchTermsView` (`/api/search-terms/<int:id>/`) will be modified for creating and editing single terms with `pico_category`.
    *   The existing bulk edit functionality in `UpdateSearchTermsView` (`/api/search-terms/update/<int:id>/`) will be extended to handle bulk assignment of `pico_category`.
    *   The `SearchTermSerializer` must be updated to include the `pico_category` field in API responses. [Done]

4.  **Frontend: Literature Search List View:**
    *   Files to modify:
        *   `templates/lit_reviews/search_terms.html`
        *   `static/lit_reviews/vue/search_terms.js`
    *   A new column titled "PICO Category" to Add & Edit search query modal
    *   ensure on edit, the "PICO Category" still intact with the form
    *   Add "PICO Category" to filters
    *   Add section for Pico Group ensure using the current table to render the rows by loop ["unorder groups", ...pico_categories]
        the rows should show based the group

5.  **Frontend: Bulk Editing:**
    *   Files to modify:
        *   `templates/lit_reviews/search_terms.html`
        *   `static/lit_reviews/vue/search_terms.js`
    *   The literature searches table must include checkboxes to select multiple searches.
    *   When one or more searches are selected, a "Bulk Edit" button shall become visible.
    *   Clicking "Bulk Edit" will reveal an option to "Assign PICO Category".
    *   This option will present a dropdown menu with all PICO categories, including an option to "Clear Category" (which sets the field to `NULL`).
    *   Applying the change will update the PICO category for all selected searches.

## 5. Non-Goals (Out of Scope for this version)

*   **No Custom Categories:** Users will not be able to create their own custom PICO categories in this version.
*   **No Reporting Integration:** The PICO category data will not be included in any downloadable reports or exports in this initial release.
*   **No Import Functionality:** Assigning PICO categories during the literature search import process is not included.

## 6. Design Considerations

*   **UI:** PICO categories should be displayed as colored tags (pills) for quick visual identification.
*   **Color Scheme:**
    *   **Population:** Blue (`#007bff`)
    *   **Intervention:** Green (`#28a745`)
    *   **Comparator:** Orange (`#fd7e14`)
    *   **Outcome:** Purple (`#6f42c1`)

## 7. Success Metrics

*   Adoption of the feature: Percentage of projects created after release that utilize PICO category assignments.
*   Reduction in time spent organizing search terms, measured by user feedback.
*   Successful and error-free assignment of categories via single, quick-edit, and bulk-edit methods.

## 8. Open Questions

*   None at this time.
