axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#ae-list',
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
    mounted() {
        const timeOut = setTimeout(() => {
            this.styleTooltips();
            return clearTimeout(timeOut);
        }, 2000);
    }
});
