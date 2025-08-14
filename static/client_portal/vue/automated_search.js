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
        }
    },
    methods : {
        // helpers
    },
    mounted() {
        this.isRecordsLoading = true;
        // AutomatedSearchURL this var de clared inside the django template
        axios.get(AutomatedSearchURL)
            .then(
                res => {
                    console.log(res);
                    this.isRecordsLoading = false;
                    this.entries = res.data.entries;
                    this.projects = res.data.projects;
                },
                err => {
                    console.log(err);
                    this.isRecordsLoading = false;
                }
            );
    }
})
