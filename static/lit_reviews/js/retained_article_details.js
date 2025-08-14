function showMore(term_span,term) {
    term_span.innerHTML = term;
}

function showLess(term_span,term) {
    term_span.innerHTML = term.slice(0, 45) ;
}

function showTerm(term) {
    const term_span = document.getElementById("search_term");
    const view_more_btn = document.getElementById("view_more");
    const view_less_btn = document.getElementById("view_less");
    
    if (term.length > 45) { 
        showLess(term_span,term) 
        view_more_btn.style.display = "inline"
        view_more_btn.addEventListener("click", function () {
            showMore(term_span,term)
            view_less_btn.style.display = "inline"
            view_more_btn.style.display = "none"
        })
    }
    else { 
        showMore(term_span,term) 
    }
    view_less_btn.addEventListener("click", function () {
        showLess(term_span,term) 
        view_more_btn.style.display = "inline"
        view_less_btn.style.display = "none"
   })
}





