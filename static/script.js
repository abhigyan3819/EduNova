const chatBox = document.getElementById("chat-box");
const input = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

sendBtn.addEventListener("click", sendMessage);
input.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;

  appendMessage("user", text);
  input.value = "";
  appendTyping();

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    const data = await res.json();
    removeTyping();

    if (data.reply) appendMessage("ai", data.reply);
    else appendMessage("ai", "⚠️ " + (data.error || "Unknown error"));

  } catch (err) {
    removeTyping();
    appendMessage("ai", "⚠️ Error contacting server.");
    console.error(err);
  }
}

// --- UI rendering ---
function appendMessage(sender, text) {
  const msg = document.createElement("div");
  msg.classList.add("message", sender);
  const bubble = document.createElement("div");
  bubble.classList.add("bubble");

  let html = "";
  try { html = marked.parse(text); } 
  catch { html = text.replace(/\n/g, "<br>"); }

  const safeHTML = DOMPurify.sanitize(html);
  bubble.innerHTML = safeHTML;
  msg.appendChild(bubble);
  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;

  if (window.MathJax) MathJax.typesetPromise([bubble]);
}

function appendTyping() {
  const typing = document.createElement("div");
  typing.classList.add("message", "ai");
  typing.id = "typing";
  typing.innerHTML = `<div class="bubble typing">Thinking...</div>`;
  chatBox.appendChild(typing);
  chatBox.scrollTop = chatBox.scrollHeight;
}
function removeTyping() {
  const typing = document.getElementById("typing");
  if (typing) typing.remove();
}
