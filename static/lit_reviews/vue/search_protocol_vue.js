axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#app',
    mixins: [globalMixin],
    delimiters: ["[[", "]]"],
    data() {
        return {
            currentDB: null,
            currentDBType: "",
            switcher: 'recommended',
            dbAvailableConfig: ["pubmed", "ct_gov", "cochrane", "pmc", "scholar"],
            excludedParamsName: ['Recruitment Status', 'Expanded Access Status'], // In accordance with issue 1823 these clinical 
            // trials db configs are no longer applied and must be hidden from the user interface. 
            currentDBConfigStartDate: "",
            currentDBConfigEndDate: "",
            dbSearchConfigParams: [],
            isSubmitDataLoading: false,
            isSubmitDBConfigLoading: false,
            inputlitDatabaseSearch: "",
            inputaeDatabaseSearch: "",
            literature_review: "",
            searchParametersForm: {
                lit_date_of_search: "",
                lit_start_date_of_search: "",
                ae_date_of_search: "",
                ae_start_date_of_search: "",
                max_imported_search_results: null
            },
            deviceDescriptionForm: {
                device_description: "",
                intended_use: "",
                indication_of_use: "",
            },
            similarDeviceForm: {
                comparator_devices: "",
                sota_product_name: "",
                sota_description: "",
            },
            claimsForm: {
                safety_claims: "",
                performance_claims: "",
                other_info: "",
            },
            scopeOfReviewForm: {
                scope: "",
            },
            preparerForm: {
                preparer: "",
            },
            vigilanceDataForm: {
                vigilance_inclusion_manufacturers: "",
                vigilance_inclusion_keywords: "",
            },
            lit_db_selected: [],
            ae_db_selected: [],
            lit_search_protocol: null,
            lit_searches_databases_to_search: null,
            ae_databases_to_search: null,
            slideState: false,
            toggles: {
                "toggle_1": false,
                "toggle_2": false,
                "toggle_3": false,
                "toggle_4": false,
                "toggle_5": false,
                "toggle_6": false,
                "toggle_7": false,
            }
        }
    },
    computed: {
        isReadOnly() {
            return this.switcher === 'recommended';
        },
        optionsSplit() {
            return function (options) {
                if (options)
                    return options.split(',')
            }
        },
        filterlitDatabaseSearch() {
            if (this.lit_searches_databases_to_search)
                return this.lit_searches_databases_to_search.filter((db) =>
                    db.name.toLowerCase().includes(this.inputlitDatabaseSearch.toLowerCase())
                );
            return []
        },
        filterAeDatabaseSearch() {
            if (this.ae_databases_to_search)
                return this.ae_databases_to_search.filter((db) =>
                    db.name.toLowerCase().includes(this.inputaeDatabaseSearch.toLowerCase())
                );
            return []
        },
        isSearchParametersValid() {
            for (let key in this.searchParametersForm) {
                if (!this.searchParametersForm[key])
                    return false;
            }
            return true;
        },
        isDatabasesSearchValid() {
            if (this.lit_search_protocol)
                return this.lit_db_selected.length || this.ae_db_selected.length
            return false;
        },
        progressDeviceDescription() {
            return this.calculeProgress(this.deviceDescriptionForm)
        },
        progressSimilarDevice() {
            return this.calculeProgress(this.similarDeviceForm)
        },
        progressClaims() {
            return this.calculeProgress(this.claimsForm)
        },
        progressScopeOfReview() {
            return this.calculeProgress(this.scopeOfReviewForm)
        },
        progressPreparer() {
            return this.calculeProgress(this.preparerForm)
        },
        progressVigilance() {
            return this.calculeProgress(this.vigilanceDataForm)
        },
        isInLitDatabases() {
            return function (db_name) {
                const index = this.lit_db_selected.findIndex(name => name === db_name)
                return hasDB = index !== -1;
            }
        },
        isInAeDatabases() {
            return function (db_name) {
                const index = this.ae_db_selected.findIndex(name => name === db_name)
                return hasDB = index !== -1;
            };
        },
    },
    watch: {
        switcher: function () {
            if (this.switcher == 'manual') {
                this.setManualCurrentDBConfig()
            } else {
                this.setRecomendedCurrentDBConfig()
            }
        },
        // searchParametersForm: function (newVal, oldVal) {
        //     // Provide a recomanded / default db start/end date param
        //     if (newVal.lit_date_of_search !== oldVal.lit_date_of_search) {

        //     };
        //     if (newVal.lit_start_date_of_search !== oldVal.lit_start_date_of_search) {

        //     };
        // },
    },
    methods: {
        onSwitcher() {
            this.switcher = this.switcher === 'recommended' ? 'manual' : 'recommended';
        },
        onCheckAllOptions(param_id) {
            for (let index = 0; index < this.currentDB.search_configuration.length; index++) {
                let element = this.currentDB.search_configuration[index]
                let new_params = element.params.map((param) => {
                    if (param.type === 'CK' && param.id === param_id) {
                        if (param.selectAll) {
                            param.selected = []
                            param.selectAll = false
                        } else {
                            param.selected = param.options.split(',')
                            param.selectAll = true
                        }
                    }
                    return param
                });
                if (new_params) {
                    this.currentDB.search_configuration[index].params = new_params
                }
            }
        },
        validateDBConfig(database) {
            for (let index = 0; index < database.search_configuration.length; index++) {
                let element = database.search_configuration[index];
                for (let j = 0; j < element.params.length; j++) {
                    const param = element.params[j]
                    if (param.type === 'NB' && !param.value.match(/^-?\d+$/)) {
                        this.makeToast("danger", `'${param.name}' value should be a number`);
                        return false;
                    } else if (param.type === 'NB') {
                        if (parseInt(param.value) > 250) param.value = "250";
                    }
                }
            };

            // valid!
            return true;
        },
        onSaveDBConfiguration() {
            if (!this.vaidateStartEndDates(this.currentDBConfigStartDate, this.currentDBConfigEndDate)) {
                this.makeToast("danger", "Please make sure that Start Date Value is less than End Date Value");
                return;
            }
            
            if (this.currentDB) {
                if (this.currentDB.search_configuration.length) {
                    // Validate db config values 
                    if (!this.validateDBConfig(this.currentDB)) {
                        return 
                    };

                    for (let index = 0; index < this.currentDB.search_configuration.length; index++) {
                        let element = this.currentDB.search_configuration[index];
                        for (let j = 0; j < element.params.length; j++) {
                            const param = element.params[j]
                            if (param.type === 'CK') {
                                element.params[j].value = element.params[j]['selected'].join(',');
                            }
                        }
                    };

                    let config_params = this.currentDB.search_configuration[0].params.map((item) => {
                        let param = {
                            "id": item.id,
                            "value": item.value
                        };

                        if (item.type === 'DT') {
                            if (item.name === "Start Date") {
                                param.value = this.currentDBConfigStartDate;
                            } else {
                                param.value = this.currentDBConfigEndDate;
                            }
                        }
                        return param
                    })

                    this.isSubmitDBConfigLoading = true;

                    axios.put(`${searchProtocolURL}${this.currentDB.search_configuration[0].id}/`, data = { 
                        'params': config_params, 
                        'config_type': this.switcher
                    })
                        .then((res) => {
                            this.isSubmitDBConfigLoading = false;
                            this.makeToast("success", "Your database config has been updated successfuly");
                            this.currentDB.search_configuration[0] = res.data
                            if(this.currentDBType == "lit_database"){
                                this.setLiteratureDBParams(this.currentDB.name)
                            }
                            if(this.currentDBType == "ae_database"){
                                this.setAEDBParams(this.currentDB.name)
                            }
                            this.hideModal('db-config-slider');
                        }).catch((err) => {
                            this.isSubmitDBConfigLoading = false;
                            this.makeToast("danger", "Error Occured, failed to update your database config");
                        })
                } else {
                    this.makeToast("danger", "Database selected doesn't hava any configuration params ");
                }
            } else {
                this.makeToast("danger", "Please select one database to config it");
            }
        },
        onSaveChange() {
            if (this.searchParametersForm.lit_date_of_search.trim() === ''
                || this.searchParametersForm.lit_start_date_of_search.trim() === ''
                || this.searchParametersForm.ae_date_of_search.trim() === ''
                || this.searchParametersForm.ae_start_date_of_search.trim() === ''
            ) {
                this.makeToast("danger", "Please make sure these fields are not empty before submitting your form:" +
                    " Literature Search Start Date    Adverse Event Search Start Date");
                return;
            }
            if (!this.vaidateStartEndDates(this.searchParametersForm.lit_start_date_of_search, this.searchParametersForm.lit_date_of_search)) {
                this.makeToast("danger", "Please make sure that Literature Search Start Date Value is less than Literature Search End Date Value");
                return;
            }
            if (!this.vaidateStartEndDates(this.searchParametersForm.ae_start_date_of_search, this.searchParametersForm.ae_date_of_search)) {
                this.makeToast("danger", "Please make sure that Adverse Event Start Date Value is less than Adverse Event End Date Value");
                return;
            }
            const FormData = {
                literature_review: this.lit_search_protocol.literature_review.id,
                lit_date_of_search: this.searchParametersForm.lit_date_of_search,
                lit_start_date_of_search: this.searchParametersForm.lit_start_date_of_search,
                ae_date_of_search: this.searchParametersForm.ae_date_of_search,
                ae_start_date_of_search: this.searchParametersForm.ae_start_date_of_search,
                max_imported_search_results: this.searchParametersForm.max_imported_search_results,
                device_description: this.deviceDescriptionForm.device_description,
                intended_use: this.deviceDescriptionForm.intended_use,
                indication_of_use: this.deviceDescriptionForm.indication_of_use,
                comparator_devices: this.similarDeviceForm.comparator_devices,
                sota_product_name: this.similarDeviceForm.sota_product_name,
                sota_description: this.similarDeviceForm.sota_description,
                safety_claims: this.claimsForm.safety_claims,
                performance_claims: this.claimsForm.performance_claims,
                other_info: this.claimsForm.other_info,
                scope: this.scopeOfReviewForm.scope,
                preparer: this.preparerForm.preparer,
                lit_searches_databases_to_search: this.lit_db_selected,
                ae_databases_to_search: this.ae_db_selected,
                // Vigilance / PMCF Fields
                vigilance_inclusion_manufacturers: this.vigilanceDataForm.vigilance_inclusion_manufacturers,
                vigilance_inclusion_keywords: this.vigilanceDataForm.vigilance_inclusion_keywords,
            };
            
            this.isSubmitDataLoading = true
            axios.put(searchProtocolURL, data = FormData)
                .then((res) => {
                    this.lit_search_protocol = res.data
                    this.pushResultDataToForm()
                    this.makeToast('success', "Search protocol updated  successfully");
                    this.isSubmitDataLoading = false
                }).catch((err) => {
                    this.makeToast(variant, err);
                    this.isSubmitDataLoading = false
                })
        },
        vaidateStartEndDates: function (startDate, EndDate) {
            if (startDate >= EndDate) {
                return false;
            };
            return true;
        },
        handleAddDatabaseTOConfig(db_name) {
            this.lit_db_selected.push(db_name)
        },
        calculeProgress(object_name) {
            let count = 0
            let total = 0
            for (let key in object_name) {
                if (object_name[key])
                    count += 1;
                total += 1
            }
            const height = parseInt((count / total) * 100)
            return height
        },
        setManualCurrentDBConfig() {
            // this.currentDBConfigStartDate = "";
            // this.currentDBConfigEndDate = "";

            const includesAll = (arr, values) => values.every(v => arr.includes(v));
            for (let index = 0; index < this.currentDB.search_configuration.length; index++) {
                let element = this.currentDB.search_configuration[index];
                for (let j = 0; j < element.params.length; j++) {
                    const param = element.params[j]
                    if (param.type === 'CK') {
                        const valuesList = element.params[j].value ? element.params[j].value.split(',') : [];

                        element.params[j]['selectAll'] = includesAll(valuesList , element.params[j].options.split(','))
                        if (element.params[j].value) {
                            element.params[j]['selected'] = valuesList;
                        } else {
                            element.params[j]['selected'] = []
                        }
                    } else if (param.type === 'DT') {
                        if (element.params[j].value) {
                            if (param.name === "Start Date") {
                                this.currentDBConfigStartDate = element.params[j].value;
                            } else {
                                this.currentDBConfigEndDate = element.params[j].value;
                            }
                        }
                    }
                }
            }
        },
        setRecomendedCurrentDBConfig() {
            // Set Database Params Start/End dates to match General Paramaters Start/End Datet
            if (this.currentDBType === 'lit_database') {
                this.currentDBConfigStartDate = this.lit_search_protocol.lit_start_date_of_search;
                this.currentDBConfigEndDate = this.lit_search_protocol.lit_date_of_search;
            };
            if (this.currentDBType === 'ae_database') {
                this.currentDBConfigStartDate = this.lit_search_protocol.ae_start_date_of_search;
                this.currentDBConfigEndDate = this.lit_search_protocol.ae_date_of_search;
            };

            // Clear all fields
            if (this.currentDB.search_configuration.length) {
                let element = this.currentDB.search_configuration[0];
                for (let j = 0; j < element.params.length; j++) {
                    const param = element.params[j]
                    if (param.type === 'CK') {
                        element.params[j]['selectAll'] = false
                        element.params[j]['selected'] = []
                    }
                }
            };
        },        
        // for  Clinical Literature Databases (select params, set Date state, Date End)
        setLiteratureDBParams(db_name) {
            this.currentDBType = "lit_database" // or ae_database
            const db = this.lit_searches_databases_to_search.find(item => {
                if (item.name === db_name) {
                    return item
                }
            });
            this.currentDB = db;
            const config = this.currentDB.search_configuration?.[0];             
            if (config?.config_type === "manual") {
                this.switcher = "manual";
            } else {
                this.switcher = "recommended"; 
            }


            if (this.dbAvailableConfig.includes(db.entrez_enum)) 
                this.setManualCurrentDBConfig();
            else 
                this.setRecomendedCurrentDBConfig();
            
            this.showModal("db-config-slider");
        },
        setAEDBParams(db_name) {
            this.currentDBType = "ae_database";
            const db = this.ae_databases_to_search.find(item => {
                if (item.name === db_name) {
                    return item
                }
            });
            this.currentDB = db;
            const config = this.currentDB.search_configuration?.[0];             
            if (config?.config_type === "manual") {
                this.switcher = "manual";
            } else {
                this.switcher = "recommended"; 
            }
            this.setRecomendedCurrentDBConfig();
            this.showModal("db-config-slider");
        },
        toggleElement(toggle_id) {
            this.toggles[toggle_id] = !this.toggles[toggle_id]
        },
        assignObject(targetObj, sourceObj) {
            for (const key in targetObj) {
                if (targetObj.hasOwnProperty(key) && sourceObj.hasOwnProperty(key)) {
                    targetObj[key] = sourceObj[key];
                }
            }
        },
        pushResultDataToForm() {
            this.assignObject(this.searchParametersForm, this.lit_search_protocol);
            this.assignObject(this.deviceDescriptionForm, this.lit_search_protocol);
            this.assignObject(this.similarDeviceForm, this.lit_search_protocol);
            this.assignObject(this.claimsForm, this.lit_search_protocol);
            this.assignObject(this.scopeOfReviewForm, this.lit_search_protocol);
            this.assignObject(this.preparerForm, this.lit_search_protocol);
            this.assignObject(this.vigilanceDataForm , this.lit_search_protocol);

            // init databases selected
            this.lit_db_selected = this.lit_search_protocol.lit_searches_databases_to_search.map(db => db.name);
            this.ae_db_selected = this.lit_search_protocol.ae_databases_to_search.map(db => db.name);
        }
    },
    mounted() {
        this.isSubmitDataLoading = true
        axios.get(searchProtocolURL).then(res => {
            const {
                lit_search_protocol,
                lit_searches_databases_to_search,
                ae_databases_to_search,
            } = res.data
            this.lit_search_protocol = lit_search_protocol;
            this.lit_searches_databases_to_search = lit_searches_databases_to_search;
            this.ae_databases_to_search = ae_databases_to_search;
            this.pushResultDataToForm();
            this.isSubmitDataLoading = false;

        }).catch((err) => {
            this.isSubmitDataLoading = false;
        })
    }
})
