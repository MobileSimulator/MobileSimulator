// _static/custom.js
document.addEventListener("DOMContentLoaded", function() {
    var tabs = document.querySelectorAll(".sd-tab-label");
    tabs.forEach(function(tab) {
        tab.addEventListener("click", function() {
            var tabId = this.getAttribute("for");
            var content = document.getElementById(tabId);
            content.checked = true;
        });
    });
});