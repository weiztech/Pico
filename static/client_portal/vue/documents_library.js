axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#content',
    delimiters: ["[[","]]"],
    data() {
        return {
            entries: [],
            devices: [],
            projects: [],
            lit_reviews: [],
            isRecordsLoading: false,
            loadingPage: false,
            count: 0,
            page_number: 0,
            last_page_number: 0,
            search_term: "",
            search_term_url: "",
            deviceFilter: "",
            litReviewFilter: "",
            pubDateFilter: "",
            DatePickerFormat: 'yyyy',
            currentEditedArticle: {
                "title": "",
                "citation": "",
                "pub_date": "",
                "full_text": "",
            },
            activeContainer:"manual-articles",
            article: {
                "title":"",
                "abstract":"",
                "citation":"",
                "pubmed_uid":"",
                "pmc_uid":"",
                "pdf_file": null,
                "project":"",
                "type_creation":"",
                "zip_file":null
            },
            currentURL: "",
            currentEditedArticle: {
                "title": "",
                "citation": "",
                "pub_date": "",
                "full_text": "",
            },
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
    },
    watch: {
        // whenever pubDateFilter changes, this function will run
        pubDateFilter(newpubDateFilter, oldpubDateFilter) {
            this.onFilter();
        }
      }, 
    methods : {
        // helpers
        compare: function( a, b, key, type) {
            if ( a[key].toLowerCase() < b[key].toLowerCase() ){
                return type === "ASC" ? -1 : 1;
            }
            if ( a[key].toLowerCase() > b[key].toLowerCase() ){
                return type === "ASC" ? 1 : -1;
            }
            return 0;
        },
        enableElement: function(ele, text=null){
            ele.style.pointerEvents = "auto";
            ele.style.opacity = "1";
            if (text)
                ele.innerHTML  = text;
        },
        disableElement: function(ele, text=null){
            ele.style.pointerEvents = "None";
            ele.style.opacity = ".7";
            if (text)
                ele.innerHTML  = text;
        },
        makeToast(variant = null, title, body) {
            this.$bvToast.toast(body, {
              title: title,
              variant: variant,
              autoHideDelay: 3000,
              solid: true,
              toaster: "b-toaster-top-center",
            })
        },
        handleErrors: function(error){
            const errorMsg = error.response.data;
            let displayableError = "";

            function extractErrorMessages(object){
                for (const key in object) {
                    const argument = object[key];
                    const isObject = typeof argument === "object";
                    const isArray = Array.isArray(argument);

                    if (isObject && !isArray)
                        extractErrorMessages(argument);
                    else if (isArray){
                        const errors = argument.join();
                        displayableError += key === "error message" ? errors : `'${key} Field': ${errors} ,`;
                    } 
                    else
                        displayableError += key === "error message" ? argument :  `'${key} Field': ${argument} ,`;      
                }; 
            };

            try {
                if(error.response.status === 400)
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

            return  displayableError;
        },

        // actions
        onErrorDisplay: function(error_msg){
            const variant = "danger";
            const title = "Search Terms Error";
            this.makeToast(variant, title, error_msg);
        },
        onDeviceFilterChange: function(e){
            this.deviceFilter = e.target.value;
            this.onFilter();
        },
        onLitReviewFilterChange: function(e){
            this.litReviewFilter = e.target.value;
            this.onFilter();
        },
        showEditArticle: function(articleReview){
            this.currentEditedArticle = {
                "id": articleReview.article.id,
                "title": articleReview.article.title,
                "citation": articleReview.article.citation,
                "pub_date": articleReview.article.publication_year,
                "full_text": articleReview.article.full_text,
            }
            this.$refs['update-article-modal'].show();
        },
        changeActiveContainer: function(container_name){
            this.activeContainer = container_name
        },
        onProjectChange: function(event){
            this.article.project = event.target.value;
        },
        onpdfChange: function(){
            this.article.pdf_file = this.$refs.articlePDFFile.files[0]
        },
        onzipChange: function(){
            this.article.zip_file = document.getElementById("article-zip formFile").files[0]
        },
        // Async Actions
        onValidateTerms: function(){
            const termsValidatorBTN = document.getElementById("terms-validator-btn");
            this.disableElement(termsValidatorBTN, "Running Please Wait...");

            axios.post(searchTermsValidatorURL, data={})
            .then(
                res => this.checkValidatorStatus(),
                err => {
                    console.log({err});
                    let error_msg = this.handleErrors(err);
                    this.makeToast("danger", "Search terms validator error", error_msg);
                    this.enableElement(termsValidatorBTN, "Validate Search Terms");
                }
            )
        },
        validateSingleArticleCreation: function(){
            console.log("validate form submitted");
            const articleSingleValidatorBTN = document.getElementById("single-btn-creation");
            this.disableElement(articleSingleValidatorBTN, "Creating Please Wait...");

            this.article.type_creation = "single";
            console.log("article",this.article);
            article = this.article
            if (article.title && article.abstract && article.citation && article.pdf_file && article.pubmed_uid && article.pmc_uid && this.article.project) {
                //send form to url
                axios.post(CreateArticleURL, data=article,{
                    headers: {
                      'Content-Type': 'multipart/form-data'
                    }
                })
                .then(
                    res => {
                        console.log(res);
                        // remove defualt values
                        this.article = {
                            "title":"",
                            "abstract":"",
                            "citation":"",
                            "pubmed_uid":"",
                            "pmc_uid":"",
                            "pdf_file":"",
                            "device":"",
                            "type_creation":"",
                            "zip_file":""
                        }
                        this.$refs.articlePDFFile.value = null
                        let success_msg = "The article has been created successfully."
                        this.makeToast("success", "Add Article Form Success", success_msg);
                        // get data
                        this.isRecordsLoading = true;
                        this.onGetPage(1);
                        // change current conatiner
                        this.changeActiveContainer("manual-articles");
                        this.enableElement(articleSingleValidatorBTN, "Create");
                    },
                    err => {
                        console.log(err);
                        let error_msg = this.handleErrors(err);
                        this.makeToast("danger", "Add Article Form Error", error_msg);
                        this.enableElement(articleSingleValidatorBTN, "Create");
                    }
                )

            }else{
                console.log("form is not valid");
                error_msg = "Please fill all required fields before submitting your form."
                this.makeToast("danger", "Article Form is not Valid", error_msg);
                this.enableElement(articleSingleValidatorBTN, "Create");
            }
        },
        validateBulkArticleCreation: function(){
            console.log("validate form submitted");
            const articleBulkValidatorBTN = document.getElementById("bulk-btn-creation");
            this.disableElement(articleBulkValidatorBTN, "Creating Please Wait...");

            this.article.type_creation = "bulk";
            console.log("article",this.article);
            article = this.article
            if (this.article.zip_file && this.article.project){
                //send form to url
                axios.post(CreateArticleURL, data=this.article,{
                    headers: {
                      'Content-Type': 'multipart/form-data'
                    }
                })
                .then(
                    res => {
                        console.log(res);
                        // remove defualt values
                        this.article.zip_file = ""
                        document.getElementById("article-zip formFile").value = null

                        let success_msg = "The articles have been created successfully."
                        this.makeToast("success", "Create bulk Articles Form Success", success_msg);
                        // get data
                        this.isRecordsLoading = true;
                        this.onGetPage(1);
                        // change current conatiner
                        this.changeActiveContainer("manual-articles");
                        this.enableElement(articleBulkValidatorBTN, "Create");
                    },
                    err => {
                        console.log({err});
                        let error_msg = this.handleErrors(err);
                        this.makeToast("danger", "Add Article Form Error", error_msg);
                        this.enableElement(articleBulkValidatorBTN, "Create");
                    }
                )

            }else{
                console.log("form is not valid");
                error_msg = "Please fill all required fields before submitting your form."
                this.makeToast("danger", "Article Form is not Valid", error_msg);
                this.enableElement(articleBulkValidatorBTN, "Create");
            }
        },
        showEditArticle: function(articleReview){
            this.currentEditedArticle = {
                "id": articleReview.article.id,
                "title": articleReview.article.title,
                "citation": articleReview.article.citation,
                "pub_date": articleReview.article.publication_year,
                "full_text": articleReview.article.full_text,
            }
            this.$refs['update-article-modal'].show();
        },
        hideEditeArticle: function(){
            this.$refs['update-article-modal'].hide();
        },

        // Async Actions
        onGetPage: function(pageNumber){
            // this.isRecordsLoading = true;
            this.loadingPage = true;
            // DocumentsLibraryURL this var de clared inside the django template.
            let URL = `${DocumentsLibraryURL}?page_number=${pageNumber}`;
            if (this.search_term){
                this.search_term_url = this.search_term;
                URL += `&search_term=${this.search_term}`;
            }
            if (this.deviceFilter)
                URL += `&device_filter=${this.deviceFilter}`;
            if (this.litReviewFilter)
                URL += `&lit_review_filter=${this.litReviewFilter}`;
            if (this.pubDateFilter)
                URL += `&year_filter=${this.pubYear}`;
            
            this.currentURL = URL;
            axios.get(URL)
                .then(
                    res => {
                        console.log(res);
                        this.isRecordsLoading = false;
                        this.loadingPage = false;
                        this.entries = res.data.entries;
                        this.count = res.data.count;
                        this.page_number = res.data.page_number;
                        this.last_page_number = res.data.last_page_number;
                    },
                    err => {
                        console.log(err);
                        this.loadingPage = false;
                        this.isRecordsLoading = false;
                    }
                );
        },
        onFilter: function(e){
            if(e) e.preventDefault();
            this.isRecordsLoading = true;
            this.onGetPage(1);
        },
        clearState: function(state){
            this._data[state] = "";
            this.onFilter();
        },
        onUpdateArticleSubmit: function(e){
            e.preventDefault(); 
            const formData = new FormData()

            // hide submit button
            const submitBTN = this.$refs["modal-submit-btn"];
            this.disableElement(submitBTN);

            formData.append('title', this.currentEditedArticle.title);
            formData.append('citation', this.currentEditedArticle.citation);
            formData.append('publication_year', this.currentEditedArticle.pub_date);
            
            const fullTextPDFInput = this.$refs["full-text-pdf"]
            if (fullTextPDFInput.files[0]){
                formData.append('full_text', fullTextPDFInput.files[0]);
            } 

            // updateArticleURL is available under the template
            const URL = updateArticleURL.replace("/0/", `/${this.currentEditedArticle.id}/`)
            axios.patch(URL, formData)
                .then(
                    res => {
                        console.log(res);
                        const newEntries = this.entries.map((item, index) => {
                            if (item.article.id === res.data.id){
                                item.article = res.data;
                               return item;
                            } else 
                                return item;
                        });
                        this.entries = newEntries;

                        const variant = "success";
                        const title = "Article Update";
                        let success_msg = "The article has been updated successfully."

                        this.makeToast(variant, title, success_msg);
                        this.enableElement(submitBTN);
                        this.hideEditeArticle();
                    },
                    err => {
                        console.log(err);
                        const variant = "danger";
                        const title = "Update Article Error";

                        let error_msg = "Error occurred on the following fields: "
                        error_msg += this.handleErrors(err);

                        this.makeToast(variant, title, error_msg);
                        this.enableElement(submitBTN);
                    }
                );
        },
    },
    components: {
        'vuejs-datepicker':vuejsDatepicker
    },
    mounted() {
        this.isRecordsLoading = true;
        // DocumentsLibraryURL this var de clared inside the django template
        axios.get(DocumentsLibraryURL)
            .then(
                res => {
                    console.log(res);
                    this.isRecordsLoading = false;
                    this.entries = res.data.entries;
                    this.count = res.data.count;
                    this.page_number = res.data.page_number;
                    this.last_page_number = res.data.last_page_number;
                    this.devices = res.data.devices;
                    this.projects = res.data.projects;
                    this.lit_reviews = res.data.lit_reviews;
                },
                err => {
                    console.log(err);
                    this.isRecordsLoading = false;
                }
            );
    }
})
