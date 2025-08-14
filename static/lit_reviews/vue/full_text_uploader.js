axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
  el: '#app-full-text-upload',
  delimiters: ["[[", "]]"],
  mixins: [globalMixin],
  data() {
    return {
      isLoadingUpload: false,
      isLoadingRecords: false,
      isLoadingClearing: false,
      articleReviews: [],
      awsS3UploadingFile: null,
      awsS3CurrentKey: null,
      statusSort: new URL(window.location.href).searchParams.get("sort") || "status",
      selectedTab: 'idMatch',  // Default tab
      idMatchLoading: true,
      titleMatchLoading: false,
      idMatchData: [],
      titleMatchData: [],
      currentArticleId: '',
      pdfAttachLoading: false
    }
  },
  computed: {
    uploadedRecords () {
      return this.articleReviews.filter(articleRev => articleRev.full_text_status !== "missing");
    },
    missingRecords () {
      return this.articleReviews.filter(articleRev => articleRev.full_text_status === "missing");
    },
  },
  methods: {
    onSort(value) {
      if (this.sorting === value) {
        if (value.includes("-")) value.replace("-", "") 
        else value = "-"+value;
      }
      this.sorting = value;
      this.loadRecords();
    },
    truncateText(text) {
      return text.length > 30 ? text.slice(0, 30) + '...' : text;
    },
    onRequestHelp() {
      axios.post(SEND_EMAIL_URL, { type: "FULL_TEXT" })
        .then(() => {
          this.$refs['popup-success-message'].show();
          console.log("your message has been send ");
        })
        .catch((err) => {
          this.$refs['popup-error-message'].show();
          console.log("Failed to send support request");
        })
    },

    // File Upload 
    updateArticleReview(newValue){
      this.articleReviews = this.articleReviews.map(review => {
        if (review.id == newValue.id) return newValue;
        return review;
      });
    },
    isValidFileExtension: function (selected_db, fileType) {
      const isValid = fileType === "pdf";
      if (!isValid) this.makeToast("error", "Invalid file format. Please upload a PDF file.");
      return isValid;
    },
    onUploadFile: function (e, articleReview) {
      const file = e.target.files[0];

      this.awsS3UploadingFile = file;
      const fileType = file.name.split('.').pop();

      if (!this.isValidFileExtension("", fileType)) {
        return;
      }

      this.uploadFileToAWSVue(file, fileType, articleReview, "FULL_TEXT_PDF", this.updateArticleReview, this.onAttachUploadedPDF);
    },
    updateIsUploadReadyForArticleReview: function(articleReview) {
      articleReview.isUploadReady = true;
    },
    onClearFile: function(event, article_review) {
      this.awsS3UploadingFile = null;
      const fileElm = document.getElementById(`input-${article_review.id}`);
      fileElm.value = null;

      const dropzone = document.getElementById("drop-zone-" + article_review.id);
      const dropzoneInner = document.getElementById("drop-zone-inner-" + article_review.id);
      const uploadSuccessSection = document.getElementById("upload-success-" + article_review.id);
      const uploadedFileDetailsElm = document.getElementById('file-details-'+ article_review.id);
      const clearIcon = document.getElementById("clear-file-icon-"+ article_review.id)
      const progressElmInner = document.getElementById('progress-inner-'+ article_review.id);
      const preogressPercentageElm =  document.getElementById('progress-percentage-'+ article_review.id);

      clearIcon.style.display = "none";
      dropzone.style.display = "block";
      dropzoneInner.classList.remove("active");
      uploadSuccessSection.style.display = "none";
      uploadedFileDetailsElm.style.display = "none";
      progressElmInner.style.width = "0%";
      preogressPercentageElm.innerHTML = "0%";
    },
    onAttachUploadedPDF(articleReview) {
      const formData = new FormData();

      // input are valid submit request  
      formData.append('article_review', articleReview.id);
      formData.append('aws_file_key', articleReview.toBeUploadedFile.awsKey);
      this.axiosPost(
        null,
        url = UPLOAD_FULL_TEXT_URL,
        isLoadingKey = "isLoadingUpload",
        successMsg = "Your file has been uploaded successfully!",
        postData = formData,
        callBack = (resData) => {
          this.articleReviews = this.articleReviews.map(review => {
            if (review.id === resData.id) return resData;
            return review;
          });
        },
      );
    },
    onClearFullText(articleReview){
      const formData = new FormData();

      // input are valid submit request  
      formData.append('article_review', articleReview.id);
      this.axiosPost(
        event=null,
        url = CLEAR_FULL_TEXT_URL,
        isLoadingKey = "isLoadingClearing",
        successMsg = "Your file has been cleared successfully!",
        postData = formData,
        callBack = (resData) => {
          this.articleReviews = this.articleReviews.map(review => {
            if (review.id === resData.id) return resData;
            return review;
          });
        },
      );
    },

    //
    loadIdMatchData(Method) {
      this.selectedTab = 'idMatch';
      this.idMatchLoading = true;
      const formData = new FormData();
      formData.append("article_id", this.currentArticleId);
      formData.append("match_method", Method);
      console.log("article_id", this.currentArticleId);
      console.log("match_method", Method);

      axios.post(ARTICLE_MATCHES_URL, data = formData)
        .then(
          res => {
            console.log(res);
            this.idMatchData = res.data;
            setTimeout(() => {
              this.styleTooltips();
            }, 1000);
            this.idMatchLoading = false;
          },
          err => {
            console.log({ err });
            errorMessage = this.handleErrors(err);
            this.makeToast("error", errorMessage);
          }
        )
    },
    loadTitleMatchData(Method) {
      this.selectedTab = 'titleMatch';
      this.titleMatchLoading = true;
      const formData = new FormData();
      formData.append("article_id", this.currentArticleId);
      formData.append("match_method", Method);
      console.log("article_id", this.currentArticleId);
      console.log("match_method", Method);

      axios.post(ARTICLE_MATCHES_URL, data = formData)
        .then(
          res => {
            console.log(res);
            this.titleMatchData = res.data;
            setTimeout(() => {
              this.styleTooltips();
            }, 1000);
            this.titleMatchLoading = false;
          },
          err => {
            console.log({ err });
            errorMessage = this.handleErrors(err);
            this.makeToast("error", errorMessage);
            this.titleMatchLoading = false;
          }
        )
    },
    selectTab(tab) {
      this.selectedTab = tab;
      if (tab === 'idMatch' && this.idMatchData.length === 0) {
        this.loadIdMatchData('by_id');
      } else if (tab === 'titleMatch' && this.titleMatchData.length === 0) {
        this.loadTitleMatchData('by_title');
      }
    },
    openSearchPreviousProjectModal(articleId) {
      // empty old data
      this.selectedTab = 'idMatch';
      this.idMatchData = [];
      this.titleMatchData = [];
      this.currentArticleId = articleId
      // Open the modal (assuming it's hidden with CSS)
      this.showModal('search-previous-project-model')
      // Load ID match data by default when the modal is opened
      this.loadIdMatchData("by_id");
    },
    attachPdf(articleId) {
      this.pdfAttachLoading = true
      const formData = new FormData();
      formData.append("current_article_id", this.currentArticleId);
      formData.append("article_id", articleId);
      console.log("current_article_id", this.currentArticleId);
      console.log("article_id", articleId);

      axios.post(ARTICLE_ATTACH_PDF_URL, data = formData)
        .then(
          res => {
            console.log(res);
            console.log("PDF attached successfully:");
            this.makeToast("success", "PDF has been attached successfully");
            setTimeout(() => {
              location.reload(); // Reload the page after a short delay
            }, 2000);
          },
          err => {
            this.pdfAttachLoading = false
            console.log({ err });
            errorMessage = this.handleErrors(err);
            this.makeToast("error", errorMessage);

          }
        )
    },
    loadRecords() {
      let URL = `${UPLOAD_FULL_TEXT_URL}?`;
      if (this.sorting) URL += `sorting=${this.sorting}` 

      this.axiosGet(
        url = URL,
        isLoadingKey = "isLoadingRecords",
        callBack = (resData) => {
          this.articleReviews = resData;
        },
      );
    },
  },
  mounted() {
    this.loadRecords();
  }
})