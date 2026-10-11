"use strict";

console.log("Interview app.js loaded successfully.");

document.addEventListener("DOMContentLoaded", function () {
    const message = document.getElementById("interview-message");

    if (message) {
        message.textContent =
            "JavaScript loaded successfully. Checking Twilio connection next.";
    }
});