axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#content',
    delimiters: ["[[","]]"],
    data() {
        return {
            isRecordsLoading: false,
            searchId:"",
            reviews: [],
            selectedArticle:"",
            AddCommentForm:false,
            currentComment:"",
            datesFilterValues: [],
            dateFilterSelected: "",
            // whether all searches related to term in a given interval are completed?
            searchStatus: "Pending",
        }
    },


    methods : {
        // helpers
        makeToast(variant = null, title, body) {
            this.$bvToast.toast(body, {
              title: title,
              variant: variant,
              autoHideDelay: 3000,
              solid: true,
              toaster: "b-toaster-top-center",
            })
        },

        selectArticle(articleId) {
            // i want this function to go over this.articles and get me the article with id= articleId
            this.selectedArticle = this.reviews.find(review => review.article.id === articleId).article;
            console.log("this.selectedArticle",this.selectedArticle);
            this.currentComment = ""
            this.AddCommentForm = false
            // open the popup
            this.$refs['update-article-modal'].show();
        },
        hideEditeArticle: function(){
            this.$refs['update-article-modal'].hide();
        },
        showAddCommentForm: function(){
            this.AddCommentForm = !this.AddCommentForm 
        },
        formatDate: function(inputDate) {
            const date = new Date(inputDate);

            // Get the date components
            const day = date.getDate();
            const month = date.getMonth() + 1; // Month is zero-based
            const year = date.getFullYear();

            // Get the time components
            let hours = date.getHours();
            let minutes = date.getMinutes();
            const ampm = hours >= 12 ? 'PM' : 'AM';

            // Convert to 12-hour time format
            let formattedHours = hours % 12 || 12;

            // Add leading zeros to hours and minutes
            formattedHours = String(formattedHours).padStart(2, '0');
            minutes = String(minutes).padStart(2, '0');

            // Pad single-digit day and month with leading zeros
            const formattedDay = String(day).padStart(2, '0');
            const formattedMonth = String(month).padStart(2, '0');

            // Format the date and time as required
            const formattedDate = `${formattedMonth}-${formattedDay}-${year}`;
            const formattedTime = `${formattedHours}:${minutes} ${ampm}`;

            return `${formattedDate} ${formattedTime}`;
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

        // actions
        onErrorDisplay: function(error_msg){
            const variant = "danger";
            const title = "Automated Search Error";
            this.makeToast(variant, title, error_msg);
        },
        addArticleComment: function() {
            const postData = {
                "text" : this.currentComment,
                "article":  this.selectedArticle,
                "search_id": this.searchId,
            }
            axios.post(CreateArticleCommentURL,data=postData, {
                headers: {
                  'Content-Type': 'multipart/form-data', 
                },
            })
            .then(
                  res => {
                        console.log(res.data);
                        this.reviews = this.reviews.map(review => {
                            if (review.article.id === this.selectedArticle.id){
                                const newReview = review;
                                newReview.article = res.data.updated_article;
                                return newReview;
                            } else 
                                return review
                        });
                        this.selectedArticle = this.reviews.find(review => review.article.id === this.selectedArticle.id).article;
                        this.currentComment = ""
                        const variant = "success";
                        const title = "Article Comment Creation";
                        this.makeToast(variant, title, "Your comment has been added successfully.");
                        this.showAddCommentForm()

                  },
                  err => {
                        console.log({err});
                        this.onErrorDisplay({err})
                  }
              )

        },
        onDateFilter: async function(){
            this.isRecordsLoading = true;
            const URL = `${AutomatedSearchResultsURL}?date_filter=${this.dateFilterSelected}`;

            try {
                const res = await axios.get(URL);
                console.log(res);
                this.isRecordsLoading = false;
                this.reviews = res.data.article_reviews;
                this.searchStatus = res.data.search_status;

            } catch (err) {
                console.log(err);
                this.isRecordsLoading = false;
                this.onErrorDisplay({err});
            }
            
        },
        onClearFilterResults: async function(){
            this.dateFilterSelected = "";
            await this.onDateFilter();
        },
        saveArticleToLibrary: function(articleId ,addMethod) {
            const postData = {
                "article_id":  articleId,
                "search_id": this.searchId,
            }
            axios.post(saveArticleToLibraryURL,data=postData, {
                headers: {
                  'Content-Type': 'multipart/form-data', 
                },
            })
            .then(
                  res => {
                        this.reviews = this.reviews.map(review => {
                            if (review.article.id === articleId){
                                const newReview = review;
                                newReview.article = res.data.updated_article;
                                return newReview;
                            } else 
                                return review
                        });
                        // show success message
                        if (!addMethod) {
                            const variant = "success";
                            const title = "Article Save To Library";
                            this.makeToast(variant, title, "Your article has been saved successfully.");
                        } else {
                            // Your code for successful removal
                            const variant = "success";
                            const title = "Article Remove From Library";
                            this.makeToast(variant, title, "Your article has been removed successfully.");
                        }

                  },
                  err => {
                        console.log({err});
                        this.onErrorDisplay({err})
                  }
              )

        },
    },
    mounted() {
        this.isRecordsLoading = true;
        // CreateAutomatedSearchURL this var de clared inside the django template
        axios.get(AutomatedSearchResultsURL)
            .then(
                res => {
                    console.log(res);
                    this.isRecordsLoading = false;
                    this.reviews = res.data.article_reviews;
                    this.searchId = res.data.search_id;
                    this.datesFilterValues = res.data.dates_filter_values_ser;
                    this.searchStatus = res.data.search_status;
                },
                err => {
                    console.log(err);
                    this.isRecordsLoading = false;
                    this.onErrorDisplay({err})
                }
            );
    }
})
