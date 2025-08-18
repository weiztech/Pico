## Relevant Files

- `lit_reviews/models.py` - Contains the `LiteratureSearch` model that needs to be updated.
- `lit_reviews/api/search_terms/serializers.py` - Contains the serializers for creating and updating `LiteratureSearch` objects.
- `lit_reviews/api/search_terms/views.py` - Contains the API views for handling `LiteratureSearch` operations.
- `lit_reviews/tests/api/test_search_terms.py` - New test file to be created for testing the PICO category functionality.

### Notes

- Unit tests should be created to cover the new functionality.
- Use `python manage.py test lit_reviews.tests.api.test_search_terms` to run the new tests.

## Tasks

- [ ] 1.0 Update Database Model and Create Migration
  - [x] 1.1 Add `PicoCategory` TextChoices enum to `lit_reviews/models.py`.
  - [x] 1.2 Add `pico_category` field to the `LiteratureSearch` model, making it optional (`null=True`, `blank=True`).
  - [x] 1.3 Run `python manage.py makemigrations` to generate the database migration file.
  - [x] 1.4 Run `python manage.py migrate` to apply the changes to the database schema.
- [ ] 2.0 Update API Serializers to Handle `pico_category`
  - [x] 2.1 Add `pico_category` to the `CreateNewSearchTermSerializer` as an optional field.
  - [x] 2.2 Add `pico_category` to the `UpdateSearchTermSerializer` as an optional field.
  - [x] 2.3 Update the `create` method in `CreateNewSearchTermSerializer` to handle saving the `pico_category`.
  - [x] 2.4 Update the `create` method in `UpdateSearchTermSerializer` to handle updating the `pico_category`.
  - [x] 2.5 Add `pico_category` to the `SearchTermSerializer` to ensure it's included in API responses for listing.
- [ ] 3.0 Modify API Views for Single and Bulk PICO Updates
  - [ ] 3.1 In `SearchTermsView`, ensure the optional `pico_category` is passed to the `CreateNewSearchTermSerializer` when creating a new search.
  - [ ] 3.2 In `UpdateSearchTermsView`, modify the logic for `update_type == "single"` to pass the optional `pico_category` to the `UpdateSearchTermSerializer`.
  - [ ] 3.3 In `UpdateSearchTermsView`, modify the logic for `update_type == "bulk"` to accept a `pico_category` and apply it to all selected `LiteratureSearch` instances.
- [ ] 4.0 Implement Unit Tests for PICO Category Functionality
  - [ ] 4.1 Create a new test file `lit_reviews/tests/api/test_search_terms.py`.
  - [ ] 4.2 Write a test case to verify that a `pico_category` can be added when creating a `LiteratureSearch`.
  - [ ] 4.3 Write a test case to verify that the `pico_category` of a single `LiteratureSearch` can be updated.
  - [ ] 4.4 Write a test case to verify that the `pico_category` can be updated for multiple `LiteratureSearch` instances in a bulk operation.
  - [ ] 4.5 Write a test case to verify that the `pico_category` can be cleared (set to null).