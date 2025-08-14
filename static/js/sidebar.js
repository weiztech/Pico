function activateSidebar () {
    const sidebar = document.getElementById("sidebar")
    const content = document.getElementById("content")
    const body = document.getElementById("body")
    var infos = document.getElementsByClassName("block")
    setTimeout(()=>{
        sidebar.classList.toggle("sidebar__container__active")
        content.classList.toggle("content__container__active")
        body.classList.toggle("body__container__active")
        Array.from(infos).forEach(item=>{
            item.classList.toggle("block__active")
        })
    }, 500)
}