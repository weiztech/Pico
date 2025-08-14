axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#app',
    delimiters: ["[[","]]"],
    data() {
        return {
            article: {
                "title":"",
                "abstract":"",
                "citation":"",
                "pubmed_uid":"",
                "pmc_uid":"",
                "pdf_file":"",
                "device":"",
                "type_creation":"",
                "zip_file":""
            },
            
        }
    },
    methods : {
        makeToast(variant = null, title, body) {
            this.$bvToast.toast(body, {
              title: title,
              autoHideDelay: 3000,
              solid: true,
              variant:variant,
              toaster: "b-toaster-top-center"
            })
        },
        // helpers
        submit_single_article_creation: function(){
            console.log("single form submitted");
            single_form_validation = this.validate_single_article_creation()
        },
        validate_single_article_creation: function(){
            console.log("validate form submitted");
            this.article.type_creation = "single";
            console.log("article",this.article);
            article = this.article
            if (article.title && article.abstract && article.citation && article.pdf_file && article.pubmed_uid && article.pmc_uid) {
                console.log("form is valid");
                //send form to url
                axios.post(CreateArticleURL, data=article)
                .then(
                    res => {
                        console.log({res});
                        // remove defualt values
                        this.article = {
                            "title":"",
                            "abstract":"",
                            "citation":"",
                            "pubmed_uid":"",
                            "pmc_uid":"",
                            "pdf_file":"",
                            "device":"",
                            "type_creation":"",
                            "zip_file":""
                        }
                        let success_msg = "The article has been created successfully."
                        this.makeToast("success", "Add Article Form Success", success_msg);
                    },
                    err => {
                        console.log({err});
                        let error_msg = this.handleErrors(err);
                        this.makeToast("danger", "Add Article Form Error", error_msg);
                    }
                )

            }else{
                console.log("form is not valid");
                error_msg = "Please fill all required fields before submitting your form."
                this.makeToast("danger", "Article Form is not Valid", error_msg);
            }
        },
        submit_bulk_article_creation: function(){
            console.log("single form submitted");
            single_form_validation = this.validate_bulk_article_creation()
        },
        validate_bulk_article_creation: function(){
            console.log("validate form submitted");
            this.article.type_creation = "bulk";
            console.log("article",this.article);
            article = this.article
            if (article.zip_file) {
                console.log("form is valid");
            }else{
                console.log("form is not valid");
                error_msg = "Please fill all required fields before submitting your form."
                this.makeToast("danger", "Article Form is not Valid", error_msg);
            }
        },
        ondeviceChange: function(){
            this.article.device = this.$refs.device.value;
        },
        onpdfChange: function(){
            this.article.pdf_file = this.$refs.pdf_file.files[0];
        },
        onzipChange: function(){
            this.article.zip_file = this.$refs.zip_file.files[0];
        },
    },
    mounted() {
    }
})
