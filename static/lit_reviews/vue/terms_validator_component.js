const SearchTermValidator = {
  template: `
    <div v-if="validator && validator.status !== 'COMPLETE'" class="alert warning term-validator">
      <div class="center-h">
        Search Term Matching Tool
        <span
          class="ml"
          title="On some projects, you want to run the same terms across multiple databases and have them match up. This tool simply shows you if forgot any terms on any database. If you intend to have different search terms for different databases, ignore this warning"
        >
          <svg 
          width="16" 
          height="16" 
          viewBox="0 0 16 16" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg"
          style="height: 16px; margin-bottom: -3px;"
          >
            <path 
              d="M8 8V5M8 10.2236V10.25M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8Z" 
              :stroke="validator && validator.status == 'COMPLETE' ? '#027A48' : '#B54708'" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"
            />
          </svg>
        </span>
      </div>

      <div class="warning-box" v-on:click="showModal('terms-validator-errors')" title="Show Warning"> 02 </div>

      <div class="modal" id="terms-validator-errors">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <div class="modal-header-icon-wrapper warning-icon">
                <svg width="24" height="25" viewBox="0 0 24 25" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path
                    d="M12 13.4V8.91447M12 16.7248V16.7642M17.6699 20.5H6.33007C4.7811 20.5 3.47392 19.4763 3.06265 18.0757C2.88709 17.4778 3.10281 16.8551 3.43276 16.3249L9.10269 6.10102C10.4311 3.96632 13.5689 3.96633 14.8973 6.10103L20.5672 16.3249C20.8972 16.8551 21.1129 17.4778 20.9373 18.0757C20.5261 19.4763 19.2189 20.5 17.6699 20.5Z"
                    stroke="#DC7003" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </div>
              Search Terms Validation Error
              <div class="hint mt-2"> 
              On some projects, you want to run the same terms across multiple databases and have them match up. 
              This tool simply shows you if forgot any terms on any database. 
              If you intend to have different search terms for different databases, ignore this warning
              </div>
            </div>
            <div class="modal-body" v-html="validator && validator.error_msg" style="color: black;">
            </div>
            <div class="modal-footer">
              <button class="error-button w-50" v-on:click="onValidateTerms" :disabled="isLoading"> Re Validate Terms </button>
              <button class="secondary-gray-button w-50 ml" v-on:click="hideModal('terms-validator-errors')"> Close </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="validator && validator.status === 'COMPLETE'" class="alert success term-validator">
      <div class="center-h">
        Search Term Matching Tool
        <span
          class="ml"
          title="On some projects, you want to run the same terms across multiple databases and have them match up. This tool simply shows you if forgot any terms on any database. If you intend to have different search terms for different databases, ignore this warning"
        >
          <svg 
          width="16" 
          height="16" 
          viewBox="0 0 16 16" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg"
          style="height: 16px; margin-bottom: -3px;"
          >
            <path 
              d="M8 8V5M8 10.2236V10.25M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8Z" 
              :stroke="validator && validator.status == 'COMPLETE' ? '#027A48' : '#B54708'" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"
            />
          </svg>
        </span>
      </div>

      <div class="success-box" v-on:click="showModal('terms-validator-success')" title="Show Warning"> Revalidate </div>

      <div class="modal" id="terms-validator-success">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <div class="modal-header-icon-wrapper info-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M15.3754 11.9995H12.0004M12.0004 11.9995H8.62537M12.0004 11.9995V15.3744M12.0004 11.9995L12.0004 8.62447M21 6.37498L21 17.625C21 19.489 19.489 21 17.625 21H6.375C4.51104 21 3 19.489 3 17.625V6.37498C3 4.51103 4.51104 3 6.375 3H17.625C19.489 3 21 4.51103 21 6.37498Z" stroke="#014EE9" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
              </div>
              Search Terms Validation
              <div class="hint mt-2"> 
              On some projects, you want to run the same terms across multiple databases and have them match up. 
              This tool simply shows you if forgot any terms on any database. 
              If you intend to have different search terms for different databases, ignore this warning
              </div>
            </div>
            <div class="modal-body" style="color: black;">
              <h3> Your Terms are all valid! No Warnings found! </h3>
            </div>
            <div class="modal-footer">
              <button class="primary-button w-50" v-on:click="onValidateTerms" :disabled="isLoading"> Re Validate Terms </button>
              <button class="secondary-gray-button w-50 ml" v-on:click="hideModal('terms-validator-success')"> Close </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  mixins: [globalMixin],
  props: ["initValidator"],
  data: () => ({
    validator: this.initValidator,
    isLoading: false,
  }),
  methods: {
    checkValidatorStatus: function () {
      const interval = setInterval(
        function () {
          const postData = { is_checking: true };

          axios.post(searchTermsValidatorURL, (data = postData)).then(
            (res) => {
              if (res.data.validator.status !== "PROCESSING") {
                this.isLoading = false;
                try {
                  this.hideModal("terms-validator-success");
                } catch(e) {
                  this.hideModal("terms-validator-errors");
                }
                this.validator = res.data.validator;
                clearInterval(interval);
                console.log("Interval has been cleared");
              }
            },
            (err) => {
              console.log({ err });
            }
          );
        }.bind(this),
        5000
      );
    },
    // Async Actions
    onValidateTerms: function () {
      this.isLoading = true;

      axios.post(searchTermsValidatorURL, (data = {})).then(
        (res) => {
          this.checkValidatorStatus(); 
        },
        (err) => {
          console.log({ err });
          this.isLoading = false;
          let error_msg = this.handleErrors(err);
          this.makeToast("danger", error_msg);
          this.enableElement(termsValidatorBTN, "Validate Search Terms");
        }
      );
    },
  },
  mounted() {
    console.log(this.initValidator)
    this.validator = this.initValidator;
  }
};

// Register component to be accessed globaly
Vue.component('search-term-validator', SearchTermValidator);