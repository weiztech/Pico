axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#content',
    delimiters: ["[[","]]"],
    data() {
        return {
            devices: [],
            manufacturers: [],
            lit_dbs: [],
            ae_basic_dbs: [],
            ae_extra_dbs: [],
            isRecordsLoading: false,
            clients: [],
            selectedLitDbs: [], // Store selected LIT databases
            selectedAEDbs: [],  // Store selected AE databases
            selectedExtraLicenseDbs: [], // Store selected Extra License databases

            selectedDevice: "",
            createDevice:false,
            selectedInterval: "",
            selectedDatabases: [],
            selectDbsSection:false,
            searchType: "terms",
            searchTerms:"",
            searchFile:"",
            deviceName:"",
            createManufacturer:false,
            selectedManufacturer:"",
            selectedClient:"",
            manufacturerName:"",
            classification:"",
            markets:"",
            startDate: "",
            yearsBack: 10,
        }
    },


    methods : {
        // helpers
        makeToast(variant = null, title, body) {
            this.$bvToast.toast(body, {
              title: title,
              variant: variant,
              autoHideDelay: 3000,
              solid: true,
              toaster: "b-toaster-top-center",
            })
        },
        handleFileChange(event) {
            // Access the selected file from the event
            this.searchFile = event.target.files[0];
        },
        showCreateNewDeviceSection() {
            // Access the selected file from the event
            this.createDevice = !this.createDevice;
        },
        showCreateNewManufacturerSection() {
            // Access the selected file from the event
            this.createManufacturer = !this.createManufacturer;
        },
        showSelectDbsSection() {
            // Access the selected file from the event
            this.selectDbsSection = !this.selectDbsSection;
        },
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

        // actions
        onErrorDisplay: function(error_msg){
            const variant = "danger";
            const title = "Search Terms Error";
            this.makeToast(variant, title, error_msg);
        },

        validateNewAutomatedSearch() {
            const validateNewAutomatedSearchBTN = document.getElementById("creation-automated-search-form-submit-btn");
            this.disableElement(validateNewAutomatedSearchBTN, "Running Please Wait...");
            // Initialize an array to store validation errors
            const errors = [];
        
            // Check if createDevice is true and validate fields accordingly
            if (this.createDevice) {
            if (!this.deviceName) errors.push('Device name is required.');
            if (this.createManufacturer) {
                if (!this.manufacturerName) errors.push('Manufacturer name is required.');
            } else {
                console.log("this.selectedManufacturer",this.selectedManufacturer);
                if (!this.selectedManufacturer) errors.push('Manufacturer is required.');
            }
            if (!this.classification) errors.push('Classification is required.');
            if (!this.markets.length) errors.push('At least one market must be selected.');
            } else {
            if (!this.selectedDevice) errors.push('Selected device is required.');
            }
            
            // Validate Years Back
            // if (!this.yearsBack) errors.push('Please make sure to provide years back');

            // Validate startDate
            if (!this.startDate) errors.push('Please make sure to provide a start date.');

            // Validate other variables
            if (!this.selectedInterval) errors.push('Selected interval is required.');
            if (
            !(
                this.selectedLitDbs.length ||
                this.selectedAEDbs.length ||
                this.selectedExtraLicenseDbs.length
            )
            ) {
                errors.push('At least one database must be selected.');
            }
        
            if (this.searchType === 'terms') {
            if (!this.searchTerms) errors.push('Search terms are required.');
            } else {
            if (!this.searchFile) errors.push('Search file is required.');
            }
        
            // Check if there are any validation errors
            if (errors.length > 0) {
                this.enableElement(validateNewAutomatedSearchBTN, "Add Search");
                // Log or display errors
                errors.forEach((error) => {
                    this.onErrorDisplay(error)
                    console.error(error); // You can log errors here
                });
            } else {

                const selectedLitDbsList = this.selectedLitDbs.filter(db => typeof db === 'string');
                const selectedAEDbsList = this.selectedAEDbs.filter(db => typeof db === 'string');
                const selectedExtraLicenseDbsList = this.selectedExtraLicenseDbs.filter(db => typeof db === 'string');
                const selectedDbs = [...selectedLitDbsList, ...selectedAEDbsList, ...selectedExtraLicenseDbsList];
                
                const postData = {
                    createDevice: this.createDevice,
                    createManufacturer: this.createManufacturer,
                    deviceName: this.deviceName,
                    manufacturerName: this.manufacturerName,
                    selectedManufacturer: this.selectedManufacturer,
                    classification: this.classification,
                    markets: this.markets,
                    selectedDevice: this.selectedDevice,
                    selectedInterval: this.selectedInterval,
                    selectedDbs: JSON.stringify(selectedDbs),
                    searchType: this.searchType,
                    searchTerms: this.searchTerms.trim(),
                    searchFile: this.searchFile,
                    // yearsBack: this.yearsBack,
                    startDate: this.startDate,
                    client: this.selectedClient,
                }
                
                axios.post(CreateAutomatedSearchURL,data=postData, {
                    headers: {
                      'Content-Type': 'multipart/form-data', 
                    },
                })
                .then(
                      res => {
                            console.log(res.data);
                            const variant = "success";
                            const title = "Automated Search Creation";
                            this.makeToast(variant, title, "Your Automated Search Project Has Been Created Successfully.");
                            this.enableElement(validateNewAutomatedSearchBTN, "Add Search");
                            window.location.href = '/client_portal/automated_search';
                      },
                      err => {
                            console.log({err});
                            this.enableElement(validateNewAutomatedSearchBTN, "Add Search");
                            this.onErrorDisplay({err})
                      }
                  )
            }    
        },
    },
    mounted() {
        this.isRecordsLoading = true;
        // CreateAutomatedSearchURL this var de clared inside the django template
        axios.get(CreateAutomatedSearchURL)
            .then(
                res => {
                    console.log(res);
                    this.isRecordsLoading = false;
                    this.devices = res.data.devices;
                    this.clients = res.data.clients;
                    this.manufacturers = res.data.manufacturers;
                    this.lit_dbs = res.data.lit_dbs;
                    this.ae_basic_dbs = res.data.ae_basic_dbs;
                    this.ae_extra_dbs = res.data.ae_extra_dbs;

                    if (this.clients.length)
                        this.selectedClient = this.clients[0].id;
                },
                err => {
                    console.log(err);
                    this.isRecordsLoading = false;
                }
            );
    }
})
