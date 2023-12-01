function addElement(parentE, child) {
    let createElement = document.createElement(child.createTag)
    parentE.appendChild(createElement)
    for(let attr in child.options){
        createElement[attr] = child.options[attr]
    }
    return createElement
}

export default addElement;
