// Medical Chatbot Frontend Logic - Enhanced Version

const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const typingIndicator = document.getElementById('typingIndicator');
const clearButton = document.getElementById('clearButton');
const suggestedPrompts = document.getElementById('suggestedPrompts');
const themeToggleSmall = document.getElementById('themeToggleSmall');
const themeIconSmall = document.getElementById('themeIconSmall');
const historyToggle = document.getElementById('historyToggle');
const historyDrawer = document.getElementById('historyDrawer');
const historyClose = document.getElementById('historyClose');
const historyTableBody = document.getElementById('historyTableBody');
// File upload and voice input intentionally disabled for now

let messageIdCounter = 0;
// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme
    initializeTheme();
    
    // Initialize Prism.js theme based on current theme
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    setPrismTheme(currentTheme);
    
    userInput.focus();
    
    // Auto-resize textarea
    userInput.addEventListener('input', autoResizeTextarea);
    
    // Handle Enter key (send) vs Shift+Enter (new line)
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!sendButton.disabled) {
                handleSubmit(e);
            }
        }
    });

    // Theme toggle
    if (themeToggleSmall) {
        themeToggleSmall.addEventListener('click', toggleTheme);
    }

    // Clear conversation
    clearButton.addEventListener('click', clearConversation);

    if (historyToggle && historyDrawer && historyClose) {
        historyToggle.addEventListener('click', async () => {
            historyDrawer.classList.add('open');
            historyDrawer.setAttribute('aria-hidden', 'false');
            await loadHistoryTable();
        });
        historyClose.addEventListener('click', () => {
            historyDrawer.classList.remove('open');
            historyDrawer.setAttribute('aria-hidden', 'true');
        });
    }

    // Suggested prompts
    document.querySelectorAll('.prompt-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const prompt = chip.getAttribute('data-prompt');
            userInput.value = prompt;
            autoResizeTextarea();
            userInput.focus();
            handleSubmit(new Event('submit'));
        });
    });
    
    // Load reactions for existing messages (like welcome message)
    loadAllReactions();
    
});

async function loadHistoryTable() {
    if (!historyTableBody) return;
    historyTableBody.innerHTML = '<tr><td colspan="3">Loading...</td></tr>';
    try {
        const res = await fetch('/api/history');
        const data = await res.json();
        if (!data.success || !data.messages || data.messages.length === 0) {
            historyTableBody.innerHTML = '<tr><td colspan="3">No messages yet.</td></tr>';
            return;
        }
        historyTableBody.innerHTML = data.messages.map((m) => {
            return `<tr>
                <td>${new Date(m.timestamp).toLocaleString()}</td>
                <td>${m.role}</td>
                <td>${escapeHtml(m.content)}</td>
            </tr>`;
        }).join('');
    } catch (e) {
        historyTableBody.innerHTML = '<tr><td colspan="3">Failed to load history.</td></tr>';
    }
}

// Load reactions for all existing messages
function loadAllReactions() {
    const messages = document.querySelectorAll('.message[data-message-id]');
    messages.forEach(message => {
        const messageId = message.getAttribute('data-message-id');
        const likeBtn = message.querySelector('.reaction-btn[data-reaction="like"]');
        const dislikeBtn = message.querySelector('.reaction-btn[data-reaction="dislike"]');
        
        if (likeBtn && dislikeBtn) {
            loadReaction(messageId, likeBtn, dislikeBtn);
        }
    });
}

// Highlight code blocks and add copy functionality
function highlightCodeBlocks(container) {
    const codeBlocks = container.querySelectorAll('pre code');
    
    codeBlocks.forEach(codeBlock => {
        const pre = codeBlock.closest('pre');
        if (!pre) return;
        
        // Skip if already processed
        if (pre.querySelector('.code-block-header')) return;
        
        // Get language from class
        const langMatch = pre.className.match(/language-(\w+)/);
        const language = langMatch ? langMatch[1] : 'text';
        
        // Create header with language and copy button
        const header = document.createElement('div');
        header.className = 'code-block-header';
        
        const langSpan = document.createElement('span');
        langSpan.className = 'code-language';
        langSpan.textContent = language;
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-code-btn';
        copyBtn.innerHTML = '<i class="fas fa-copy"></i> <span>Copy</span>';
        copyBtn.onclick = () => copyCodeBlock(codeBlock, copyBtn);
        
        header.appendChild(langSpan);
        header.appendChild(copyBtn);
        
        // Insert header before code
        pre.insertBefore(header, codeBlock);
        
        // Ensure Prism highlighting is applied
        if (window.Prism && Prism.languages[language]) {
            try {
                codeBlock.innerHTML = Prism.highlight(
                    codeBlock.textContent,
                    Prism.languages[language],
                    language
                );
            } catch (e) {
                console.log('Prism highlighting error:', e);
            }
        }
    });
}

// Copy code block to clipboard
function copyCodeBlock(codeBlock, button) {
    const textToCopy = codeBlock.textContent;
    
    navigator.clipboard.writeText(textToCopy).then(() => {
        // Visual feedback
        const icon = button.querySelector('i');
        const span = button.querySelector('span');
        const originalIcon = icon.className;
        const originalText = span.textContent;
        
        icon.className = 'fas fa-check';
        span.textContent = 'Copied!';
        button.style.color = 'var(--secondary)';
        
        setTimeout(() => {
            icon.className = originalIcon;
            span.textContent = originalText;
            button.style.color = '';
        }, 2000);
        
        showToast('Code copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy code:', err);
        showToast('Failed to copy code', 'error');
    });
}

// Theme Management
function initializeTheme() {
    // Get saved theme or default to dark
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
}

function setPrismTheme(theme) {
    const prismTheme = document.getElementById('prism-theme');
    if (prismTheme) {
        if (theme === 'light') {
            prismTheme.href = 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css';
        } else {
            prismTheme.href = 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css';
        }
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    showToast(`Switched to ${newTheme} theme`, 'success');
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    
    // Update icon
    const iconClass = theme === 'light' ? 'fas fa-sun' : 'fas fa-moon';
    if (themeIconSmall) {
        themeIconSmall.className = iconClass;
    }
    
    // Update Prism theme
    setPrismTheme(theme);
    
    // Re-highlight code blocks with new theme
    setTimeout(() => {
        document.querySelectorAll('.message-text pre code').forEach(block => {
            const pre = block.closest('pre');
            if (pre) {
                const lang = pre.className.match(/language-(\w+)/);
                if (lang && window.Prism && Prism.languages[lang[1]]) {
                    block.innerHTML = Prism.highlight(block.textContent, Prism.languages[lang[1]], lang[1]);
                }
            }
        });
    }, 100);
    
    // Add smooth transition
    document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
    
    // Remove transition after animation
    setTimeout(() => {
        document.body.style.transition = '';
    }, 300);
}

// Auto-resize textarea
function autoResizeTextarea() {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 150) + 'px';
}

// Handle form submission
chatForm.addEventListener('submit', handleSubmit);

// Configuration for retry logic
const RETRY_CONFIG = {
    maxRetries: 3,
    initialDelay: 1000, // 1 second
    maxDelay: 10000, // 10 seconds
    timeout: 30000, // 30 seconds
    backoffMultiplier: 2
};

// Request with timeout
function fetchWithTimeout(url, options, timeout = RETRY_CONFIG.timeout) {
    return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
            reject(new Error('Request timeout. Please try again.'));
        }, timeout);

        fetch(url, options)
            .then(response => {
                clearTimeout(timer);
                resolve(response);
            })
            .catch(error => {
                clearTimeout(timer);
                reject(error);
            });
    });
}

// Retry with exponential backoff
async function fetchWithRetry(url, options, retryCount = 0) {
    try {
        const response = await fetchWithTimeout(url, options, RETRY_CONFIG.timeout);
        
        // Check if response is ok
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return response;
    } catch (error) {
        // Don't retry on certain errors
        if (error.message.includes('timeout') && retryCount < RETRY_CONFIG.maxRetries) {
            const delay = Math.min(
                RETRY_CONFIG.initialDelay * Math.pow(RETRY_CONFIG.backoffMultiplier, retryCount),
                RETRY_CONFIG.maxDelay
            );
            
            console.log(`Retry attempt ${retryCount + 1}/${RETRY_CONFIG.maxRetries} after ${delay}ms`);
            showToast(`Retrying... (${retryCount + 1}/${RETRY_CONFIG.maxRetries})`, 'success');
            
            await new Promise(resolve => setTimeout(resolve, delay));
            return fetchWithRetry(url, options, retryCount + 1);
        }
        
        throw error;
    }
}

async function handleSubmit(e) {
    e.preventDefault();
    
    const question = userInput.value.trim();
    if (!question) return;
    
    // Input validation
    if (question.length > 2000) {
        showToast('Message is too long. Please keep it under 2000 characters.', 'error');
        return;
    }
    
    // Hide suggested prompts
    if (suggestedPrompts) {
        suggestedPrompts.classList.add('hidden');
    }
    
    // Disable input while processing
    userInput.disabled = true;
    sendButton.disabled = true;
    
    // Add user message to chat
    const userMessageId = addMessage(question, 'user');
    
    // Clear input
    userInput.value = '';
    autoResizeTextarea();
    
    // Show typing indicator
    showTypingIndicator();
    
    // Track request state
    let botMessageId = null;
    let hasError = false;
    
    try {
        // Send request to backend with retry logic
        const response = await fetchWithRetry('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question })
        });
        
        const data = await response.json();
        
        // Hide typing indicator
        hideTypingIndicator();
        
        if (data.success) {
            // Add bot response
            botMessageId = addMessage(data.answer, 'bot');
            updateConnectionStatus(true);
        } else {
            // Show error message with retry option
            hasError = true;
            const errorMsg = data.error || 'Something went wrong. Please try again.';
            botMessageId = addMessage(`Error: ${errorMsg}`, 'bot', true, true, question);
            showToast(errorMsg, 'error');
            updateConnectionStatus(false);
        }
    } catch (error) {
        hideTypingIndicator();
        hasError = true;
        
        // Determine error type and message
        let errorMsg = 'An error occurred. Please try again.';
        let errorType = 'error';
        
        if (error.message.includes('timeout')) {
            errorMsg = 'Request timed out. The server is taking too long to respond.';
            errorType = 'timeout';
        } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMsg = 'Network error. Please check your internet connection.';
            errorType = 'network';
        } else if (error.message.includes('HTTP')) {
            errorMsg = `Server error: ${error.message}`;
            errorType = 'server';
        }
        
        botMessageId = addMessage(errorMsg, 'bot', true, true, question);
        showToast(errorMsg, 'error');
        updateConnectionStatus(false);
        console.error('Error:', error);
    } finally {
        // Re-enable input
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.focus();
    }
}

// Retry a failed message
async function retryMessage(messageId) {
    const originalQuestion = messageQuestions.get(messageId);
    if (!originalQuestion) {
        showToast('Could not find original question to retry', 'error');
        return;
    }
    
    // Find and remove the error message
    const errorMessage = document.querySelector(`[data-message-id="${messageId}"]`);
    if (errorMessage) {
        errorMessage.remove();
    }
    
    // Set the question in input and submit
    userInput.value = originalQuestion;
    autoResizeTextarea();
    handleSubmit(new Event('submit'));
}

// Connection status management
function updateConnectionStatus(isConnected) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-indicator span:last-child');
    
    if (statusDot && statusText) {
        if (isConnected) {
            statusDot.style.background = '#10b981';
            statusDot.classList.remove('error');
            statusText.textContent = 'AI Assistant Ready';
        } else {
            statusDot.style.background = '#ef4444';
            statusDot.classList.add('error');
            statusText.textContent = 'Connection Issue';
        }
    }
}

// Check connection status periodically
function checkConnectionStatus() {
    fetch('/health', { method: 'GET' })
        .then(response => {
            if (response.ok) {
                updateConnectionStatus(true);
            } else {
                updateConnectionStatus(false);
            }
        })
        .catch(() => {
            updateConnectionStatus(false);
        });
}

// Periodic connection check (every 30 seconds)
setInterval(checkConnectionStatus, 30000);

// Store original questions for retry
const messageQuestions = new Map();

// Add message to chat
function addMessage(text, sender, isError = false, showRetry = false, originalQuestion = null) {
    const messageDiv = document.createElement('div');
    const messageId = `msg-${++messageIdCounter}`;
    messageDiv.className = `message ${sender}-message`;
    messageDiv.setAttribute('data-message-id', messageId);
    
    // Store original question for retry if it's a user message or error message
    if (sender === 'user') {
        messageQuestions.set(messageId, text);
    } else if (showRetry && originalQuestion) {
        messageQuestions.set(messageId, originalQuestion);
    }
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Create avatar
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = sender === 'user' 
        ? '<i class="fas fa-user"></i>' 
        : '<i class="fas fa-robot"></i>';
    
    // Create message content
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const messageText = document.createElement('div');
    messageText.className = isError ? 'message-text error-message' : 'message-text';
    
    // Format text with markdown support
    if (sender === 'bot' && !isError) {
        // Use marked.js for markdown rendering
        try {
            // Configure marked renderer for code blocks
            const renderer = new marked.Renderer();
            renderer.code = function(code, lang, escaped) {
                const langClass = lang ? `language-${lang}` : 'language-text';
                return `<pre class="${langClass}"><code class="${langClass}">${escaped ? code : escapeHtml(code)}</code></pre>`;
            };
            
            marked.setOptions({
                breaks: true,
                gfm: true,
                renderer: renderer
            });
            
            messageText.innerHTML = marked.parse(text);
            
            // Highlight code blocks with Prism.js after rendering
            setTimeout(() => {
                highlightCodeBlocks(messageText);
            }, 100);
        } catch (e) {
            // Fallback to plain text if markdown parsing fails
            messageText.innerHTML = formatMessage(text);
        }
    } else {
        messageText.innerHTML = formatMessage(text);
    }
    
    // Message actions (copy button and reactions for bot messages)
    const messageTime = document.createElement('div');
    messageTime.className = 'message-time';
    messageTime.textContent = time;
    
    content.appendChild(messageText);
    
    if (sender === 'bot') {
        const messageActions = document.createElement('div');
        messageActions.className = 'message-actions';
        
        // Copy button
        const copyBtn = document.createElement('button');
        copyBtn.className = 'action-btn';
        copyBtn.setAttribute('onclick', `copyMessage(this)`);
        copyBtn.setAttribute('title', 'Copy message');
        copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
        messageActions.appendChild(copyBtn);
        
        // Retry button (only for error messages)
        if (showRetry) {
            const retryBtn = document.createElement('button');
            retryBtn.className = 'action-btn retry-btn';
            retryBtn.setAttribute('onclick', `retryMessage('${messageId}')`);
            retryBtn.setAttribute('title', 'Retry request');
            retryBtn.innerHTML = '<i class="fas fa-redo"></i>';
            messageActions.appendChild(retryBtn);
        }
        
        // Like button (only for non-error messages)
        if (!isError) {
            const likeBtn = document.createElement('button');
            likeBtn.className = 'action-btn reaction-btn';
            likeBtn.setAttribute('onclick', `handleReaction(this, 'like')`);
            likeBtn.setAttribute('title', 'Helpful');
            likeBtn.setAttribute('data-reaction', 'like');
            likeBtn.setAttribute('data-message-id', messageId);
            likeBtn.innerHTML = '<i class="fas fa-thumbs-up"></i>';
            messageActions.appendChild(likeBtn);
            
            // Dislike button
            const dislikeBtn = document.createElement('button');
            dislikeBtn.className = 'action-btn reaction-btn';
            dislikeBtn.setAttribute('onclick', `handleReaction(this, 'dislike')`);
            dislikeBtn.setAttribute('title', 'Not helpful');
            dislikeBtn.setAttribute('data-reaction', 'dislike');
            dislikeBtn.setAttribute('data-message-id', messageId);
            dislikeBtn.innerHTML = '<i class="fas fa-thumbs-down"></i>';
            messageActions.appendChild(dislikeBtn);
            
            // Load saved reaction if exists
            loadReaction(messageId, likeBtn, dislikeBtn);
        }
        
        content.appendChild(messageActions);
    }
    
    content.appendChild(messageTime);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    scrollToBottom();
    
    return messageId;
}

// Escape HTML helper
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Format message text (preserve line breaks, escape HTML)
function formatMessage(text) {
    // Escape HTML to prevent XSS
    const escaped = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    
    // Convert line breaks to <br>
    return escaped.replace(/\n/g, '<br>');
}

// Copy message to clipboard
function copyMessage(button) {
    const messageDiv = button.closest('.message');
    const messageText = messageDiv.querySelector('.message-text');
    
    // Get text content (strip HTML)
    const textToCopy = messageText.innerText || messageText.textContent;
    
    // Copy to clipboard
    navigator.clipboard.writeText(textToCopy).then(() => {
        showToast('Message copied to clipboard!', 'success');
        
        // Visual feedback
        const icon = button.querySelector('i');
        const originalClass = icon.className;
        icon.className = 'fas fa-check';
        button.style.color = 'var(--secondary)';
        
        setTimeout(() => {
            icon.className = originalClass;
            button.style.color = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        showToast('Failed to copy message', 'error');
    });
}

// Clear conversation
async function clearConversation() {
    if (!confirm('Are you sure you want to clear the conversation history?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Clear all messages except welcome message
            const messages = chatMessages.querySelectorAll('.message:not([data-message-id="welcome"])');
            messages.forEach(msg => msg.remove());
            
            // Show suggested prompts again
            if (suggestedPrompts) {
                suggestedPrompts.classList.remove('hidden');
            }
            
            showToast('Conversation cleared', 'success');
            scrollToBottom();
        } else {
            showToast(data.error || 'Failed to clear conversation', 'error');
        }
    } catch (error) {
        console.error('Error clearing conversation:', error);
        showToast('Failed to clear conversation', 'error');
    }
}

// Show typing indicator
function showTypingIndicator() {
    typingIndicator.classList.add('active');
    scrollToBottom();
}

// Hide typing indicator
function hideTypingIndicator() {
    typingIndicator.classList.remove('active');
}

// Scroll to bottom of chat
function scrollToBottom() {
    setTimeout(() => {
        const chatContainer = document.querySelector('.chat-container');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 100);
}

// Handle message reactions (like/dislike)
function handleReaction(button, reactionType) {
    const messageDiv = button.closest('.message');
    const messageId = messageDiv.getAttribute('data-message-id');
    const allReactionBtns = messageDiv.querySelectorAll('.reaction-btn');
    
    // Remove active state from all reaction buttons
    allReactionBtns.forEach(btn => {
        btn.classList.remove('liked', 'disliked', 'active');
    });
    
    // Check if clicking the same reaction (toggle off)
    const isAlreadyActive = button.classList.contains(reactionType === 'like' ? 'liked' : 'disliked');
    
    if (isAlreadyActive) {
        // Remove reaction
        button.classList.remove(reactionType === 'like' ? 'liked' : 'disliked');
        saveReaction(messageId, null);
        showToast('Reaction removed', 'success');
    } else {
        // Add reaction
        button.classList.add(reactionType === 'like' ? 'liked' : 'disliked');
        button.classList.add('active');
        saveReaction(messageId, reactionType);
        
        const feedback = reactionType === 'like' ? 'Thank you for the feedback!' : 'We\'ll work to improve our responses.';
        showToast(feedback, 'success');
        
        // Remove active animation class after animation
        setTimeout(() => {
            button.classList.remove('active');
        }, 300);
    }
    
    // Optional: Send feedback to backend
    sendReactionToBackend(messageId, isAlreadyActive ? null : reactionType);
}

// Save reaction to localStorage
function saveReaction(messageId, reaction) {
    const reactions = JSON.parse(localStorage.getItem('messageReactions') || '{}');
    if (reaction) {
        reactions[messageId] = reaction;
    } else {
        delete reactions[messageId];
    }
    localStorage.setItem('messageReactions', JSON.stringify(reactions));
}

// Load saved reaction
function loadReaction(messageId, likeBtn, dislikeBtn) {
    const reactions = JSON.parse(localStorage.getItem('messageReactions') || '{}');
    const reaction = reactions[messageId];
    
    if (reaction === 'like') {
        likeBtn.classList.add('liked');
    } else if (reaction === 'dislike') {
        dislikeBtn.classList.add('disliked');
    }
}

// Send reaction to backend (optional - for analytics)
async function sendReactionToBackend(messageId, reaction) {
    try {
        // You can implement this endpoint in your Flask app if needed
        await fetch('/api/reaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message_id: messageId,
                reaction: reaction
            })
        });
    } catch (error) {
        // Silently fail - reactions are saved locally anyway
        console.log('Could not send reaction to backend:', error);
    }
}

// Toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastIcon = toast.querySelector('.toast-icon');
    const toastMessage = toast.querySelector('.toast-message');
    
    // Set icon based on type
    if (type === 'success') {
        toastIcon.className = 'toast-icon fas fa-check-circle';
        toast.classList.remove('error');
        toast.classList.add('success');
    } else {
        toastIcon.className = 'toast-icon fas fa-exclamation-circle';
        toast.classList.remove('success');
        toast.classList.add('error');
    }
    
    toastMessage.textContent = message;
    toast.classList.add('show');
    
    // Hide after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Smooth scroll behavior
const observer = new MutationObserver(() => {
    scrollToBottom();
});

observer.observe(chatMessages, {
    childList: true,
    subtree: true
});
