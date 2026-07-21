document.addEventListener('DOMContentLoaded', () => {
  const chatHistory = document.getElementById('chatHistory');
  const input = document.getElementById('questionInput');
  const sendButton = document.getElementById('sendButton');
  const suggestionChips = document.querySelectorAll('.suggestion-chip');

  const welcomeMessage = {
    role: 'ai',
    content: 'Hello! I can help you review pipeline health, revenue performance, client priorities, and work order risk. What would you like to explore?'
  };

  function addMessage(message, role = 'ai') {
    const bubble = document.createElement('div');
    bubble.className = `message ${role}`;
    bubble.textContent = message;
    chatHistory.appendChild(bubble);
    chatHistory.scrollTop = chatHistory.scrollHeight;
  }

  function addTypingIndicator() {
    const typing = document.createElement('div');
    typing.className = 'typing-indicator';
    typing.innerHTML = '<span></span><span></span><span></span>';
    chatHistory.appendChild(typing);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return typing;
  }

  function removeTypingIndicator(typingElement) {
    if (typingElement && typingElement.parentNode) {
      typingElement.parentNode.removeChild(typingElement);
    }
  }

  async function sendQuestion(question) {
    const trimmed = question.trim();
    if (!trimmed) {
      return;
    }

    addMessage(trimmed, 'user');
    input.value = '';
    input.style.height = 'auto';

    const typingIndicator = addTypingIndicator();

    try {
      const response = await fetch('http://127.0.0.1:5000/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question: trimmed })
      });

      const data = await response.json();
      removeTypingIndicator(typingIndicator);

      if (!response.ok) {
        const friendlyMessage = data.message || 'The assistant could not answer that request right now.';
        addMessage(friendlyMessage, 'ai');
        return;
      }

      addMessage(data.answer || 'I could not produce a response.', 'ai');
    } catch (error) {
      removeTypingIndicator(typingIndicator);
      addMessage('I am having trouble reaching the backend right now. Please try again in a moment.', 'ai');
    }
  }

  function adjustTextareaHeight() {
    input.style.height = 'auto';
    input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
  }

  sendButton.addEventListener('click', () => sendQuestion(input.value));

  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendQuestion(input.value);
    }
  });

  input.addEventListener('input', adjustTextareaHeight);

  suggestionChips.forEach((chip) => {
    chip.addEventListener('click', () => {
      sendQuestion(chip.dataset.question || chip.textContent);
    });
  });

  addMessage(welcomeMessage.content, welcomeMessage.role);
  adjustTextareaHeight();
});
