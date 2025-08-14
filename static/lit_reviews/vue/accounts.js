axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#accounts-pages',
    mixins: [globalMixin],
    delimiters: ["[[","]]"],
    data() {
        return {
            searchTerm: "",
        }
    },
    methods : {
        // Helpers
    },
});


