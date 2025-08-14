axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#app',
    mixins: [globalMixin],
    delimiters: ["[[","]]"],
    data() {
        return {
        }
    },
    methods : {
        // Actions
        onSwitchSimpleAdvanced(){
            const subOptions =  document.getElementsByClassName("menu-sub-option-list");
            for (let i = 0; i < subOptions.length; i++) {
              subOptions[i].classList.toggle("hide")
            }
        }
    },
    mounted() {
    }
})
