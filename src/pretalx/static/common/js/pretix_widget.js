document.addEventListener("DOMContentLoaded", function() {

    window.pretixWidgetCallback = function () {
        window.PretixWidget.addCloseListener(function () {
            console.log("Widget has been closed!");
            location.reload();
        });
    }
    function pretixWidgetOpen(target_url) {
        window.PretixWidget.open(
            target_url,
            null,
            null,
            [],
            {},
            true //skips ssl check, to make it work on local machine
        )
    }


    // Select all elements with the class `btn-pretix-purchase-ticket`
    const buttons = document.querySelectorAll(".btn-pretix-purchase-ticket");

    // Loop through each button and attach the click event
    buttons.forEach(function (button) {
        button.addEventListener("click", function (event) {
            event.preventDefault(); // Prevent the default link behavior
            const targetUrl = button.getAttribute("href"); // Get the URL from the href attribute
            pretixWidgetOpen(targetUrl); // Call your function with the target URL
        });
    });
})
