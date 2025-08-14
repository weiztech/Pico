axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#nav-bar',
    mixins: [globalMixin],
    delimiters: ["[[","]]"],
    data() {
        return {
        }
    },
    methods : {
        // Actions
    },
    mounted() {
    }
})
