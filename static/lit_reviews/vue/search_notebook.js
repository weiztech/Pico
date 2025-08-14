axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
  el: '#search-notebook',
  mixins: [globalMixin],
  components: {
    'drop-down': DropDown,
    'toast': Toast,
    'custom-select': CustomSelect,
  },
  delimiters: ["[[", "]]"],
  data() {
    return {
      isRecordsLoading:true,
      isArchiving: false,
      isUpdating: false,
      isArchivedShown: false,
      isSeachResultsLoading: false,
      isBulkUpdateLoading: false,
      isCreatingLitReviewLoading: false,

      notebookReview: null,
      searchText: "",
      selectedDatabase: null,
      startDate: null,
      endDate: null,
      dbs: [],
      clients: [],
      resultGenerating:false,
      searchResulsLoading: false,
      searchHide:false,
      searchTerm:"",
      articles:[],
      selectedReviews: [],
      searchesHistory:[],
      selectedSearchId: null,
      articlesReviews:[],
      showedSearchesIds:[],
      sort: "article__id",
      appliedSort: "article__id",
      sortOptions: [
        {name: "ID", value: "article__id"},
        {name: "Title", value: "article__title"},
      ],
      sortingDirection: "Ascending",
      sortingDirectionOptions: [
        {name: "Ascending", value: "Ascending"},
        {name: "Descending", value: "Descending"},
      ],
      bulkArticle: {
        notes: "",
        tag: null,
      },
      
      newProjectName: "",
      selectedClient: "",
      selectedTag: "",

      // filters
      selectedTags: [],

      selectedDatabases: [],
      articleTags: [],
      selectedStartDate: "",
      selectedEndDate: "",

      collapse: false
    };
  },
  computed: {
    hasSelectedArticles() {
      return this.selectedArticles.length > 0;
    },
    dbOptions: function() {
      let dbsOps = this.dbs.map((db) => ({
        name: db.name,
        value: db.entrez_enum,
      }));

      return dbsOps; 
    },
    isCurrentSearchUpdated() {
      const selectedSearch = this.searchesHistory.find(s => s.id == this.selectedSearchId);

      if (selectedSearch) 
        return ( 
          this.searchText !== selectedSearch.term
          || this.selectedDatabase !== selectedSearch.db.entrez_enum
          || this.startDate !== selectedSearch.start_search_interval
          || this.endDate !== selectedSearch.end_search_interval
        )
      else
        return false;
    },
    articleTagsOptions() {
      let tagsOptions =  this.articleTags.map(tag => ({
          name: tag.name,
          value: tag.id,
          color: tag.color,
        })
      );
      tagsOptions = [{
        name: "Attach Tag",
        value: "",
      }, ...tagsOptions];
      return tagsOptions;
    },
    isSearchParametersValid() {
      return (
        this.searchText &&        
        this.selectedDatabase && 
        this.startDate &&         
        this.endDate             
      );
    },
    isFiltersApplied() {
      return this.selectedDatabases.length || this.selectedTags.length || this.selectedStartDate || this.selectedEndDate;
    },
    selectedSearch(){
      return this.searchesHistory.find(search => search.id === this.selectedSearchId);
    },
    isCheckAll() {
      return this.selectedReviews.length === this.articlesReviews.length;
    }
  },
  methods: {
    toogleIsCheckAll: function(){
      if (this.selectedReviews.length === this.articlesReviews.length) this.selectedReviews = [];
      else this.selectedReviews = this.articlesReviews.map(review => review.id);
    },
    collapseMenu(){
      console.log("collapse before",this.collapse);
      
      this.collapse = !this.collapse
      console.log("collapse after",this.collapse);
    },
    filterTagStyle(tag) {
      if (this.selectedTags.includes(tag.name)){
        let rgbaColor = this.hexToRgba(tag.color, 0.2);
        return `background-color: ${rgbaColor}; width: max-content; color: ${tag.color}; border: 1px solid ${tag.color}; padding: 8px 12px;`;
      }else{
        return `width: max-content; color: ${tag.color}; border: 1px solid ${tag.color}; padding: 8px 12px;`;
      }
    },
    toggleTag(tag) {
      const index = this.selectedTags.indexOf(tag);
      if (index > -1){
        this.selectedTags.splice(index, 1);
      } else {
        this.selectedTags.push(tag)
      }
    },
    applyURLFilters: function(URL) {
      if (this.searchTerm) {
        if (URL.includes("?"))
          URL =  `${URL}&search=${this.searchTerm}`;
        else
          URL =  `${URL}?search=${this.searchTerm}`;
      };

      if (this.selectedTags.length) {
        const tags = this.selectedTags.join(",")
        if (URL.includes("?"))
          URL =  `${URL}&tag=${tags}`;
        else
          URL =  `${URL}?tag=${tags}`;
      };

      if (this.selectedDatabases.length) {
        const dbs = this.selectedDatabases.join(",")
        if (URL.includes("?"))
          URL =  `${URL}&db=${dbs}`;
        else
          URL =  `${URL}?db=${dbs}`;
      };

      if (this.selectedStartDate) {
        if (URL.includes("?"))
          URL =  `${URL}&start_date=${this.selectedStartDate}`;
        else
          URL =  `${URL}?start_date=${this.selectedStartDate}`;
      };

      if (this.selectedEndDate) {
        if (URL.includes("?"))
          URL =  `${URL}&end_date=${this.selectedEndDate}`;
        else
          URL =  `${URL}?end_date=${this.selectedEndDate}`;
      };

      return URL;
    },
    onClearFilters() {
      this.selectedTags = [];
      this.searchTerm = "";
      this.selectedDatabases = [];
      this.selectedStartDate = "";
      this.selectedEndDate = "";
      this.updateSearchResults();
    },
    onApplyFilters: function(event){
      event.preventDefault();
      this.updateSearchResults();
    },
    onSelectedTagChange: function(newTag){
      this.bulkArticle.tag = newTag;
      this.selectedTag = newTag;
    },
    selectSearch(id) {
      // unselected previously selected one;
      this.onUnselectSearch(this.selectedSearchId);
      this.selectedSearchId = id;
      this.updateSearchResults(id);

      const search = this.searchesHistory.find(search => search.id === id);
      this.resultGenerating = true
      this.searchText = search.term
      this.selectedDatabase = search.db.entrez_enum
      this.startDate = search.start_search_interval
      this.endDate = search.end_search_interval
    },
    onUnselectSearch(id) {
      this.selectedSearchId = null;
      this.updateSearchResults(id);
      const search = this.searchesHistory.find(search => search.id === id);
      this.searchText= "";
      this.selectedDatabase = null;
      this.startDate = null;
      this.endDate = null;
    },
    onShowArchived() {
      this.isArchivedShown = !this.isArchivedShown;
    },
    toggleSearchVisibility(searchId) {
      this.resultGenerating = true
      this.updateSearchResults(searchId)
    },
    clearAllSelectedSearches: function() {
      this.selectedSearchId = null;
      this.articlesReviews = [];
      this.showedSearchesIds = [];
      this.searchText= "";
      this.selectedDatabase = null;
      this.startDate = null;
      this.endDate = null;
    },
    onToggleSortingDropDown() {
      this.$refs["sorting-dropdown"].classList.toggle("active");
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
      this.loadSearches();
    },
    formatDjangoDate(djangoDateStr) {
      const date = new Date(djangoDateStr);
      const timeOptions = { hour: 'numeric', minute: 'numeric', hour12: true };
      const dateOptions = { year: 'numeric', month: 'short', day: 'numeric' };
      const formattedTime = new Intl.DateTimeFormat('en-US', timeOptions).format(date);
      const formattedDate = new Intl.DateTimeFormat('en-US', dateOptions).format(date);
      return `${formattedTime} / ${formattedDate}`;
    },
    truncateText(text,caracterNumber) {
      return text.length > caracterNumber ? text.slice(0, caracterNumber) + '...' : text; 
    },
    // Actions
    onCloseFilters() {
      this.hideModal('filters-slider');
    },
    sortBy(sorting){
      if (sorting == "article__title"){
        if (this.sort === "article__title"){
          this.sort = "-article__title";
        }else {
          this.sort = "article__title";
        }
      }else if (sorting=="id") {
        if (this.sort === "id"){
          this.sort = "-id";
        }else {
          this.sort = "id";
        }
      }
      // this.loadArticles(false, 1);
    },
    archiveSelectedSearch() {
      // archive Selected Search
      console.log("Selected Search has been archived");
      
    },
    createNewSearch() {
      this.selectedSearchId= ""
      this.resultGenerating = false
      this.showedSearchesIds = []

      this.searchText= ""
      this.selectedDatabase= null
      this.startDate= null
      this.endDate= null
    },
    onDatabaseChange(selectedValue) {      
      this.selectedDatabase = selectedValue; // Update selected database
    },
    hideSearchSection() {
      this.searchHide = !this.searchHide;
      console.log('Search section toggled:', this.searchHide);
    },
    newSearch() {
      if (new Date(this.endDate) <= new Date(this.startDate)) {
        this.makeToast("danger", "End date must be later than start date.");
      }else{
        const formData = {
          term: this.searchText,
          db: this.selectedDatabase,
          start_search_interval: this.startDate,
          end_search_interval: this.endDate,
        }
        this.clearAllSelectedSearches();
        this.isRecordsLoading = true;

        axios.post(notebookSearchAPI, data = formData)
        .then(
          res => {
            console.log(res.data.notebook_search.id);
            newSearch = res.data.notebook_search
            this.searchesHistory.unshift(newSearch);
            this.selectedSearchId = res.data.notebook_search.id
            this.resultGenerating = true;
            this.isRecordsLoading = false;
            this.checkSearchStatus(newSearch);
          },
          err => {
            console.log(err);
            this.isRecordsLoading = false;
          }
        );
      }
    },
    checkSearchStatus: function(litSearch){
      `
      Check The Running Searches Status and update their status once completed;
      `
      this.searchResulsLoading = true;
      this.selectSearch(litSearch.id);
      const interval = setInterval(async function() {
        const URL = CheckStatusURL.replace("/0/", `/${this.notebookReview.id}/`);
        const postData = { "search_id": litSearch.id };
        let axiosConfig = {
          headers: {
            'Content-Type': 'application/json; charset=UTF-8',
          }
        };
        const res = await axios({
          method: 'post',
          url: URL,
          headers: axiosConfig,
          data: postData,
        });
        console.log(res.data);
        if (res.data.is_completed) {
          clearInterval(interval);
          this.searchResulsLoading = false;
          this.loadSearches(this.selectedSearchId);
        };
      }.bind(this), 5000);
    },
    onCreateLitReview: function(event){
      const client = clientID ? clientID : this.selectedClient;

      const projectData = {
        project_name: this.newProjectName, 
        type: "lit_review", 
        client: client,
      };

      const postData = {
        review_tag: this.selectedTag,
        project: projectData,
        client: client,
        review_type: "SIMPLE",
        lit_review_id: this.notebookReview.id,
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
    onArchiveSearch: function(event, search){
      event.stopPropagation();
      const URL = updateLiteratureSearchView.replace("/0/", `/${search.id}/`);
      const data = {"is_archived": search.is_archived ? false : true};

      this.axiosPatch(
          event=event, 
          url=URL, 
          isLoadingKey="isArchiving", 
          successMsg=`The search has been ${search.is_archived?'unarchived':'archived'} successfully!`,
          postData=data,
          callBack= (responseData) => {
            this.searchesHistory = this.searchesHistory.map((item) =>  {
              if (item.id === responseData.id) {
                return responseData;
              } else return item
            });
            console.log(this.searchesHistory)

            // unselected the search if it's selected
            if (responseData.is_archived && this.selectedSearchId === responseData.id) {
              this.onUnselectSearch(responseData.id);
            }
          },
      );
    },
    onSaveToLibrary: function(event, articleReview){
      const URL = SaveToLibraryURL.replace("/0/", `/${articleReview.article.id}/`);
      const isSaved = articleReview.article.is_added_to_library;
      const data = {
        "article_review_id": articleReview.id,
        "is_added_to_library": isSaved ? false : true,
      };

      this.axiosPatch(
          event=event, 
          url=URL, 
          isLoadingKey="isUpdating", 
          successMsg=`The article has been ${isSaved?'removed':'saved'} to your library successfully!`,
          postData=data,
          callBack= (responseData) => {
            this.articlesReviews = this.articlesReviews.map(articleR => {
              if (articleR.id === responseData.id) {
                return responseData;
              } else return articleR;
            })
          },
      );
    },
    onBulkSaveToLibrary: function(event) {
      const data = {
        "article_review_ids": this.selectedReviews,
        "is_added_to_library": true,
      };

      this.axiosPost(
          event=event, 
          url=BulkSaveToLibraryURL, 
          isLoadingKey="isBulkUpdateLoading", 
          successMsg=`The selected articles has been saved to your library successfully!`,
          postData=data,
          callBack= (responseData) => {
            this.selectedReviews = [];
            this.isBulkUpdateLoading = false;
            this.articlesReviews = this.articlesReviews.map(review => {
              const updatedReview = responseData.find(upReview => upReview.id === review.id);
              if (updatedReview) return updatedReview;
              else return review;
            })
          },
      );

    },
    onAddArticleNote(event, review) {
      event.preventDefault();
      const values = {notes: review.notes}
      this.onUpdateReview(event, review.id, values);
    },
    onUpdateReview(event, articleReviewID, values) {
      // Values that can be updates : notes, tags

      // update the url lit review id and article review id query parameters
      const URL = ArticleReviewUpdateAPI.replace("/1/", `/${this.notebookReview.id}/`).replace("/0/", `/${articleReviewID}/`);
      this.axiosPatch(
        event=event, 
        url=URL, 
        isLoadingKey="isUpdating", 
        successMsg=`The article has been updated successfully!`,
        postData=values,
        callBack = (responseData) => {
          this.articlesReviews = this.articlesReviews.map(articleR => {
            if (articleR.id === responseData.id) {
              return responseData;
            } else return articleR;
          });
          this.hideModal('add-note-modal-'+responseData.id)
        },
      );
    },
    onBulkStateUpdate(e) {
      e.preventDefault();
      const values = {
        review_ids: this.selectedReviews,
        notes: this.bulkArticle.notes,
        tag: this.bulkArticle.tag,
      };
      this.isBulkUpdateLoading = true;
      const URL = bulkStateUpdateAPI.replace("/0/", `/${this.notebookReview.id}/`);

      axios.post(URL, data=values)
        .then(
          res => {
            this.makeToast("success", "Selected articles were updated successfully.");
            this.selectedReviews = [];
            this.isBulkUpdateLoading = false;
            this.articlesReviews = this.articlesReviews.map(review => {
              const updatedReview = res.data.updated_reviews.find(upReview => upReview.id === review.id);
              if (updatedReview) return updatedReview;
              else return review;
            });
            this.bulkArticle = {
              notes: "",
              tag: null,
            };
          },
          err => {
            // this.hideUpdateProgressPopup();
            console.log("Failed to bulk update articles due to folowing error: ");
            console.log(err);
            this.makeToast("error", "Failed to bulk update. Please try again.");
            this.isBulkUpdateLoading = false;
          }
        );
    },
    updateSearchResults: async function(searchID=null) {
      if (searchID) {
        const index = this.showedSearchesIds.indexOf(searchID);
        // If ID is in showedSearchesIds, remove it and its articles
        if (index !== -1 && this.selectedSearchId !== searchID) {
          this.showedSearchesIds.splice(index, 1);
        } else if (index === -1) {
          // If ID is not in showedSearchesIds, add it and its articles
          if(searchID) this.showedSearchesIds.push(searchID);
        }
      }

      const searchIDS = this.showedSearchesIds.toString();
      if(searchIDS) {
        let URL = SearchResultsURL.replace("/0/", `/${searchIDS}/`);
        URL = this.applyURLFilters(URL);
        return await this.axiosGet(
          url=URL,
          isLoadingKey="isSeachResultsLoading",
          callBack=(resData) => {
            const results = resData;
            this.articlesReviews = results;
            this.hideModal("filters-slider");
          },
        );  
      }    
    },
    loadSearches: async function(selectSearchID=null){
      try {
        const res = await axios.get(notebookSearchAPI);
        console.log({res});
        this.isRecordsLoading = false;
        this.searchesHistory = res.data.literature_searches;
        this.dbs = res.data.databases_to_search;
        this.notebookReview = res.data.notebook_review;
        this.articleTags = res.data.tags;
        // if there is a selected search we make sure to display it's results
        if(selectSearchID) this.selectSearch(selectSearchID);
        return res;
      }
      catch (err) {
        console.log(err);
        this.isRecordsLoading = false;
      }
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
    this.loadSearches();   
    if (!clientID) this.loadClients(); 
    const timeOut = setTimeout(() => {
      this.styleTooltips();
      return clearTimeout(timeOut);
    }, 2000);
  }
})
