var app = new Vue({
    el: '#app',
    mixins: [globalMixin],
    mounted(){
        const errorsDiv = document.getElementById("error_1_id_reason")
        if(errorsDiv) this.showModal('new-reason')
    }
})