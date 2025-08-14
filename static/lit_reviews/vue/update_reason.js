var app = new Vue({
    el: '#app',
    mixins: [globalMixin],
    delimiters: ["[[","]]"],
    data() {
        return{

        }
    },
    methods : {
        changeUpdateMethod: function(method){
            var inputElement = document.getElementById('UpdateMethod');
            inputElement.value = method;
            
            // submit the form
            form = document.getElementById('update-reason-form')
            form.submit()
        }
    }
})
