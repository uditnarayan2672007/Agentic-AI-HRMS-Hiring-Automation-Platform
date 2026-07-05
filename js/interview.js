// ==========================================
// HRGenie AI - Interview JS
// ==========================================

document.addEventListener("DOMContentLoaded", function () {

    console.log("AI Interview Module Loaded");

    // ================================
    // START / END INTERVIEW
    // ================================

    const startBtn = document.querySelector(".start-btn");
    const endBtn = document.querySelector(".end-btn");
    const recording = document.querySelector(".recording");

    let isLive = true;

    if (startBtn) {
        startBtn.addEventListener("click", () => {
            isLive = true;
            if (recording) recording.textContent = "🔴 Recording";
            alert("Interview Started");
        });
    }

    if (endBtn) {
        endBtn.addEventListener("click", () => {
            isLive = false;
            if (recording) recording.textContent = "⏸ Interview Ended";
            alert("Interview Ended");
        });
    }

    // ================================
    // AI CHAT AUTO TYPING EFFECT
    // ================================

    const chatBox = document.querySelector(".chat-box");

    const aiQuestions = [
        "Tell me about your experience with React.",
        "Explain JavaScript closures.",
        "How do you optimize frontend performance?",
        "What is the difference between REST and GraphQL?"
    ];

    function addMessage(text, type) {

        const msg = document.createElement("div");
        msg.classList.add(type === "ai" ? "ai-message" : "user-message");
        msg.innerText = text;

        chatBox.appendChild(msg);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Simulate AI chat flow
    let i = 0;

    function simulateChat() {

        if (!isLive) return;

        if (i < aiQuestions.length) {

            setTimeout(() => {
                addMessage(aiQuestions[i], "ai");

                setTimeout(() => {
                    addMessage("Sample candidate answer...", "user");
                    i++;
                    simulateChat();
                }, 2000);

            }, 1500);

        }

    }

    simulateChat();

    // ================================
    // PROGRESS BAR ANIMATION
    // ================================

    const bars = document.querySelectorAll(".progress-bar");

    bars.forEach(bar => {

        const width = bar.style.width;

        bar.style.width = "0%";

        setTimeout(() => {
            bar.style.transition = "width 1.5s ease";
            bar.style.width = width;
        }, 300);

    });

    // ================================
    // CAMERA BUTTON EFFECTS
    // ================================

    const camButtons = document.querySelectorAll(".camera-controls button");

    camButtons.forEach(btn => {

        btn.addEventListener("click", () => {

            btn.classList.toggle("active");
            btn.style.transform = "scale(0.9)";

            setTimeout(() => {
                btn.style.transform = "scale(1)";
            }, 150);

        });

    });

    // ================================
    // CANDIDATE SEARCH
    // ================================

    const searchInput = document.querySelector(".top-actions input");

    searchInput.addEventListener("input", function () {

        const value = this.value.toLowerCase();

        const name = document.querySelector(".candidate-profile h2");

        if (name && !name.innerText.toLowerCase().includes(value)) {
            name.style.opacity = "0.3";
        } else {
            name.style.opacity = "1";
        }

    });

    // ================================
    // TIMELINE ANIMATION
    // ================================

    const dots = document.querySelectorAll(".dot");

    dots.forEach((dot, index) => {

        setTimeout(() => {
            dot.style.transform = "scale(1.5)";
            dot.style.transition = "0.3s";
        }, index * 500);

    });

});