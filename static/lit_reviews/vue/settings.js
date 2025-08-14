axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#settings-app',
    mixins: [globalMixin],
    delimiters: ["[[","]]"],
    data() {
        return {
            isLoading: false,
            isUpdating: false,
            settings: null,
            articleFields: [],
            nonArticleFields: ["ris_file_fields", "ris_fields_list", "id", "client", "full_texts_naming_format", "format_choices"],
            valueMatchError: false,
            valueMatchErrorMessage: "",
            customeLabels:[],
            isValid: true,
            selectedFTFormat: "",
        }
    },
    methods : {
        // Helpers
        getArticleFields: function(){
            const fields = [];
            if (this.settings) {
                for (key in this.settings) {
                    if (!this.nonArticleFields.includes(key)) {
                        const fieldName = key.split("_").slice(2).join(" ");
                        fields.push([fieldName, this.settings[key]]);
                    }
                }
            }

            return fields;
        },
        formatArticleField: function(key){
            return key.split("_").slice(2).join(" ");
        },
        clearSelectErrors: function(){
            for (key in this.settings) { 
                if(this.$refs['select-item-'+key]) this.$refs['select-item-'+key][0].classList.remove("select-error");
            }
        },
        addCustomLabel: function(){
            const CustomLabel = {
                'id':0,
                'label' : '',
            }
            this.customeLabels.push(CustomLabel)
        },
        // actions
        onUpdateSettings: function(e){
            let URL = UpdateCustomerSettingsURL.replace("0", this.settings.id);
            this.axiosPatch(
                event=e, 
                url=URL, 
                isLoadingKey="isUpdating", 
                successMsg="Your settings has been updated successfully!",
                postingD=this.settings
            );
        },
        validateLabelForm: function(){
            all_custom_labes = []
            this.customeLabels.forEach(label => {
                if (label.label == ''){
                    this.isValid = false; 
                    this.validation_message = "Please fill all custom label fields."
                }
                if(all_custom_labes.includes(label.label)){
                    this.isValid = false;
                    this.validation_message = "Please remove duplicate custom keyword."
                }else{
                    all_custom_labes.push(label.label)
                }
            });
            return this.isValid
        },
        getLabels: function(){
            axios.get(CustomLabelURL)
            .then(
                res => {
                    console.log(res);
                    this.customeLabels = res.data.search_labels;
                    console.log(this.customeLabels);
                },
                err => {
                    console.log(err);
                }
            );
        },
        deleteCustomLabel: function(index,id){
            if (id != 0){
                url = CustomLabelURL+id+"/delete/"
                axios.delete(url)
                .then(
                    res => {
                        console.log(res);
                        this.customeLabels.splice(index,1);
                        this.makeToast("success", "A custom label has been deleted successfully.");
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
        submitCustomLabelForm: function(){
            valid = this.validateLabelForm();
            if (valid){
                formData = {
                    "custome_labels" : this.customeLabels
                }
                axios.post(CustomLabelURL, data=formData,{
                    headers: {
                        'Content-Type': 'application/json',
                    }       
                })
                .then(
                    res => {
                        console.log(res);
                        this.makeToast("success", "Your project's custom labels have been updated successfully.");
                        this.customeLabels = res.data.search_labels;
                        // // location.reload();
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
        getSettings: function(){
            const successCallBack = (resData) => {
                this.settings = resData;
                this.selectedFTFormat = resData.format_choices[0][0];
                this.articleFields = this.getArticleFields();
            };

            this.axiosGet(
                url=CustomerSettingsURL,
                isLoadingKey="isLoading",
                callBack=successCallBack,
            );
        },
    },
    watch: {
        settings: {
            handler: function(newSettings, oldSettings) {
                /* Watch whenever settings changes and raise error if there is two fields with the same value */

                console.log({newSettings})
                if (newSettings) {
                    let matchFound = false;
                    for (key in this.settings) {
                        for (key2 in this.settings) { 
                            if (key !== key2 && this.settings[key] == this.settings[key2] && !this.nonArticleFields.includes(key)) {
                                this.valueMatchError = true;
                                this.valueMatchErrorMessage = `${this.formatArticleField(key)} and ${this.formatArticleField(key2)} have the same value`;
                                this.$refs['select-item-'+key][0].classList.add("select-error");
                                this.$refs['select-item-'+key2][0].classList.add("select-error");
                                matchFound = true;
                            }
                        }
                    }
                    if (!matchFound) {
                        this.valueMatchError = false;
                        this.valueMatchErrorMessage = "";
                        this.clearSelectErrors();
                    }
                }
            },
            deep: true,
        }
    },
    mounted() {
        this.getSettings();
        this.getLabels();
    }
})
