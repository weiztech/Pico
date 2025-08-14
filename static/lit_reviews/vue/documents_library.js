axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

const initUploadOwnCitationsForm = {
  database: 'embase',
  file: null,
  external_db_name: "",
  external_db_url: "",
};

var app = new Vue({
  el: '#app',
  mixins: [globalMixin],
  components: {
    'drop-down': DropDown,
    'toast': Toast,
    'vuejs-datepicker': vuejsDatepicker,
    'file-uploader': FileUploader,
    // 'page-switcher': PageSwitcher,
    'custom-select': CustomSelect,
    // 'exclude-button-drop-down': ExcludeButtonDropDown,
  },
  delimiters: ["[[", "]]"],
  data() {
    return {
      entries: [],
      devices: [],
      projects: [],
      lit_reviews: [],
      dbs: [],
      selectedDatabases: [],
      selectedCitations: [],
      tags: [],
      tagsOptions: [],
      clients: [],

      // forms
      selectedTag: null,
      isCheckAll: false,
      count: 0,
      isSubmitForm: false,
      page_number: 0,
      last_page_number: 0,
      search_term: "",
      search_term_url: "",
      deviceFilter: "",
      litReviewFilter: "",
      pubDateFilter: "",
      DatePickerFormat: 'yyyy',
      
      newProjectName: "",
      selectedClient: null,

      bulkCreationMethod: "",
      uploadOwnCitationsForm: structuredClone(initUploadOwnCitationsForm),
      currentEditedArticle: {
        "title": "",
        "citation": "",
        "pub_date": "",
        "full_text": "",
        "project": "",
      },
      activeContainer: "manual-articles",
      article: {
        "title": "",
        "abstract": "",
        "citation": "",
        "pubmed_uid": "",
        "pmc_uid": "",
        "pdf_file": null,
        "project": "",
        "type_creation": "",
        "zip_file": null,
        "pub_date": "",
      },
      currentURL: "",
      currentEditedArticle: {
        "title": "",
        "citation": "",
        "pub_date": "",
        "full_text": "",
      },

      // loading
      isCreateArticleModalActive: false,
      isCreatingLitReviewLoading: false,
      isAttachTagLoading: false,
      isRecordsLoading: false,
      isUploadOwnCitationsLoading: false,
      loadingPage: false,

      // pagination
      tablePageIndicator: "",
      pagination: {
        current: 0,
        count: 0,
        next: 0,
        previous: 0,
        last: 0,
        page_range: []
      },

      // Pre-fetching
      nextPageData: null,
      previousPageData: null,
      lastPageData: null,
    }
  },
  computed: {
    // a computed getter
    pubYear() {
      return this.pubDateFilter.getFullYear();
    },
    selectedDeviceName() {
      return this.devices.find(device => device.id === parseInt(this.deviceFilter)).device_name;
    },
    selectedLitReviewName() {
      return this.lit_reviews.find(review => review.id === parseInt(this.litReviewFilter)).name;
    },
    isFiltersApplied() {
      return this.deviceFilter || this.litReviewFilter || this.pubDateFilter || this.selectedDatabases.length;
    },
    dbOptions: function() {
      let dbsOps = this.dbs.map((db) => ({
        name: db.name,
        value: db.name,
      }));
      dbsOps = [...dbsOps, {
        name: "Custom (Not Listed)",
        value: "external",
      }];

      return dbsOps; 
    },
  },
  watch: {
    // whenever isCheckAll changes, this function will run
    isCheckAll(newIsCheckAll, oldIsCheckAll) {
      if (newIsCheckAll) {
        const allEntries = this.entries.map(entry => entry.article.id);
        this.selectedCitations = allEntries;
      } else {
        this.selectedCitations = [];
      }
    },
    tags(newVal, oldVal) {
      this.tagsOptions = this.tags.map(tag => ({value: tag.id, name: tag.name, color: tag.color}));
    },
  },
  methods: {
    // helpers
    compare: function (a, b, key, type) {
      if (a[key].toLowerCase() < b[key].toLowerCase()) {
        return type === "ASC" ? -1 : 1;
      }
      if (a[key].toLowerCase() > b[key].toLowerCase()) {
        return type === "ASC" ? 1 : -1;
      }
      return 0;
    },
    truncateText(text) {
      return text.length > 100 ? text.slice(0, 100) + '...' : text;
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
    handleErrors: function (error) {
      const errorMsg = error.response.data;
      let displayableError = "";

      function extractErrorMessages(object) {
        for (const key in object) {
          const argument = object[key];
          const isObject = typeof argument === "object";
          const isArray = Array.isArray(argument);

          if (isObject && !isArray)
            extractErrorMessages(argument);
          else if (isArray) {
            const errors = argument.join();
            displayableError += key === "error message" ? errors : `'${key} Field': ${errors} ,`;
          }
          else
            displayableError += key === "error message" ? argument : `'${key} Field': ${argument} ,`;
        };
      };

      try {
        if (error.response.status === 400)
          extractErrorMessages(errorMsg);
        else if (error.response.data.detail)
          displayableError = error.response.data.detail;
        else
          displayableError = "Server Error, To Get instant help from our team Please submit a ticket Here: https://share.hsforms.com/1jqB4CJx9RxyvGL3qQYo2rgcq0hk .";
      } catch {
        displayableError = "Server Error, To Get instant help from our team Please submit a ticket Here: https://share.hsforms.com/1jqB4CJx9RxyvGL3qQYo2rgcq0hk .";
      }

      if (displayableError.includes("non_field_errors:"))
        displayableError = displayableError.replace("non_field_errors:", "");

      return displayableError;
    },

    // actions
    onSelectedTagChange(newTag) {
      this.selectedTag = newTag;
    },
    onClearFilters() {
      this.search_term = ""
      this.pubDateFilter = ""
      this.litReviewFilter = ""
      this.deviceFilter = ""
      this.selectedDatabases = [];

      this.onFilter();
    },
    onErrorDisplay: function (error_msg) {
      const variant = "danger";
      const title = "Search Terms Error";
      this.makeToast(variant, error_msg);
    },
    onDeviceFilterChange: function (e) {
      this.deviceFilter = e.target.value;
      this.onFilter();
    },
    onLitReviewFilterChange: function (e) {
      this.litReviewFilter = e.target.value;
      this.onFilter();
    },
    onUploadCitationsDbChanged: function(selectedDatabase) {
      this.uploadOwnCitationsForm.database = selectedDatabase;
    },
    onUploadCitationsFileChanged: function(uploadedFile) {
      this.uploadOwnCitationsForm.file = uploadedFile;
    },
    onProjectChange: function (event) {
      this.article.project = event.target.value;
    },
    onpdfChange: function (uploadedFile) {
      this.article.pdf_file = uploadedFile
      // this.article.pdf_file = this.$refs.articlePDFFile.files[0]
    },
    onzipChange: function (uploadedFile) {
      this.article.zip_file = uploadedFile
      // this.article.zip_file = document.getElementById("article-zip formFile").files[0]
    },
    onCurrentEditedArticlePdfChange: function (uploadedFile) {
      this.currentEditedArticle.full_text = uploadedFile
      // this.article.zip_file = document.getElementById("article-zip formFile").files[0]
    },

    // Async Actions
    onValidateTerms: function () {
      const termsValidatorBTN = document.getElementById("terms-validator-btn");
      this.disableElement(termsValidatorBTN, "Running Please Wait...");

      axios.post(searchTermsValidatorURL, data = {})
        .then(
          res => this.checkValidatorStatus(),
          err => {
            console.log({ err });
            let error_msg = this.handleErrors(err);
            this.makeToast("danger", error_msg);
            this.enableElement(termsValidatorBTN, "Validate Search Terms");
          }
        )
    },
    validateSingleArticleCreation: function () {
      this.article.type_creation = "single";
      const article = this.article;

      if (article.title && article.abstract && article.citation && article.pubmed_uid && article.pmc_uid && this.article.project) {
        //send form to url
        this.isSubmitForm = true
        axios.post(CreateArticleURL, data = article, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
          .then(
            res => {
              console.log(res);
              const newEntries = this.entries;
              newEntries.splice(0, 0, res.data);
              this.entries = newEntries;

              this.isSubmitForm = false
              // remove defualt values
              this.article = {
                "title": "",
                "abstract": "",
                "citation": "",
                "pubmed_uid": "",
                "pmc_uid": "",
                "pdf_file": "",
                "device": "",
                "type_creation": "",
                "zip_file": ""
              }
              let success_msg = "The article has been created successfuly"
              this.makeToast("success", success_msg);
              this.hideModal('create-article-modal');
              this.isCreateArticleModalActive = false;
            },
            err => {
              console.log(err);
              this.isSubmitForm = false
              let error_msg = this.handleErrors(err);
              this.makeToast("danger", error_msg);
            }
          )

      } else {
        console.log("form is not valid");
        error_msg = "Please fill all required fill before submitting your form"
        this.makeToast("danger", error_msg);
        // this.enableElement(articleSingleValidatorBTN, "Create");
      }
    },
    validateBulkArticleCreation: function () {
      this.article.type_creation = "bulk";
      const article = this.article;

      if (this.article.zip_file && this.article.project) {
        //send form to url
        this.isSubmitForm = true
        axios.post(CreateArticleURL, data = this.article, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
          .then(
            res => {
              console.log(res);
              this.isSubmitForm = false
              // remove defualt values
              this.article.zip_file = ""

              let success_msg = "The articles has been created successfuly"
              this.makeToast("success", success_msg);
              // get data
              this.isRecordsLoading = true;
              this.onGetPage(this.last_page_number);
              this.hideModal('create-bulk-article-modal')
            },
            err => {
              console.log({ err });
              this.isSubmitForm = false
              let error_msg = this.handleErrors(err);
              this.makeToast("danger", error_msg);
            }
          )

      } else {
        console.log("form is not valid");
        error_msg = "Please fill all required fill before submitting your form"
        this.makeToast("danger", error_msg);
      }
    },
    showCreateArticle: function () {
      this.showModal('create-article-modal');
      this.isCreateArticleModalActive = true;
    },
    showEditArticle: function (articleReview) {
      this.currentEditedArticle = {
        "id": articleReview.article.id,
        "title": articleReview.article.title,
        "citation": articleReview.article.citation,
        "pub_date": articleReview.article.publication_year,
        "full_text": articleReview.article.full_text,
        "project": articleReview.article.project,
      }
      this.showModal('update-article-modal')
    },
    initCurrentEditArticle: function () {
      this.currentEditedArticle = {
        "id": "",
        "title": "",
        "citation": "",
        "pub_date": "",
        "full_text": "",
        "project": "",
      }
    },
    constructFetchURL: function(pageNumber=1) {
      // DocumentsLibraryURL this var de clared inside the django template.
      let URL = `${DocumentsLibraryURL}?page_number=${pageNumber}`;
      if (this.search_term) {
        this.search_term_url = this.search_term;
        URL += `&search_term=${this.search_term}`;
      }
      if (this.deviceFilter)
        URL += `&device_filter=${this.deviceFilter}`;
      if (this.litReviewFilter)
        URL += `&lit_review_filter=${this.litReviewFilter}`;
      if (this.pubDateFilter)
        URL += `&year_filter=${this.pubYear}`;

      if (this.selectedDatabases.length) {
        const dbs = this.selectedDatabases.join(",")
        if (URL.includes("?"))
          URL = `${URL}&db=${dbs}`;
        else
          URL = `${URL}?db=${dbs}`;
      };

      return URL;
    },

    // Async Actions
    onGetPage: function (pageNumber) {
      // check if this page was prefetched first
      if (pageNumber === this.pagination.current+1 && this.nextPageData) {
        this.entries = this.nextPageData.entries;
        this.updatePaginationDetails(this.nextPageData, pageNumber);
        window.scrollTo({top: 0, behavior: 'smooth'});
        this.preFetch();
        return;
      } else if (pageNumber === this.pagination.current-1 && this.previousPageData) {
        this.entries = this.previousPageData.entries;
        this.updatePaginationDetails(this.previousPageData, pageNumber);  
        window.scrollTo({top: 0, behavior: 'smooth'});  
        this.preFetch();    
        return;
      } else if (pageNumber === this.pagination.last) {
        this.entries = this.lastPageData.entries;
        this.updatePaginationDetails(this.lastPageData, pageNumber);  
        window.scrollTo({top: 0, behavior: 'smooth'}); 
        this.preFetch();     
        return;
      }

      // this.isRecordsLoading = true;
      this.loadingPage = true;
      const URL = this.constructFetchURL(pageNumber);

      this.currentURL = URL;
      axios.get(URL)
        .then(
          res => {
            console.log('data', res);
            this.isRecordsLoading = false;
            this.loadingPage = false;
            this.entries = res.data.entries;
            this.count = res.data.count;
            this.updatePaginationDetails(res.data, pageNumber);
            this.hideModal("filters-slider");
            this.preFetch();
            window.scrollTo({top: 0, behavior: 'smooth'});
          },
          err => {
            console.log(err);
            this.loadingPage = false;
            this.isRecordsLoading = false;
          }
        );
    },
    onFilter: function (e) {
      if(e) e.preventDefault();
      this.isRecordsLoading = true;
      this.onGetPage(1);
    },
    clearState: function (state) {
      this._data[state] = "";
      this.onFilter();
    },
    updatePaginationDetails: function (data, page = 1) {
      this.pagination.current = page;
      this.pagination.count = data.count;
      // this.pagination.next = data.next;
      // this.pagination.previous = data.previous;
      this.pagination.last = Math.floor(this.pagination.count / 50);
      if ((this.pagination.count % 50) > 0)
        this.pagination.last += 1;
      this.pagination.page_range = [
        this.pagination.current - 1,
        this.pagination.current,
        this.pagination.current + 1
      ];
      const currentPageTotalIncriment = this.entries.length < 50 ?
        this.entries.length + (this.pagination.current - 1) * 50
        : this.pagination.current * 50
      this.tablePageIndicator = `${this.pagination.current * 50 - 49}-${currentPageTotalIncriment} Of ${this.pagination.count}`;
    },
    onAttachTag: function(event){
      const postData = {
        tag: this.selectedTag,
        articles: this.selectedCitations,
      };

      const successCallBack = () => {
        this.hideModal("attach-tags-modal");
        this.loadEntries();
      }

      this.axiosPost(
          event,
          url=AttachTagURL,
          isLoadingKey="isAttachTagLoading",
          successMsg="the tag was attached to the selected articles successfully",
          postData,
          callBack=successCallBack,
      );
    },
    onUploadOwnCitations: function() {
      const formData = new FormData();
      // Validation 
      if (!this.uploadOwnCitationsForm.database || !this.uploadOwnCitationsForm.file) {
        this.makeToast("error", "Please provide both fields a database and upload a file");
        return;
      }
      if (this.uploadOwnCitationsForm.database === "external" && !this.uploadOwnCitationsForm.external_db_name) {
        this.makeToast("error", "Please provide a name for your external database");
        return;
      }
      // get selected project 
      const selectedProjectID = document.getElementById("ris-article-project").value;
      const selectedProject = this.projects.find(p => p.id === Number(selectedProjectID));
      if (!selectedProject) {
        this.makeToast("error", "Please select a project");
        return;
      }

      formData.append("database", this.uploadOwnCitationsForm.database);
      formData.append("file", this.uploadOwnCitationsForm.file);
      if (this.uploadOwnCitationsForm.database == "external") {
        formData.append("external_db_name", this.uploadOwnCitationsForm.external_db_name);
        formData.append("external_db_url", this.uploadOwnCitationsForm.external_db_url);
      }
      this.isUploadOwnCitationsLoading = true;
      const URL = uploadCitationsAPI.replace("/0/", `/${selectedProject.lit_review}/`)

      axios.post(URL, data=formData)
      .then(
        res => {
          this.makeToast("success", `Your file has been processed successfully and ${res.data.imported_articles} results were imported!`);
          this.hideModal("create-bulk-article-modal");
          this.isUploadOwnCitationsLoading = false;
          this.uploadOwnCitationsForm = structuredClone(initUploadOwnCitationsForm);
          this.bulkCreationMethod = "";
          this.loadEntries();
        },
        err => {
          console.log({err});
          errorMessage = this.handleErrors(err);
          this.makeToast("error", errorMessage);
          this.hideModal("create-bulk-article-modal");
          this.isUploadOwnCitationsLoading = false;
        }
      )
      console.log(this.uploadOwnCitationsForm);
    },
    onCreateLitReview: function(event){
      const client = clientID ? clientID : this.selectedClient;

      const projectData = {
        project_name: this.newProjectName, 
        type: "lit_review", 
        client: client,
      };

      const postData = {
        tag: this.selectedTag,
        project: projectData,
        client: client,
        review_type: "SIMPLE",
      };

      const successCallBack = (resData) => {
        this.hideModal("create-literature-review-modal");
        window.location = `/literature_reviews/${resData.id}/`;
      }

      this.axiosPost(
          event,
          url=CreateLitReviewURL,
          isLoadingKey="isCreatingLitReviewLoading",
          successMsg="Your project has been created successfully",
          postData,
          callBack=successCallBack,
      );
    },
    onUpdateArticleSubmit: function (e) {
      e.preventDefault();
      console.log(this.currentEditedArticle)

      const formData = new FormData()

      formData.append('title', this.currentEditedArticle.title);
      formData.append('citation', this.currentEditedArticle.citation);
      formData.append('publication_year', this.currentEditedArticle.pub_date);
      formData.append('project', this.currentEditedArticle.project);

      if (this.currentEditedArticle.full_text instanceof File) {
        formData.append('full_text', this.currentEditedArticle.full_text);
      }

      this.isSubmitForm = true
      // updateArticleURL is available under the template
      const URL = updateArticleURL.replace("/0/", `/${this.currentEditedArticle.id}/`)
      axios.patch(URL, formData)
        .then(
          res => {
            this.isSubmitForm = false
            console.log(res);
            const newEntries = this.entries.map((item, index) => {
              if (item.article.id === res.data.article.id) return res.data;
              return item;
            });
            this.initCurrentEditArticle()
            this.entries = newEntries;
            this.makeToast("success", "The Article has been updated successfully");
            this.hideModal("update-article-modal");
          },
          err => {
            console.log(err);
            this.isSubmitForm = false
            let error_msg = "error occured on the following fields: "
            error_msg += this.handleErrors(err);
            this.makeToast("error", error_msg);
          }
        );
    },
    loadEntries: function(){
      this.isRecordsLoading = true;
      this.loadingPage = true
      // DocumentsLibraryURL this var de clared inside the django template
      axios.get(DocumentsLibraryURL)
        .then(
          res => {
            console.log(res);
            this.isRecordsLoading = false;
            this.entries = res.data.entries;
            this.updatePaginationDetails(res.data, 1);
            this.count = res.data.count;
            this.loadingPage = false;
            this.preFetch();
          },
          err => {
            console.log(err);
            this.loadingPage = false
            this.isRecordsLoading = false;
          }
        );
    },
    loadFilterData: function(){
      axios.get(LibraryEntryFiltersURL)
        .then(
          res => {
            this.tags = res.data.tags;
            this.devices = res.data.devices;
            this.projects = res.data.projects;
            this.lit_reviews = res.data.lit_reviews;
          },
          err => {
            console.log(err);
          }
        );
    },
    preFetch() {
      // prefetch next page data
      if (this.pagination.current+1 <= this.pagination.last) {
        const URL = this.constructFetchURL(this.pagination.current+1);
        axios.get(URL)
        .then(
          res => {
            this.nextPageData = res.data;
          },
          err => {
            console.log(err);
            this.nextPageData = null;
          }
        );
      };

      // prefetch previous page data
      if (this.pagination.current-1 > 0) {
        const URL = this.constructFetchURL(this.pagination.current-1);
        axios.get(URL)
        .then(
          res => {
            this.previousPageData = res.data;
          },
          err => {
            console.log(err);
            this.previousPageData = null;
          }
        );
      };

      // prefetch last page data
      if (this.pagination.last) {
        const URL = this.constructFetchURL(this.pagination.last);
        axios.get(URL)
        .then(
          res => {
            this.lastPageData = res.data;
          },
          err => {
            console.log(err);
            this.lastPageData = null;
          }
        );
      };
    },
    loadClients() {
      // load Clients
      axios.get(ClientsListAPI)
        .then(
          res => {
            console.log(res);
            this.clients = res.data;
            this.selectedClient = res.data[0].id;
          },
          err => {
            console.log(err);
          }
        );
    },
  },

  mounted() {
    this.loadEntries();
    this.loadDatabases();
    this.loadFilterData();
    if (!clientID) this.loadClients();
  }
})
