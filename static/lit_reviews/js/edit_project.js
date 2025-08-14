const clientNameInput = document.getElementById("id_client_form-name")
const clientShortNameInput = document.getElementById("id_client_form-short_name") 
const clientLongNameInput = document.getElementById("id_client_form-long_name") 
const clientAddressInput = document.getElementById("id_client_form-full_address_string") 
const deviceNameInput = document.getElementById("id_name") 
const deviceClassificationInput = document.getElementById("id_classification") 
const deviceMarketsInput = document.getElementById("id_markets") 
const imageBtn = document.getElementById("id_client_form-logo") 
const imageLink = document.querySelector("#div_id_client_form-logo a")
const imageName = document.getElementById("image-name")
const imageSize = document.getElementById("image-size")
const uploadBtn = document.getElementById("re-upload-btn")
const currentImage = document.getElementById("current-image")

const clientName= document.getElementById("client-name")
const clientShortName = document.getElementById("client-short-name")
const clientLongName = document.getElementById("client-long-name") 
const clientAddress = document.getElementById("client-address") 
const clientImage = document.getElementById("client-img") 
const deviceName = document.getElementById("device-name")
const deviceClassification = document.getElementById("device-classification")
const deviceMarkets = document.getElementById("device-markets")

clientName.innerText = clientNameInput.value
clientShortName.innerText = clientShortNameInput.value
clientLongName.innerText = clientLongNameInput.value
clientAddress.innerText = clientAddressInput.value

deviceName.innerText = deviceNameInput.value
deviceClassification.innerText = deviceClassificationInput.value
deviceMarkets.innerText = deviceMarketsInput.value

const onChangeClientName = (value)=>{
    clientName.innerText = value
}

const onChangeClientShortName = (value)=>{
    clientShortName.innerText = value
}

const onChangeClientLongName = (value)=>{
    clientLongName.innerText = value
}

const onChangeClientAddress = (value)=>{
    clientAddress.innerText = value
}

const onChangeDeviceName = (value)=>{
    deviceName.innerText = value
}

const onChangeDeviceClassification = (value)=>{
    deviceClassification.innerText = value
}

const onChangeDeviceMarkets = (value)=>{
    deviceMarkets.innerText = value
}


const onChangePreviewImage = async ()=>{
    const [file] = imageBtn.files
    if (file) {
      currentImage.classList.remove("hide")
      currentImage.src = URL.createObjectURL(file)
      imageName.innerText = file.name 
      const fileSizeInMB = file.size / (1024 * 1024);
      imageSize.innerText = `${fileSizeInMB.toFixed(2)} MB` 
      clientImage.classList.remove("hide")
      clientImage.src = URL.createObjectURL(file)
    }
}

// initialize the preview fields
const  init = () => {
    onChangeClientName(clientNameInput.value)
    onChangeClientShortName(clientShortNameInput.value)
    onChangeClientLongName(clientLongNameInput.value)
    onChangeClientAddress(clientAddressInput.value)
    onChangeDeviceName(deviceNameInput.value)
    onChangeDeviceClassification(deviceClassificationInput.value)
    onChangeDeviceMarkets(deviceMarketsInput.value)
    onChangePreviewImage()
}

init()

uploadBtn.addEventListener("click",function(e){
    imageBtn.click()
})

imageBtn.addEventListener("change",function(e){
    onChangePreviewImage()
})


clientNameInput.addEventListener("change",function(e){
    onChangeClientName(e.target.value)
})

clientShortNameInput.addEventListener("change",function(e){
    onChangeClientShortName(e.target.value)
})

clientLongNameInput.addEventListener("change",function(e){
    onChangeClientLongName(e.target.value)
})

clientAddressInput.addEventListener("change",function(e){
    onChangeClientAddress(e.target.value)
})

deviceNameInput.addEventListener("change",function(e){
    onChangeDeviceName(e.target.value)
})

deviceClassificationInput.addEventListener("change",function(e){
    onChangeDeviceClassification(e.target.value)
})

deviceMarketsInput.addEventListener("change",function(e){
    onChangeDeviceMarkets(e.target.value)
})