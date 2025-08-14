axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";

var app = new Vue({
    el: '#living-reviews',
    mixins: [globalMixin],
    delimiters: ["[[", "]]"],
    data() {
        return {
            livingReviews: [],
            filteredReviews: [],
            count: 0,
            isPageLoading: false,
            isCheckAll: false,
            searchTerm: '',
            selectedDevices: [],
            selectedIntervals: [],
            isFiltersApplied: false,
            devices: [], 
            intervals: ["weekly", "monthly", "quarterly", "annually"]
        };
    },
    methods: {
        fetchLivingReviews() {
            this.isPageLoading = true;
            axios.get(LivingReviewURL)
                .then(response => {
                    this.livingReviews = response.data;
                    this.filteredReviews = this.livingReviews; // Initialize filtered reviews
                    this.extractDevices(); // Extract unique devices from livingReviews
                    console.log("Living reviews data:", this.livingReviews);
                    this.count = this.livingReviews.length;
                })
                .catch(error => {
                    console.error("Error fetching living reviews:", error);
                })
                .finally(() => {
                    this.isPageLoading = false;
                });
        },
        extractDevices() {
            // Extract unique devices from livingReviews
            const deviceSet = new Set();
            this.livingReviews.forEach(review => {
                if (review.device) {
                    deviceSet.add(review.device);
                }
            });
            this.devices = Array.from(deviceSet).sort(); // Convert to sorted array
            console.log("Extracted devices:", this.devices);
        },
        onSearch(e) {
            e.preventDefault();
            const term = this.searchTerm.toLowerCase();
            this.filteredReviews = this.filteredReviews.filter(review =>
                review.device.name.toLowerCase().includes(term)
            );
        },
        onClearFilters() {
            this.searchTerm = '';
            this.selectedDevices = [];
            this.selectedIntervals = [];
            this.isFiltersApplied = false;
            this.filteredReviews = this.livingReviews; // Reset to all reviews
        },
        toggleCheckAll() {
            this.isCheckAll = !this.isCheckAll;
            this.filteredReviews.forEach(review => {
                review.isChecked = this.isCheckAll;
            });
        },
        onCloseFilters() {
            this.hideModal('filters-slider');
        },
        onFilter() {
            console.log("Selected Devices:", this.selectedDevices);
            console.log("Selected Intervals:", this.selectedIntervals);

            // Combine both filters into one filter operation
            this.filteredReviews = this.livingReviews.filter(review => {
                const matchesDevice = this.selectedDevices.length === 0 || this.selectedDevices.includes(review.device.name);
                const matchesInterval = this.selectedIntervals.length === 0 || this.selectedIntervals.includes(review.interval);
                const matchesSearch = review.device.name.toLowerCase().includes(this.searchTerm.toLowerCase());
                return matchesDevice && matchesInterval && matchesSearch;
            });

            console.log("Filtered Reviews:", this.filteredReviews);

            // Update filter state
            this.isFiltersApplied = true;

            // Close the modal after filtering
            this.hideModal("filters-slider");
        },
    },
    computed: {
        selectedCount() {
            return this.filteredReviews.filter(review => review.isChecked).length;
        }
    },
    mounted() {
        this.fetchLivingReviews();
    }
});
