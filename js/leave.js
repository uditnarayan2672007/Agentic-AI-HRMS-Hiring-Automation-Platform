// ==========================================
// HRGenie AI
// Leave Management
// leave.js
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

    console.log("Leave Management Loaded");

    // =====================================
    // Search Employee
    // =====================================

    const searchInput = document.querySelector(".top-actions input");
    const rows = document.querySelectorAll(".leave-table tbody tr");

    if (searchInput) {

        searchInput.addEventListener("keyup", function () {

            const value = this.value.toLowerCase();

            rows.forEach(row => {

                const text = row.innerText.toLowerCase();

                row.style.display = text.includes(value) ? "" : "none";

            });

        });

    }

    // =====================================
    // Apply Leave
    // =====================================

    const applyBtn = document.querySelector(".apply-btn");

    if (applyBtn) {

        applyBtn.addEventListener("click", () => {

            alert("📅 Leave Application Form will open.");

        });

    }

    // =====================================
    // Approve Leave
    // =====================================

    const approveButtons =
        document.querySelectorAll(".approve-btn");

    approveButtons.forEach(button => {

        button.addEventListener("click", function () {

            const row = this.closest("tr");

            const badge = row.querySelector(".status");

            badge.innerText = "Approved";

            badge.classList.remove("pending");
            badge.classList.remove("rejected");
            badge.classList.add("approved");

            alert("✅ Leave Approved.");

        });

    });

    // =====================================
    // Reject Leave
    // =====================================

    const rejectButtons =
        document.querySelectorAll(".reject-btn");

    rejectButtons.forEach(button => {

        button.addEventListener("click", function () {

            const row = this.closest("tr");

            const badge = row.querySelector(".status");

            badge.innerText = "Rejected";

            badge.classList.remove("pending");
            badge.classList.remove("approved");
            badge.classList.add("rejected");

            alert("❌ Leave Rejected.");

        });

    });

    // =====================================
    // View Request
    // =====================================

    const viewButtons =
        document.querySelectorAll(".view-btn");

    viewButtons.forEach(button => {

        button.addEventListener("click", function () {

            const employee =
                this.closest("tr").querySelector("h4").innerText;

            alert("Viewing leave details for " + employee);

        });

    });

    // =====================================
    // Approve All
    // =====================================

    const approveAll =
        document.querySelector(".section-title button");

    if (approveAll) {

        approveAll.addEventListener("click", () => {

            document.querySelectorAll(".status.pending")
                .forEach(status => {

                    status.innerText = "Approved";

                    status.classList.remove("pending");
                    status.classList.add("approved");

                });

            alert("✅ All pending leave requests approved.");

        });

    }

    // =====================================
    // Progress Bar Animation
    // =====================================

    const bars = document.querySelectorAll(".progress-bar");

    bars.forEach(bar => {

        const finalWidth = getComputedStyle(bar).width;

        bar.style.width = "0";

        setTimeout(() => {

            bar.style.transition = "width 1.5s ease";

            bar.style.width = finalWidth;

        }, 300);

    });

    // =====================================
    // Statistics Cards Animation
    // =====================================

    const statCards =
        document.querySelectorAll(".stat-card");

    statCards.forEach(card => {

        card.addEventListener("mouseenter", () => {

            card.style.transform =
                "translateY(-10px) scale(1.03)";

        });

        card.addEventListener("mouseleave", () => {

            card.style.transform = "";

        });

    });

    // =====================================
    // AI Insights
    // =====================================

    const insights =
        document.querySelectorAll(".insight");

    insights.forEach(insight => {

        insight.style.cursor = "pointer";

        insight.addEventListener("click", () => {

            const title =
                insight.querySelector("h4").innerText;

            alert("🤖 AI Insight\n\n" + title);

        });

    });

    // =====================================
    // Recent Activity
    // =====================================

    const activity =
        document.querySelectorAll(".activity-list li");

    activity.forEach(item => {

        item.style.cursor = "pointer";

        item.addEventListener("click", () => {

            alert(item.innerText);

        });

    });

    // =====================================
    // Quick Actions
    // =====================================

    const quickButtons =
        document.querySelectorAll(".quick-actions button");

    quickButtons.forEach(button => {

        button.addEventListener("click", function () {

            const action = this.innerText.trim();

            switch (action) {

                case "Apply Leave":
                    alert("Opening Leave Application...");
                    break;

                case "Approve Requests":
                    alert("Approving Leave Requests...");
                    break;

                case "Export Report":
                    alert("Exporting Leave Report...");
                    break;

                case "View Calendar":
                    alert("Opening Leave Calendar...");
                    break;

                default:
                    alert(action);

            }

        });

    });

    // =====================================
    // Fade-in Animation
    // =====================================

    const cards = document.querySelectorAll(

        ".stat-card, .leave-table, .insights-card, .analytics-card, .availability-card, .activity-card, .quick-actions"

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