// ==========================================
// HRGenie AI
// HR Assistant
// chatbot.js
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

    const chatBox = document.getElementById("chatBox");
    const input = document.getElementById("messageInput");
    const sendBtn = document.getElementById("sendBtn");

    // =============================
    // Send Button
    // =============================

    sendBtn.addEventListener("click", sendMessage);

    // =============================
    // Press Enter
    // =============================

    input.addEventListener("keypress", function(e){

        if(e.key === "Enter"){

            sendMessage();

        }

    });

    // =============================
    // Send Message
    // =============================

    function sendMessage(){

        const text = input.value.trim();

        if(text === "") return;

        addMessage(text,"user");

        input.value="";

        showTyping();

        setTimeout(()=>{

            removeTyping();

            addMessage(getReply(text),"bot");

        },1200);

    }

    // =============================
    // Add Message
    // =============================

    function addMessage(text,type){

        const message=document.createElement("div");

        message.className="message "+type;

        message.innerHTML=`
            <div class="bubble">
                ${text}
            </div>
        `;

        chatBox.appendChild(message);

        chatBox.scrollTop=chatBox.scrollHeight;

    }

    // =============================
    // Typing Indicator
    // =============================

    function showTyping(){

        const typing=document.createElement("div");

        typing.className="message bot";

        typing.id="typing";

        typing.innerHTML=`
            <div class="typing">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;

        chatBox.appendChild(typing);

        chatBox.scrollTop=chatBox.scrollHeight;

    }

    function removeTyping(){

        const typing=document.getElementById("typing");

        if(typing){

            typing.remove();

        }

    }

    // =============================
    // AI Replies
    // =============================

    function getReply(message){

        message=message.toLowerCase();

        if(message.includes("leave")){

            return "📅 You currently have <b>12 leave days</b> remaining. You can apply from the Leave Management page.";

        }

        if(message.includes("salary") || message.includes("payroll")){

            return "💰 Your next payroll is scheduled for <b>31 July 2026</b>.";

        }

        if(message.includes("attendance")){

            return "📊 Your attendance this month is <b>97%</b>. Excellent work!";

        }

        if(message.includes("policy")){

            return "📖 Company policies are available in the HR Portal. Contact HR for detailed documents.";

        }

        if(message.includes("holiday")){

            return "🎉 The next company holiday is Independence Day on <b>15 August</b>.";

        }

        if(message.includes("benefit")){

            return "🏥 Employees receive medical insurance, paid leave, annual bonuses and learning benefits.";

        }

        if(message.includes("hello") || message.includes("hi")){

            return "👋 Hello! How can I assist you today?";

        }

        return "🤖 I understand your question. This demo version provides sample responses. In the full project, this would connect to an AI service.";

    }

    // =============================
    // Suggested Questions
    // =============================

    document.querySelectorAll(".suggestion-btn")
    .forEach(button=>{

        button.addEventListener("click",()=>{

            input.value=button.innerText;

            sendMessage();

        });

    });

    // =============================
    // Quick Actions
    // =============================

    document.querySelectorAll(".action-btn")
    .forEach(button=>{

        button.addEventListener("click",()=>{

            const action=button.innerText.trim();

            switch(action){

                case "Apply Leave":

                    addMessage("Apply Leave","user");

                    showTyping();

                    setTimeout(()=>{

                        removeTyping();

                        addMessage("📅 Opening Leave Management module...","bot");

                    },800);

                    break;

                case "Download Payslip":

                    addMessage("Download Payslip","user");

                    showTyping();

                    setTimeout(()=>{

                        removeTyping();

                        addMessage("💰 Payslip download started (Demo).","bot");

                    },800);

                    break;

                case "Contact HR":

                    addMessage("Contact HR","user");

                    showTyping();

                    setTimeout(()=>{

                        removeTyping();

                        addMessage("📞 HR Email: hr@company.com<br>☎ Phone: +91-9876543210","bot");

                    },800);

                    break;

                case "Raise Support Ticket":

                    addMessage("Raise Support Ticket","user");

                    showTyping();

                    setTimeout(()=>{

                        removeTyping();

                        addMessage("🎫 Support ticket created successfully (Demo).","bot");

                    },800);

                    break;

            }

        });

    });

    // =============================
    // Activity Click
    // =============================

    document.querySelectorAll(".activity-list li")
    .forEach(item=>{

        item.addEventListener("click",()=>{

            alert(item.innerText);

        });

    });

});