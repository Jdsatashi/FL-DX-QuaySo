const inputSearch = document.querySelector('#input-search-number');
const showListSelected = document.querySelector('#show-selected-number')
const groupData = document.querySelector('#group-data')
let listItem = groupData.querySelectorAll('.group-item')
const turnChoose = parseInt(document.getElementById('turn_choose').innerText)
const randomNumber = document.getElementById('randNum')
let randomLoop = 0
const dateClose = document.getElementById('date-close')

document.addEventListener('DOMContentLoaded', function () {
    let date = dateClose.textContent
    let closureDate = new Date(date)
    closureDate.setHours(23, 59, 59);
    let x = setInterval(function () {
        let now = new Date().getTime();
        let distance = closureDate - now;
        let days = Math.floor(distance / (1000 * 60 * 60 * 24));
        let hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        let minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        let seconds = Math.floor((distance % (1000 * 60)) / 1000);

        document.getElementById("demo").innerHTML = days + " ngày - " + hours + ":"
            + minutes + ":" + seconds;

        if (distance < 0) {
            clearInterval(x);
            document.getElementById("demo").innerHTML = "EXPIRED";
        }
    }, 500);
});


// giftRuleBtn.onclick = function () {
//     let giftRuleImg = document.getElementById('giftRuleImage')
//     giftRuleImg.style.display = 'block'
// }

randomNumber.onclick = RandomChoice

// Live searching navigate function
let inputSearchEvent = (e) => {
    liveSearch(e, listItem)
}
// Live search Event
inputSearch.addEventListener('input', inputSearchEvent)
// Live search main function
listItem.forEach((item) => {
    item.onclick = (e) => {
        let item_value = item.textContent.trim()
        let limit = checkLimit()
        if (limit) {
            if(turnChoose <= 0){
                 alert(`Bạn không có lượt chọn nào.`)
            }
            alert(`Bạn đã chọn ${turnChoose} số, loại bỏ số hiện tại để chọn số mới.`)
        } else {
            clickAddItem(item, item_value)
        }
    }
})

// Get selected number
const placeSelecting = document.getElementById('item-selecting')
const selecting = placeSelecting.querySelectorAll('.group-item')
// Show selected number to chosen place function
selecting.forEach(item => {
    let item_value = item.textContent.trim()
    clickAddItem(item, item_value)
})

// Function handling search item
function liveSearch(e, listItem) {
    let value = e.target.value.toLowerCase()
    listItem.forEach((item) => {
        let item_value = item.textContent.trim()
        if (item_value.includes(value)) {
            let arrCurrent = currentSelecting()
            if (!arrCurrent.includes(item_value)) {
                setTimeout(() => {
                    item.style.display = 'block'
                }, 1)
            }
            item.onclick = onClickLiveSearch
        } else {
            setTimeout(() => {
                item.style.display = 'none'
            }, 1)
        }
    })
}

function RandomChoice(e) {
    randomLoop++
    let min = 1;
    let max = Array.from(listItem).length;
    let randomNum = Math.floor(Math.random() * (max - min + 1) + min)
    let arrResult = currentSelecting()
    if (arrResult.some(item => item.trim() === randomNum.toString())) {
        if (arrResult.length < max) {
            if (randomLoop <= 15) {
                console.log("Rerandom" + randomLoop)
                return RandomChoice(e)
            } else {
                randomLoop = 0
                alert("Không thể chọn ngẫu nhiên, vui lòng thử lại")
            }
        } else {
            randomLoop = 0
            alert("Không thể chọn ngẫu nhiên, vui lòng thử lại")
        }
    } else {
        let limit = checkLimit(e)
        if (limit) {
            alert(`Bạn đã chọn ${turnChoose} số, loại bỏ số hiện tại để chọn số mới.`)
        } else {
            randomNum -= 1
            let item = Array.from(listItem)[randomNum]
            try {
                let item_value = item.textContent.trim()
                clickAddItem(item, item_value)
                randomLoop = 0
            } catch (e) {
                randomLoop = 0
                alert("Không thể chọn ngẫu nhiên, vui lòng thử lại")
            }
        }
    }
}

function onClickLiveSearch(e) {
    let limit = checkLimit()
    if (limit) {
        alert(`Bạn đã chọn ${turnChoose} số, loại bỏ số hiện tại để chọn số mới.`)
    } else {
        clickAddItem(e.target, e.target.innerHTML.trim())
    }

    setTimeout(() => {
        inputSearch.value = ''
    }, 1)
    listItem.forEach(item => {
        let arrResult = currentSelecting()
        if (arrResult.includes(item.innerText.trim())) {
            arrResult.splice(arrResult.indexOf(item.innerText.trim()), 1)
        } else {
            setTimeout(() => {
                item.style.display = 'block'
            }, 1)
        }
    })
}

// Show item selected place at choosing position
function updatePlaceSelectingDisplay() {
    let hasDisplayedItem = false;
    selecting.forEach(item => {
        if (item.style.display === 'block') {
            hasDisplayedItem = true;
        }
    });
    placeSelecting.style.display = hasDisplayedItem ? 'block' : 'none';
}

// Function handle clicking to add item to place showing selected item
function clickAddItem(item, item_value) {
    item.style.display = 'none'
    let arrResult = currentSelecting()
    if (arrResult.includes(item_value)) {
        alert(`Không thể chọn số ${item_value}\n${arrResult}`)
    } else {
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
                innerHTML: xButton
            }
        })

        const removeBtnE = document.getElementById(removeButton.id)
        removeBtnE.onclick = function (evn) {
            evn.preventDefault()
            addItem.remove()
            removeButton.remove()
            item.style.display = 'block'
            updatePlaceSelectingDisplay()
        }
        updatePlaceSelectingDisplay()
    }
}

function checkLimit() {
    let limit = false
    // Get group chosen number at time were called
    let groupChosen = showListSelected.querySelectorAll("p.item-card")
    let groupChosenLength = Array.from(groupChosen).length
    if (groupChosenLength >= turnChoose) {
        limit = true
    }
    return limit
}

function currentSelecting() {
    // Get group chosen number at time were called
    let groupChosen = showListSelected.querySelectorAll('p.item-card')
    let arrResult = []
    for (let i of groupChosen) {
        arrResult.push(i.innerText.trim())
    }
    return arrResult
}

function addElement(parentE, child) {
    let createElement = document.createElement(child.createTag)
    parentE.appendChild(createElement)
    for (let attr in child.options) {
        createElement[attr] = child.options[attr]
    }
    return createElement
}
