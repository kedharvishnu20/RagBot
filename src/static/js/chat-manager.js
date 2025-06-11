// Optimized Chat management functionality
class ChatManager {
  constructor() {
    // Don't persist session across page reloads - always start fresh
    this.sessionId = null;
    this.sessions = [];
    this.chatHistory = [];
    this.isLoading = false;

    // Optimized source management
    this.sourcesCache = new Map(); // LRU cache for sources
    this.cacheMaxSize = 50; // Limit cache size
    this.cacheTTL = 5 * 60 * 1000; // 5 minutes TTL
    this.pendingSourceRequests = new Map(); // Prevent duplicate requests

    // Performance optimization
    this.debounceTimers = new Map();
    this.abortControllers = new Map();
  }

  async fetchSessions() {
    try {
      const response = await fetch("/sessions");
      const data = await response.json();
      this.sessions = data;
      this.renderChatList();
      // No session persistence - always start fresh
      return data;
    } catch (error) {
      console.error("Error fetching sessions:", error);
      return [];
    }
  }

  renderChatList(searchQuery = "") {
    const chatList = document.getElementById("chat-list");
    if (!chatList) return;

    const filteredSessions = searchQuery
      ? this.sessions.filter((s) =>
          s.name.toLowerCase().includes(searchQuery.toLowerCase())
        )
      : this.sessions;

    chatList.innerHTML = filteredSessions
      .map(
        (s) =>
          `<div class="chat-item${s.id === this.sessionId ? " active" : ""}" 
                 data-chat-id="${s.id}">
                <span class="chat-name">${s.name || "Untitled Chat"}</span>
                <span class="rename-icon" data-action="delete" data-chat-id="${
                  s.id
                }" title="Delete chat">🗑️</span>
                <span class="rename-icon" data-action="rename" data-chat-id="${
                  s.id
                }" title="Rename chat">✏️</span>
            </div>`
      )
      .join("");

    this.highlightActiveChat();
  }

  highlightActiveChat() {
    if (this.sessionId) {
      const activeChat = document.querySelector(
        `.chat-item[data-chat-id="${this.sessionId}"]`
      );
      if (activeChat) {
        document.querySelectorAll(".chat-item").forEach((item) => {
          item.classList.remove("active");
        });
        activeChat.classList.add("active");
      }
    }
  }

  async selectChat(id) {
    if (!id) {
      return;
    }

    // Abort any pending source requests from previous chat
    this.abortPendingSourceRequests();

    this.sessionId = id;
    // Don't persist session in localStorage - always start fresh on reload
    this.highlightActiveChat();

    try {
      // First, verify the session exists
      const sessionResponse = await fetch(`/sessions/${id}`);
      if (!sessionResponse.ok) {
        throw new Error("Session not found");
      }

      // Then fetch the chat history
      const historyResponse = await fetch(`/sessions/${id}/history`);
      if (historyResponse.ok) {
        const history = await historyResponse.json();
        this.chatHistory = history || [];
      } else {
        this.chatHistory = [];
      }

      // Preload session-level sources ONLY if showSources enabled (optimization)
      if (window.aiConfig && window.aiConfig.showSources) {
        try {
          const sourcesResponse = await fetch(`/sessions/${id}/sources`);
          if (sourcesResponse.ok) {
            this.messageSources = await sourcesResponse.json();
            console.log(
              `📚 [selectChat] Preloaded ${this.messageSources.length} session sources`
            );
          }
        } catch (e) {
          console.warn("⚠️ [selectChat] Preload session sources failed:", e);
          this.messageSources = [];
        }
      }

      // OPTIMIZATION: Remove excessive prefetching that was blocking UI
      // Instead of prefetching ALL sources, just initialize the currentMessageSources array
      this.currentMessageSources = new Array(this.chatHistory.length).fill([]);

      console.log(
        `🚀 [selectChat] Chat loaded. History: ${this.chatHistory.length} messages. Prefetching disabled for better performance.`
      );

      this.renderChatHistory(this.chatHistory);
    } catch (error) {
      console.error("Error loading chat:", error);
      this.chatHistory = [];
      this.messageSources = [];
      this.currentMessageSources = [];
      this.renderChatHistory([]);
    }
  }

  async newChat() {
    // Abort any pending source requests
    this.abortPendingSourceRequests();

    // Clear session data for fresh start
    this.sessionId = null;
    this.chatHistory = [];
    this.messageSources = [];
    this.currentMessageSources = [];

    // Clear cache when starting new chat
    this.sourcesCache.clear();

    this.renderChatHistory([]);
    await this.fetchSessions();

    setTimeout(() => {
      const userInput = document.getElementById("user-input");
      if (userInput) userInput.focus();
    }, 100);
  }

  async deleteChat(chatId) {
    if (!chatId) return;

    try {
      const response = await fetch(`/sessions/${chatId}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Delete failed");

      if (chatId === this.sessionId) {
        // Abort any pending requests for this session
        this.abortPendingSourceRequests();

        this.sessionId = null;
        // localStorage.removeItem replaced - now handled server-side;
        this.chatHistory = [];
        this.messageSources = [];
        this.currentMessageSources = [];

        // Clear cache for deleted session
        this.sourcesCache.clear();

        this.renderChatHistory([]);
      }

      await this.fetchSessions();
    } catch (error) {
      console.error("Error deleting chat:", error);
      alert("Error deleting chat: " + error.message);
    }
  }

  // Utility methods for optimization
  clearSourcesCache() {
    console.log(
      `🗑️ [clearSourcesCache] Clearing cache with ${this.sourcesCache.size} entries`
    );
    this.sourcesCache.clear();
  }

  getCacheStats() {
    return {
      cacheSize: this.sourcesCache.size,
      maxSize: this.cacheMaxSize,
      pendingRequests: this.pendingSourceRequests.size,
      activeAbortControllers: this.abortControllers.size,
      debounceTimers: this.debounceTimers.size,
    };
  }

  // Debug method for development
  logPerformanceStats() {
    const stats = this.getCacheStats();
    console.log("📊 [Performance Stats]", {
      ...stats,
      cacheUtilization: `${Math.round(
        (stats.cacheSize / stats.maxSize) * 100
      )}%`,
      cacheTTL: `${this.cacheTTL / 1000}s`,
    });
  }

  renderChatHistory(history = []) {
    console.log(
      `🎨 [renderChatHistory] Called with history length: ${
        history?.length || 0
      }`
    );
    console.log(
      `🔘 [renderChatHistory] Show sources setting: ${
        window.aiConfig ? window.aiConfig.showSources : "No aiConfig"
      }`
    );

    const chatMessages = document.getElementById("chatgpt-messages");
    if (!chatMessages) {
      console.log(`❌ [renderChatHistory] No chat messages container found`);
      return;
    }

    chatMessages.innerHTML = "";
    if (!history || !history.length) {
      console.log(`📭 [renderChatHistory] No history - showing empty state`);
      chatMessages.innerHTML =
        '<div class="text-center p-4" style="color:white">Start the conversation below…</div>';
      return;
    }

    console.log(`📝 [renderChatHistory] Rendering ${history.length} messages`);
    let lastRole = null;
    let lastAiType = null;
    let messageGroup = [];
    let messageIndex = 0;

    for (const msg of history) {
      if (msg.role !== lastRole || msg.ai_type !== lastAiType) {
        if (messageGroup.length) {
          this.addMessageGroup(
            messageGroup,
            messageIndex - messageGroup.length
          );
          messageGroup = [];
        }
        lastRole = msg.role;
        lastAiType = msg.ai_type;
      }
      messageGroup.push(msg);
      messageIndex++;
    }
    if (messageGroup.length)
      this.addMessageGroup(messageGroup, messageIndex - messageGroup.length);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // CRITICAL FIX: Maintain sources after re-render to prevent them from disappearing
    // This ensures that when new messages are added, existing RAG/MetaRAG sources remain visible
    setTimeout(() => {
      this.maintainSourcesAcrossRerender();
    }, 100); // Small delay to ensure DOM is fully updated
  }

  addMessageGroup(messageGroup, startIndex = 0, immediateSources = null) {
    const chatMessages = document.getElementById("chatgpt-messages");
    if (!chatMessages) return;

    const isUser = messageGroup[0].role === "user";
    const groupDiv = document.createElement("div");
    groupDiv.className =
      "message-group " + (isUser ? "user-group" : "assistant-group");
    groupDiv.style.padding = "12px 0";
    groupDiv.style.width = "100%";

    if (isUser) {
      groupDiv.style.display = "flex";
      groupDiv.style.flexDirection = "column";
      groupDiv.style.alignItems = "flex-end";
    }

    for (let i = 0; i < messageGroup.length; i++) {
      const groupMsg = messageGroup[i];
      const currentMessageIndex = startIndex + i;
      this.addBubbleToContainer(
        groupMsg.role,
        groupMsg.content,
        groupMsg.ai_type,
        groupDiv,
        currentMessageIndex,
        immediateSources
      );
    }
    chatMessages.appendChild(groupDiv);
  }

  addBubbleToContainer(
    role,
    content,
    aiType,
    container,
    messageIndex = null,
    immediateSources = null
  ) {
    const bubbleDiv = document.createElement("div");
    let bubbleClass = "chatgpt-bubble";
    if (role === "user") {
      bubbleClass += " user";
      bubbleDiv.style.justifyContent = "flex-end";
      bubbleDiv.style.textAlign = "right";
    }
    if (aiType) bubbleClass += ` chatgpt-bubble-${aiType.toLowerCase()}`;
    bubbleDiv.className = bubbleClass;

    const avatarDiv = document.createElement("div");
    avatarDiv.className = "chatgpt-avatar";
    if (role === "user") {
      avatarDiv.textContent = "🧑";
    } else if (aiType === "RAG") {
      avatarDiv.textContent = "📚";
    } else if (aiType === "Gemini") {
      avatarDiv.textContent = "🔮";
    } else if (aiType === "Meta") {
      avatarDiv.textContent = "🤖";
    } else if (aiType === "MetaRAG") {
      avatarDiv.textContent = "🔍";
    } else {
      avatarDiv.textContent = "🤖";
    }

    const contentDiv = document.createElement("div");
    contentDiv.className = "chatgpt-bubble-content";

    let title = "";
    if (role === "user") {
      title = '<div class="msg-title-user">You</div>';
    } else if (aiType === "RAG") {
      title = '<div class="msg-title-rag">RAG</div>';
    } else if (aiType === "Gemini") {
      title = '<div class="msg-title-gemini">Gemini</div>';
    } else if (aiType === "Meta") {
      title = '<div class="msg-title-meta">Meta</div>';
    } else if (aiType === "MetaRAG") {
      title = '<div class="msg-title-MetaRAG">MetaRAG</div>';
    }
    if (role === "user") {
      contentDiv.innerHTML =
        title + "<div>" + this.escapeHtml(content) + "</div>";
    } else {
      const markdownContent =
        typeof marked !== "undefined"
          ? marked.parse(content)
          : this.escapeHtml(content);
      // Wrap AI assistant responses in bot-response container
      contentDiv.innerHTML =
        title + '<div class="bot-response">' + markdownContent + "</div>";

      if (typeof hljs !== "undefined") {
        setTimeout(() => {
          contentDiv.querySelectorAll("pre code").forEach((block) => {
            hljs.highlightElement(block);
          });
        }, 0);
      }
    }
    bubbleDiv.appendChild(avatarDiv);
    bubbleDiv.appendChild(contentDiv);

    // IMPORTANT: Add the bubble to the container BEFORE checking for sources
    // This ensures the element is in the DOM when we try to add sources to it
    container.appendChild(bubbleDiv);

    // Optimized source loading for RAG and MetaRAG messages
    if (
      role === "assistant" &&
      (aiType === "RAG" || aiType === "MetaRAG") &&
      messageIndex !== null &&
      window.aiConfig &&
      window.aiConfig.showSources
    ) {
      console.log(
        `✅ [addBubbleToContainer] Source conditions met for message ${messageIndex}`
      );

      // Strategy 0: Use immediate sources from chat response (fastest - NEW!)
      if (immediateSources && immediateSources.length > 0) {
        console.log(
          `⚡ [addBubbleToContainer] Using immediate ${immediateSources.length} sources from chat response`
        );
        this.addSourceReferences(bubbleDiv, aiType, immediateSources);
        return;
      }

      // Strategy 1: Use prefetched sources from currentMessageSources (fastest)
      const prefetchedSources =
        this.currentMessageSources && this.currentMessageSources[messageIndex];
      if (prefetchedSources && prefetchedSources.length > 0) {
        console.log(
          `🚀 [addBubbleToContainer] Using prefetched ${prefetchedSources.length} sources`
        );
        this.addSourceReferences(bubbleDiv, aiType, prefetchedSources);
        return;
      }

      // Strategy 2: Use debounced fetching for better UI responsiveness
      this.debouncedFetchMessageSources(this.sessionId, messageIndex, 50)
        .then((sources) => {
          if (sources && sources.length > 0) {
            console.log(
              `🎨 [addBubbleToContainer] Adding ${sources.length} sources via debounced fetch`
            );
            this.addSourceReferences(bubbleDiv, aiType, sources);
          } else {
            // Strategy 3: Fallback to session-level sources
            this.trySourceFallbacks(bubbleDiv, aiType);
          }
        })
        .catch((error) => {
          console.error(`💥 [addBubbleToContainer] Error:`, error);
          // Strategy 4: Error fallback
          this.trySourceFallbacks(bubbleDiv, aiType);
        });
    }
  }

  // Helper method for source fallback strategies
  trySourceFallbacks(bubbleDiv, aiType) {
    if (this.messageSources && this.messageSources.length > 0) {
      console.log(
        `🔄 [trySourceFallbacks] Using ${this.messageSources.length} session sources`
      );
      this.addSourceReferences(bubbleDiv, aiType, this.messageSources);
    } else if (
      window.currentMessageSources &&
      Array.isArray(window.currentMessageSources)
    ) {
      console.log(`💾 [trySourceFallbacks] Using local currentMessageSources`);
      this.addSourceReferences(bubbleDiv, aiType, window.currentMessageSources);
    } else {
      console.log(`❌ [trySourceFallbacks] No fallback sources available`);
    }
  }

  escapeHtml(unsafe) {
    if (typeof unsafe !== "string") return "";
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  generateChatName(message) {
    // Generate intelligent, concise chat names instead of using complete question
    const trimmed = message.trim();

    if (!trimmed) return "New Chat";

    // Remove common question words and filler words at the start
    let cleaned = trimmed
      .replace(
        /^(what|how|why|when|where|who|which|can|could|would|should|do|does|did|is|are|was|were|will|have|has|had|please|help|explain|tell me|show me|give me)\s+/i,
        ""
      )
      .replace(/^(about|with|for|to|in|on|at|by|from)\s+/i, "");

    // Extract key concepts and topics
    let title = cleaned;

    // If it's a code-related question, extract the technology/language
    const codeKeywords =
      /(javascript|python|html|css|react|node|java|c\+\+|sql|database|api|function|class|variable|array|object|component)/i;
    const codeMatch = title.match(codeKeywords);
    if (codeMatch) {
      const keyword = codeMatch[1];
      if (
        title.toLowerCase().includes("error") ||
        title.toLowerCase().includes("fix") ||
        title.toLowerCase().includes("debug")
      ) {
        title = `${keyword} Debugging`;
      } else if (
        title.toLowerCase().includes("create") ||
        title.toLowerCase().includes("build") ||
        title.toLowerCase().includes("make")
      ) {
        title = `${keyword} Development`;
      } else {
        title = `${keyword} Help`;
      }
    }
    // If it's a general question, extract main topic
    else {
      // Split into words and take first meaningful words
      const words = title.split(/\s+/);
      const meaningfulWords = words.filter(
        (word) =>
          word.length > 2 &&
          ![
            "the",
            "and",
            "for",
            "you",
            "can",
            "how",
            "what",
            "this",
            "that",
            "with",
            "from",
            "they",
            "have",
            "more",
            "will",
            "been",
            "said",
            "each",
            "make",
            "like",
            "into",
            "time",
            "very",
            "when",
            "come",
            "may",
            "way",
          ].includes(word.toLowerCase())
      );

      if (meaningfulWords.length > 0) {
        // Take first 2-3 meaningful words for the title
        title = meaningfulWords.slice(0, 3).join(" ");

        // Capitalize first letter of each word
        title = title.replace(/\b\w/g, (l) => l.toUpperCase());
      }
    }

    // Limit title length to 40 characters for better UI
    if (title.length > 40) {
      title = title.substring(0, 37) + "...";
    }

    // Fallback to a shortened version of original message if processing failed
    if (!title || title.length < 3) {
      title = trimmed.length <= 40 ? trimmed : trimmed.substring(0, 37) + "...";
    }

    return title;
  }

  // Debounced source fetching for better UI responsiveness
  debouncedFetchMessageSources(sessionId, messageIndex, delay = 100) {
    const pendingKey = `${sessionId}_${messageIndex}`;

    // Clear existing timer
    if (this.debounceTimers.has(pendingKey)) {
      clearTimeout(this.debounceTimers.get(pendingKey));
    }

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.debounceTimers.delete(pendingKey);
        this.fetchMessageSources(sessionId, messageIndex)
          .then(resolve)
          .catch(reject);
      }, delay);

      this.debounceTimers.set(pendingKey, timer);
    });
  }

  // Batch source fetching for multiple messages (used during prefetching if needed)
  async batchFetchMessageSources(sessionId, messageIndices, maxConcurrent = 3) {
    console.log(
      `📦 [batchFetchMessageSources] Fetching sources for ${messageIndices.length} messages`
    );

    const results = [];
    for (let i = 0; i < messageIndices.length; i += maxConcurrent) {
      const batch = messageIndices.slice(i, i + maxConcurrent);
      const batchPromises = batch.map((index) =>
        this.fetchMessageSources(sessionId, index).catch((error) => {
          console.warn(
            `⚠️ [batchFetchMessageSources] Error for message ${index}:`,
            error
          );
          return [];
        })
      );

      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);
    }

    return results;
  }

  // Optimized cache management methods
  getCachedSources(cacheKey) {
    const cached = this.sourcesCache.get(cacheKey);
    if (!cached) return null;

    const { data, timestamp } = cached;
    const now = Date.now();

    if (now - timestamp > this.cacheTTL) {
      this.sourcesCache.delete(cacheKey);
      return null;
    }

    // Update cache position for LRU
    this.sourcesCache.delete(cacheKey);
    this.sourcesCache.set(cacheKey, { data, timestamp });
    return data;
  }

  setCachedSources(cacheKey, sources) {
    // Implement LRU eviction
    if (this.sourcesCache.size >= this.cacheMaxSize) {
      const firstKey = this.sourcesCache.keys().next().value;
      this.sourcesCache.delete(firstKey);
    }

    this.sourcesCache.set(cacheKey, {
      data: sources,
      timestamp: Date.now(),
    });
  }

  // Optimized source fetching with intelligent caching and request management
  async fetchMessageSources(sessionId, messageIndex) {
    console.log(
      `🔍 [fetchMessageSources] Called with sessionId: ${sessionId}, messageIndex: ${messageIndex}`
    );

    if (!sessionId || messageIndex === null || messageIndex === undefined) {
      console.log(
        `❌ [fetchMessageSources] Invalid parameters - returning empty array`
      );
      return [];
    }

    // Create cache key
    const cacheKey = `${sessionId}_${messageIndex}`;

    // Check cache first - major performance improvement
    const cachedResult = this.getCachedSources(cacheKey);
    if (cachedResult) {
      console.log(
        `📋 [fetchMessageSources] Cache hit for message ${messageIndex}`
      );
      return cachedResult;
    }

    // Check for pending request to prevent duplicate API calls
    const pendingKey = `${sessionId}_${messageIndex}`;
    if (this.pendingSourceRequests.has(pendingKey)) {
      console.log(
        `⏳ [fetchMessageSources] Request already pending for message ${messageIndex}`
      );
      return this.pendingSourceRequests.get(pendingKey);
    }

    // Clear any existing debounce timer for this request
    if (this.debounceTimers.has(pendingKey)) {
      clearTimeout(this.debounceTimers.get(pendingKey));
      this.debounceTimers.delete(pendingKey);
    }

    // Check if we have local message sources from the current response (fast path)
    if (
      window.currentMessageSources &&
      Array.isArray(window.currentMessageSources) &&
      messageIndex >=
        this.chatHistory.length - window.currentMessageSources.length
    ) {
      const relativeIndex =
        messageIndex -
        (this.chatHistory.length - window.currentMessageSources.length);

      if (
        window.currentMessageSources[relativeIndex] &&
        Array.isArray(window.currentMessageSources[relativeIndex])
      ) {
        const localSources = window.currentMessageSources[relativeIndex];
        console.log(
          `✅ [fetchMessageSources] Found ${localSources.length} local sources for message ${messageIndex}`
        );

        // Cache the local sources for future use
        this.setCachedSources(cacheKey, localSources);
        return localSources;
      }
    }

    // Create abort controller for this request
    const abortController = new AbortController();
    this.abortControllers.set(pendingKey, abortController);

    // Create and store the pending request promise
    const requestPromise = this.performSourceRequest(
      sessionId,
      messageIndex,
      abortController.signal,
      cacheKey
    );
    this.pendingSourceRequests.set(pendingKey, requestPromise);

    try {
      const result = await requestPromise;
      return result;
    } finally {
      // Clean up pending request and abort controller
      this.pendingSourceRequests.delete(pendingKey);
      this.abortControllers.delete(pendingKey);
    }
  }

  // Separated request logic for better organization and testing
  async performSourceRequest(sessionId, messageIndex, signal, cacheKey) {
    console.log(
      `🌐 [performSourceRequest] Fetching from server: /sessions/${sessionId}/message_sources/${messageIndex}`
    );

    try {
      const response = await fetch(
        `/sessions/${sessionId}/message_sources/${messageIndex}`,
        {
          signal,
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          // Add timeout for better UX
          ...{ timeout: 8000 },
        }
      );

      console.log(
        `📡 [performSourceRequest] Server response status: ${response.status}`
      );

      if (response.ok) {
        const sources = await response.json();
        const normalizedSources = sources || [];

        console.log(
          `📄 [performSourceRequest] Received ${normalizedSources.length} sources from server`
        );

        // Cache successful results
        this.setCachedSources(cacheKey, normalizedSources);

        return normalizedSources;
      } else {
        console.warn(
          `⚠️ [performSourceRequest] Server returned error status: ${response.status}`
        );

        // Try fallback strategies on non-200 responses
        return this.tryFallbackSources(sessionId, messageIndex);
      }
    } catch (error) {
      if (error.name === "AbortError") {
        console.log(
          `🚫 [performSourceRequest] Request aborted for message ${messageIndex}`
        );
        return [];
      }

      console.error(`❌ [performSourceRequest] Network/fetch error:`, error);

      // Try fallback strategies on network errors
      return this.tryFallbackSources(sessionId, messageIndex);
    }
  }

  // Intelligent fallback strategies
  async tryFallbackSources(sessionId, messageIndex) {
    console.log(
      `🔄 [tryFallbackSources] Attempting fallback for message ${messageIndex}`
    );

    // Strategy 1: Try session-level sources
    try {
      const sessionResponse = await fetch(`/sessions/${sessionId}/sources`, {
        timeout: 5000,
      });
      if (sessionResponse.ok) {
        const sessionSources = await sessionResponse.json();
        if (sessionSources && sessionSources.length > 0) {
          console.log(`📚 [tryFallbackSources] Using session-level sources`);
          return sessionSources.slice(0, 3); // Limit to prevent UI overload
        }
      }
    } catch (e) {
      console.warn("⚠️ [tryFallbackSources] Session sources failed:", e);
    }

    // Strategy 2: Use cached session sources from this.messageSources
    if (this.messageSources && this.messageSources.length > 0) {
      console.log(`🌐 [tryFallbackSources] Using cached global sources`);
      return this.messageSources.slice(0, 3);
    }

    // Strategy 3: Use any locally stored sources
    if (
      window.currentMessageSources &&
      Array.isArray(window.currentMessageSources)
    ) {
      console.log(`💾 [tryFallbackSources] Using local message sources`);
      return window.currentMessageSources.slice(0, 3);
    }

    console.warn(
      `❌ [tryFallbackSources] All fallback strategies failed for message ${messageIndex}`
    );
    return [];
  }

  // Abort all pending source requests (useful for chat switching)
  abortPendingSourceRequests() {
    console.log(
      `🚫 [abortPendingSourceRequests] Aborting ${this.abortControllers.size} pending requests`
    );

    for (const [key, controller] of this.abortControllers) {
      controller.abort();
    }

    this.abortControllers.clear();
    this.pendingSourceRequests.clear();

    // Clear debounce timers
    for (const [key, timer] of this.debounceTimers) {
      clearTimeout(timer);
    }
    this.debounceTimers.clear();
  }

  addSourceReferences(bubbleDiv, aiType, sources = null) {
    console.log(
      `🔗 [addSourceReferences] Called for aiType: ${aiType}, with ${
        sources?.length || 0
      } sources`
    );

    // Use provided sources or fallback to global messageSources
    const sourcesToUse = sources || this.messageSources;
    console.log(
      `📚 [addSourceReferences] Using sources: ${
        sourcesToUse?.length || 0
      } items (provided: ${sources ? "Yes" : "No"}, global: ${
        this.messageSources?.length || 0
      })`
    );

    if (!sourcesToUse || sourcesToUse.length === 0) {
      console.log(`❌ [addSourceReferences] No sources available - skipping`);
      return;
    }

    // Find the bubble content to append sources inside it
    const bubbleContent = bubbleDiv.querySelector(".chatgpt-bubble-content");
    if (!bubbleContent) {
      console.log(
        `❌ [addSourceReferences] No bubble content found - cannot add sources`
      );
      return;
    }

    // CRITICAL FIX: Remove any existing sources div to prevent duplicates
    const existingSourcesDiv =
      bubbleContent.querySelector(".source-references");
    if (existingSourcesDiv) {
      console.log(
        `🗑️ [addSourceReferences] Removing existing sources to prevent duplicates`
      );
      existingSourcesDiv.remove();
    }

    console.log(
      `✅ [addSourceReferences] Creating sources UI for ${sourcesToUse.length} sources`
    );

    const sourcesDiv = document.createElement("div");
    sourcesDiv.className = "source-references";
    sourcesDiv.style.marginTop = "8px";
    sourcesDiv.style.paddingTop = "8px";
    sourcesDiv.style.borderTop = "1px solid rgba(255, 255, 255, 0.1)";

    const sourceLabel = document.createElement("span");
    sourceLabel.className = "source-label";
    sourceLabel.textContent = `Sources (${sourcesToUse.length}): `;
    sourceLabel.style.fontSize = "0.85rem";
    sourceLabel.style.color = "rgba(255, 255, 255, 0.7)";
    sourceLabel.style.marginRight = "8px";
    sourcesDiv.appendChild(sourceLabel);

    // Create source reference buttons for all relevant sources
    sourcesToUse.forEach((source, index) => {
      console.log(
        `📄 [addSourceReferences] Adding source ${index + 1}: ${
          source.name || "Unnamed"
        }`
      );
      const sourceRef = document.createElement("button");
      sourceRef.className = "source-ref";
      sourceRef.textContent = `${index + 1}`;
      sourceRef.title = source.name || `Source ${index + 1}`;
      sourceRef.onclick = () => this.showSourceModal(source);

      // Add visual indicator if this source links to a file
      const fileName = this.extractFileName(source);
      if (fileName) {
        sourceRef.classList.add("has-file");
        sourceRef.title += ` (${fileName})`;
      }

      // Add some styling for better visibility
      sourceRef.style.marginRight = "4px";
      sourceRef.style.padding = "2px 6px";
      sourceRef.style.fontSize = "0.8rem";

      sourcesDiv.appendChild(sourceRef);
    });

    // Append sources to the bubble content div instead of the bubble itself
    bubbleContent.appendChild(sourcesDiv);
    console.log(
      `🎉 [addSourceReferences] Successfully added ${sourcesToUse.length} source references to bubble`
    );
  }

  showSourceModal(source) {
    // Remove existing modal if any
    const existingModal = document.querySelector(".source-modal");
    if (existingModal) {
      existingModal.remove();
    }

    // Create modal
    const modal = document.createElement("div");
    modal.className = "source-modal";
    modal.onclick = (e) => {
      if (e.target === modal) {
        modal.remove();
      }
    };

    const modalContent = document.createElement("div");
    modalContent.className = "source-modal-content";

    const header = document.createElement("div");
    header.className = "source-modal-header";

    const title = document.createElement("h3");
    title.textContent = source.name || "Source";
    title.style.margin = "0";

    const closeBtn = document.createElement("span");
    closeBtn.className = "source-modal-close";
    closeBtn.innerHTML = "&times;";
    closeBtn.onclick = () => modal.remove();
    closeBtn.style.cursor = "pointer";
    closeBtn.style.fontSize = "24px";
    closeBtn.style.color = "#fff";

    header.appendChild(title);
    header.appendChild(closeBtn);

    const content = document.createElement("div");
    content.className = "source-modal-body";

    // Check if this is a file-based source that we can preview
    const sourceFileName = this.extractFileName(source);

    if (sourceFileName) {
      this.createFilePreviewContent(content, source, sourceFileName);
    } else {
      // Fallback to text content display
      this.createTextPreviewContent(content, source);
    }

    modalContent.appendChild(header);
    modalContent.appendChild(content);
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
  }

  extractFileName(source) {
    // Try to extract filename from source metadata or name
    if (source.metadata && source.metadata.source) {
      const sourcePath = source.metadata.source;
      return sourcePath.split(/[/\\]/).pop(); // Get filename from path
    }

    if (
      source.name &&
      (source.name.includes(".pdf") ||
        source.name.includes(".docx") ||
        source.name.includes(".txt"))
    ) {
      return source.name;
    }

    return null;
  }
  async createFilePreviewContent(container, source, fileName) {
    // Create clean, minimal design with proper CSS classes
    container.innerHTML = `
      <div class="clean-source-container">
        <!-- Clean Header -->
        <div class="source-header">
          <div class="source-file-info">
            <h4>📄 ${fileName}</h4>
            ${
              source.metadata && source.metadata.page
                ? `<div class="page-badge">Page ${source.metadata.page}</div>`
                : ""
            }
          </div>
          <div class="source-actions">
            <button class="action-btn primary" onclick="window.chatManager.openFileViewer('${fileName}')" title="View Full Document">
              🔍
            </button>
          </div>
        </div>
          <!-- Clean Tab Navigation -->
        <div class="clean-tabs">
          <button class="clean-tab" onclick="window.chatManager.switchTab(this, 'source-content')">
            📄 Text Extract
          </button>
          <button class="clean-tab active" onclick="window.chatManager.switchTab(this, 'document-preview')">
            🔍 Document Preview
          </button>
        </div>
          <!-- Clean Tab Content -->
        <div class="clean-tab-content">
          <!-- Source Content Tab -->
          <div id="source-content" class="clean-tab-pane">
            <div class="clean-source-text">
              ${this.escapeHtml(source.content || "No content available")}
            </div>
            ${source.metadata ? this.formatSourceMetadata(source.metadata) : ""}
          </div>
          
          <!-- Document Preview Tab (Active by default) -->
          <div id="document-preview" class="clean-tab-pane active">
            <div class="clean-loading">
              <div class="loading-spinner"></div>
              <p>Loading document preview...</p>
            </div>
          </div>
        </div>
      </div>
    `;

    // Load document preview asynchronously
    this.loadDocumentPreview(fileName, source.metadata?.page);
  }
  // Switch between tabs in the source modal
  switchTab(tabButton, targetTabId) {
    // Remove active class from all tabs and tab panes
    const tabs = document.querySelectorAll(".clean-tab");
    const tabPanes = document.querySelectorAll(".clean-tab-pane");

    tabs.forEach((tab) => tab.classList.remove("active"));
    tabPanes.forEach((pane) => pane.classList.remove("active"));

    // Add active class to clicked tab and corresponding pane
    tabButton.classList.add("active");
    const targetPane = document.getElementById(targetTabId);
    if (targetPane) {
      targetPane.classList.add("active");

      // If switching to document preview, ensure it loads
      if (targetTabId === "document-preview") {
        const loadingElement = targetPane.querySelector(".clean-loading");
        if (loadingElement && loadingElement.textContent.includes("Loading")) {
          // Try to reload if still showing loading
          const modal = document.querySelector(".source-modal");
          if (modal) {
            const fileName =
              modal.querySelector("h4")?.textContent?.replace("📄 ", "") || "";
            if (fileName) {
              this.loadDocumentPreview(fileName);
            }
          }
        }
      }
    }
  } // Load document preview content asynchronously with enhanced viewers
  async loadDocumentPreview(fileName, pageNumber = null) {
    try {
      console.log(
        `Loading document preview for: ${fileName}, page: ${pageNumber}`
      );

      // Find the document preview pane (could be in modal)
      let documentPreviewPane = null;
      const currentModal = document.querySelector(".source-modal");
      if (currentModal) {
        documentPreviewPane = currentModal.querySelector("#document-preview");
      }
      if (!documentPreviewPane) {
        documentPreviewPane = document.getElementById("document-preview");
      }

      if (!documentPreviewPane) {
        console.error("Document preview pane not found");
        return;
      }

      // Check if it's a Word document and use fast preview first
      const fileExt = fileName.toLowerCase().split(".").pop();
      const isWordDoc = ["docx", "doc"].includes(fileExt);

      // Build the API URL with optional page parameter and fast mode for Word docs
      let url = `/api/files/content-preview/${fileName}`;
      const params = new URLSearchParams();
      if (pageNumber) {
        params.append("page", pageNumber);
      }
      if (isWordDoc) {
        params.append("fast", "true"); // Use fast mode for initial load
      }
      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      console.log(`Fetching URL: ${url}`);

      // Add timeout protection (shorter for fast mode)
      const controller = new AbortController();
      const timeoutId = setTimeout(
        () => controller.abort(),
        isWordDoc ? 5000 : 10000
      );

      const response = await fetch(url, {
        signal: controller.signal,
        headers: {
          "Cache-Control": "no-cache",
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        // Enhanced error handling for specific status codes
        if (response.status === 404) {
          throw new Error(
            "Document file not found - file may have been deleted by user"
          );
        } else if (response.status === 403) {
          throw new Error("Access denied to document file");
        } else if (response.status >= 500) {
          throw new Error("Server error while loading document preview");
        } else {
          throw new Error(
            `Failed to load document preview: ${response.statusText} (${response.status})`
          );
        }
      }

      const previewData = await response.json();
      console.log("Received preview data:", previewData);

      // Create enhanced document viewer based on file type
      const documentViewerContent = this.createDocumentViewer(
        fileName,
        previewData
      );

      // Update the document preview pane with clean design
      documentPreviewPane.innerHTML = `
        <div class="document-preview-section">
          <div class="document-preview-header">
            <strong>📄 ${this.getFileTypeIcon(
              previewData.file_type
            )} Document Preview</strong>
            ${
              previewData.has_multiple_pages
                ? `
              <div class="document-page-info">
                <span>Page ${previewData.page} of ${
                    previewData.total_pages
                  }</span>
                <div class="document-page-navigation">
                  <button class="btn btn-sm btn-outline-primary" 
                          onclick="window.chatManager.loadDocumentPreview('${fileName}', ${Math.max(
                    1,
                    previewData.page - 1
                  )})"
                          ${previewData.page <= 1 ? "disabled" : ""}>
                    ← Prev
                  </button>
                  <button class="btn btn-sm btn-outline-primary" 
                          onclick="window.chatManager.loadDocumentPreview('${fileName}', ${Math.min(
                    previewData.total_pages,
                    previewData.page + 1
                  )})"
                          ${
                            previewData.page >= previewData.total_pages
                              ? "disabled"
                              : ""
                          }>
                    Next →
                  </button>
                </div>
              </div>
            `
                : ""
            }
          </div>
          ${documentViewerContent}
          <div class="document-preview-info">
            <small class="text-muted">
              ${this.getDocumentInfo(previewData)}
            </small>
          </div>
        </div>
      `;

      // If this is a Word document in fast mode, optionally trigger background conversion
      if (
        isWordDoc &&
        previewData.fast_preview &&
        previewData.will_convert_to_pdf
      ) {
        this.triggerBackgroundConversion(fileName, documentPreviewPane);
      }
    } catch (error) {
      console.error("Error loading document preview:", error);

      // Find the document preview pane using the same logic as above
      let documentPreviewPane = null;
      const currentModal = document.querySelector(".source-modal");
      if (currentModal) {
        documentPreviewPane = currentModal.querySelector("#document-preview");
      }
      if (!documentPreviewPane) {
        documentPreviewPane = document.getElementById("document-preview");
      }

      if (documentPreviewPane) {
        // Handle different error types with clean design
        let errorMessage = error.message;
        let errorTitle = "Preview Not Available";
        let errorIcon = "⚠️";

        if (error.name === "AbortError") {
          errorMessage =
            "Document preview timed out. The file might be too large or the server is busy.";
        } else if (
          error.message.includes("Document file not found") ||
          error.message.includes("404") ||
          error.message.includes("file may have been deleted")
        ) {
          // Handle file not found case
          errorMessage = "Document has been deleted by user";
          errorTitle = "Document Not Found";
          errorIcon = "🗑️";
        }

        documentPreviewPane.innerHTML = `
          <div class="document-preview-error">
            <div class="error-icon">${errorIcon}</div>
            <h4>${errorTitle}</h4>
            <p>${errorMessage}</p>
            <div class="error-actions">
              <button class="btn btn-sm btn-primary" onclick="window.chatManager.openFileViewer('${fileName}')">
                🔍 Try Opening Full Document
              </button>
            </div>
          </div>        `;
      }
    }
  }

  // Trigger background PDF conversion for Word documents
  async triggerBackgroundConversion(fileName, documentPreviewPane) {
    try {
      console.log(`Starting background conversion for: ${fileName}`);

      // Add a subtle conversion indicator
      const conversionIndicator = document.createElement("div");
      conversionIndicator.className = "conversion-indicator";
      conversionIndicator.innerHTML = `
        <div class="conversion-notice">
          <span class="conversion-spinner">🔄</span>
          <span>Converting to PDF for better preview...</span>
          <button class="btn btn-sm" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
      `;

      // Insert at the top of the preview pane
      const previewSection = documentPreviewPane.querySelector(
        ".document-preview-section"
      );
      if (previewSection) {
        previewSection.insertBefore(
          conversionIndicator,
          previewSection.firstChild
        );
      }

      // Start the conversion
      const response = await fetch(`/api/files/convert-to-pdf/${fileName}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const result = await response.json();

      if (response.ok && result.status === "success") {
        console.log(`Background conversion completed for: ${fileName}`);

        // Update the indicator to show completion
        conversionIndicator.innerHTML = `
          <div class="conversion-notice success">
            <span class="conversion-success">✅</span>
            <span>Converted to PDF! 
              <button class="btn btn-sm btn-primary" onclick="window.chatManager.loadDocumentPreview('${fileName}')">
                📄 Reload Preview
              </button>
            </span>
            <button class="btn btn-sm" onclick="this.parentElement.parentElement.remove()">×</button>
          </div>
        `;

        // Auto-remove after a few seconds
        setTimeout(() => {
          if (conversionIndicator.parentElement) {
            conversionIndicator.remove();
          }
        }, 5000);
      } else {
        console.warn(`Background conversion failed for: ${fileName}`, result);

        // Update indicator to show failure
        conversionIndicator.innerHTML = `
          <div class="conversion-notice error">
            <span class="conversion-error">⚠️</span>
            <span>PDF conversion failed. Text preview available.</span>
            <button class="btn btn-sm" onclick="this.parentElement.parentElement.remove()">×</button>
          </div>
        `;

        // Auto-remove after a few seconds
        setTimeout(() => {
          if (conversionIndicator.parentElement) {
            conversionIndicator.remove();
          }
        }, 3000);
      }
    } catch (error) {
      console.error(`Background conversion error for ${fileName}:`, error);

      // Silently handle the error - the text preview is still working
      const conversionIndicator = documentPreviewPane.querySelector(
        ".conversion-indicator"
      );
      if (conversionIndicator) {
        conversionIndicator.remove();
      }
    }
  }

  createPageNavigation(fileName, currentPage) {
    if (!fileName.toLowerCase().endsWith(".pdf")) {
      return "";
    }

    const pageNum = parseInt(currentPage);
    if (isNaN(pageNum)) {
      return "";
    }

    return `
      <div class="page-navigation">
        <button class="btn btn-sm btn-outline-primary" onclick="window.chatManager.openPdfPage('${fileName}', ${Math.max(
      1,
      pageNum - 1
    )})" ${pageNum <= 1 ? "disabled" : ""}>
          ← Prev
        </button>
        <span class="page-indicator">Page ${pageNum}</span>
        <button class="btn btn-sm btn-outline-primary" onclick="window.chatManager.openPdfPage('${fileName}', ${
      pageNum + 1
    })">
          Next →
        </button>
      </div>
    `;
  }

  async openPdfPage(fileName, pageNumber) {
    try {
      // For PDFs, we can use the browser's built-in PDF viewer with fragment identifier
      const url = `/api/files/view/${fileName}#page=${pageNumber}`;
      window.open(url, "_blank");
    } catch (error) {
      console.error("Error opening PDF page:", error);
      alert("Failed to open PDF page: " + error.message);
    }
  }

  /**
   * Maintain sources across re-renders to prevent them from disappearing
   * This is critical for RAG and MetaRAG functionality
   */
  maintainSourcesAcrossRerender() {
    console.log(
      "🔄 [maintainSourcesAcrossRerender] Starting source maintenance..."
    );

    try {
      // Get all message bubbles that should have sources
      const chatMessages = document.getElementById("chatgpt-messages");
      if (!chatMessages) {
        console.warn(
          "⚠️ [maintainSourcesAcrossRerender] Chat messages container not found"
        );
        return;
      }

      // Find RAG and MetaRAG assistant bubbles that should have sources
      const ragBubbles = chatMessages.querySelectorAll(
        ".chatgpt-bubble-rag, .chatgpt-bubble-metarag"
      );
      console.log(
        `🔍 [maintainSourcesAcrossRerender] Found ${ragBubbles.length} RAG/MetaRAG bubbles`
      );

      ragBubbles.forEach((bubble, index) => {
        const existingSourcesDiv = bubble.querySelector(".source-references");
        const hasExistingSources = existingSourcesDiv !== null;

        console.log(
          `🎯 [maintainSourcesAcrossRerender] Bubble ${index + 1}: ${
            hasExistingSources
              ? "Already has sources ✅"
              : "Missing sources - attempting to restore ⚠️"
          }`
        );

        if (!hasExistingSources && window.aiConfig?.showSources) {
          // Attempt to restore sources for this bubble
          const aiType = bubble.classList.contains("chatgpt-bubble-rag")
            ? "RAG"
            : "MetaRAG";

          console.log(
            `🔧 [maintainSourcesAcrossRerender] Restoring sources for ${aiType} bubble ${
              index + 1
            }`
          );

          // Try to get sources from various fallback strategies
          this.trySourceFallbacks(bubble, aiType);
        }
      });
    } catch (error) {
      console.error(
        "❌ [maintainSourcesAcrossRerender] Error in source maintenance:",
        error
      );
    }
  }

  // Loading bubble management methods
  addLoadingMessageGroup(messageGroup, startIndex = 0, aiMode) {
    const chatMessages = document.getElementById("chatgpt-messages");
    if (!chatMessages) return null;

    const groupDiv = document.createElement("div");
    groupDiv.className = "message-group assistant-group loading";
    groupDiv.style.padding = "12px 0";
    groupDiv.style.width = "100%";

    // Create loading bubble
    this.addLoadingBubbleToContainer("assistant", "", aiMode, groupDiv);

    chatMessages.appendChild(groupDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return groupDiv;
  }

  addLoadingBubbleToContainer(
    role,
    content,
    aiType,
    container,
    messageIndex = null
  ) {
    const bubbleDiv = document.createElement("div");
    bubbleDiv.className = `chatgpt-bubble loading chatgpt-bubble-${aiType.toLowerCase()}`;

    const avatarDiv = document.createElement("div");
    avatarDiv.className = "chatgpt-avatar";
    if (aiType === "RAG") {
      avatarDiv.textContent = "📚";
    } else if (aiType === "Gemini") {
      avatarDiv.textContent = "🔮";
    } else if (aiType === "Meta") {
      avatarDiv.textContent = "🤖";
    } else if (aiType === "MetaRAG") {
      avatarDiv.textContent = "🔍";
    } else {
      avatarDiv.textContent = "🤖";
    }

    const contentDiv = document.createElement("div");
    contentDiv.className = "chatgpt-bubble-content";

    let title = "";
    if (aiType === "RAG") {
      title = '<div class="msg-title-rag">RAG</div>';
    } else if (aiType === "Gemini") {
      title = '<div class="msg-title-gemini">Gemini</div>';
    } else if (aiType === "Meta") {
      title = '<div class="msg-title-meta">Meta</div>';
    } else if (aiType === "MetaRAG") {
      title = '<div class="msg-title-MetaRAG">MetaRAG</div>';
    }

    // Create loading animation
    contentDiv.innerHTML = `
      ${title}
      <div class="bot-response">
        <div class="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    `;

    bubbleDiv.appendChild(avatarDiv);
    bubbleDiv.appendChild(contentDiv);
    container.appendChild(bubbleDiv);

    return bubbleDiv;
  }

  replaceLoadingBubbleWithResponse(
    loadingGroup,
    content,
    aiType,
    sources = []
  ) {
    if (!loadingGroup) return;

    // Find the loading bubble within the group
    const loadingBubble = loadingGroup.querySelector(".chatgpt-bubble.loading");
    if (!loadingBubble) return;

    // Remove loading class and update content
    loadingBubble.classList.remove("loading");

    const contentDiv = loadingBubble.querySelector(".chatgpt-bubble-content");
    if (contentDiv) {
      let title = "";
      if (aiType === "RAG") {
        title = '<div class="msg-title-rag">RAG</div>';
      } else if (aiType === "Gemini") {
        title = '<div class="msg-title-gemini">Gemini</div>';
      } else if (aiType === "Meta") {
        title = '<div class="msg-title-meta">Meta</div>';
      } else if (aiType === "MetaRAG") {
        title = '<div class="msg-title-MetaRAG">MetaRAG</div>';
      }

      const markdownContent =
        typeof marked !== "undefined"
          ? marked.parse(content)
          : this.escapeHtml(content);

      contentDiv.innerHTML =
        title + '<div class="bot-response">' + markdownContent + "</div>";

      // Highlight code if available
      if (typeof hljs !== "undefined") {
        setTimeout(() => {
          contentDiv.querySelectorAll("pre code").forEach((block) => {
            hljs.highlightElement(block);
          });
        }, 0);
      }

      // Add sources if available and sources are enabled
      if (
        sources &&
        sources.length > 0 &&
        window.aiConfig &&
        window.aiConfig.showSources &&
        (aiType === "RAG" || aiType === "MetaRAG")
      ) {
        this.addSourceReferences(loadingBubble, aiType, sources);
      }
    }

    // Remove loading class from group
    loadingGroup.classList.remove("loading");
  }

  replaceLoadingBubbleWithError(loadingGroup, aiType) {
    if (!loadingGroup) return;

    const loadingBubble = loadingGroup.querySelector(".chatgpt-bubble.loading");
    if (!loadingBubble) return;

    loadingBubble.classList.remove("loading");

    const contentDiv = loadingBubble.querySelector(".chatgpt-bubble-content");
    if (contentDiv) {
      let title = "";
      if (aiType === "RAG") {
        title = '<div class="msg-title-rag">RAG</div>';
      } else if (aiType === "Gemini") {
        title = '<div class="msg-title-gemini">Gemini</div>';
      } else if (aiType === "Meta") {
        title = '<div class="msg-title-meta">Meta</div>';
      } else if (aiType === "MetaRAG") {
        title = '<div class="msg-title-MetaRAG">MetaRAG</div>';
      }

      contentDiv.innerHTML =
        title +
        '<div class="bot-response error">Sorry, there was an error processing your request.</div>';
    }

    loadingGroup.classList.remove("loading");
  }

  // Utility functions for enhanced source preview
  formatSourceMetadata(metadata) {
    if (!metadata) return "";

    let metadataHtml = '<div class="source-metadata">';

    if (metadata.page) {
      metadataHtml += `<div><strong>Page:</strong> ${metadata.page}</div>`;
    }

    if (metadata.score) {
      metadataHtml += `<div><strong>Relevance:</strong> ${Math.round(
        metadata.score * 100
      )}%</div>`;
    }

    if (metadata.source) {
      const fileName = metadata.source.split(/[/\\]/).pop();
      metadataHtml += `<div><strong>File:</strong> ${fileName}</div>`;
    }

    metadataHtml += "</div>";
    return metadataHtml;
  }

  createTextPreviewContent(container, source) {
    container.innerHTML = `
      <div class="source-preview-section">
        <div><strong>Content:</strong></div>
        <div class="source-content">${this.escapeHtml(
          source.content || ""
        )}</div>
        ${
          source.info
            ? `<div class="mt-2"><strong>Info:</strong> ${this.escapeHtml(
                source.info
              )}</div>`
            : ""
        }
        ${source.metadata ? this.formatSourceMetadata(source.metadata) : ""}
      </div>
    `;
  }
  async openFileViewer(fileName) {
    try {
      // First get file metadata to determine how to display it
      const response = await fetch(`/api/files/preview/${fileName}`);
      if (!response.ok) {
        throw new Error("Failed to get file preview");
      }

      const fileInfo = await response.json();

      // Create a new window/tab for the file viewer
      if (fileInfo.is_pdf || fileInfo.will_convert_to_pdf) {
        // For PDFs or Word documents that will be converted to PDF, open in browser
        if (fileInfo.will_convert_to_pdf && fileInfo.is_word) {
          // Show brief notification for Word-to-PDF conversion
          console.log(`Converting Word document to PDF: ${fileName}`);
        }
        window.open(`/api/files/view/${fileName}`, "_blank");
      } else if (fileInfo.is_text) {
        // For text files, show in a modal
        this.showTextFileModal(fileName, fileInfo);
      } else if (fileInfo.is_word && !fileInfo.will_convert_to_pdf) {
        // For Word docs that can't be converted, fall back to download
        this.downloadFile(fileName);
        alert(
          "Word documents will be downloaded. Please open with Microsoft Word or a compatible application."
        );
      } else {
        // For other file types, try to open directly
        window.open(`/api/files/view/${fileName}`, "_blank");
      }
    } catch (error) {
      console.error("Error opening file viewer:", error);
      alert("Failed to open file: " + error.message);
    }
  }

  async showTextFileModal(fileName, fileInfo) {
    try {
      const response = await fetch(`/api/files/content-preview/${fileName}`);
      if (!response.ok) {
        throw new Error("Failed to get file content");
      }

      const contentData = await response.json();

      // Create a modal to show the text content
      const modal = document.createElement("div");
      modal.className = "source-modal";
      modal.onclick = (e) => {
        if (e.target === modal) {
          modal.remove();
        }
      };

      const modalContent = document.createElement("div");
      modalContent.className = "source-modal-content";
      modalContent.style.maxWidth = "80vw";
      modalContent.style.maxHeight = "80vh";

      modalContent.innerHTML = `
        <div class="source-modal-header">
          <h3>📄 ${fileName}</h3>
          <span class="source-modal-close" onclick="this.closest('.source-modal').remove()">&times;</span>
        </div>
        <div class="source-modal-body" style="overflow-y: auto; max-height: 70vh;">
          <pre style="white-space: pre-wrap; font-family: monospace; font-size: 14px;">${this.escapeHtml(
            contentData.content || "No content available"
          )}</pre>
        </div>
      `;

      modal.appendChild(modalContent);
      document.body.appendChild(modal);
    } catch (error) {
      console.error("Error showing text file modal:", error);
      alert("Failed to show file content: " + error.message);
    }
  }
  downloadFile(fileName) {
    try {
      // Create a temporary link element to trigger download
      const link = document.createElement("a");
      link.href = `/api/files/view/${fileName}?download=true`;
      link.download = fileName;
      link.style.display = "none";

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error("Error downloading file:", error);
      alert("Failed to download file: " + error.message);
    }
  }

  // Enhanced source visibility management
  showSourcesForExistingMessages() {
    console.log(
      "🔍 [showSourcesForExistingMessages] Showing sources for existing RAG/MetaRAG messages"
    );

    const chatMessages = document.getElementById("chatgpt-messages");
    if (!chatMessages) return;

    // Find all RAG and MetaRAG bubbles
    const ragBubbles = chatMessages.querySelectorAll(
      ".chatgpt-bubble-rag, .chatgpt-bubble-metarag"
    );

    ragBubbles.forEach((bubble, index) => {
      const existingSourcesDiv = bubble.querySelector(".source-references");
      if (!existingSourcesDiv) {
        // Determine AI type
        const aiType = bubble.classList.contains("chatgpt-bubble-rag")
          ? "RAG"
          : "MetaRAG";

        console.log(
          `🔧 [showSourcesForExistingMessages] Adding sources to ${aiType} bubble ${
            index + 1
          }`
        );

        // Try to add sources using fallback strategies
        this.trySourceFallbacks(bubble, aiType);
      } else {
        // Sources already exist, just make sure they're visible
        existingSourcesDiv.style.display = "block";
      }
    });
  }
  hideAllSources() {
    console.log("🙈 [hideAllSources] Hiding all source displays");

    const chatMessages = document.getElementById("chatgpt-messages");
    if (!chatMessages) return;

    const sourcesContainers =
      chatMessages.querySelectorAll(".source-references");
    sourcesContainers.forEach((container) => {
      container.style.display = "none";
    });
  }
  // Enhanced Document Viewer Functions
  createDocumentViewer(fileName, previewData) {
    const fileType = previewData.file_type?.toLowerCase() || "unknown";

    // Handle Word documents that have been converted to PDF
    if (
      (fileType === "docx" || fileType === "doc") &&
      previewData.converted_to_pdf
    ) {
      return this.createConvertedWordViewer(fileName, previewData);
    }
    switch (fileType) {
      case "pdf":
        return this.createPdfViewer(fileName, previewData);
      case "docx":
      case "doc":
        return this.createWordViewer(fileName, previewData);
      case "txt":
      case "text":
        return this.createTextViewer(fileName, previewData);
      case "image":
      case "png":
      case "jpg":
      case "jpeg":
        return this.createImageViewer(fileName, previewData);
      default:
        return this.createGenericViewer(fileName, previewData);
    }
  }
  createPdfViewer(fileName, previewData) {
    const content =
      previewData.content || "No content available for this PDF page";
    const pdfUrl = `/api/files/view/${fileName}`;

    return `
      <div class="document-viewer pdf-viewer">
        <div class="pdf-preview-options">
          <div class="preview-tabs">
            <button class="preview-tab" onclick="this.parentElement.parentElement.querySelector('.pdf-text-preview').style.display='block'; this.parentElement.parentElement.querySelector('.pdf-embed-preview').style.display='none'; this.parentElement.querySelectorAll('.preview-tab').forEach(t => t.classList.remove('active')); this.classList.add('active');">
              📄 Text Extract
            </button>
            <button class="preview-tab active" onclick="this.parentElement.parentElement.querySelector('.pdf-text-preview').style.display='none'; this.parentElement.parentElement.querySelector('.pdf-embed-preview').style.display='block'; this.parentElement.querySelectorAll('.preview-tab').forEach(t => t.classList.remove('active')); this.classList.add('active');">
              🔍 Document Preview
            </button>
          </div>
        </div>
        
        <!-- Text Preview (Hidden by default) -->
        <div class="pdf-text-preview" style="display: none;">
          <div class="pdf-preview-notice">
            <span class="info-icon">📄</span>
            <span>PDF Text Content (Page ${previewData.page || 1})</span>
          </div>
          <div class="pdf-text-content">
            <pre class="text-formatted-content"><code>${this.escapeHtml(
              content
            )}</code></pre>
          </div>
        </div>
        
        <!-- PDF Document Preview (Default/Active) -->
        <div class="pdf-embed-preview">
          <div class="pdf-embed-container">
            <iframe 
              src="${pdfUrl}#page=${previewData.page || 1}" 
              width="100%" 
              height="600px"
              style="border: 1px solid #ddd; border-radius: 4px; background: white;">
              <p>PDF cannot be displayed in this browser. 
                 <a href="${pdfUrl}" target="_blank">Click here to open PDF in new tab</a>
              </p>
            </iframe>
          </div>
        </div>
        
        <!-- Action Buttons -->
        <div class="pdf-view-actions">
          <button class="btn btn-sm btn-primary" onclick="window.open('${pdfUrl}', '_blank')" title="Open PDF in new tab">
            🔍 Open in New Tab
          </button>
          <button class="btn btn-sm btn-secondary" onclick="window.chatManager.downloadFile('${fileName}')" title="Download PDF">
            💾 Download
          </button>
        </div>
      </div>
    `;
  }
  createConvertedWordViewer(fileName, previewData) {
    // Show the actual converted PDF document instead of text content
    const pdfUrl = `/api/files/view/${fileName}`;

    return `
      <div class="document-viewer converted-word-viewer">
        <div class="conversion-notice">
          <span class="conversion-icon">🔄</span>
          <span class="conversion-text">Word document converted to PDF for preview</span>
        </div>
        
        <div class="word-document-preview">
          <div class="pdf-embed-container">
            <iframe 
              src="${pdfUrl}" 
              width="100%" 
              height="600px"
              style="border: 1px solid #ddd; border-radius: 4px; background: white;">
              <p>Document cannot be displayed in this browser. 
                 <a href="${pdfUrl}" target="_blank">Click here to open document in new tab</a>
              </p>
            </iframe>
          </div>
        </div>
        
        <div class="word-view-actions">
          <button class="btn btn-sm btn-primary" onclick="window.open('${pdfUrl}', '_blank')" title="Open document in new tab">
            🔍 Open Full Document
          </button>
          <button class="btn btn-sm btn-secondary" onclick="window.chatManager.downloadFile('${fileName}')" title="Download original Word document">
            💾 Download Original
          </button>
        </div>
      </div>
    `;
  }
  createWordViewer(fileName, previewData) {
    const content = previewData.content || "No content available";

    // Check if conversion to PDF is available
    const conversionNotice = previewData.will_convert_to_pdf
      ? `<div class="conversion-available-notice">
        <span class="info-icon">ℹ️</span>
        <span>This Word document can be viewed as PDF for better formatting. 
          <button class="btn btn-sm btn-primary" onclick="window.chatManager.openFileViewer('${fileName}')">
            📄 View as PDF
          </button>
        </span>
      </div>`
      : "";

    return `
      <div class="document-viewer word-viewer">
        ${conversionNotice}
        <div class="word-document-content">
          ${this.formatWordContent(content)}
        </div>
      </div>
    `;
  }

  createTextViewer(fileName, previewData) {
    const content = previewData.content || "No content available";
    return `
      <div class="document-viewer text-viewer">
        <div class="text-content-container">
          <pre class="text-formatted-content"><code>${this.escapeHtml(
            content
          )}</code></pre>
        </div>
      </div>
    `;
  }

  createImageViewer(fileName, previewData) {
    const imageUrl = `/api/files/view/${fileName}`;
    return `
      <div class="document-viewer image-viewer">
        <div class="image-content-container">
          <img src="${imageUrl}" alt="${fileName}" style="max-width: 100%; height: auto; border-radius: 4px;" 
               onerror="this.parentElement.innerHTML='<p>Unable to load image</p>'">
        </div>
      </div>
    `;
  }

  createGenericViewer(fileName, previewData) {
    const content =
      previewData.content || "No preview available for this file type";
    return `
      <div class="document-viewer generic-viewer">
        <div class="generic-content-container">
          <div class="file-type-info">
            <h4>📄 ${fileName}</h4>
            <p>File Type: ${
              previewData.file_type?.toUpperCase() || "Unknown"
            }</p>
          </div>
          <div class="content-preview">
            <pre><code>${this.escapeHtml(content)}</code></pre>
          </div>
        </div>
      </div>
    `;
  }

  formatWordContent(content) {
    if (!content) return '<p class="text-muted">No content available</p>';

    // Clean up the content first
    let formatted = content
      .trim()
      // Handle multiple line breaks
      .replace(/\n{3,}/g, "\n\n")
      // Convert paragraphs
      .replace(/\n\n/g, '</p><p class="doc-paragraph">')
      // Convert single line breaks to <br> only within paragraphs
      .replace(/\n/g, "<br>")
      // Handle common formatting patterns
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      // Handle headers (simple detection)
      .replace(/^([A-Z][A-Z\s]{5,})/gm, '<h3 class="doc-heading">$1</h3>')
      // Handle bullet points
      .replace(/^[\s]*[-•]\s*(.+)/gm, '<div class="doc-bullet">$1</div>')
      // Handle numbered lists
      .replace(/^[\s]*\d+\.\s*(.+)/gm, '<div class="doc-numbered">$1</div>')
      // Clean up extra breaks
      .replace(/<br><\/p>/g, "</p>")
      .replace(/<p class="doc-paragraph"><br>/g, '<p class="doc-paragraph">');

    // Wrap in paragraphs if not already wrapped
    if (
      !formatted.startsWith("<p") &&
      !formatted.startsWith("<h") &&
      !formatted.startsWith("<div")
    ) {
      formatted = `<p class="doc-paragraph">${formatted}</p>`;
    }

    return formatted;
  }

  getFileTypeIcon(fileType) {
    switch (fileType?.toLowerCase()) {
      case "pdf":
        return "📕";
      case "docx":
      case "doc":
        return "📘";
      case "txt":
      case "text":
        return "📄";
      case "image":
      case "png":
      case "jpg":
      case "jpeg":
        return "🖼️";
      default:
        return "📄";
    }
  }

  getDocumentInfo(previewData) {
    const info = [];

    if (previewData.page && previewData.total_pages) {
      info.push(`Page ${previewData.page} of ${previewData.total_pages}`);
    } else if (previewData.total_pages) {
      info.push(`${previewData.total_pages} pages`);
    }

    if (previewData.file_size) {
      info.push(`${this.formatFileSize(previewData.file_size)}`);
    }

    return info.join(" | ") || "Single page document";
  }

  formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }
}
