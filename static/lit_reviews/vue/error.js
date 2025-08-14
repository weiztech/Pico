axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

// Define global functions first
function showPopup() {
    const popup = document.getElementById("reportbug-popup");
    if (popup) {
        popup.style.display = "flex";
    }
    // Reset errors when opening popup
    if (window.app) {
        window.app.resetSupportForm();
    }
}

function hidePopup() {
    const popup = document.getElementById("reportbug-popup");
    if (popup) {
        popup.style.display = "none";
    }
    // Reset form through Vue app
    if (window.app) {
        window.app.hidePopup();
    }
}

var app = new Vue({
    el: '#error-app',
    delimiters: ["[[", "]]"],
    mixins: [globalMixin],
    data() {
        return {
            supportForm: {
                description: '',
                demo_video: '',
                follow_up_option: 'email'
            },
            formErrors: [],
            submitSuccess: false,
            isSubmitting: false
        }
    },
    computed: {
        isFormValid() {
            // Check basic required fields
            const hasDescription = this.supportForm.description.trim().length > 0;
            const hasFollowUpOption = this.supportForm.follow_up_option;
            
            // Check URL validity if URL is provided
            let isUrlValid = true;
            if (this.supportForm.demo_video && this.supportForm.demo_video.trim()) {
                isUrlValid = this.isValidUrl(this.supportForm.demo_video);
            }
            
            return hasDescription && hasFollowUpOption && isUrlValid;
        },
        isButtonDisabled() {
            return this.isSubmitting || !this.isFormValid;
        }
    },
    methods: {
        isValidUrl(string) {
            if (!string || !string.trim()) {
                return true; // Empty string is valid (optional field)
            }
            
            let url = string.trim();
            
            // If URL doesn't start with http:// or https://, add https://
            if (!url.startsWith('http://') && !url.startsWith('https://')) {
                url = 'https://' + url;
            }
            
            try {
                const urlObj = new URL(url);
                // Check if it has a valid domain
                return urlObj.hostname && urlObj.hostname.includes('.');
            } catch (e) {
                return false;
            }
        },
        
        normalizeUrl(string) {
            if (!string || !string.trim()) {
                return '';
            }
            
            let url = string.trim();
            
            // If URL doesn't start with http:// or https://, add https://
            if (!url.startsWith('http://') && !url.startsWith('https://')) {
                url = 'https://' + url;
            }
            
            return url;
        },
        
        validateSupportForm() {
            this.formErrors = [];
            
            // Check if description is not empty
            if (!this.supportForm.description.trim()) {
                this.formErrors.push('Please describe how we can help you.');
            }
            
            // Check if follow-up option is selected
            if (!this.supportForm.follow_up_option) {
                this.formErrors.push('Please select a follow-up option.');
            }
            
            // Validate video URL if provided
            if (this.supportForm.demo_video && this.supportForm.demo_video.trim()) {
                if (!this.isValidUrl(this.supportForm.demo_video)) {
                    this.formErrors.push('Please provide a valid video URL (e.g., www.loom.com/share/... or https://youtu.be/...)');
                }
            }
            
            return this.formErrors.length === 0;
        },
        
        submitSupportForm() {
            this.submitSuccess = false;
            this.formErrors = [];
            
            if (!this.validateSupportForm()) {
                return;
            }
            
            this.isSubmitting = true;
            
            const formData = new FormData();
            formData.append('description', this.supportForm.description);
            
            // Normalize the URL before sending
            const normalizedUrl = this.normalizeUrl(this.supportForm.demo_video);
            formData.append('demo_video', normalizedUrl);
            
            formData.append('follow_up_option', this.supportForm.follow_up_option);
            
            return axios.post(SupportTicketUrl, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                }
            })
            .then(
                res => {
                    console.log(res);
                    if (res.data.success) {
                        this.submitSuccess = true;
                        this.makeToast("success", "Support request submitted successfully. We'll get back to you soon.");
                        this.resetSupportForm();
                                                    this.hidePopup();
                                            } else {
                        this.formErrors = res.data.errors || ['An error occurred while submitting your request.'];
                        this.makeToast("danger", "Failed to submit support request. Please try again.");
                    }
                    this.isSubmitting = false;
                },
                err => {
                    console.log(err);
                    let error_msg = this.handleErrors(err);
                    this.makeToast("danger", error_msg);
                    
                    if (err.response && err.response.data && err.response.data.errors) {
                        this.formErrors = err.response.data.errors;
                    } else {
                        this.formErrors = ['Network error. Please try again later.'];
                    }
                    this.isSubmitting = false;
                }
            );
        },
        
        resetSupportForm() {
            this.supportForm = {
                description: '',
                demo_video: '',
                follow_up_option: 'email'
            };
            this.formErrors = [];
            this.submitSuccess = false;
            this.isSubmitting = false;
        },
        
        hidePopup() {
            const popup = document.getElementById("reportbug-popup");
            if (popup) {
                popup.style.display = "none";
            }
            this.resetSupportForm();
        }
    },
    mounted() {
        // Make the app instance available globally
        window.app = this;
        
        // Setup window click listener to close popup when clicking outside
        window.addEventListener('click', (e) => {
            const popup = document.querySelector('#reportbug-popup');
            const popupContent = document.querySelector('#reportbug-popup .modal-content');
            const reportButton = document.querySelector('#report-bug-btn');
            
            // Check if all elements exist before checking contains
            if (popup && popupContent && reportButton) {
                // If popup is visible and click is outside the popup content and not on the report button
                if (popup.style.display === 'flex' && 
                    !popupContent.contains(e.target) && 
                    !reportButton.contains(e.target)) {
                    this.hidePopup();
                }
            }
        });
    }
})
