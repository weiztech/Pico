axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#article-tags-app',
    mixins: [globalMixin],
    delimiters: ["[[","]]"],
    data() {
        return {
            isLoading: false,
            tags : [],
            isEdit: false,
            currentEditedTagId: null,
            formTagInfo: {
                name: "",
                literature_review: litReviewID,
                description: "",
                color: "#000000",
            },
        }
    },
    methods : {
        // Helpers

        // actions
        onCancelEdit: function(){
            this.isEdit = false;
            this.formTagInfo = {
                name: "",
                literature_review: litReviewID,
                description: "",
                color: "",
            };
        },
        onDeleteTag: function(TagID){
            url = `${TagsListAPI}${TagID}/delete/`;
            axios.delete(url)
            .then(
                res => {
                    console.log(res);
                    const index = this.tags.findIndex(tag => tag.id === TagID);
                    this.tags.splice(index, 1);
                    this.makeToast("success", "Article tag was deleted successfully.");
                    this.closeBootstrapModal('deleteArticleTag-' + TagID);
                },
                err => {
                    console.log({err});
                    let error_msg = this.handleErrors(err);
                    this.makeToast("danger", error_msg);
                }
            );
        
        },
        onClickEditTag: function(tagetedTag){
            this.isEdit = true;
            this.formTagInfo.name = tagetedTag.name;
            this.formTagInfo.description = tagetedTag.description;
            this.formTagInfo.color = tagetedTag.color;
            this.currentEditedTagId = tagetedTag.id;
        },
        editTag: function(){
            const EditURL = `${TagsListAPI}${this.currentEditedTagId}/update/`;
            axios.patch(EditURL, data=this.formTagInfo, {
                headers: {
                    'Content-Type': 'application/json',
                }       
            })
            .then(
                res => {
                    console.log(res);
                    this.makeToast("success", "Your article tag was updated successfully.");
                    const tagIndex = this.tags.findIndex(tag => tag.id === this.currentEditedTagId);
                    if (tagIndex >-1){
                        this.tags.splice(tagIndex, 1, res.data)
                    }
                    this.isEdit = false;
                    this.formTagInfo = {
                        name: "",
                        literature_review: litReviewID,
                        description: "",
                        color: "",
                    }
                },
                err => {
                    console.log({err});
                    let error_msg = this.handleErrors(err);
                    this.makeToast("danger", error_msg);
                }
            );
        },
        onSubmit: function(e){
            e.preventDefault();
            if (this.isEdit) 
                this.editTag();
            else  
                this.addTag();
        },
        addTag: function(){
            axios.post(CreateTagAPI, data=this.formTagInfo, {
                headers: {
                    'Content-Type': 'application/json',
                }       
            })
            .then(
                res => {
                    console.log(res);
                    this.makeToast("success", "Your article tag was added successfully.");
                    this.tags.push(res.data);
                    this.formTagInfo = {
                        name: "",
                        literature_review: litReviewID,
                        description: "",
                        color: "",
                    }
                },
                err => {
                    console.log({err});
                    let error_msg = this.handleErrors(err);
                    this.makeToast("danger", error_msg);
                }
            );
        },
        loadTags: function(){
            this.isLoading = true;
            // TagsListAPI this var declared inside the django template
            axios.get(TagsListAPI)
                .then(
                    res => {
                        console.log(res);
                        this.tags = res.data;
                        this.isLoading = false;
                    },
                    err => {
                        console.log(err);
                        this.isLoading = false;
                    }
                );
        },
    },
    computed: {
        // a computed getter
        addTagColorRGBA: function () {
            // Remove '#' if present
            let hexColor = this.formTagInfo.color.replace('#', '');

            // Convert hex to RGB
            let r = parseInt(hexColor.substring(0, 2), 16);
            let g = parseInt(hexColor.substring(2, 4), 16);
            let b = parseInt(hexColor.substring(4, 6), 16);
            let alpha = "0.2";
            
            // Convert RGB to RGBA with the specified alpha (opacity)
            return 'rgba(' + r + ', ' + g + ', ' + b + ', ' + alpha + ')';
            
        }
    },
    mounted() {
        this.loadTags();
    }
})
