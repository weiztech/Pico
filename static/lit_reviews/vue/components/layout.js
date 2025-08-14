Vue.component('living-review-analysis', {
  template: `
    <div class="statistics-section">
      <div class="statics-section-header">
        {{title}}
      </div>
      <div class="statics-section-body">
        <!-- add statistic section -->
        <div class="statistics-section-left">
          <div class="statistics-section-upper">
            <h1 class="statistics-section-upper-title"> Detail Publication Mentions </h1>
            <h1 class="statistics-section-upper-sub-title"> VS last month </h1>
          </div>
          <div class="statistics-section-lower">
            <div class="statistics-section-lower-icon">
              <img 
                    v-if="relevantArticles > relevantArticlesBefore" 
                    :src="upperIcon" 
                    alt="Increase" 
                    class="badge-icon-big"
                  />
                  <img 
                    v-else-if="relevantArticles < relevantArticlesBefore" 
                    :src="lowerIcon" 
                    alt="Decrease" 
                    class="badge-icon-big"
                  />
                  <img 
                    v-else="relevantArticles = relevantArticlesBefore" 
                    :src="sameIcon" 
                    alt="Same" 
                    class="badge-icon-big"
                  />
            </div>
            <div class="statistics-section-lower-text">
              {{relevantArticles}}
            </div>
            <div class="statistics-section-lower-sub-text">
              ({{relevantArticlesBefore}})
            </div>
          </div>
        </div>
        <div class="statistics-section-right">
          <div class="statistics-section-upper">
            <h1 class="statistics-section-upper-title"> Articles Reviews </h1>
            <h1 class="statistics-section-upper-sub-title"> VS last month </h1>
          </div>
          <div class="statistics-section-lower">
            <div class="statistics-section-lower-icon">
              <img 
                    v-if="reviewedArticles > reviewedArticlesBefore" 
                    :src="upperIcon" 
                    alt="Increase" 
                    class="badge-icon-big"
                  />
                  <img 
                    v-else-if="reviewedArticles < reviewedArticlesBefore" 
                    :src="lowerIcon" 
                    alt="Decrease" 
                    class="badge-icon-big"
                  />
                  <img 
                    v-else="reviewedArticles = reviewedArticlesBefore" 
                    :src="sameIcon"
                    alt="Same" 
                    class="badge-icon-big"
                  />
            </div>
            <div class="statistics-section-lower-text">
              {{reviewedArticles}}
            </div>
            <div class="statistics-section-lower-sub-text">
              ({{reviewedArticlesBefore}})
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  props: {
    title: {
      type: String,
    },
    relevantArticles: {
      type: Number,
    },
    relevantArticlesBefore: {
      type: Number,
    },
    upperIcon: {
      type: String,
    },
    lowerIcon: {
      type: String,
    },
    sameIcon: {
      type: String,
    },
    reviewedArticles: {
      type: Number,
    },
    reviewedArticlesBefore: {
      type: Number,
    },
  },
})


