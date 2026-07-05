// ==========================================
// HRGenie AI - Employee Management
// employees.js
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

    console.log("Employee Module Loaded");

    // ===============================
    // Search Employee
    // ===============================

    const searchInput = document.querySelector(".top-actions input");
    const tableRows = document.querySelectorAll(".employee-table tbody tr");

    if (searchInput) {

        searchInput.addEventListener("keyup", function () {

            const value = this.value.toLowerCase();

            tableRows.forEach(row => {

                const text = row.innerText.toLowerCase();

                row.style.display = text.includes(value) ? "" : "none";

            });

        });

    }

    // ===============================
    // Add Employee Button
    // ===============================

    const addBtn = document.querySelector(".add-btn");

    if (addBtn) {

        addBtn.addEventListener("click", () => {

            alert("Add Employee feature will be connected to the backend.");

        });

    }

    // ===============================
    // View All Button
    // ===============================

    const viewBtn = document.querySelector(".section-title button");

    if (viewBtn) {

        viewBtn.addEventListener("click", () => {

            alert("Displaying all employees.");

        });

    }

    // ===============================
    // Profile Buttons
    // ===============================

    const profileButtons = document.querySelectorAll(".profile-buttons button:first-child");

    profileButtons.forEach(button => {

        button.addEventListener("click", function () {

            const name = this.closest(".profile-card").querySelector("h3").innerText;

            alert("Opening profile of " + name);

        });

    });

    // ===============================
    // Message Buttons
    // ===============================

    const messageButtons = document.querySelectorAll(".profile-buttons button:last-child");

    messageButtons.forEach(button => {

        button.addEventListener("click", function () {

            const name = this.closest(".profile-card").querySelector("h3").innerText;

            alert("Messaging " + name);

        });

    });

    // ===============================
    // Employee Table Row Click
    // ===============================

    tableRows.forEach(row => {

        row.style.cursor = "pointer";

        row.addEventListener("click", function () {

            const employee = this.querySelector("h4").innerText;

            alert(employee + "'s details opened.");

        });

    });

    // ===============================
    // Progress Bar Animation
    // ===============================

    const progressBars = document.querySelectorAll(".progress-bar");

    progressBars.forEach(bar => {

        const finalWidth = window.getComputedStyle(bar).width;

        bar.style.width = "0";

        setTimeout(() => {

            bar.style.transition = "width 1.5s ease";

            bar.style.width = finalWidth;

        }, 300);

    });

    // ===============================
    // Statistics Card Hover
    // ===============================

    const statCards = document.querySelectorAll(".stat-card");

    statCards.forEach(card => {

        card.addEventListener("mouseenter", function () {

            this.style.transform = "translateY(-10px) scale(1.03)";

        });

        card.addEventListener("mouseleave", function () {

            this.style.transform = "";

        });

    });

    // ===============================
    // Quick Action Buttons
    // ===============================

    const quickButtons = document.querySelectorAll(".quick-actions button");

    quickButtons.forEach(button => {

        button.addEventListener("click", function () {

            alert(this.innerText + " clicked.");

        });

    });

    // ===============================
    // Fade-in Animation
    // ===============================

    const cards = document.querySelectorAll(
        ".stat-card, .employee-table, .profile-card, .performance-card, .attendance-card, .birthday-card, .quick-actions"
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

    // ===============================
    // Birthday Card Click
    // ===============================

    const birthdays = document.querySelectorAll(".birthday-person");

    birthdays.forEach(person => {

        person.style.cursor = "pointer";

        person.addEventListener("click", function () {

            const name = this.querySelector("h4").innerText;

            alert("Birthday reminder for " + name);

        });

    });

});