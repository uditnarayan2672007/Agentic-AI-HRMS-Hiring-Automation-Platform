// ==========================================
// HRGenie AI
// Analytics Dashboard
// analytics.js
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

    // ==============================
    // Animated Counters
    // ==============================

    animateCounter("employeeCount", 245);
    animateCounter("hiredCount", 34);
    animateCounter("payrollCount", 485, "$", "K");
    animateCounter("attendanceCount", 97, "", "%");

    function animateCounter(id, target, prefix = "", suffix = "") {

        const element = document.getElementById(id);

        if (!element) return;

        let current = 0;

        const increment = target / 60;

        const timer = setInterval(() => {

            current += increment;

            if (current >= target) {

                current = target;

                clearInterval(timer);

            }

            element.textContent = prefix + Math.floor(current) + suffix;

        }, 20);

    }

    // ==============================
    // Export Button
    // ==============================

    const exportBtn = document.getElementById("exportBtn");

    if (exportBtn) {

        exportBtn.addEventListener("click", () => {

            alert("Analytics report exported successfully! (Demo)");

        });

    }

    // ==============================
    // Date Filter
    // ==============================

    const filter = document.getElementById("dateFilter");

    if (filter) {

        filter.addEventListener("change", function () {

            alert("Showing data for: " + this.value);

        });

    }

    // ==============================
    // Hiring Analytics Chart
    // ==============================

    const hiringChart = document.getElementById("hiringChart");

    if (hiringChart) {

        new Chart(hiringChart, {

            type: "bar",

            data: {

                labels: ["Jan","Feb","Mar","Apr","May","Jun"],

                datasets: [{

                    label: "New Hires",

                    data: [8,12,9,15,18,22],

                    backgroundColor: "#2563eb",

                    borderRadius: 8

                }]

            },

            options: {

                responsive: true,

                plugins: {

                    legend: {

                        display: false

                    }

                }

            }

        });

    }

    // ==============================
    // Employee Growth Chart
    // ==============================

    const employeeChart = document.getElementById("employeeChart");

    if (employeeChart) {

        new Chart(employeeChart, {

            type: "line",

            data: {

                labels: ["Jan","Feb","Mar","Apr","May","Jun"],

                datasets: [{

                    label: "Employees",

                    data: [180,192,205,220,232,245],

                    borderColor: "#2563eb",

                    backgroundColor: "rgba(37,99,235,.15)",

                    fill: true,

                    tension: .4

                }]

            },

            options: {

                responsive: true

            }

        });

    }

    // ==============================
    // Payroll Chart
    // ==============================

    const payrollChart = document.getElementById("payrollChart");

    if (payrollChart) {

        new Chart(payrollChart, {

            type: "doughnut",

            data: {

                labels: [

                    "Engineering",

                    "HR",

                    "Sales",

                    "Finance",

                    "Marketing"

                ],

                datasets: [{

                    data: [42,10,22,14,12],

                    backgroundColor: [

                        "#2563eb",

                        "#22c55e",

                        "#f59e0b",

                        "#ef4444",

                        "#8b5cf6"

                    ]

                }]

            },

            options: {

                responsive: true

            }

        });

    }

    // ==============================
    // Leave Trends Chart
    // ==============================

    const leaveChart = document.getElementById("leaveChart");

    if (leaveChart) {

        new Chart(leaveChart, {

            type: "pie",

            data: {

                labels: [

                    "Casual",

                    "Medical",

                    "Paid",

                    "WFH"

                ],

                datasets: [{

                    data: [35,20,30,15],

                    backgroundColor: [

                        "#2563eb",

                        "#22c55e",

                        "#f59e0b",

                        "#ef4444"

                    ]

                }]

            },

            options: {

                responsive: true

            }

        });

    }

    // ==============================
    // Quick Action Buttons
    // ==============================

    document.querySelectorAll(".action-btn").forEach(btn => {

        btn.addEventListener("click", () => {

            alert(btn.innerText.trim() + " (Demo)");

        });

    });

    // ==============================
    // Report Buttons
    // ==============================

    document.querySelectorAll(".report-item button").forEach(btn => {

        btn.addEventListener("click", () => {

            alert("Downloading report... (Demo)");

        });

    });

    // ==============================
    // AI Recommendation Click
    // ==============================

    document.querySelectorAll(".recommendation-list li").forEach(item => {

        item.style.cursor = "pointer";

        item.addEventListener("click", () => {

            alert(item.innerText);

        });

    });

});