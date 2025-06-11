// Main application class that coordinates everything
class RAGApplication {
  constructor() {
    // Check dependencies before instantiation
    if (typeof ChatManager === "undefined") {
      throw new Error(
        "ChatManager is not loaded. Make sure chat-manager.js loads before main.js"
      );
    }
    if (typeof AIConfigManager === "undefined") {
      throw new Error(
        "AIConfigManager is not loaded. Make sure ai-config.js loads before main.js"
      );
    }
    if (typeof FileManager === "undefined") {
      throw new Error(
        "FileManager is not loaded. Make sure file-manager.js loads before main.js"
      );
    }
    this.chatManager = new ChatManager();
    this.aiConfig = new AIConfigManager();
    this.fileManager = new FileManager();
    this.fileBrowser = null; // Will be initialized after DOM is ready
    this.isLoading = false;

    // Make aiConfig and chatManager globally accessible for enhanced source functionality
    window.aiConfig = this.aiConfig;
    window.chatManager = this.chatManager;
  }
  async init() {
    console.log("Initializing RAG Application...");

    // Initialize components in the correct order
    await this.aiConfig.initApiKeys();

    // IMPORTANT: Update UI from saved settings AFTER API keys are loaded
    this.aiConfig.updateUIFromSettings();
    await this.chatManager.fetchSessions();
    await this.aiConfig.updateUsageStats(); // Setup event listeners AFTER UI is updated
    this.setupEventListeners();

    // Initialize file browser
    this.initializeFileBrowser();

    // Always start with "New Chat" - no session persistence
    console.log(`📝 [init] Starting with fresh "New Chat" state`);
    const chatMessages = document.getElementById("chatgpt-messages");
    if (chatMessages) {
      chatMessages.innerHTML =
        '<div class="text-center p-4" style="color:white">Start the conversation below…</div>';
    }

    // Focus on input
    const userInput = document.getElementById("user-input");
    if (userInput) userInput.focus();

    console.log("RAG Application initialized successfully");
  }

  setupEventListeners() {
    // Chat form submission
    const messageForm = document.getElementById("message-form");
    if (messageForm) {
      messageForm.addEventListener("submit", (e) =>
        this.handleMessageSubmit(e)
      );
    } // Upload button - Enhanced to work both ways
    const uploadBtn = document.getElementById("upload-btn");
    if (uploadBtn) {
      uploadBtn.addEventListener("click", async () => {
        const fileInput = document.getElementById("file-upload");
        if (fileInput && fileInput.files.length > 0) {
          // Files are already selected, upload them
          try {
            console.log("📤 Uploading selected files...");
            const result = await this.fileManager.uploadFiles(fileInput.files);
            console.log("✅ Upload successful:", result);

            // Clear the file input after successful upload
            fileInput.value = ""; // Show success notification
            this.fileManager.showNotification(
              "Files uploaded successfully!",
              "success"
            );
          } catch (error) {
            console.error("❌ Upload failed:", error);
            this.fileManager.showNotification(
              `Upload failed: ${error.message}`,
              "error"
            );
          }
        } else {
          // No files selected, open file dialog
          console.log("📁 Opening file dialog...");
          fileInput.click();
        }
      });
    }

    // Rebuild index button
    const rebuildIndexBtn = document.getElementById("rebuild-index-btn");
    if (rebuildIndexBtn) {
      rebuildIndexBtn.addEventListener("click", () =>
        this.fileManager.rebuildIndex()
      );
    }

    // Clear vector DB button
    const clearVectorDbBtn = document.getElementById("clear-vector-db");
    if (clearVectorDbBtn) {
      clearVectorDbBtn.addEventListener("click", () =>
        this.fileManager.clearVectorDb()
      );
    }

    // New chat button
    const newChatBtn = document.getElementById("new-chat-btn");
    if (newChatBtn) {
      newChatBtn.addEventListener("click", () => this.chatManager.newChat());
    } // API key selection
    const apiKeySelect = document.getElementById("api-key-select");
    if (apiKeySelect) {
      apiKeySelect.addEventListener("change", (e) => {
        this.aiConfig.apiKeyIndex = parseInt(e.target.value) || 0;
        this.aiConfig.saveSettings();
      });
    }

    // Gemini model selection
    const geminiModelSelect = document.getElementById("gemini-model-select");
    if (geminiModelSelect) {
      geminiModelSelect.addEventListener("change", (e) => {
        this.aiConfig.geminiModel = e.target.value;
        this.aiConfig.saveSettings();
      });
    }

    // AI mode checkboxes
    const aiModeCheckboxes = document.querySelectorAll(".ai-mode-checkbox");
    aiModeCheckboxes.forEach((checkbox) => {
      checkbox.addEventListener("change", () => this.aiConfig.updateAiModes());
    }); // Show sources checkbox
    // Show sources checkbox event handler - ENHANCED VERSION
    const showSourcesCheckbox = document.getElementById("show-sources");
    if (showSourcesCheckbox) {
      // Initialize from aiConfig
      showSourcesCheckbox.checked = window.aiConfig
        ? window.aiConfig.showSources
        : false;

      showSourcesCheckbox.addEventListener("change", (e) => {
        const isChecked = e.target.checked;
        console.log(`🔍 [ShowSources] Checkbox changed to: ${isChecked}`);
        console.log(
          `📊 Current session ID: ${
            window.ragApp ? window.ragApp.chatManager.sessionId : "none"
          }`
        );
        console.log(
          `💬 Chat history length: ${
            window.ragApp ? window.ragApp.chatManager.chatHistory.length : 0
          }`
        );

        // Update aiConfig immediately
        if (window.aiConfig) {
          window.aiConfig.showSources = isChecked;
          window.aiConfig.saveSettings();
          console.log(
            `💾 [ShowSources] Settings saved. aiConfig.showSources: ${window.aiConfig.showSources}`
          );
        }
        console.log(`🔄 [ShowSources] Updating sources visibility...`);
        // CRITICAL FIX: Instead of re-rendering entire chat, just toggle source visibility
        if (window.ragApp && window.ragApp.chatManager) {
          if (isChecked) {
            // Show sources: fetch and display for existing RAG/MetaRAG messages
            console.log(
              `🔍 [ShowSources] Showing sources for existing messages...`
            );
            window.ragApp.chatManager.showSourcesForExistingMessages();
          } else {
            // Hide sources: remove all existing source displays
            console.log(`🙈 [ShowSources] Hiding all sources...`);
            window.ragApp.chatManager.hideAllSources();
          }

          console.log(
            `✅ [ShowSources] Sources visibility updated without re-render`
          );
        }
      });
    }

    // Chat list interactions
    const chatList = document.getElementById("chat-list");
    if (chatList) {
      chatList.addEventListener("click", (e) => this.handleChatListClick(e));
    }

    // Chat search
    const chatSearch = document.getElementById("chat-search");
    if (chatSearch) {
      chatSearch.addEventListener("input", (e) => {
        this.chatManager.renderChatList(e.target.value);
      });
    }
  }

  /**
   * Initialize the file browser functionality
   */
  initializeFileBrowser() {
    try {
      // Check if FileBrowser class is available
      if (typeof FileBrowser === "undefined") {
        console.warn(
          "FileBrowser class not found, skipping file browser initialization"
        );
        return;
      }

      // Initialize file browser with file manager instance
      this.fileBrowser = new FileBrowser(this.fileManager);

      // Listen for file selection events
      document.addEventListener("fileSelected", (event) => {
        const { filePath, fileName } = event.detail;
        console.log(`📁 File selected: ${fileName}`);
        // You can add additional file selection handling here
      });

      console.log("✅ File browser initialized successfully");
    } catch (error) {
      console.error("❌ Failed to initialize file browser:", error);
    }
  }

  async handleMessageSubmit(e) {
    e.preventDefault();

    if (this.isLoading) return;

    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const message = userInput?.value?.trim();

    if (!message) return;

    this.isLoading = true;
    userInput.disabled = true;
    sendBtn.disabled = true;
    sendBtn.textContent = "Sending...";

    try {
      // Get current session or create new one
      if (!this.chatManager.sessionId) {
        const response = await fetch("/sessions", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({}),
        });
        const session = await response.json();
        this.chatManager.sessionId = session.id;
        // localStorage.setItem replaced - now handled server-side;

        // Auto-name the session based on first message
        const chatName = this.chatManager.generateChatName(message);
        await this.updateSessionName(session.id, chatName);
      }

      // Update AI configuration
      this.aiConfig.updateAiModes();

      // Prepare chat request
      const chatRequest = {
        session_id: this.chatManager.sessionId,
        message: message,
        ai_modes: this.aiConfig.aiModes,
        api_key_index: this.aiConfig.getSelectedApiKey(),
        gemini_model: this.aiConfig.getSelectedModel(),
      }; // Add user message to UI immediately
      this.addUserMessageToUI(message);
      userInput.value = "";

      // Add loading bubbles for each selected AI mode immediately
      this.addLoadingBubblesForAiModes(this.aiConfig.aiModes); // Send chat request
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(chatRequest),
      });

      if (!response.ok)
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);

      const result = await response.json();
      this.handleChatResponse(result);

      // Update usage stats
      await this.aiConfig.updateUsageStats();

      // Refresh sessions list
      await this.chatManager.fetchSessions();
    } catch (error) {
      console.error("Error sending message:", error);

      // Replace any remaining loading bubbles with error message
      if (this.loadingBubbles) {
        this.loadingBubbles.forEach((loadingBubble, aiType) => {
          this.chatManager.replaceLoadingBubbleWithError(loadingBubble, aiType);
        });
        this.loadingBubbles.clear();
      }

      this.addErrorMessageToUI("Error: " + error.message);
    } finally {
      this.isLoading = false;
      userInput.disabled = false;
      sendBtn.disabled = false;
      sendBtn.textContent = "Send";
      userInput.focus();
    }
  }
  addUserMessageToUI(message) {
    const chatMessages = document.getElementById("chatgpt-messages");
    if (!chatMessages) return;

    const messageGroup = [
      {
        role: "user",
        content: message,
        ai_type: null,
      },
    ];

    this.chatManager.addMessageGroup(messageGroup, 0);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  addLoadingBubblesForAiModes(aiModes) {
    const chatMessages = document.getElementById("chatgpt-messages");
    if (!chatMessages) return;

    // Store loading bubble references for later replacement
    this.loadingBubbles = new Map();

    aiModes.forEach((aiMode, index) => {
      const loadingMessageGroup = [
        {
          role: "assistant",
          content: "", // Empty content for loading state
          ai_type: aiMode,
          isLoading: true,
        },
      ];

      // Create loading bubble
      const loadingBubble = this.chatManager.addLoadingMessageGroup(
        loadingMessageGroup,
        0,
        aiMode
      );

      // Store reference to replace later
      this.loadingBubbles.set(aiMode, loadingBubble);
    });

    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
  handleChatResponse(result) {
    const answers = result.answers || [result.answer];
    const aiModes = this.aiConfig.aiModes;
    const messageSources = result.message_sources || [];

    // Replace loading bubbles with actual responses
    answers.forEach((answer, index) => {
      const aiType = aiModes[index] || "Unknown";

      // Check if we have a loading bubble to replace
      if (this.loadingBubbles && this.loadingBubbles.has(aiType)) {
        const loadingBubble = this.loadingBubbles.get(aiType);
        this.chatManager.replaceLoadingBubbleWithResponse(
          loadingBubble,
          answer,
          aiType,
          messageSources[index] || []
        );
        this.loadingBubbles.delete(aiType);
      } else {
        // Fallback: add new message group if no loading bubble exists
        const messageGroup = [
          {
            role: "assistant",
            content: answer,
            ai_type: aiType,
          },
        ];

        // Pass sources for this specific answer if available
        const sourcesForThisAnswer = messageSources[index] || [];
        this.chatManager.addMessageGroup(messageGroup, 0, sourcesForThisAnswer);
      }
    });

    // Clean up any remaining loading bubbles (in case of errors or missing responses)
    if (this.loadingBubbles) {
      this.loadingBubbles.forEach((loadingBubble, aiType) => {
        this.chatManager.replaceLoadingBubbleWithError(loadingBubble, aiType);
      });
      this.loadingBubbles.clear();
    }

    const chatMessages = document.getElementById("chatgpt-messages");
    if (chatMessages) {
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  }

  addErrorMessageToUI(errorMessage) {
    const messageGroup = [
      {
        role: "assistant",
        content: errorMessage,
        ai_type: "Error",
      },
    ];

    this.chatManager.addMessageGroup(messageGroup, 0);

    const chatMessages = document.getElementById("chatgpt-messages");
    if (chatMessages) {
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  }

  handleChatListClick(e) {
    const chatItem = e.target.closest(".chat-item");
    if (!chatItem) return;

    const action = e.target.dataset.action;
    const chatId = e.target.dataset.chatId || chatItem.dataset.chatId;

    if (action === "delete") {
      this.chatManager.deleteChat(chatId);
    } else if (action === "rename") {
      this.handleRenameChat(chatId);
    } else {
      this.chatManager.selectChat(chatId);
    }
  }

  async handleRenameChat(chatId) {
    const newName = prompt("Enter new chat name:");
    if (!newName || !newName.trim()) return;

    try {
      await this.updateSessionName(chatId, newName.trim());
      await this.chatManager.fetchSessions();
    } catch (error) {
      alert("Error renaming chat: " + error.message);
    }
  }

  async updateSessionName(sessionId, name) {
    const response = await fetch(`/sessions/${sessionId}/rename`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name }),
    });

    if (!response.ok) {
      throw new Error(`Failed to rename session: ${response.statusText}`);
    }

    return await response.json();
  }
}

// Global application instance and initialization state
let ragApp = null;
let isInitialized = false;

// Wait for all dependencies to load
function waitForDependencies() {
  return new Promise((resolve, reject) => {
    const checkDependencies = () => {
      if (
        typeof FileManager !== "undefined" &&
        typeof AIConfigManager !== "undefined" &&
        typeof ChatManager !== "undefined"
      ) {
        console.log("✅ All dependencies loaded successfully");
        resolve();
      } else {
        console.log("⏳ Waiting for dependencies...", {
          FileManager: typeof FileManager !== "undefined",
          AIConfigManager: typeof AIConfigManager !== "undefined",
          ChatManager: typeof ChatManager !== "undefined",
        });
        setTimeout(checkDependencies, 50);
      }
    };

    checkDependencies();

    // Timeout after 5 seconds
    setTimeout(() => {
      reject(new Error("Timeout waiting for dependencies to load"));
    }, 5000);
  });
}

async function init() {
  if (isInitialized) {
    console.log("🔄 Application already initialized, skipping...");
    return;
  }

  console.log("🚀 Initializing RAG Application...");

  try {
    // Wait for all dependencies to be loaded
    await waitForDependencies();

    ragApp = new RAGApplication();
    window.ragApp = ragApp; // Expose immediately after creation

    await ragApp.init();
    isInitialized = true;
    console.log("✅ RAG Application initialized successfully");
  } catch (error) {
    console.error("❌ Failed to initialize RAG Application:", error);
    isInitialized = false;
  }
}

// Global initialization function for HTML onload
window.initializeApplication = function () {
  console.log("🎯 Global initializeApplication called");
  init();
};

// Remove automatic initialization - only initialize when called from HTML
// This prevents conflicts and double initialization
console.log("📦 Main.js loaded, waiting for explicit initialization...");

function togglermenubar() {
  const sidebar = document.getElementsByClassName("sidebar1")[0];
  const toggleButton = document.querySelector(".sidebar-toggle");
  if (!sidebar || !toggleButton) return;

  const isCurrentlyHidden = sidebar.style.display === "none";

  // Toggle active state for hamburger transformation
  toggleButton.classList.toggle("active", isCurrentlyHidden);

  // Toggle sidebar visibility
  if (isCurrentlyHidden) {
    sidebar.style.display = "block";
    toggleButton.style.marginLeft = "182.8px";
  } else {
    sidebar.style.display = "none";
    toggleButton.style.marginLeft = "0px";
  }
}
