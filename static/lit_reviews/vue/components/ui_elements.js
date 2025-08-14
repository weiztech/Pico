// Switcher help the user to navigate from one page to another
const PageSwitcher = {
	template: `
    <div class="switcher" v-cloak>
        <a :class="activePageSelected===firstPageLabel ? 'switch-item active' : 'switch-item'" :href="firstPageLink" v-on:click="onSwitch(firstPageLabel)">
            {{firstPageLabel}} 
        </a>
        <a :class="activePageSelected===secondPageLabel ? 'switch-item active' : 'switch-item'" :href="secondPageLink" v-on:click="onSwitch(secondPageLabel)">
            {{secondPageLabel}}
        </a>
    </div>
  `,
	mixins: [globalMixin],
	props: ["firstPageLabel", "secondPageLabel", "firstPageLink", "secondPageLink", "activePage", "type", "switchCallBack"],
	data() {
		return {
			activePageSelected: "",
			projectConfigID: null
		}
	},
	methods: {
		onSwitch: function (selectedPage) {
			this.activePageSelected = selectedPage;
			if (this.type === "ADVANCED_MODE") {
				let sidebar_mode = ""
				if (selectedPage === this.firstPageLabel) sidebar_mode = 'B'
				else sidebar_mode = 'A'
				this.switchCallBack(sidebar_mode, this.projectConfigID);
			} else {
				this.switchCallBack(this.activePageSelected);
			}
		},
	},
	mounted() {
		if (this.type === "ADVANCED_MODE") {
			axios.get(ProjectConfigUrl)
				.then((res) => {
					this.projectConfigID = res.data.id;
					if (res.data.sidebar_mode === "B") {
						this.activePageSelected = this.firstPageLabel
						this.hideSubMenu()
					}
					else {
						this.activePageSelected = this.secondPageLabel
						this.showSubMenu()
					}

				})
				.catch(err => console.log(err))
		}
		else this.activePageSelected = this.activePage;
	}
};


const DropDown = {
	template: `
    <div class="nav-bar-project-drop-down" v-on:click="onShowDropDown" v-cloak>
      <div v-if="text"> {{text}} </div>
      <img v-if="iconSource" :src="iconSource" alt="dropdown icon" class="drop-down-icon" />
    </div>
  `,
	props: ["iconSource", "text", "targetElement", "parentWrapper", "positionRight", "positionLeft", "positionBottom", "positionTop"],
	mixins: [globalMixin],
	methods: {
		onShowDropDown: function (event) {
			event.stopPropagation();
			const dropDown = document.getElementById(this.targetElement);
			dropDown.classList.toggle("drop-down-active")
		},
		clickOutsideEvent: function (event) {
			const dropDown = document.getElementById(this.targetElement);
			// here I check that click was outside the dropDown and his children
			if (dropDown) {
				if (!(dropDown == event.target || dropDown.contains(event.target) || this.$el == event.target || this.$el.contains(event.target))) {
					dropDown.classList.remove("drop-down-active");
				}
			} else {
				document.removeEventListener("click", this.clickOutsideEvent);
			}

		},
	},
	mounted() {
		const dropDownWrapper = document.getElementById(this.parentWrapper);
		const dropDown = document.getElementById(this.targetElement);
		dropDownWrapper.style.position = "relative";
		dropDown.style.bottom = this.positionBottom ? this.positionBottom : '';
		dropDown.style.right = this.positionRight ? this.positionRight : '';
		dropDown.style.left = this.positionLeft ? this.positionLeft : '';
		dropDown.style.top = this.positionTop ? this.positionTop : '';

		// add event listner to hide popup if we click outside it
		document.addEventListener("click", this.clickOutsideEvent);
	},
	beforeDestroy: el => {
		document.removeEventListener("click", this.clickOutsideEvent);
	},
};


const Toast = {
	template: `
    <div :class="'toast ' + type" :id="id" v-cloak>
        <div class="type">
            {{ type }}
        </div>
        <div class="body">
            <h4> {{ title }} </h4>
            <div> 
                <slot></slot> 
                <div class="close-icon" v-on:click="hide">
                    <svg width="12" height="13" viewBox="0 0 12 13" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M9 3.5L3 9.5M3 3.5L9 9.5" stroke="#EE46BC" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
            </div> 
        </div>
    </div>
  `,
	mixins: [globalMixin],
	props: ["id", "type", "title", "expires", "hidden"],
	data() {
		return {
			active: false,
		}
	},
	methods: {
		show() {
			const toast = document.getElementById(this.id);
			toast.classList.add("active");
			this.closeToast(this.expires)
		},
		hide() {
			const toast = document.getElementById(this.id);
			toast.classList.remove("active");
		},
		closeToast(closeIn) {
			// closeID in milliseconds
			setTimeout(() => {
				const toast = document.getElementById(this.id);
				if (toast) toast.classList.remove("active");
			}, closeIn)
		},
	},
	mounted() {
		if (this.hidden === false) {
			const toast = document.getElementById(this.id)
			if (toast) toast.classList.add("active");
			this.active = true;
		}
		if (this.expires)
			this.closeToast(this.expires);
	},
};


const FileUploader = {
	template: `
    <div class="file-uploader" v-cloak>
        <div 
            class="drop-zone mb-2" 
            :ref="'drop-zone-'+id" 
            v-on:dragover="onDragOver"
            v-on:dragleave="onDragLeave"
            v-on:drop="onDropFile"
            v-on:click="onUploadFile"
        >
            <div class="drop-zone-inner" :ref="'drop-zone-inner-'+id" >
                <div class="upload-icon">
                    <img :src="dropZoneImageUrl"  alt="upload icon">
                </div>
                <div class="upload-hint"> 
                    <div>
                        <span class="click-here">Click to upload</span>
                        <span class="drag-drop"> Or Drag and Drop the file Here.</span>
                    </div>
                    <small v-if="allowedFormats" class="file-types"> Allowed File Formats: {{allowedFormats.join(', ')}} </small>
                </div>
            </div>

            <input 
                v-on:change="onFileChanges" 
                type="file" 
                style="display: none;" 
                :id="id"
                :ref="'input-'+id"
                :name="name"
            />
        </div>

        <div class="file-details" :ref="'file-details-'+id" style="display: none">
            <div class="image-preview">
                <img v-if="isUploadedFileImage()" alt="logo imageee" :src="this.selectedFileURL" />
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="25" viewBox="0 0 24 25" fill="none">
                    <path d="M16.5162 0H5.97767C4.53012 0 3.3623 1.14249 3.3623 2.59001V10.388H17.2296C18.9385 10.388 20.3359 11.7676 20.3359 13.4765V19.2877C20.3359 20.9966 18.9385 22.4018 17.2296 22.4018H3.36936C3.41113 23.8071 4.55676 24.9368 5.97764 24.9368H21.376C22.8235 24.9368 24.0006 23.7496 24.0006 22.302V7.49061L16.5162 0ZM12.1982 7.41216H6.66369C6.35803 7.41216 6.11026 7.15251 6.11026 6.84685C6.11026 6.69387 6.17215 6.55003 6.27225 6.4499C6.37238 6.34979 6.51074 6.2824 6.66369 6.2824H12.1982C12.5039 6.2824 12.7517 6.54163 12.7517 6.84726C12.7517 7.15298 12.5039 7.41216 12.1982 7.41216ZM12.2234 4.07806H6.68885C6.38319 4.07806 6.13539 3.82511 6.13539 3.51945C6.13539 3.3665 6.19728 3.23308 6.29741 3.13295C6.39751 3.03284 6.53589 2.97589 6.68885 2.97589H12.2234C12.529 2.97589 12.7768 3.22134 12.7768 3.52697C12.7768 3.83261 12.529 4.07806 12.2234 4.07806ZM16.0098 7.96325V1.85392L22.1353 7.96325H16.0098Z" fill="#292D32"/>
                    <path d="M6.63752 16.3758C6.65405 17.004 6.30686 17.635 5.43063 17.635H4.62891V15.1826H5.43063C6.26829 15.1826 6.62099 15.775 6.63752 16.3758Z" fill="#292D32"/>
                    <path d="M9.70706 15.0625C8.79776 15.0625 8.4233 15.7954 8.43983 16.4457C8.45636 17.0795 8.79776 17.7573 9.70706 17.7573C10.6164 17.7573 10.958 17.074 10.9691 16.4402C10.9801 15.7899 10.6164 15.0625 9.70706 15.0625ZM9.70706 15.0625C8.79776 15.0625 8.4233 15.7954 8.43983 16.4457C8.45636 17.0795 8.79776 17.7573 9.70706 17.7573C10.6164 17.7573 10.958 17.074 10.9691 16.4402C10.9801 15.7899 10.6164 15.0625 9.70706 15.0625ZM18.985 13.7035C18.985 12.6027 18.0927 11.7104 16.992 11.7104H1.99302C0.892297 11.7104 0 12.6027 0 13.7035V19.086C0 20.1867 0.892297 21.079 1.99302 21.079H16.992C18.0927 21.079 18.985 20.1867 18.985 19.086V13.7035ZM5.43088 18.3511H3.91274V14.4935H5.43088C6.7535 14.4935 7.34316 15.4358 7.35969 16.3892C7.37623 17.3646 6.78105 18.3511 5.43088 18.3511ZM9.70706 18.4241C8.35166 18.4241 7.72341 17.4487 7.72341 16.4347C7.72341 15.4207 8.3737 14.4012 9.70706 14.4012C11.0352 14.4012 11.6965 15.4207 11.6855 16.4292C11.6745 17.4267 11.0627 18.4241 9.70706 18.4241ZM14.1544 18.4241C12.7215 18.4241 12.1153 17.4377 12.1098 16.4347C12.1043 15.4262 12.7601 14.4012 14.1544 14.4012C14.6779 14.4012 15.1739 14.5996 15.5707 14.9908L15.0857 15.4593C14.8322 15.2113 14.4905 15.0955 14.1543 15.0955C13.223 15.0955 12.8207 15.7899 12.8262 16.4347C12.8317 17.074 13.201 17.7408 14.1543 17.7408C14.4905 17.7408 14.8707 17.603 15.1242 17.3495L15.6202 17.851C15.2234 18.2423 14.711 18.4241 14.1544 18.4241ZM9.70706 15.0625C8.79776 15.0625 8.4233 15.7954 8.43983 16.4457C8.45636 17.0795 8.79776 17.7573 9.70706 17.7573C10.6164 17.7573 10.958 17.074 10.9691 16.4402C10.9801 15.7899 10.6164 15.0625 9.70706 15.0625Z" fill="#292D32"/>
                </svg>
            </div>
            <div class="image-details">
                <div class="image-info">
                    <h4 class="image-name" id="image-name">
                        {{ selectedFile && selectedFile.name }}
                    </h4>
                    <span class="image-size" id="image-size">
                        {{ selectedFileSize }}
                    </span>
                </div>
                <div>
                    <button class="re-upload-btn" type="button" v-on:click="onUploadFile">
                        <img :src='editFileImageUrl' alt="">
                    </button>
                </div>
            </div>
        </div>
    </div>
  `,
	mixins: [globalMixin],
	props: ["id", "name", "onChange", "dropZoneImageUrl", "editFileImageUrl", "allowedFormats"],
	data() {
		return {
			selectedFile: null,
			selectedFileType: "",
			selectedFileURL: "",
			selectedFileSize: "",
		}
	},
	methods: {
		validate: function () {
			if (!this.allowedFormats.includes(this.selectedFileType)) {
				this.makeToast("error", "Invalid File Format")
				return false;
			}
			return true;
		},
		isUploadedFileImage() {
			return ['png', 'jpeg', 'jpg'].includes(this.selectedFileType);
		},
		fillDropZone: function () {
			const dropzone = this.$refs["drop-zone-inner-" + this.id];
			dropzone.classList.add("active");
		},
		emptyDropZone: function () {
			const dropzone = this.$refs["drop-zone-inner-" + this.id];
			dropzone.classList.remove("active");
		},
		onDragOver(e) {
			e.preventDefault();
			this.fillDropZone();
		},
		onDragLeave(e) {
			e.preventDefault();
			this.emptyDropZone();
		},
		onUploadFile() {
			const input = this.$refs["input-" + this.id];
			input.click();
		},
		onDropFile(e) {
			e.preventDefault();
			const input = this.$refs["input-" + this.id];
			input.files = e.dataTransfer.files;
			const file = e.dataTransfer.files[0];
			const fileType = file.name.split('.').pop();
			this.selectedFile = file;
			this.selectedFileType = fileType;

			if (this.validate() == false) {
				this.selectedFile = null;
				this.selectedFileType = "";
				this.selectedFileURL = "";
				this.selectedFileSize = "";
				return;
			}
			if (this.onChange)
				this.onChange(file);

			// get uploaded file details 
			this.selectedFileURL = URL.createObjectURL(file);
			this.selectedFileSize = this.formatFileSize(file);

			// hide dropzone area
			const fileDetails = this.$refs["file-details-" + this.id];
			const dropZoneArea = this.$refs["drop-zone-" + this.id];
			fileDetails.style.display = "flex";
			dropZoneArea.style.display = "none";

		},
		onFileChanges(e) {
			const file = e.target.files[0];
			const fileType = file.name.split('.').pop();
			this.selectedFile = file;
			this.selectedFileType = fileType;
			if (this.validate() == false) {
				this.selectedFile = null;
				this.selectedFileType = "";
				this.selectedFileURL = "";
				this.selectedFileSize = "";
				return;
			}
			if (this.onChange)
				this.onChange(file);

			// get uploaded file details 
			this.selectedFileURL = URL.createObjectURL(file);
			this.selectedFileSize = this.formatFileSize(file);

			// hide dropzone area
			const fileDetails = this.$refs["file-details-" + this.id];
			const dropZoneArea = this.$refs["drop-zone-" + this.id];
			fileDetails.style.display = "flex";
			dropZoneArea.style.display = "none";
		},
	},
	mounted() {
		if (this.hidden === false) {
			document.getElementById(this.id).classList.add("active");
			this.active = true;
		}
		if (this.expires)
			this.closeToast(this.expires);
	},
};


const CustomSelect = {
	template: `
    <div class="custom-select" :ref="'wrapper-'+id" v-cloak>
        <select :id="id" :name="name"> 
            <option 
                v-for="option in options" 
                :value="option.value" 
                :key="option.value"
                :selected='selectedOption === option.value'
            > 
                {{option.name}} 
            </option>
        </select>

        <div class="custom-select-box" :ref="'custom-'+id" v-on:click="onClickSelect">
            <div class="custom-select-box-text"> {{ selectedOptionObj ? selectedOptionObj.name : placeholder }} </div>
            <div v-if="iconUrl" class="icon">
                <img :src="iconUrl" alt="plus"/>
            </div>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="14" height="15" viewBox="0 0 14 15" fill="none">
                <path d="M10.4534 5.27148H6.81926H3.54676C2.98676 5.27148 2.70676 5.94815 3.10343 6.34482L6.1251 9.36648C6.60926 9.85065 7.39676 9.85065 7.88093 9.36648L9.0301 8.21732L10.9026 6.34482C11.2934 5.94815 11.0134 5.27148 10.4534 5.27148Z" fill="#989FAE"/>
            </svg>
        </div>
        <div class="custom-options" :ref="'custom-options-'+id">
            <ul>
                <li 
                    v-for="option in options" 
                    v-if="isActionButton ? option.value != '' : true"
                    v-on:click="onSelectOption($event, option.value)" 
                    :key="option.value" 
                    :ref="'custom-option-'+option.value"
                    :object-id="objectId"
                > 
                    <div class="center-v">
                        <div v-if="option.color" class="option-color" :style="'background-color: '+option.color"> </div>
                        <div> {{option.name}}  </div>
                    </div>
                </li>
            </ul>
        </div>
    </div>
  `,
	mixins: [globalMixin],
	props: ["id", "name", "options", "defaultSelected", "placeholder", "onChange", "iconUrl", "objectId", "isActionButton"],
	// objectId: if we want to update a related object onChange we pass it through here.
	// isActionButton: if true treat select as a button / don't display default value / Don't change selected item 
	data() {
		return {
			selectedOption: [undefined, null].includes(this.defaultSelected) ? '' : this.defaultSelected,
		}
	},
	watch: {
		defaultSelected(newValue) {
			this.selectedOption = [undefined, null].includes(newValue) ? '' : newValue;
		}
	},
	computed: {
		selectedOptionObj() {
			let selected = this.options.find(opt => opt.value === this.selectedOption);
			if (!selected) {
				selected = this.selectedOption;
			};
			return selected;
		},
	},
	methods: {
		onSelectOption: function (event, selectedOption) {
			if (!this.isActionButton) {
				for (let option of this.options) {
					this.$refs['custom-option-' + option.value][0].classList.remove("active");
				}
				this.$refs['custom-option-' + selectedOption][0].classList.add("active");
				this.selectedOption = selectedOption;
			}
			this.$refs['custom-options-' + this.id].classList.remove("active");
			if (this.onChange) this.onChange(selectedOption, event);
		},
		onClickSelect: function () {
			this.$refs['custom-options-' + this.id].classList.toggle("active");
		},
	},
	mounted() {
		if (!this.isActionButton && this.$refs['custom-option-' + this.selectedOption])
			this.$refs['custom-option-' + this.selectedOption][0].classList.add("active");

		const el = this.$refs['wrapper-' + this.id];
		el.clickOutsideEvent = event => {
			// here I check that click was outside the el and his children
			if (!(el == event.target || el.contains(event.target))) {
				this.$refs['custom-options-' + this.id].classList.remove("active");
			}
		};
		document.addEventListener("click", el.clickOutsideEvent);
	},
	beforeDestroy() {
		const el = this.$refs['wrapper-' + this.id];
		document.removeEventListener("click", el.clickOutsideEvent);
	},
};


const PrismaAndSubscriptionData = {
	template: `
    <div v-cloak>
  
      <div class="sandbox-banner" v-if="userSubscription && userSubscription.licence_type === 'sandbox'">
        This is a sandbox environment, all data will be deleted every 24-48 hours if no license is activated.
        You can either purchase a monthy subscription license, <a href="https://buy.stripe.com/3cscQG4KH3rD7165ko" target="_blank">by clicking here</a>.
        Or you can purchase credits based license, <a :href="CREDITS_PURCAHSE_LINK" target="_blank">by clicking here</a>.
      </div>
      <div class="credits-banner" v-if="userSubscription && userSubscription.licence_type === 'credits' && userSubscription.remaining_credits > 0">
        You have a credit based subscription with {{userSubscription.remaining_credits}} remaining credits.
      </div>
      <div class="credits-banner-warning" v-else-if="userSubscription && userSubscription.licence_type === 'credits'">
        Oops you are out of credits!
        You can purchase more credits by following 
        <a :href="CREDITS_PURCAHSE_LINK" target="_blank"> this link </a>
        Or you can subscribe for an unlimited use by following
        <a href="https://buy.stripe.com/3cscQG4KH3rD7165ko" target="_blank"> this link </a>
      </div>


      <div class="prisma" id="prisma" v-if="showPrismaSection">
        <div class="prisma-show-table" v-if="prismaOpen">
          <div :class="sharedState.prismaStatus === 'RUNNING' ? 'prisma-show-table-header prisma-show-table-header-warning' : 'prisma-show-table-header'">
            <div class="prisma-show-table-header-left">
              <div class="prisma-show-button-text" v-on:click="openPrismaPopup">
                <h1>Hide Prisma</h1>
                <img :src="ArrowDownSmall" alt="prisma-show-button-icon" class="prisma-show-button-icon"/>
              </div>
              <div class="prisma-show-button-text-status">
                <span v-if="sharedState.prismaStatus == 'RUNNING'" class="prisma-warining-status">
                  Deduplication Script Running
                </span>
                <span v-else class="prisma-completed-status">
                  Deduplication Script Completed
                </span>
              </div>
            </div>
            <div class="prisma-show-table-header-right">
              <button v-on:click="refreshStatistics" :class="sharedState.prismaStatus === 'RUNNING' ? 'secondary-buttom refresh-prisma-button refresh-prisma-button-yellow' : 'secondary-buttom refresh-prisma-button'">
                <span v-if="isLoading" class="prisma-refresh-span">Refreshing...</span>
                <span v-else class="prisma-refresh-span">
                  Refresh
                  <img :src="RefreshIconYellow" alt="prisma-refresh-icon" class="prisma-refresh-icon" v-if="sharedState.prismaStatus == 'RUNNING'"/>
                  <img :src="RefreshIcon" alt="prisma-refresh-icon" class="prisma-refresh-icon" v-else/>
                </span>
              </button>
            </div>
            
          </div>
          <div class="prisma-show-table-body">
            <div class="prisma-warining-status-badge" v-if="sharedState.prismaStatus == 'RUNNING'">
              Deduplication is still running, please don't start your review until it's completed. This process can take a few minutes.
            </div>
            <div class="prisma-success-status-badge" v-else>
              Deduplication is completed you can start your review now.
            </div>
            <div class="prisma-table-btn" v-on:click="togglePrismaTable">
              <h1 class="prisma-table-btn-text">Prisma Summary</h1>
              <img :src="MinusIcon" alt="prisma-minus-icon" class="prisma-minus-plus-icon" v-if="statisticPrismaOpen"/>
              <img :src="PlusIcon" alt="prisma-plus-icon" class="prisma-minus-plus-icon" v-else/>
            </div>
            <div :class="statisticPrismaOpen ? 'prisma-table' : 'prisma-table-none'" id="prisma-summary">
              <table class="custom-table">
                <thead class="citation-list-table-header">
                    <tr>
                        <th scope="col" class="table-header-col term-header-col">Label</th>
                        <th scope="col" class="table-header-col count-header-col" >Count</th>
                    </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in prismaSummary" :key="index">
                    <td> {{ item.label }} </td>
                    <td> {{ item.count }}  </td>
                  </tr>
                </tbody>
            </table>
            </div>
            <div class="prisma-table-btn" v-on:click="toggleExcludedTable">
              <h1 class="prisma-table-btn-text">Excluded Article Summary</h1>
              <img :src="MinusIcon" alt="prisma-minus-icon" class="prisma-minus-plus-icon" v-if="statisticArticlesOpen"/>
              <img :src="PlusIcon" alt="prisma-plus-icon" class="prisma-minus-plus-icon" v-else/>
            </div>
            <div  id="articles-summary" :class="statisticArticlesOpen ? 'prisma-table' : 'prisma-table-none'">
              <table class="custom-table">
                <thead class="citation-list-table-header">
                    <tr>
                        <th scope="col" class="table-header-col term-header-col">Reason</th>
                        <th scope="col" class="table-header-col count-header-col" >Count</th>
                    </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in excludedSummary" :key="index">
                    <td> {{ item.reason }} </td>
                    <td> {{ item.count }} </td>
                  </tr>
                </tbody>
            </table>
            </div>
          </div>
        </div>
        <div v-on:click="openPrismaPopup" :class="sharedState.prismaStatus === 'RUNNING' ? 'prisma-show-button prisma-show-button-warning' : 'prisma-show-button'" v-else>
          <div class="prisma-show-button-text">
            <h1> Prisma Status </h1>
            <span v-if="sharedState.prismaStatus == 'RUNNING'" class="prisma-warining-status ml-2">
              ( Deduplication Running - Please wait ) 
            </span>
            <span v-else class="prisma-completed-status ml-2">
              ( Deduplication Completed - You're all set for your 1st pass review ) 
            </span>
            <img :src="ArrowUpSmall" alt="prisma-show-button-icon" class="prisma-show-button-icon"/>
          </div>
          <!-- <div class="prisma-show-button-text-status">
            <span v-if="sharedState.prismaStatus == 'RUNNING'" class="prisma-warining-status">
              Deduplication Script Running
            </span>
            <span v-else class="prisma-completed-status">
              Deduplication Script Completed
            </span>
          </div> -->
        </div>
      </div>
    </div>
    `,
	mixins: [globalMixin],
	props: [
		"PrismaStatisticUrl",
		"ArrowDownSmall",
		"ArrowUpSmall",
		"RefreshIconYellow",
		"RefreshIcon",
		"MinusIcon",
		"PlusIcon",
		"showPrismaSection"
	],
	data() {
		return {
			prismaSummary: [],
			excludedSummary: [],
			prismaOpen: false,
			statisticPrismaOpen: true,
			statisticArticlesOpen: false,
			intervalId: null,
			userSubscription: null,
			isLoading: false,
      CREDITS_PURCAHSE_LINK: CREDITS_PURCAHSE_LINK,
		};
	},
	methods: {
		openPrismaPopup: function () {
			this.prismaOpen = !this.prismaOpen;
		},
		togglePrismaTable() {
			this.statisticPrismaOpen = !this.statisticPrismaOpen;
		},
		toggleExcludedTable() {
			this.statisticArticlesOpen = !this.statisticArticlesOpen;
		},
		loadData() {
			this.isLoading = true;
			axios
				.get(this.PrismaStatisticUrl)
				.then((res) => {
					this.prismaSummary = res.data.prisma_summary;
					this.excludedSummary = res.data.excluded_summary;
					this.userSubscription = res.data.user_subscription;
					store.setPrismaStatus(res.data.duplication_report_status);
				})
				.catch((err) => {
					console.error(err);
				})
				.finally(() => {
					this.isLoading = false;
				});
		},
		refreshStatistics() {
			this.loadData();
		},
		startAutoUpdate() {
			const SECOND = 1000;
			const MINUTE = 60 * SECOND;

			this.intervalId = setInterval(() => {
				this.loadData();
			}, MINUTE);
		},
		stopAutoUpdate() {
			if (this.intervalId) {
				clearInterval(this.intervalId);
			}
		},
	},
	mounted() {
		this.loadData();
		this.startAutoUpdate();
	},
	beforeDestroy() {
		this.stopAutoUpdate();
	},
};


const PageWikiHelper = {
	template: `
    <div class="tooltip" style="padding-left: 10px;" v-cloak>
      <a class="help-button" :class="variant ? variant : 'warning' "
      :href="wikiLink"
      target="_blank">
        <span> {{ title ? title : 'What do I do on this page?' }} </span>
      </a>
      <span class="tooltiptext">
	  	<span v-if="tooltip"> {{tooltip}} </span>
	  	<span v-else> Need help with this page? <br/> Read the Wiki </span>
	 </span>
    </div>
  `,
	props: ["wikiLink", "title", "tooltip", "variant"],
};

const Loader = {
	template: `
		<div class="css-loader">
			<h3> {{headerText?headerText:'Loading'}} </h3>
			<div v-if="helper" class="helper"> {{helper}} </div>
			<div class="container">
			<div class="post">
					<div class="avatar"></div>
					<div class="line"></div>
					<div class="line"></div>
			</div>

			<div class="post">
					<div class="avatar"></div>
					<div class="line"></div>
					<div class="line"></div>
			</div>

			<div class="post">
					<div class="avatar"></div>
					<div class="line"></div>
					<div class="line"></div>
			</div>
			</div>
		</div>
  `,
	props: ["headerText", "helper"],
};

const DatabaseConfigViewer = {
  delimiters: ["[[", "]]"],
  template: `
    <div class="slider" :id="id" v-cloak>
      <div class="slider-dialog db-slide-condig">
        <div class="slider-dialog-inner">

          <div class="slider-header">
            <button class="pagintaion-item mr" @click="hideModal">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M10.0002 13.28L5.65355 8.93333C5.14022 8.42 5.14022 7.58 5.65355 7.06667L10.0002 2.72"
                  stroke="#292D32" stroke-width="1.5" stroke-miterlimit="10" stroke-linecap="round"
                  stroke-linejoin="round" />
              </svg>
            </button>
            [[ currentDb ? currentDb.name : '' ]] Database Configurations
          </div>

          <div v-if="currentDb" class="slider-content">
            <div v-if="currentDbType == 'ae_database'">              
              <div class="filter-section">
                <div class="helper-text">
                  The general Adverse Event Start/End Search Date you set on the Search Parameters will be applied Here.
                  as for now this can not be edited/changed if you have a case where you want to set a specific start/end date 
                  for this database please contact our support team at support@citemedical.com.
                </div>
              </div>
              
              <div class="horizantal-devider"></div>
            </div>          

            <!-- Database Config start/end date -->
            <div class="filter-section">
              <div>
                <div>
                  <label>Start Date</label>
                  <input type="date" v-model="currentDbConfigStartDate" disabled />
                </div>
                <div>
                  <label>End Date</label>
                  <input type="date" v-model="currentDbConfigEndDate" disabled />
                </div>
              </div>
            </div>

            <div v-for="searchConfig in currentDb.search_configuration" :key="searchConfig.id">
              <div v-for="(param, idx) in searchConfig.params" :key="param.id">
                <!-- for Checkbox type -->
                <div v-if="param.type == 'CK'">
                  <div class="filter-section" v-if="currentDb.entrez_enum != 'ct_gov' || (currentDb.entrez_enum == 'ct_gov' && !excludedParamsName.includes(param.name))">
                    <h3 class=""> [[ param.name ]] </h3>
                    <div class="filter-box">
                      <div class="filter-checkbox" v-for="ck in optionsSplit(param.options)">
                        <label :for="ck + '_view'">[[ ck ]]</label>
                        <input 
                          type="checkbox" 
                          :id="ck + '_view'"
                          :value="ck"
                          :checked="isValueSelected(param.value, ck)"
                          disabled
                          class="view-only-checkbox"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <!-- for select type -->
                <div v-if="param.type == 'DP'">
                  <div class="filter-section" v-if="currentDb.entrez_enum != 'ct_gov' || (currentDb.entrez_enum == 'ct_gov' && !excludedParamsName.includes(param.name))">
                    <h3 class=""> [[ param.name ]] </h3>
                    <div class="selected-value">
                      <span>[[ param.value ]]</span>
                    </div>
                  </div>
                </div>
                
                <!-- For Number Type -->
                <div v-if="param.type == 'NB'">
                  <div>
                    <label> [[ param.name ]] </label>
                    <div v-if="param.name == 'Max Results'" class="hint">
                      Google scholar searches can return incredible large and unrelated result sets, 
                      we have to limit the amount of results processed. We recommend no more than the first 3 pages of results 
                      for any search (around 50 results).
                    </div>
                    <div class="selected-value">
                      <span>[[ param.value ]]</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="slider-footer">
            <div class="center-v">
              <button class="secondary-gray-button" type="button" @click="hideModal">
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  mixins: [globalMixin],
  props: {
    id: String,
    currentDb: Object,
    currentDbType: String,
    currentDbConfigStartDate: String,
    currentDbConfigEndDate: String,
    excludedParamsName: Array
  },
  methods: {
    hideModal() {
		// Use the parent hideModal method, passing the component's id
		this.$emit('hide-modal', this.id);
	  },
    optionsSplit(options) {
      return options ? options.split(',') : [];
    },
	isValueSelected(paramValue, optionValue) {
	  // Handle case where param.value is a string of comma-separated values
	  if (typeof paramValue === 'string') {
		const selectedValues = paramValue.split(',').map(v => v.trim());
		return selectedValues.includes(optionValue.trim());
	  }
	  
	  // Handle case where param.value is already an array
	  if (Array.isArray(paramValue)) {
		return paramValue.includes(optionValue);
	  }
	  
	  // Handle case where param.selected is an array (if that's what your API returns)
	  if (paramValue && paramValue.selected && Array.isArray(paramValue.selected)) {
		return paramValue.selected.includes(optionValue);
	  }
	  
	  return false;
	}
  }
};

// Reusable side slider component for forms and information display
const SideSlider = {
  template: `
    <div class="side-slider" :class="{ 'active': isOpen }" :id="id" v-cloak>
      <div class="side-slider-backdrop" v-if="isOpen" @click="onClose"></div>
      <div class="side-slider-content">
        <div class="side-slider-header"> 
			<button class="pagintaion-item mr" @click="onClose">
				<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
				<path d="M10.0002 13.28L5.65355 8.93333C5.14022 8.42 5.14022 7.58 5.65355 7.06667L10.0002 2.72"
					stroke="#292D32" stroke-width="1.5" stroke-miterlimit="10" stroke-linecap="round"
					stroke-linejoin="round" />
				</svg>
			</button>
          <div class="side-slider-title">
            {{ title }}
          </div>
        </div>
        <div class="side-slider-body">
          <slot></slot>
        </div>
        <div class="side-slider-footer">
			<button class="secondary-gray-button ml" @click="onClose">
				Cancel
			</button>
			<button v-if="actionButtonText" class="primary-button" :disabled="actionDisabled" @click="onAction">
				{{ actionButtonText }}
			</button>
        </div>
      </div>
    </div>
  `,
  props: {
    id: {
      type: String,
      required: true
    },
    title: {
      type: String,
      default: ''
    },
    isOpen: {
      type: Boolean,
      default: false
    },
    actionButtonText: {
      type: String,
      default: 'Save'
    },
    actionDisabled: {
      type: Boolean,
      default: false
    }
  },
  methods: {
    onClose() {
      this.$emit('close');
    },
    onAction() {
      this.$emit('action');
    }
  }
};


const Spinner = {
  template: `
    <div :style="styling" class="spinner"> </div>
  `,
  data() {
    return {
      styling: 'width: '+String(this.width)+'; height: '+String(this.height)+';',
    }
  },
  props: {
    width: {
      type: Number,
      default: 20
    },
    height: {
      type: Number,
      default: 20
    },
  },
}
// Register components to be accessed globaly
Vue.component('page-switcher', PageSwitcher);
Vue.component('drop-down', DropDown);
Vue.component('toast', Toast);
Vue.component('file-uploader', FileUploader);
Vue.component('custom-select', CustomSelect);
Vue.component('page-wiki-helper', PageWikiHelper);
Vue.component('prisma-and-subscription-data', PrismaAndSubscriptionData);
Vue.component('loader', Loader);
Vue.component('side-slider', SideSlider);
Vue.component('database-config-viewer', DatabaseConfigViewer);
Vue.component('spinner', Spinner);
