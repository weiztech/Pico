axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

const SplitTermInit = {
  term: "",
  initTerm: "",
  type: "",
  dbs: [],
  propIDs: null,
  isSearchFile: null,
  clinicalTrialsSearchField: "",
  maudeSearchField: "",
  
  dbsOptions: [],
  aeDbsOptions: [],
};

var app = new Vue({
  el: '#app',
  mixins: [globalMixin],
  delimiters: ["[[", "]]"],
  data() {
    return {
      // fixed values
      typeSelcetOptions: [
        {
          name: "Device",
          value: false,
        },
        {
          name: "Sota",
          value: true,
        },
      ],
      // list of databases where preview is available
      dbPreviews: ["pubmed", "pmc", "cochrane", "ct_gov", "maude", "pmc_europe", "maude_recalls", "scholar"],
      urlDbPreviews: ["pubmed", "pmc", "scholar"],
      currentExpectedDB: "",
      scraperError: "",

      // Asynce Data
      terms: [],
      filteredTerms: [],
      // maxTerms this var is declared inside the django template
      maxTerms: maxTerms,
      dbs: [],
      searchTerm: "",
      statusFilter: "",
      typeFilter: "",
      customTypeFilter: "",
      lit_dbs: [],
      ae_dbs: [],
      SearchLabelOptions: [],
      litReviewID: null,
      projectType:projectType,
      searchProtocol: null,
      summaryDoc: null,
      totalTermsCount: null,
      lastTermIndex: null,
      validator: null,
      picoCategories: [],
      
      // Fixed backend values
      clinicalTrialsSearchFields: [],
      maudeSearchFields: [],

      // forms
      newTerm: {
        term: "",
        type: "",
        dbs: [],
        isUpdateTerm: false,
        propID: null,
        isSearchFile: null,
        clinicalTrialsSearchField: "",
        maudeSearchField: "",
        pico_category: "",
      },
      splitTerm: SplitTermInit,
      dbBulkTerm: {
        dbs: [],
      },
      sortedBy: "id",
      isCheckAll: false,
      selectedTerms: [],
      delete_warning_data: {
        termTruncate: "",
        propID: null,
        term: "",
        dbs: "",
        hasFile: false,
      },
      update_warning_data: {
        term: "",
        propID: null,
      },
      specificBulkUpdateForm: {
        dbs: [],
        yearsBack: 10,
        isSota: null,
      },
      splittedTerm: null,
      previews: [],
      previewResultsURL: null,
      dbFilter: [],
      dbAppliedFilters: [],
      isSearchApplied: false,

      // loading
      isCreatingTermLoading: false,
      isRecordsLoading: false,
      isDeletePending: false,
      isBulkDeletePending: false,
      isSplittingTermLoading: false,

      // Properties for database config viewer
      currentDB: null,
      currentDBType: '',
      currentDBConfigStartDate: '',
      currentDBConfigEndDate: '',
      excludedParamsName: [],
    }
  },
  computed: {
    isCreateNewTermValid: function () {
      if (this.isCreatingTermLoading)
        return false;

      const ignoredFields = ["isSearchFile", "isUpdateTerm", "propID"]
      for (let key in this.newTerm) {
        if (key !== "dbs" && !ignoredFields.includes(key) && !this.newTerm[key])
          return false;
        if (key === "dbs" && !this.newTerm[key].length)
          return false;
      }

      return true;
    },
    isSplitTermValid: function () {
      if (this.isSplittingTermLoading)
        return false;

      const ignoredFields = ["isSearchFile", "isUpdateTerm", "propID"]
      for (let key in this.splitTerm) {
        if (key !== "dbs" && !ignoredFields.includes(key) && !this.splitTerm[key])
          return false;
        if (key === "dbs" && !this.splitTerm[key].length)
          return false;
      }

      return true;
    },
    searchTerms: function() {
      if (this.isSearchApplied)
        return this.filteredTerms;
      else
        return this.terms;
    },
    isAllClinicalDBSelected: function() {
      const litDBSEnums = this.lit_dbs.map(db => db.entrez_enum);
      for (let db of litDBSEnums) {
        if (!this.newTerm.dbs.includes(db)) return false;
      }
      return true;
    },
    isAllAEDBSelected: function() {
      const adverseDBsEnums = this.ae_dbs.map(db => db.entrez_enum);
      for (let db of adverseDBsEnums) {
        if (!this.newTerm.dbs.includes(db)) return false;
      }
      return true;
    },
    groupedTerms: function() {
      const groups = {
        "Unordered": [],
        "Population": [],
        "Intervention": [],
        "Comparator": [],
        "Outcome": [],
      };
      const PicoMap = Object.fromEntries(this.picoCategories.map(item => [item.value, item.label]));

      this.searchTerms.forEach(term => {
        const category = PicoMap[term.pico_category] || "Unordered";
        if (groups[category]) {
          groups[category].push(term);
        } else {
          groups["Unordered"].push(term);
        }
      });
      return groups;
    }
  },
  watch: {
    // whenever isCheckAll changes, this function will run
    isCheckAll(newIsCheckAll, oldIsCheckAll) {
      if (newIsCheckAll) {
        const allTerms = this.terms.map(term => term.id);
        this.selectedTerms = allTerms;
      } else {
        this.selectedTerms = [];
      }
    },
    terms: function (newVal, oldVal) { // watch it
      this.filteredTerms = this.filteredTerms.map(term => newVal.find(item => item.id === term.id));
    },
  },
  methods: {
    // helpers
    getDbDateRange(proposal) {
      const dbEntrezEnum = proposal.db_entrez_enum;
      
      const allDBs = [...this.lit_dbs, ...this.ae_dbs];
      const db = allDBs.find(d => d.entrez_enum === dbEntrezEnum);
    
      if (db && db.search_configuration?.length) {
        const params = db.search_configuration[0].params || [];
    
        const startDateParam = params.find(p => p.name === 'Start Date');
        const endDateParam = params.find(p => p.name === 'End Date');
    
        const start = startDateParam?.value?.trim();
        const end = endDateParam?.value?.trim();
    
        if (start && end) {
          return `${start} → ${end}`;
        }
      }
    
      // If not found or missing values, fall back based on AE or Recall
      if (proposal.db_is_ae || proposal.db_is_recall) {
        return `${this.searchProtocol.ae_start_date_of_search} → ${this.searchProtocol.ae_date_of_search}`;
      } else {
        return `${this.searchProtocol.lit_start_date_of_search} → ${this.searchProtocol.lit_date_of_search}`;
      }
    },
    dateFormat(str_date){
      if (str_date) {
        const [year, month, day] = str_date.split('-');
        const formattedDate = `${month}-${day}-${year}`;  
        return formattedDate;
      };
    },
    getReportStatus: function (termObj) {
      const report = termObj.value[termObj.value.length - 1].report;
      const previewFailure = report && report.errors && (
        report.errors.includes("Fetching Preview and Expected Results Count") 
        || 
        report.errors.includes("Failed to fetch preview data")
      );

      if (report) {
        if (report.status === 'FETCHING_PREVIEW')
          return 'Fetching Expected Count';
        else if (report.status === 'FAILED' && previewFailure) {
          return "UPDATED";
        } else
          return report.status;
      } else {
        return "UPDATED";
      }
    },
    getReportStatusClasses: function (status) {
      switch (status) {
        case 'FETCHING_PREVIEW':
          return 'badge warning';
        case 'SAVING':
          return 'badge primary';
        case 'FAILED':
          return 'badge error';
        case 'UPDATED':
          return 'badge success';
        default:
          return 'badge secondary';
      }
    },
    getGroupColor: function (groupName) {
      switch (groupName) {
        case 'Population':
          return '#007bff';
        case 'Intervention':
          return '#28a745';
        case 'Comparator':
          return '#fd7e14';
        case 'Outcome':
          return '#6f42c1';
        default:
          return '#6c757d'; // default color for Unordered
      }
    },
    isTermIncluded: function (item) {
      const index = this.selectedTerms.findIndex(i => i === item.id);
      if (index > -1)
        return true
      else
        return false
    },
    compare: function (a, b, key, type) {
      if (a[key].toLowerCase() < b[key].toLowerCase()) {
        return type === "ASC" ? -1 : 1;
      }
      if (a[key].toLowerCase() > b[key].toLowerCase()) {
        return type === "ASC" ? 1 : -1;
      }
      return 0;
    },
    isSearchTermTypeValid: function (propID, index) {
      const isSota = document.getElementById(`sota-${propID}`).value;
      
      if (isSota == "") {
        this.onErrorDisplay(`Please fill Is Sota field for search term with ID ${index}`)
        return false;
      }
      return true
    },
    getRowData: function (propID) {
      const term = document.getElementById(`term_${propID}`).value;
      const selectedTermObject = this.terms.find(item => item.id === propID);
      const dbs = selectedTermObject.value.map(item => item.proposal.db_entrez_enum);
      const isSota = document.getElementById(`sota-${propID}`).value //=== "sota";
      let term_type;
      let is_sota_term;

      if (projectType === 'Custom') {
        term_type = isSota;
        is_sota_term = false;
      } else {
        term_type = isSota;
        is_sota_term = isSota 
      }
      

      return {
        prop_id: propID,
        lit_review_id: litReviewID,
        term,
        // years_back: yearsBack,
        entrez_enums: dbs,
        is_sota_term: is_sota_term,
        term_type: term_type,
      };
    },
    isDatabaseSelected: function (termsList, database) {
      for (let i = 0; i < termsList.length; i++)
        if (termsList[i].proposal.db === database.displayed_name)
          return true;

      return false;
    },
    getSelectedDB: function (termsList) {
      const selectedDbs = [];
      for (let i = 0; i < termsList.length; i++) {
        const selectedDB = this.dbs.find(db => db.name === termsList[i].proposal.db);
        if (selectedDB)
          selectedDbs.push(selectedDB);
      }

      return selectedDbs;
    },
    getSelectedDBForm: function () {
      const selectedDbs = [];
      const formDBS = this.specificBulkUpdateForm.dbs;

      for (let i = 0; i < formDBS.length; i++) {
        const selectedDB = this.dbs.find(db => db.entrez_enum === formDBS[i]);
        if (selectedDB)
          selectedDbs.push(selectedDB);
      }

      return selectedDbs;
    },
    expandDatabaseSection: function(propID) {
      const dbListElm = this.$refs['db-section-'+propID][0];
      dbListElm.classList.toggle("active");
    },
    showLoadingPopup: function () {
      popup = document.getElementById("loading-section");
      popup.style.display = "flex";
    },
    hideLoadingPopup: function () {
      popup = document.getElementById("loading-section");
      if (popup) popup.style.display = "none";
    },
    showDatabaseConfig(proposal) {
      const dbEntrezEnum = proposal.db_entrez_enum;
      
      // Find the database in the combined list
      const allDBs = [...this.lit_dbs, ...this.ae_dbs];
      const db = allDBs.find(d => d.entrez_enum === dbEntrezEnum);
      
      if (db) {
        this.currentDB = db;
        console.log("currentDB", this.currentDB);
        
        this.currentDBType = proposal.db_is_ae || proposal.db_is_recall ? 'ae_database' : 'literature_database';
        
        // Get start and end dates
        if (db.search_configuration?.length) {
          const params = db.search_configuration[0].params || [];
          
          const startDateParam = params.find(p => p.name === 'Start Date');
          const endDateParam = params.find(p => p.name === 'End Date');
          
          this.currentDBConfigStartDate = startDateParam?.value?.trim() || '';
          this.currentDBConfigEndDate = endDateParam?.value?.trim() || '';
        } else {
          // Fall back to protocol dates
          if (proposal.db_is_ae || proposal.db_is_recall) {
            this.currentDBConfigStartDate = this.searchProtocol.ae_start_date_of_search || '';
            this.currentDBConfigEndDate = this.searchProtocol.ae_date_of_search || '';
          } else {
            this.currentDBConfigStartDate = this.searchProtocol.lit_start_date_of_search || '';
            this.currentDBConfigEndDate = this.searchProtocol.lit_date_of_search || '';
          }
        }
        
        // Set excluded params for clinical trials
        this.excludedParamsName = ['Recruitment Status', 'Study Results', 'Study Type'];
        
        // Show the slider
        this.showModal('db-config-viewer');
      }
    },

    // actions
    onSearch: function (e) {
      e.preventDefault();

      if (this.searchTerm){
        this.isSearchApplied = true;
        this.filteredTerms = this.terms.filter(item => item.term.toLowerCase().includes(this.searchTerm.toLowerCase()));
      } else {
        this.isSearchApplied = false;
        this.filteredTerms = [];
      }
    },
    onFilter: function(e) {
      this.filteredTerms = this.terms.filter(item => {
        const dbMatch = this.dbFilter.length ? item.value.find(item => this.dbFilter.includes(item.proposal.db_entrez_enum)) : true;
        const isSotaMatch = this.typeFilter !== "" ? this.typeFilter === item.value[0].proposal.is_sota_term : true;
        const customTypeMatch = this.customTypeFilter ? this.customTypeFilter === item.value[0].proposal.search_label : true;
        const statusMatch = this.statusFilter ? this.statusFilter === this.getReportStatus(item) : true;
        
        return dbMatch && isSotaMatch && statusMatch && customTypeMatch;
      });
      this.isSearchApplied = true;
      this.dbAppliedFilters = this.dbFilter;
      this.hideModal("filters-slider");
    },
    onClearFilters: function () {
      this.searchTerm = "";
      this.dbFilter = [];
      this.dbAppliedFilters = [];
      this.typeFilter = "";
      this.customTypeFilter = "";
      this.statusFilter = "";
      this.filteredTerms = [];
      this.isSearchApplied = false;
    },
    onCloseFilters: function () {
      this.hideModal('filters-slider');
    },
    toggleStatusFilter: function (status) {
      this.statusFilter = status;
      if (status === "all")
        this.statusFilter = "";
    },
    toggleTypeFilter: function (type) {
      this.typeFilter = type;
      if (type === "all")
        this.typeFilter = "";
    },
    toggleCustomTypeFilter: function (type) {
      this.customTypeFilter = type;
      if (type === "all")
        this.customTypeFilter = "";
    },
    onSortTerm: function () {
      if (this.sortedBy === "-term") {
        this.sortedBy = "term";
        this.terms = this.terms.sort((a, b) => this.compare(a, b, "term", "ASC"));
      } else {
        this.sortedBy = "-term";
        this.terms = this.terms.sort((a, b) => this.compare(a, b, "term", "DSC"));
      }
    },
    onShowAddTermModal: function() {
      // checking if search protocol fields are valid
      if (
        !this.searchProtocol.lit_date_of_search ||
        !this.searchProtocol.max_imported_search_results ||
        !this.searchProtocol.lit_searches_databases_to_search ||
        this.searchProtocol.lit_searches_databases_to_search.length === 0
      ) {
        this.showModal("add-term-blocker-toast");
        return;
      };

      this.newTerm = {
        term: "",
        type: "",
        dbs: [],
        isUpdateTerm: false,
        propID: null,
        isSearchFile: null,
        clinicalTrialsSearchField: this.clinicalTrialsSearchFields[0],
        maudeSearchField: this.maudeSearchFields[0],
        pico_category: "",
      };
      this.showModal('add-edit-term-modal');
    },
    onDisplayExpectCountFailedError: function(db, scraperError) {
      this.currentExpectedDB = db;
      // check if there is a term syntax error in the scraper
      if (scraperError && scraperError.includes("Error parsing query ")) {
        this.scraperError = "It seems like your search term query cannot be searched as given Are you sure your syntax is acceptable? Try running this search directly on the database to make sure the results populate.";
      } else {
        this.scraperError = "";
      };
      this.showModal("expected-failed-warning");
    },
    onDIsplayMaudeWarning: function() {
      this.makeToast('warning', 'You got more than 500 results. Please narrow your searches down.');
    },
    onSelectAllClinicalDBs: function (e) {
      const litDBSEnums = this.lit_dbs.map(db => db.entrez_enum)
      this.newTerm.dbs = this.newTerm.dbs.filter(db => !litDBSEnums.includes(db));
      if (e.target.checked)
        this.newTerm.dbs = [...this.newTerm.dbs, ...this.lit_dbs.map(db => db.entrez_enum)];
    },
    onSelectAllAEDBs: function (e) {
      const adverseDBsEnums = this.ae_dbs.map(db => db.entrez_enum)
      this.newTerm.dbs = this.newTerm.dbs.filter(db => !adverseDBsEnums.includes(db));
      if (e.target.checked)
        this.newTerm.dbs = [...this.newTerm.dbs, ...this.ae_dbs.map(db => db.entrez_enum)];
    },
    onSelectAllClinicalDBsBulk: function (e) {
      const litDBSEnums = this.lit_dbs.map(db => db.entrez_enum)
      this.dbBulkTerm.dbs = this.dbBulkTerm.dbs.filter(db => !litDBSEnums.includes(db));
      if (e.target.checked)
        this.dbBulkTerm.dbs = [...this.dbBulkTerm.dbs, ...this.lit_dbs.map(db => db.entrez_enum)];
    },
    onSelectAllAEDBsBulk: function (e) {
      const adverseDBsEnums = this.ae_dbs.map(db => db.entrez_enum)
      this.dbBulkTerm.dbs = this.dbBulkTerm.dbs.filter(db => !adverseDBsEnums.includes(db));
      if (e.target.checked)
        this.dbBulkTerm.dbs = [...this.dbBulkTerm.dbs, ...this.ae_dbs.map(db => db.entrez_enum)];
    },

    updateRowStatus: function(rowID, status){
      const termIndex = this.terms.findIndex(item => item.id === rowID);
      const termVal = this.terms[termIndex];
      termVal.value[termVal.value.length-1].report.status = status;
      this.$set(this.terms, termIndex, termVal);
    },
    onDisplayValidationError: function (errorMSG) {
      this.makeToast("danger", errorMSG);
    },
    onTermChange: function (propID, event) {
      const termIndex = this.terms.findIndex(item => item.id === propID);
      const termVal = this.terms[termIndex];
      termVal.term = event.target.value;
      if (termVal.value[termVal.value.length-1].report.status !== "Requires Updating")
        termVal.value[termVal.value.length-1].report.status = "Requires Updating";

      this.$set(this.terms, termIndex, termVal);
    },
    onRowChecked: function (item) {
      const index = this.selectedTerms.findIndex(i => i === item.id);
      if (index > -1) {
        this.selectedTerms.splice(index, 1);
      } else
        this.selectedTerms.push(item.id);
    },
    onSplitTerm: function(termItem) {
      const dbs = termItem.value.map(item => item.proposal.db_entrez_enum);
      const clinicalTrialsTerm = termItem.value.find(term => term.proposal.db_entrez_enum == "ct_gov");
      const maudeTerm = termItem.value.find(term => term.proposal.db_entrez_enum == "maude");
      
      this.splitTerm = {
        term: termItem.term,
        initTerm: termItem.term,
        type: termItem.value[0].proposal.is_sota_term ? "sota" : "device",
        dbs: dbs,  
        clinicalTrialsSearchField: (clinicalTrialsTerm && clinicalTrialsTerm.search_field) ? clinicalTrialsTerm.search_field : this.clinicalTrialsSearchFields[0],
        maudeSearchField: (maudeTerm && maudeTerm.search_field) ? maudeTerm.search_field : this.maudeSearchFields[0],  
        isSearchFile: termItem.isSearchFile,

        dbsOptions: this.lit_dbs.filter(db => dbs.includes(db.entrez_enum)),
        aeDbsOptions: this.ae_dbs.filter(db => dbs.includes(db.entrez_enum)),
      };
      console.log(this.splitTerm)

      this.showModal("split-terms-modal");
    },
    onSubmitTerm: function (e, validateQuotes=true, validateMaude=true, isRemoveTermQuote=false) {
      e.preventDefault();
      const isSearchFile = this.newTerm.isSearchFile;
      const term = this.newTerm.term;
      const ID = this.newTerm.propID;

      // validation
      const isMaude = this.newTerm.dbs.includes("maude") || this.newTerm.dbs.includes("maude_recalls");
      const isMaudeSearchFieldDefault = this.newTerm.maudeSearchField === this.maudeSearchFields[0];

      if(isMaude && term.length > 3 && isMaudeSearchFieldDefault && validateMaude){
        // Show maude error
        this.update_warning_data = {
          term,
          propID: ID,
        }
        // show warining popup
        this.showModal("update-term-maude-warning");
        return;
      }
      
      if (this.newTerm.term.includes("'") && validateQuotes) {
        if (isSearchFile) {
          // show eror of quote with file validation
          this.update_warning_data = {
            term,
            propID: ID,
          }
          this.showModal('update-term-validation-warning');
          return;
        } else {
          // show error of quote only
          this.update_warning_data = {
            term,
            propID: ID,
          }
          this.showModal("update-term-signle-quote-warning");
          return;
        }
      }
      if (isSearchFile) {
        // show error of file validation only
        this.update_warning_data = {
          term,
          propID: ID,
        }
        this.showModal("update-term-warning");
        return;
      }

      // close all warnings if any 
      this.hideModal("update-term-signle-quote-warning");
      this.hideModal("update-term-maude-warning");

      // add or update
      if (this.newTerm.isUpdateTerm) this.onUpdateTerm(this.newTerm.propID, e, isRemoveTermQuote);
      else this.onAddTerm(e, isRemoveTermQuote);
    },
    onSplitTermSubmitted: function (e, validate=true) {
      e.preventDefault();
      const isSearchFile = this.splitTerm.isSearchFile;
      const initTerm = this.splitTerm.initTerm;

      // validation
      if (isSearchFile && validate) {
        // show error of file validation only
        this.update_warning_data = {
          term: initTerm,
          propID: null,
        };
        this.showModal("split-term-warning");
        return;
      }

      let postData;
      const termItem = this.terms.find(item => item.term === initTerm);
      // termItem.value[0].proposal.id
      const selectedProps = termItem.value.filter(prop => this.splitTerm.dbs.includes(prop.proposal.db_entrez_enum));
      const propsIds = selectedProps.map(prop => prop.proposal.id);

      postData = {
        prop_ids: propsIds,
        term: this.splitTerm.term,
        is_sota_term: this.splitTerm.type === "sota" ? true : false,
        clinical_trials_search_field: this.splitTerm.clinicalTrialsSearchField,
        maude_search_field: this.splitTerm.maudeSearchField,
        update_type: "split"
      }
      console.log({ postData });

      // hide any warning
      this.hideModal("split-term-warning");

      // Update Status to Saving
      this.updateRowStatus(termItem.value[0].proposal.id, "SAVING");

      this.isSplittingTermLoading = true;
      axios.post(searchTermsUpdateURL, data = postData)
        .then(
          res => {
            console.log(res);
            this.isSplittingTermLoading = false;
            this.terms = res.data.terms;
            this.totalTermsCount = res.data.total_terms;
            this.splitTerm = SplitTermInit;
            this.hideModal("split-terms-modal");
            this.makeToast("success", "The search term was split successfully.");
            this.fetchDBsPreviews();
          },
          err => {
            console.log({ err });
            this.isSplittingTermLoading = false;
            let error_msg = this.handleErrors(err);
            this.makeToast("danger", error_msg);
          }
        )
    },
    onSignleTermUpdate: function (propID) {
      const termIndex = this.terms.findIndex(item => item.id === propID);
      const termVal = this.terms[termIndex];
      const dbs = termVal.value.map(item => item.proposal.db_entrez_enum);
      const clinicalTrialsTerm = termVal.value.find(term => term.proposal.db_entrez_enum == "ct_gov");
      const maudeTerm = termVal.value.find(term => term.proposal.db_entrez_enum == "maude");

      if (projectType === 'Custom') {
        type = termVal.value[0].proposal.search_label;
      } else {
        type = termVal.value[0].proposal.is_sota_term ? "sota" : "device";
      }

      this.newTerm = {
        term: termVal.term,
        type: type,
        dbs: dbs,  
        clinicalTrialsSearchField: this.clinicalTrialsSearchFields[0],
        maudeSearchField: this.maudeSearchFields[0],
        pico_category: termVal.value[0].proposal.pico_category || "",
      };
      
      if (clinicalTrialsTerm && clinicalTrialsTerm.search_field) this.newTerm.clinicalTrialsSearchField = clinicalTrialsTerm.search_field;
      if (maudeTerm && maudeTerm.search_field) this.newTerm.maudeSearchField = maudeTerm.search_field;
      
      this.newTerm.isUpdateTerm = true;
      this.newTerm.propID = propID;
      this.newTerm.isSearchFile = termVal.is_search_file;
      this.showModal("add-edit-term-modal");
    },
    onUpdateTriggered: function (index, ID, term, isSearchFile, event) {
      if (this.isSearchTermTypeValid(ID, index)) {
        let foundTerm = this.terms.find(term => term.id === ID);
        let foundMaude = foundTerm.value.some(value => value.proposal.db_entrez_enum === "maude");
        let foundMaudeRecalls = foundTerm.value.some(value => value.proposal.db_entrez_enum === "maude_recalls");
        const isMaudeSearchFieldDefault = this.newTerm.maudeSearchField === this.maudeSearchFields[0];

        if((foundMaude || foundMaudeRecalls) && term.length > 3 && isMaudeSearchFieldDefault){
          // show eror of quote with file validation
          this.update_warning_data = {
            term,
            propID: ID,
          }
          // show warining popup
          this.showModal("update-term-maude-warning")
          return;
        }
        if (term.includes("'")) {
          if (isSearchFile) {
            // show eror of quote with file validation
            this.update_warning_data = {
              term,
              propID: ID,
            }
            this.showModal('update-term-validation-warning');
          } else {
            // show error of quote only
            this.update_warning_data = {
              term,
              propID: ID,
            }
            this.showModal("update-term-signle-quote-warning");
          }
        }
        else if (isSearchFile) {
          // show error of file validation only
          this.update_warning_data = {
            term,
            propID: ID,
          }
          this.showModal("update-term-warning");
        } else
          this.onUpdateTerm(ID, event);
      }

    },
    onBulkUpdateTriggered: function () {
      this.showModal("bulk-update-warning");
    },
    onDeleteTriggered: function (propID, deletedTerm, isSearchFile, event) {
      // show delete warning
      const termLen = deletedTerm.length;
      const deletedTermTruncate = termLen < 50 ?
        deletedTerm : `${deletedTerm.slice(0, 20)}....${deletedTerm.slice(termLen - 10, termLen)}`;
      const termValues = this.terms.find(item => item.term === deletedTerm).value;
      let dbs = termValues.map(item => item.proposal.db);
      dbs = dbs.join(", ");
      this.delete_warning_data = {
        term: deletedTerm,
        termTruncate: deletedTermTruncate,
        propID,
        dbs,
        hasFile: isSearchFile ? true : false,
      }
      this.showModal("delete-warning-modal");
    },
    onPreviewResults: async function (preview, expectedResults, db) {
      console.log({ preview });
      if (!expectedResults || expectedResults === -1 || !preview) {
        this.makeToast("info", "0 results were found for this search term.");
        return
      }
      if (preview && !preview.results && !preview.results_url && expectedResults > this.searchProtocol.max_imported_search_results) {
        this.onErrorDisplay("Way too many results can't create a preview for this Search Term.", title = "Search Terms Preview Unavailable");
        return
      } else if (preview && !preview.results && !preview.results_url) {
        this.onErrorDisplay("Failed to create the preview for this database search term", title = "Search Terms Preview Unavailable");
        return
      }
      if (db === "pubmed" || db === "scholar") {
        this.previewResultsURL = preview.results_url;
        const timeOur = setTimeout(() => {
          document.getElementById("preview-pubmed-url").click();
          return () => clearTimeout(timeOur);
        }, 500);
        // this.showModal("pubmed-preview-modal");
      } else if (db === "pmc") {
        let resultsPostURL = preview.results_url;
        resultsPostURL = JSON.parse(resultsPostURL);
        setTimeout(() => {
          document.getElementById("pmc-preview-toast-term").setAttribute('value', resultsPostURL.term);
          document.getElementById("pmc-preview-toast-date-filter").setAttribute('value', resultsPostURL.filters[0].value);
          document.getElementById('pmc-preview-form').submit();
        }, 500);
        // this.showModal("pmc-preview-modal");
      } else {
        this.previews = JSON.parse(preview.results);
        console.log(this.previews)
        this.showModal("preview-resuls-section");
      }

    },
    

    // Async Actions
    fetchDBsPreviews: function () {
      // Check the Fetching Preview & Expected Results Count Status.
      const interval2 = setInterval(function () {

        const postData = {
          is_checking: true,
          order_by: this.sortedBy,
        };
        axios.post(searchTermsUpdateURL, data = postData)
          .then(
            res => {
              this.terms.forEach((item, index) => {
                const lastValue = item.value[item.value.length - 1];
                if (lastValue.report && lastValue.report.status === "FETCHING_PREVIEW") {
                  const newItem = res.data.terms.find(newTerm => newTerm.id === item.id);
                  if (newItem && newItem.value[item.value.length - 1].report.status !== "FETCHING_PREVIEW") {
                    console.log("Updating Terms ...");
                    this.$set(this.terms, index, newItem);
                  }
                }
              });

              if (res.data.is_completed) {
                this.validator = res.data.validator;
                this.terms = res.data.terms;
                console.log("this.terms", this.terms);
                // const foundError = this.terms.findIndex(item => item.value[item.value.length-1].report.status === "FAILED");
                const foundError = this.terms.findIndex(item => {
                  if (item.value && item.value.length > 0) {
                    const lastValue = item.value[item.value.length - 1];
                    if (lastValue.report && lastValue.report.status === "FAILED") {
                      return true; // Error condition found
                    }
                  }
                  return false; // No error condition
                });

                if (foundError > -1) {
                  // const errorMsg = this.$createElement(
                  //   'div',
                  //   [
                  //     "Some search terms were not updated successfully, please check the failed one's errors & fix them accordingly.",
                  //     this.$createElement("br"),
                  //     "Still stuck? Get instant help from our team by submitting a ticket",
                  //     this.$createElement('a', { attrs: { "href": "https://share.hsforms.com/1jqB4CJx9RxyvGL3qQYo2rgcq0hk " } }, [' Here']),
                  //   ]
                  // );
                  // this.makeToast("error", errorMsg);
                } else
                  this.makeToast("success", "Search term updating expected results count succeeded.");

                clearInterval(interval2);
                console.log("Interval has been cleared");
                this.hideLoadingPopup();
                // this.enableActionButtons()
              };
            },
            err => {
              console.log({ err });
            }
          )
      }.bind(this), 5000);
    },
    onDeleteSearchTerm: function (propID, deletedTerm, event) {
      const url = searchTermsDeleteURL.replace("/0/", `/${propID}/`);
      this.isDeletePending = true;

      axios.delete(url).then(
        res => {
          this.isDeletePending = false;
          const { term } = res.data;
          const newTerms = this.terms;
          const deletedTermIndex = newTerms.findIndex(item => item.term === term);
          if (deletedTermIndex > -1)
            newTerms.splice(deletedTermIndex, 1);

          this.terms = newTerms;
          this.totalTermsCount = this.totalTermsCount - 1;
          this.hideModal("delete-warning-modal");
          const success_msg = `'${term}' Search Term has been deleted successfully`;
          this.makeToast("success", success_msg);
        },
        err => {
          this.isDeletePending = false;
          console.log({ err });
          let error_msg = this.handleErrors(err);
          this.makeToast("danger", error_msg);
        }
      )
    },
    onUpdateTerm: function (propID, event, isRemoveTermQuote=false) {
      let postData;

      if (this.newTerm.isUpdateTerm) {
        postData = {
          prop_id: propID,
          lit_review_id: litReviewID,
          term: this.newTerm.term,
          entrez_enums: this.newTerm.dbs,
          is_sota_term: this.newTerm.type === "sota" ? true : false,
          clinical_trials_search_field: this.newTerm.clinicalTrialsSearchField,
          maude_search_field: this.newTerm.maudeSearchField,
          term_type: this.newTerm.type,
          pico_category: this.newTerm.pico_category,
        }
      }
      else {
        postData = this.getRowData(propID);
      }
      
      // check term_quote_remove
      if (isRemoveTermQuote) {
        console.log("replacing search term single quote with double quotes");
        for (let key in postData) {
          if (key === "term") {
            postData[key] = postData[key].replace(/'/g, '"');
          }
        }
      }

      postData = { ...postData, update_type: "single", "total_count": this.terms.length }
      console.log({ postData });

      // hide any warning
      this.hideModal("update-term-signle-quote-warning");
      this.hideModal('update-term-validation-warning');
      this.hideModal("update-term-warning");
      this.hideModal("update-term-maude-warning");
      // this.disableActionButtons();

      // Update Status to Saving
      this.updateRowStatus(propID, "SAVING");
      this.isCreatingTermLoading = true;

      axios.post(searchTermsUpdateURL, data = postData)
        .then(
          res => {
            console.log(res);
            this.isCreatingTermLoading = false;
            this.terms = this.terms.map(termObj => {
              if (termObj.id === propID)
                return res.data.new_terms[0];
              else
                return termObj;
            });
            this.newTerm = {
              term: "",
              type: "",
              dbs: [],
              isUpdateTerm: false,
            };
            this.hideModal("add-edit-term-modal");
            this.makeToast("success", "Search terms update was successful.");
            this.fetchDBsPreviews();
          },
          err => {
            console.log({ err });
            this.isCreatingTermLoading = false;
            let error_msg = this.handleErrors(err);
            // Update Status to Saving
            this.updateRowStatus(propID, "FAILED");
            this.makeToast("danger", error_msg);
          }
        )
    },
    onBulkUpdate: function () {
      this.hideModal("bulk-update-warning");
      
      let isSotaNull = this.terms.some((item) => {
        if (this.isSearchTermTypeValid(item.value[0].proposal.id, item.index)) return false
        return true
      });
      if (!isSotaNull) {
        const rows = [];
        this.terms.map(item => {
          if (this.selectedTerms.includes(item.id)) {
            const propID = item.value[0].proposal.id;
            const updatedRow = this.getRowData(propID);
            rows.push(updatedRow);
          };
        });
        const postData = {
          update_type: "bulk",
          rows,
        }

        // Update Status to Saving
        this.selectedTerms.forEach(termID => {
          this.updateRowStatus(termID, "SAVING");
        });

        axios.post(searchTermsUpdateURL, data = postData)
          .then(
            res => {
              // Update Status 
              this.selectedTerms.forEach(termID => {
                this.updateRowStatus(termID, "Fetching Expected Count");
              });
              this.selectedTerms = [];
              this.isCheckAll = false;
              this.fetchDBsPreviews();
            },
            err => {
              console.log({ err });
              // Update Status to FAILED
              this.selectedTerms.forEach(termID => {
                this.updateRowStatus(termID, "FAILED");
              });
              let error_msg = this.handleErrors(err);
              this.makeToast("danger", error_msg);
            }
          )
      }

    },
    onSpecificBulkUpdate: function (e) {
      e.preventDefault();
      const rows = [];
      this.terms.map(item => {
        if (this.selectedTerms.includes(item.id)) {
          const propID = item.value[0].proposal.id;
          const updatedRow = this.getRowData(propID);
          updatedRow.entrez_enums = this.dbBulkTerm.dbs;
          rows.push(updatedRow);
        };
      });

      const postData = {
        update_type: "bulk",
        rows,
      };

      // Update Status to Saving
      this.selectedTerms.forEach(termID => {
        this.updateRowStatus(termID, "SAVING");
      });

      this.hideModal("db-bulk-update");
      axios.post(searchTermsUpdateURL, data = postData)
        .then(
          res => {
            // Update Status 
            this.selectedTerms = [];
            this.fetchDBsPreviews();
          },
          err => {
            console.log({ err });
            // Update Status to FAILED
            this.selectedTerms.forEach(termID => {
              this.updateRowStatus(termID, "FAILED");
            });
            let error_msg = this.handleErrors(err);
            this.makeToast("danger", error_msg);
          }
        )
    },
    onBulkDelete: function(){
      const postData = {props_ids: this.selectedTerms};
      this.isBulkDeletePending = true;

      axios.post(BulkDeleteURL, data=postData)
        .then(
          res => {
            this.isBulkDeletePending = false;
            const newTerms = this.terms;

            this.selectedTerms.forEach(deletedTermID => {  
              const deletedTermIndex = newTerms.findIndex(item => item.id === deletedTermID);
              if (deletedTermIndex > -1)
                newTerms.splice(deletedTermIndex, 1);
            });
            this.terms = newTerms;
            this.totalTermsCount = this.totalTermsCount - this.selectedTerms.length;

            this.makeToast("success", `${this.selectedTerms.length} terms were deleted successfully.`);
            this.hideModal("bulk-delete-confirm");
            this.selectedTerms = [];
          },
          err => {
            console.log({ err });
            this.isBulkDeletePending = false;
          }
        )
    },
    onAddTerm: function (e, isRemoveTermQuote=false) {
      if (this.totalTermsCount > parseInt(this.maxTerms))
        this.$refs['max-terms-toast'].show();

      const formData = {
        total_count: this.totalTermsCount,
        term: this.newTerm.term,
        is_sota_term: this.newTerm.type === "sota" ? true : false,
        entrez_enums: this.newTerm.dbs,
        clinical_trials_search_field: this.newTerm.clinicalTrialsSearchField,
        maude_search_field: this.newTerm.maudeSearchField,
        entrez_enums: this.newTerm.dbs,
        term_type: this.newTerm.type,
        pico_category: this.newTerm.pico_category,
      }
      // check term_quote_remove
      if (isRemoveTermQuote) {
        console.log("replacing search term single quote with double quotes");
        for (let key in formData) {
          if (key === "term") {
            formData[key] = formData[key].replace(/'/g, '"');
          }
        }
      }

      this.isCreatingTermLoading = true;

      axios.post(searchTermsURL, data = formData)
        .then(
          res => {
            this.hideModal('add-edit-term-modal');
            this.isCreatingTermLoading = false;
            this.terms = [...this.terms, ...res.data.added_terms];
            this.totalTermsCount = this.totalTermsCount + 1;
            this.newTerm = {
              term: "",
              type: "",
              dbs: [],
              isUpdateTerm: false,
            };

            // scroll to the bottom of the page
            let timeOutID = setTimeout(() => {
              window.scrollTo(0, document.body.scrollHeight);
              return clearTimeout(timeOutID);
            }, 1000);
            this.fetchDBsPreviews();
            this.makeToast("success", "A new search term has been added successfully.");
          },
          err => {
            console.log({ err });
            this.isCreatingTermLoading = false;
            let error_msg = this.handleErrors(err);
            this.makeToast("danger", error_msg);
          }
        )
    },
  },
  async mounted() {
    // aeListURL and maxTerms those vars are declared inside the django template
    this.isRecordsLoading = true;
    this.showLoadingPopup();
    await axios.get(searchTermsURL)
      .then(
        res => {
          this.hideLoadingPopup();
          console.log(res);
          const {
            terms, dbs, lit_dbs, ae_dbs, validator, lit_review_id, search_protocol, summary_doc, total_terms,
            CLINICAL_TRIALS_SEARCH_FIELD_OPTIONS, FDA_MAUDE_SEARCH_FIELD_OPTIONS,search_labels, pico_categories
          } = res.data;

          this.isRecordsLoading = false;
          this.terms = terms;
          this.dbs = dbs;
          this.lit_dbs = lit_dbs;
          this.ae_dbs = ae_dbs;
          this.clinicalTrialsSearchFields = CLINICAL_TRIALS_SEARCH_FIELD_OPTIONS;
          this.maudeSearchFields = FDA_MAUDE_SEARCH_FIELD_OPTIONS;
          this.clinicalTrialsSearchField = CLINICAL_TRIALS_SEARCH_FIELD_OPTIONS[0];
          this.maudeSearchField = FDA_MAUDE_SEARCH_FIELD_OPTIONS[0];
          this.validator = validator;
          this.litReviewID = lit_review_id;
          this.searchProtocol = search_protocol;
          this.summaryDoc = summary_doc;
          this.totalTermsCount = total_terms;
          this.lastTermIndex = total_terms;
          this.SearchLabelOptions = search_labels;
          this.picoCategories = pico_categories;
          
          for (let term of this.terms) {
            if (term.value[0].report && term.value[0].report.status === 'FETCHING_PREVIEW') {
              this.fetchDBsPreviews();
              break;
            }
          }
          setTimeout(() => {
            if (this.totalTermsCount > parseInt(this.maxTerms))
              this.$refs['max-terms-toast'].show();
          }, 1000);
        },
        err => {
          this.hideLoadingPopup();
          console.log(err);
          this.isRecordsLoading = false;
        }
      );
    const timeOut = setTimeout(() => {
      this.styleTooltips();
      return clearTimeout(timeOut);
    }, 2000);
  }
})

