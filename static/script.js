const chatBody = document.querySelector(".chat-body");
const messageInput = document.querySelector(".message-input");
const sendMessageButton = document.querySelector("#send-message");
const chatbotToggler = document.querySelector("#chatbot-toggler");
const closeChatbot = document.querySelector("#close-chatbot");

// Helper: create chat bubble
const createMessageElement = (content, ...classes) => {
  const div = document.createElement("div");
  div.classList.add("message", ...classes);
  div.innerHTML = content;
  return div;
};

// Handle message sending
const handleOutgoingMessage = async (e) => {
  e.preventDefault();
  const userMessage = messageInput.value.trim();
  if (!userMessage) return;

  // Reset input
  messageInput.value = "";
  messageInput.dispatchEvent(new Event("input"));

  // Append user message
  const userDiv = createMessageElement(
    `<div class="message-text">${userMessage}</div>`,
    "user-message"
  );
  chatBody.appendChild(userDiv);

  // Append bot placeholder
  const botDiv = createMessageElement(
    `<svg class="bot-avatar" xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 1024 1024"><path d="M738.3 287.6H285.7c-59 0-106.8 47.8-106.8 106.8v303.1c0 59 47.8 106.8 106.8 106.8h81.5v111.1c0 .7.8 1.1 1.4.7l166.9-110.6 41.8-.8h117.4l43.6-.4c59 0 106.8-47.8 106.8-106.8V394.5c0-59-47.8-106.9-106.8-106.9z"></path></svg>
     <div class="message-text"><div class="thinking-indicator"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div></div>`,
    "bot-message",
    "thinking"
  );
  chatBody.appendChild(botDiv);
  chatBody.scrollTo({ top: chatBody.scrollHeight, behavior: "smooth" });

  // Fetch chatbot response
  try {
    const response = await fetch("/get", {
      method: "POST",
      body: new URLSearchParams({ msg: userMessage }),
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    const data = await response.text();

    botDiv.classList.remove("thinking");
    botDiv.querySelector(".message-text").innerText = data;
  } catch (err) {
    botDiv.classList.remove("thinking");
    botDiv.querySelector(".message-text").innerText =
      "⚠️ Error: Unable to reach the server.";
  }

  chatBody.scrollTo({ top: chatBody.scrollHeight, behavior: "smooth" });
};

// Send message on button click
sendMessageButton.addEventListener("click", handleOutgoingMessage);

// Send on Enter key (Shift+Enter for newline)
messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleOutgoingMessage(e);
  }
});

// Toggle chatbot visibility
chatbotToggler.addEventListener("click", () => {
  document.body.classList.toggle("show-chatbot");
});

closeChatbot.addEventListener("click", () => {
  document.body.classList.remove("show-chatbot");
});
