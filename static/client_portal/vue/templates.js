var app = new Vue({
    el: '#content',
    delimiters: ["[[","]]"],
    data() {
        return {
            active_tab : "clinical",
        }
    },
    methods : {
        // helpers   
        changeselectedtab: function(tab){
            this.active_tab = tab;
        },
    },

    mounted() {
    }
})
