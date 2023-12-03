function JdModal(info) {
    const modalParent = document.querySelector(`#${info.idModalParent}`);
    const openModalButton = document.querySelector(`#${info.idOpenModal}`)
    const closeModalButton = document.querySelector(`#${info.idCloseModal}`)
    const showData = document.querySelector(`#${info.idShowNumberToConfirm}`)
    const mainModal = document.querySelector(`#${info.idMainModal}`)
    const formModal = document.querySelector(`#${info.idModalForm}`)
    const inputModalForm = formModal.querySelector(`#${info.idModalInput}`)
    const idModalConfirm = mainModal.querySelector(`#${info.idModalConfirm}`)
    console.log(idModalConfirm, inputModalForm)
    // Open modal and send data to confirm
    openModalButton.addEventListener('click', (e) => {
        let listNumber = Array.from(showData.querySelectorAll('p.list-group-item'))
        // Display modal when have value selected
        if (listNumber.length > 0) {
            // Change style to 'block' to display modal
            mainModal.style.display = 'block'
            modalParent.style.display = 'block';
            // Add data to modal
            let listValue = Array()
            listNumber.forEach((number) => {
                let confirmValue = number.textContent
                // push data to an array
                listValue.push(confirmValue)
                // Add selected item
                let addItem = document.createElement('p')
                idModalConfirm.appendChild(addItem)
                addItem.className = `list-group-item jd-col border border-1 border-success px-4 py-2 text-center`
                addItem.innerHTML = confirmValue.toString()
            })
            // Add list data to input as string datatype
            inputModalForm.value = listValue.toString()
        }
    })

    // close modal
    modalParent.onclick = function (e) {
        switch (e.target) {
            case(mainModal):
            case(mainModal.querySelector('div.container')):
            case(closeModalButton):
                clearData()
        }
    }

    // Function clear data in modal while closing modal
    function clearData() {
        mainModal.style.display = 'none'
        modalParent.style.display = 'none';
        const
            itemList = Array.from(idModalConfirm.querySelectorAll('p.list-group-item'))
        if (itemList) {
            itemList.forEach(item => item.remove())
        }
    }
}
