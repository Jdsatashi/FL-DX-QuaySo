function JdFormModal(info) {
    const modalParent = document.querySelector(`#${info.idModalParent}`);
    const openModalButton = document.querySelector(`#${info.idOpenModal}`)
    const closeModalButton = document.querySelector(`#${info.idCloseModal}`)
    const showData = document.querySelector(`#${info.idShowNumberToConfirm}`)
    const mainModal = document.querySelector(`#${info.idMainModal}`)
    const formModal = document.querySelector(`#${info.idModalForm}`)
    const inputModalForm = formModal.querySelector(`#${info.idModalInput}`)
    const idModalConfirm = mainModal.querySelector(`#${info.idModalConfirm}`)

    function preventDefault(event) {
        event.preventDefault();
    }

    // Open modal and send data to confirm
    openModalButton.addEventListener('click', (e) => {
        let listNumber = Array.from(showData.querySelectorAll('span.item-list'))
        // Display modal when have value selected
        if (listNumber.length > 0) {
            document.addEventListener('wheel', preventDefault, {passive: false});
            document.addEventListener('touchmove', preventDefault, {passive: false});
            // Change style to 'block' to display modal
            mainModal.style.display = 'block'
            modalParent.style.display = 'block';
            if (idModalConfirm.hasChildNodes()) {
                while (idModalConfirm.firstChild) {
                    idModalConfirm.firstChild.remove()
                }
            }
            // Add data to modal
            let listValue = Array()
            listNumber.forEach((number) => {
                let confirmValue = number.textContent
                // push data to an array
                listValue.push(confirmValue)
                // Add selected item
                let addItem = document.createElement('p')
                idModalConfirm.appendChild(addItem)
                addItem.className = `item-list-result text-center w-[64px] md-max:w-auto md-max:text-lg md-max:m-1 bg-white m-2 p-2 text-base ring-1 ring-gray-400`
                addItem.innerHTML = confirmValue.toString()
            })
            // Add list data to input as string datatype
            inputModalForm.value = listValue.toString()
        } else {

        }
    })

    // close modal
    modalParent.onclick = function (e) {
        switch (e.target) {
            case(modalParent):
            case(modalParent.firstElementChild):
            case(closeModalButton):
                clearData()
                document.removeEventListener('wheel', preventDefault);
                document.removeEventListener('touchmove', preventDefault);
        }
    }

    // Function clear data in modal while closing modal
    function clearData() {
        mainModal.style.display = 'none'
        modalParent.style.display = 'none';
        const
            itemList = Array.from(idModalConfirm.querySelectorAll('p.item-card'))
        if (itemList) {
            itemList.forEach(item => item.remove())
        }
    }
}
