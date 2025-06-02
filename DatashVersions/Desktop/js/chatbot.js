/**
 * Datash - Cyberpunk Theme
 * Chatbot JavaScript
 * Handles the AI assistant chat interface and responses
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize chatbot
    const Chatbot = new DatashAI();
    Chatbot.init();
});

/**
 * DatashAI - AI Assistant Class
 * Manages the chat interface, responses, and interactions
 */
class DatashAI {
    constructor() {
        // Chat elements
        this.chatMessages = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-message');
        
        // Chat state
        this.chatHistory = [];
        this.isTyping = false;
        this.typingTimeout = null;
        this.messageQueue = [];
        
        // Predefined responses
        this.responses = {
            greeting: [
                "Hello! I'm NEXA, your Datash AI assistant. How can I help you today?",
                "Greetings, human! I'm NEXA, here to assist with all things Datash. What can I do for you?",
                "Welcome to Datash support! I'm NEXA, your AI guide. What would you like to know about Datash?"
            ],
            fallback: [
                "I'm not sure I understand. Could you rephrase your question about Datash?",
                "My neural networks are having trouble processing that. Can you ask about Datash in a different way?",
                "That's beyond my current programming. Could we focus on Datash features or functionality?"
            ],
            thanks: [
                "You're welcome! Is there anything else I can help with?",
                "My pleasure! I'm here if you need more assistance with Datash.",
                "Anytime! That's what I'm programmed for. Any other Datash questions?"
            ]
        };
        
        // Knowledge base for responses
        this.knowledge = {
            "what is datash": "Datash is a powerful data management tool designed for processing, analyzing, and visualizing complex datasets. It features AI-powered analytics, secure data handling, and intuitive interfaces for both technical and non-technical users.",
            
            "how do i start using datash": "To start using Datash, download the latest version from the Downloads section, run the installer, and follow the on-screen instructions. Once installed, you can launch Datash and begin by importing your data or connecting to a database. The intuitive interface will guide you through the process.",
            
            "what data formats are supported": "Datash supports a wide range of data formats including CSV, JSON, XML, Excel spreadsheets (XLS/XLSX), SQL databases, NoSQL databases, API connections, and even unstructured text data through our advanced parsing capabilities.",
            
            "how to connect to databases": "Datash offers seamless database connectivity. Open the 'Connections' panel, click 'New Connection', select your database type (MySQL, PostgreSQL, MongoDB, etc.), enter your credentials, and establish the connection. You can then query, visualize, and analyze your database data directly.",
            
            "explain the ai analytics feature": "The AI Analytics feature in Datash uses advanced machine learning algorithms to automatically analyze your data, identify patterns, detect anomalies, and generate insights. It can predict trends, classify data points, and even recommend optimal visualization methods based on your dataset characteristics.",
            
            "troubleshoot installation issues": "If you're experiencing installation issues, try these steps: 1) Ensure your system meets the minimum requirements, 2) Run the installer as administrator, 3) Temporarily disable antivirus software, 4) Check for and install any missing dependencies, 5) Clear temporary files and try reinstalling. If problems persist, contact our support team with the error logs located in the installation directory.",
            
            "system requirements": "Datash requires: Windows 10/11, macOS 12+, or Linux (Ubuntu 20.04+), Multi-core processor (2.0 GHz+), 4GB RAM minimum (8GB recommended), 500MB free storage space, and an internet connection for cloud features and updates.",
            
            "is datash free": "Datash offers both free and premium versions. The free version includes essential features for personal use, while the premium version provides advanced capabilities for professional and enterprise environments, including dedicated support and customization options.",
            
            "offline usage": "Yes, Datash works offline for most core functionalities. Some advanced features like cloud synchronization and certain AI capabilities require an internet connection. The offline mode ensures you can continue working with your data regardless of connectivity status.",
            
            "reporting bugs": "You can report bugs and request features through our GitHub repository or via the feedback form in the application. Our development team actively reviews all submissions and prioritizes them based on user impact and alignment with our product roadmap.",
            
            "api access": "Yes, Datash provides a comprehensive API for developers. You can integrate Datash capabilities into your own applications, automate workflows, and extend functionality. Full API documentation is available in the Developer section of our website.",
            
            "data security": "Datash takes data security seriously. All data is encrypted both in transit and at rest using industry-standard encryption protocols. We implement strict access controls, regular security audits, and follow best practices for secure development. Your data never leaves your system unless you explicitly enable cloud features.",
            
            "updates frequency": "Datash releases major updates quarterly, with minor updates and security patches released as needed. The free version receives essential updates, while the premium version gets priority access to new features and enhancements.",
            
            "export options": "Datash supports exporting your data and analysis results in multiple formats, including CSV, JSON, Excel, PDF reports, interactive HTML dashboards, and direct database exports. You can also schedule automated exports to various destinations."
        };
    }
    
    /**
     * Initialize the chatbot
     */
    init() {
        // Set up event listeners
        this.setupEventListeners();
        
        // Add suggestions click handlers
        this.setupSuggestions();
        
        // Apply holographic effects
        this.applyHolographicEffects();
        
        // Add initial welcome message after a short delay
        setTimeout(() => {
            // Initial message is already in HTML
            this.saveChatHistory('ai', this.getRandomResponse('greeting'));
        }, 500);
    }
    
    /**
     * Set up event listeners for chat interactions
     */
    setupEventListeners() {
        // Send message on button click
        this.sendButton.addEventListener('click', () => {
            this.handleUserInput();
        });
        
        // Send message on Enter key press
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleUserInput();
            }
        });
        
        // Focus input field when clicking on chat interface
        document.querySelector('.chat-interface').addEventListener('click', () => {
            this.chatInput.focus();
        });
    }
    
    /**
     * Set up click handlers for chat suggestions
     */
    setupSuggestions() {
        document.querySelectorAll('.chat-suggestion').forEach(suggestion => {
            suggestion.addEventListener('click', (e) => {
                e.preventDefault();
                const suggestionText = suggestion.textContent;
                this.chatInput.value = suggestionText;
                this.handleUserInput();
            });
        });
    }
    
    /**
     * Apply holographic effects to chat elements
     */
    applyHolographicEffects() {
        // Add scan lines effect to chat interface
        document.querySelector('.chat-interface').classList.add('scan-lines');
        
        // Add hologram effect to AI avatar
        document.querySelector('.ai-avatar').classList.add('hologram');
        
        // Add random glitch effects
        setInterval(() => {
            if (Math.random() > 0.7 && !this.isTyping) {
                const statusText = document.querySelector('.status-text');
                ThemeUtils.addGlitchEffect(statusText, 300);
            }
        }, 5000);
    }
    
    /**
     * Handle user input from the chat input field
     */
    handleUserInput() {
        const userMessage = this.chatInput.value.trim();
        
        // Don't process empty messages
        if (!userMessage) return;
        
        // Add user message to chat
        this.addMessageToChat('user', userMessage);
        
        // Clear input field
        this.chatInput.value = '';
        
        // Process the message and get AI response
        this.processUserMessage(userMessage);
    }
    
    /**
     * Process user message and generate appropriate response
     * @param {string} message - The user's message
     */
    processUserMessage(message) {
        // Save to chat history
        this.saveChatHistory('user', message);
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Simulate AI thinking time (for UX purposes)
        setTimeout(() => {
            let response = this.generateResponse(message);
            
            // Handle multiple responses if array
            if (Array.isArray(response)) {
                this.messageQueue = [...response];
                this.processMessageQueue();
            } else {
                this.addMessageToChat('ai', response);
                this.saveChatHistory('ai', response);
            }
            
            // Hide typing indicator
            this.hideTypingIndicator();
        }, 1000 + Math.random() * 1000); // Random delay between 1-2 seconds
    }
    
    /**
     * Process message queue for multi-part responses
     */
    processMessageQueue() {
        if (this.messageQueue.length === 0) return;
        
        const message = this.messageQueue.shift();
        this.addMessageToChat('ai', message);
        this.saveChatHistory('ai', message);
        
        if (this.messageQueue.length > 0) {
            this.showTypingIndicator();
            setTimeout(() => {
                this.hideTypingIndicator();
                this.processMessageQueue();
            }, 1000 + Math.random() * 1500);
        }
    }
    
    /**
     * Generate AI response based on user input
     * @param {string} userMessage - The user's message
     * @returns {string} - The AI's response
     */
    generateResponse(userMessage) {
        const message = userMessage.toLowerCase();
        
        // Check for thanks/gratitude
        if (message.includes('thank') || message.includes('thanks') || message.includes('appreciate')) {
            return this.getRandomResponse('thanks');
        }
        
        // Check knowledge base for matching response
        for (const [key, value] of Object.entries(this.knowledge)) {
            if (message.includes(key)) {
                return value;
            }
        }
        
        // For more complex queries, we could break them down into multiple responses
        if (message.includes('how to use') && message.includes('advanced')) {
            return [
                "Using advanced features in Datash requires some familiarity with the basics first.",
                "The advanced analytics module can be accessed from the 'Analytics' tab in the main interface.",
                "I recommend checking our tutorial videos on the website for detailed walkthroughs of advanced features.",
                "Is there a specific advanced feature you want to learn about?"
            ];
        }
        
        // If no specific match is found, return a fallback response
        return this.getRandomResponse('fallback');
    }
    
    /**
     * Add a message to the chat interface
     * @param {string} sender - 'user' or 'ai'
     * @param {string} message - The message text
     */
    addMessageToChat(sender, message) {
        // Create message element
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.classList.add(sender === 'user' ? 'user-message' : 'ai-message');
        
        // Add message content
        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');
        
        const messageText = document.createElement('p');
        messageText.textContent = message;
        messageContent.appendChild(messageText);
        
        // Add timestamp
        const messageTime = document.createElement('div');
        messageTime.classList.add('message-time');
        messageTime.textContent = this.getCurrentTime();
        
        // Assemble message
        messageElement.appendChild(messageContent);
        messageElement.appendChild(messageTime);
        
        // Add to chat
        this.chatMessages.appendChild(messageElement);
        
        // Apply effects
        if (sender === 'ai') {
            ThemeUtils.addGlitchEffect(messageElement, 300);
        }
        
        // Scroll to bottom
        this.scrollToBottom();
    }
    
    /**
     * Show typing indicator in chat
     */
    showTypingIndicator() {
        if (this.isTyping) return;
        
        this.isTyping = true;
        
        // Create typing indicator
        const typingElement = document.createElement('div');
        typingElement.classList.add('message', 'ai-message', 'typing-message');
        
        const typingContent = document.createElement('div');
        typingContent.classList.add('message-content');
        
        const typingIndicator = document.createElement('div');
        typingIndicator.classList.add('typing-indicator');
        
        // Add dots
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            typingIndicator.appendChild(dot);
        }
        
        typingContent.appendChild(typingIndicator);
        typingElement.appendChild(typingContent);
        
        // Add to chat
        this.chatMessages.appendChild(typingElement);
        
        // Scroll to bottom
        this.scrollToBottom();
    }
    
    /**
     * Hide typing indicator from chat
     */
    hideTypingIndicator() {
        this.isTyping = false;
        
        // Remove typing indicator
        const typingMessage = document.querySelector('.typing-message');
        if (typingMessage) {
            typingMessage.remove();
        }
    }
    
    /**
     * Scroll chat to the bottom
     */
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    /**
     * Get current time formatted for messages
     * @returns {string} Formatted time string
     */
    getCurrentTime() {
        const now = new Date();
        let hours = now.getHours();
        let minutes = now.getMinutes();
        
        // Format hours and minutes to always have 2 digits
        hours = hours < 10 ? '0' + hours : hours;
        minutes = minutes < 10 ? '0' + minutes : minutes;
        
        return `${hours}:${minutes}`;
    }
    
    /**
     * Get a random response from a category
     * @param {string} category - The response category
     * @returns {string} A random response
     */
    getRandomResponse(category) {
        const responses = this.responses[category] || this.responses.fallback;
        const randomIndex = Math.floor(Math.random() * responses.length);
        return responses[randomIndex];
    }
    
    /**
     * Save message to chat history
     * @param {string} sender - 'user' or 'ai'
     * @param {string} message - The message text
     */
    saveChatHistory(sender, message) {
        this.chatHistory.push({
            sender,
            message,
            timestamp: new Date().toISOString()
        });
        
        // Optionally, save to localStorage for persistence
        this.persistChatHistory();
    }
    
    /**
     * Save chat history to localStorage
     */
    persistChatHistory() {
        try {
            localStorage.setItem('datash_chat_history', JSON.stringify(this.chatHistory));
        } catch (error) {
            console.error('Failed to save chat history to localStorage:', error);
        }
    }
    
    /**
     * Load chat history from localStorage
     */
    loadChatHistory() {
        try {
            const savedHistory = localStorage.getItem('datash_chat_history');
            if (savedHistory) {
                this.chatHistory = JSON.parse(savedHistory);
                
                // Optionally display past conversations
                // this.displaySavedHistory();
            }
        } catch (error) {
            console.error('Failed to load chat history from localStorage:', error);
        }
    }
    
    /**
     * Display saved chat history
     * Only show last few messages to avoid clutter
     */
    displaySavedHistory() {
        // Only show the last 5 messages
        const recentHistory = this.chatHistory.slice(-5);
        
        // Clear current chat
        this.chatMessages.innerHTML = '';
        
        // Add messages to chat
        recentHistory.forEach(item => {
            this.addMessageToChat(item.sender, item.message);
        });
    }
    
    /**
     * Clear chat history
     */
    clearChatHistory() {
        this.chatHistory = [];
        this.chatMessages.innerHTML = '';
        localStorage.removeItem('datash_chat_history');
        
        // Add initial message
        this.addMessageToChat('ai', this.getRandomResponse('greeting'));
    }
}

/**
 * Error handling for chat failures
 */
window.addEventListener('error', function(e) {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages && e.target.src) {
        // Handle image loading errors in chat
        console.error('Resource loading error:', e);
    }
});

