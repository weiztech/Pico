axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#content',
    delimiters: ["[[","]]"],
    data() {
        return {
            isRecordsLoading: false,
            active_tab : "messages",
            projects :[],
            messages : [],
            typeFilter: "",
            dateFilter: "",
            search_term: "",
            search_term_url: "",
            dateFilter:"",
            types: [
                {id: "lit_review", name: "Lit. Review"},
                {id: "CER", name: "CER"},
                {id: "PMCF", name: "PMCF"},
                {id: "Vigilance", name: "Vigilance"},
            ]
        }
    },
    computed: {
        // a computed getter
        pubDate() {
            year = this.dateFilter.getFullYear();
            month = this.dateFilter.getMonth() + 1;
            day = this.dateFilter.getDate();
            return year + "-" + month + "-" + day;
        }
    },
    watch: {
        // whenever pubDateFilter changes, this function will run
        dateFilter() {
            this.onFilter();
        }
      }, 
    methods : {
        // helpers   
        changeselectedtab: function(tab){
            this.active_tab = tab;
        },
        onTypeFilterChange: function(e){
            this.typeFilter = e.target.value;
            this.onGetPage();
        },
        onClearFilters: function(e){
            e.preventDefault();
            this.deviceFilter = "";
            this.dateFilter = "";
            this.typeFilter = "";
            this.search_term = "";
            this.onFilter();
        },
        // Async Actions
        onGetPage: function(){
            // this.isRecordsLoading = true;
            this.isRecordsLoading = true;
            // DocumentsLibraryURL this var de clared inside the django template.
            let URL = `${projectsURL}?`;
            if (this.search_term){
                this.search_term_url = this.search_term;
                URL += `&search_term=${this.search_term}`;
            }
            if (this.dateFilter)
                URL += `date_filter=${this.pubDate}&`;
            if (this.typeFilter) 
                URL += `type_filter=${this.typeFilter}&`;

            axios.get(URL)
                .then(
                    res => {
                        console.log(res);
                        this.isRecordsLoading = false;
                        this.projects = res.data;
                        // this.devices = res.data.devices;
                    },
                    err => {
                        console.log(err);
                        this.isRecordsLoading = false;
                    }
                );
        },
        onFilter: function(){
            this.isRecordsLoading = true;
            this.onGetPage();
        },

        
    },
    components: {
        'vuejs-datepicker':vuejsDatepicker
    },
    mounted() {
        this.isRecordsLoading = true;
        // aeListURL this var de clared inside the django template
        axios.get(projectsURL)
            .then(
                res => {
                    console.log(res);
                    this.isRecordsLoading = false;
                    this.projects = res.data;
                    // this.devices = res.data.devices;
                },
                err => {
                    console.log(err);
                    this.isRecordsLoading = false;
                }
            );
        axios.get(messagesURL)
            .then(
                res => {
                    console.log(res);
                    this.isRecordsLoading = false;
                    this.messages = res.data;
                    // this.devices = res.data.devices;
                },
                err => {
                    console.log(err);
                    this.isRecordsLoading = false;
                }
            );
    }
})
