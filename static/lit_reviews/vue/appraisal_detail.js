axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';  // Note the capitalization
axios.defaults.withCredentials = true;

var app = new Vue({
  el: '#appraisal_detail',
  mixins: [globalMixin],
  delimiters: ["[[", "]]"],
  data() {
    return {
      currentTab: "article-details",
      isSubExtractionLoading: false,
      subExtractions: [1],
      isHighlightPDFLoading: false,
      menuNavItems: [
        {
          id: 'article-details',
          displayName: 'Article Abstract'
        },
        {
          id: 'suitability-outcomes',
          displayName: 'Suitability and Outcomes'
        },
        {
          id: 'inclusion-sota',
          displayName: 'Inclusion and Device/Sota Decision'
        },
        {
          id: 'quality-contribution',
          displayName: 'Quality and Contribution Questions'
        },
        {
          id: 'mdcg-ranking',
          displayName: 'MDCG Ranking'
        },
        {
          id: 'sota',
          displayName: 'SoTA'
        },
        {
          id: 'extra-extraction-fields',
          displayName: 'Extraction Fields'
        },
        {
          id: 'justification-fields',
          displayName: 'Exclusion Justification'
        },
      ],
      currentAppraisalId: currentAppraisalId,  // Current appraisal ID
      nextAppraisalId: null,     // Next appraisal ID
      previousAppraisalId: null, // Previous appraisal ID 
      currentSorting: currentSorting || "article_review__article__title",
      searchTitle: searchTitle || "",
      filterStatus: filterStatus || "",
      filterIsSota: filterIsSota || "",
      filterIsCk3: filterIsCk3 || "",
      formFields: {
        included: '',
        is_sota_article: '',
        suitabilityOutcomes: [], // SO section
        stateOfTheArt: [], // ST section
        extractionFields: [], // EF section
        qualityContribution: [], // QC section
        mdcgRanking: [], // MR section
      },
      formValues: {
        included: '',
        is_sota_article: '',
        justification: '',
      },
      article_review: null,
      showSota: false,
      showDevice: false,
      showJustification: false,
      inactiveNavs: {
        'quality-contribution': false,
        'mdcg-ranking': false,
        'sota': false,
        'extra-extraction-fields': false,
        'justification-fields': false
      },
      showPdfViewer: false,
      pdfUrl: null,
      aiFieldsGenerated: false, // Track if AI fields have been generated
      aiStatuses: {}, // Track AI status for each field
      originalValues: {}, // Store original values before AI generation
      aiLoading: false,
      isRecordsLoading: false,
      searchTerm: {
        text: '',
        expanded: false,
        isLong: false
      },
      aiStatus: 'not_started', // 'not_started', 'running', 'completed', 'failed'
    }
  },
  computed: {
    getCurrentTab() {
      return this.currentTab
    },
    groupedExtractionFields() {
      const groups = {};
      const orderedFields = this.formFields.extractionFields.sort((a, b) => b.field_type.localeCompare(a.field_type)).map(item => item.name);
      const orderedFieldsUnique = [...new Set(orderedFields)];
      // [
      //   'device_name',
      //   'indication',
      //   'study_conclusions',
      //   'treatment_modality',
      //   'objective',
      //   'total_sample_size',
      //   'study_design',
      //   'adverse_events',
      //   'performance',
      //   'safety',
      //   'other'
      // ];

      // Group fields by their label
      this.formFields.extractionFields.forEach(field => {
        if (!groups[field.name]) {
          groups[field.name] = {
            label: field.name,
            fields: []
          };
        }
        groups[field.name].fields.push(field);
      });

      // Sort fields within each group by extraction_field_number
      Object.values(groups).forEach(group => {
        group.fields.sort((a, b) => a.extraction_field_number - b.extraction_field_number);
      });

      // Return groups in specified order
      if (orderedFieldsUnique) {
        return orderedFieldsUnique
          .filter(label => groups[label])
          .map(label => groups[label]);
      } else []

    },
    displayedSearchTerm() {
      if (!this.searchTerm.text) return '';

      if (this.searchTerm.expanded || !this.searchTerm.isLong) {
        return this.searchTerm.text;
      } else {
        return this.searchTerm.text.slice(0, 45);
      }
    }
  },
  methods: {
    setCurrentTab(tab) {
      this.currentTab = tab
    },
    showLoadingPopup: function () {
      const popup = document.getElementById("loading-section");
      if (popup) popup.style.display = "flex";
    },
    hideLoadingPopup: function () {
      const popup = document.getElementById("loading-section");
      if (popup) popup.style.display = "none";
    },
    // Helpers
    generateUrl(appraisalId) {
      if (!appraisalId) return '#';  // return a placeholder if no appraisal ID

      const currentUrl = window.location.href;  // Get the current URL
      const urlParts = currentUrl.split('?');  // Split URL at the '?' to separate path and query string
      const baseUrl = urlParts[0];  // The part before the "?"
      const queryParams = urlParts[1] ? `?${urlParts[1]}` : '';  // The part after the "?"

      // Remove the last number or segment after the last '/' in baseUrl
      const newBaseUrl = baseUrl.replace(/\/\d+$/, '');
      const newUrl = newBaseUrl + '/' + appraisalId + queryParams;
      window.location.href = newUrl;
    },
    updateNavigationLinks() {
      // Fetch the next and previous IDs based on the current appraisal and filters
      const postData = {
        "current_appraisal_id": this.currentAppraisalId,
        "current_sorting": this.currentSorting, // Update based on your sorting mechanism
        "search_title": this.searchTitle,       // Update based on your search mechanism
        "filter_status": this.filterStatus,      // Update based on your filters
        "filter_is_sota": this.filterIsSota,      // Update based on your filters
        "filter_is_ck3": this.filterIsCk3      // Update based on your filters
      };
      console.log("postData", postData);

      const URL = NavigationListAPI;
      axios.post(URL, postData, {
        headers: {
          'Content-Type': 'application/json',
        },
      })
        .then(
          res => {
            console.log(res.data);
            this.previousAppraisalId = res.data.previous;
            this.nextAppraisalId = res.data.next;
            console.log("Previous Appraisal ID:", this.previousAppraisalId);
            console.log("Next Appraisal ID:", this.nextAppraisalId);

          },
          err => {
            console.log("Error fetching navigation links:", err);
          }
        );
    },
    onAddSubExtraction(event) {
      this.axiosPost(
        event,
        url = AddSubExtractionURL,
        isLoadingKey = "isSubExtractionLoading",
        successMsg = "A new sub extraction has been added",
        postData = {},
        callBack = (resData) => {
          // this.subExtractions = resData.sub_extractions;
          this.loadInitData();
        },
      );
    },
    onDeleteSubExtraction(event, SubID) {
      this.axiosPost(
        event,
        url = DeleteSubExtractionURL,
        isLoadingKey = "isSubExtractionLoading",
        successMsg = "Sub Extraction has been deleted successfully!",
        postData = { sub_extraction: SubID },
        callBack = (resData) => {
          // this.subExtractions = resData.sub_extractions;
          location.reload();
        },
      );
    },
    getSubExtraction() {
      this.axiosGet(
        url = AddSubExtractionURL,
        isLoadingKey = "isSubExtractionLoading",
        callBack = (resData) => {
          this.subExtractions = resData.sub_extractions;
        },
      );
    },
    // let's get the appraisal data
    getAppraisalData(is_show_ai=false) {
      axios.get(AppraisalDataURL, {
        headers: {
          'Content-Type': 'application/json',
        },
      })
        .then(
          res => {
            console.log("Appraisal data:", res.data);
            this.article_review = res.data.article_review;
            this.aiStatus = res.data.ai_generation_status;
            this.organizeFields(res.data.fields);
            this.initializeFormValues(res.data);

            // Initialize search term here
            if (this.article_review && this.article_review.search && this.article_review.search.term) {
              const term = this.article_review.search.term;
              this.searchTerm.text = term;
              this.searchTerm.isLong = term.length > 45;
              this.searchTerm.expanded = false;
            }

            this.isRecordsLoading = false;
            this.hideLoadingPopup();
            if (is_show_ai) this.autoGenerateExtractionFields()
          },
          err => {
            console.log("Error fetching appraisal data:", err);
            this.makeToast('error', 'Error loading appraisal data. Please refresh the page.');
            this.isRecordsLoading = false;
            this.hideLoadingPopup();
          }
        );
    },
    organizeFields(fields) {
      // Reset field groups
      this.formFields.suitabilityOutcomes = [];
      this.formFields.stateOfTheArt = [];
      this.formFields.extractionFields = [];
      this.formFields.qualityContribution = [];
      this.formFields.mdcgRanking = [];
      this.formFields.customSection = [];

      // Organize fields by section
      fields.forEach(field => {
        switch (field.field_section) {
          case 'SO':
            this.formFields.suitabilityOutcomes.push(field);
            break;
          case 'ST':
            this.formFields.stateOfTheArt.push(field);
            break;
          case 'EF':
            this.formFields.extractionFields.push(field);
            break;
          case 'QC':
            this.formFields.qualityContribution.push(field);
            break;
          case 'MR':
            this.formFields.mdcgRanking.push(field);
            break;
          case 'CS':
            this.formFields.customSection.push(field);
            break;
        }
      });
    },
    // Initialize form values with existing data   
    initializeFormValues(data) {
      // Initialize basic fields
      this.formValues = {
        included: data.included === null ? '' : data.included.toString(),
        is_sota_article: data.is_sota_article === null ? '' : data.is_sota_article.toString(),
        justification: data.justification || ''
      };

      // Initialize all fields with their values
      data.fields.forEach(field => {
        // For extraction fields, use the compound key
        if (field.field_section === 'EF') {
          const fieldKey = `${field.name}_${field.extraction_field_number}`;
          this.$set(this.formValues, fieldKey, field.value);
        } else {
          // For other sections, use just the name and ensure reactivity
          this.$set(this.formValues, field.name, field.value);
        }
      });

      console.log('Initialized form values:', this.formValues);
    },
    onHighlightPDF(event) {
      const data = {article_id: this.article_review.article.id}
      this.axiosPost(
        event,
        url=PDFHighloghtingURL,
        isLoadingKey="isHighlightPDFLoading",
        successMsg="",
        postData=data,
        callBack = (resData) => {
          this.isHighlightPDFLoading = true;
          console.log("PDF Highlighting processing...")
        },
      );
    },
    updateVisibility() {
      const included = this.formValues.included;
      const isSota = this.formValues.is_sota_article;

      // Yes included, Yes Sota
      if (isSota === 'true' && included === 'true') {
        this.showSota = true;
        this.showDevice = false;
        this.showJustification = false;

        this.inactiveNavs = {
          'quality-contribution': true,
          'mdcg-ranking': true,
          'sota': false,
          'extra-extraction-fields': true,
          'justification-fields': true
        };
      }
      // Yes included, No Sota
      else if (isSota === 'false' && included === 'true') {
        this.showDevice = true;
        this.showSota = false;
        this.showJustification = false;

        this.inactiveNavs = {
          'quality-contribution': false,
          'mdcg-ranking': false,
          'sota': true,
          'extra-extraction-fields': false,
          'justification-fields': true
        };
      }
      // No included, Yes Sota
      else if (isSota === 'true' && included === 'false') {
        this.showSota = true;
        this.showDevice = false;
        this.showJustification = true;

        this.inactiveNavs = {
          'quality-contribution': true,
          'mdcg-ranking': true,
          'sota': false,
          'extra-extraction-fields': true,
          'justification-fields': false
        };
      }
      // No included, No Sota
      else if (isSota === 'false' && included === 'false') {
        this.showSota = false;
        this.showDevice = false;
        this.showJustification = true;

        this.inactiveNavs = {
          'quality-contribution': true,
          'mdcg-ranking': true,
          'sota': true,
          'extra-extraction-fields': true,
          'justification-fields': false
        };
      }
    },
    // Updated submitForm method with detailed logging and simplified value support
    submitForm() {
      console.log("submitForm called");
      console.log("aiFieldsGenerated:", this.aiFieldsGenerated);

      // Check if there are unreviewed AI fields
      if (this.aiFieldsGenerated) {
        // Determine which sections to check based on form values
        const isSota = this.formValues.is_sota_article === 'true';
        const isIncluded = this.formValues.included === 'true';

        // Always check Suitability and Outcomes for all articles
        const sectionsToCheck = ['suitabilityOutcomes'];

        // If it's a SoTA article, add SoTA section
        if (isSota) {
          sectionsToCheck.push('stateOfTheArt');
        }

        // If it's included but not SoTA, check Quality, MDCG Ranking, and Extraction Fields
        if (isIncluded && !isSota) {
          sectionsToCheck.push('qualityContribution', 'mdcgRanking', 'extractionFields');
        }

        // Check only fields in the relevant sections
        const hasUnreviewedFields = Object.entries(this.aiStatuses).some(([fieldId, status]) => {
          if (status !== 'not_reviewed') return false;

          // Find which section this field belongs to
          let fieldSection = null;
          for (const section of sectionsToCheck) {
            if (!Array.isArray(this.formFields[section])) continue;

            const found = this.formFields[section].some(field => field.id.toString() === fieldId);
            if (found) {
              fieldSection = section;
              break;
            }
          }

          // Only consider it "unreviewed" if it's in one of the sections we care about
          return fieldSection !== null;
        });

        console.log("Final check result - hasUnreviewedFields:", hasUnreviewedFields);

        if (hasUnreviewedFields) {
          console.log("Unreviewed fields found in relevant sections, showing modal");

          // Show Modal
          this.showModal('unreviewed-ai-fields-modal');

          return; // Should stop execution here to prevent saving
        } else {
          console.log("No unreviewed fields in relevant sections, proceeding with save");
          this.saveFormData();
        }
      } else {
        console.log("No AI fields generated, proceeding with save");
        this.saveFormData();
      }
    },

    // Extract the form submission logic into a separate method
    saveFormData() {
      // Collect all currently displayed values, including any simplified values
      // that are currently shown instead of original AI values
      const formData = {
        included: this.formValues.included === 'true',
        is_sota_article: this.formValues.is_sota_article === 'true',
        justification: this.formValues.justification || '',

        fields: [
          ...this.formFields.suitabilityOutcomes,
          ...this.formFields.stateOfTheArt,
          ...this.formFields.qualityContribution,
          ...this.formFields.mdcgRanking,
          ...this.formFields.extractionFields,
          ...this.formFields.customSection,
        ].map(field => {
          // For extraction fields, use compound key
          const fieldKey = field.field_section === 'EF'
            ? `${field.name}_${field.extraction_field_number}`
            : field.name;

          // Use the current value that's displayed in the form
          // This will include any simplified values that were selected
          const currentValue = this.formValues[fieldKey] || null;

          // Track if we're using the simplified value for this field
          const isUsingSimplifiedValue = field.ai_simplified_value &&
            currentValue === field.ai_simplified_value;

          return {
            id: field.id,
            value: currentValue,
            extraction_field_number: field.extraction_field_number,
            // Optional: you can include this if you want the server to know
            // when a simplified value was chosen instead of the original AI value
            using_simplified_value: isUsingSimplifiedValue
          };
        })
      };

      console.log("Submitting formData:", formData);

      axios.post(AppraisalDataURL, formData, {
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
      })
        .then(response => {
          console.log('Form submitted successfully:', response.data);
          this.makeToast('success', 'Form saved successfully.');

          // Navigate to next appraisal if available
          if (this.nextAppraisalId) {
            this.generateUrl(this.nextAppraisalId);
          }
        })
        .catch(error => {
          console.error('Error details:', error.response?.data || error);
          this.makeToast('error', 'Error saving form. Please try again.');
        });
    },
    showFullTextPdf() {
      this.showPdfViewer = !this.showPdfViewer;
      if (this.showPdfViewer) {
        if (this.article_review?.full_text_pdf) {
          this.pdfUrl = this.article_review.full_text_pdf;
          this.showPdfViewer = true;
          // scroll to the PDF viewer
          // Wait for the PDF viewer to be rendered
          this.$nextTick(() => {
            const pdfViewer = document.getElementById('pdf-viewer');
            if (pdfViewer) {
              pdfViewer.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
              });
            }
          });
        } else {
          this.makeToast("warning", "No PDF available for this article.");
        }
      } else {
        this.closePdfViewer();
      }

    },
    closePdfViewer() {
      this.showPdfViewer = false;
      this.pdfUrl = null;
    },
    getFieldKey(field) {
      // Return appropriate key based on field section
      return field.field_section === 'EF'
        ? `${field.name}_${field.extraction_field_number}`
        : field.name;
    },
    acceptAIValue(field) {
      // Update local state first
      this.$set(this.aiStatuses, field.id, 'accepted');
      const fieldKey = field.field_section === 'EF'
        ? `${field.name}_${field.extraction_field_number}`
        : field.name;
      field.original_value = this.formValues[fieldKey];

      // Now send the update to the server
      this.updateAIStatusOnServer(field.id, 'accepted', field.extraction_field_number);
    },
    editAIValue(field) {
      // Update local state
      this.$set(this.aiStatuses, field.id, 'edited');

      // Send the update to the server
      this.updateAIStatusOnServer(field.id, 'edited', field.extraction_field_number);
    },
    refuseAIValue(field) {
      // Update local state
      this.$set(this.aiStatuses, field.id, 'rejected');
      const fieldKey = field.field_section === 'EF'
        ? `${field.name}_${field.extraction_field_number}`
        : field.name;
      this.formValues[fieldKey] = this.originalValues[fieldKey] || '';

      // Send the update to the server
      this.updateAIStatusOnServer(field.id, 'rejected', field.extraction_field_number);
    },
    // Updated updateAIStatusOnServer method
    updateAIStatusOnServer(fieldId, status, extractionFieldNumber = 1) {
      // Get CSRF token
      const csrfToken = this.getCSRFToken();

      if (!csrfToken) {
        console.error('CSRF token not found');
        this.makeToast('error', 'CSRF token not found. Please refresh the page.');
        return;
      }

      // Prepare data to send
      const postData = {
        status: status,
        extraction_field_number: extractionFieldNumber
      };

      console.log(`Sending AI status update to server: Field ID ${fieldId}, Status: ${status}`);

      // Replace the placeholder field_id (0) with the actual fieldId
      const updateUrl = AppraisalExtractionFieldUpdateURL.replace('/0/', `/${fieldId}/`);

      // Send PATCH request to the server
      axios.patch(updateUrl, postData, {
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        }
      })
        .then(response => {
          console.log('Status updated successfully:', response.data);
        })
        .catch(error => {
          console.error('Error updating AI status:', error);
          if (error && error.response) {
            console.error("Server error response:", error.response.data);
          }
        });
    },
    getCSRFToken() {
      return document.querySelector('[name=csrfmiddlewaretoken]')?.value
        || document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    },
    autoGenerateExtractionFields(regenerate=false, showHideToast=true) {      
      // If AI fields are already generated and not regenerating, this becomes a "Hide" button
      if (this.aiFieldsGenerated && !regenerate) {
        // Only hide fields that are still in "not_reviewed" status
        this.hideUnreviewedAIFields(showHideToast);
        return;
      }

      // If AI has already completed, fields aren't shown, and not regenerating, just show existing fields without making API call
      if (this.aiStatus === 'completed' && !regenerate && !this.aiFieldsGenerated) {
        console.log("AI already completed, showing existing fields without API call");

        // We already have the fields from initial data load
        // Just need to set up the UI to show AI values

        // Process fields we already have
        const fieldsWithAiValues = this.getAllFieldsWithAiValues();
        const totalFieldsWithAiValue = this.setupAIFields(fieldsWithAiValues);

        if (totalFieldsWithAiValue > 0) {
          this.aiFieldsGenerated = true;
          this.makeToast('success', `Showing ${totalFieldsWithAiValue} AI-generated Fields.`);
        } else {
          this.makeToast('warning', 'No AI-generated Values Found.');
        }

        return;
      }

      try {
        console.log(regenerate ? "Re-generating AI extractions..." : "Generating AI extractions...");

        // Set loading state
        this.aiLoading = true;

        // Reset AI statuses
        this.aiStatuses = {};

        // Store current values for all sections
        this.originalValues = {};
        const sectionsToUpdate = [
          'extractionFields',
          'suitabilityOutcomes',
          'qualityContribution',
          'mdcgRanking'
        ];

        // Store original values
        sectionsToUpdate.forEach(section => {
          this.formFields[section].forEach(field => {
            const fieldKey = this.getFieldKey(field);
            this.$set(this.originalValues, fieldKey, this.formValues[fieldKey]);
            console.log(`Storing original value for ${fieldKey}:`, this.formValues[fieldKey]);
          });
        });

        // Get CSRF token
        const csrfToken = this.getCSRFToken();

        if (!csrfToken) {
          console.error('CSRF token not found');
          this.makeToast('error', 'CSRF token not found. Please refresh the page.');
          this.aiLoading = false;
          return;
        }

        this.showLoadingPopup();
        axios.patch(AppraisalAIDataURL, {
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
          }
        })
          .then(response => {
            // this process is a background job using celery once completed, a websocket message will be sent to refresh the data
            
            // console.log(regenerate ? "AI Re-generated fields:" : "AI Generated fields:", response.data);
            // const totalFieldsWithAiValue = this.setupAIFields(response.data.fields);
            // // Only set aiFieldsGenerated to true if we found fields with AI values
            // if (totalFieldsWithAiValue > 0) {
            //   this.aiFieldsGenerated = true;
            //   const successMessage = regenerate
            //     ? `AI extraction re-generated with ${totalFieldsWithAiValue} fields!`
            //     : `AI extraction completed with ${totalFieldsWithAiValue} fields!`;
            //   this.makeToast('success', successMessage);
            // } else {
            //   this.makeToast('warning', 'No AI-generated values were found in the response.');
            // }
          })
          .catch(error => {
            console.error(regenerate ? "Error re-generating AI extractions:" : "Error generating AI extractions:", error);
            // Safely check if error.response exists
            if (error && error.response) {
              console.error("Server error response:", error.response.data);
            }

            // Use safe toast method with fallback
            const errorMessage = regenerate
              ? 'Error re-generating AI extractions. Please try again.'
              : 'Error generating AI extractions. Please try again.';
            this.makeToast('error', errorMessage);
          })
          .finally(() => {
            this.aiLoading = false;
          });
      } catch (err) {
        console.error(regenerate ? "Exception in regenerateExtractionFields:" : "Exception in autoGenerateExtractionFields:", err);
        this.aiLoading = false;
        this.makeToast('error', 'An unexpected error occurred. Please try again.');
      }
    },
    hideUnreviewedAIFields(showToast=true) {
      console.log("Hiding unreviewed AI fields only");

      // Get all field IDs that are still in "not_reviewed" status
      const unreviewedFieldIds = Object.entries(this.aiStatuses)
        .filter(([id, status]) => status === 'not_reviewed')
        .map(([id]) => id);

      console.log(`Found ${unreviewedFieldIds.length} unreviewed fields to hide`);

      // Only restore original values for unreviewed fields
      for (const fieldId of unreviewedFieldIds) {
        // Find the corresponding field
        let matchingField = null;
        for (const section in this.formFields) {
          // Check if this.formFields[section] is an array before using find
          if (Array.isArray(this.formFields[section])) {
            const found = this.formFields[section].find(f => f.id.toString() === fieldId);
            if (found) {
              matchingField = found;
              break;
            }
          }
        }

        if (matchingField) {
          const fieldKey = this.getFieldKey(matchingField);
          // Restore original value only for this field
          this.$set(this.formValues, fieldKey, this.originalValues[fieldKey] || '');
          // Remove from aiStatuses
          this.$delete(this.aiStatuses, fieldId);
          console.log(`Restored original value for field ${fieldId} (${fieldKey})`);
        } else {
          console.warn(`Could not find matching field for ID ${fieldId}`);
        }
      }

      this.aiFieldsGenerated = false;

      // Adjust the toast message based on what happened
      if (showToast && unreviewedFieldIds.length > 0) {
        this.makeToast('success', `Hidden ${unreviewedFieldIds.length} unreviewed AI fields`);
      } else if (showToast) {
        this.makeToast('success', 'All AI fields have been hidden or reviewed');
      }
    },

    // Modify hideGeneratedFields to handle both use cases
    hideGeneratedFields() {
      console.log("Hiding all generated fields");

      // Restore all original values (used for the "Hide AI Fields & Save" button)
      Object.keys(this.originalValues).forEach(fieldKey => {
        this.$set(this.formValues, fieldKey, this.originalValues[fieldKey] || '');
      });

      // Reset AI states
      this.aiStatuses = {};
      this.aiFieldsGenerated = false;

      this.makeToast('success', 'All AI fields hidden successfully');
    },
    toggleSearchTerm() {
      this.searchTerm.expanded = !this.searchTerm.expanded;
    },
    // Add this new method to your Vue component
    setupAIFields(fields) {
      // Reset AI statuses
      this.aiStatuses = {};

      // Count how many fields should have AI values
      let totalFieldsWithAiValue = 0;

      // Process all fields
      if (fields && Array.isArray(fields)) {
        console.log(`Processing ${fields.length} fields`);

        // Store original values for all sections
        if (Object.keys(this.originalValues).length === 0) {
          const sectionsToUpdate = [
            'extractionFields',
            'suitabilityOutcomes',
            'qualityContribution',
            'mdcgRanking',
            'customSection'
          ];

          // Store original values only if we haven't stored them before
          sectionsToUpdate.forEach(section => {
            this.formFields[section].forEach(field => {
              const fieldKey = this.getFieldKey(field);
              this.$set(this.originalValues, fieldKey, this.formValues[fieldKey]);
              console.log(`Storing original value for ${fieldKey}:`, this.formValues[fieldKey]);
            });
          });
        }

        // Process all fields
        fields.forEach(field => {
          if (field.ai_value) {
            totalFieldsWithAiValue++;

            const fieldKey = this.getFieldKey(field);
            // Store original value if not already stored
            if (!this.originalValues[fieldKey]) {
              this.$set(this.originalValues, fieldKey, this.formValues[fieldKey] || '');
            }
            // Update the form value
            this.$set(this.formValues, fieldKey, field.ai_value);
            // Store original value in field for reference
            field.original_value = this.originalValues[fieldKey];
            // Add to aiStatuses to track as not reviewed
            this.$set(this.aiStatuses, field.id, field.ai_value_status || 'not_reviewed');
          }
        });

        // Force Vue to re-render
        this.$forceUpdate();

        // Style tooltips after a small delay to ensure DOM is updated
        const timeOut = setTimeout(() => {
          this.styleTooltips();
          return clearTimeout(timeOut);
        }, 500);
      } else {
        console.warn("No valid fields array provided");
      }

      return totalFieldsWithAiValue;
    },
    getAllFieldsWithAiValues() {
      // Collect all fields with AI values from all sections
      const fieldsWithAiValues = [];

      const sectionsToCheck = [
        'extractionFields',
        'suitabilityOutcomes',
        'qualityContribution',
        'mdcgRanking',
        'customSection',
      ];

      sectionsToCheck.forEach(section => {
        if (Array.isArray(this.formFields[section])) {
          this.formFields[section].forEach(field => {
            // If field has AI value, include it
            if (field.ai_value) {
              fieldsWithAiValues.push(field);
            }
          });
        }
      });

      console.log(`Found ${fieldsWithAiValues.length} fields with AI values`);
      return fieldsWithAiValues;
    },
    // Add this method to your Vue instance
    useSimplifiedAIValue(field) {
      // Check if we have a simplified value
      if (!field.ai_simplified_value) {
        console.warn(`No simplified value available for field ${field.name}`);
        this.makeToast('warning', 'No simplified version available for this field');
        return;
      }

      // Get the field key
      const fieldKey = this.getFieldKey(field);

      // Store original value if not already stored
      if (!field.original_ai_value) {
        field.original_ai_value = field.ai_value;
      }

      // Toggle between original AI value and simplified value
      if (this.formValues[fieldKey] === field.ai_simplified_value) {
        // Currently showing simplified value, switch to original
        this.formValues[fieldKey] = field.ai_value;
        this.makeToast('info', 'Showing original AI version');
      } else {
        // Currently showing original value, switch to simplified
        this.formValues[fieldKey] = field.ai_simplified_value;
        this.makeToast('info', 'Showing simplified version');
      }

    },
    // Add this method to your Vue instance
    hideAIFieldsAndSave() {
      console.log("Hiding AI fields and saving form");

      // First hide any modal that might be open
      this.hideModal('unreviewed-ai-fields-modal');

      // Handle unreviewed fields
      const unreviewedFieldIds = Object.entries(this.aiStatuses)
        .filter(([id, status]) => status === 'not_reviewed')
        .map(([id]) => id);

      console.log(`Found ${unreviewedFieldIds.length} unreviewed fields to reset before saving`);

      // Restore original values for unreviewed fields only
      for (const fieldId of unreviewedFieldIds) {
        // Find the corresponding field
        let matchingField = null;
        for (const section in this.formFields) {
          if (Array.isArray(this.formFields[section])) {
            const found = this.formFields[section].find(f => f.id.toString() === fieldId);
            if (found) {
              matchingField = found;
              break;
            }
          }
        }

        if (matchingField) {
          const fieldKey = this.getFieldKey(matchingField);

          // Restore original value only for unreviewed fields
          this.$set(this.formValues, fieldKey, this.originalValues[fieldKey] || '');

          // Remove from aiStatuses
          this.$delete(this.aiStatuses, fieldId);
          console.log(`Reset field ${fieldId} (${fieldKey}) before saving`);
        }
      }

      // Mark AI fields as hidden
      this.aiFieldsGenerated = false;

      // Now save the form with the updated values
      console.log("Proceeding to save form data after hiding unreviewed AI fields");
      this.saveFormData();
    },
    loadInitData: function () {
      this.isRecordsLoading = true;

      // First let Vue finish rendering
      this.$nextTick(() => {
        // Now we can safely access DOM elements
        this.showLoadingPopup();
        this.getAppraisalData();
        this.updateNavigationLinks();
        this.getSubExtraction();
        this.updateVisibility(); // Initial visibility update
      });
    },

    // websocket related 
    initiatSocket() {
      // update websocket onmessage callBack
      try {
        const webSocket = this.sharedState.reviewSocket;
        const vm = this;

        webSocket.onmessage = function(e) {
          const socketMessage = JSON.parse(e.data);
          console.log("Recieved message from socket : ");
          console.log({socketMessage});

          if (socketMessage.type === "review_second_pass_ai_fields_completed") {
            if (socketMessage.message.appraisal_id === parseInt(vm.currentAppraisalId)) {
              if (socketMessage.message.text.includes("failed")) vm.makeToast("error", "The AI modal failed to extract values from the full text PDF.");
              else vm.makeToast("success", "AI generation for extraction fields is completed successfully!")
              vm.getAppraisalData(false);
            }
          }

          if (socketMessage.type === "pdf_kw_highlighting_completed") {
            if (socketMessage.message.article_id === parseInt(vm.article_review.article.id)) {
              vm.isHighlightPDFLoading = false;
              vm.makeToast("success", "PDF Highlighting is Completed Successfully!")
              vm.loadInitData();
            };
          }
        };

        store.setReviewSocket(webSocket);
      } catch (error) {
        console.log("Failed to initial websocket due to below error")
        console.error(error);
      };
    },
  },
  watch: {
    'formValues.included'() {
      this.updateVisibility();
    },
    'formValues.is_sota_article'() {
      this.updateVisibility();
    }
  },
  mounted() {
    this.loadInitData();
    this.initiatSocket();
  }
})
