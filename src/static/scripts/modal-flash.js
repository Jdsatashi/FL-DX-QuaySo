function ModalFlash(ParentId, CloseBtnId) {
    const modalParent = document.getElementById(ParentId);
    const closeModalButton = document.getElementById(CloseBtnId)

    if (modalParent.style.display !== 'none') {
        document.addEventListener('wheel', preventDefault, {passive: false});
        document.addEventListener('touchmove', preventDefault, {passive: false});
        document.addEventListener('keydown', inputKey, {passive: false});
    }

    function preventDefault(event) {
        event.preventDefault();
    }

    function inputKey(event) {
        switch (event.code) {
            case 'ArrowLeft':
            case 'ArrowRight':
            case 'ArrowUp':
            case 'ArrowDown':
                event.preventDefault();
                break
            case 'Enter':
            case 'Escape':
                console.log("Close modal")
                closeModal()
                break
            case 'Space':
                event.preventDefault();
                closeModal()
                break
        }
    }

    function closeModal() {
        modalParent.style.display = "none";
        document.removeEventListener('wheel', preventDefault);
        document.removeEventListener('touchmove', preventDefault);
        document.removeEventListener('keydown', inputKey)
    }

    modalParent.onclick = function (e) {
        switch (e.target) {
            case(modalParent):
            case(modalParent.firstElementChild):
            case(closeModalButton):
                closeModal()
        }
    }
}
