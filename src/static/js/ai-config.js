// AI Configuration and API management
class AIConfigManager {
  constructor() {
    this.aiModes = ["RAG"];
    // Initialize with default value, but will be overridden by localStorage
    this.showSources = false;
    this.apiKeyIndex = 0;
    this.geminiModel = "gemini-1.5-flash";
    this.usageStats = {
      RAG: 0,
      Gemini: 0,
      Meta: 0,
      MetaRAG: 0,
    };

    // Load settings from localStorage
    this.loadSettings();
  }

  loadSettings() {
    try {
      // Load showSources setting
      const savedShowSources = localStorage.getItem("rag_show_sources");
      if (savedShowSources !== null) {
        this.showSources = savedShowSources === "true";
        console.log(
          `📁 [loadSettings] Loaded showSources: ${this.showSources}`
        );
      }

      // Load other settings
      const savedApiKeyIndex = localStorage.getItem("rag_api_key_index");
      if (savedApiKeyIndex !== null) {
        this.apiKeyIndex = parseInt(savedApiKeyIndex) || 0;
      }

      const savedGeminiModel = localStorage.getItem("rag_gemini_model");
      if (savedGeminiModel !== null) {
        this.geminiModel = savedGeminiModel;
      }

      console.log(`📁 [loadSettings] Loaded showSources: ${this.showSources}`);
    } catch (error) {
      console.error("Error loading settings from localStorage:", error);
    }
  }

  saveSettings() {
    try {
      localStorage.setItem("rag_show_sources", this.showSources.toString());
      localStorage.setItem("rag_api_key_index", this.apiKeyIndex.toString());
      localStorage.setItem("rag_gemini_model", this.geminiModel);
      console.log(`💾 [saveSettings] Saved showSources: ${this.showSources}`);
    } catch (error) {
      console.error("Error saving settings to localStorage:", error);
    }
  }

  updateUIFromSettings() {
    // Update show sources checkbox
    const showSourcesCheckbox = document.getElementById("show-sources");
    if (showSourcesCheckbox) {
      showSourcesCheckbox.checked = this.showSources;
      console.log(
        `🔘 [updateUIFromSettings] Set checkbox to: ${this.showSources}`
      );
    }

    // Update API key select
    const apiKeySelect = document.getElementById("api-key-select");
    if (apiKeySelect && apiKeySelect.options.length > 0) {
      apiKeySelect.value = this.apiKeyIndex;
    }

    // Update Gemini model select
    const geminiModelSelect = document.getElementById("gemini-model-select");
    if (geminiModelSelect) {
      geminiModelSelect.value = this.geminiModel;
    }
  }
  async initApiKeys() {
    const apiKeySelect = document.getElementById("api-key-select");
    if (!apiKeySelect) return;

    apiKeySelect.innerHTML = '<option value="">Loading...</option>';

    try {
      console.log("🔑 [initApiKeys] Fetching API keys...");
      const response = await fetch("/api_keys");
      if (!response.ok) throw new Error("Failed to fetch API keys");
      const data = await response.json();

      apiKeySelect.innerHTML = "";

      if (!data || data.length === 0) {
        apiKeySelect.innerHTML = '<option value="">No API keys found</option>';
        console.warn("⚠️ [initApiKeys] No API keys available");
        return;
      }

      console.log(`🔑 [initApiKeys] Received ${data.length} API keys:`, data);
      data.forEach((key) => {
        const option = document.createElement("option");
        option.value = key.index;
        // Backend returns 'key' field, not 'name'
        option.textContent = key.key || key.name || `API Key ${key.index + 1}`;
        apiKeySelect.appendChild(option);
        console.log(
          `🔑 [initApiKeys] Added option: ${option.textContent} (value: ${option.value})`
        );
      });

      // Use saved apiKeyIndex or default to the first option
      if (apiKeySelect.options.length > 0) {
        const savedIndex = null; // localStorage.getItem replaced - now handled server-side;
        if (savedIndex !== null) {
          this.apiKeyIndex = parseInt(savedIndex) || 0;
        } else {
          this.apiKeyIndex = parseInt(apiKeySelect.options[0].value);
        }
        apiKeySelect.value = this.apiKeyIndex;
        console.log(
          `🔑 [initApiKeys] Selected API key index: ${this.apiKeyIndex}`
        );
      }
    } catch (error) {
      console.error("❌ [initApiKeys] Error fetching API keys:", error);
      apiKeySelect.innerHTML = '<option value="">Error loading keys</option>';

      // Fallback: create dummy options for testing
      for (let i = 0; i < 5; i++) {
        const option = document.createElement("option");
        option.value = i;
        option.textContent = `API Key ${i + 1}`;
        apiKeySelect.appendChild(option);
      }
      this.apiKeyIndex = 0;
    }
  }

  updateAiModes() {
    const aiModeCheckboxes = document.querySelectorAll(".ai-mode-checkbox");
    this.aiModes = [];

    aiModeCheckboxes.forEach((checkbox) => {
      if (checkbox.checked && checkbox.value) {
        this.aiModes.push(checkbox.value);
      }
    });

    if (this.aiModes.length === 0) {
      const ragCheckbox = document.querySelector(
        '.ai-mode-checkbox[value="RAG"]'
      );
      if (ragCheckbox) {
        ragCheckbox.checked = true;
        this.aiModes = ["RAG"];
      }
    }
  }
  async updateUsageStats() {
    try {
      console.log("📊 [updateUsageStats] Fetching usage statistics...");
      const response = await fetch("/api/chat/usage");
      if (response.ok) {
        const stats = await response.json();
        console.log("📊 [updateUsageStats] Received stats:", stats);
        this.usageStats = { ...this.usageStats, ...stats };
        this.displayUsageStats();
      } else {
        console.warn(
          "⚠️ [updateUsageStats] Failed to fetch usage stats:",
          response.status
        ); // Try fallback endpoint
        const fallbackResponse = await fetch("/api/chat/usage");
        if (fallbackResponse.ok) {
          const fallbackStats = await fallbackResponse.json();
          console.log("📊 [updateUsageStats] Fallback stats:", fallbackStats);
          this.usageStats = { ...this.usageStats, ...fallbackStats };
          this.displayUsageStats();
        }
      }
    } catch (error) {
      console.error("❌ [updateUsageStats] Error fetching usage stats:", error);
    }
  }
  displayUsageStats() {
    Object.keys(this.usageStats).forEach((mode) => {
      // Handle special case for MetaRAG to match HTML id
      const elementId =
        mode === "MetaRAG" ? "MetaRAG-count" : `${mode.toLowerCase()}-count`;
      const element = document.getElementById(elementId);
      if (element) {
        element.textContent = this.usageStats[mode];
        console.log(
          `📊 [displayUsageStats] Updated ${mode}: ${this.usageStats[mode]}`
        );
      } else {
        console.warn(`⚠️ [displayUsageStats] Element not found: ${elementId}`);
      }
    });
  }

  getSelectedApiKey() {
    const apiKeySelect = document.getElementById("api-key-select");
    return apiKeySelect ? parseInt(apiKeySelect.value) || 0 : 0;
  }

  getSelectedModel() {
    const geminiModelSelect = document.getElementById("gemini-model-select");
    return geminiModelSelect ? geminiModelSelect.value : this.geminiModel;
  }

  getShowSources() {
    const showSourcesCheckbox = document.getElementById("show-sources");
    return showSourcesCheckbox ? showSourcesCheckbox.checked : false;
  }
}
