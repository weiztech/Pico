axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

const ExcludeButtonDropDown = {
  template: `
  <button 
    :ref="'exclude-button'+review.id" 
    :disabled="isLoading" 
    :class="{'ai-suggested': isShowAISuggestions && review.ai_state_decision === 'E'}" 
    class="error-button exclude-button"
  > 
    <div v-on:click="onOpenDropDown" class="exclude-item"> 
      <div 
        class="center-v" 
        :title="isShowAISuggestions && review.ai_state_decision === 'E' ? 'AI Suggested' : ''"
        :class="{'tooltip-elt': isShowAISuggestions && review.ai_state_decision === 'E'}" 
      >
        <img
          v-if="isShowAISuggestions && review.ai_state_decision === 'E'" 
          class="header-right-icon mr" 
          style="width: 15px;" 
          :src="aiIcon" alt="show-pdf-file-icon" srcset=""
        />
        Exclude  
      </div>
    </div>
    <div v-on:click="onExcludeWithComment" class="exclude-item comment-exclude"> 
      <svg width="14" height="15" viewBox="0 0 14 15" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M6.9995 8.8125V7.5M6.9995 7.5V6.1875M6.9995 7.5H5.68713M6.9995 7.5H8.31188M12.249 7.5C12.249 8.2547 12.0898 8.97221 11.8031 9.62076L12.25 12.7495L9.56897 12.0792C8.80946 12.5064 7.93293 12.75 6.9995 12.75C4.10028 12.75 1.75 10.3995 1.75 7.5C1.75 4.60051 4.10028 2.25 6.9995 2.25C9.89872 2.25 12.249 4.60051 12.249 7.5Z" stroke="#FEF3F2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>

    <!-- Exclude Options Drop Down -->
    <div class="custom-options exclusion-options" :ref="'exclude-options'+review.id">
        <ul :class="isCommentExclude ? 'exclusions-list' : ''">
            <li 
                v-for="exclusion in exclusions" 
                v-on:click="onExclude(exclusion)" 
                :key="exclusion.id" 
                :class="[{'active': exclusion.reason === selectedReason}]"
            > 
                <div class="center-v">
                  <div v-if="isShowAISuggestions && review.ai_exclusion_reason == exclusion.reason" class="ai-suggested-reason">
                    <img 
                      class="header-right-icon" 
                      style="width: 15px;" 
                      :src="aiIconBlue" alt="show-pdf-file-icon" srcset=""
                    />
                  </div>
                  <div style="text-align: start;"> {{exclusion.reason}} </div>
                </div>
            </li>
        </ul>
        <div v-if="isCommentExclude" class="exclusion-dropdown-footer">
          <label class="hint center-v" :for="'comment-'+review.id"> 
            Custom Exclusion Comment (Optional) 
            <div style="margin-left: 3px; height: 16px;" title="Add an optional detailed reason about why this article was excluded. You must still choose a standard reason as well.">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8 8V5M8 10.2236V10.25M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8Z" stroke="#848D9F" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
          </label>
          <textarea v-model="exclusionComment" id="'comment-'+review.id" rows="3" placeholder="You can also add a customer exclusion comment in addition to the selected reason...">
          </textarea>
          <div class="center-v ml-auto w-max">
            <button v-on:click="onCancel" class="secondary-gray-button small-button mr"> cancel </button>
            <button 
              v-on:click="onCommentExclude"
              class="primary-button small-button" 
              :disabled="!selectedReason || isLoading"
            > 
              <div class="center-v">
                <div> Apply </div>
                <div style="margin-left: 3px; height: 16px;" title="Please choose a standard exclusion reason from the drop-down to proceed.">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M8 8V5M8 10.2236V10.25M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8Z" stroke="#848D9F" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
              </div>
            </button>
          </div>
        </div>
    </div>
  </button>
`,
  mixins: [globalMixin],  
  props: ["review", "exclusions", "onExcludeArticle", "aiIcon", "aiIconBlue", "isShowAISuggestions"],
  data() {
    return {
      isLoading: false,
      isCommentExclude: false,
      exclusionComment: "",
      selectedReason: "",
    }
  },
  methods: {
    onOpenDropDown() {
      this.isCommentExclude = false;
      this.$refs['exclude-options'+this.review.id].classList.toggle("active");
      const isDropdownOffScreen = this.isDropdownOffScreen();
      if (isDropdownOffScreen === true)
        this.$refs['exclude-options'+this.review.id].classList.add("upper-dropdown");
    },
    onExcludeWithComment() {
      this.isCommentExclude = true;
      this.$refs['exclude-options'+this.review.id].classList.toggle("active");
      const isDropdownOffScreen = this.isDropdownOffScreen();
      if (isDropdownOffScreen === true)
        this.$refs['exclude-options'+this.review.id].classList.add("upper-dropdown");
    },
    onCancel() {
      this.$refs['exclude-options'+this.review.id].classList.remove("active");
    },
    isDropdownOffScreen() {
      let dropdown = this.$refs['exclude-options'+this.review.id];
      let dropdownRect = dropdown.getBoundingClientRect();
      // let viewportWidth = window.innerWidth || document.documentElement.clientWidth;
      let viewportHeight = window.innerHeight || document.documentElement.clientHeight;
      // dropdownWrapper = document.getElementsByClassName("body-content")[0];

      return (
        // dropdownRect.right > viewportWidth ||
        dropdownRect.bottom > viewportHeight
      );
    },
    async onExclude(exclusion) {
      if (this.isCommentExclude) {
        this.selectedReason = exclusion.reason;
      } else {
        this.isLoading = true;
        this.$refs['exclude-options'+this.review.id].classList.remove("active");
        try {
          await this.onExcludeArticle(exclusion, this.review.id);
          this.isLoading = false;
        } catch (e) {
          console.log(e);
          this.isLoading = false;
        }   
      } 
    },
    async onCommentExclude() {
      this.isLoading = true;
      this.$refs['exclude-options'+this.review.id].classList.remove("active");
      try {
        const exclusion = this.exclusions.find(exclusion => exclusion.reason === this.selectedReason);
        await this.onExcludeArticle(exclusion, this.review.id, this.exclusionComment);
        this.isLoading = false;
      } catch (e) {
        console.log(e);
        this.isLoading = false;
      }  
    },
  },
  mounted() {
    // check if article is excluded
    if (this.review.state_symbole === 'E') {
      this.selectedReason = this.review.exclusion_reason;
      if (this.review.exclusion_comment)
        this.exclusionComment = this.review.exclusion_comment;
    }

    // Handle Click outside to close dropdown
    const el = this.$refs['exclude-button'+this.review.id];
    el.clickOutsideEvent = event => {
      // here I check that click was outside the el and his children
      if (!(el == event.target || el.contains(event.target))) {
        this.$refs['exclude-options'+this.review.id].classList.remove("active");
      }
    };
    document.addEventListener("click", el.clickOutsideEvent);
  },
  beforeDestroy() {
    const el = this.$refs['exclude-button'+this.review.id];
    document.removeEventListener("click", el.clickOutsideEvent);
  },
};

var app = new Vue({
  el: '#app',
  components: {
    'exclude-button-drop-down': ExcludeButtonDropDown,
  },
  mixins: [globalMixin],
  delimiters: ["[[", "]]"],
  data() {
    return {
      isLoading: false,
      isArticleUpdateLoading: false,
      isBulkUpdateLoading: false,
      isHistoricalStatusLoading :false,
      stateSymbole: "",
      articleState: "",
      isUnclassified: false,
      isAISuggestionsLoading: false,
      isShowAISuggestions: false,

      articles:[],
      comments:[],
      exclusions: [],
      articleTags: [],
      dbs: [],
      selectedReviews: [],
      isCheckAll: false,
      comment:{
        text:"",
      },
      sort: "article__title",
      appliedSort: "article__title",
      sortOptions: [
        {name: "ID", value: "id"},
        {name: "Title", value: "article__title"},
        {name: "Score", value: "score"},
      ],
      sortingDirection: "Ascending",
      sortingDirectionOptions: [
        {name: "Ascending", value: "Ascending"},
        {name: "Descending", value: "Descending"},
      ],
      searchTerm: "",

      viewType: window.location.search.includes("state=U") ? "Board View" : "Table View",
      currentArticle: {
        id: null,
        state_symbole: "",
        notes: "",
        exclusionComment: "",
        exclusionReason: "",
        history: [],
        selected: false,
      },
      bulkArticle: {
        state_symbole: "",
        notes: "",
        exclusionComment: "",
        exclusionReason: "",
      },
      statesOptions: [
        {name: "Select Article State", value: ""},
        {name: "Unclassified", value: "U"},
        {name: "Included", value: "I"},
        {name: "Excluded", value: "E"},
        {name: "Maybe", value: "M"},
        {name: "Duplicate", value: "D"},
      ],

      // appliedStates on the backend / selectedStates, selectedTags on the frontend.
      selectedStates: [],
      selectedTags: [],

      minScoreValue: null,
      maxScoreValue: null,
      fromScoreValue: null,
      toScoreValue: null,
      isScoreFilterApplied: false,
      sliderColor:"#6B7281",
      rangeColor:"#206AFF",
      steps: 10,

      tablePageIndicator: "",
      appliedStates: [],
      currentURL: "",
      selectedDatabases: [],
      pagination: {
        current: 0,
        count: 0,
        next: 0,
        previous: 0,
        last: 0,
        page_range: []
      },
    }
  },
  computed: {
    articleTagsOptions() {
      let tagsOptions =  this.articleTags.map(tag => ({
          name: tag.name,
          value: tag.id,
          color: tag.color,
        })
      );
      tagsOptions = [{
        name: "Add",
        value: "",
      }, ...tagsOptions];
      return tagsOptions;
    },
    exclusionOptions: function() {
      let options =  this.exclusions.map(exclusion => ({
        name: exclusion.reason,
        value: exclusion.reason,
      })
    );
    options = [{
      name: "Select Exclusion Reason",
      value: "",
    }, ...options];
    return options;
    },
    isFiltersApplied() {
      if (this.isUnclassified)
        return this.selectedDatabases.length || this.selectedTags.length || this.isScoreFilterApplied;
      else
        return this.selectedStates.length || this.selectedDatabases.length || this.selectedTags.length || this.isScoreFilterApplied;
    },
  },
  methods: {
    // helpers
    convertDate(dateString) {
      const date = new Date(dateString);
      const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
      const formattedDate = `${months[date.getMonth()]}, ${date.getDate()}, ${date.getFullYear()}`;
      return formattedDate;
    },
    onViewSource(event, review) {
      event.preventDefault();
      if (review.article.url && review.article.url !== "Not Available") {
        let sourceLinkTagElems = this.$refs['source-link-'+review.id];
        if (sourceLinkTagElems.length){
          const sourceLinkTagElem = sourceLinkTagElems[0]
          sourceLinkTagElem.click();
        }
      } else {
        this.makeToast("error", "Opps... the source link for this article is Unavailable.")
      }
    },
    initiateScoreFilterValues(res) {
      const oldScoreMinValue = this.minScoreValue ;
      const oldScoreMaxValue = this.maxScoreValue;

      this.minScoreValue = res.data.min_score;
      this.maxScoreValue = res.data.max_score;

      this.fromScoreValue = (this.fromScoreValue === null || this.fromScoreValue === oldScoreMinValue) ? res.data.min_score : this.fromScoreValue;
      this.toScoreValue = ( this.toScoreValue === null || this.toScoreValue === oldScoreMaxValue)  ? res.data.max_score : this.toScoreValue;
      if ((this.toScoreValue && this.toScoreValue !== this.maxScoreValue) || (this.fromScoreValue && this.fromScoreValue !== this.minScoreValue))
        this.isScoreFilterApplied = true;
      else 
        this.isScoreFilterApplied = false;
    },
    getState(symbole) {
      switch (symbole) {
        case "U":
          return "Unclassified";
        case "I":
          return "Retained";
        case "M":
          return "Maybe";
        case "E":
          return "Excluded";
        case "D":
          return "Duplicate";

        default:
          return "Unclassified";
      }
    },
    getStateClassName(stateSymbole) {
      switch (stateSymbole) {
        case "U":
          return "badge secondary";
        case "I":
          return "badge success";
        case "M":
          return "badge info";
        case "E":
          return "badge error";
        case "D":
          return "badge warning";

        default:
          return "badge secondary";
      }
    },
    validateUpdateArtice() {
      if (this.currentArticle.state_symbole === "E" && !this.currentArticle.exclusionReason) {
        this.makeToast("error", "You can't exclude an article without providing an exclusion reason, please select an option from exclusion reason dropwdown to exclude this article");
        return false;
      };
      return true;
    },
    truncateText(text) {
      return text.length > 30 ? text.slice(0, 30) + '...' : text; 
    },
    hideArticleDetails(review) {
      this.currentArticle = {
        id: null,
        state_symbole: "",
        notes: "",
        exclusionComment: "",
        exclusionReason: "",
        history: [],
        selected: false,
      };
      this.hideModal('article-details-'+review.id);
    },
    toggleState(state) {
      const index = this.selectedStates.indexOf(state);
      if (index > -1){
        this.selectedStates.splice(index, 1);
      } else {
        this.selectedStates.push(state)
      }
    },
    toggleTag(tag) {
      const index = this.selectedTags.indexOf(tag);
      if (index > -1){
        this.selectedTags.splice(index, 1);
      } else {
        this.selectedTags.push(tag)
      }
    },
    filterTagStyle(tag) {
      if (this.selectedTags.includes(tag.name)){
        let rgbaColor = this.hexToRgba(tag.color, 0.2);
        return `background-color: ${rgbaColor}; width: max-content; color: ${tag.color}; border: 1px solid ${tag.color}; padding: 8px 12px;`;
      }else{
        return `width: max-content; color: ${tag.color}; border: 1px solid ${tag.color}; padding: 8px 12px;`;
      }
    },
    getCurrentFilterValue(type) {
      const queryParams = this.currentURL.split("?");
      const queryParamsItems = queryParams[1].split("&");
      for (queryparam of queryParamsItems) {
        const filter = queryparam.split("=");
        const filterLabel = filter[0];
        const filterValue = filter[1];

        if (type===filterLabel)
          return filterValue;
      };

      return null;
    },
    getCurrentStates() {
      const values = this.getCurrentFilterValue("state");
      if (values){
        const states = values.split(",");
        this.appliedStates = states;
        return states;
      }
      return [];
    },
    getCurrentTags() {
      const values = this.getCurrentFilterValue("tag");
      if (values){
        const tags = values.split(",");
        this.appliedTags = tags;
        return tags;
      }
      return [];
    },
    toggleArticleActionVisibility(articleID) {
      const articleElem = this.$refs['article-review-'+articleID][0];

      // highlight article details box 
      const articleDetailsContainer = articleElem.getElementsByClassName("article-details")[0];
      articleDetailsContainer.classList.add("active");

      const articleDetailsActions = articleElem.getElementsByClassName("update-state-actions")[0];
      articleDetailsActions.style.display = "none";

    },
    updateArticle(updatedArticle, refreshPagination=false, sendNotification=true) {
      if (this.isUnclassified && refreshPagination && updatedArticle.state_symbole !== "U") {
        // if we are on Uclassified page we remove article instead since it's state has been updated
        this.articles = this.articles.filter(article => updatedArticle.id !== article.id);
        // Refresh Pagination
        this.loadArticles(false, this.pagination.current, true);
      } else {
        // update articles list with the new article if any changes / updates 
        this.articles = this.articles.map(article => {
          if (updatedArticle.id === article.id)
            return updatedArticle;
          return article;
        });
      };
      
      if (sendNotification) {
        // stream the update through webshocket channel to other live users
        this.sharedState.reviewSocket.send(JSON.stringify({
          'message': {
            user_username: userUsername,
            review_id: updatedArticle.id,
          },
          'type': 'review.state.updated',
        }));
      }
    },
    showUpdateProgressPopup: function(){
      popup = document.getElementById("update-loading-section");
      popup.style.display= "flex";
    },
    hideUpdateProgressPopup: function(){
        popup = document.getElementById("update-loading-section");
        popup.style.display= "none";
    },
    onExpandTagsSection: function(reviewID) {
      const termElm = this.$refs['term-section-'+reviewID][0];
      termElm.classList.toggle("active");
    },
    isShowTagExpand: function(reviewID) {
      const article = this.articles.find(ar => ar.id == reviewID);
      return article.tags.length > 1;
    },

    // Score Filter Slider
    controlFromSlider() {
      const fromSlider = this.$refs.fromSlider;
      const toSlider = this.$refs.toSlider;
      const fromTooltip = this.$refs.fromSliderTooltip;
      const toTooltip = this.$refs.toSliderTooltip;

      const [from, to] = this.getParsed(fromSlider, toSlider);
      this.fillSlider();
      if (from > to) {
        this.fromScoreValue = to;
      }
      this.setTooltip(fromSlider, fromTooltip);
    },
    controlToSlider() {
      const fromSlider = this.$refs.fromSlider;
      const toSlider = this.$refs.toSlider;
      const fromTooltip = this.$refs.fromSliderTooltip;
      const toTooltip = this.$refs.toSliderTooltip;

      const [from, to] = this.getParsed(fromSlider, toSlider);
      this.fillSlider();
      this.setToggleAccessible();
      if (from <= to) {
        this.toScoreValue = to;
      } else {
        this.toScoreValue = from;
      }
      this.setTooltip(toSlider, toTooltip, true);
    },
    getParsed(currentFrom, currentTo) {
      const from = parseInt(currentFrom.value, 10);
      const to = parseInt(currentTo.value, 10);
      return [from, to];
    },
    fillSlider() {
      const fromSlider = this.$refs.fromSlider;
      const toSlider = this.$refs.toSlider;
  
      if (toSlider && fromSlider) {
        const rangeDistance = this.maxScoreValue - this.minScoreValue;
        const fromPosition = this.fromScoreValue - this.minScoreValue;
        const toPosition = this.toScoreValue - this.minScoreValue;
        const linearBG = `linear-gradient(
          to right,
          ${this.sliderColor} 0%,
          ${this.sliderColor} ${(fromPosition) / (rangeDistance) * 100}%,
          ${this.rangeColor} ${((fromPosition) / (rangeDistance)) * 100}%,
          ${this.rangeColor} ${(toPosition) / (rangeDistance) * 100}%, 
          ${this.sliderColor} ${(toPosition) / (rangeDistance) * 100}%, 
          ${this.sliderColor} 100%)`;

        toSlider.style.background = linearBG;
      }
    },
    setToggleAccessible() {
      const toSlider = this.$refs.toSlider;
      if (Number(toSlider.value) <= 0) {
        toSlider.style.zIndex = 2;
      } else {
        toSlider.style.zIndex = 0;
      }
    },
    setTooltip(slider, tooltip, to=false) {
      // const value = slider.value;
      const value = to ? this.toScoreValue : this.fromScoreValue;
      tooltip.textContent = `${value}`;
      const thumbPosition = (value - this.minScoreValue) / (this.maxScoreValue - this.minScoreValue);
      const percent = thumbPosition * 100;
      const markerWidth = 20;
      const offset = (((percent - 50) / 50) * markerWidth) / 2;
      tooltip.style.left = `calc(${percent}% - ${offset}px)`;
    },
    createScale(min, max, step) {
      const scale = this.$refs.scale;
      const range = max - min;
      const steps = range / step;
      for (let i = 0; i <= steps; i++) {
        const value = min + (i * step);
        const percent = (value - min) / range * 100;
        const marker = document.createElement('div');
        marker.style.left = `${percent}%`;
        marker.textContent = `${value}`;
        scale.appendChild(marker);
      }
    },
    initSliderUpdate() {
      this.fillSlider();
      this.setToggleAccessible();
      this.setTooltip(this.$refs.fromSlider, this.$refs.fromSliderTooltip);
      this.setTooltip(this.$refs.toSlider, this.$refs.toSliderTooltip, true);
      this.createScale(this.minScoreValue, this.maxScoreValue, this.Steps);
    },

    // Actions
    sortBy(sorting){
      if (sorting == "article__title"){
        if (this.sort === "article__title"){
          this.sort = "-article__title";
        }else {
          this.sort = "article__title";
        }
      } else if (sorting=="score") {
        if (this.sort === "score"){
          this.sort = "-score";
        }else {
          this.sort = "score";
        }
      } else if (sorting=="id") {
        if (this.sort === "id"){
          this.sort = "-id";
        }else {
          this.sort = "id";
        }
      }
      this.loadArticles(false, 1);
    },
    onSort() {
      if (this.sortingDirection === "Descending")
        this.sort = "-" + this.appliedSort; 
      else 
        this.sort = this.appliedSort;
      
      this.$refs["sorting-dropdown"].classList.remove("active");
      this.loadArticles(false, 1);
    },
    onSwitchView(selectedBoard) {
      this.viewType = selectedBoard;
    },
    onCloseFilters() {
      this.selectedStates = this.getCurrentStates();
      this.selectedTags = this.getCurrentTags();
      this.hideModal('filters-slider');
    },
    onSearch(e) {
      e.preventDefault();
      // add selected database
      // const dbInputs = document.getElementsByName("database");
      // this.selectedDatabases = [];
      // for (let i=0; i<=dbInputs.length-1; i++) {
      //     const dbName = dbInputs[i].value;
      //     if (dbInputs[i].checked)
      //       this.selectedDatabases.push(dbName);
      // };
      this.hideModal('filters-slider');
      this.loadArticles(false, 1);
    },
    onClearFilters() {
      this.selectedStates = [];
      this.selectedTags = [];
      this.searchTerm = "";
      this.selectedDatabases = [];
      this.fromScoreValue = this.minScoreValue;
      this.toScoreValue = this.maxScoreValue;
      this.loadArticles(false, 1);
    },
    onCurrentArticleStateChange(selected) {
      this.currentArticle.state_symbole = selected;
    },
    onCurrentArticleExclusionReasonChange(selected) {
      this.currentArticle.exclusionReason = selected;
    },
    onBulkArticleStateChange(selected) {
      this.bulkArticle.state_symbole = selected;
    },
    onBulkArticleExclusionReasonChange(selected) {
      this.bulkArticle.exclusionReason = selected;
    },
    onSortingChange(selected) {
      this.appliedSort = selected;
    },
    onSortingDirectionChange(selected) {
      this.sortingDirection = selected;
    },
    onToggleSortingDropDown() {
      this.$refs["sorting-dropdown"].classList.toggle("active");
    },
    onNoTags() {
      this.makeToast('info', "You must create a new Tag to apply here. Go to 'Article Tags' in the advanced menu");
    },

    // Async Calls
    onChangeArticleTags(selectedTagID, event, remove=false) {
      // Add / Remove Article Tag
      selectedTag = this.articleTags.find(tag => tag.id === selectedTagID); 
      const reviewID = event.currentTarget.getAttribute("object-id");
      const review = this.articles.find(article => article.id === parseInt(reviewID));

      let tags = [];
      if (remove)
        tags = review.tags.filter(tag => tag.id !== selectedTag.id);
      else {
        tags = review.tags.map(tag => tag);
        tags.push(selectedTag);
      }
      tags = tags.map(tag => tag.id);

      const values = {tags_ids: tags};
      const URL = ArticleReviewUpdateAPI.slice(0, -2) + reviewID + "/";
      axios.patch(URL, data=values)
        .then(
          res => {
            // this.makeToast("success", "Tag was added successfully");
            this.updateArticle(res.data);
          },
          err => {
            console.log(err);
            this.makeToast("danger", `Failed to ${remove ? "Remove" : "Add"} tag`);
          }
        )
    },
    onExcludeArticle(exclusion, reviewID, exclusionComment="") {
      const values = {exclusion_reason: exclusion.reason, state: "E"}
      if (exclusionComment)
        values.exclusion_comment = exclusionComment;
      const URL = ArticleReviewUpdateAPI.slice(0, -2) + reviewID + "/";

      axios.patch(URL, data=values)
        .then(
          res => {
            this.updateArticle(res.data, true);
          },
          err => {
            console.log(err);
            let errMessage = err?.response?.data?.detail;
            errMessage = errMessage ? errMessage : "";
            this.makeToast("danger", `Failed to update the state for article #${reviewID} : ${errMessage}`);
          }
        )
    },
    onChangeArticleState(reviewID, state) {
      const values = {state: state}
      const URL = ArticleReviewUpdateAPI.slice(0, -2) + reviewID + "/";

      axios.patch(URL, data=values)
        .then(
          res => {
            this.updateArticle(res.data, true);
          },
          err => {
            console.log(err);
            let errMessage = err?.response?.data?.detail;
            errMessage = errMessage ? errMessage : "";
            this.makeToast("danger", `Failed to update the state for article #${reviewID} : ${errMessage}`);
          }
        )
    },
    onAddArticleNote(event, reviewID) {
      event.preventDefault();
      const notes = event.currentTarget.elements.article_note.value;
      const values = {notes};
      const URL = ArticleReviewUpdateAPI.slice(0, -2) + reviewID + "/";
      this.hideModal('add-note-modal-'+reviewID);

      axios.patch(URL, data=values)
        .then(
          res => {
            this.updateArticle(res.data);

          },
          err => {
            console.log("Failed to add the article note due to folowing error: ");
            console.log(err);
            this.makeToast("danger", `Failed to add Article Note`);
          }
        )
    },
    onUpdateArticle(event, next=false) {
      // validation 
      if (!this.validateUpdateArtice()) {
        return;
      };
      
      const values = {
        state: this.currentArticle.state_symbole,
        exclusion_reason: this.currentArticle.exclusionReason,
        notes: this.currentArticle.notes,
        exclusion_comment: this.currentArticle.exclusionComment,
      };
      this.isArticleUpdateLoading = true;
      const URL = ArticleReviewUpdateAPI.slice(0, -2) + this.currentArticle.id + "/";
      axios.patch(URL, data=values)
        .then(
          res => {
            this.isArticleUpdateLoading = false;
            const updatedReview = res.data;
            if (next) {
              this.hideArticleDetails(updatedReview);
              const currentReviewIndex = this.articles.findIndex(review => review.id === updatedReview.id);
              if (currentReviewIndex < this.articles.length) {
                const nextReview = this.articles[currentReviewIndex+1];
                this.onShowArticleDetails(nextReview);
              } else if (this.pagination.next) {
                this.loadArticles(false, this.pagination.current + 1);
              }
            } else this.hideArticleDetails(updatedReview);
            
            this.updateArticle(updatedReview, true);
          },
          err => {
            this.isArticleUpdateLoading = false;
            console.log("Failed to update the article due to folowing error: ");
            console.log(err);
            this.makeToast("danger", `Failed to update the article, try again please!`);
          }
        )
    },
    onShowArticleDetails(review) {
      this.currentArticle = {
        id: review.id,
        state_symbole: review.state_symbole,
        notes: review.notes,
        exclusionComment: review.exclusion_comment,
        exclusionReason: review.exclusion_reason,
        history: [],
        selected: true,
      },
      this.showModal('article-details-'+review.id);
      const URL = ArticleReviewHistoryAPI.slice(0, -2) + review.id + "/";
      console.log(this.currentArticle);
      axios.get(URL)
        .then(
          res => {
            this.currentArticle.history = res.data;
          },
          err => {
            console.log("Failed to retrieve the article history due to folowing error: ");
            console.log(err);
          }
        )
      const commentsURL = ArticleCommentsListAPI.slice(0, -2) + review.id + "/";

      axios.get(commentsURL)
        .then(
          res => {
            this.comments = res.data;
          },
          err => {
            console.log("Failed to retrieve the article history due to folowing error: ");
            console.log(err);
          }
        )
    },
    onAddComment(review){
      this.isLoading = true
      const values = {
        article_review:review.id,
        text:this.comment.text
      }
      axios.post(urlAddComment, data=values)
      .then((res)=>{
          this.comments.push(res.data)
          this.comment.text = ""
          this.isLoading = false
      })
      .catch((err)=>{
        console.log(err)
        this.isLoading = false
      })
    },
    onRefreshArticle(articleReview) {
      this.articles = this.articles.map(article => {
        if (articleReview.id === article.id)
          return articleReview;
        return article;
      });
    },
    loadArticles(loadExclusions = false, page = 1, uclassifiedRefresh=false) {
      // uclassifiedRefresh: we don't show popup modal when update states in unclassified page 
      if (page < 1 || (page > this.pagination.last && this.pagination.last!== 0))
        return ;
      if (!uclassifiedRefresh)
        this.showUpdateProgressPopup();

      const urlParams = new URLSearchParams(window.location.search);
      const state = urlParams.get('state');
      this.stateSymbole = state;
      this.articleState = this.getState(this.stateSymbole);
      let URL = ArticlesListAPI;

      if (this.stateSymbole === 'U') {
        this.isUnclassified = true;
        this.selectedStates = ['U'];
      } else if (loadExclusions) {
        this.onSwitchView("Table View");
      }
        

      if (this.stateSymbole && loadExclusions){
        URL = `${URL}?state=${this.stateSymbole}`;
        this.selectedStates = [this.stateSymbole];
      }  
      
      if (page){
        if (URL.includes("?"))
          URL =  `${URL}&page=${page}`;
        else
          URL =  `${URL}?page=${page}`;
      };

      if (this.sort){
        if (URL.includes("?"))
          URL =  `${URL}&ordering=${this.sort}`;
        else
          URL =  `${URL}?ordering=${this.sort}`;
      };

      if (this.searchTerm) {
        if (URL.includes("?"))
          URL =  `${URL}&search=${this.searchTerm}`;
        else
          URL =  `${URL}?search=${this.searchTerm}`;
      };

      if (this.selectedStates.length) {
        const states = this.selectedStates.join(",")
        if (URL.includes("?"))
          URL =  `${URL}&state=${states}`;
        else
          URL =  `${URL}?state=${states}`;
      };

      if (this.selectedTags.length) {
        const tags = this.selectedTags.join(",")
        if (URL.includes("?"))
          URL =  `${URL}&tag=${tags}`;
        else
          URL =  `${URL}?tag=${tags}`;
      };

      if (this.selectedDatabases.length) {
        const dbs = this.selectedDatabases.join(",")
        if (URL.includes("?"))
          URL =  `${URL}&db=${dbs}`;
        else
          URL =  `${URL}?db=${dbs}`;
      };

      // score filter
      if (this.fromScoreValue !== null && this.fromScoreValue != this.minScoreValue) {
        if (URL.includes("?"))
          URL =  `${URL}&min_score=${this.fromScoreValue}`;
        else
          URL =  `${URL}?min_score=${this.fromScoreValue}`;
      };
      if (this.toScoreValue !== null && this.toScoreValue != this.maxScoreValue) {
        if (URL.includes("?"))
          URL =  `${URL}&max_score=${this.toScoreValue}`;
        else
          URL =  `${URL}?max_score=${this.toScoreValue}`;
      };

      this.appliedStates = this.selectedStates;
      this.currentURL = URL;
      this.isLoading = true;
      // ArticlesListAPI this var declared inside the django template
      axios.get(URL)
        .then(
          res => {
            console.log(res);
            this.articles = res.data.results;
            this.initiateScoreFilterValues(res);
            this.initSliderUpdate();

            this.isLoading = false;
            this.hideUpdateProgressPopup();
            this.pagination.current = page;
            this.pagination.count = res.data.count;
            this.pagination.next = res.data.next;
            this.pagination.previous = res.data.previous;
            this.pagination.last =  Math.floor(this.pagination.count/50);
            if ((this.pagination.count % 50) > 0)
              this.pagination.last += 1;
            this.pagination.page_range = [
              this.pagination.current-1, 
              this.pagination.current, 
              this.pagination.current+1
            ];
            const currentPageTotalIncriment = this.articles.length < 50 ? 
            this.articles.length + (this.pagination.current-1) * 50
            : this.pagination.current * 50
            this.tablePageIndicator = `${this.pagination.current*50-49}-${currentPageTotalIncriment} Of ${this.pagination.count}`;
            
            this.loadArticlesHistoricalStatus();
            if (loadExclusions) {
              this.loadExclusionReasons();
              this.loadArticleTags();
            };

            // Scroll to the top of the page
            if (!uclassifiedRefresh) {
              window.scrollTo({
                top: 0,
                behavior: 'smooth' // Optional: adds smooth scrolling effect
              });
            }

            // hide warnings if any!
            this.hideModal("kw-updated-notification");
          },
          err => {
            console.log(err);
            this.isLoading = false;
            this.hideUpdateProgressPopup();
          }
        );
    },
    loadExclusionReasons() {
      // load exclusion reasons
      axios.get(ExclusionReasonAPI)
        .then(
          res => {
            console.log(res);
            this.exclusions = res.data;
          },
          err => {
            console.log(err);
            this.isLoading = false;
          }
        );
    },
    loadArticlesHistoricalStatus() {
      const articles = this.articles.map(articleReview => ({
        article: articleReview.id,
      }))
      this.axiosPost(
        null,
        url = ArticlesHistoricalStatusAPI,
        isLoadingKey = "isHistoricalStatusLoading",
        successMsg = "",
        postData = articles,
        callBack = (resData) => {
          this.articles = this.articles.map((articleReview) => {
            const retrievedArticle = resData.find(i => i.id === articleReview.id);
            articleReview.previous_article_state = retrievedArticle.previous_article_state;

            return articleReview;
          });
        },
      );
    },
    loadArticleTags() {
      axios.get(ArticleTagsListAPI)
        .then(
          res => {
            console.log(res);
            this.articleTags = res.data;
          },
          err => {
            console.log(err);
          }
        );
    },
    // checkBulkUpdateState: function(){
    //   const interval = setInterval(function(){
    //     axios.post(bulkStateUpdateAPI, data = { review_ids: this.selectedReviews, is_check: true })
    //       .then(
    //         res => {
    //           if (res.data.updated_articles.length){
    //             // this.hideUpdateProgressPopup();
    //             // this.loadArticles(false);
    //             this.isBulkUpdateLoading = false;
    //             res.data.updated_articles.forEach(review => {
    //               if (review.state_symbole !== 'U')
    //                 this.updateArticle(review, true);
    //               else 
    //                 this.updateArticle(review);
    //             });
    //             this.makeToast("success", "Bulk update is successful");
    //             this.selectedReviews = [];
    //             clearInterval(interval);
    //             this.bulkArticle = {
    //               state_symbole: "",
    //               notes: "",
    //               exclusionComment: "",
    //               exclusionReason: "",
    //             };
    //           };   
    //         },
    //         err => {
    //           this.hideUpdateProgressPopup();
    //           console.log("Failed to check status for bulk update articles due to folowing error: ");
    //           console.log(err);
    //         }
    //       );
    //   }.bind(this), 5000);
    // },
    onBulkStateUpdate(e) {
      // const state = this.stateSymbole;
      // this.hideModal('retain-all-warning')
      e.preventDefault();
      const values = {
        review_ids: this.selectedReviews,
        state: this.bulkArticle.state_symbole,
        exclusion_reason: this.bulkArticle.exclusionReason,
        notes: this.bulkArticle.notes,
        exclusion_comment: this.bulkArticle.exclusionComment,
      };
      
      this.isBulkUpdateLoading = true;
      console.log({values})
      // this.showUpdateProgressPopup()
      axios.post(bulkStateUpdateAPI, data=values)
        .then(
          // res => this.checkBulkUpdateState(),
          res => {
            if (this.bulkArticle.state_symbole != 'U') {
              this.loadArticles();
            } else if (res.data.updated_reviews.length){
              // this.hideUpdateProgressPopup();
              // this.loadArticles(false);
              
              res.data.updated_reviews.forEach(review => {
                if (review.state_symbole !== 'U')
                  this.updateArticle(review, true);
                else 
                  this.updateArticle(review);
              });
            };  
            
            this.isBulkUpdateLoading = false;
            this.makeToast("success", "Bulk update is successful");
            this.selectedReviews = [];
            this.bulkArticle = {
              state_symbole: "",
              notes: "",
              exclusionComment: "",
              exclusionReason: "",
            };
          },
          err => {
            // this.hideUpdateProgressPopup();
            console.log("Failed to bulk update articles due to folowing error: ");
            console.log(err);
            let error_msg = this.handleErrors(err);
            this.makeToast("danger", error_msg);
            this.isBulkUpdateLoading = false;
          }
        );
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
    
          if (socketMessage.type === "review_state_updated") {
            vm.onArticleUpdateByAnotherUser(socketMessage.message.review, socketMessage.message.user);
          } else if (socketMessage.type === "review_kw_updated") {
            vm.onKeywordsUpdated();
          } else if (socketMessage.type === "article_review_ai_suggestions_completed") {
            vm.onRefreshArticle(socketMessage.message.article_review);
          } else if (socketMessage.type === "article_review_ai_suggestions_completed_all") {
            vm.isAISuggestionsLoading = false;
            vm.makeToast("success", "Your AI suggestions are ready!");
          };
        };

        store.setReviewSocket(webSocket);
      } catch (error) {
        console.log("Failed to initial websocket due to below error")
        console.error(error);
      };
    },
    onArticleUpdateByAnotherUser(updatedArticle, updatedBy) {
      // if this user is not the one who has updated the article
      if (updatedBy.username != userUsername) {
        const toastMessage = `Article #${updatedArticle.id} state was updated to ${updatedArticle.state} by ${updatedBy.username}.`;
        const alertType = updatedArticle.state_symbole == "I" ? "success" : updatedArticle.state_symbole == "E" ? "danger" : "warning";
        this.makeToast(alertType, toastMessage, 10000, "Article State Updated");

        this.toggleArticleActionVisibility(updatedArticle.id);

        // update article with notification info
        this.articles = this.articles.map(article => {
          if (updatedArticle.id === article.id) {
            article.stateUpdatedByAnotherUser = {
              by: updatedBy,
              newState: updatedArticle.state,
            };
            article.updatedReview = updatedArticle;
          }
          return article;
        });
      }
    },
    onShowAISuggestions() {
      this.isShowAISuggestions = !this.isShowAISuggestions;
    },
    onGenerateAISuggestions(event) {
      const URL = `${AISuggestionURL}?sorting=${this.sort}`;
      this.isShowAISuggestions = true;

      this.axiosPost(
        event,
        url = URL,
        isLoadingKey = "isAISuggestionsLoading",
        successMsg = "AI Suggestion processing started successfully. This will run in the background and may take several minutes to complete depending on the number of appraisals.",
        postData = {},
        callBack = (resData) => {
          console.log({resData});
          this.isAISuggestionsLoading = true;
        },
      );
    },
    onKeywordsUpdated() {
      this.showModal("kw-updated-notification");
    },
  },

  watch: {
    // whenever isCheckAll changes, this function will run
    isCheckAll(newIsCheckAll, oldIsCheckAll) {
      if (newIsCheckAll) {
        const allReviews = this.articles.map(review => review.id);
        this.selectedReviews = allReviews;
      } else {
        this.selectedReviews = [];
      }
    },
    articles(oldVal, newVal) {
      const timeOut = setTimeout(() => {
        this.styleTooltips();
        return clearTimeout(timeOut);
      }, 2000);
    },
    viewType(oldVal, newVal) {
      const timeOut = setTimeout(() => {
        this.styleTooltips();
        return clearTimeout(timeOut);
      }, 2000);
    }
  },
  mounted() {
    this.loadArticles(true);
    this.loadDatabases(); 
    this.initiatSocket();
  }
})