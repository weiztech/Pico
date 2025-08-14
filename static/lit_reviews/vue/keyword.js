axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#keyword-app',
    mixins: [globalMixin],
    delimiters: ["[[","]]"],
    data() {
        return {
            custome_keywords: [],
            keyword: {},
            isValid: true,
            isLoading: false,
            validation_message: ''
        }
    },
    methods : {
        // Helpers
        addCustomKeyword: function(){
            const CustomKeyword = {
                'id':0,
                'custom_kw' : '',
                'custom_kw_color': "#3c3c3c"
            }

            const customeKeywords = this.custome_keywords
            customeKeywords.push(CustomKeyword)
            this.custome_keywords = customeKeywords

        },
        validateKeywordForm: function(){
            all_custom_keywords = []
            this.custome_keywords.forEach(kw => {
                if (kw.custom_kw == ''){
                    this.isValid = false; 
                    this.validation_message = "Please fill all custom keyword fields."
                }
                if(all_custom_keywords.includes(kw.custom_kw)){
                    this.isValid = false;
                    this.validation_message = "Please remove duplicate custom keyword."
                }else{
                    all_custom_keywords.push(kw.custom_kw)
                }
            });
            return this.isValid
        },
        // actions
        deleteCustomKeyword: function(index,id){
            if (id != 0){
                url = KeywordURL+id+"/delete/"
                axios.post(url)
                .then(
                    res => {
                        console.log(res);
                        this.custome_keywords.splice(index,1);
                        this.makeToast("success", "A Custom Keyword has been Deleted Successfully!");
                    },
                    err => {
                        console.log({err});
                        let error_msg = this.handleErrors(err);
                        this.makeToast("danger", error_msg);
                    }
                );
            }
            else{
                this.custome_keywords.splice(index,1);
            }
        },
        submitKeywordForm: function(){
            this.isValid = true
            valid = this.validateKeywordForm();
            if (valid){
                formData = {
                    "keyword" : this.keyword,
                    "custom_keyword" : this.custome_keywords
                }
                axios.post(KeywordURL, data=formData,{
                    headers: {
                        'Content-Type': 'application/json',
                    }       
                })
                .then(
                    res => {
                        console.log(res);
                        this.makeToast("success", "Keyword has been Updated Successfully!");
                        this.keyword = res.data.keyword;
                        this.custome_keywords = res.data.custom_keywords;
                        // location.reload();
                    },
                    err => {
                        console.log({err});
                        let error_msg = this.handleErrors(err);
                        this.makeToast("danger", error_msg);
                    }
                );
            }else{
                this.makeToast("danger", this.validation_message);
            }
        },
    },
    mounted() {
        this.isLoading = true;
        // KeywordURL this var declared inside the django template
        axios.get(KeywordURL)
            .then(
                res => {
                    console.log(res);
                    this.keyword = res.data.keyword;
                    this.custome_keywords = res.data.custom_keywords;
                    this.isLoading = false;
                    console.log(this.keyword);
                    console.log(this.custome_keywords);
                },
                err => {
                    console.log(err);
                    this.isLoading = false;
                }
            );
    }
})
