axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
  el: '#side-bar',
  mixins: [globalMixin],
  delimiters: ["[[", "]]"],
  data() {
    return {
    }
  },
  methods: {
    // Actions
    onSwitchSimpleAdvanced(mode, id) {
      if (mode === "B") this.hideSubMenu()
      else this.showSubMenu()
      const updateProjectConfigUrl = `${ProjectConfigUrl}${id}/update/`
      axios.post(updateProjectConfigUrl, data = {
        sidebar_mode: mode
      })
        .then((res) => { console.log(res.data.sidebar_mode) })
        .catch(err => console.log(err))
    },
    initiatTourGuide() {
      this.getProjectConfig()
        .then(
          res => {
            if (res.is_new_project) introJs().start();
          },
          err => console.log(err)
        );
    },
  },
  mounted() {
    // const regex = /^\/literature_reviews\/\d+\/$/; // project details page url
    // const currentURLPathName = window.location.pathname;
    // // kick up the menu tour guide if we're in the project details page
    // if (regex.test(currentURLPathName)) this.$tours['menu-tour'].start();

    const regex = /^\/literature_reviews\/\d+\/$/; // project details page url
    const currentURLPathName = window.location.pathname;
    // kick up the menu tour guide if we're in the project details page
    // if (regex.test(currentURLPathName)) this.initiatTourGuide();
  }
})
