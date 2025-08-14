// axios.defaults.xsrfCookieName = 'csrftoken'
// axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
  el: '#app',
  delimiters: ["[[", "]]"],
  mixins: [globalMixin],
  data() {
    return {
      devices: [],
      manufacturers: [],
      clients: [],
      reviews: [],
      searchedDevices: [],
      searchedCompetitorDevices: [],
      searchedSimilarDevices: [],
      searchedClients: [],
      searchedReviews: [],
      CreateLiteratureReviewURL: CreateLiteratureReviewURL,
      CreateLivingReviewPageURL: CreateLivingReviewPageURL,

      clientSearchTerm: "",
      deviceSearchTerm: '',
      reviewSearchTerm: '',
      competitorDevicesSearchTerm: '',
      similarDevicesSearchTerm: '',

      currentStep: 1,
      TOTAL_STEPS: 5,
      currentStepLabel: "device",
      // steps : device - protocol - additional-devices - interval - notifications

      isEditDeviceSection: false,
      isEditProtocol: false,
      isEditAdditionalDevices: false,
      isEditInterval: false,
      isEditNotifications: false,

      newDevice: {
        name: "",
        manufacturer: "",
        classification: "",
        markets: "",
      },
      isNewManufacturer: false,
      livingReview: {
        device: null,
        protocol: null,
        similarDevices: [],
        competitorDevices: [],
        interval: "",
        startDate: "",
        notification: "",
      },
      notificationsTypes: [
        {value: "under_evaluation", description: "I want notifications of articles mentioning my product"},
        {value: "competitor", description: "I what notifications on articles mentioning similar products"},
        {value: "similar", description: "I want notifications on articles mentioning my competitors"},
        {value: "all", description: "I want notifications on all the above"},
      ],
      intervalOptions: [
        {name:"Select time interval", value: ""},
        {name:"Weekly", value: "weekly"},
        {name:"Monthly", value: "monthly"},
        {name:"Quarterly", value: "quarterly"},
        {name:"Annualy", value: "annually"},

      ],

      isCreateDeviceLoading: false,
      isCreateClientLoading: false,
      isCreateProjectLoading: false,
    }
  },
  computed: {
    progressPerccentage: function () {
      return parseInt((this.currentStep / this.TOTAL_STEPS) * 100);
    },
    // forms validation
    isCreateDeviceValid: function () {
      if (this.isCreateDeviceLoading)
        return false;

      for (let key in this.newDevice) {
        if (!this.newDevice[key])
          return false;
      }

      return true;
    },
    
    // steps status if (closed or opened)
    selectDeviceStatus: function () {
      if (this.isEditDeviceSection || this.currentStepLabel === "device")
        return "open"
      else
        return "completed"
    },
    selectProtocolStatus: function () {
      if (this.isEditProtocol || this.currentStepLabel === "protocol")
        return "open"
      else if (this.currentStep < 2)
        return "closed"
      else
        return "completed"
    },
    selectAdditionalDevices: function () {
      if (this.isEditAdditionalDevices || this.currentStepLabel === "additional-devices")
        return "open"
      else if (this.currentStep < 3)
        return "closed"
      else
        return "completed"
    },
    selectIntervalStatus: function () {
      if (this.isEditInterval || this.currentStepLabel === "interval")
        return "open"
      else if (this.currentStep < 4)
        return "closed"
      else
        return "completed"
    },
    setNotificationsStatus: function () {
      if (this.isEditNotifications || this.currentStepLabel === "notifications")
        return "open"
      else if (this.currentStep < 5)
        return "closed"
      else
        return "completed"
    },
    isCreateLivingReviewValid: function() {
      return this.livingReview.device && this.livingReview.protocol && this.livingReview.notification 
      && this.livingReview.interval && this.livingReview.startDate;
    },  
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
    competitorDevicesSearchTerm(newValue, oldValue) {
      if (newValue === "") {
        this.searchedCompetitorDevices = this.devices.map(device => device);;
      } else {
        this.searchedCompetitorDevices = this.devices.filter(device => device.name.toLowerCase().includes(newValue.toLowerCase()));
      }
    },
    similarDevicesSearchTerm(newValue, oldValue) {
      if (newValue === "") {
        this.searchedSimilarDevices = this.devices.map(device => device);;
      } else {
        this.searchedSimilarDevices = this.devices.filter(device => device.name.toLowerCase().includes(newValue.toLowerCase()));
      }
    },
    'livingReview.device': function (newVal, oldVal){
      this.loadReview(newVal);
    },
  },
  methods: {
    // helpers

    // actions 
    onDeviceUpdated() {
      this.isEditDeviceSection=false;
      this.livingReview.protocol = "";
      this.isEditProtocol = true;
    },
    onChangeTimeInterval(newValue) {
      this.livingReview.interval = newValue;
    },
    onClientLogoChange(uploadedFile) {
      this.newClient.logo = uploadedFile;
    },
    onSwitchNewManufacturer(isNew) {
      this.isNewManufacturer = isNew;
      this.newDevice.manufacturer = "";
    },
    goToNextStep() {
      if (this.currentStep < this.TOTAL_STEPS) {
        this.currentStep += 1;
      }
      switch (this.currentStepLabel) {
        case "device":
          this.currentStepLabel = "protocol";
          break;
        case "protocol":
          this.currentStepLabel = "additional-devices";
          break;
        case "additional-devices":
          this.currentStepLabel = "interval";
          break;
        case "interval":
          this.currentStepLabel = "notifications";
          break;
        case "notifications":
          this.currentStepLabel = "";
          break;
        default:
          this.currentStepLabel = "";
          break;
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
    formatDateUSA(dateString) {
      // take dateString in format YY-mm-dd return YY/dd/mm
      const [year, month, day] = dateString.split('-');
      const formatted = `${month}/${day}/${year}`;
      return formatted;
    },

    // async
    // Change/Input Listeners
    onSelectClient(clientID) {
      this.livingReview.client = clientID;
    },

    // Forms
    onCreateClient(e) {
      e.preventDefault();
      const postData = new FormData();
      for (let key in this.newClient)
        postData.append(key, this.newClient[key]);

      this.isCreateClientLoading = true;
      axios.post(CreateClientAPI, data = postData)
        .then(
          res => {
            console.log(res);
            this.isCreateClientLoading = false;
            this.clients = [res.data, ...this.clients];
            this.searchedClients = [res.data, ...this.searchedClients];
            this.livingReview.client = res.data.id;
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
      axios.post(CreateDeviceAPI, data = this.newDevice)
        .then(
          res => {
            console.log(res);
            this.isCreateDeviceLoading = false;
            this.devices = [res.data, ...this.devices];
            this.searchedDevices = [res.data, ...this.searchedDevices];
            this.livingReview.device = res.data.id;
            this.hideModal('create-device');
          },
          err => {
            this.isCreateDeviceLoading = false;
            console.log(err);
          }
        );
    },
    onCreateLivingReview() {
      const {
        device, protocol, similarDevices, competitorDevices, interval, startDate, notification 
      } = this.livingReview;

      let postData = {
        device,
        project_protocol: protocol,
        similar_devices: similarDevices,
        competitor_devices: competitorDevices,
        interval,
        start_date: startDate,
        alert_type: notification === 'no' ? '' : notification,
      } ;

      this.isCreateProjectLoading = true;
      axios.post(CreatelivingReviewAPI, data = postData)
        .then(
          res => {
            console.log(res);
            window.location = LivingReviewsListView;
          },
          err => {
            this.isCreateProjectLoading = false;
            console.log(err);
            const errorMsg = this.handleErrors(err);
            this.makeToast("error", errorMsg);
          }
        );
    },
    loadDevices() {
      // load Devices
      axios.get(DevicesListAPI)
        .then(
          res => {
            console.log(res);
            this.devices = res.data;
            this.searchedDevices = res.data;
            this.searchedCompetitorDevices = res.data;
            this.searchedSimilarDevices = res.data;
            
            if (this.defaultSelectedDeviceID) {
              const selectedDevice = parseInt(this.defaultSelectedDeviceID);
              const deviceIndex = this.devices.findIndex(device => device.id === selectedDevice);

              const isDeviceFound = deviceIndex > -1;
              if (isDeviceFound) {
                this.livingReview.device = selectedDevice;
                this.goToNextStep();
              } else this.loadAndSelectDevice(selectedDevice);
            }
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
          this.devices = [resData, ...this.devices];
          this.searchedDevices = [resData, ...this.searchedDevices];
          this.livingReview.device = resData.id;
          this.goToNextStep();
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
    loadReview(deviceID) {
      // load reviews
      let URL = reviewListAPI;
      if (deviceID) 
        URL = `${URL}?device=${deviceID}&exclude_living=true`;

      axios.get(URL)
        .then(
          res => {
            console.log(res);
            this.reviews = res.data;
            this.searchedReviews = res.data;
          },
          err => {
            console.log(err);
          }
        );
    }
  },
  mounted() {
    const params = new URLSearchParams(window.location.search);
    const device = params.get("device");
    this.defaultSelectedDeviceID = device;

    this.loadDevices();
    this.loadManufacturers();
    this.loadClients();

    const timeOut = setTimeout(() => {
      this.styleTooltips();
      return clearTimeout(timeOut);
    }, 2000);
  }
})
