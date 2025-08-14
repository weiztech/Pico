axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
  el: '#app',
  mixins: [globalMixin],
  delimiters: ["[[", "]]"],
  data() {
    return {
      litSearches: [],
      dbs: [],
      lit_dbs: [],
      ae_dbs: [],
      maxImportedSearchResults: null,
      isRecordsLoading: false,
      isUploadOwnCitationsLoading: false,
      isUploadCitaionModalOpen: false,
      currentEditedAE: null,
      sortedBy: "",
      currentDB: null,
      autoSearch: null,
      awsS3UploadingFile: null,
      awsS3CurrentKey: null,
      runSearchReady: false,
      uploadOwnCitationsForm: {
        database: 'embase',
        file: null,
        external_db_name: "",
        external_db_url: "",
      },
      isRunAllAutoSearch:false,
      isRunAutoSearch:false,
      isValidationModalOpen: false,

      isResultsFiltered: false,
      isSearchesClearing: false,
      isCheckAll: false,
      selectedSearches: [],
      isManualUploadLoading: false,
      
      filteredSearches: [],
      dbFilter: [],
      dbAppliedFilters: [],
      searchTerm: "",
      statusFilter: "",
      typeFilter: "",
    }
  },
  computed: {
    validateSearchOptions: function () {
      const completedSearches = this.litSearches.filter(search => search.import_status === 'COMPLETE');
      const options = [{
        name: "Select A Search Term",
        value: "",
      }];

      completedSearches.forEach(search => {
        options.push({
          name: `${search.db.displayed_name}-${search.term}`,
          value: search.id,
        })
      });

      return options;
    },
    visibileLiteratureSearches: function() {
      if (this.isResultsFiltered)
        return this.filteredSearches;
      else
        return this.litSearches;
    },
    dbOptions: function() {
      let dbsOps = this.dbs.map((db) => ({
        name: db.name,
        value: db.name,
      }));
      dbsOps = [{
        name: "Custom (Not Listed)",
        value: "external",
      }, ...dbsOps];

      return dbsOps; 
    },
  },
  watch: {
    selectedSearches: function (newVal, oldVal) { // watch it
      if (this.isResultsFiltered)
        this.isCheckAll = this.filteredSearches.length === this.selectedSearches.length;
      else
        this.isCheckAll = this.litSearches.length === this.selectedSearches.length;
    },
    litSearches: function (newVal, oldVal) { // watch it
      this.filteredSearches = this.filteredSearches.map(search => newVal.find(s => s.id === search.id));
    },
  },
  methods: {
    dateFormat:function(str_date){
      const [day, month, year] = str_date.split('-');
      const formattedDate = `${month}-${day}-${year}`;
      return formattedDate
    },
    // Helpers
    isCountHasValue: function(search, fieldName) {
      return (search[fieldName] && search[fieldName] != '-1') || search[fieldName] == 0;
    },
    refreshFileUploader: function (ID) {
      // display dropsoze again and allow user to reupload files again
      document.getElementById("drop-zone-" + ID).style.display = "block";
      document.getElementById("drop-zone-inner-" + ID).classList.remove("active");
      document.getElementById("progress-bar-" + ID).style.display = "none";
      document.getElementById('file-details-' + ID).style.display = "none";
      document.getElementById("upload-success-" + ID).style.display = "none";
      this.runSearchReady = false;

      // reset progress bar to 0%
      document.getElementById('progress-inner-' + ID).style.width = "0%";
      document.getElementById('progress-percentage-' + ID).innerHTML = "0%";
    },
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
    isSearchExcluded: function(search) {
      return search.import_status === 'COMPLETE' && search.limit_excluded;
    },
    closeOnManualUploadModal(ID) {
      this.hideModal('search-modal-' + ID);
      this.refreshFileUploader(ID);
    },
    onUploadSearchFile: function (e, litSearch) {
      const file = e.target.files[0];

      this.awsS3UploadingFile = file;
      const fileType = file.name.split('.').pop();

      if (!this.isValidFileExtension(litSearch.db.entrez_enum, fileType)) {
        this.currentDB = litSearch.db.entrez_enum;
        this.showToast("search-file-warning");
        return;
      }

      this.uploadFileToAWS(file, fileType, litSearch.id, "SEARCH");
    },
    onClearSearchFile: function(event, search) {
      this.awsS3UploadingFile = null;
      const fileElm = document.getElementById(`input-${search.id}`);
      fileElm.value = null;

      const dropzone = document.getElementById("drop-zone-" + search.id);
      const dropzoneInner = document.getElementById("drop-zone-inner-" + search.id);
      const uploadSuccessSection = document.getElementById("upload-success-" + search.id);
      const uploadedFileDetailsElm = document.getElementById('file-details-'+ search.id);
      const clearIcon = document.getElementById("clear-file-icon-"+ search.id)
      const progressElmInner = document.getElementById('progress-inner-'+ search.id);
      const preogressPercentageElm =  document.getElementById('progress-percentage-'+ search.id);

      clearIcon.style.display = "none";
      dropzone.style.display = "block";
      dropzoneInner.classList.remove("active");
      uploadSuccessSection.style.display = "none";
      uploadedFileDetailsElm.style.display = "none";
      progressElmInner.style.width = "0%";
      preogressPercentageElm.innerHTML = "0%";
    },
    downloadFile(url) {
      var link = document.createElement('a');
      link.href = url;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },
    // downloadFile('https://example.com/myfile.pdf', 'My File.pdf');
    isValidFileExtension: function (selected_db, fileType) {
      let isValid = false;
      
      switch (selected_db) {
        case 'pubmed':
          isValid = (fileType === 'xml' || fileType === 'text' || fileType === 'txt');

        case 'cochrane':
          isValid = (fileType === 'text' || fileType === 'txt');

        case 'ct_gov':
          isValid = (fileType === 'csv');

        case 'pmc':
          isValid = (fileType === 'xml' || fileType === 'text' || fileType === 'txt');

        case 'pmc_europe':
          isValid = (fileType === 'ris');

        case 'maude_recalls':
          isValid = (fileType === 'xlsx' || fileType === 'xls' || fileType === 'csv');

        case 'maude':
          isValid = (fileType === 'xlsx' || fileType === 'xls' || fileType === 'csv');
        
        case 'scholar':
            isValid = (fileType === 'xlsx' || fileType === 'xls' || fileType === 'csv' || fileType === 'ris');
        
        case 'embase':
          isValid = (fileType === 'ris');

        default:
          isValid = (fileType === 'xlsx' || fileType === 'xls' || fileType === 'csv' || fileType === 'ris' || fileType === 'text' || fileType === 'txt');
      }

      if (!isValid) this.showToast("search-file-warning");
      return isValid;
    },

    // Actions 
    onCheckAll: function(e) {
      if (e.target.checked) {
        this.selectedSearches = this.isResultsFiltered ?
        this.filteredSearches.map(s => s.id)
        : this.litSearches.map(s => s.id);
      } else {
        this.selectedSearches = [];
      }
    },
    onOpenValidationModal: function() {
      this.isValidationModalOpen = false;
      const TM01 = setTimeout(() => {
        this.isValidationModalOpen = true;
        return clearTimeout(TM01);
      }, 300);
      
      this.showModal('validate-search-popup-section');
    },
    onCloseValidationModal: function() {
      this.isValidationModalOpen = false;
      this.hideModal('validate-search-popup-section');
    },
    onSearch: function (e) {
      e.preventDefault();

      this.filteredSearches = this.litSearches.filter(search => search.term.toLowerCase().includes(this.searchTerm.toLowerCase()));
      this.isResultsFiltered = true;
    },
    onFilter: function (e) {
      this.filteredSearches = this.litSearches.filter(search => {
        const dbMatch = this.dbFilter.length ? this.dbFilter.includes(search.db.entrez_enum) : true;
        const isSotaMatch = this.typeFilter !== "" ? this.typeFilter === search.is_sota_term : true;
        let statusMatch = this.statusFilter ? this.statusFilter === search.import_status : true;
        // Is Ecxluded ?
        statusMatch = this.statusFilter === "EXCLUDED" 
        ? this.isSearchExcluded(search)
        : statusMatch;
        // Is Completed ?
        statusMatch = this.statusFilter === "COMPLETE" 
        ? search.import_status === 'COMPLETE' && !search.none_excluded && !search.limit_excluded
        : statusMatch;

        this.isResultsFiltered = true;
        return dbMatch && isSotaMatch && statusMatch;
      });

      this.dbAppliedFilters = this.dbFilter;
      this.hideModal("filters-slider");
    },
    onClearFilters: function () {
      this.searchTerm = "";
      this.dbFilter = [];
      this.dbAppliedFilters = [];
      this.typeFilter = "";
      this.statusFilter = "";
      this.filteredSearches = [];
      this.isResultsFiltered = false;
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
    expandDatabaseSection: function(reviewID) {
      const termElm = this.$refs['term-section-'+reviewID][0];
      termElm.classList.toggle("active");
    },
    isShowTermExpand: function(literature_search) {
      if (window.innerWidth < 1500) {
        return literature_search.term.length > 40;
      }
      return literature_search.term.length > 200;
    },
    onUploadCitationsDbChanged: function(selectedDatabase) {
      this.uploadOwnCitationsForm.database = selectedDatabase;
    },
    onUploadCitationsFileChanged: function(uploadedFile) {
      this.uploadOwnCitationsForm.file = uploadedFile;
    },
    onOpenUploadOwnCitationsModal: function() {
      this.isUploadCitaionModalOpen = true;
      this.showModal('upload-own-searches');
    },
    onUploadOwnCitations: function() {
      const formData = new FormData();
      // Validation 
      if (!this.uploadOwnCitationsForm.database || !this.uploadOwnCitationsForm.file) {
        this.makeToast("error", "Please provide both fields: a database and upload a file.");
        return;
      }
      if (this.uploadOwnCitationsForm.database === "external" && !this.uploadOwnCitationsForm.external_db_name) {
        this.makeToast("error", "Please provide a name for your external database.");
        return;
      }

      formData.append("database", this.uploadOwnCitationsForm.database);
      formData.append("file", this.uploadOwnCitationsForm.file);
      if (this.uploadOwnCitationsForm.database == "external") {
        formData.append("external_db_name", this.uploadOwnCitationsForm.external_db_name);
        formData.append("external_db_url", this.uploadOwnCitationsForm.external_db_url);
      }
      this.isUploadOwnCitationsLoading = true;

      axios.post(uploadCitationsAPI, data=formData)
      .then(
        res => {
          this.makeToast("success", `Your file has been processed successfully and ${res.data.imported_articles} results were imported!`);
          this.hideModal("upload-own-searches");
          this.isUploadCitaionModalOpen = false;
          this.isUploadOwnCitationsLoading = false;
        },
        err => {
          console.log({err});
          errorMessage = this.handleErrors(err);
          this.makeToast("error", errorMessage);
          this.hideModal("upload-own-searches");
          this.isUploadCitaionModalOpen = false;
          this.isUploadOwnCitationsLoading = false;
        }
      )
      console.log(this.uploadOwnCitationsForm);
    },
    // onSortTerm: function () {
    //   if (this.sortedBy === "-term") {
    //     this.sortedBy = "term";
    //     this.terms = this.terms.sort((a, b) => this.compare(a, b, "term", "ASC"));
    //   } else {
    //     this.sortedBy = "-term";
    //     this.terms = this.terms.sort((a, b) => this.compare(a, b, "term", "DSC"));
    //   }
    // },

    // Async Actions
    checkStatus: function (litSearch) {
      const interval = setInterval(function () {
        const postData = { "search_id": litSearch.id };
        let axiosConfig = {
          headers: {
            'Content-Type': 'application/json; charset=UTF-8',
          }
        };
        axios({
          method: 'post',
          url: CheckStatusURL,
          headers: axiosConfig,
          data: postData,
        }).then(
          res => {
            console.log(res.data);
            if (res.data.is_completed) {
              const newRecords = this.litSearches.map((item) => {
                const updatedLitSearch = res.data.literature_search;
                if (item.id === updatedLitSearch.id) {

                  return updatedLitSearch;
                }
                return item;
              });

              this.litSearches = newRecords;
              clearInterval(interval);
              if(this.isRunAllAutoSearch){
                this.isRunAutoSearch = false
              }
              console.log("Interval has been cleared");
            }
          },
          err => {
            console.log({ err });
            if(this.isRunAllAutoSearch){
              this.isRunAutoSearch = false
            }
          }
        );
      }.bind(this), 5000);
    },
    checkGenerateSearchReport: function (search_id) {
      const generateBTN = this.$refs["generate-search-report-btn-" + search_id][0];

      const interval5 = setInterval(function () {
        const postData = { "search_id": search_id, is_checking: true };
        axios({
          method: 'post',
          url: generateReportURL,
          data: postData,
        }).then(
          res => {
            console.log(res.data);
            const Search = res.data;
            const Search_file = res.data.search_report
            if (Search.search_report) {
              const newRecords = this.litSearches.map((item, index) => {
                if (item.id === Search.id) {
                  return Search;
                }
                return item;
              });

              this.litSearches = newRecords;
              let success_msg = `Search Report Has been generated successfully.`;
              this.makeToast("success", success_msg);
              // this.enableElement(generateBTN, "Download Results File");
              generateBTN.disabled = false;

              // download the file
              this.downloadFile(Search_file)

              this.litSearches = newRecords;
              clearInterval(interval5);
              console.log("Interval has been cleared");
            } else if (Search.search_report_failing_msg) {
              clearInterval(interval5);
              const error_msg = Search.search_report_failing_msg
              this.onErrorDisplay(error_msg, "Search Term Result File");
              // this.enableElement(generateBTN, "Download Results File");
              generateBTN.disabled = false;
            }
          },
          err => {
            console.log({ err });
            clearInterval(interval5);
            const error_msg = this.handleErrors(err);
            this.makeToast("danger", error_msg);
            // this.enableElement(generateBTN, "Download Results File");
            generateBTN.disabled = false;
          }
        );
      }.bind(this), 5000);
    },
    checkClearDBStatus: function (searches) {
      const interval = setInterval(function () {
        const postData = {
          searches: searches,
          check_status: true,
        }

        axios({
          method: 'post',
          url: clearDatabaseURL,
          data: postData,
        }).then(
          res => {
            console.log(res.data);
            if (res.data.is_completed) {
              // const clearBTN = document.getElementById("clear-btn");
              // this.enableElement(clearBTN, "Clear");
              const newRecords = this.litSearches.map((item) => {
                const updatedLitSearches = res.data.literature_searchs;
                const updatedLitSearch = updatedLitSearches.find(ele => ele.id === item.id);
                if (updatedLitSearch) {
                  return updatedLitSearch;
                }
                return item;
              });
              this.litSearches = newRecords;
              this.isSearchesClearing = false;
              let success_msg = `Your selected searches has been cleared successfully!`;
              this.makeToast("success", success_msg);
              clearInterval(interval);
              console.log("Interval has been cleared");
            }
          },
          err => {
            console.log({ err });
          }
        );
      }.bind(this), 20000);
    },
    getDBCorrectFormat: function (db) {
      if (db === 'pubmed')
        return ["xml", "text", "txt"];

      if (db === 'cochrane')
        return ["text", "txt"];;

      if (db === 'ct_gov')
        return ["csv"];

      if (db === 'pmc')
        return ["xml", "text", "txt"];

      if (db === 'pmc_europe')
        return ["ris"];

      if (db === 'maude_recalls')
        return ["xlsx", "xls", "csv"];

      if (db === 'maude')
        return ["xlsx", "xls", "csv"];

      if (db === 'embase')
        return ["ris"];
    },

    // Actions
    onSortTerm: function () {
      if (this.sortedBy === "-term") {
        this.sortedBy = "term";
        this.litSearches = this.litSearches.sort((a, b) => this.compare(a, b, "term", "ASC"));
        this.filteredSearches = this.filteredSearches.sort((a, b) => this.compare(a, b, "term", "ASC"));
      } else {
        this.sortedBy = "-term";
        this.litSearches = this.litSearches.sort((a, b) => this.compare(a, b, "term", "DSC"));
        this.filteredSearches = this.filteredSearches.sort((a, b) => this.compare(a, b, "term", "DSC"));
      }
    },
    onSortDB: function () {
      if (this.sortedBy === "-db") {
        this.sortedBy = "db";
        this.litSearches = this.litSearches.sort((a, b) => this.compare(a, b, "db_name", "ASC"));
        this.filteredSearches = this.filteredSearches.sort((a, b) => this.compare(a, b, "db_name", "ASC"));
      } else {
        this.sortedBy = "-db";
        this.litSearches = this.litSearches.sort((a, b) => this.compare(a, b, "db_name", "DSC"));
        this.filteredSearches = this.filteredSearches.sort((a, b) => this.compare(a, b, "db_name", "DSC"));
      }
    },
    onSortStatus: function() {
      if (this.sortedBy === "-import_status") {
        this.sortedBy = "import_status";
        this.litSearches = this.litSearches.sort((a, b) => this.compare(a, b, "import_status", "ASC"));
        this.filteredSearches = this.filteredSearches.sort((a, b) => this.compare(a, b, "import_status", "ASC"));
      } else {
        this.sortedBy = "-import_status";
        this.litSearches = this.litSearches.sort((a, b) => this.compare(a, b, "import_status", "DSC"));
        this.filteredSearches = this.filteredSearches.sort((a, b) => this.compare(a, b, "import_status", "DSC"));
      }
    },
    clearSelectedSearches: function() {
      this.selectedSearches = [];
    },

    // Async Actions
    onRunSearch: function (litSearch, e) {
      // validation
      const fileWasUploadedSuccessfully = document.getElementById("upload-success-" + litSearch.id);
      if (fileWasUploadedSuccessfully.style.display == "none") {
        this.onErrorDisplay("Please Upload Search Term File first", title = "Search Dashboard Error");
        return;
      }

      const formData = new FormData();
      const fileType = this.awsS3UploadingFile.name.split('.').pop();

      // hide manual search popup
      this.hideModal('search-modal-' + litSearch.id);

      // input are valid submit request  
      formData.append('literature_search_id', litSearch.id);
      formData.append('file', this.awsS3CurrentKey);
      formData.append('file_type', fileType);
      axios.post(searchDashboardURL, data = formData)
        .then(
          res => {
            console.log(res);
            // this.isManualUploadLoading = false;
            const newRecords = this.litSearches.map((item, index) => {
              if (item.id === res.data.id) {
                return res.data;
              }
              return item;
            });

            this.litSearches = newRecords;
            this.checkStatus(litSearch);
            this.closeOnManualUploadModal(litSearch.id)
          },
          err => {
            console.log({ err });
            let error_msg = this.handleErrors(err);
            this.makeToast("danger", error_msg);
            this.refreshFileUploader(litSearch.id);
          }
        )
    },
    sleep(milliseconds) {
      return new Promise((resolve) => setTimeout(resolve, milliseconds));
    },
    async onRunAllAutoSearch(){
      // display dropsoze again and allow user to reupload files again
      
      this.runSearchReady = false;

      document.getElementById("progress-bar-run-all").classList.add("active");    

      // reset progress bar to 0%
      document.getElementById('progress-inner-run-all').style.width = "0%";
      document.getElementById('progress-percentage-run-all').innerHTML = "0%";
      this.isRunAllAutoSearch = true
      
      const LitListForRunSearch = this.litSearches.filter(elem => elem.is_ae_not_maude !== true && elem.db.auto_search_available === true);
      console.log(LitListForRunSearch)
      for(let i = 0; i < LitListForRunSearch.length;i++){ 
        const element = LitListForRunSearch[i]
       
          this.onRunAutoSearch(element, null, true);
          console.log('Start run auto search :', element.id)
          this.isRunAutoSearch = true
          console.log(LitListForRunSearch[i].import_status)
          // if (LitListForRunSearch[i].import_status === "RUNNING" )  {
            while (this.isRunAutoSearch) {           
              await  this.sleep(1000);
            }
          // }
          let p = (((i+1) * 100)/ LitListForRunSearch.length)
          console.log('p : ',p)
          document.getElementById('progress-inner-run-all').style.width = `${p.toFixed(2)}%`;
          document.getElementById('progress-percentage-run-all').innerHTML = `${p.toFixed(2)}%`;
          console.log('end run auto search :', element.id)
        // }       
      } 
      this.isRunAllAutoSearch = false  
      document.getElementById("progress-bar-run-all").classList.remove("active");    
      // reset progress bar to 0%
      document.getElementById('progress-inner-run-all').style.width = "0%";
      document.getElementById('progress-percentage-run-all').innerHTML = "0%"; 
      this.makeToast("success", "Run All Automated Search is completed");  
    },

    onRunAutoSearch: function (litSearch, e, overide_warning) { 
      const isMaude = litSearch.db_name == "FDA MAUDE";
      const isRecall = litSearch.db_name == "Maude Recalls";
      const sureProceed = overide_warning === true;
      const maudeSearchFieldtDefault = litSearch.maude_search_field && litSearch.maude_search_field.includes('product code');

      if (isRecall &&  !sureProceed && litSearch.term.length > 3){
        this.showModal('maude-search-warining'+litSearch.id);
      } else if (isMaude &&  !sureProceed && litSearch.term.length > 3 && maudeSearchFieldtDefault) {
        this.showModal('maude-search-warining'+litSearch.id);
      } else {
        if(sureProceed){
          this.hideModal('maude-search-warining'+litSearch.id)
        }
        const formData = new FormData();

        // input are valid submit request  
        formData.append('literature_search_id', litSearch.id);
        formData.append('search_term', litSearch.term);

        axios.post(runAutoSearchURL, data = formData)
          .then(
            res => {
              console.log(res);
              const newRecords = this.litSearches.map((item, index) => {
                if (item.id === res.data.id) {
                  return res.data;
                }
                return item;
              });
              this.litSearches = newRecords;
              this.checkStatus(litSearch);
            },
            err => {
              console.log({ err });
              let error_msg = this.handleErrors(err);
              this.makeToast("danger", error_msg);
            }
          )
        }
    },
    onForceImport: function (litSearch) {
      const formData = new FormData();

      // hide manual search popup
      this.hideModal('exclusion-modal-' + litSearch.id);

      // input are valid submit request  
      formData.append('literature_search_id', litSearch.id);
      formData.append('disableExclusion', true);
      // this.isManualUploadLoading = true;

      axios.post(searchDashboardURL, data = formData)
        .then(
          res => {
            console.log(res);
            // this.isManualUploadLoading = false;
            const newRecords = this.litSearches.map((item, index) => {
              if (item.id === res.data.id) {
                return res.data;
              }
              return item;
            });

            this.litSearches = newRecords;
            this.checkStatus(litSearch);
            this.closeOnManualUploadModal(litSearch.id)
          },
          err => {
            console.log({ err });
            let error_msg = this.handleErrors(err);
            this.makeToast("danger", error_msg);
            // this.isManualUploadLoading = false;
          }
        )
    },
    onExcludeSearch: function (litSearch, e) {
      const formData = new FormData();
      e.preventDefault();
      const count = e.target.elements.count.value;
      const excludeSearchBTN = document.getElementById("exclude-search-" + litSearch.id);
      excludeSearchBTN.disabled = true;

      // input are valid submit request  
      formData.append('literature_search_id', litSearch.id);
      formData.append('result_count', count);

      axios.put(excludeSearchURL, data = formData)
        .then(
          res => {
            console.log(res);

            const newRecords = this.litSearches.map((item, index) => {
              if (item.id === res.data.id) {
                return res.data;
              }
              return item;
            });

            this.litSearches = newRecords;
            let success_msg = `Result count for search term '${litSearch.term}' has been updated successfully!`;
            this.makeToast("success", success_msg);
            excludeSearchBTN.disabled = false;
            // this.hideModal("exclude-search-modal");
            this.hideModal('search-modal-'+litSearch.id);
          },
          err => {
            console.log({ err });
            let error_msg = this.handleErrors(err);
            this.makeToast("danger", error_msg);

            excludeSearchBTN.disabled = false;
            // this.hideModal("exclude-search-modal");
            this.hideModal('search-modal-'+litSearch.id);
          }
        )
    },
    onClearSearches: function (e) {
      e.preventDefault();
      const searches = this.selectedSearches;
      this.isSearchesClearing = true;

      // input are valid submit request  
      const postData = {
        searches: searches,
      }

      axios.post(clearDatabaseURL, data = postData)
        .then(
          res => {
            console.log(res);
            this.checkClearDBStatus(searches);
          },
          err => {
            console.log({ err });
            let error_msg = this.handleErrors(err);
            this.makeToast("danger", error_msg);
            this.isSearchesClearing = false;
          }
        )
    },
    onRunSearchForMe: async function (e) {
      const values = { type: "RUN_SEARCH" };
      this.disableElement(e.target);

      try {
        const res = await axios.post(requestHelpURL, data = values);
        this.enableElement(e.target);
        if (res.data.success)
          this.makeToast("success", "Your request have been submitted our team will run the searches and notify you asap");
        else {
          this.onErrorDisplay("Something wrong went, we couldn't send your request please wait a bit and try again", title = "Request Support Help")
        }

      } catch (err) {
        this.enableElement(e.target);
        const error_msg = this.handleErrors(err);
        this.makeToast("danger", error_msg);
      }
    },
    onGenerateSearchReport: function (search_id) {
      const generateBTN = this.$refs["generate-search-report-btn-" + search_id][0];
      const postData = { search_id: search_id }
      // this.disableElement(generateBTN, "Loading...");
      generateBTN.disabled = true;
      const search = this.litSearches.find(s => s.id === search_id);
      if (search && search.import_status !== "COMPLETE") {
        this.onErrorDisplay(`
                    This Search is not completed yet, 
                    thereby preventing the generation of the results file until the search is completed.
                    In order to to download the search results file, Please either Run a manual or an Auto search first.
                `)
        this.enableElement(generateBTN, "Download Results File");
        return;
      };

      axios.post(generateReportURL, data = postData)
        .then(
          res => {
            this.checkGenerateSearchReport(search_id)
          },
          err => {
            console.log({ err });
            let error_msg = this.handleErrors(err);
            this.makeToast("danger", error_msg);
            // this.enableElement(generateBTN, "Download Results File");
            generateBTN.disabled = false;
          }
        )
    },
    onValidateSearchTerm: function () {
      const search_term = document.getElementById("select-search-term").value;
      const manual_file = document.getElementById("select-manual-file").value;

      if (search_term && manual_file) {

        const file = document.getElementById("select-manual-file").files[0];
        const formData = new FormData();
        formData.append("search_id", search_term);
        formData.append("manual_file", file);

        console.log("formData", formData);
        axios.post(validateManualFileSearch, formData)
          .then(
            res => {
              validation = res.data.validation
              validation_error = res.data.validation_error
              if (validation) {
                console.log("Results Are Matching, Auto Search Results Are Correct");
                // hideModal
                this.hideModal("validate-search-popup-section")
                this.makeToast("success", "Results Are Matching, Auto Search Results Are Correct");
              } else {
                console.log("your file is not valid");
                // hideModal
                this.hideModal("validate-search-popup-section")
                this.onErrorDisplay(validation_error, title = "Validate Search Terms Error");
              }
            },
            err => {
              console.log({ err });
              // hideModal
              this.hideModal("validate-search-popup-section")
              let error_msg = this.handleErrors(err);
              this.makeToast("danger", error_msg);
            }
          )
      } else {
        console.log("please uplode file and search term first");
        // hideModal
        this.hideModal("validate-search-popup-section")
        let error_msg = "Please Select a Search Term and Upload a Manual Search Results File Befor Validation";
        this.makeToast("danger", error_msg);
      }
    },
  },
  async mounted() {
    this.isRecordsLoading = true;
    // aeListURL this var de clared inside the django template
    await axios.get(searchDashboardURL)
      .then(
        res => {
          console.log(res);
          this.isRecordsLoading = false;
          this.litSearches = res.data.literature_searchs;
          this.dbs = res.data.dbs;
          this.lit_dbs = res.data.dbs.filter(db => !db.is_ae && !db.is_recall);
          this.ae_dbs = res.data.dbs.filter(db => db.is_ae || db.is_recall)
          this.autoSearch = res.data.autosearch;
          this.maxImportedSearchResults = res.data.max_imported_search_results;
          this.uploadOwnCitationsForm.database = this.dbs.length ? this.dbs[0].name : '';

          // if any running search wach them (Refresh page once completed)
          for (search of this.litSearches) {
            if (search.import_status === "RUNNING") {
              this.checkStatus(search);
            }
          }
        },
        err => {
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