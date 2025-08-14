axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

var app = new Vue({
    el: '#app-lit-review',
    delimiters: ["[[", "]]"],
    mixins: [globalMixin],
    data() {
        return {
            isSubmit:false,
            isshowPopup: false,
            message: "",
            demo_video: "",
            help_channels: [],
            isDrag : false,
            elmnt:null,
            position:{
                pos1:0,
                pos2:0,
                pos3:0,
                pos4:0,
            }
        }
    },
    methods: {
        clearHelpRequestFields: function () {
            this.message = ""
            this.demo_video = ""
            this.help_channels = []
        },
        onRequestHelp: async function (type, current_page = "") {
            this.isSubmit = true
            try {
                let data = {};
                if (type == "SUPPORT_CALL") {
                    data.type = type
                    data.current_page = current_page
                }
                else {
                    data = {
                        type:type, message: this.message,
                        demo_video: this.demo_video,
                        help_channels: this.help_channels,
                        current_page: current_page,
                    }
                }
                console.log('data', data)
                console.log('url',HelpUrl)

                const res = await axios.post(HelpUrl, data = data);
                if (res.data.success) {
                    document.getElementById("success-submit").classList.remove("hide");
                    document.getElementById("form-request").classList.add("hide");
                    this.clearHelpRequestFields();
                }

                this.isSubmit = false

            } catch (err) {
                this.isSubmit = false
                errorMsg = this.handleErrors(err);
                this.makeToast("danger", errorMsg, 3000)
            }
        },
        onReturnForm: function () {
            document.getElementById("success-submit").classList.add("hide");
            document.getElementById("form-request").classList.remove("hide");
            this.clearHelpRequestFields();
        },
        dragMouseDown(e) {
            console.log('dragMouseDown',this.isDrag)
            e = e || window.event;
            e.preventDefault();
           
            // get the mouse cursor position at startup:
            this.position.pos3 = e.clientX;
            this.position.pos4 = e.clientY;
            document.onmouseup = this.closeDragElement;
            // call a function whenever the cursor moves:
            document.onmousemove = this.elementDrag;
          },
          elementDrag(e) {
            this.isDrag = true

            e = e || window.event;
            e.preventDefault();
            // calculate the new cursor position:
            this.position.pos1 = this.position.pos3 - e.clientX;
            this.position.pos2 = this.position.pos4 - e.clientY;
            this.position.pos3 = e.clientX;
            this.position.pos4 = e.clientY;
            // set the element's new position:
            this.elmnt.style.top = (this.elmnt.offsetTop - this.position.pos2) + "px";
            this.elmnt.style.left = (this.elmnt.offsetLeft - this.position.pos1) + "px";
          },
          closeDragElement() {
            console.log('closeDragElement',this.isDrag)
            /* stop moving when mouse button is released:*/
            document.onmouseup = null;
            document.onmousemove = null;
            
          },
        onMousedown(){
            
            this.elmnt = document.getElementById("popup-btn")            
            if (document.getElementById( this.elmnt.id + "header")) {
              /* if present, the header is where you move the DIV from:*/
              document.getElementById( this.elmnt.id + "header").onmousedown = this.dragMouseDown;
            } else {
              /* otherwise, move the DIV from anywhere inside the DIV:*/
              this.elmnt.onmousedown = this.dragMouseDown;
            }
        },
      
        showPopup: function (e) {
            console.log('showPopup',this.isDrag)
            if(this.isDrag){
                this.isDrag = false
                return
            }
            this.isshowPopup = !this.isshowPopup
            console.log('update',this.isDrag)
            if (this.isshowPopup) {
                const helpPopup = document.getElementById("help-popup")
                helpPopup.classList.remove("help-popup-hide")
                helpPopup.classList.remove("hide")
                document.getElementById("form-request").classList.remove("hide");
                document.getElementById("success-submit").classList.add("hide");
            } else {
                const helpPopup = document.getElementById("help-popup")
                this.clearHelpRequestFields();
                helpPopup.classList.add("help-popup-hide")
                setTimeout(() => {
                    helpPopup.classList.add("hide")
                }, 300);
            }
        },
    },
    mounted() {
        
        this.onMousedown()
    }
})