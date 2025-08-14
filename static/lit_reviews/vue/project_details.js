axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#project-details-app',
    mixins: [globalMixin],
    delimiters: ["[[","]]"],
    data() {
        return {
            actions: [],
            users: [],
            action_types:[],
            isValid: true,
            isLoading: false,
            validation_message: '',
            tablePageIndicator: "",
            searchTerm: "",
            selectedUser:"",
            selectedStartDate:"",
            selectedEndDate:"",
            selectedTypes: [],
            sort: "-timestamp",
            appliedSort: "-timestamp",
            pagination: {
                current: 0,
                count: 0,
                next: 0,
                previous: 0,
                last: 0,
                page_range: []
            },
            tourGuideSteps: [
              {
                target: '#menu-tour-step-00',
                title: "Sidebar Menu",
                content: `
                  This is where the steps for your entire review live.
                  Generally, it goes from the top down (start with Search Protocol,  then pick Search Terms etc.).
                `,
              },
              {
                target: '#menu-tour-step-01',
                title: "Advance / Basic modes",
                content: `
                    Here you see a switch to toggle between Basic and Advanced modes:
                    Basic Mode: Contains only the essential pages you need to complete the setup and report generation.
                    Advanced Mode: Provides additional options and extra pages for better filtering, viewing results, and enhanced control.
                `,
              },
              {
                target: '#menu-tour-step-02',
                title: "Projects List",
                content: 'This will take you back to the main page where you have all your projects listed',
              },
              {
                target: '#menu-tour-step-03',
                title: "Search Protocol",
                content: `
                  This page is for defining what databases you will search,  what filters you will use on those searches, and the date ranges for your review.  
                `,
              },
              {
                target: '#menu-tour-step-04',
                title: "Search Terms",
                content: 'This page is where you will discover and lock-in your search terms for the review.',
              },
              {
                target: '#menu-tour-step-05',
                title: "Protocol Repository",
                content: '(Optional) - if you would like to generate a Search Protocol document,  you can do it here with our report builder.',
              },
              {
                target: '#menu-tour-step-06',
                title: "Run Searches",
                content: `
                  This is where you will run all of your searches or upload your own results.  
                  Remember, we support automatic search collection from PubMed, PMC, Cochrane, Clinicaltrials.gov,  Scholar, and FDA Maude! 
                `,
              },
              {
                target: '#menu-tour-step-07',
                title: "Unclassified Articles",
                content: `  
                  This is where you perform your Abstract Review (we call it the 1st pass).  
                `
              },
              {
                target: '#menu-tour-step-08',
                title: "Adverse Events",
                content: '(Optional)  If you have chosen Adverse Event Databases to include in your search, they will be handled here.',
              },
              {
                target: '#menu-tour-step-09',
                title: "Clinical Appraisals",
                content: `
                  This is the Full-Text Review of your Retained articles.  You will be performing your data extraction here (we call it the 2nd Pass Review).  
                `,
              },
              {
                target: '#menu-tour-step-10',
                title: "Generated Outputs",
                content: 'Finished Your Review?  Generate a report (in many formats),  your PRISMA chart,  Search Validation, and more on this page. ',
              },
              {
                target: '#menu-tour-step-11',
                title: "Exclusion Reasons",
                content: 'Pre-define your exclusion reasons (to be used in the Abstract Review)  here.  You will be able to add additional custom comments on each exclusion in the Abstract Review Screen (Unclassified)',
              },
              {
                target: '#menu-tour-step-12',
                title: "Update Keywords",
                content: '(Optional) Keywords are there to help you review faster.  They offer simple color-coded highlighting to help sort and determine good abstracts from useless ones.',
              },
              {
                target: '#menu-tour-step-13',
                title: "Article Tags",
                content: 'Want an extra way to sort your Articles while you’re doing your review?  Use Tags to label Articles in any way you see fit. ',
              },
              {
                target: '#menu-tour-step-14',
                title: "All Citations",
                content: 'Think of this as the full Library of your review.  You can sort, search and filter your Citations here. ',
              },
              {
                target: '#menu-tour-step-15',
                title: "Upload Full Text",
                content: 'While we automatically download and save Full-Texts that are freely available, some of your Retained Articles will require you to purchase separately and upload it.  You can upload your PDFs in this screen. ',
              },
              {
                target: '#menu-tour-step-16',
                title: "Fix Bad Citations",
                content: '(Optional) Sometimes article data will come to us from the database missing pieces or malformed.  You can attempt to look-up and correct article citations here. ',
              },
              {
                target: '#menu-tour-step-17',
                title: "Manual AE Searches",
                content: '(Optional) These are for Adverse Event Databases that we can’t support search and upload functions on.  Here you will add in your relevant Adverse Events (from searching separately) to be included in your final reports. ',
              },
              {
                target: '#menu-tour-step-18',
                title: "AE DB Summaries",
                content: '(Optional) This is a screen allows you to enter in your conclusions and writeups to address any Adverse Events found on your search.  Remember Adverse Event Searches are optional!',
              },
              {
                target: '#menu-tour-step-19',
                title: "Configure Extraction Fields",
                content: 'What type of data do you want to extract and record from your Retained Articles?  This view lets you set the templates for the type of data you will extract.  You can use our default categories, or build your own. ',
              },
            ],
        }
    },
    computed: {
        isFiltersApplied() {
            const isApplied = this.selectedTypes.length > 0 || 
                    this.selectedUser !== "" || 
                    this.selectedStartDate !== "" || 
                    this.selectedEndDate !== "";
            
            return isApplied;
        },
    },
    methods : {
        // Helpers
        // actions
        sortBy(sorting){
          if (sorting == "timestamp"){
            if (this.sort === "timestamp"){
              this.sort = "-timestamp";
            }else {
              this.sort = "timestamp";
            }
          }
          else if (sorting=="actor_object_id") {
            if (this.sort === "actor_object_id"){
              this.sort = "-actor_object_id";
            }else {
              this.sort = "actor_object_id";
            }
          }
          else if (sorting=="verb") {
            if (this.sort === "verb"){
              this.sort = "-verb";
            }else {
              this.sort = "verb";
            }
          }
          this.loadActions(1);
        },
        onSearch(e) {
            e.preventDefault();
            console.log("selectedUser",this.selectedUser);
            console.log("selectedTypes",this.selectedTypes);
            this.hideModal('filters-slider');
            this.loadActions(1);
        },
        onClearFilters() {
            // this.selectedStates = [];
            this.searchTerm = "";
            this.selectedUser = "",
            this.selectedTypes = [],
            this.selectedStartDate = "",
            this.selectedEndDate = "",
            this.loadActions(1);
        },
        onCloseFilters() {
            // this.selectedStates = this.getCurrentStates();
            this.hideModal('filters-slider');
        },
        formatDescription(description) {
          let changes = description.split(';').filter(change => change.trim() !== "");
          let formattedChanges = changes.map(change => {
              // Use regex to extract the field name, old value, and new value
              let match = change.match(/Field "(.*?)" changed from "(.*?)" to "(.*?)"/);
              if (match) {
                  let fieldName = match[1].replace(/_/g, ' ');;
                  let oldValue = match[2];
                  let newValue = match[3];
                  
                  // Return an HTML list item with bolded old and new values
                  return `<li class="action-description-list">Field <strong>${fieldName}</strong> changed from <strong>${oldValue}</strong> to <strong>${newValue}</strong>.</li>`;
              }
              return change;  // If no match, return the unchanged string
          });

          // Wrap the formatted changes in an unordered list
          return `<ul>${formattedChanges.join('')}</ul>`;
        },
        initiatTourGuide() {
          // introJs().start();
          const BASIC_STEPS = [...Array(11).keys()];
          const ADVANCED_STEPS =  [...Array(20).keys()];;

          let steps = document.getElementsByClassName("menu-sub-option-list")[0].classList.contains("hide") ? BASIC_STEPS : ADVANCED_STEPS;
          const tourSteps = steps.map(step => ({
            title: this.tourGuideSteps[step].title,
            element: document.querySelector(`#menu-tour-step-${step}`),
            intro: this.tourGuideSteps[step].content,
          }));

          introJs().setOptions({
            steps: tourSteps
          }).start();
        },
        loadActions(page = 1) {
            // uclassifiedRefresh: we don't show popup modal when update states in unclassified page 
            if (page < 1 || (page > this.pagination.last && this.pagination.last!== 0))
              return ;
            let URL = ACTIONSURL; 

            if (this.searchTerm) {
                if (URL.includes("?"))
                  URL =  `${URL}&search=${this.searchTerm}`;
                else
                  URL =  `${URL}?search=${this.searchTerm}`;
              };
            
            if (this.selectedUser) {
                if (URL.includes("?"))
                  URL =  `${URL}&selected_user=${this.selectedUser}`;
                else
                  URL =  `${URL}?selected_user=${this.selectedUser}`;
            };

            if (this.selectedTypes.length) {
                if (URL.includes("?"))
                  URL =  `${URL}&selected_types=${this.selectedTypes}`;
                else
                  URL =  `${URL}?selected_types=${this.selectedTypes}`;
            };

            if (this.selectedStartDate) {
                if (URL.includes("?"))
                  URL =  `${URL}&selected_start_date=${this.selectedStartDate}`;
                else
                  URL =  `${URL}?selected_start_date=${this.selectedStartDate}`;
            };

            if (this.selectedEndDate) {
                if (URL.includes("?"))
                  URL =  `${URL}&selected_end_date=${this.selectedEndDate}`;
                else
                  URL =  `${URL}?selected_end_date=${this.selectedEndDate}`;
            };

            if (this.sort){
              if (URL.includes("?"))
                URL =  `${URL}&ordering=${this.sort}`;
              else
                URL =  `${URL}?ordering=${this.sort}`;
            };

            if (page){
              if (URL.includes("?"))
                URL =  `${URL}&page=${page}`;
              else
                URL =  `${URL}?page=${page}`;
            };
    
            this.isLoading = true;
            axios.get(URL)
              .then(
                res => {
                    console.log(res);
                    this.actions = res.data.results;
                    this.isLoading = false;
                    console.log(this.actions);
      
                    this.pagination.current = page;
                    this.pagination.count = res.data.count;
                    this.pagination.next = res.data.next;
                    this.pagination.previous = res.data.previous;
                    this.pagination.last =  Math.floor(this.pagination.count/10);
                    if ((this.pagination.count % 10) > 0)
                        this.pagination.last += 1;
                    this.pagination.page_range = [
                        this.pagination.current-1, 
                        this.pagination.current, 
                        this.pagination.current+1
                    ];
                    const currentPageTotalIncriment = this.actions.length < 10 ? 
                    this.actions.length + (this.pagination.current-1) * 10
                    : this.pagination.current * 10
                    this.tablePageIndicator = `${this.pagination.current*10-9}-${currentPageTotalIncriment} Of ${this.pagination.count}`;
                    console.log(this.pagination);
                },
                err => {
                  console.log(err);
                  this.isLoading = false;
                }
              );
          },
        loadActionsFilters() {
            let URL = ACTIONSFILTERSURL; 
            axios.get(URL).then( 
                res => {
                    console.log(res);
                    this.users = res.data.users;
                    this.action_types = res.data.verbs;
                    console.log(this.users);
                },
                err => {
                  console.log(err);
                  this.isLoading = false;
                }
              );
        }
    }, 
    mounted() {
        this.loadActions();
        this.loadActionsFilters();
        const timeOut = setTimeout(() => {
          this.styleTooltips();
          return clearTimeout(timeOut);
        }, 2000);
    }
})
