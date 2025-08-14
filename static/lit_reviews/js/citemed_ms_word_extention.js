/*
 * Copyright (c) Microsoft Corporation. All rights reserved. Licensed under the MIT license.
 * See LICENSE in the project root for license information.
 */

/* global document, Office, Word */

axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";

let isLoading = false;
let search = "";
let citationsURL = "/client_portal/api/documents_library/?page_number=";
let lastPageNumber = 2;
let currentPage = 0;
let records = [];
let totalCount = 0;

const countDiv = document.createElement("div");
const listElm =  document.getElementById("list-records");
const buttons =  document.getElementById("buttons-section");
const currentPageBtn = document.getElementById("current-page");
const loadingElm =  document.getElementById("loading");

async function loadRecords (pageNumber, isPrevious=false) {

  if (isPrevious) currentPage -= 1;
  else currentPage += 1;
  setNextPreviousEvents();

  if (lastPageNumber > pageNumber && pageNumber > 0) {
    isLoading = true;
    let URL = `${citationsURL}${pageNumber}`;
    if (search) URL = `${citationsURL}${pageNumber}&search_term=${search}`;
    // document.getElementById("debug").innerHTML = `URL ${URL}`;
    

    listElm.style.display = "none";
    buttons.style.display = "none";
    loadingElm.style.display = "block";
    listElm.innerHTML = "";
    countDiv.innerHTML = "";
    currentPageBtn.innerHTML = currentPage;
    
    axios.get(URL).then(
      res => {
        console.log({res});
        lastPageNumber = res.data.last_page_number;
        records = res.data.entries;
        totalCount = res.data.count;

        countDiv.setAttribute("class", "count");
        countDiv.innerHTML = `Total Citations Found <strong> ${totalCount} </strong>`;
        listElm.appendChild(countDiv);

        for (let i=0; i<records.length; i++){
          const li = document.createElement("li");
          li.innerHTML = records[i].article.title;
          li.setAttribute("record-id", records[i].id);
          li.onclick = (event) => addCitationToWord(records[i].id);

          listElm.appendChild(li);
          listElm.style.display = "block";
          buttons.style.display = "block";
          loadingElm.style.display = "none";
        }
      },
      err => {
        console.log({err});
        // document.getElementById("debug").innerHTML = `err ${String(err)}`;
      }
    );

  }
};

async function addCitationToWord(recordID) {
  return Word.run(async (context) => {
    const record = records.find(r => r.id === recordID);
    if (record) {
      const selection = context.document.getSelection();

    // insert a paragraph at the end of the document.
    const paragraph = selection.insertParagraph(record.article.title, "After");

    }
    
    await context.sync();
  });

};

function onSearch (event) {
  event.preventDefault();
  search = document.getElementById("search-input").value;
  currentPage = 1;
  loadRecords(1);
};

function setNextPreviousEvents() {
  const nextBtn =  document.getElementById("next");
  const previousBtn =  document.getElementById("previous");
  const nextPage = currentPage+1;
  const previousPage = currentPage-1;

  nextBtn.onclick = () => loadRecords(nextPage);
  previousBtn.onclick = () => loadRecords(previousPage, true);
};

Office.onReady(async (info) => {
  if (info.host === Office.HostType.Word) {
    document.getElementById("app-body").style.display = "flex";
    document.getElementById("search-form").onsubmit = onSearch;

    setNextPreviousEvents();

    // load backend citations
    await loadRecords(1);
  }
});