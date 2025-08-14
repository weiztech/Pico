var app = new Vue({
    el: '#app',
    delimiters: ["[[","]]"],
    data() {
        return {
            errorMessages : []
        }
    },
    mixins: [globalMixin],
    methods : {
        // helpers
        isEmptyInput(value){
            return value.trim() === ''
        },

        // actions
        onErrorDisplay: function(error_msg){
            const variant = "danger";
            this.makeToast(variant, error_msg);
        },
        vaidateStartEndDates: function(startDate, EndDate){
          if (startDate >= EndDate) {
            return false;
          };
          return true;
        },
        // Async Actions
        onFormSubmition(e) {
            e.preventDefault();
            const lit_start_date_of_search = document.getElementById("id_lit_start_date_of_search").value;
            const ae_start_date_of_search = document.getElementById("id_ae_start_date_of_search").value;
            const ae_date_of_search = document.getElementById("id_ae_date_of_search").value;
            const lit_date_of_search = document.getElementById("id_lit_date_of_search").value;
            const max_imported_search_results = document.getElementById("id_max_imported_search_results").value;
            const lit_searches_databases_to_search = document.querySelectorAll('input[name="lit_searches_databases_to_search"]:checked');
            const ae_databases_to_search = document.querySelectorAll('input[name="ae_databases_to_search"]:checked');

            const isEmptyFields = {
              "Literature Search Start Date": this.isEmptyInput(lit_start_date_of_search),
              "Literature Search End Date": this.isEmptyInput(lit_date_of_search),
              "Adverse Event Search Start Date": this.isEmptyInput(ae_start_date_of_search),
              "Max imported search results": this.isEmptyInput(max_imported_search_results),
              "Clinical Literature Databases To Search": lit_searches_databases_to_search.length === 0,
            };
          
            const emptyFieldsLabels = Object.entries(isEmptyFields)
              .filter(([_, value]) => value)
              .map(([key, _]) => key);
          
            const isLitDatesValid = this.vaidateStartEndDates(lit_start_date_of_search, lit_date_of_search);
            let isAEDatesValid = true;
            if (ae_date_of_search && ae_start_date_of_search)
              isAEDatesValid = this.vaidateStartEndDates(ae_start_date_of_search, ae_date_of_search);

            const form = document.getElementById("search_protocol_form");
            
            if (emptyFieldsLabels.length > 0) {
              this.errorMessages = [...emptyFieldsLabels];
              this.$refs["invalid-form"].show();
              // this.showToast("invalid-form");
            } else if (!isLitDatesValid) {
              this.makeToast("danger", "Please make sure that Literature Search Start Date Value is less than Literature Search End Date Value");
            } else if (!isAEDatesValid) {
              this.makeToast("danger", "Please make sure that Adverse Event Start Date Value is less than Adverse Event End Date Value");
            } else {
              form.submit();
            }
          },
    },
    mounted() {
    }
})