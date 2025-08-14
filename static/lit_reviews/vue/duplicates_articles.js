axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
  el: '#app',
  components: {
  },
  mixins: [globalMixin],
  delimiters: ["[[", "]]"],
  data() {
    return {
      isLoading: false,

      stateSymbole: "",
      articleState: "",

      duplicate_articles:[],
      potential_duplicate_articles:[],
      dbs: [],
      sort: "article__title",
      appliedSort: "article__title",
      sortOptions: [
        {name: "ID", value: "id"},
        {name: "Title", value: "article__title"},
      ],
      sortingDirection: "Ascending",
      sortingDirectionOptions: [
        {name: "Ascending", value: "Ascending"},
        {name: "Descending", value: "Descending"},
      ],
      searchTerm: "",

      viewType:"Duplicates",
      statesOptions: [
        {name: "Select Article State", value: ""},
        {name: "Unclassified", value: "U"},
        {name: "Included", value: "I"},
        {name: "Excluded", value: "E"},
        {name: "Maybe", value: "M"},
        {name: "Duplicate", value: "D"},
      ],

      // appliedStates on the backend / selectedStates, selectedTags on the frontend.
      selectedStates: [],

      tablePageIndicator: "",
      tablePageIndicatorPotential: "",
      appliedStates: [],
      currentURL: "",
      selectedDatabases: [],
      pagination: {
        current: 0,
        count: 0,
        next: 0,
        previous: 0,
        last: 0,
        page_range: []
      },
      pagination_potential: {
        current: 0,
        count: 0,
        next: 0,
        previous: 0,
        last: 0,
        page_range: []
      },
    }
  },
  computed: {
    isFiltersApplied() {
        return this.selectedDatabases.length;
    },
  },
  methods: {
    // helpers
    getState(symbole) {
      switch (symbole) {
        case "U":
          return "Unclassified";
        case "I":
          return "Retained";
        case "M":
          return "Maybe";
        case "E":
          return "Excluded";
        case "D":
          return "Duplicate";

        default:
          return "Unclassified";
      }
    },
    getStateClassName(stateSymbole) {
      switch (stateSymbole) {
        case "U":
          return "badge secondary";
        case "I":
          return "badge success";
        case "M":
          return "badge info";
        case "E":
          return "badge error";
        case "D":
          return "badge warning";

        default:
          return "badge secondary";
      }
    },
    truncateText(text) {
      return text.length > 30 ? text.slice(0, 30) + '...' : text; 
    },
    hideArticleDetails(review) {
      this.hideModal('article-details-'+review.id);
    },
    toggleState(state) {
      const index = this.selectedStates.indexOf(state);
      if (index > -1){
        this.selectedStates.splice(index, 1);
      } else {
        this.selectedStates.push(state)
      }
    },
    hexToRgba(hex, opacity) {
      // Remove '#' if present and convert hex to RGB
      let hexColor = hex.startsWith('#') ? hex.slice(1) : hex;
      let rgb = parseInt(hexColor, 16);
      let r = (rgb >> 16) & 0xff;
      let g = (rgb >>  8) & 0xff;
      let b = (rgb >>  0) & 0xff;
    
      // Return RGBA with specified opacity
      return `rgba(${r}, ${g}, ${b}, ${opacity})`;
    },
    getCurrentFilterValue(type) {
      const queryParams = this.currentURL.split("?");
      const queryParamsItems = queryParams[1].split("&");
      for (queryparam of queryParamsItems) {
        const filter = queryparam.split("=");
        const filterLabel = filter[0];
        const filterValue = filter[1];

        if (type===filterLabel)
          return filterValue;
      };

      return null;
    },
    getCurrentStates() {
      const values = this.getCurrentFilterValue("state");
      if (values){
        const states = values.split(",");
        this.appliedStates = states;
        return states;
      }
      return [];
    },
    showUpdateProgressPopup: function(){
      popup = document.getElementById("update-loading-section");
      popup.style.display= "flex";
    },
    hideUpdateProgressPopup: function(){
        popup = document.getElementById("update-loading-section");
        popup.style.display= "none";
    },


    // Actions
    sortBy(sorting){
      if (sorting == "article__title"){
        if (this.sort === "article__title"){
          this.sort = "-article__title";
        }else {
          this.sort = "article__title";
        }
      }else if (sorting=="score") {
        if (this.sort === "score"){
          this.sort = "-score";
        }else {
          this.sort = "score";
        }
      }
      this.loadRecords();
    },
    onSort() {
      if (this.sortingDirection === "Descending")
        this.sort = "-" + this.appliedSort; 
      else 
        this.sort = this.appliedSort;
      
      this.$refs["sorting-dropdown"].classList.remove("active");
      this.loadRecords();
    },
    onSwitchView(selectedBoard) {
      this.viewType = selectedBoard;
    },
    onCloseFilters() {
      this.selectedStates = this.getCurrentStates();
      this.hideModal('filters-slider');
    },
    onSearch(e) {
      e.preventDefault();
      // add selected database
      // const dbInputs = document.getElementsByName("database");
      // this.selectedDatabases = [];
      // for (let i=0; i<=dbInputs.length-1; i++) {
      //     const dbName = dbInputs[i].value;
      //     if (dbInputs[i].checked)
      //       this.selectedDatabases.push(dbName);
      // };
      this.hideModal('filters-slider');
      this.loadRecords();
    },
    onClearFilters() {
      this.selectedStates = [];
      this.searchTerm = "";
      this.selectedDatabases = [];
      this.loadRecords();
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
    onMarkasDuplicate(reviewID) {
      const values = {state: 'D'}
      const URL = ArticleReviewDuplicateAPI.slice(0, -2) + reviewID + "/";

      axios.patch(URL, data=values)
        .then(
          res => {
            this.loadRecords();
          },
          err => {
            console.log("Failed to update the article state due to folowing error: ");
            console.log(err);
            this.makeToast("danger", `Failed to update the state for article #${reviewID}.`);
          }
        )
    },
    onShowArticleDetails(review) {
      this.showModal('article-details-'+review.id);
    },
    loadDuplicateArticles(page = 1) {
      // uclassifiedRefresh: we don't show popup modal when update states in unclassified page 
      if (page < 1 || (page > this.pagination.last && this.pagination.last!== 0))
        return ;
      this.showUpdateProgressPopup();

      const urlParams = new URLSearchParams(window.location.search);
      const state = urlParams.get('state');
      this.stateSymbole = state;
      this.articleState = this.getState(this.stateSymbole);
      let URL = DuplicatesArticlesListAPI;


      if (this.stateSymbole){
        URL = `${URL}?state=${this.stateSymbole}`;
        this.selectedStates = [this.stateSymbole];
      }  
      
      if (page){
        if (URL.includes("?"))
          URL =  `${URL}&page=${page}`;
        else
          URL =  `${URL}?page=${page}`;
      };

      if (this.sort){
        if (URL.includes("?"))
          URL =  `${URL}&ordering=${this.sort}`;
        else
          URL =  `${URL}?ordering=${this.sort}`;
      };

      if (this.searchTerm) {
        if (URL.includes("?"))
          URL =  `${URL}&search=${this.searchTerm}`;
        else
          URL =  `${URL}?search=${this.searchTerm}`;
      };

      if (this.selectedDatabases.length) {
        const dbs = this.selectedDatabases.join(",")
        if (URL.includes("?"))
          URL =  `${URL}&db=${dbs}`;
        else
          URL =  `${URL}?db=${dbs}`;
      };

      this.appliedStates = this.selectedStates;
      this.currentURL = URL;
      this.isLoading = true;
      // ArticlesListAPI this var declared inside the django template
      return axios.get(URL)
        .then(
          res => {
            console.log(res);
            this.duplicate_articles = res.data.results;

            this.isLoading = false;
            // this.hideUpdateProgressPopup();
            this.pagination.current = page;
            this.pagination.count = res.data.count;
            this.pagination.next = res.data.next;
            this.pagination.previous = res.data.previous;
            this.pagination.last =  Math.floor(this.pagination.count/50);
            if ((this.pagination.count % 50) > 0)
              this.pagination.last += 1;
            this.pagination.page_range = [
              this.pagination.current-1, 
              this.pagination.current, 
              this.pagination.current+1
            ];
            const currentPageTotalIncriment = this.duplicate_articles.length < 50 ? 
            this.duplicate_articles.length + (this.pagination.current-1) * 50
            : this.pagination.current * 50
            this.tablePageIndicator = `${this.pagination.current*50-49}-${currentPageTotalIncriment} Of ${this.pagination.count}`;

          },
          err => {
            console.log(err);
            this.isLoading = false;
            // this.hideUpdateProgressPopup();
          }
        );
    },
    loadPotentialDuplicateArticles(page = 1) {
      // uclassifiedRefresh: we don't show popup modal when update states in unclassified page 
      if (page < 1 || (page > this.pagination_potential.last && this.pagination_potential.last!== 0))
        return ;
      this.showUpdateProgressPopup();

      const urlParams = new URLSearchParams(window.location.search);
      const state = urlParams.get('state');
      this.stateSymbole = state;
      this.articleState = this.getState(this.stateSymbole);
      let URL = PotentialDuplicatesArticlesListAPI;


      if (this.stateSymbole){
        URL = `${URL}?state=${this.stateSymbole}`;
        this.selectedStates = [this.stateSymbole];
      }  
      
      if (page){
        if (URL.includes("?"))
          URL =  `${URL}&page=${page}`;
        else
          URL =  `${URL}?page=${page}`;
      };

      if (this.sort){
        if (URL.includes("?"))
          URL =  `${URL}&ordering=${this.sort}`;
        else
          URL =  `${URL}?ordering=${this.sort}`;
      };

      if (this.searchTerm) {
        if (URL.includes("?"))
          URL =  `${URL}&search=${this.searchTerm}`;
        else
          URL =  `${URL}?search=${this.searchTerm}`;
      };

      if (this.selectedDatabases.length) {
        const dbs = this.selectedDatabases.join(",")
        if (URL.includes("?"))
          URL =  `${URL}&db=${dbs}`;
        else
          URL =  `${URL}?db=${dbs}`;
      };

      this.appliedStates = this.selectedStates;
      this.currentURL = URL;
      this.isLoading = true;
      // PotentialDuplicatesArticlesListAPI this var declared inside the django template
      return axios.get(URL)
        .then(
          res => {
            console.log(res);
            this.potential_duplicate_articles = res.data.results;

            this.isLoading = false;
            // this.hideUpdateProgressPopup();
            this.pagination_potential.current = page;
            this.pagination_potential.count = res.data.count;
            this.pagination_potential.next = res.data.next;
            this.pagination_potential.previous = res.data.previous;
            this.pagination_potential.last =  Math.floor(this.pagination_potential.count/50);
            if ((this.pagination_potential.count % 50) > 0)
              this.pagination_potential.last += 1;
            this.pagination_potential.page_range = [
              this.pagination_potential.current-1, 
              this.pagination_potential.current, 
              this.pagination_potential.current+1
            ];
            const currentPageTotalIncriment = this.potential_duplicate_articles.length < 50 ? 
            this.potential_duplicate_articles.length + (this.pagination_potential.current-1) * 50
            : this.pagination_potential.current * 50
            this.tablePageIndicatorPotential = `${this.pagination_potential.current*50-49}-${currentPageTotalIncriment} Of ${this.pagination_potential.count}`;

          },
          err => {
            console.log(err);
            this.isLoading = false;
            // this.hideUpdateProgressPopup();
          }
        );
    },
    loadRecords: function(){
      Promise.all([this.loadDuplicateArticles(), this.loadPotentialDuplicateArticles()]).then((values) => {
        this.hideUpdateProgressPopup();
      });
    },
  },
  mounted() {
    this.loadDatabases();
    this.loadRecords();
  }
})