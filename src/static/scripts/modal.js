function JdModal(info) {
    const modalParent = document.querySelector(`#${info.idModalParent}`);
    const openModalButton = document.querySelector(`#${info.idOpenModal}`)
    const closeModalButton = document.querySelector(`#${info.idCloseModal}`)
    const mainModal = document.querySelector(`#${info.idMainModal}`)

    function preventDefault(event) {
        event.preventDefault();
    }

    openModalButton.onclick = () => {
        document.addEventListener('wheel', preventDefault, {passive: false});
        document.addEventListener('touchmove', preventDefault, {passive: false});
        // Change style to 'block' to display modal
        mainModal.style.display = 'block'
        modalParent.style.display = 'block';
    }

    modalParent.onclick = function (e) {
        switch (e.target) {
            case(modalParent):
            case(modalParent.firstElementChild):
            case(closeModalButton):
                document.removeEventListener('wheel', preventDefault);
                document.removeEventListener('touchmove', preventDefault);
        }
    }
}
