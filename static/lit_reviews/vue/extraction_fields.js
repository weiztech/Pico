axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
  el: '#app',
  mixins: [globalMixin],
  delimiters: ["[[", "]]"],
  data() {
    return {
      extractionFields: [],
      isExtractionFieldsLoading: false,
      addedExtractionField: {
        name: "",
        type: "",
        category: "ST",
        field_section: "",
        name_in_report: "",
        description: "",
        ai_prompte: "",
        drop_down_values: [],
      },
      searchTerm: "",
      sort: "id",
      appliedSort: "id",
      sortOptions: [
        { name: "ID", value: "id" },
        { name: "Name", value: "name" },
        { name: "Type", value: "type" },
      ],
      sortingDirection: "Ascending",
      sortingDirectionOptions: [
        { name: "Ascending", value: "Ascending" },
        { name: "Descending", value: "Descending" },
      ],
      extractionFields: [],
      selectedExtractionFields: [],
      filteredExtractionFields: [],
      currentURL: "",
      appliedExtractionFields: [],
      isCheckAll: false,
      isResultsFiltered: false,
      filter_field_section: [],
      fieldSectionFilter: [],
      fieldCategoryFilter: [],
      fieldTypeFilter: [],
      fieldSectionAppliedFilters: [],
      fieldCategoryAppliedFilters: [],
      fieldTypeAppliedFilters: [],
      editedExtractionField: "",
    }
  },
  computed: {
    isFiltersApplied() {
      return this.fieldSectionAppliedFilters.length || this.fieldCategoryAppliedFilters.length || this.fieldTypeAppliedFilters.length;
    },
    canAddNewDropDownItem() {
      return (isEditing) => {
        const targetField = isEditing ? this.editedExtractionField : this.addedExtractionField;
        const values = targetField.drop_down_values;
        return values.length === 0 || values[values.length - 1].trim() !== "";
      };
    },
    onAddExtractionFieldValidation() {
      const field = this.addedExtractionField;

      // Check required fields
      if (!field.name || !field.type || !field.category || !field.field_section || !field.name_in_report) {
        return true; // Disable button if any required field is empty
      }

      // Check `drop_down_values` only if `type` is "DROP_DOWN"
      if (field.type === "DROP_DOWN" && (!field.drop_down_values || field.drop_down_values.length === 0 || field.drop_down_values.every(value => !value))) {
        return true; // Disable button if `drop_down_values` is required and empty
      }

      return false; // Enable button if all checks pass
    },
    onEditExtractionFieldValidation() {
      const field = this.editedExtractionField;

      // Check required fields
      if (!field.name || !field.type || !field.category || !field.field_section || !field.name_in_report) {
        return true; // Disable button if any required field is empty
      }

      // Check `drop_down_values` only if `type` is "DROP_DOWN"
      if (field.type === "DROP_DOWN" && (!field.drop_down_values || field.drop_down_values.length === 0 || field.drop_down_values.every(value => !value))) {
        return true; // Disable button if `drop_down_values` is required and empty
      }

      return false; // Enable button if all checks pass
    },
    visibileExtractionFields: function () {
      if (this.isResultsFiltered)
        return this.filteredExtractionFields;
      else
        return this.extractionFields;
    },
  },
  watch: {
    selectedExtractionFields: function (newVal, oldVal) { // watch it
      if (this.isResultsFiltered)
        this.isCheckAll = this.filteredExtractionFields.length === this.selectedExtractionFields.length;
      else
        this.isCheckAll = this.extractionFields.length === this.selectedExtractionFields.length;
    },
    extractionFields: function (newVal, oldVal) { // watch it
      this.filteredExtractionFields = this.filteredExtractionFields.map(field => newVal.find(s => s.id === field.id));
    },
  },
  methods: {
    onCheckAll: function (e) {
      if (e.target.checked) {
        this.selectedExtractionFields = this.isResultsFiltered ?
          this.filteredExtractionFields.map(s => s.id)
          : this.extractionFields.map(s => s.id);
      } else {
        this.selectedExtractionFields = [];
      }
    },
    clearSelectedExtractionFields: function () {
      this.selectedExtractionFields = [];
    },
    onSearch: function (e) {
      e.preventDefault();
      this.filteredExtractionFields = this.extractionFields.filter(field => field.name.toLowerCase().includes(this.searchTerm.toLowerCase()));
      this.isResultsFiltered = true;
    },
    onSortingChange(selected) {
      this.appliedSort = selected;
    },
    onSortingDirectionChange(selected) {
      this.sortingDirection = selected;
    },
    onToggleSortingDropDown() {
      this.$refs["sorting-dropdown"].classList.toggle("active");
    },
    onSort() {
      if (this.sortingDirection === "Descending")
        this.sort = "-" + this.appliedSort;
      else
        this.sort = this.appliedSort;

      this.$refs["sorting-dropdown"].classList.remove("active");
      this.loadExtractionFields(false, 1);
    },
    toggleField(field) {
      const index = this.selectedExtractionFields.indexOf(field);
      if (index > -1) {
        this.selectedExtractionFields.splice(index, 1);
      } else {
        this.selectedExtractionFields.push(field)
      }
    },
    onClearFilters: function () {
      this.searchTerm = "";
      this.fieldSectionFilter = [];
      this.fieldCategoryFilter = [];
      this.fieldTypeFilter = [];
      this.fieldSectionAppliedFilters = [];
      this.fieldCategoryAppliedFilters = [];
      this.fieldTypeAppliedFilters = [];
      this.isResultsFiltered = false;
    },
    onCloseFilters() {
      this.hideModal('filters-slider');
    },
    getCurrentExtractionFields() {
      const values = this.getCurrentFilterValue("field_section");
      if (values) {
        const extractionFields = values.split(",");
        this.appliedExtractionFields = extractionFields;
        return extractionFields;
      }
      return [];
    },
    getCurrentFilterValue(type) {
      const queryParams = this.currentURL.split("?");
      const queryParamsItems = queryParams[1].split("&");
      for (queryparam of queryParamsItems) {
        const filter = queryparam.split("=");
        const filterLabel = filter[0];
        const filterValue = filter[1];

        if (type === filterLabel)
          return filterValue;
      };

      return null;
    },
    // Actions
    onFilter: function () {
      console.log("this.fieldSectionFilter:", this.fieldSectionFilter);
      console.log("this.fieldCategoryFilter:", this.fieldCategoryFilter);
      console.log("this.extractionFields:", this.extractionFields);

      // Combine both filters into one filter operation
      this.filteredExtractionFields = this.extractionFields.filter(field => {
        const matchesSection = this.fieldSectionFilter.length
          ? this.fieldSectionFilter.includes(field.field_section)
          : true;

        const matchesCategory = this.fieldCategoryFilter.length
          ? this.fieldCategoryFilter.includes(field.category)
          : true;

        const matchesType = this.fieldTypeFilter.length
          ? this.fieldTypeFilter.includes(field.type)
          : true;

        return matchesSection && matchesCategory && matchesType;
      });

      console.log("this.filteredExtractionFields:", this.filteredExtractionFields);

      // Update filter state
      this.isResultsFiltered = true;
      this.fieldSectionAppliedFilters = [...this.fieldSectionFilter];
      this.fieldCategoryAppliedFilters = [...this.fieldCategoryFilter];
      this.fieldTypeAppliedFilters = [...this.fieldTypeFilter];

      // Close the modal after filtering
      this.hideModal("filters-slider");
    },
    showAddExtractionsModal: function () {
      this.addedExtractionField = {
        name: "",
        type: "",
        category: "ST",
        field_section: "",
        name_in_report: "",
        description: "",
        ai_prompte: "",
        drop_down_values: [""],
      };
      this.showModal("add-extraction");
    },
    showEditExtractionModal(field) {
      console.log("field", field);

      // Mapping for field_section
      const fieldSectionMap = {
        "Suitability and Outcomes (All Articles including SoTA)": "SO",
        "Quality and Contribution Questions": "QC",
        "MDCG Ranking": "MR",
        "Extraction Fields": "EF",
        "SoTa": "ST"
      };

      // Mapping for category
      const categoryMap = {
        "Study Design": "ST",
        "Treatment": "T",
        "Study Result": "SR"
      };

      // Mapping for type
      const typeMap = {
        "Text": "TEXT",
        "Long Text": "LONG_TEXT",
        "Drop Down": "DROP_DOWN"
      };

      // Replace field values with their shorthand codes
      this.editedExtractionField = {
        ...field,
        field_section: fieldSectionMap[field.field_section] || "",
        category: categoryMap[field.category] || "ST",
        type: typeMap[field.type] || "",
        drop_down_values: field.drop_down_values || [""],
        description: field.description || "",
        ai_prompte: field.ai_prompte || "",
      };

      console.log("this.editedExtractionField", this.editedExtractionField);

      this.showModal("edit-extraction");
    },
    onDropDownItemChange: function (event, index, isEditing = false) {
      const targetField = isEditing ? this.editedExtractionField : this.addedExtractionField;
      targetField.drop_down_values[index] = event.target.value;
    },
    // Add a new dropdown item
    onAddDropDownItem: function (isEditing = false) {
      const targetField = isEditing ? this.editedExtractionField : this.addedExtractionField;
      console.log("targetField", targetField);
      if (this.canAddNewDropDownItem(isEditing)) {
        targetField.drop_down_values.push(""); // Add empty item only if allowed
      }

    },
    // Remove a dropdown item
    onRemoveDropDownItem: function (index, isEditing = false) {
      const targetField = isEditing ? this.editedExtractionField : this.addedExtractionField;
      targetField.drop_down_values.splice(index, 1);
    },
    // Helpers
    enableElement: function (ele, text = null) {
      ele.style.pointerEvents = "auto";
      ele.style.opacity = "1";
      if (text)
        ele.innerHTML = text;
    },
    disableElement: function (ele, text = null) {
      ele.style.pointerEvents = "None";
      ele.style.opacity = ".7";
      if (text)
        ele.innerHTML = text;
    },

    // Async Calls
    onAddExtractionField: function (e) {
      e.preventDefault();

      // Remove empty strings from drop_down_values
      if (this.addedExtractionField.type === "DROP_DOWN") {
        this.addedExtractionField.drop_down_values = this.addedExtractionField.drop_down_values.filter(value => value.trim() !== "");
      }

      if (this.addedExtractionField.field_section !== "EF") {
        this.addedExtractionField.category = ""
      }
      const postData = this.addedExtractionField;
      const btn = this.$refs["modal-submit-btn"];

      // extractionsURL this var declared inside the django template
      axios.post(extractionsURL, postData)
        .then(
          res => {
            this.disableElement(btn);
            const newRecords = this.extractionFields;
            newRecords.push(res.data);
            this.extractionFields = newRecords;
            this.enableElement(btn);
            this.makeToast("success", "A new extraction field has been created successfully.");
            this.hideModal("add-extraction");

          },
          err => {
            console.log({ err });
            const variant = "danger";
            let error_msg = this.handleErrors(err);
            this.makeToast(variant, error_msg);

            // show update button again
            this.enableElement(btn);
          }
        )
    },
    onEditExtractionField: function (e) {
      e.preventDefault();
      // Remove empty strings from drop_down_values
      if (this.editedExtractionField.type === "DROP_DOWN") {
        this.editedExtractionField.drop_down_values = this.editedExtractionField.drop_down_values.filter(value => value.trim() !== "");
      }

      const formData = this.editedExtractionField;
      console.log("formData", formData);

      axios.put(extractionsURL, data = formData)
        .then(
          res => {
            const updatedIndex = this.extractionFields.findIndex(field => field.id === res.data.id);
            if (updatedIndex !== -1) {
              this.$set(this.extractionFields, updatedIndex, res.data);
            }
            this.makeToast("success", "The extraction field has been updated successfully.");
            this.hideModal("edit-extraction");
          },
          err => {
            console.error(err);
            const error_msg = this.handleErrors(err);
            this.makeToast("danger", error_msg);
          }
        );
    },

    onDeleteField: function (id) {
      const URL = deleteExtractionFieldURL;
      const btn = this.$refs["confirm-delete" + id][0];

      axios.delete(URL, { data: { selectedExtractionFields: [id] } })
        .then(
          res => {
            this.disableElement(btn);
            const newRecords = this.extractionFields;
            const index = newRecords.findIndex(item => item.id === id);
            newRecords.splice(index, 1);
            this.extractionFields = newRecords;
            this.makeToast("success", `Extraction field with ID ${id} has been deleted successfully.`);
            this.hideModal('delete-field' + id);
          },

          err => {
            console.log({ err });
            this.hideModal('delete-field' + id);
            const variant = "danger";
            let error_msg = this.handleErrors(err);
            this.makeToast(variant, error_msg);

            // show delete button again
            this.enableElement(btn);
          }
        )
    },
    onBulkDeleteFields: function () {
      const URL = deleteExtractionFieldURL;
      const postData = {
        selectedExtractionFields: this.selectedExtractionFields,
      }
      console.log("postData", postData);

      axios.delete(URL, { data: postData })
        .then(
          res => {
            this.extractionFields = this.extractionFields.filter(
              field => !this.selectedExtractionFields.includes(field.id)
            );
            this.selectedExtractionFields = [];
            this.hideModal('fields-bulk-delete')
            this.makeToast("success", "Selected extraction fields have been deleted successfully.");
          },

          err => {
            console.log({ err });
            this.makeToast("danger", this.handleErrors(err));
          }
        )
    },
    loadExtractionFields() {
      this.isExtractionFieldsLoading = true;
      let URL = extractionsURL;
      if (this.sort) {
        if (URL.includes("?"))
          URL = `${URL}&ordering=${this.sort}`;
        else
          URL = `${URL}?ordering=${this.sort}`;
      };

      // extractionsURL this var declared inside the django template
      axios.get(URL)
        .then(
          res => {
            console.log(res);
            this.isExtractionFieldsLoading = false;
            this.extractionFields = res.data;
          },
          err => {
            console.log(err);
            this.isExtractionFieldsLoading = false;
          }
        );
    }

  },
  mounted() {
    this.loadExtractionFields()
  }
})
