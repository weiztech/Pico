// global store for shared states
const store = {
  debug: true,
  state: {
    prismaStatus: '',
    reviewSocket: null,
  },
  setPrismaStatus(newValue) {
    this.state.prismaStatus = newValue;
  },
  setReviewSocket(newSocketValue){
    this.state.reviewSocket = newSocketValue;
  }
}

// define a mixin object
const globalMixin = {
  data: function () {
    return {
      sharedState: store.state,
      isArchived: is_archived,
    }
  },
  methods: {
    showModal: function (modalID) {
      const modal = document.getElementById(modalID);
      modal.classList.add("active");
      document.getElementsByTagName("body")[0].classList.add("modal-open");
    },
    hideModal: function (modalID) {
      const modal = document.getElementById(modalID);
      modal.classList.remove("active");
      document.getElementsByTagName("body")[0].classList.remove("modal-open");
    },
    showToast(toastID) {
      const toast = document.getElementById(toastID);
      toast.classList.add("active");
    },
    hideToast(toastID) {
      const toast = document.getElementById(toastID);
      toast.classList.remove("active");
    },
    styleTooltips() {
      // find all tooltips in the current page and style them
      const tooltips = document.querySelectorAll('[title]');
      tooltips.forEach(function (element) {
        const tooltipText = element.getAttribute("title");
        element.removeAttribute("title");
        element.classList.add("tooltip")
        const tooltipTextElement = document.createElement("div");
        tooltipTextElement.innerHTML = tooltipText;
        tooltipTextElement.classList.add("tooltiptext");
        element.appendChild(tooltipTextElement);
      });
    },
    formatFieldName(name) {
      return name
        .replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
    },
    capitalizeWords(phrase, containSlashed=false) {
      if (containSlashed) return phrase.replace(/(?:^|[ /])\w/g, match => match.toUpperCase());
      return phrase.replace(/\b\w/g, char => char.toUpperCase());
    },
    formatFileSize(file) {
      // KB
      const kbSize = file.size / 1000;
      if (kbSize < 100) {
        return kbSize.toFixed(2) + " KB."
      };

      // MB
      const mbSize = kbSize / 1000;
      return mbSize.toFixed(2) + " MB.";
    },
    makeToast(type, content, expires=10000, label=null) {
      // toast types (success, info, warning, danger, secondary)
      if (type === "danger")
        type = "error"

      const toastDiv = document.createElement("div");
      toastDiv.classList.add("toast");
      toastDiv.classList.add("active");
      toastDiv.classList.add(type);
      const nowTimeStamp = Date.now();
      const toastID = "toast-" + nowTimeStamp
      toastDiv.id = toastID;

      // Create the div with class "type" and add text content
      const typeDiv = document.createElement("div");
      typeDiv.classList.add("type");
      if (label) typeDiv.textContent = label;
      else typeDiv.textContent = type;

      // Create the div with class "body"
      const bodyDiv = document.createElement("div");
      bodyDiv.classList.add("body");

      // Create the div with class "text" and add content text
      const contentDiv = document.createElement("div");
      contentDiv.classList.add("content");
      contentDiv.id = "toast-content" + toastID;

      // Create close icon 
      const colseIcon = document.createElement("div");
      const closeIconID = "close-icon-" + nowTimeStamp;
      colseIcon.innerHTML = `
            <div class="close-icon" id="${closeIconID}">
                <svg width="12" height="13" viewBox="0 0 12 13" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 3.5L3 9.5M3 3.5L9 9.5" stroke="#EE46BC" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            `;

      // Append all elements to their respective parents
      bodyDiv.appendChild(contentDiv);
      bodyDiv.appendChild(colseIcon);

      toastDiv.appendChild(typeDiv);
      toastDiv.appendChild(bodyDiv);

      document.body.appendChild(toastDiv);

      if (typeof content === 'string') {
        contentDiv.innerHTML = content;
      } else {
        const vnode = content;

        // Create a Vue instance without el option
        const vm = new Vue({
          render: function () {
            return vnode; // Return the VNode
          }
        });

        // Mount the Vue instance to a specific div
        vm.$mount('#toast-content' + toastID);
      }

      // add event Listener for closing toast manualy
      document.getElementById(closeIconID).addEventListener("click", function () {
        document.getElementById(toastID).classList.remove("active");
      });
      setTimeout(() => {
        document.getElementById(toastID).classList.remove("active");
      }, expires)
    },
    closeToast: function (toastID) {
      document.getElementById(toastID).classList.remove("active");
    },
    showSubMenu: function () {
      const subOptions = document.getElementsByClassName("menu-sub-option-list");
      for (let i = 0; i < subOptions.length; i++) {
        subOptions[i].classList.remove("hide")
      }
    },
    hideSubMenu: function () {
      const subOptions = document.getElementsByClassName("menu-sub-option-list");
      for (let i = 0; i < subOptions.length; i++) {
        subOptions[i].classList.add("hide")
      }
    },
    enableElement: function (ele, text = null) {
      ele.style.pointerEvents = "auto";
      ele.style.opacity = "1";
      if (text)
        ele.innerHTML = text;
    },
    disableElement: function (ele, text = null) {
      ele.style.pointerEvents = "None";
      ele.style.opacity = ".7";
      if (text)
        ele.innerHTML = text;
    },
    formatErrorMessage: function (errorMsg) {
      // format error message and filter out unuseful messages and return a blank text instead.
      // if this function returns blank text please make sure to provide a usefull message based on the functionality / page you are at.
      // return {type: <'valid' | 'backend'>, errorMsg: <error message text>}
      // we only return a message if the type is valid other types are just indications to help display a useful message.

      console.log("Error message : " + String(errorMsg));
      const IMPORTANT_ERRORS = [
        "doesn't contain the correct columns",
        "The search process has been running for over an hour",
        "No results found",
        "Error reading the RIS file",
        "search parameters",
        "start date",
        "end date",
      ]

      for (let importantErr of IMPORTANT_ERRORS) {
        if (errorMsg.includes(importantErr))
          return { type: "valid", errorMsg };
      };

      // based on the backend error create a useful / meaninful error message for the user
      if (errorMsg.includes("Error parsing query"))
        return { type: "valid", errorMsg: "It seems like your search term query cannot be searched as given Are you sure your syntax is acceptable? Try running this search directly on the database to make sure the results populate." };

      if (errorMsg.includes("not an allowed value"))
        return { type: "valid", errorMsg: "500 error please contact our support team at support@citemedical.com " }

      // excluded errors

      // scraper related errors
      else if (
        errorMsg.includes("browser") ||
        errorMsg.includes("invalid session") ||
        errorMsg.includes("chrome") ||
        errorMsg.includes("click") ||
        errorMsg.includes("downloading the file")
      )
        return { type: "scraper", errorMsg: "" };
      // backend fields errors
      else if (
        errorMsg.includes("AsyncResult") ||
        errorMsg.includes("variable") ||
        errorMsg.includes("non-iterable") ||
        errorMsg.includes("NoneType") ||
        errorMsg.includes("decode")
      )
        return { type: "backend", errorMsg: "" };
      // scraper http errors
      else if (errorMsg.includes("HTTPConnectionPool"))
        return { type: "backend", errorMsg: "" };

      else if (errorMsg.length > 1000)
        return { type: "backend", errorMsg: "" };

      return { type: "valid", errorMsg };
    },
    compare: function (a, b, key, type) {
      if (a[key].toLowerCase() < b[key].toLowerCase()) {
        return type === "ASC" ? -1 : 1;
      }
      if (a[key].toLowerCase() > b[key].toLowerCase()) {
        return type === "ASC" ? 1 : -1;
      }
      return 0;
    },
    hexToRgba(hex, opacity) {
      // Remove '#' if present and convert hex to RGB
      let hexColor = hex.startsWith('#') ? hex.slice(1) : hex;
      let rgb = parseInt(hexColor, 16);
      let r = (rgb >> 16) & 0xff;
      let g = (rgb >>  8) & 0xff;
      let b = (rgb >>  0) & 0xff;
    
      // Return RGBA with specified opacity
      return `rgba(${r}, ${g}, ${b}, ${opacity})`;
    },
    formTagStyle(tag) {
      let rgbaColor = this.hexToRgba(tag.color, 0.2);
      return `background-color: ${rgbaColor}; width: max-content; color: ${tag.color}; border: 1px solid ${tag.color}; padding: 2px 8px;`;
    },
    onErrorDisplay: function (errMessage, title = "Search Dashboard Error") {
      // This will be used to display text error messages coming from the backend mostly from a celery task
      // If you want to display a text error message use this function
      const variant = "danger";
      if (errMessage.includes("duplicate key value violates unique constraint \"unique_review_term\"")) {
        errMessage = "The search term you're trying to add already exists!";
      }
      const displayableError = this.$createElement(
        'div',
        [
          this.$createElement('h4', [title]),
          errMessage,
          this.$createElement("br"),
          this.$createElement("br"),
          "Still stuck? Get instant help from our team by submitting a ticket",
          this.$createElement('a', { attrs: { "href": "https://share.hsforms.com/1jqB4CJx9RxyvGL3qQYo2rgcq0hk ", "target": "_blank" } }, [' Here']),
        ]
      );
      console.log({ displayableError });
      this.makeToast(variant, displayableError);
    },
    extractErrorMessages: function (object) {
      let messagesElements = [];


      for (const key in object) {
        const argument = object[key];
        const isObject = typeof argument === "object";
        const isArray = Array.isArray(argument);

        if (isObject && !isArray)
          return this.extractErrorMessages(argument);
        else if (isArray) {
          // const errors = argument.join();
          let errMsg;
          if (key === "error message" || argument.length < 2) {
            element = this.$createElement("li", { style: { listStyleType: 'none' } }, `${key} : ${argument}`);
            messagesElements.push(element);
          } else {
            for (let i = 0; i < argument.length; i++) {
              errMsg = `${key}: ${argument[i]}`;
              errMsg = errMsg.includes("non_field_errors:") ? errMsg.replace("non_field_errors:", "") : errMsg;
              element = this.$createElement("li", errMsg);
              messagesElements.push(element);
            };
          };
        }
        else {
          // displayableError += key === "error message" ? argument :  `'${key} Field': ${argument} ,`; 
          const element = key === "error message" ?
            this.$createElement("li", { style: { listStyleType: 'none' } }, argument)
            : this.$createElement("li", { style: { listStyleType: 'none' } }, [`${key}: `, ...argument])
          messagesElements.push(element);
        }

      };

      return this.$createElement(
        'div',
        messagesElements
      );
    },
    getProjectConfig() {
      // Project configs includes
      // sidebar_mode: Advanced or Basic
      // count_client_projects: number of projects created by this project owner (client)
      // is_new_project: a project is considered a new if the number of created projects by its owner is less than 3
      return axios.get(ProjectConfigUrl)
        .then((res) => {
          return res.data;
        })
        .catch(err => console.log(err))
    },
    loadDatabases() {
      // load NCBI Databases List
      axios.get(DatabasesListAPI)
        .then(
          res => {
            console.log(res);
            this.dbs = res.data;
          },
          err => {
            console.log(err);
          }
        );
    },
    handleErrors: function (error) {
      // this will be used to display handle and extract the backend error message based on the resp status
      // error is an object that has the error message, error status ...etc.
      // once the error message is retured plz used a taost to display it
      const errorMsg = error.response.data;
      let displayableError = "";

      if (error.response.status === 400) {
        let errors = this.extractErrorMessages(errorMsg);
        displayableError = this.$createElement(
          'div',
          [
            errors,
            this.$createElement("br"),
            "Still stuck? Get instant help from our team by submitting a ticket",
            this.$createElement('a', { attrs: { "href": "https://share.hsforms.com/1jqB4CJx9RxyvGL3qQYo2rgcq0hk ", "target": "_blank" } }, [' Here']),
          ]
        );
      }
      else if (error.response.status === 403) {
        let errMessage = error?.response?.data?.detail;
        errMessage = errMessage ? errMessage : "You are not allowed to edit an archived project, if the project is unarchived then you don't have permission to perform this action, Please contact a Senior Medical Writer or The Project Manager"

        displayableError = this.$createElement(
          'div',
          [
            errMessage,
            this.$createElement("br"),
            "Still stuck? Get instant help from our team by submitting a ticket",
            this.$createElement('a', { attrs: { "href": "https://share.hsforms.com/1jqB4CJx9RxyvGL3qQYo2rgcq0hk ", "target": "_blank" } }, [' Here']),
          ]
        );
      } else {
        displayableError = this.$createElement(
          'div',
          [
            "500 Server Error",
            this.$createElement("br"),
            "Please Submit a ticket to get instant help from our support team!",
            this.$createElement('a', { attrs: { "href": "https://share.hsforms.com/1jqB4CJx9RxyvGL3qQYo2rgcq0hk ", "target": "_blank" } }, [' Here']),
          ]
        );
      }


      return displayableError;
    },
    fillDropZone: function (itemID) {
      const dropzone = document.getElementById("drop-zone-inner-" + itemID);
      dropzone.classList.add("active");
    },
    emptyDropZone: function (itemID) {
      const dropzone = document.getElementById("drop-zone-inner-" + itemID);
      dropzone.classList.remove("active");
    },
    onDropZoneDragOver: function (e, itemID) {
      e.preventDefault();
      this.fillDropZone(itemID);
    },
    onDropZoneDragLeave: function (e, itemID) {
      e.preventDefault();
      this.emptyDropZone(itemID);
    },
    onDrop: function (e, item, validationCallBack, uploadType="SEARCH", postUploadCallBack=null, updateItemCallBack=null) {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      const fileType = file.name.split('.').pop();
      this.awsS3UploadingFile = file;

      if (validationCallBack) {
        const database = item.db ? item.db : item.database ? item.database : null;
        if (database && !validationCallBack(database.entrez_enum, fileType)) {
          this.currentDB = database.entrez_enum;
          // this.showToast("search-file-warning");
          this.emptyDropZone(item.id);
          return;
        }
      }
      if (uploadType === "FULL_TEXT_PDF") this.uploadFileToAWSVue(file, fileType, item, uploadType, updateItemCallBack, postUploadCallBack);
      else this.uploadFileToAWS(file, fileType, item.id, uploadType, postUploadCallBack);
    },
    onDropZoneClick: function (itemID) {
      const fileInput = document.getElementById('input-' + itemID);
      fileInput.click();
    },
    isFileSizeValid(file){
      const maxSizeInMB = 200;
      const maxSizeInBytes = maxSizeInMB * 1024 * 1024;

      if (file.size > maxSizeInBytes) {
        this.showToast("search-file-size-warning");
        return false;
      }
      return true;
    },
    uploadFileToAWS: async function (file, fileType, ID, uploadType, postUploadCallBack=null) {
      if (!this.isFileSizeValid(file)) return "";

      const dropzone = document.getElementById("drop-zone-" + ID);
      const progressBarElm = document.getElementById("progress-bar-" + ID)
      dropzone.style.display = "none";
      // document.getElementById("drop-zone-inner-" + ID).style.display = "none";
      progressBarElm.style.display = "flex";


      const progressElmInner = document.getElementById('progress-inner-' + ID);
      const preogressPercentageElm = document.getElementById('progress-percentage-' + ID);
      const uploadedFileDetailsElm = document.getElementById('file-details-' + ID);

      // display file details 
      uploadedFileDetailsElm.style.display = "flex";
      uploadedFileDetailsElm.getElementsByClassName("file-title")[0].innerHTML = file.name;
      uploadedFileDetailsElm.getElementsByClassName("file-size")[0].innerHTML = this.formatFileSize(file);

      const formData = new FormData();
      let signedURLResp;
      try {
        signedURLResp = await axios.post(S3DirectUploadURL, data = {
          type: uploadType,
          file_format: fileType,
          object_id: ID,
        });
      } catch (err) {
        console.log(err);
        this.handleErrors(err);
      }

      const signed_url_obj = signedURLResp.data
      const key = signed_url_obj.fields.key;
      const policy = signed_url_obj.fields.policy;
      const signature = signed_url_obj.fields.signature;
      const URL = signed_url_obj.url;
      const accessKey = signed_url_obj.fields.AWSAccessKeyId;
      this.awsS3CurrentKey = key;

      formData.append("Key", key);
      formData.append("AWSAccessKeyId", accessKey);
      formData.append("policy", policy);
      formData.append("signature", signature);
      formData.append("file", file);

      const config = {
        onUploadProgress: progressEvent => {
          var percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          progressElmInner.style.width = String(percentCompleted) + "%";
          preogressPercentageElm.innerHTML = String(percentCompleted) + "%";
          console.log(percentCompleted);
        }
      };

      try {
        const res = await axios.post(URL, data = formData, config);
        console.log(res);
        const uploadSuccessElm = document.getElementById("upload-success-" + ID);
        if (uploadSuccessElm) uploadSuccessElm.style.display = "block";

        const clearFileIcon = document.getElementById("clear-file-icon-" + ID);
        if(clearFileIcon) clearFileIcon.style.display = "block";

        this.runSearchReady = true;
        
        progressBarElm.style.display = "none";
        if (postUploadCallBack) postUploadCallBack();
      } catch (err) {
        console.log(err);
        // display dropzone again
        dropzone.style.display = "block";
        progressBarElm.style.display = "none";
        uploadedFileDetailsElm.style.display = "none";
        this.handleErrors(err);
      };
    },
    uploadFileToAWSVue: async function (file, fileType, item, uploadType, updateItemCallBack, postUploadCallBack=null) {
      // manipulate dom directly with vue instead
      if (!this.isFileSizeValid(file)) return "";

      const dropzone = document.getElementById("drop-zone-" + item.id);
      dropzone.style.display = "none";

      item.toBeUploadedFile = {
        title: file.name,
        size: this.formatFileSize(file),
        showClearBTN: false,
        uploadPercentage: 0,
        awsKey: null,
      };
      updateItemCallBack(item);
      
      const formData = new FormData();
      let signedURLResp;
      try {
        signedURLResp = await axios.post(S3DirectUploadURL, data = {
          type: uploadType,
          file_format: fileType,
          object_id: item.id,
        });
      } catch (err) {
        console.log(err);
        this.handleErrors(err);
      }

      const signed_url_obj = signedURLResp.data
      const key = signed_url_obj.fields.key;
      const policy = signed_url_obj.fields.policy;
      const signature = signed_url_obj.fields.signature;
      const URL = signed_url_obj.url;
      const accessKey = signed_url_obj.fields.AWSAccessKeyId;
      this.awsS3CurrentKey = key;
      item.toBeUploadedFile.awsKey = key;

      formData.append("Key", key);
      formData.append("AWSAccessKeyId", accessKey);
      formData.append("policy", policy);
      formData.append("signature", signature);
      formData.append("file", file);

      const config = {
        onUploadProgress: progressEvent => {
          var percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          // progressElmInner.style.width = String(percentCompleted) + "%";
          // preogressPercentageElm.innerHTML = String(percentCompleted) + "%";
          console.log(percentCompleted);
          item.toBeUploadedFile.uploadPercentage = percentCompleted;
          updateItemCallBack(item);
        }
      };

      try {
        const res = await axios.post(URL, data = formData, config);
        console.log(res);
        if (postUploadCallBack) postUploadCallBack(item);
      } catch (err) {
        console.log(err);
        // display dropzone again
        dropzone.style.display = "block";
        this.handleErrors(err);
      };
    },

    axiosPatch: function (event, url, isLoadingKey, successMsg, postData, callBack) {
      event.preventDefault();
      this[isLoadingKey] = true;
      axios.patch(url, data = postData, {
        headers: {
          'Content-Type': 'application/json',
        }
      })
        .then(
          res => {
            console.log(res);
            this[isLoadingKey] = false;
            if (callBack) callBack(res.data);
            this.makeToast("success", successMsg);
          },
          err => {
            console.log({ err });
            this[isLoadingKey] = false;
            let error_msg = this.handleErrors(err);
            this.makeToast("danger", error_msg);
          }
        );
    },
    axiosPost: function (event, url, isLoadingKey, successMsg, postData, callBack) {
      if (event) event.preventDefault();
      this[isLoadingKey] = true;
      axios.post(url, data = postData, {
        headers: {
          'Content-Type': 'application/json',
        }
      })
        .then(
          res => {
            console.log(res);
            this[isLoadingKey] = false;
            if (callBack) callBack(res.data);
            if(successMsg) this.makeToast("success", successMsg);
          },
          err => {
            console.log({ err });
            this[isLoadingKey] = false;
            let error_msg = this.handleErrors(err);
            this.makeToast("danger", error_msg);
          }
        );
    },
    axiosGet: function (url, isLoadingKey, callBack) {
      this[isLoadingKey] = true;
      axios.get(url)
        .then(
          res => {
            console.log(res);
            if(isLoadingKey) this[isLoadingKey] = false;
            if (callBack) callBack(res.data);
          },
          err => {
            console.log({ err });
            if(isLoadingKey) this[isLoadingKey] = false;
          }
        );
    },
    websocketConnect: function() {
      if (literatureReviewID) {
        const roomName = `review-room-${literatureReviewID}`;
        
        const isLocalServer = window.location.href.includes("localhost") || window.location.href.includes("127.0.0.1");
        const socketProtocol = isLocalServer ? 'ws://' : 'wss://';
        const webSocket = new WebSocket(
            socketProtocol
            + window.location.host
            + '/ws/literature_review/'
            + roomName
            + '/'
        );

        webSocket.onmessage = function(e) {
            const socketMessage = JSON.parse(e.data);
            console.log("Recieved message from socket : ")
            console.log({socketMessage})
        };
  
        webSocket.onclose = function(e) {
            console.error('web socket was closed unexpectedly');
            console.log(e);
        };
  
        store.setReviewSocket(webSocket);
      } else {
        console.error("No Literature Review ID found websocket connection failed!")
      }
    }
  }
}