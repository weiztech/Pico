// axios.defaults.xsrfCookieName = 'csrftoken'
// axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#app',
    delimiters: ["[[","]]"],
    mixins: [globalMixin],
    data() {
        return {
            devices: [],
            manufacturers: [],
            clients: [],
            reviews: [],
            searchedDevices: [],
            searchedClients: [],
            searchedReviews: [],
          
            clientSearchTerm: "",
            deviceSearchTerm: '',
            reviewSearchTerm: '',
            
            currentStep: 1,
            TOTAL_STEPS: 6,
            currentStepLabel: "project-name",

            isUserClient: false,
            isEditProjectNameSection: false,
            isEditClientSection: false,
            isEditDeviceSection: false,
            isEditProjectTypeSection: false,
            isEditLitProjectTypeSection: false,
            isEditCopyData: false,

            newClient: {
              name: "",
              short_name : "",
              long_name : "",
              full_address_string : "",
              logo : "",
            },
            newDevice: {
              name: "",
              manufacturer: "",
              classification: "",
              markets: "",
            },
            isNewManufacturer: false,
            literatureReview: {
                device: "",
                type: "",
                client: "",
                projectType: "",
                isCopyData: null,
                copyDataFrom: "",
                project: {
                    name: "",
                }
            },
            loadAndSelectDeviceID: null,
            onCompleteRedirectURL: null,

            isCreateDeviceLoading: false,
            isCreateClientLoading: false,
            isCreateProjectLoading: false,
          }
    },
    computed: {
      progressPerccentage: function () {
        return parseInt((this.currentStep / this.TOTAL_STEPS) * 100);
      },
      isCreateClientValid: function() {
        if (this.isCreateClientLoading)
          return false;

        for (let key in this.newClient){
          if (key !== "logo" && !this.newClient[key])
            return false;
        }

        return true;
      },
      isCreateDeviceValid: function() {
        if (this.isCreateDeviceLoading)
          return false;

        for (let key in this.newDevice){
          if (!this.newDevice[key])
            return false;
        }

        return true;
      },
      isProjectCreationValid: function() {
        if (this.isCreateProjectLoading)
          return false;

        const validClient = this.isUserClient ? true : this.literatureReview.client;
        let isValid = false;
        if (this.literatureReview.type === "SIMPLE") {
          isValid = (this.literatureReview.project.name && this.literatureReview.type && validClient)
        } else if (this.literatureReview.type) {  
          isValid = (
            this.literatureReview.project.name && this.literatureReview.type && validClient 
            && this.literatureReview.device && this.literatureReview.projectType && 
            (this.literatureReview.isCopyData ? (this.literatureReview.copyDataFrom) : this.literatureReview.isCopyData === false)
          )
        }

        return isValid ? true : false;
      },
      projectNameSectionStatus: function() {
        if (this.isEditProjectNameSection || this.currentStepLabel === "project-name")
          return "open"
        else 
          return "completed"
      },
      clientSectionStatus: function() {
        if (this.isEditClientSection || this.currentStepLabel === "client")
          return "open"
        else if (this.currentStep < 2)
          return "closed"
        else
          return "completed"
      },
      projectTypeSectionStatus: function() {
        if (this.isEditProjectTypeSection || this.currentStepLabel === "project-type")
          return "open"
        else if (this.currentStep < 3)
          return "closed"
        else
          return "completed"
      },
      deviceSectionStatus: function(){
        if (this.isEditDeviceSection || this.currentStepLabel === "device")
          return "open"
        else if (this.currentStep < 4)
          return "closed"
        else
          return "completed" 
      },
      litProjectTypeSectionStatus: function(){
        if (this.isEditLitProjectTypeSection || this.currentStepLabel === "literature-type")
          return "open"
        else if (this.currentStep < 5)
          return "closed"
        else
          return "completed"   
      },
      copyDataSectionStatus: function(){
        if (this.isEditCopyData || this.currentStepLabel === "copy-data")
          return "open"
        else if (this.currentStep < 6)
          return "closed"
        else
          return "completed"   
      }
    },
    watch: {
      clientSearchTerm(newValue, oldValue) {
        if (newValue === "") {
          this.searchedClients = this.clients.map(client => client);
        } else {
          this.searchedClients = this.clients.filter(client => client.name.toLowerCase().includes(newValue.toLowerCase()));
        }
      },
      deviceSearchTerm(newValue, oldValue) {
        if (newValue === "") {
          this.searchedDevices = this.devices.map(device => device);;
        } else {
          this.searchedDevices = this.devices.filter(device => device.name.toLowerCase().includes(newValue.toLowerCase()));
        }
      },
      reviewSearchTerm(newValue, oldValue) {
        if (newValue === "") {
          this.searchedReviews = this.reviews.map(review => review);;
        } else {
          this.searchedReviews = this.reviews.filter(review => review.label.toLowerCase().includes(newValue.toLowerCase()));
        }
      },
    },
    methods : {
        // helpers

        // actions 
        onClientLogoChange(uploadedFile) {
          this.newClient.logo = uploadedFile;
        },
        onSwitchNewManufacturer(isNew){
          this.isNewManufacturer = isNew;
          this.newDevice.manufacturer = "";
        },
        goToNextStep() {
          if (this.currentStep < this.TOTAL_STEPS){
            this.currentStep += 1;
          }

          switch(this.currentStepLabel) {
            case "project-name":
              if (this.isUserClient)
                this.currentStepLabel = "project-type";
              else
                this.currentStepLabel = "client";
              break;
            case "client":
              this.currentStepLabel = "project-type";
              break;
            case "project-type":
              if (this.literatureReview.projectType === "SIMPLE")
                this.currentStepLabel = "completed";
              else
                this.currentStepLabel = "device";
              break;
            case "device":
              this.currentStepLabel = "literature-type";
              break;
            case "literature-type":
              this.currentStepLabel = "copy-data";
              break;
            case "copy-data":
              this.currentStepLabel = "completed";
              break;
            default:
              // code block
          }          
        },
        getClientWithID(clientID) {
          return this.clients.find(client => client.id === clientID);
        },
        getDeviceWithID(deviceID) {
          return this.devices.find(device => device.id === deviceID);
        },
        getReviewWithID(reviewID) {
          return this.reviews.find(review => review.id === reviewID);
        },

        // async
        // Change/Input Listeners
        onSelectClient(clientID){
          this.literatureReview.client = clientID;
        },
        onProjectTypeChange(projectType) {
          this.literatureReview.type = projectType;
          if (this.literatureReview.type === "SIMPLE") {
            this.$refs["device-section"].style.display = "none";
            this.$refs["project-type-section"].style.display = "none";
            this.$refs["copy-data-section"].style.display = "none";
            this.TOTAL_STEPS = this.isUserClient ? 2 : 3;
          } else {
            this.$refs["device-section"].style.display = "block";
            this.$refs["project-type-section"].style.display = "block";
            this.$refs["copy-data-section"].style.display = "block";
            this.TOTAL_STEPS = this.isUserClient ? 5 : 6;
          };
        },
        onChangeLitProjectType(litType) {
          this.literatureReview.projectType = litType;
        },
        onChangeIsCopyData(isCopy) {
          this.literatureReview.isCopyData = isCopy;
        },
        onChangeCopyDataFrom(copyFrom) {
          this.literatureReview.copyDataFrom = copyFrom;
        },
        
        // Forms
        onCreateClient(e) {
          e.preventDefault();
          const postData = new FormData();
          for (let key in this.newClient)
              postData.append(key, this.newClient[key]);
          
          this.isCreateClientLoading = true;
          axios.post(CreateClientAPI, data=postData)
          .then(
            res => {
                console.log(res);
                this.isCreateClientLoading = false;
                this.clients = [res.data, ...this.clients];
                this.searchedClients = [res.data, ...this.searchedClients];
                this.literatureReview.client = res.data.id;
                this.hideModal('create-client');
              },
              err => {
                console.log(err);
                this.isCreateClientLoading = false;
              }
            );
        },
        onCreateDevice(e) {
          e.preventDefault();
          
          this.isCreateDeviceLoading = true;
          axios.post(CreateDeviceAPI, data=this.newDevice)
          .then(
            res => {
                console.log(res);
                this.isCreateDeviceLoading = false;
                this.devices = [res.data, ...this.devices];
                this.searchedDevices = [res.data, ...this.searchedDevices];
                this.literatureReview.device = res.data.id;
                this.hideModal('create-device');
              },
              err => {
                this.isCreateDeviceLoading = false;
                console.log(err);
              }
            );
        },
        onCreateProject() {
          let postData = {}
          if (this.literatureReview.type === "STANDARD"){
            postData = {
              client : this.literatureReview.client,
              device :  this.literatureReview.device,
              review_type :  this.literatureReview.type,
              is_copy_data: this.literatureReview.isCopyData,
              project : {
                project_name : this.literatureReview.project.name,
                type : this.literatureReview.projectType,
                client : this.literatureReview.client,
              }
            }
            if (this.literatureReview.isCopyData)
              postData.copy_from_lit_id = this.literatureReview.copyDataFrom;
          } else if (this.literatureReview.type === "SIMPLE") {
            postData = {
              client : this.literatureReview.client,
              review_type :  this.literatureReview.type,
              project : {
                project_name : this.literatureReview.project.name,
                client : this.literatureReview.client,
              }
            }
          }

          this.isCreateProjectLoading = true;
          axios.post(CreateLiteratureReviewAPI, data=postData)
          .then(
            res => {
                console.log(res);
                const redirect = () => {
                  this.isCreateProjectLoading = false;
                  const redirectURL = this.onCompleteRedirectURL ? this.onCompleteRedirectURL : `/literature_reviews/${res.data.id}/`;
                  window.location = redirectURL;
                };

                if (this.literatureReview.isCopyData) {
                  // wait till copying is completed
                  HALF_MINUTE = 1000 * 30;
                  const TM = setTimeout(() => {
                    redirect();
                    return clearTimeout(TM);
                  }, HALF_MINUTE);
                }
                else redirect();
              },
              err => {
                this.isCreateProjectLoading = false;
                console.log(err);
              }
            );
        },
        loadDevices(selectedDeviceID) {
            // load Devices
            axios.get(DevicesListAPI)
              .then(
                res => {
                  console.log(res);
                  this.devices = res.data;
                  this.searchedDevices = res.data;
                  if (this.loadAndSelectDeviceID) this.loadAndSelectDevice(this.loadAndSelectDeviceID);
                },
                err => {
                  console.log(err);
                }
              );
        },
        loadAndSelectDevice(deviceID) {
          let URL = GetDevicesAPI.replace("/0/", `/${deviceID}/`)
          this.axiosGet(
            url=URL,
            isLoadingKey = "",
            callBack = (resData) => {
              const deviceIndex = this.devices.findIndex(device => device.id === resData.id);
              const deviceNotFound = deviceIndex < 0;
              if (deviceNotFound) {
                this.devices = [resData, ...this.devices];
                this.searchedDevices = [resData, ...this.searchedDevices];
              }
              this.literatureReview.device = resData.id;
            },
          );
        },
        loadManufacturers() {
          // load Devices
          axios.get(ManufacturerListAPI)
            .then(
              res => {
                console.log(res);
                this.manufacturers = res.data;
              },
              err => {
                console.log(err);
              }
            );
        },
        loadClients() {
            // load Clients
            axios.get(ClientsListAPI)
              .then(
                res => {
                  console.log(res);
                  this.clients = res.data;
                  this.searchedClients = res.data;
                },
                err => {
                  console.log(err);
                  // current user is a client
                  if (err.response.status === 403) {
                    this.isUserClient = true;
                    this.$refs["client-section"].style.display = "none";
                    this.TOTAL_STEPS = 5;
                  }
                }
              );
        },
        loadReview() {
            // load reviews
            axios.get(LiteratureReviewListAPI)
              .then(
                res => {
                  console.log(res);
                  this.reviews = res.data;
                  this.searchedReviews =res.data;
                },
                err => {
                  console.log(err);
                }
              );
        }
    },
    mounted() {
    // check if there is  a default device that should be created
    const params = new URLSearchParams(window.location.search);
    const device = params.get("device");
    const redirectURL = params.get("redirect_url");
    if(device) this.loadAndSelectDeviceID = device;
    if(redirectURL) this.onCompleteRedirectURL = `${redirectURL}?device=${device}`;

    this.loadDevices();
    this.loadManufacturers();
    this.loadReview();
    this.loadClients();

    // replace with default logo image if src img is not found
    const clientLogo = document.getElementById("client-img");
    clientLogo.addEventListener("error", function(event) {
      event.target.src = DEFAULT_CLIENT_LOGO;
      event.onerror = null;
    })  
  }
})
