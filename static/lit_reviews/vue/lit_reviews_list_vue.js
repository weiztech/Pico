axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#app',
    mixins: [globalMixin],
    delimiters: ["[[", "]]"],
    data() {
        return {
            litReivews: [],
            // isFilter: false,
            allProjectTypeSelected:"",
            allSearchTypeSelected:"",
            projecTypeFilter: [],
            searchTypeFilter: [],
            devicesTypeFilter: [],
            manufacturersTypeFilter: [],
            selectedStartDate:"",
            selectedEndDate:"",
            selectedDeviceType:"",
            selectedManufacturerType:"",
            statusFilter:["active"],
            pageSize: 20,
            isLoading: false,
            stateSymbole: "U",
            articleState: "Unclassified",
            exclusions: [],
            sort: "article__title",
            searchTerm: "",
            reviewAnalysis: null,
            // appliedStates on the backend / selectedStates on the frontend.
            selectedStates: ['U'],
            tablePageIndicator: "",
            appliedStates: ['U'],
            currentURL: "",
            dbs: [],
            selectedDatabases: [],
            pagination: {
                current: 0,
                count: 0,
                next: 0,
                previous: 0,
                last: 0,
                page_range: []
            },
            tourGuideSteps: [
                {
                  target: '#tour-step-01',
                  title: "Articles Overview",
                  content: 'General overview for the articles status in all of your projects',
                //   params: {
                //     enableScrolling: false
                //   }
                },
                {
                  target: '#tour-step-02',
                  content: 'Create new project from here',
                },
                {
                    target: '#tour-step-03',
                    title: "Projects List",
                    content: 'Below table list all of your previous projects',
                },
                {
                    target: '#tour-step-04',
                    title: "Projects Filters",
                    content: 'You are searching for a specific project ? you can filter down the results from here',
                },
                {
                    target: '#tour-step-05',
                    title: "Pagination",
                    content: 'If you have a big number of results not all of them will show up in the first page, so you need to navigate from here to next pages to review older ones',
                },
              ],
              tourOptions: {
                useKeyboardNavigation: true,
              }
        }
    },
    computed: {
        isFilterApplied: function(){
            return this.projecTypeFilter.length || this.searchTypeFilter.length || this.statusFilter.length || this.searchTerm || this.selectedStartDate || this.selectedEndDate || this.selectedDeviceType || this.selectedManufacturerType;
        },
    },
    methods: {
        sortBy(sorting) {
            if (sorting == "project__project_name") {
                if (this.sort === "project__project_name") {
                    this.sort = "-project__project_name";
                } else {
                    this.sort = "project__project_name";
                }
            }
            this.loadLitReviews(1);

        },
        onCloseFilters() {
            // this.selectedStates = this.getCurrentStates();
            this.hideModal('filters-slider');
        },
        getProjectName(review) {
            return review.project &&  review.project.project_name ? review.project.project_name : review.device ? review.device.name : '';
        },
        formatCount(number) {
            return number > 9000 ? String((number/1000).toFixed(1)) + "K" : number;
        },
        onSearch() {
            // if (this.searchTerm)
            //     this.isFilter = true
            this.loadLitReviews(1);
        },
        onClearFilters() {
            // this.isFilter = false
            this.searchTerm = "";
            this.projecTypeFilter = [];
            this.searchTypeFilter = [];
            this.statusFilter = [];
            this.selectedStartDate = "";
            this.selectedEndDate = "";
            this.selectedDeviceType = "";
            this.selectedManufacturerType = "";

            this.loadLitReviews(1);
        },
        showUpdateProgressPopup: function () {
            popup = document.getElementById("update-loading-section");
            popup.style.display = "flex";
        },
        hideUpdateProgressPopup: function () {
            popup = document.getElementById("update-loading-section");
            popup.style.display = "none";
        },

        // Async Calls
        initiatTourGuide() {
            setTimeout(() => {
                if (this.litReivews.length < 3){
                    introJs().setOptions({
                        steps: [
                            {
                                title: this.tourGuideSteps[0].title,
                                element: document.querySelector('#tour-step-01'),
                                intro: this.tourGuideSteps[0].content,
                            },
                            {
                                title: this.tourGuideSteps[1].title,
                                element: document.querySelector('#tour-step-02'),
                                intro: this.tourGuideSteps[1].content,
                            },
                            {
                                title: this.tourGuideSteps[2].title,
                                element: document.querySelector('#tour-step-03'),
                                intro: this.tourGuideSteps[2].content,
                            },
                            {
                                title: this.tourGuideSteps[3].title,
                                element: document.querySelector('#tour-step-04'),
                                intro: this.tourGuideSteps[3].content,
                            },
                            {
                                title: this.tourGuideSteps[4].title,
                                element: document.querySelector('#tour-step-05'),
                                intro: this.tourGuideSteps[4].content,
                            },
                        ]
                    }).start();
                };
            }, 500);
        },
        loadAnalysis() {
            const URL = literatureReviewAnalysisURL;
            axios.get(URL)
                .then(
                    res => {
                        this.reviewAnalysis = res.data;
                    }, err => {
                        console.log(err);
                    }
                )
        },
        loadLitReviews(page = 1) { 
            console.log(page)
            if (page < 1 || (page > this.pagination.last && this.pagination.last !== 0))
                return;
            //   this.showUpdateProgressPopup();
            // this.articles = [];
            let URL = literatureReviewURL;


            if (page) {
                if (URL.includes("?"))
                    URL = `${URL}&page=${page}&page_size=${this.pageSize}`;
                else
                    URL = `${URL}?page=${page}&page_size=${this.pageSize}`;
            };

            if (this.sort) {
                if (URL.includes("?"))
                    URL = `${URL}&ordering=${this.sort}`;
                else
                    URL = `${URL}?ordering=${this.sort}`;
            };

            if (this.searchTerm) {
                if (URL.includes("?"))
                    URL = `${URL}&search=${this.searchTerm}`;
                else
                    URL = `${URL}?search=${this.searchTerm}`;
            };

            if (this.projecTypeFilter.length) {
                let values = this.projecTypeFilter.join(',')                
                if (URL.includes("?"))
                    URL = `${URL}&project_type=${values}`;
                else
                    URL = `${URL}?project_type=${values}`;
            }
            if (this.searchTypeFilter.length) {
                let values = this.searchTypeFilter.join(',')
                if (URL.includes("?"))
                    URL = `${URL}&search_type=${values}`;
                else
                    URL = `${URL}?search_type=${values}`;
            }
            if (this.statusFilter.length) {
                let values = this.statusFilter.join(',')
                if (URL.includes("?"))
                    URL = `${URL}&status=${values}`;
                else
                    URL = `${URL}?status=${values}`;
            }
            
            if (this.selectedStartDate) {
                if (URL.includes("?"))
                  URL =  `${URL}&selected_start_date=${this.selectedStartDate}`;
                else
                  URL =  `${URL}?selected_start_date=${this.selectedStartDate}`;
            };

            if (this.selectedEndDate) {
                if (URL.includes("?"))
                  URL =  `${URL}&selected_end_date=${this.selectedEndDate}`;
                else
                  URL =  `${URL}?selected_end_date=${this.selectedEndDate}`;
            };

            if (this.selectedDeviceType) {
                if (URL.includes("?"))
                  URL =  `${URL}&selected_device_type=${this.selectedDeviceType}`;
                else
                  URL =  `${URL}?selected_device_type=${this.selectedDeviceType}`;
            };

            if (this.selectedManufacturerType) {
                if (URL.includes("?"))
                  URL =  `${URL}&selected_manufacturer_type=${this.selectedManufacturerType}`;
                else
                  URL =  `${URL}?selected_manufacturer_type=${this.selectedManufacturerType}`;
            };

            this.appliedStates = this.selectedStates;
            this.currentURL = URL;
            this.isLoading = true;
            axios.get(URL)
                .then(
                    res => {
                        let limit = this.pageSize
                        this.litReivews = res.data.results;
                        this.devicesTypeFilter = res.data.devices;
                        this.manufacturersTypeFilter = res.data.manufacturers;
                        
                        this.isLoading = false;
                        this.hideUpdateProgressPopup();
                        this.pagination.current = page;
                        this.pagination.count = res.data.count;
                        this.pagination.next = res.data.next;
                        this.pagination.previous = res.data.previous;
                        this.pagination.last = Math.floor(this.pagination.count / limit);
                        if ((this.pagination.count % limit) > 0)
                            this.pagination.last += 1;

                        this.pagination.page_range = [
                            this.pagination.current - 1,
                            this.pagination.current,
                            this.pagination.current + 1
                        ];
                        const currentPageTotalIncriment = this.litReivews.length < limit ?
                            this.litReivews.length + (this.pagination.current - 1) * limit
                            : this.pagination.current * limit
                        this.tablePageIndicator = `${((this.pagination.current * limit) - limit) + 1}-${currentPageTotalIncriment} Of ${this.pagination.count}`;
                        this.hideModal("filters-slider");

                        // this.initiatTourGuide();
                    },
                    err => {
                        console.log(err);
                        this.isLoading = false;
                        this.hideUpdateProgressPopup();
                    }
                );
        },

    },
    watch: {
        pageSize() {
            this.loadLitReviews()
        },
        allProjectTypeSelected:function(newValue, oldValue){
            if(newValue){
                this.projecTypeFilter =  ['lit_review', 'Vigilance', 'CER', 'PMCF']
            }else{
                this.projecTypeFilter = []
            }
        },
        allSearchTypeSelected:function(newValue, oldValue){
            if(newValue){
                this.searchTypeFilter =  ['true', 'false']
            }else{
                this.searchTypeFilter = []
            }
        }
    },    
    async mounted() {
        await this.loadLitReviews();
        await this.loadAnalysis();        
    }
});