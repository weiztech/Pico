axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#content',
    delimiters: ["[[","]]"],
    data() {
        return {
            projects: [],
            devices: [],
            deviceFilter: "",
            dateFilter: "",
            dateFilterFormated: "",
            isRecordsLoading: false,
            loadingPage: false,
            typeFilter: "",
            types: [
                {id: "lit_review", name: "Lit. Review"},
                {id: "CER", name: "CER"},
                {id: "PMCF", name: "PMCF"},
                {id: "Vigilance", name: "Vigilance"},
            ]
        }
    },
    watch: {
        // whenever dateFilter changes, this function will run
        dateFilter(newDateFilter, oldDateFilter) {
            if (newDateFilter && newDateFilter !== oldDateFilter){
                this.dateFilterFormated = this.formatDate(newDateFilter);
                this.onFilter();  
            };
        },
      },
    methods : {
        // helpers
        formatDate: function(date){
            const year =  date.getFullYear();
            const month = date.getMonth()+1;
            let day = date.getDate();
            day = day.length === 1 ? `0${day}` : day;

            return `${year}-${month}-${day}`;
        },
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
            this.onGetPage();
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
            this.dateFilterFormated = "";
            this.onFilter();
        },

        // Async Actions
        onGetPage: function(){
            // this.isRecordsLoading = true;
            this.isRecordsLoading = true;
            // DocumentsLibraryURL this var de clared inside the django template.
            let URL = `${projectsURL}?`;
            if (this.deviceFilter)
                URL += `device_filter=${this.deviceFilter}&`;
            if (this.dateFilterFormated)
                URL += `date_filter=${this.dateFilterFormated}&`;
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
        // projectsURL this var de clared inside the django template
        let URL = `${projectsURL}?`;
        if (window.location.href.includes("type_filter=Vigilance")){
            this.typeFilter = "Vigilance";
            URL += `type_filter=Vigilance&`;
        }   
            
             
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

        // devicesURL this var de clared inside the django template
        axios.get(devicesURL)
            .then(
                res => {
                    console.log(res);
                    this.devices = res.data;
                },
                err => {
                    console.log(err);
                }
            );
    }
})
