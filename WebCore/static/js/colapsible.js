function collapsible_event(event) {
    event.classList.toggle("collapsible-active");
    let content = event.nextElementSibling;
    if (content.style.maxHeight) {content.style.maxHeight = null}
    else {content.style.maxHeight = content.scrollHeight + "px"}
}