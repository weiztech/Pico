var app = new Vue({
    el: '#content',
    delimiters: ["[[","]]"],
    data() {
        return {
            active_tab : "ae_events",
            search_term: ""
        }
    },
    methods : {
        // helpers   
        changeselectedtab: function(tab){
            this.active_tab = tab;
        },
        filterDevice: function(selected_status){
            const filterByDevicecheckbox = document.getElementsByClassName('filter-device-checkbox');
            let selectedDevices =  Array.from(filterByDevicecheckbox).filter(item => item.checked);
            selectedDevices = selectedDevices.map(item => item.value);
            const newURL = `?filter_status=${selected_status.toString()}&filter_device=${selectedDevices.toString()}&search_term=${this.search_term}`;
            window.location.href = newURL;
        },
        filterStatus: function(selected_device){
            const filterByStatusCheckbox = document.getElementsByClassName('filter-status-checkbox');
            let selectedStatus =  Array.from(filterByStatusCheckbox).filter(item => item.checked);
            selectedStatus = selectedStatus.map(item => item.value);
            const newURL = `?filter_status=${selectedStatus.toString()}&filter_device=${selected_device.toString()}&search_term=${this.search_term}`;
            window.location.href = newURL;
        },
        searchFilter: function(selected_status,selected_device){
            const searchTerm = document.getElementById('searchTerm').value;
            this.search_term = searchTerm
            const newURL = `?filter_status=${selected_status.toString()}&filter_device=${selected_device.toString()}&search_term=${this.search_term}`;
            window.location.href = newURL;
        },
        onClearFilters: function(){
            this.search_term = ""
            window.location.href = "?filter_status=I,IN";
        }

    },

    mounted() {
    }
})
