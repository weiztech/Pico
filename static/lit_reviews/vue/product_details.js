var app = new Vue({
    el: '#app',
    delimiters: ["[[","]]"],
    data() {
        return {
            errorMessages : []
        }
    },
    methods : {
        // helpers
        onCancelEdit: function(e) {
            window.location.reload();
        }
    },
    mounted() {
    }
})