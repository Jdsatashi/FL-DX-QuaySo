import addElement from "./helper.js";
const inputSearch = document.querySelector('#input-search-number');
const showListSelected = document.querySelector('#show-selected-number')
const groupData = document.querySelector('#group-data')
let listItem = groupData.querySelectorAll('.grid-col.grid-item')
// Live searching
let inputSearchEvent = (e) => {
    liveSearch(e, listItem, showListSelected)
}

inputSearch.addEventListener('input', inputSearchEvent)

listItem.forEach((item) => {
    item.onclick = () => {
        let item_value = item.textContent.trim()
        clickAddItem(item, item_value, showListSelected)
    }
})

function liveSearch(e, listItem, showListSelected) {
    let value = e.target.value.toLowerCase()
    listItem.forEach((item) => {
        let item_value = item.textContent.trim()
        if (item_value.includes(value)) {
            item.style.display = 'block'
            item.onclick = function () {
                clickAddItem(item, item_value, showListSelected)
                setTimeout(() => {
                    e.target.value = ''
                    listItem.forEach(item => {
                        item.style.display = 'block'
                    })
                }, 100)
            }
        } else {
            item.style.display = 'none'
        }
    })
}


function clickAddItem(item, item_value, showListSelected) {
    let addItem = addElement(showListSelected, {
        createTag: 'p',
        options: {
            id: `li-result-${item_value}`,
            className: 'list-group-item jd-col border border-1 border-success px-4 py-2 text-center',
            innerHTML: item_value.toString()
        }
    })

    let removeButton = addElement(addItem, {
        createTag: 'button',
        options: {
            id: `btn-remove-${item_value}`,
            className: 'btn-close',
            'style.padding': '8px',
            'style.margin': '0 0 8px 0'
        }
    })
    const removeBtnE = document.getElementById(removeButton.id)
    removeBtnE.onclick = function (evn) {
        evn.preventDefault()
        addItem.remove()
        removeButton.remove()
    }
    item.remove()
}
