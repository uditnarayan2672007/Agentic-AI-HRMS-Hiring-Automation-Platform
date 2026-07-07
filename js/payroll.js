// ==========================================
// HRGenie AI
// Payroll Management
// payroll.js
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

    console.log("Payroll Module Loaded");

    // ===============================
    // Search Employee
    // ===============================

    const searchInput = document.querySelector(".top-actions input");
    const tableRows = document.querySelectorAll(".payroll-table tbody tr");

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
    // Process Payroll
    // ===============================

    const processBtn = document.querySelector(".process-btn");

    if (processBtn) {

        processBtn.addEventListener("click", () => {

            processBtn.disabled = true;
            processBtn.innerHTML =
                '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';

            setTimeout(() => {

                alert("✅ Payroll processed successfully!");

                processBtn.disabled = false;
                processBtn.innerHTML =
                    '<i class="fa-solid fa-money-bill-wave"></i> Process Payroll';

            }, 2000);

        });

    }

    // ===============================
    // Generate Payslips
    // ===============================

    const payslipBtn = document.querySelector(".section-title button");

    if (payslipBtn) {

        payslipBtn.addEventListener("click", () => {

            alert("📄 Payslips generated successfully.");

        });

    }

    // ===============================
    // Employee Row Click
    // ===============================

    tableRows.forEach(row => {

        row.style.cursor = "pointer";

        row.addEventListener("click", function () {

            const employee = this.querySelector("h4").innerText;

            alert("Opening payroll details for " + employee);

        });

    });

    // ===============================
    // Progress Bars
    // ===============================

    const bars = document.querySelectorAll(".progress-bar");

    bars.forEach(bar => {

        const finalWidth = getComputedStyle(bar).width;

        bar.style.width = "0";

        setTimeout(() => {

            bar.style.transition = "width 1.5s ease";
            bar.style.width = finalWidth;

        }, 300);

    });

    // ===============================
    // Statistics Cards Animation
    // ===============================

    const statCards = document.querySelectorAll(".stat-card");

    statCards.forEach(card => {

        card.addEventListener("mouseenter", () => {

            card.style.transform = "translateY(-10px) scale(1.03)";

        });

        card.addEventListener("mouseleave", () => {

            card.style.transform = "";

        });

    });

    // ===============================
    // Quick Action Buttons
    // ===============================

    const quickButtons =
        document.querySelectorAll(".quick-actions button");

    quickButtons.forEach(button => {

        button.addEventListener("click", function () {

            const action = this.innerText.trim();

            switch (action) {

                case "Process Payroll":

                    alert("Payroll processing started...");
                    break;

                case "Generate Payslips":

                    alert("Payslips generated successfully.");
                    break;

                case "Export Excel":

                    alert("Payroll exported to Excel.");
                    break;

                case "Download Report":

                    alert("Payroll report downloaded.");
                    break;

                default:

                    alert(action);

            }

        });

    });

    // ===============================
    // AI Insights Click
    // ===============================

    const insights =
        document.querySelectorAll(".insight");

    insights.forEach(item => {

        item.style.cursor = "pointer";

        item.addEventListener("click", () => {

            const title = item.querySelector("h4").innerText;

            alert("AI Details:\n\n" + title);

        });

    });

    // ===============================
    // Recent Activity Click
    // ===============================

    const activities =
        document.querySelectorAll(".activity-list li");

    activities.forEach(activity => {

        activity.style.cursor = "pointer";

        activity.addEventListener("click", () => {

            alert(activity.innerText);

        });

    });

    // ===============================
    // Fade-in Animation
    // ===============================

    const cards = document.querySelectorAll(
        ".stat-card, .payroll-table, .insights-card, .analytics-card, .activity-card, .quick-actions"
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