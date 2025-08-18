## Relevant Files

- `templates/lit_reviews/search_terms.html` - Contains the Vue.js template for the literature search list.
- `static/lit_reviews/vue/search_terms.js` - Contains the Vue.js component logic for the literature search list.

### Notes

- The backend API now provides `pico_categories` in the response, which can be used to populate dropdowns and filters.
- The `SearchTermSerializer` now includes the `pico_category` for each literature search.

## Tasks

- [ ] 1.0 Update Add/Edit Modal
  - [x] 1.1 In `search_terms.html`, add a "PICO Category" dropdown to the "Add New Search Query" modal.
  - [x] 1.2 The dropdown should be populated with the `pico_categories` provided by the API.
  - [x] 1.3 Ensure that when editing a search, the current `pico_category` is pre-selected in the dropdown.
  - [x] 1.4 In `search_terms.js`, update the `addSearchTerm` and `updateSearchTerm` methods to include the `pico_category` in the API request.

- [ ] 2.0 Update List Table
  - [ ] 2.1 The groups  should be "Unordered", "Population", "Intervention", "Comparator", and "Outcome", and the table should be rendered by looping through these groups.
  - [ ] 2.2 on each group section add colored tag/pill, as per the color scheme in the PRD's Design Considerations.

- [ ] 3.0 Implement Filtering
  - [ ] 3.1 In `search_terms.html`, add a "PICO Category" filter dropdown to the filter section.
  - [ ] 3.2 In `search_terms.js`, implement the logic to filter the literature searches based on the selected PICO category.

- [ ] 4.0 Implement Bulk Editing
  - [ ] 4.1 In `search_terms.html`, add checkboxes to each row of the literature searches table to allow for multiple selections.
  - [ ] 4.2 Add a "Bulk Edit" button that becomes visible when one or more searches are selected.
  - [ ] 4.3 The "Bulk Edit" button should reveal a dropdown to "Assign PICO Category".
  - [ ] 4.4 This dropdown should include all PICO categories and an option to "Clear Category".
  - [ ] 4.5 In `search_terms.js`, implement the `bulkUpdatePicoCategory` method to send the selected category and search IDs to the bulk update API endpoint.
