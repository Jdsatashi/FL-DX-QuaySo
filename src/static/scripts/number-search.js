import addElement from "./helper.js";
const inputSearch = document.querySelector('#input-search-number');
const showListSelected = document.querySelector('#show-selected-number')
const groupData = document.querySelector('#group-data')
let listItem = groupData.querySelectorAll('.group-item')
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
            className: 'item-card',
            title: `Số ${item_value.toString()}`,
            innerHTML: `<span class="item-list">${item_value.toString()}</span>`
        }
    })

    let removeButton = addElement(addItem, {
        createTag: 'button',
        options: {
            id: `btn-remove-${item_value}`,
            className: 'item-button',
            title: `Bỏ chọn số ${item_value.toString()}`,
            innerHTML: `
                    <svg class="w-2 h-2" aria-hidden="true" xmlns="http://www.w3.org/2000/svg"
                         fill="none"
                         viewBox="0 0 14 14">
                        <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                              stroke-width="2"
                              d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6"></path>
                    </svg>`
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
