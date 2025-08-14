axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#app',
    delimiters: ["[[","]]"],
    mixins: [globalMixin],
    data() {
        return {
            records: [],
            isRecordsLoading: false,
            currentEditedAE: null,
        }
    },
    methods : {
        // Actions
        addEventForm: function(db_enum){
            const newRecords = this.records.map((item, index) => {
                if (item.database.entrez_enum === db_enum){
                    item.forms_count = item.forms_count + 1;
                } 
                return item;
            });
            this.records = newRecords;
        },
        removeEventForm: function(db_enum){
            const newRecords = this.records.map((item, index) => {
                if (item.database.entrez_enum === db_enum){
                    item.forms_count = item.forms_count - 1;
                } 
                return item;
            });
            this.records = newRecords;
        },
        showEditModal(item, ae, ae_type) {
            const aeReview = {
                searches: item.searches,
                review: ae,
                db: item.database.name,
                ae_type,
            };

            this.currentEditedAE = aeReview;
            this.showModal("update-ae-modal");
        },
        // Helpers
        enableElement: function(ele, text=null){
            ele.style.pointerEvents = "auto";
            ele.style.opacity = "1";
            if (text)
                ele.innerHTML  = text;
        },
        disableElement: function(ele, text=null){
            ele.style.pointerEvents = "None";
            ele.style.opacity = ".7";
            if (text)
                ele.innerHTML  = text;
        },
        extractValues: function(htmlElemnt, formData, index){
            const inputs = htmlElemnt.getElementsByTagName("input");
            const inputsArray = [...inputs];

            inputsArray.map(input => {
                if (input.type === "file"){
                    const file = input.files[0];

                    if (file)
                        formData.append(input.name+index, file, file.name)
                }
                else
                    formData.append(input.name+index, input.value);
            });

            const selects = htmlElemnt.getElementsByTagName("select");
            const selectsArray = [...selects];
            selectsArray.map(select => {
                formData.append(select.name+index, select.value);
            });
        },
        
        // Async Calls
        onDeleteAdverseEvent: function(review, is_recall, e){
            const ae_id = review.id;
            // hide delete button
            this.disableElement(e.target, "Deleting...");
            let deleteURL;
            if (is_recall)
                deleteURL = `/literature_reviews/api/${litReviewID}/adverse_recalls/${ae_id}/delete/`;
            else
                deleteURL = `/literature_reviews/api/${litReviewID}/adverse_events/${ae_id}/delete/`;

            axios.delete(deleteURL)
                .then(
                    res => {
                        console.log(res);

                        // id => review id 
                        // object_id => review.ae.id 
                        const {id, object_id} = res.data;

                        const newRecords = this.records.map((item, index) => {
                            const newAEs = [];
                            const oldAEs =  is_recall ? item.adverse_recalls : item.adverse_events; 
                            for (ae_review of oldAEs){
                                if (id !== ae_review.id){
                                    newAEs.push(ae_review);
                                }
                            };

                            if (is_recall){
                                item.adverse_recalls = newAEs;
                            } else {
                                item.adverse_events = newAEs;
                            };
                            return item;
                        });

                        this.records = newRecords;
                        const variant = "success";
                        const title = "Delete Adverse Event";
                        let success_msg = "Adverse Event with ID '" + object_id + "' has been Deleted Successfully!";

                        this.makeToast(variant, success_msg);
                        this.enableElement(e.target, "Delete");
                    },
                    err => {
                        console.log({err});
                        const variant = "danger";
                        const title = "Error Deleting AE";
                        let error_msg = "Error occured while trying to delete adverse event with id " + review.ae.id + " : ";
                        error_msg += this.handleErrors(err);
                        this.makeToast(variant, error_msg);

                        // show delete button again
                        this.enableElement(e.target, "Delete");
                    }
                )
        },  
        onAddEventFormSubmit: function(e){
            e.preventDefault(); 
            const db = e.target.elements.db.value;
            const aeForms = e.target.getElementsByClassName("add-event-form");
            const aeFormsArray = [...aeForms]
            const formData = new FormData()
            let formsCount = 0;

            // hide submit button
            const submitBTN = document.getElementById(`submit-btn-${db}`);
            this.disableElement(submitBTN);

            aeFormsArray.map((item) => {
                formsCount += 1;
                const values = this.extractValues(item, formData, formsCount);
            });
            formData.append('is_completed', e.target["review-completed"].checked);
            formData.append('db', db);
            formData.append('forms_count', formsCount);

            console.log(...formData);
            axios.post(aeListURL, formData)
                .then(
                    res => {
                        console.log(res);
                        const newRecords = this.records.map((item, index) => {
                            if (item.database.entrez_enum === res.data.database.entrez_enum){
                               return res.data;
                            } else 
                                return item;
                        });
                        this.records = newRecords;

                        const variant = "success";
                        const title = "Manual Adverse Event";
                        let success_msg = "A new Manual Adverse Event has been added Successfully!"

                        this.makeToast(variant, success_msg);
                        this.enableElement(submitBTN);
                    },
                    err => {
                        console.log(err);
                        this.isRecordsLoading = false;
                        const variant = "danger";
                        const title = "Error Adding AE";

                        let error_msg = this.handleErrors(err);
                        this.makeToast(variant, error_msg);
                        this.enableElement(submitBTN);
                    }
                );
        },
        onUpdateAEFormSubmit: function(e){
            e.preventDefault();
            const formData = new FormData();
            const ae_id = e.target.elements.ae_id.value;
            const review_id = e.target.elements.review_id.value;
            const is_recall = e.target.elements.ae_type.value === "AR";
            const formElements = e.target.elements;

            formData.append("ae.manual_type", formElements.type.value);
            formData.append("ae.manual_severity", formElements.severity.value);
            formData.append("ae.manual_link", formElements.link.value);
            formData.append("ae.manual_pdf", formElements.pdf.files.length ? formElements.pdf.files[0] : "");
            formData.append("ae.event_date", formElements.event_date.value);
            formData.append("search", formElements.search.value);
            console.log(...formData);

            // disable submit btn
            const btn = document.getElementById("modal-submit-btn");
            this.disableElement(btn, "Saving...");

            // send data to server
            let updateURL;
            if (is_recall)
                updateURL = `/literature_reviews/api/${litReviewID}/adverse_recalls/${review_id}/update/`;
            else
                updateURL = `/literature_reviews/api/${litReviewID}/adverse_events/${review_id}/update/`;

            axios.patch(updateURL, data=formData)
                .then(
                    res => {
                        // id => review id 
                        // object_id => review.ae.id 
                        const {id, object_id, updated_instance} = res.data;

                        const newRecords = this.records.map((item, index) => {
                            const newAEs = [];
                            const oldAEs =  is_recall ? item.adverse_recalls : item.adverse_events; 
                            for (ae_review of oldAEs){
                                if (id !== ae_review.id)
                                    newAEs.push(ae_review);
                                else
                                    newAEs.push(updated_instance);
                            };

                            if (is_recall){
                                item.adverse_recalls = newAEs;
                            } else {
                                item.adverse_events = newAEs;
                            };
                            return item;
                        });

                        this.records = newRecords;
                        const variant = "success";
                        const title = "Update Adverse Event";
                        let success_msg = "Adverse Event with ID '" + object_id + "' has been Updated Successfully!";

                        this.makeToast(variant, success_msg);
                        this.enableElement(btn, "Save");
                        this.hideModal('update-ae-modal');
                    },
                    err => {
                        console.log({err});
                        const variant = "danger";
                        const title = "Error Updating AE";
                        let error_msg = "Error occured while trying to update adverse event with id " + ae_id + " : ";
                        error_msg += this.handleErrors(err);
                        this.makeToast(variant, error_msg);

                        // show update button again
                        this.enableElement(btn, "Save");
                    }
                )
        },
    },
    mounted() {
        this.isRecordsLoading = true;
        // aeListURL this var de clared inside the django template
        axios.get(aeListURL)
            .then(
                res => {
                    console.log(res);
                    this.isRecordsLoading = false;
                    this.records = res.data;
                },
                err => {
                    console.log(err);
                    this.isRecordsLoading = false;
                }
            );
    }
})
