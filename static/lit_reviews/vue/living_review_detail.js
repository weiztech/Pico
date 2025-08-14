axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";

var app = new Vue({
  el: '#living-review-detail',
  mixins: [globalMixin],
  components: {
    'drop-down': DropDown,
    'toast': Toast,
    'custom-select': CustomSelect,
  },
  delimiters: ["[[", "]]"],
  data() {
    return {
      isRecordsLoading: true,
      livingReviewId: null,
      livingReview: null,
      latestLiteratureReviews: [],
      selectedLiteratureReviewArticles: [],
      ResulsLoading: false,
      collapse: false,
      selectedReviews: [],
      selectedProjectID: null,
      isAutoUpdate: false,
      isConfigurationLoading: false, // Add this line

      // filters 
      searchTerm: "",
      selectedStartDate: "",
      selectedEndDate: "",
      dbs: [],
      selectedDatabases: [],
      deviceMentionsFilter: "",

      devices: [],
      manufacturers: [],
      
      // New device creation
      newDevice: {
        name: "",
        manufacturer: "",
        classification: "",
        markets: "",
      },
      isNewManufacturer: false,
      isCreateDeviceLoading: false,

      // Device configuration
      activeDeviceTab: 'evaluation',
      deviceSearchTerm: "",
      similarDevicesSearchTerm: "",
      competitorDevicesSearchTerm: "",

      // Notification types
      notificationsTypes: [
        {value: "under_evaluation", description: "I want notifications of articles mentioning my product"},
        {value: "competitor", description: "I want notifications on articles mentioning similar products"},
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
    };
  },
  computed: {
    hasSelectedArticles() {
      return this.selectedLiteratureReviewArticles.length > 0;
    },
    // selectedSearch() {
    //   return this.searchesHistory?.find(search => search.id === this.selectedSearchId);
    // },
    selectedProject() {
      return this.latestLiteratureReviews.find(review => review.id === this.selectedProjectID);
    },
    isCheckAll() {
      return this.selectedReviews?.length === this.selectedLiteratureReviewArticles.length;
    },
    isFiltersApplied() {
      if (this.selectedStartDate || this.selectedEndDate || this.selectedDatabases.length || this.deviceMentionsFilter) return true;
      else return false;
    },
    searchedDevices() {
      if (!this.deviceSearchTerm) {
        return this.devices;
      }
      return this.devices.filter(device => 
        device.name.toLowerCase().includes(this.deviceSearchTerm.toLowerCase()) ||
        device.manufacturer.toLowerCase().includes(this.deviceSearchTerm.toLowerCase())
      );
    },
    searchedSimilarDevices() {
      if (!this.similarDevicesSearchTerm) {
        return this.devices;
      }
      return this.devices.filter(device => 
        device.name.toLowerCase().includes(this.similarDevicesSearchTerm.toLowerCase()) ||
        device.manufacturer.toLowerCase().includes(this.similarDevicesSearchTerm.toLowerCase())
      );
    },
    searchedCompetitorDevices() {
      if (!this.competitorDevicesSearchTerm) {
        return this.devices;
      }
      return this.devices.filter(device => 
        device.name.toLowerCase().includes(this.competitorDevicesSearchTerm.toLowerCase()) ||
        device.manufacturer.toLowerCase().includes(this.competitorDevicesSearchTerm.toLowerCase())
      );
    },
    isCreateDeviceValid() {
      return this.newDevice.name && 
             this.newDevice.manufacturer && 
             this.newDevice.classification && 
             this.newDevice.markets;
    },
  },
  methods: {
    toogleIsCheckAll() {
      if (this.selectedReviews?.length === this.selectedLiteratureReviewArticles.length) {
        this.selectedReviews = [];
      } else {
        this.selectedReviews = this.selectedLiteratureReviewArticles.map(review => review.id);
      }
    },
    collapseMenu() {
      this.collapse = !this.collapse;
    },
    applyURLFilters(URL) {
      if (this.searchTerm) {
        if (URL.includes("?")) {
          URL = `${URL}&search=${this.searchTerm}`;
        } else {
          URL = `${URL}?search=${this.searchTerm}`;
        }
      }

      if (this.selectedDatabases.length) {
        const dbs = this.selectedDatabases.join(",")
        if (URL.includes("?"))
          URL =  `${URL}&db=${dbs}`;
        else
          URL =  `${URL}?db=${dbs}`;
      };

      if (this.selectedStartDate) {
        if (URL.includes("?"))
          URL =  `${URL}&start_date=${this.selectedStartDate}`;
        else
          URL =  `${URL}?start_date=${this.selectedStartDate}`;
      };

      if (this.selectedEndDate) {
        if (URL.includes("?"))
          URL =  `${URL}&end_date=${this.selectedEndDate}`;
        else
          URL =  `${URL}?end_date=${this.selectedEndDate}`;
      };

      if (this.deviceMentionsFilter) {
        if (URL.includes("?"))
          URL =  `${URL}&device_mention=${this.deviceMentionsFilter}`;
        else
          URL =  `${URL}?device_mention=${this.deviceMentionsFilter}`;
      };

      return URL;
    },
    onClearFilters() {
      this.searchTerm = "";
      this.selectedStartDate = "";
      this.selectedEndDate = "";
      this.selectedDatabases = [];
      this.deviceMentionsFilter = "";
      this.fetchLivingReviewArticles(this.selectedProjectID);

      // clear device mentions filter UI
      const underFilterElm = this.$refs["under-evaluation-filter"];
      const similarFilterElm = this.$refs["similar-devices-filter"];
      const competitorFilterElm = this.$refs["competitor-devices-filter"];
      underFilterElm.classList.remove("active");
      similarFilterElm.classList.remove("active");
      competitorFilterElm.classList.remove("active");
    },
    onApplyFilters(event) {
      event.preventDefault();
      this.onCloseFilters();
      this.fetchLivingReviewArticles(this.selectedProjectID);
    },
    formatDjangoDate(djangoDateStr) {
      const date = new Date(djangoDateStr);
      const timeOptions = { hour: 'numeric', minute: 'numeric', hour12: true };
      const dateOptions = { year: 'numeric', month: 'short', day: 'numeric' };
      const formattedTime = new Intl.DateTimeFormat('en-US', timeOptions).format(date);
      const formattedDate = new Intl.DateTimeFormat('en-US', dateOptions).format(date);
      return `${formattedTime} / ${formattedDate}`;
    },
    truncateText(text, caracterNumber) {
      return text.length > caracterNumber ? text.slice(0, caracterNumber) + '...' : text;
    },
    onCloseFilters() {
      this.hideModal('filters-slider');
    },

    // Method to close review configuration slider
    onCloseReviewConfiguration() {
      this.hideModal('review-configuration-slider');
    },

    // Method to save review configuration
    onSaveReviewConfiguration() {
      const {
        device, similar_devices, competitor_devices, interval, alert_type 
      } = this.livingReview;

      let putData = {
        device: device?.id || device,
        similar_devices: similar_devices?.map(d => d.id) || [],
        competitor_devices: competitor_devices?.map(d => d.id) || [],
        interval,
        alert_type: alert_type === 'no' ? '' : alert_type,
      };

      console.log('Updating review configuration...', putData);
      
      // Show loading state (you can add a loading variable if needed)
      this.isConfigurationLoading = true;
      
      const updateUrl = LivingReviewUpdateAPI.replace("/0/", `/${this.livingReview.id}/`);
      
      axios.put(updateUrl, putData)
        .then(
          res => {
            console.log('Configuration updated successfully:', res);
            this.isConfigurationLoading = false;
            this.hideModal('review-configuration-slider');
            this.makeToast("success", "Review configuration updated successfully!");
            
            // Update the local livingReview data with the response
            this.livingReview = res.data;
          },
          err => {
            this.isConfigurationLoading = false;
            console.log('Error updating configuration:', err);
            const errorMsg = this.handleErrors(err);
            this.makeToast("error", errorMsg || "Failed to update review configuration");
          }
        );
    },

    // Similar Device Methods
    isSimilarDeviceSelected(deviceId) {
      return this.livingReview?.similar_devices?.some(device => device.id === deviceId) || false;
    },

    onToggleSimilarDevice(deviceId) {
      if (!this.livingReview.similar_devices) {
        this.livingReview.similar_devices = [];
      }
      
      const index = this.livingReview.similar_devices.findIndex(device => device.id === deviceId);
      
      if (index > -1) {
        // Remove device if already selected
        this.livingReview.similar_devices.splice(index, 1);
      } else {
        // Add device if not selected
        const device = this.devices.find(d => d.id === deviceId);
        if (device) {
          this.livingReview.similar_devices.push(device);
        }
      }
    },

    // Competitor Device Methods
    isCompetitorDeviceSelected(deviceId) {
      return this.livingReview?.competitor_devices?.some(device => device.id === deviceId) || false;
    },

    onToggleCompetitorDevice(deviceId) {
      if (!this.livingReview.competitor_devices) {
        this.livingReview.competitor_devices = [];
      }
      
      const index = this.livingReview.competitor_devices.findIndex(device => device.id === deviceId);
      
      if (index > -1) {
        // Remove device if already selected
        this.livingReview.competitor_devices.splice(index, 1);
      } else {
        // Add device if not selected
        const device = this.devices.find(d => d.id === deviceId);
        if (device) {
          this.livingReview.competitor_devices.push(device);
        }
      }
    },

    // Async Functions
    onSelectProject(id) {
      // Unselect previously selected one
      this.selectedProjectID = id;
      this.fetchLivingReviewArticles();
    },
    async fetchLivingReviewArticles() {
      this.ResulsLoading = true;

      // Fetch article reviews for the selected literature review
      try {
        let url = ArticleReviewListURL.replace("/0/", `/${this.selectedProjectID}/`);
        url = this.applyURLFilters(url);

        const response = await axios.get(url);
        console.log("Article Reviews Data:", response.data);
        this.selectedLiteratureReviewArticles = response.data; // Update the articles list
        this.ResulsLoading = false;
      } catch (err) {
        console.error("Error fetching article reviews:", err);
        this.selectedLiteratureReviewArticles = []; // Reset articles on error
        this.ResulsLoading = false;
      }
    },
    async loadLivingReviewData(livingReviewId) {
      try {
        const url = LivingReviewDetailURL.replace("/0/", `/${livingReviewId}/`)
        const res = await axios.get(url);
        console.log("Living Review Data:", res.data);
        this.livingReview = res.data;
        this.latestLiteratureReviews = res.data.latest_literature_reviews;
        this.isRecordsLoading = false;
        // Auto-select the first literature review if any exist
      if (this.latestLiteratureReviews && this.latestLiteratureReviews.length > 0) {
        for (let project of this.latestLiteratureReviews)
          if (!project.is_missing) {
            this.onSelectProject(project.id);
            break;
          }
            
      }
      } catch (err) {
        console.error("Error loading living review data:", err);
        this.isRecordsLoading = false;
      }
    },
    onChangeTimeInterval(newValue) {
      this.livingReview.interval = newValue;
    },
    onChangeNotificationType(notificationType) {
      if (this.livingReview) {
        this.livingReview.alert_type = notificationType;
      }
    },
    onFilterWithMentions(deviceType) {
      this.deviceMentionsFilter = deviceType;
      const underFilterElm = this.$refs["under-evaluation-filter"]
      const similarFilterElm = this.$refs["similar-devices-filter"]
      const competitorFilterElm = this.$refs["competitor-devices-filter"]
      
      if (deviceType === "under") {
        underFilterElm.classList.add("active");
        similarFilterElm.classList.remove("active");
        competitorFilterElm.classList.remove("active");
      } else if (deviceType === "similar") {
        underFilterElm.classList.remove("active");
        similarFilterElm.classList.add("active");
        competitorFilterElm.classList.remove("active");
      } else {
        underFilterElm.classList.remove("active");
        similarFilterElm.classList.remove("active");
        competitorFilterElm.classList.add("active");
      };

      this.fetchLivingReviewArticles();
    },
    loadDevices() {
      // load Devices
      axios.get(DevicesListAPI)
        .then(
          res => {
            console.log(res);
            this.devices = res.data;
          },
          err => {
            console.log(err);
          }
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
    onSelectEvaluationDevice(deviceId) {
      // Find the selected device from the devices list
      const selectedDevice = this.devices.find(device => device.id === deviceId);
      if (selectedDevice) {
        // Update the living review device
        this.livingReview.device = selectedDevice;
      }
    },
    onCreateDevice(e) {
      e.preventDefault();

      this.isCreateDeviceLoading = true;
      axios.post(CreateDeviceAPI, this.newDevice)
        .then(
          res => {
            console.log(res);
            this.isCreateDeviceLoading = false;
            this.devices = [res.data, ...this.devices];
            // Set the newly created device as selected
            this.livingReview.device = res.data;
            this.hideModal('create-device');
            // Reset the form
            this.newDevice = {
              name: "",
              manufacturer: "",
              classification: "",
              markets: "",
            };
          },
          err => {
            this.isCreateDeviceLoading = false;
            console.log(err);
          }
        );
    },
    onSwitchNewManufacturer(isNew) {
      this.isNewManufacturer = isNew;
      if (!isNew) {
        this.newDevice.manufacturer = "";
      }
    },
  },
  mounted() {
    const livingReviewId = window.location.pathname.split('/').filter(Boolean).pop(); // Extract ID from URL
    this.loadLivingReviewData(livingReviewId);
    this.loadDatabases() // mixins method
    this.loadDevices();
    this.loadManufacturers();

    const timeOut = setTimeout(() => {
      this.styleTooltips();
      clearTimeout(timeOut);
    }, 2000);
  }
});
