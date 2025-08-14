axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";

var app = new Vue({
  el: '#reviews-base',
  mixins: [globalMixin],
  delimiters: ["[[", "]]"],
  data() {
    return {
      hidePrismaPages: [
        "search_protocol",
      ]
    }
  },
  methods: {
    isHidePrisma: function() {
      for (let pageLabel of this.hidePrismaPages) {
        if (window.location.pathname.includes(pageLabel)) return true;
      }

      return false
    },
  },
  mounted(){
    this.websocketConnect();
    setTimeout(() => {
      this.sharedState.reviewSocket.send(JSON.stringify({
        'message': {
          user_username: userUsername,
          text: "user is active",
          page: location.href,
        },
        'type': 'review.user.active',
      }));
    }, 1000)
  }
})
