// ==========================================
// HRGenie AI Recruitment JavaScript
// ==========================================

document.addEventListener("DOMContentLoaded", function () {

    console.log("Recruitment Module Loaded");

    // ==========================================
    // Search Candidate
    // ==========================================

    const searchBox = document.querySelector(".top-actions input");

    if (searchBox) {

        searchBox.addEventListener("keyup", function () {

            const value = this.value.toLowerCase();

            const rows = document.querySelectorAll(".candidate-table tbody tr");

            rows.forEach(row => {

                const text = row.innerText.toLowerCase();

                row.style.display = text.includes(value) ? "" : "none";

            });

        });

    }

    // ==========================================
    // Resume Upload Button
    // ==========================================

    const uploadButton = document.querySelector(".upload-box button");

    if (uploadButton) {

        uploadButton.addEventListener("click", function () {

            alert("Resume Upload feature will be connected to the backend.");

        });

    }

    // ==========================================
    // Add Candidate Button
    // ==========================================

    const addButton = document.querySelector(".add-btn");

    if (addButton) {

        addButton.addEventListener("click", function () {

            alert("Add Candidate Form Coming Soon!");

        });

    }

    // ==========================================
    // Quick Action Buttons
    // ==========================================

    const quickButtons = document.querySelectorAll(".quick-actions button");

    quickButtons.forEach(button => {

        button.addEventListener("click", function () {

            alert(this.innerText + " Clicked");

        });

    });

    // ==========================================
    // Candidate Row Click
    // ==========================================

    const rows = document.querySelectorAll(".candidate-table tbody tr");

    rows.forEach(row => {

        row.style.cursor = "pointer";

        row.addEventListener("click", function () {

            const candidate =
                this.querySelector("h4").innerText;

            alert(candidate + " Profile Opened");

        });

    });

    // ==========================================
    // AI Match Score Animation
    // ==========================================

    const circle = document.querySelector(".circle");

    if (circle) {

        let current = 0;

        const target = 94;

        const interval = setInterval(() => {

            current++;

            circle.innerHTML = current + "%";

            if (current >= target) {

                clearInterval(interval);

            }

        }, 20);

    }

    // ==========================================
    // Upload Box Hover Effect
    // ==========================================

    const uploadBox = document.querySelector(".upload-box");

    if (uploadBox) {

        uploadBox.addEventListener("dragover", function (e) {

            e.preventDefault();

            this.style.background = "#dbeafe";

            this.style.borderColor = "#1d4ed8";

        });

        uploadBox.addEventListener("dragleave", function () {

            this.style.background = "#f8fbff";

            this.style.borderColor = "#2563eb";

        });

        uploadBox.addEventListener("drop", function (e) {

            e.preventDefault();

            this.style.background = "#f8fbff";

            this.style.borderColor = "#2563eb";

            alert("Resume Uploaded Successfully!");

        });

    }

    // ==========================================
    // Statistics Card Animation
    // ==========================================

    const statCards = document.querySelectorAll(".stat-card");

    statCards.forEach(card => {

        card.addEventListener("mouseenter", function () {

            this.style.transform = "translateY(-8px) scale(1.03)";

        });

        card.addEventListener("mouseleave", function () {

            this.style.transform = "";

        });

    });

    // ==========================================
    // Smooth Fade Animation
    // ==========================================

    const cards = document.querySelectorAll(

        ".stat-card, .upload-card, .analysis-card, .score-card, .candidate-table, .recommendation-card, .pipeline-card, .interview-card, .quick-actions"

    );

    cards.forEach((card, index) => {

        card.style.opacity = "0";

        card.style.transform = "translateY(25px)";

        setTimeout(() => {

            card.style.transition = "all .6s ease";

            card.style.opacity = "1";

            card.style.transform = "translateY(0)";

        }, index * 120);

    });

});