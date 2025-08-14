axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
	el: '#app',
	mixins: [globalMixin],
	delimiters: ["[[", "]]"],
	data() {
		return {
			reports: [],
			isRecordsLoading: false,
			sorting: "",
			validator: null,
			configuration: null,
			project: null,
			projectAppraisals: {},
			selectedReportID: null,
			no_validation: false,
			reportComment: "",
			reportType: "",
			fileFormats: [],
			selectedStatus: [],
			appliedStatus: [],
			reportDescription: "Report Description Box",
			reportFileExampleWordUrl: "Report File Foramt Url",
			reportFileExampleExcelUrl: "Report File Foramt Url",
			reportFileExampleZipUrl: "Report File Foramt Url",
			reportFileExampleRisUrl: "",
			selectedFileForamt: "",
			searchTerm: "",
			filterTypes: [],
			reportTypes: [
				{
					name: "PROTOCOL",
					displayedName: "Protocol",
					isProtocol: true,
					isSimple: false,
					value: "protocol",
				},
				{
					name: "REPORT",
					displayedName: "Report",
					isSimple: false,
					value: "report",
				},
				{
					name: "SIMPLE_PROTOCOL",
					displayedName: "Simple Protocol",
					isProtocol: true,
					isSimple: false,
					value: "simple_protocol",
				},
				{
					name: "SIMPLE_REPORT",
					displayedName: "Simple Report",
					isSimple: false,
					value: "simple_report",
				},
				{
					name: "CONDENSED_REPORT",
					displayedName: "Condensed Report",
					isSimple: false,
					value: "condense_report",
				},
				{
					name: "SECONDPASS",
					displayedName: "Second Pass Extraction Articles",
					isSimple: true,
					value: "2nd_pass",
				},
				{
					name: "APPENDIX_E2",
					displayedName: "Appendix E2",
					isSimple: false,
					value: "appendix_e2",
				},
				{
					name: "ARTICLE_REVIEWS",
					displayedName: "Full Review Data",
					isSimple: true,
					value: "export_article_reviews",
				},
				{
					name: "PRISMA",
					displayedName: "Prisma",
					isSimple: true,
					value: "prisma",
				},
				{
					name: "FULL_TEXT_ZIP",
					displayedName: "Full Text Zip",
					isSimple: true,
					value: "full_text_zip",
				},
				{
					name: "TERMS_SUMMARY",
					displayedName: "Search Terms Summary",
					isProtocol: true,
					isSimple: true,
					value: "terms_summary",
				},
				{
					name: "SEARCH_VALIDATION_ZIP",
					displayedName: "Search Validation Zip",
					isSimple: false,
					value: "search_validation_zip",
				},
				{
					name: "DUPLICATES",
					displayedName: "Duplicates Report",
					isSimple: true,
					value: "duplicates",
				},
				{
					name: "AUDIT_TRACKING_LOGS",
					displayedName: "Audit Tracking Logs",
					isSimple: true,
					value: "audit_tracking_logs",
				},
				{
					name: "DEVICE_HISTORY",
					displayedName: "Device History",
					isSimple: false,
					value: "device_history",
				},
				{
					name: "CUMULATIVE_REPORT",
					displayedName: "Cumulative Report",
					isSimple: false,
					value: "cumulative_report",
				},
				{
					name: "ABBOTT_REPORT",
					displayedName: "Abbott Report",
					isSimple: false,
					value: "ABBOTT_REPORT",
				},
			],
			activeCommentModal: null,
			isUpdatingComment: false,
			isGenerateReportSliderOpen: false,
			selectedFileForamt: '',
			selectedReportType: '',
			reportStep: 1, // Current step in the report generation process
			// Report types for each format
			excelReportTypes: [
				{
					name: "Search Term Summary",
					displayedName: "TERMS_SUMMARY_EXCEL",
					value: "terms_summary_excel",
					isProtocol: true,
					description: "Contains all search terms and which databases each term is scheduled to be run on.",
					exampleLink: "https://docs.google.com/spreadsheets/d/e/2PACX-1vQf7W14bcKsVWc-tVZcVJjuZwJ4vzjIuNFlGGIwtApSkrbPaAfI9ytufyTQz67XZg/pubhtml?widget=true&amp;headers=false"
				},
				{
					name: "Full Data Review",
					displayedName: "ARTICLE_REVIEWS",
					value: "export_article_reviews",
					description: "Contains the List of articles processed during the first pass with their details.",
					exampleLink: "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnqov-BIpyg-5kW1vP-7stZyIzM8kMK5xWaB6SmKyBV1MZ0XIlC62kM4yexE5yPA/pubhtml?widget=true&amp;headers=false",
				},
				{
					name: "Second Pass Extraction Articles",
					displayedName: "SECONDPASS",
					value: "2nd_pass",
					description: "Contains the List of included articles processed during the second pass with their appraisal details only.",
					exampleLink: "https://docs.google.com/spreadsheets/d/e/2PACX-1vTSQ0jiNH5A4Io-Xo_-HZawx1qs7wdwrBJZjmV_hh9yitvi3ASQtEIw-P-PvOUgqQ/pubhtml?widget=true&amp;headers=false"
				},
				{
					name: "Duplicates Summary",
					displayedName: "DUPLICATES",
					value: "duplicates",
					description: "Contains a list of duplicates found. Each set of duplicates will share the same Duplicate ID, making it easy to identify which entries were flagged as duplicates by the app.",
					exampleLink: "https://docs.google.com/spreadsheets/d/e/2PACX-1vQCDSFaLUVnZMEKqtUWvhnk2X1b3Qhi0IXd4HqI9swmA8qMtKbvTVmxOqBAI3nXvw/pubhtml?widget=true&amp;headers=false"
				},
				{
					name: "Appendix E2 Report",
					displayedName: "APPENDIX_E2",
					value: "appendix_e2_excel",
					description: "Contains all Maude processed events and any associated summary.",
					exampleLink: "https://docs.google.com/spreadsheets/d/e/2PACX-1vT2fFJQnLAUzsxeANRBF5jL25Ueo6J3-InqP7S48mdXwTG7k4oqex8-k15GP_dCYw/pubhtml?widget=true&amp;headers=false"
				},
				{
					name: "Audit Tracking Logs",
					displayedName: "AUDIT_TRACKING_LOGS",
					value: "audit_tracking_logs",
					description: "Contains a list of all the actions performed on a specific literature review.",
					exampleLink: "https://docs.google.com/spreadsheets/d/e/2PACX-1vSgXR33tCAvtVTlqa6q7jt7pLAU-Atifq44oG2de746oW3aj8ErN8N56b-R5Wrylg/pubhtml?widget=true&amp;headers=false"
				}
			],
			wordReportTypes: [
				{
					name: "Search Term Summary",
					displayedName: "TERMS_SUMMARY",
					value: "terms_summary",
					isProtocol: true,
					description: "Contains all search terms and which databases each term is scheduled to be run on.",
					exampleLink: "https://docs.google.com/document/d/e/2PACX-1vR2ZndPViP7jFqXCDw7SO7NGiawWGkJ5wcsziV4R2oMvCUyy2nsXjm1ZJgjGeVmNA/pub?embedded=true"
				},
				// {
				// 	name: "Abbott Report",
				// 	displayedName: "ABBOTT_REPORT",
				// 	value: "abbott_report",
				// 	isProtocol: false,
				// 	description: "A custom report for Abbot",
				// 	exampleLink: ""
				// },
				{
					name: "Appendix E2 Report",
					displayedName: "APPENDIX_E2",
					value: "appendix_e2",
					description: "Contains all Maude processed events and any associated summary.",
					exampleLink: "https://docs.google.com/document/d/e/2PACX-1vSz27MBPZzuIqmuxYobr49ozTHxvyHdH6l46XtkUdin7RfpuTniY0S490uvwJ35jQ/pub?embedded=true"
				},
				{
					name: "Search Protocol",
					displayedName: "PROTOCOL",
					value: "protocol",
					isProtocol: true,
					description: "Contains key information about the Literature Review that will be conducted such as product info and descriptions, which databases will be searched, process for abstract review and full text review.",
					exampleLink: "https://docs.google.com/document/d/e/2PACX-1vTcfJNLVF9fHD_qFgwd1iXdWyDu8u7pmhLrvfrmvpp0461_6K7GVzPazmleLI639Q/pub?embedded=true"
				},
				{
					name: "Simple Search Protocol",
					displayedName: "SIMPLE_PROTOCOL",
					value: "simple_protocol",
					isProtocol: true,
					description: "Similar to the full protocol but with fewer details and a more streamlined structure.",
					exampleLink: "https://docs.google.com/document/d/e/2PACX-1vTrUfe9RDZ3oDLVt3nnARZr9YH6Tq3LgnaWpgT68DKmweeeWv4vdU0DkngaHdeKYg/pub?embedded=true"
				},
				{
					name: "Search Report",
					displayedName: "REPORT",
					value: "report",
					description: "Contains the submission-ready report template containing your entire systematic review.",
					exampleLink: "https://docs.google.com/document/d/e/2PACX-1vTDQj0j-8rYrW2xRRkGhOVBb8FhvOGuhwvQC2v42u5cjTNW6wZN9pbLCxGS6i1b9g/pub?embedded=true"
				},
				{
					name: "Simple Search Report",
					displayedName: "SIMPLE_REPORT",
					value: "simple_report",
					description: "Contains the submission-ready report template containing your entire systematic review.",
					exampleLink: "https://docs.google.com/document/d/e/2PACX-1vQULHY6-GlHziOa_YUkJvMixbDktsBrZdCgGYp4wOSmhu87DoSwlsLi0Y7VX3Siow/pub?embedded=true"
				},
				{
					name: "Second Pass Extraction Articles",
					displayedName: "SECONDPASS",
					value: "2nd_pass_word",
					description: "Contains the List of included articles processed during the second pass with their appraisal details only.",
					exampleLink: "https://docs.google.com/document/d/e/2PACX-1vSR_ih8Yx9uk3FFycCf0aFJNK8-_FkncTigaBzeSORPrAx9LKlTJa81tMo9FFHZhQ/pub?embedded=true"
				},
			],
			zipReportTypes: [
				{
					name: "Condensed Report",
					displayedName: "CONDENSED_REPORT",
					value: "condense_report",
					description: "Contains all significant sections with only discussion and review of the Retained literature.",
					exampleLink: [
						{
							name: "NCircle Stone Extractor (Completed Review)_Cook Medical_Appendix_A_2024-06-29 V1.0",
							type: "word",
							exampleLink: "https://docs.google.com/document/d/e/2PACX-1vRMgj3a9klw_Qr16ERqVV60lrX0tn8nTirsPjNaG60rbwLJKSofFnQ1_q3TUfS-RA/pub?embedded=true"
						},
						{
							name: "NCircle Stone Extractor (Completed Review)_Cook Medical_Condensed_LITR_2024-06-29 V1.0",
							type: "word",
							exampleLink: "https://docs.google.com/document/d/e/2PACX-1vS6NVjBfsM2PeyEQWOIsEyb_hREjmHc0Z1VPtMYRMH0M4rS6GNBJISbA4wKVy0zkA/pub?embedded=true"
						},
					]
				},
				{
					name: "Prisma",
					displayedName: "PRISMA",
					value: "prisma",
					description: "Contains flowchart and tables in multiple formats (Excel, DOCX).",
					exampleLink: [
						{
							name: "Article Tags Summary",
							type: "excel",
							exampleLink: "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEatDYp2s_yfYhTGu8hkFE8t6ibA_AtoJoAbex_GUc8_yWo0ceTgCFs0FnjHLCjA/pubhtml?widget=true&amp;headers=false"
						},
						{
							name: "Excluded Articles Summary",
							type: "excel",
							exampleLink: "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8kzOaUDOAzTIEApmr5GnhjiJWQOLOAy-Ll3kPBFnM0DlkNSQ957aR_V4aC_CVmA/pubhtml?widget=true&amp;headers=false"
						},
						{
							name: "Prisma Chart",
							type: "word",
							exampleLink: "https://docs.google.com/document/d/e/2PACX-1vR5zwILQst_0PT_3RrNYamBqC1GOt_7VWUBZ3yUGXkLnbj-BW9o8nD7p-sui0Dxjw/pub?embedded=true"
						},
						{
							name: "Prisma Summary",
							type: "excel",
							exampleLink: "https://docs.google.com/spreadsheets/d/e/2PACX-1vRl19yCAnywOnL4PHa2kPYtZet3V0CqiRrt3u9ISWU989WFoEG7_a2hrQpUMPG95w/pubhtml?widget=true&amp;headers=false"
						},
					]
				},
				{
					name: "Full Text",
					displayedName: "FULL_TEXT_ZIP",
					value: "full_text_zip",
					description: "Contains full-text PDFs of selected articles.",
					exampleLink: [
						{
							name: "Test Upload Article",
							type: "pdf",
							exampleLink: "https://drive.google.com/file/d/14Yd4WiwtzrOmFdfl2uraOtZVGNoxkRfR/preview"
						},
						{
							name: "Dusting_utilizing_suction_technique_DUST_for_percutaneous_nephrolithotomy_use_of_a_dedicated_laser_handpiece_to_treat_a_staghorn_stone.",
							type: "pdf",
							exampleLink: "https://drive.google.com/file/d/1XX3OR670UshWRyibBWXw33CfhtZa_Pke/preview"
						}
					]
				},
				{
					name: "Search Validation",
					displayedName: "SEARCH_VALIDATION_ZIP",
					value: "search_validation_zip",
					description: "Contains the exact search file from every single search performed directly on the associated database.",
					exampleLink: [
						{
							name: "Cochrane-Jul-04-2023_1332Cochrane-Cook_Medical-Jul-04-2023_1332-d68f908f-b27a-46d6-a06f-d6e9e9c3",
							type: "txt",
							exampleLink: "https://drive.google.com/file/d/1CyI8l3dtKVGBPgbAqG1AUfzwrYZVPEoo/preview"
						},
						{
							name: "Cochrane-Nov-03-2022_1808Urinary_stone_basket",
							type: "txt",
							exampleLink: "https://drive.google.com/file/d/1itEjGe5TZ2LhdkVOK4rVP70Ym9zPA19s/preview"
						},
						{
							name: "FDA_MAUDE-Nov-04-2022_1803FFL",
							type: "excel",
							exampleLink: "https://docs.google.com/spreadsheets/d/e/2PACX-1vRQZDiXqBADZcvXHaCGEpIAQtijuARI5dL8oUBC7m4UQ5dLHPRu1xur1s2eVFtqYg/pubhtml?widget=true&amp;headers=false"
						},
						{
							name: "FDA_MAUDE-Nov-21-2022_1513maudeExcelReport28_BYS_2021",
							type: "excel",
							exampleLink: "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7NIfdLLCW_EUX9ITE2ENtVKqAnxEcZx2c_TiGS4otF2Gv-WiTkgwf3N0lOkEX1w/pubhtml?widget=true&amp;headers=false"
						},
					]
				},
				{
					name: "Device History",
					displayedName: "DEVICE_HISTORY",
					value: "device_history",
					description: "Contains all excel reports from all previous projects related to this device. Sorted by date and labeled by project name.",
					exampleLink: [
						{
							name: "Full Review Data",
							type: "excel",
							exampleLink: "https://docs.google.com/spreadsheets/d/e/2PACX-1vSgrG8AjP9SabjUuZV7xadovlLgvTGrRydFZQ-1MExYWZwvf4dJol4migVoWcUX1g/pubhtml?widget=true&amp;headers=false"
						},
						{
							name: "Search Terms",
							type: "excel",
							exampleLink: "https://docs.google.com/spreadsheets/d/e/2PACX-1vRm66hOcd6bjZVWVaalihR9wU_7jQBM4wFhPJQ3pQLDQdu6gr8LYfjIxjg116pPyw/pubhtml?widget=true&amp;headers=false"
						},
						{
							name: "Second Pass Appraisals",
							type: "excel",
							exampleLink: "https://docs.google.com/spreadsheets/d/e/2PACX-1vR612EF3aZ7duciTxYUL5WANoBu6CxwMarrced9FavJRD3iODESrwcaSNdwbWeHAg/pubhtml?widget=true&amp;headers=false"
						},
					],
				},
				{
					name: "Cumulative Devices",
					displayedName: "CUMULATIVE_REPORT",
					value: "cumulative_report",
					description: "This is similar to Device History, but it organizes device reports by project. Each project will have its own folder.",
					exampleLink: [
						{
							name: "Full Review Data",
							type: "excel",
							exampleLink: "https://docs.google.com/spreadsheets/d/e/2PACX-1vSgrG8AjP9SabjUuZV7xadovlLgvTGrRydFZQ-1MExYWZwvf4dJol4migVoWcUX1g/pubhtml?widget=true&amp;headers=false"
						},
						{
							name: "Search Terms",
							type: "excel",
							exampleLink: "https://docs.google.com/spreadsheets/d/e/2PACX-1vRm66hOcd6bjZVWVaalihR9wU_7jQBM4wFhPJQ3pQLDQdu6gr8LYfjIxjg116pPyw/pubhtml?widget=true&amp;headers=false"
						},
						{
							name: "Second Pass Appraisals",
							type: "excel",
							exampleLink: "https://docs.google.com/spreadsheets/d/e/2PACX-1vR612EF3aZ7duciTxYUL5WANoBu6CxwMarrced9FavJRD3iODESrwcaSNdwbWeHAg/pubhtml?widget=true&amp;headers=false"
						},
					],
				},
				{
					name: "Second Pass Extraction Articles (RIS Format)",
					displayedName: "SECONDPASS",
					value: "2nd_pass_ris",
					description: "Contains the List of included articles processed during the second pass with their appraisal details only.",
					exampleLink: [],
					downloadLink: "https://drive.google.com/file/d/1B1Y7uZuPpa7zba8OS8vVmMdIMpcHNC7A/view?usp=sharing"
				},
				{
					name: "Full Data Review (RIS Format)",
					displayedName: "ARTICLE_REVIEWS",
					value: "article_reviews_ris",
					description: "Contains the List of articles processed during the first pass with their details.",
					exampleLink: [],
					downloadLink: "https://drive.google.com/file/d/1aH1izScmw5CBCHGk0lRlieXwGtF1iYl-/view?usp=sharing"
				},
			],
			iframeLoading: true,
			selectedZipFileIndex: null, // To track which ZIP file is selected
			zipIframeLoading: true,     // Loading state for ZIP file iframe
			isValidationErrorModalVisible: false,
		}
	},
	computed: {
		showPreviewPanel() {
			const shouldShow = this.selectedReportType && this.reportStep === 2 && this.isGenerateReportSliderOpen && !this.isValidationErrorModalVisible;
			console.log('Preview panel visibility:', shouldShow, {
				selectedReportType: this.selectedReportType,
				reportStep: this.reportStep,
				isGenerateReportSliderOpen: this.isGenerateReportSliderOpen
			});
			return shouldShow;
		},
		activeZipPreview() {
			// If a ZIP file type is selected and we have files
			if (this.selectedFileForamt === 'zip' && this.getPreviewLink() && this.getPreviewLink().exampleLink) {
				// Use selectedZipFileIndex if it's set, otherwise use 0
				const index = (this.selectedZipFileIndex !== null) ? this.selectedZipFileIndex : 0;

				// Return the link for the active file
				if (this.getPreviewLink().exampleLink[index]) {
					return this.getPreviewLink().exampleLink[index].exampleLink;
				}
			}
			return null;
		},
		// Filter Excel report types based on URL parameter
		filteredExcelReportTypes() {
			// Check URL for protocol filter
			const isProtocolView = window.location.href.includes('type=protocol');

			// Filter the report types based on the URL parameter
			return this.excelReportTypes.filter(type => {
				return isProtocolView ? (type.isProtocol === true) : (type.isProtocol !== true);
			});
		},

		// Filter Word report types based on URL parameter
		filteredWordReportTypes() {
			// Check URL for protocol filter
			const isProtocolView = window.location.href.includes('type=protocol');

			// Filter the report types based on the URL parameter
			return this.wordReportTypes.filter(type => {
				return isProtocolView ? (type.isProtocol === true) : (type.isProtocol !== true);
			});
		},

		// Filter ZIP report types based on URL parameter
		filteredZipReportTypes() {
			// Check URL for protocol filter
			const isProtocolView = window.location.href.includes('type=protocol');

			// Filter the report types based on the URL parameter
			return this.zipReportTypes.filter(type => {
				return isProtocolView ? (type.isProtocol === true) : (type.isProtocol !== true);
			});
		},

		hasDownloadLinkOnly() {
			if (this.selectedFileForamt === 'zip' && this.selectedReportType) {
				const reportType = this.zipReportTypes.find(type => type.value === this.selectedReportType);
				return reportType &&
					(!reportType.exampleLink || reportType.exampleLink.length === 0) &&
					reportType.downloadLink;
			}
			return false;
		},

		getDownloadLink() {
			if (this.selectedFileForamt === 'zip' && this.selectedReportType) {
				const reportType = this.zipReportTypes.find(type => type.value === this.selectedReportType);
				return reportType && reportType.downloadLink ? reportType.downloadLink : null;
			}
			return null;
		}
	},
	methods: {
		// helpers
		enableElement: function (ele, text = null) {
			ele.style.pointerEvents = "auto";
			ele.style.opacity = "1";
			if (text) ele.innerHTML = text;
		},
		disableElement: function (ele, text = null) {
			ele.style.pointerEvents = "None";
			ele.style.opacity = ".7";
			if (text) ele.innerHTML = text;
		},
		toggleStatus(state) {
			const index = this.selectedStatus.indexOf(state);
			if (index > -1) {
				this.selectedStatus.splice(index, 1);
			} else {
				this.selectedStatus.push(state)
			}
		},
		onCloseFilters() {
			this.selectedStatus = this.appliedStatus;
			this.hideModal('filters-slider');
		},
		onClearFilters() {
			this.filterTypes = [];
			this.searchTerm = "";
			this.selectedStatus = [];
			this.appliedStatus = [];
			this.loadData();
		},
		getReportFileLink(report) {
			if (report.protocol) {
				return report.protocol;
			} else if (report.report) {
				return report.report;
			} else if (report.condensed_report) {
				return report.condensed_report;
			} else if (report.appendix_e2) {
				return report.appendix_e2;
			} else if (report.all_articles_review) {
				return report.all_articles_review;
			} else if (report.prisma) {
				return report.prisma;
			} else if (report.second_pass_word) {
				return report.second_pass_word;
			} else if (report.second_pass_ris) {
				return report.second_pass_ris;
			} else if (report.article_reviews_ris) {
				return report.article_reviews_ris;
			} else if (report.second_pass_articles) {
				return report.second_pass_articles;
			} else if (report.terms_summary_report) {
				return report.terms_summary_report;
			} else if (report.verification_zip) {
				return report.verification_zip;
			} else if (report.fulltext_zip) {
				return report.fulltext_zip;
			} else if (report.duplicates_report) {
				return report.duplicates_report;
			} else if (report.audit_tracking_logs) {
				return report.audit_tracking_logs;
			} else if (report.device_history_zip) {
				return report.device_history_zip;
			} else if (report.cumulative_report) {
				return report.cumulative_report;
			} else if (report.abbot_report) {
				return report.abbot_report;
			};
		},
		getReportFormat(report) {
			if (report.protocol) {
				return "docx";
			} else if (report.report) {
				return "docx";
			} else if (report.condensed_report) {
				return "zip";
			} else if (report.appendix_e2) {
				if (report.appendix_e2.includes(".xlsx")) {
					return "excel";
				}
				return "docx";
			} else if (report.all_articles_review) {
				return "excel";
			} else if (report.prisma) {
				return "zip";
			} else if (report.second_pass_word) {
				return "docx";
			} else if (report.second_pass_ris) {
				return "ris";
			} else if (report.article_reviews_ris) {
				return "ris";
			} else if (report.second_pass_articles) {
				return "excel";
			} else if (report.fulltext_zip) {
				return "zip";
			} else if (report.verification_zip) {
				return "zip";
			} else if (report.duplicates_report) {
				return "excel";
			} else if (report.terms_summary_report) {
				if (report.terms_summary_report.includes(".xlsx")) {
					return "excel";
				}
				return "docx";
			} else if (report.audit_tracking_logs) {
				return "excel";
			} else if (report.device_history_zip) {
				return "zip";
			} else if (report.cumulative_report) {
				return "zip";
			} else if (report.abbot_report) {
				return "docx";
			};
		},
		getReportTypeText: function (report_type, isSimple) {
			// Get the default button text based on the report builder type
			let defaultButtonText = report_type === "PROTOCOL" ? "Protocol"
				: report_type === "APPENDIX_E2" ? "Appendix E2"
					: report_type === "SECONDPASS" ? "2nd Pass Extraction Articles"
						: report_type === "ARTICLE_REVIEWS" ? "Full Review Data"
							: report_type === "SECOND_PASS_WORD" ? "2nd Pass Extraction Articles"
								: report_type === "SECOND_PASS_RIS" ? "2nd Pass Extraction Articles"
									: report_type === "ARTICLE_REVIEWS_RIS" ? "Full Review Data"
										: report_type === "TERMS_SUMMARY" ? "Search Terms Summary"
											: report_type === "TERMS_SUMMARY_EXCEL" ? "Search Terms Summary"
												: report_type === "CONDENSED_REPORT" ? "Condensed Report"
													: report_type === "PRISMA" ? "Prisma"
														: report_type === "REPORT" ? "Report"
															: report_type === "SEARCH_VALIDATION_ZIP" ? "Search Validation Zip"
																: report_type === "DUPLICATES" ? "Duplicates Report"
																	: report_type === "FULL_TEXT_ZIP" ? "Full Text Zip"
																		: report_type === "AUDIT_TRACKING_LOGS" ? "Audit Tracking Logs"
																			: report_type === "DEVICE_HISTORY" ? "Device History Report"
																				: report_type === "CUMULATIVE_REPORT" ? "Cumulative Report"
                                          : report_type === "ABBOTT_REPORT" ? "Abbott Report"
																					  : "Not Found";

			defaultButtonText = isSimple ? "Simple " + defaultButtonText : defaultButtonText;
			return defaultButtonText;
		},
		checkReportStatus: function () {
			const interval2 = setInterval(function () {
				const runningReports = this.reports.filter(report => report.status === 'RUNNING');
				if (runningReports.length) {
					const ids = runningReports.map(report => report.id);
					const postData = { running_reports_ids: ids };
					axios.post(reportStatusURL, data = postData)
						.then(
							res => {
								const { is_completed, reports } = res.data;
								if (is_completed) {
									const newReports = this.reports.map(report => {
										for (let i = 0; i < reports.length; i++)
											if (reports[i].id === report.id)
												return reports[i];

										return report;
									});
									this.reports = newReports;
									clearInterval(interval2);
									console.log("Interval has been cleared");
								};
							},
							err => {
								console.log({ err });
								clearInterval(interval2);
								console.log("Interval has been cleared");
							}
						);
				} else {
					clearInterval(interval2);
					console.log("Interval has been cleared");
				}
			}.bind(this), 5000);
		},
		afterRunReport: function () {
			this.hideGenerateReportSlider(true);
			setTimeout(() => {
				this.loadData(check_status = true);
			}, 2000);
		},
		convertTimeZone: function (timestamp) {
			// convert to current user timezone here
			var date = new Date(timestamp)
			// convert to new date time form
			new_date = this.formatDate(date)
			return new_date;
		},
		padTo2Digits: function (num) {
			return num.toString().padStart(2, '0');
		},
		formatDate: function (date) {
			return (
				[
					this.padTo2Digits(date.getDate()),
					this.padTo2Digits(date.getMonth() + 1),
					date.getFullYear()
				].join('-') +
				' ' +
				[
					this.padTo2Digits(date.getHours()),
					this.padTo2Digits(date.getMinutes()),
				].join(':')
			);
		},
		onShowCommentModal: function (report) {
			this.reportComment = report.comment || '';
			this.activeCommentModal = report.id;
		},
		hideCommentModal: function () {
			this.activeCommentModal = null;
		},
		onSort(sortValue) {
			if (this.sorting === sortValue && this.sorting.includes("-")) sortValue = sortValue.replace("-", "");
			if (this.sorting === sortValue && !this.sorting.includes("-")) sortValue = `-${sortValue}`;
			this.sorting = sortValue;

			this.loadData();
		},
		onSearch(e) {
			e.preventDefault();
			const reportTypesInput = document.getElementsByName("report-type");
			this.filterTypes = [];
			for (let i = 0; i <= reportTypesInput.length - 1; i++) {
				const dbName = reportTypesInput[i].value;
				if (reportTypesInput[i].checked) {
					this.filterTypes.push(dbName);
					if (dbName === "SECONDPASS")
						this.filterTypes.push("SECOND_PASS_WORD");
					if (dbName === "TERMS_SUMMARY")
						this.filterTypes.push("TERMS_SUMMARY_EXCEL");
				}

			};
			this.hideModal('filters-slider');
			this.loadData();
		},
		showGenerateReportSlider: function () {
			this.selectedFileForamt = ''; // Reset to empty
			this.selectedReportType = ''; // Reset report type
			this.reportStep = 1; // Reset to first step
			this.isGenerateReportSliderOpen = true;
			console.log(this.isGenerateReportSliderOpen)
		},
		hideGenerateReportSlider(close=false) {
			if (this.reportStep === 1 || close) this.isGenerateReportSliderOpen = false;
			else this.reportStep = 1;

			// Reset state after hiding
			setTimeout(() => {
				this.reportStep = 1;
				this.selectedFileForamt = '';
				this.selectedReportType = '';
				this.isValidationErrorModalVisible = false;
			}, 300);
		},
		onReportStepAction() {
			if (this.reportStep === 1) {
				// Move to the next step
				this.reportStep = 2;
			} else {
				// Generate the report
				this.onRunReport(this.selectedReportType);
			}
		},
		onRunReport: function (reportType) {
			console.log(`Generating ${reportType}`);

			const postData = {
				report_type: reportType
			};
			// if (report_type === "report" && (this.project.type === "PMCF" || this.project.type === "Vigilance"))
			//     postData["report_type"] = "vigilance";

			axios.post(reportBuilderURL, data = postData)
				.then(
					res => this.afterRunReport(),
					err => {
						console.log({ err });
						this.hideGenerateReportSlider(true);
						let error_msg = this.handleErrors(err);
						error_msg += ", Still stuck? Get instant help from our team by submitting a ticket Here: https://share.hsforms.com/1jqB4CJx9RxyvGL3qQYo2rgcq0hk ."
						this.makeToast("danger", error_msg);
					}
				);
		},
		onDeleteReport: function (report_id) {
			this.selectedReportID = report_id;
			this.showModal("delete-report-modal-" + report_id);
		},
		onDeleteReportConfirmed: function () {
			this.hideModal("delete-report-modal-" + this.selectedReportID)

			// deleteReportURL this var de clared inside the django template
			const URL = deleteReportURL.slice(0, deleteReportURL.length - 2) + this.selectedReportID + "/";
			const deleteButtonID = "delete-" + this.selectedReportID;
			const deleteBTN = this.$refs[deleteButtonID][0];
			this.disableElement(deleteBTN, "Deleting...");

			axios.delete(URL)
				.then(
					res => {
						console.log(res);
						this.makeToast("success", `Report '${this.selectedReportID}' has been deleted successfully`);
						const deletedReportID = this.reports.findIndex(report => report.id === this.selectedReportID);
						this.reports.splice(deletedReportID, 1);
						this.enableElement(deleteBTN, "Delete");
					},
					err => {
						console.log({ err });
						let error_msg = this.handleErrors(err);
						this.makeToast("danger", error_msg);
						this.enableElement(deleteBTN, "Delete");
					}
				)

		},
		onUpdateReportComment: async function (report) {
			console.log(report.id);
			const values = { comment: this.reportComment };

			// Show loading state in some other way if needed
			this.isUpdatingComment = true;

			const URL = updateCommentURL.slice(0, updateCommentURL.length - 2) + report.id + "/";
			try {
				const res = await axios.patch(URL, data = values);
				const newReports = this.reports.map(item => {
					if (item.id === report.id) {
						item.comment = this.reportComment;
					};
					return item;
				});
				this.reports = newReports;
				this.makeToast("success", "Report comment is updated successfully!");
				// this.enableElement(updateCommentBTN, "Save");
				this.isUpdatingComment = false;
				this.hideCommentModal();

			} catch (error) {
				const error_msg = this.handleErrors(error);
				this.makeToast("danger", error_msg);
				// this.enableElement(updateCommentBTN, "Save");
				this.isUpdatingComment = false;
			}
		},
		loadData: async function (check_status = false) {
			// check_status create a interval to check and update the status of reports
			if (!check_status) this.isRecordsLoading = true;
			let URL = reportBuilderURL;

			if (this.searchTerm) {
				if (URL.includes("?"))
					URL = `${URL}&search=${this.searchTerm}`;
				else
					URL = `${URL}?search=${this.searchTerm}`;
			};
			if (this.filterTypes.length) {
				const types = this.filterTypes.join(",")
				if (URL.includes("?"))
					URL = `${URL}&types=${types}`;
				else
					URL = `${URL}?types=${types}`;
			};
			if (this.selectedStatus.length) {
				const status = this.selectedStatus.join(",")
				if (URL.includes("?"))
					URL = `${URL}&status=${status}`;
				else
					URL = `${URL}?status=${status}`;
			};
			if (this.sorting) {
				if (URL.includes("?"))
					URL = `${URL}&sorting=${this.sorting}`;
				else
					URL = `${URL}?sorting=${this.sorting}`;
			};

			this.appliedStatus = [...this.selectedStatus];

			axios.get(URL)
				.then(
					res => {
						console.log(res);
						const { configuration, validator, project, reports, project_appraisals, logo_exsite } = res.data;
						this.isRecordsLoading = false;
						this.configuration = configuration;
						this.project = project;
						this.validator = validator;
						this.reports = reports;
						this.projectAppraisals = project_appraisals;
						this.$nextTick(() => {
							this.checkReportStatus("report");
						});
						if (check_status) {
							this.checkReportStatus();
						};
						// check if client has a logo and send warning based on that.
						// if (logo_exsite == false){
						//     this.showModal("client-logo-warning");
						// }
					},
					err => {
						console.log(err);
						this.isRecordsLoading = false;
					}
				);
		},
		selectReportType(typeValue) {
			console.log('Setting report type to:', typeValue);

			// Store the previous report type to check if it changed
			const previousReportType = this.selectedReportType;
			const isReportTypeChanged = previousReportType !== typeValue;

			// Update the selected report type
			this.selectedReportType = typeValue;

			// Reset the iframe loading states
			this.iframeLoading = true;
			this.zipIframeLoading = true;
			this.isValidationErrorModalVisible = false;

			// If report type changed, reset the ZIP file index to 0
			if (isReportTypeChanged) {
				console.log('Report type changed, resetting ZIP file index to 0');
				this.selectedZipFileIndex = 0;
			}

			// If it's a ZIP report type, load the first file after a delay
			if (this.selectedFileForamt === 'zip') {
				// Allow time for Vue to update the data first
				setTimeout(() => {
					const reportType = this.zipReportTypes.find(type => type.value === this.selectedReportType);
					if (reportType && reportType.exampleLink && reportType.exampleLink.length > 0) {
						this.$nextTick(() => {
							if (this.$refs.zipPreviewIframe) {
								const iframe = this.$refs.zipPreviewIframe;

								// Always use the first file (index 0) when changing report types
								const fileLink = reportType.exampleLink[0].exampleLink;

								if (fileLink) {
									console.log('Setting iframe source to first file');
									iframe.src = fileLink;
								}
							}
						});
					}
				}, 150); // Increased timeout for more reliability
			} else {
				// For non-ZIP formats, ensure iframe loads properly
				this.$nextTick(() => {
					if (this.$refs.previewIframe) {
						const iframe = this.$refs.previewIframe;
						const currentSrc = this.getPreviewLink();

						if (currentSrc) {
							iframe.src = currentSrc;
						}
					}
				});
			}
		},
		getPreviewLink() {
			if (this.selectedFileForamt === 'excel') {
				const reportType = this.excelReportTypes.find(type => type.value === this.selectedReportType);
				return reportType ? reportType.exampleLink : null;
			} else if (this.selectedFileForamt === 'word') {
				const reportType = this.wordReportTypes.find(type => type.value === this.selectedReportType);
				return reportType ? reportType.exampleLink : null;
			} else if (this.selectedFileForamt === 'zip') {
				// For ZIP files, we want to show the file list instead of a direct link
				const reportType = this.zipReportTypes.find(type => type.value === this.selectedReportType);
				// The exampleLink property is an array in this case, so we return the entire object
				return reportType ? reportType : null;
			}

			return null;
		},
		iframeLoaded() {
			console.log("Iframe loaded");
			// Short delay to ensure smooth transition
			this.iframeLoading = false;
		},
		manuallyHideLoader() {
			setTimeout(() => {
				if (this.iframeLoading) {
					console.log("Manually hiding loader after timeout");
					this.iframeLoading = false;
				}
			}, 8000); // 8 seconds timeout as fallback
		},
		selectZipFile(index) {
			console.log('Selecting ZIP file at index:', index);
			this.selectedZipFileIndex = index;
			this.zipIframeLoading = true;

			// Force iframe to reload
			this.$nextTick(() => {
				if (this.$refs.zipPreviewIframe) {
					const iframe = this.$refs.zipPreviewIframe;
					const currentSrc = this.getSelectedZipFileLink();

					if (currentSrc) {
						// Set the source with a timestamp to force reload
						iframe.src = currentSrc + (currentSrc.includes('?') ? '&' : '?') + '_t=' + Date.now();
					}
				}

				// Scroll the selected file into view
				this.$nextTick(() => {
					const selectedFileBox = document.querySelector('.zip-file-box.selected');
					if (selectedFileBox) {
						selectedFileBox.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
					}
				});
			});
		},
		getSelectedZipFileLink() {
			// Return null if we're not dealing with a zip file format
			if (this.selectedFileForamt !== 'zip') {
				return null;
			}

			// Get the selected report type object
			const reportType = this.zipReportTypes.find(type => type.value === this.selectedReportType);

			// Check if report type exists and has exampleLink array
			if (!reportType || !reportType.exampleLink || reportType.exampleLink.length === 0) {
				return null;
			}

			// Always use index 0 when the report type changes
			// Compare the current report type with the previous one
			if (this._lastReportType !== this.selectedReportType) {
				this._lastReportType = this.selectedReportType;
				this.selectedZipFileIndex = 0;
			}

			// Force index 0 if undefined/null to ensure we always have a selection
			const index = (this.selectedZipFileIndex === null || this.selectedZipFileIndex === undefined) ? 0 : this.selectedZipFileIndex;

			// Additional safety check to ensure index is valid
			if (index >= reportType.exampleLink.length) {
				console.log('Index out of bounds, defaulting to 0');
				this.selectedZipFileIndex = 0;
				return reportType.exampleLink[0].exampleLink;
			}

			// Return the link
			return reportType.exampleLink[index].exampleLink;
		},
		zipIframeLoaded() {
			console.log("ZIP iframe loaded");
			setTimeout(() => {
				this.zipIframeLoading = false;
			}, 300);
		},
		selectFileFormat(format) {
			this.selectedFileForamt = format;
			this.selectedReportType = '';
			this.selectedZipFileIndex = null; // Reset ZIP file selection
		},
		navigateZipFiles(direction) {
			if (!this.getPreviewLink() || !this.getPreviewLink().exampleLink) {
				return;
			}

			const fileCount = this.getPreviewLink().exampleLink.length;

			if (direction === 'next' && this.canNavigateNext()) {
				this.selectZipFile(this.selectedZipFileIndex === null ? 1 : this.selectedZipFileIndex + 1);
			} else if (direction === 'prev' && this.canNavigatePrev()) {
				this.selectZipFile(this.selectedZipFileIndex === null ? 0 : this.selectedZipFileIndex - 1);
			}
		},
		canNavigatePrev() {
			return this.selectedZipFileIndex !== null && this.selectedZipFileIndex > 0;
		},
		canNavigateNext() {
			if (!this.getPreviewLink() || !this.getPreviewLink().exampleLink) {
				return false;
			}

			const fileCount = this.getPreviewLink().exampleLink.length;
			return (this.selectedZipFileIndex === null && fileCount > 1) ||
				(this.selectedZipFileIndex !== null && this.selectedZipFileIndex < fileCount - 1);
		},
		showValidationErrorModal() {
			console.log("Showing validation error modal");
			// Change the step to hide the preview panel 
			this.isValidationErrorModalVisible = true;
		},
		closeValidationErrorModal() {
			console.log("Closing validation error modal");
			this.isValidationErrorModalVisible = false;
		},
	},
	async mounted() {
		let uri = window.location.href.split('?');
		if (uri.length == 2) {
			let query_params = uri[1].split('&');
			if (query_params.includes("type=protocol")) {
				this.filterTypes = ["PROTOCOL", "SIMPLE_PROTOCOL", "TERMS_SUMMARY", "TERMS_SUMMARY_EXCEL"];
			}
		}
		await this.loadData();
		const timeOut = setTimeout(() => {
			this.styleTooltips();
			return clearTimeout(timeOut);
		}, 2000);
	}
})
