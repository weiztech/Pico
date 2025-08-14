axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
  el: '#app',
  delimiters: ["[[", "]]"],
  data() {
    return {
      records: [],
      fiveMinutesUpdateInterval: null,
      isLoading: false,
      sort: "-script_timestamp",
      dbList: [],
      litReviewsList: [],
      statusList: [
        "EXCLUDED",
        "FAILED",
        "SUCCESS"
      ],
      filters: {
        term: "",
        db: [],
        startDate: "",
        endDate: "",
        user: "",
        literatureReview: [],
        status: [],
      },
      pagination: {
        current: 0,
        count: 0,
        next: 0,
        previous: 0,
        last: 0,
        page_range: []
      },
    }
  },
  methods: {
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
    getStatusClass(status){
      if(status==="EXCLUDED")
        return "badge warning";
      else if (status==="SUCCESS")
        return "badge success";
      else
        return "badge danger";
    },
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
    sortBy(sorting){
      if (sorting == "database_name"){
        if (this.sort === "database_name"){
          this.sort = "-database_name";
        }else {
          this.sort = "database_name";
        }
      }else if (sorting=="search_term") {
        if (this.sort === "search_term"){
          this.sort = "-search_term";
        }else {
          this.sort = "search_term";
        }
      } else if (sorting=="script_timestamp") {
        if (this.sort === "script_timestamp"){
          this.sort = "-script_timestamp";
        }else {
          this.sort = "script_timestamp";
        }
      }
      this.loadRecords(1)

    },
    showUpdateProgressPopup: function(){
      popup = document.getElementById("update-loading-section");
      popup.style.display= "flex";
    },
    hideUpdateProgressPopup: function(){
        popup = document.getElementById("update-loading-section");
        popup.style.display= "none";
    },
    displayFiltersPopUp: function(){
      const popup = this.$refs.filtersPopUp;
      popup.style.display= "flex";
    },
    hideFiltersPopUp: function(id){
      const popup = this.$refs.filtersPopUp;
      popup.style.display= "none";
    },
    onSearch(e){
      e.preventDefault();
      this.hideFiltersPopUp();
      this.loadRecords();
    },
    contructURL(page){
      let URL = ScraperReportsListAPI;

      // Filters
      if (this.filters.term){
        if (URL.includes("?"))
          URL =  `${URL}&search=${this.filters.term}`;
        else
          URL =  `${URL}?search=${this.filters.term}`;
      }
      if (this.filters.literatureReview.length){
        const reviewsFilter = this.filters.literatureReview.toString();
        if (URL.includes("?"))
          URL =  `${URL}&literature_review=${reviewsFilter}`;
        else
          URL =  `${URL}?literature_review=${reviewsFilter}`;
      }
      if (this.filters.db.length){
        const dbsFilter = this.filters.db.toString();
        if (URL.includes("?"))
          URL =  `${URL}&database_name=${dbsFilter}`;
        else
          URL =  `${URL}?database_name=${dbsFilter}`;
      }
      if (this.filters.status.length){
        const statusFilter = this.filters.status.toString();
        if (URL.includes("?"))
          URL =  `${URL}&status=${statusFilter}`;
        else
          URL =  `${URL}?status=${statusFilter}`;
      }

      // Ordering
      if (this.stateSymbole)
        URL = `${URL}?state=${this.stateSymbole}`;
      if (page){
        if (URL.includes("?"))
          URL =  `${URL}&page=${page}`;
        else
          URL =  `${URL}?page=${page}`;
      }
      if (this.sort){
        if (URL.includes("?"))
          URL =  `${URL}&ordering=${this.sort}`;
        else
          URL =  `${URL}?ordering=${this.sort}`;
      }

      return URL
    },
    clearFilters(){
      this.filters = {
        term: "",
        db: [],
        startDate: "",
        endDate: "",
        user: "",
        literatureReview: [],
        status: [],
      };
      this.loadRecords();
    },

    // Async Calls
    loadRecords(page=1) {
      this.isLoading = true
      const URL = this.contructURL(page);
      // this.showUpdateProgressPopup();
      // ArticlesListAPI this var declared inside the django template
      axios.get(URL)
        .then(
          res => {
            this.isLoading = false
            console.log(res);
            this.dbList = res.data.dbs.map(dbObj => {
              return {value: dbObj.name, text: dbObj.displayed_name};
            });
            this.litReviewsList = res.data.lit_reviews.map(review => {
              return {value: review.id, text: review.label};
            });
            
            const recordsResp = res.data.reports;
            this.records = recordsResp.results;
            this.hideUpdateProgressPopup();
            this.pagination.current = page;
            this.pagination.count = recordsResp.count;
            this.pagination.next = recordsResp.next;
            this.pagination.previous = recordsResp.previous;
            this.pagination.last =  Math.floor(this.pagination.count/50);
            if ((this.pagination.count % 50) > 0)
              this.pagination.last += 1;
            this.pagination.page_range = [
              this.pagination.current-1, 
              this.pagination.current, 
              this.pagination.current+1
            ];
          },
          err => {
            console.log(err);
            this.isLoading = false
            this.hideUpdateProgressPopup();
          }
        );
    },
  },
  computed: {
    appliedFilters () {
      let count = 0;
      if (this.filters.term)
        count += 1;
      if (this.filters.db.length)
        count += 1;
      if (this.filters.literatureReview.length)
        count += 1;
      if (this.filters.status.length)
        count += 1;
      return count;
    }
  },
  mounted() {
    const ONE_MINUTE = 1000*60
    const FIVE_MINUTES = ONE_MINUTE*5;
    this.loadRecords();
    this.fiveMinutesUpdateInterval = setInterval(function(){
      this.loadRecords(this.pagination.current);
    }, FIVE_MINUTES)
  },
  destroyed() {
    clearInterval(this.fiveMinutesUpdateInterval);
  }
})