// ==========================================
// HRGenie AI Dashboard JavaScript
// ==========================================

// Wait until page loads
document.addEventListener("DOMContentLoaded", function () {

    // ===============================
    // Hiring Overview Chart
    // ===============================

    const ctx = document.getElementById("hiringChart");

    if (ctx) {

        new Chart(ctx, {
            type: "bar",

            data: {
                labels: [
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun"
                ],

                datasets: [{
                    label: "Candidates Hired",

                    data: [18, 26, 20, 34, 29, 41],

                    backgroundColor: [
                        "#2563eb",
                        "#3b82f6",
                        "#60a5fa",
                        "#2563eb",
                        "#3b82f6",
                        "#60a5fa"
                    ],

                    borderRadius: 10
                }]
            },

            options: {

                responsive: true,

                plugins: {

                    legend: {
                        display: false
                    }

                },

                scales: {

                    y: {

                        beginAtZero: true,

                        grid: {
                            color: "#eeeeee"
                        }

                    },

                    x: {

                        grid: {
                            display: false
                        }

                    }

                }

            }

        });

    }

    // ===============================
    // Notification Button
    // ===============================

    const buttons = document.querySelectorAll(".top-icons button");

    buttons.forEach(btn => {

        btn.addEventListener("click", () => {

            alert("Feature coming soon!");

        });

    });

    // ===============================
    // Search Employees
    // ===============================

    const search = document.querySelector(".search-box input");

    if (search) {

        search.addEventListener("keyup", function () {

            let value = this.value.toLowerCase();

            let rows = document.querySelectorAll("tbody tr");

            rows.forEach(row => {

                row.style.display =
                    row.innerText.toLowerCase().includes(value)
                        ? ""
                        : "none";

            });

        });

    }

    // ===============================
    // Quick Action Buttons
    // ===============================

    const actionButtons = document.querySelectorAll(".actions button");

    actionButtons.forEach(button => {

        button.addEventListener("click", function () {

            alert(this.innerText + " Clicked");

        });

    });

    // ===============================
    // Sidebar Active Menu
    // ===============================

    const menuItems = document.querySelectorAll(".menu li");

    menuItems.forEach(item => {

        item.addEventListener("click", function () {

            menuItems.forEach(i => i.classList.remove("active"));

            this.classList.add("active");

        });

    });

    // ===============================
    // KPI Card Hover Animation
    // ===============================

    const cards = document.querySelectorAll(".card");

    cards.forEach(card => {

        card.addEventListener("mouseenter", () => {

            card.style.transform = "translateY(-10px) scale(1.02)";

        });

        card.addEventListener("mouseleave", () => {

            card.style.transform = "";

        });

    });

    // ===============================
    // Fade-in Animation
    // ===============================

    const elements = document.querySelectorAll(
        ".card, .chart-card, .table-card, .mini-card, .widget-card"
    );

    elements.forEach((element, index) => {

        element.style.opacity = "0";
        element.style.transform = "translateY(20px)";

        setTimeout(() => {

            element.style.transition = "all .5s ease";

            element.style.opacity = "1";

            element.style.transform = "translateY(0)";

        }, index * 120);

    });

});