axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
  el: '#appraisals',
  mixins: [globalMixin],
  delimiters: ["[[", "]]"],
  data() {
    return {
      searchTerm: "",
      // newAppraisalFile: "",
      isLoading: false,
      isManualAppraisalCreationLoading: false,
      maxResults: maxResults ? maxResults : null,
      collapsedInsights: false,

      appraisals: [],
      pageSize: 30,
      appraisalsInsights: null,
      pagination: {
        current: 0,
        count: 0,
        next: 0,
        previous: 0,
        last: 0,
        page_range: []
      },
      tablePageIndicator: "",
      // filters
      searchTerm: "",
      sorting: "article_review__article__title",

      // below are for input state only
      isSotaFilter: null,
      statusFilter: [],
      
      // below reflect the actual applied filter if any
      appliedIsSotaFilter: null,
      appliedStatusFilter: [],

      statusFilterUncompleteOptions: [
        {
          name: "Missing full text pdf/Incomplete",
          value: "Missing full text pdf/Incomplete",
        },
        {
          name: "Full text uploaded/Ready for Review",
          value: "Full text uploaded/Ready for Review",
        },
        {
          name: "Needs Suitability/Outcomes Dropdowns",
          value: "Needs Suitability/Outcomes Dropdowns",
        },
        {
          name: "Incomplete Sota",
          value: "Incomplete Sota",
        },
        {
          name: "Incomplete Device Review",
          value: "Incomplete Device Review",
        },
        {
          name: "Missing Excl. Justification",
          value: "Missing Excl. Justification",
        },
        {
          name: "Incomplete Extraction Fields",
          value: "Incomplete Extraction Fields",
        },
      ],
      statusFilterCompleOptions: [
        {
          name: "Complete SoTa Reviews",
          value: "Complete SoTa Reviews",
        },
        {
          name: "Complete Device Reviews",
          value: "Complete Device Reviews",
        },
      ],
      apprCompleted: [
        {
          name: "COMPLETED_SOTA_REVIEWS",
          displayedName: "Complete SoTa Reviews",
        },
        {
          name: "COMPLETED_DEVICES_REVIEWS",
          displayedName: "Complete Devices Reviews",
        }
      ],
      apprUnCompleted: [
        {
          name: "MISSING_FULL_TEXT_PDF",
          displayedName: "Missing full text pdf/Incomplete",
        },
        {
          name: "FULL_TEXT_UPLOADED",
          displayedName: "Full text uploaded/Ready for Review",
        },
        {
          name: "NEEDS_SUITABILITY",
          displayedName: "Needs Suitability/Outcomes Dropdowns",
        },
        {
          name: "INCOMPLETE_SOTA",
          displayedName: "Incomplete Sota",
        },
        {
          name: "COMPLETED_DEVICES_REVIEWS",
          displayedName: "Incomplete Device Review",
        },
        {
          name: "MISSING_EXCL",
          displayedName: "Missing Excl. Justification",
        },
      ],

      createManualAppraisalForm: {
        title: "",
        abstract: "",
        citation: "",
        pubmed_uid: "",
        pmc_uid: "",
        doi: "",
        databse: "",
        full_text: "",
      },
      isUploadCitaionModalOpen: false,
      isUploadOwnCitationsLoading: false,
      isManualCitationsFromPreviousProjectsLoading: false,
      isRecordsLoading: false,
      dbs: [],
      articleReviews: [],
      uploadOwnCitationsForm: {
        database: '',
        file: null,
        external_db_name: "",
        external_db_url: "",
      },
      runningCitationId: "",
      manualCreationMethod: "",
      selectedReviews: [],
      isCheckAll: false,
      currentArticle: {
        id: null,
        state_symbole: "",
        notes: "",
        exclusionComment: "",
        exclusionReason: "",
        history: [],
        selected: false,
      },
      articles: [],
      reviews: [],
      selectedPrevProject: "",
    }
  },
  computed: {
    dbOptions: function () {
      const dbOptions = this.dbs.map((db) => ({
        name: db.name,
        value: db.name,
      }));
      const defaultOption = { name: "Please select a database", value: null };
      const externalDB = {
        name: "Custom (Not Listed)",
        value: "external",
      }
      return [defaultOption, externalDB, ...dbOptions];
    },
    projectOptions: function () {
      let projectOptions = this.reviews.map((review) => ({
        name: `${review.project.project_name} ${review.device?.name}`,
        value: review.id,
      }));

      // Add the "Select a Previous Project" option at the start
      projectOptions.unshift({
        name: "Select a Previous Project",
        value: ""
      });

      return projectOptions;
    },
    isFilterApplied: function(){
      return this.appliedIsSotaFilter || this.appliedIsSotaFilter === false || this.appliedStatusFilter.length;
    },
  },
  methods: {
    // Helpers
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
    onIsSotaFilterChanged: function(value) {
      this.isSotaFilter = value;
    },
    truncateText(text) {
      return text.length > 30 ? text.slice(0, 30) + '...' : text;
    },
    onNewAppraisalFileChanges(file) {
      this.createManualAppraisalForm.full_text = file;
    },
    onOpenUploadOwnCitationsModal: function () {
      this.isUploadCitaionModalOpen = true;
      this.showModal('upload-own-searches');
    },
    onUploadCitationsDbChanged: function (selectedDatabase) {
      this.uploadOwnCitationsForm.database = selectedDatabase;
    },
    onUploadCitationsFileChanged: function (uploadedFile) {
      this.uploadOwnCitationsForm.file = uploadedFile;
    },
    showLoadingPopup: function () {
      popup = document.getElementById("loading-section");
      popup.style.display = "flex";
      this.hideManualCreationTableSection();
    },
    hideLoadingPopup: function () {
      popup = document.getElementById("loading-section");
      if (popup) popup.style.display = "none";
    },
    showManualCreationTableSection: function () {
      table = document.getElementById("manual-creation-table-section");
      table.style.display = "flex";
    },
    hideManualCreationTableSection: function () {
      table = document.getElementById("manual-creation-table-section");
      if (table) table.style.display = "none";
    },
    onSelectPrevProjectChanged: function (selectedPrevProject) {
      this.selectedPrevProject = selectedPrevProject;
      console.log("selectedPrevProject", this.selectedPrevProject);
      if (this.selectedPrevProject != "") {
        this.articleReviews = []
        // show loader
        this.showLoadingPopup();
        // get prev apparisial for the selceted project
        this.getPrevAppraisalsProjectData();
      }
    },
    collapseMenu: function() {
      this.collapsedInsights = !this.collapsedInsights;
    },
    onUploadOwnCitations: function () {
      // Validation 
      if (!this.uploadOwnCitationsForm.database || !this.uploadOwnCitationsForm.file) {
        this.makeToast("error", "Please provide both fields: a database and upload a file.");
        return;
      }
      if (this.uploadOwnCitationsForm.database === "external" && !this.uploadOwnCitationsForm.external_db_name) {
        this.makeToast("error", "Please provide a name for your external database.");
        return;
      }

      const formData = new FormData();
      formData.append("database", this.uploadOwnCitationsForm.database);
      formData.append("file", this.uploadOwnCitationsForm.file);
      if (this.uploadOwnCitationsForm.database == "external") {
        formData.append("external_db_name", this.uploadOwnCitationsForm.external_db_name);
        formData.append("external_db_url", this.uploadOwnCitationsForm.external_db_url);
      };
      this.isUploadOwnCitationsLoading = true;

      axios.post(uploadCitationsAPI, data = formData)
        .then(
          res => {
            console.log(res);
            this.runningCitationId = res.data.search
            console.log("runningCitationId", this.runningCitationId);
            const TEN_MINUTES = 1000 * 60 * 10;
            this.makeToast("success", `<div style="font-size: 13px; width: 500px;"> 
                    Your file has been processed successfully, and your articles are now being imported. 
                    This process may take a few minutes.
                    Please wait while the deduplication is completed. 
                    Once finished, your articles will appear. 
                    <br />
                    <br />
                    Note that some articles from your uploaded file may be flagged as 
                    duplicates if they already exist in your current list of articles.
                </div>`, expires = TEN_MINUTES);
            this.hideModal("upload-own-searches");
            this.isUploadCitaionModalOpen = false;
            store.setPrismaStatus("RUNNING");
            this.checkRunningCitation();
          },
          err => {
            console.log({ err });
            errorMessage = this.handleErrors(err);
            this.makeToast("error", errorMessage);
            this.hideModal("upload-own-searches");
            this.isUploadCitaionModalOpen = false;
            this.isUploadOwnCitationsLoading = false;
          }
        )
      console.log(this.uploadOwnCitationsForm);
    },
    onApplyFilters: function() {
      this.appliedIsSotaFilter = this.isSotaFilter;
      this.appliedStatusFilter = this.statusFilter;
      this.hideModal("filter-slider");
      this.loadRecords();
    },
    onClearFilters: function() {
      this.appliedIsSotaFilter = null;
      this.appliedStatusFilter = [];
      this.isSotaFilter = null;
      this.statusFilter = [];
      this.searchTerm = "";
      this.loadRecords();
    },
    onTitleSearch: function(e) {
      e.preventDefault();
      this.loadRecords();
    },
    onSortRecords: function(value) {
      if (this.sorting.includes("-")) value.replace("-", "")
      else value = `-${value}`;
      
      this.sorting = value;
      this.loadRecords();
    },

    // Async Actions
    checkRunningCitation: function () {
      const interval = setInterval(function () {
        const postData = { "search_id": this.runningCitationId };
        let axiosConfig = {
          headers: {
            'Content-Type': 'application/json; charset=UTF-8',
          }
        };
        axios({
          method: 'post',
          url: CheckRunningCitationURL,
          headers: axiosConfig,
          data: postData,
        }).then(
          res => {
            if (res.data.is_completed) {
              // this.makeToast("success", `${res.data.literature_search.processed_articles} results were imported successfully!`);
              this.hideModal("upload-own-searches");
              clearInterval(interval);
              console.log("Interval has been cleared");
              this.isUploadOwnCitationsLoading = false;
              this.loadRecords();
            }
          },
          err => {
            console.log({ err });
            if (this.isRunAllAutoSearch) {
              this.isUploadOwnCitationsLoading = false
            }
          }
        );
      }.bind(this), 5000);
    },
    onCreateManualAppraisal(e) {
      e.preventDefault();
      // validate form
      const requiredFields = ["title", "abstract", "database", "pubmed_uid", "pmc_uid"];
      for (let field of requiredFields) {
        if (!this.createManualAppraisalForm[field]) {
          const errorMsg = `This field ${field.replace("_", " ")} is required!`;
          this.makeToast("error", errorMsg);
          return;
        }
      };

      
      const URL = CreateManualAppraisalURL;
      const formData = new FormData(e.target);
      
      this.axiosPost(
        e,
        url = URL,
        isLoadingKey="isManualAppraisalCreationLoading",
        successMsg = "A new appraisal has been created successfully",
        postData = formData,
        callBack = (resData) => {
          this.hideModal("createManualAppraisal");
          this.loadRecords();
        },
      );
    },
    onShowArticleDetails(review) {
      this.currentArticle = {
        id: review.id,
        state_symbole: review.state_symbole,
        notes: review.notes,
        exclusionComment: review.exclusion_comment,
        exclusionReason: review.exclusion_reason,
        history: [],
        selected: true,
      },
        this.showModal('article-details-' + review.id);
    },
    hideArticleDetails(review) {
      this.currentArticle = {
        id: null,
        state_symbole: "",
        notes: "",
        exclusionComment: "",
        exclusionReason: "",
        history: [],
        selected: false,
      };
      this.hideModal('article-details-' + review.id);
    },
    importManualSearch() {
      this.showLoadingPopup()
      this.isManualCitationsFromPreviousProjectsLoading = true;
      const postData = { "article_ids": this.selectedReviews };
      const URL = ImportManualSearchURL;
      axios.post(URL, postData, {
        headers: {
          'Content-Type': 'application/json',
        },
      })
        .then(
          res => {
            console.log(res.data);
            const count = res.data.count;
            this.makeToast("success", `${count} Article Reviews results were imported to the current project`);
            this.hideModal("createManualAppraisal");

            // Reload the page after 2 seconds
            setTimeout(() => {
              this.loadRecords();
            }, 2000);
          },
          err => {
            console.log(err);
            const errMsg = this.handleErrors(err);
            this.makeToast("error", errMsg);
          }
        );
    },
    getAppraisalsData() {
      const URL = appraisalsDataURL;
      axios.get(URL)
        .then(
          res => {
            console.log(res);
            this.isRecordsLoading = false;
            this.dbs = res.data.dbs;
            this.reviews = res.data.lit_reviews;
          },
          err => {
            console.log(err);
            this.isRecordsLoading = false;
          }
        );
    },
    getPrevAppraisalsProjectData() {
      const URL = appraisalsDataURL;
      const postData = new FormData();
      postData.append("selected_prev_project_id", this.selectedPrevProject);
      axios.post(URL, postData, {
        headers: {
          'Content-Type': 'application/json',
        },
      })
        .then(
          res => {
            console.log(res);
            this.isRecordsLoading = false;
            this.articleReviews = res.data.article_reviews;
            console.log("this.articleReviews", this.articleReviews);
            // hide loader
            this.hideLoadingPopup()
            // show the table
            this.showManualCreationTableSection()
          },
          err => {
            console.log(err);
            // hide loader
            this.hideLoadingPopup()
            this.isRecordsLoading = false;
          }
        );
    },
    autoGenerateAllExtractionFields() {
      console.log("Generating AI extractions for all appraisals...");

      const URL = AppraisalAIAllDataURL;

      axios.post(URL, {}, {
        headers: {
          'Content-Type': 'application/json',
        },
      })
        .then(response => {
          console.log("AI Generation task started:", response.data);

          if (response.data.success) {
            // Show success toast with detailed message
            this.makeToast(
              'success',
              'AI extraction processing started successfully. This will run in the background and may take several minutes to complete depending on the number of appraisals.'
            );
          } else {
            this.makeToast('error', response.data.message || 'Error starting AI extraction process.');
          }
        })
        .catch(error => {
          console.error("Error generating AI extractions:", error);

          // Hide loading popup
          this.hideLoadingPopup();

          // Extract error message if available, or use generic fallback
          let errorMessage = 'Error generating AI extractions. Please try again.';
          if (error.response && error.response.data && error.response.data.message) {
            errorMessage = error.response.data.message;
          }

          // Show error toast
          this.makeToast('error', errorMessage);
        });
    },
    createURLParams: function(page=1){
      let URL = `?page_size=${this.pageSize}&page=${page}`;

      if (this.appliedIsSotaFilter){
        URL = `${URL}&filter_is_sota=${this.appliedIsSotaFilter}`;
      };

      if (this.appliedStatusFilter){
        for (let filter of this.appliedStatusFilter)
          URL = `${URL}&filter_status=${filter}`;
      };

      if (this.searchTerm) {
        URL = `${URL}&search_title=${this.searchTerm}`;
      }

      if (this.sorting) {
        URL = `${URL}&sorting=${this.sorting}`;
      }

      return URL;
    },
    loadRecords: function(page=1){
      const URLParams = this.createURLParams(page);
      const URL = `${clinicalAppraisalsListURL}${URLParams}`;

      this.axiosGet(
        url = URL,
        isLoadingKey = "isLoading",
        callBack = (resData) => {
          this.appraisals = resData.results;
          this.appraisalsInsights = resData.insights;
          this.pagination.current = page;
          this.pagination.count = resData.count;
          this.pagination.next = resData.next ? this.pagination.current+1 : null;
          this.pagination.previous = resData.previous ? this.pagination.current-1 : null;
          this.pagination.last =  Math.floor(this.pagination.count/this.pageSize);
          if ((this.pagination.count % this.pageSize) > 0)
            this.pagination.last += 1;
          this.pagination.page_range = [
            this.pagination.current-1, 
            this.pagination.current, 
            this.pagination.current+1,
          ];
          if (this.pagination.current > 2) this.pagination.page_range.splice(0, 0, this.pagination.current-2);
          if (this.pagination.current < this.pagination.last - 2) this.pagination.page_range.push(this.pagination.current+2);

          const currentPageTotalIncriment = this.appraisals.length < this.pageSize ? 
          this.appraisals.length + (this.pagination.current-1) * this.pageSize
          : this.pagination.current * this.pageSize;
          const pageStartFrom = this.pagination.current*this.pageSize-(this.pageSize-1);
          this.tablePageIndicator = `${pageStartFrom}-${currentPageTotalIncriment} Of ${this.pagination.count}`;
          console.log(this.pagination)
        },
      );
    },
  },
  watch: {
    // whenever isCheckAll changes, this function will run
    isCheckAll(newIsCheckAll) {
      if (newIsCheckAll) {
        this.selectedReviews = this.articleReviews.map(review => review.id);
      } else {
        this.selectedReviews = [];
      }
    },
  },
  mounted() {
    this.loadRecords();
    this.isRecordsLoading = true;
    this.getAppraisalsData();
    const timeOut = setTimeout(() => {
      this.styleTooltips();
      return clearTimeout(timeOut);
    }, 2000);
  }
})
