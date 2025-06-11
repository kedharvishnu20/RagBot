# Frontend Documentation

## 📁 /src/static/

**Purpose**: Frontend assets and user interface  
**Location**: `/src/static/`  
**Type**: Frontend Layer

### Overview

Contains all frontend assets including HTML templates, CSS styles, and JavaScript modules that provide the user interface for the RAG AI application. Built with modern web technologies and responsive design.

---

## 📄 index.html

**Purpose**: Main application template  
**Location**: `/src/index.html`  
**Type**: HTML Template

### Overview

The primary HTML template that provides the complete user interface for the RAG AI application, featuring a modern chat interface with file upload capabilities and AI model selection.

### Key Sections

#### Document Head

```html
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>RAG AI Application</title>
  <!-- Bootstrap 5 CSS -->
  <link
    href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
    rel="stylesheet"
  />
  <!-- Font Awesome Icons -->
  <link
    rel="stylesheet"
    href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
  />
  <!-- Custom Styles -->
  <link rel="stylesheet" href="/static/css/styles.css" />
  <link rel="stylesheet" href="/static/bootstrap-custom.css" />
  <link rel="stylesheet" href="/static/source-references.css" />
</head>
```

#### Navigation Bar

```html
<nav class="navbar navbar-expand-lg navbar-dark bg-primary">
  <div class="container-fluid">
    <a class="navbar-brand" href="#">
      <i class="fas fa-robot me-2"></i>RAG AI Assistant
    </a>
    <div class="navbar-nav ms-auto">
      <button
        class="btn btn-outline-light"
        data-bs-toggle="modal"
        data-bs-target="#settingsModal"
      >
        <i class="fas fa-cog me-1"></i>Settings
      </button>
    </div>
  </div>
</nav>
```

#### Main Layout

- **Sidebar**: Session management and file upload
- **Chat Area**: Message display and input
- **Status Bar**: System status and indicators

#### Chat Interface

```html
<div class="chat-container">
  <div id="chatMessages" class="chat-messages"></div>
  <div class="chat-input-container">
    <div class="input-group">
      <input
        type="text"
        id="messageInput"
        class="form-control"
        placeholder="Ask a question about your documents..."
      />
      <button id="sendButton" class="btn btn-primary">
        <i class="fas fa-paper-plane"></i>
      </button>
    </div>
  </div>
</div>
```

#### File Upload Section

```html
<div class="upload-section">
  <h6><i class="fas fa-cloud-upload-alt me-2"></i>Upload Documents</h6>
  <div class="upload-area" id="uploadArea">
    <input type="file" id="fileInput" multiple accept=".pdf,.txt,.docx" />
    <div class="upload-text">
      <i class="fas fa-file-upload fa-2x mb-2"></i>
      <p>Drop files here or click to browse</p>
      <small>Supports PDF, TXT, DOCX (max 10MB each)</small>
    </div>
  </div>
</div>
```

#### AI Model Selection

```html
<div class="model-selection">
  <h6><i class="fas fa-brain me-2"></i>AI Model</h6>
  <select id="modelSelect" class="form-select">
    <option value="gemini-1.5-flash">Gemini 1.5 Flash (Fast)</option>
    <option value="gemini-1.5-pro">Gemini 1.5 Pro (Quality)</option>
    <option value="meta-ai">Meta AI</option>
  </select>
</div>
```

### Features

- **Responsive Design**: Mobile-friendly layout
- **Dark/Light Theme**: User preference support
- **Accessibility**: ARIA labels and keyboard navigation
- **Progressive Enhancement**: Works without JavaScript
- **Real-time Updates**: Dynamic content loading

---

## 📁 /src/static/css/

### 📄 styles.css

**Purpose**: Main application styles  
**Location**: `/src/static/css/styles.css`  
**Type**: CSS Stylesheet

### Overview

Primary stylesheet containing all custom styles for the application, including layout, components, animations, and responsive design.

#### Key Style Sections

##### Layout Styles

```css
.main-container {
  display: flex;
  height: calc(100vh - 76px);
  overflow: hidden;
}

.sidebar {
  width: 300px;
  background: #f8f9fa;
  border-right: 1px solid #dee2e6;
  overflow-y: auto;
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #ffffff;
}
```

##### Chat Styles

```css
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  scroll-behavior: smooth;
}

.message-group {
  margin-bottom: 20px;
  animation: fadeInUp 0.3s ease-out;
}

.message-bubble {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 18px;
  margin-bottom: 8px;
  word-wrap: break-word;
}

.user-message {
  background: #007bff;
  color: white;
  margin-left: auto;
}

.assistant-message {
  background: #f1f3f5;
  color: #333;
  border: 1px solid #e9ecef;
}
```

##### Component Styles

```css
.upload-area {
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  padding: 30px;
  text-align: center;
  transition: all 0.3s ease;
  cursor: pointer;
}

.upload-area:hover,
.upload-area.dragover {
  border-color: #007bff;
  background-color: #f8f9ff;
}

.source-citation {
  background: #e3f2fd;
  border-left: 4px solid #2196f3;
  padding: 8px 12px;
  margin: 8px 0;
  border-radius: 4px;
  font-size: 0.9em;
}
```

##### Responsive Design

```css
@media (max-width: 768px) {
  .main-container {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    height: auto;
    order: 2;
  }

  .chat-area {
    order: 1;
    height: 60vh;
  }
}
```

### 📄 bootstrap-custom.css

**Purpose**: Bootstrap customizations  
**Location**: `/src/static/bootstrap-custom.css`  
**Type**: CSS Override

### Overview

Custom Bootstrap theme overrides to match the application's design language and branding.

#### Theme Customizations

```css
:root {
  --bs-primary: #007bff;
  --bs-secondary: #6c757d;
  --bs-success: #28a745;
  --bs-info: #17a2b8;
  --bs-warning: #ffc107;
  --bs-danger: #dc3545;
  --bs-light: #f8f9fa;
  --bs-dark: #343a40;
}

.btn-primary {
  background-color: var(--bs-primary);
  border-color: var(--bs-primary);
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.3);
}

.card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: none;
  border-radius: 12px;
}
```

### 📄 source-references.css

**Purpose**: Source citation styling  
**Location**: `/src/static/source-references.css`  
**Type**: CSS Stylesheet

### Overview

Specialized styles for source citations, references, and document metadata display.

#### Source Citation Styles

```css
.sources-container {
  margin-top: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.source-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin: 4px 0;
  background: white;
  border-radius: 6px;
  border: 1px solid #dee2e6;
  transition: all 0.2s ease;
}

.source-item:hover {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.source-icon {
  color: #007bff;
  margin-right: 8px;
  font-size: 1.1em;
}

.source-text {
  flex: 1;
  font-size: 0.9em;
  line-height: 1.4;
}

.source-metadata {
  font-size: 0.8em;
  color: #6c757d;
  margin-top: 4px;
}
```

---

## 📁 /src/static/js/

### 📄 main.js

**Purpose**: Main application JavaScript  
**Location**: `/src/static/js/main.js`  
**Type**: JavaScript Module

### Overview

Primary JavaScript file that handles application initialization, event listeners, and core functionality coordination.

#### Key Functions

##### Application Initialization

```javascript
document.addEventListener("DOMContentLoaded", function () {
  initializeApplication();
  setupEventListeners();
  loadSettings();
  checkSystemStatus();
});

function initializeApplication() {
  // Initialize chat manager
  window.chatManager = new ChatManager();

  // Initialize file manager
  window.fileManager = new FileManager();

  // Initialize AI config
  window.aiConfig = new AIConfig();

  // Load existing sessions
  loadSessions();
}
```

##### Event Listeners Setup

```javascript
function setupEventListeners() {
  // Send message
  document.getElementById("sendButton").addEventListener("click", sendMessage);
  document
    .getElementById("messageInput")
    .addEventListener("keypress", handleKeyPress);

  // File upload
  document
    .getElementById("fileInput")
    .addEventListener("change", handleFileUpload);

  // Model selection
  document
    .getElementById("modelSelect")
    .addEventListener("change", updateModelSelection);

  // Settings modal
  document
    .getElementById("settingsModal")
    .addEventListener("show.bs.modal", loadSettings);

  // Sources toggle
  document
    .getElementById("showSourcesToggle")
    .addEventListener("change", toggleSources);
}
```

##### Message Sending

```javascript
async function sendMessage() {
  const messageInput = document.getElementById("messageInput");
  const message = messageInput.value.trim();

  if (!message) return;

  // Add user message to chat
  chatManager.addMessage("user", message);

  // Clear input
  messageInput.value = "";

  // Send to API
  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message,
        model: aiConfig.getSelectedModel(),
        use_rag: aiConfig.getUseRAG(),
        session_id: chatManager.getCurrentSessionId(),
      }),
    });

    const result = await response.json();
    handleChatResponse(result);
  } catch (error) {
    console.error("Error sending message:", error);
    chatManager.addMessage(
      "assistant",
      "Sorry, there was an error processing your message."
    );
  }
}
```

##### Chat Response Handling

```javascript
function handleChatResponse(result) {
  if (result.error) {
    chatManager.addMessage("assistant", `Error: ${result.error}`);
    return;
  }

  // Add assistant message with sources
  const messageGroup = chatManager.addMessageGroup(
    "assistant",
    result.response,
    result.message_sources
  );

  // Update session if needed
  if (
    result.session_id &&
    result.session_id !== chatManager.getCurrentSessionId()
  ) {
    chatManager.setCurrentSessionId(result.session_id);
    updateSessionsList();
  }

  // Show processing time
  if (result.processing_time) {
    console.log(
      `Response generated in ${result.processing_time.toFixed(2)}s using ${
        result.model_used
      }`
    );
  }
}
```

### 📄 chat-manager.js

**Purpose**: Chat interface management  
**Location**: `/src/static/js/chat-manager.js`  
**Type**: JavaScript Class

### Overview

Manages chat interface, message display, session handling, and source citations with dynamic updates and smooth animations.

#### Key Methods

##### ChatManager Class

```javascript
class ChatManager {
  constructor() {
    this.currentSessionId = null;
    this.messages = [];
    this.chatContainer = document.getElementById("chatMessages");
    this.sourceCache = new Map();
  }

  addMessage(role, content, sources = null) {
    const messageId = this.generateMessageId();
    const message = {
      id: messageId,
      role: role,
      content: content,
      timestamp: new Date(),
      sources: sources,
    };

    this.messages.push(message);
    this.renderMessage(message);
    this.scrollToBottom();

    return messageId;
  }

  addMessageGroup(role, content, immediateSources = null) {
    const messageGroup = this.createMessageGroup(role, content);
    this.chatContainer.appendChild(messageGroup);

    // Add sources if available
    if (immediateSources && immediateSources.length > 0) {
      this.addSourcesToGroup(messageGroup, immediateSources);
    }

    this.scrollToBottom();
    return messageGroup;
  }

  renderMessage(message) {
    const messageElement = this.createMessageElement(message);
    this.chatContainer.appendChild(messageElement);

    // Animate appearance
    requestAnimationFrame(() => {
      messageElement.classList.add("visible");
    });
  }

  createMessageElement(message) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message-group ${message.role}-group`;
    messageDiv.innerHTML = `
            <div class="message-bubble ${message.role}-message">
                <div class="message-content">${this.formatMessageContent(
                  message.content
                )}</div>
                <div class="message-timestamp">${this.formatTimestamp(
                  message.timestamp
                )}</div>
            </div>
        `;

    return messageDiv;
  }

  showSourcesForExistingMessages() {
    const assistantMessages =
      this.chatContainer.querySelectorAll(".assistant-group");
    assistantMessages.forEach((group) => {
      const sourcesContainer = group.querySelector(".sources-container");
      if (sourcesContainer) {
        sourcesContainer.style.display = "block";
      }
    });
  }

  hideAllSources() {
    const sourcesContainers =
      this.chatContainer.querySelectorAll(".sources-container");
    sourcesContainers.forEach((container) => {
      container.style.display = "none";
    });
  }

  scrollToBottom() {
    this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
  }
}
```

### 📄 file-manager.js

**Purpose**: File upload and management  
**Location**: `/src/static/js/file-manager.js`  
**Type**: JavaScript Class

### Overview

Handles file upload operations, drag-and-drop functionality, progress tracking, and file list management.

#### Key Methods

##### FileManager Class

```javascript
class FileManager {
  constructor() {
    this.uploadArea = document.getElementById("uploadArea");
    this.fileInput = document.getElementById("fileInput");
    this.setupDragAndDrop();
    this.supportedTypes = [
      "application/pdf",
      "text/plain",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];
  }

  setupDragAndDrop() {
    this.uploadArea.addEventListener(
      "dragover",
      this.handleDragOver.bind(this)
    );
    this.uploadArea.addEventListener(
      "dragleave",
      this.handleDragLeave.bind(this)
    );
    this.uploadArea.addEventListener("drop", this.handleDrop.bind(this));
    this.uploadArea.addEventListener("click", () => this.fileInput.click());
  }

  async uploadFiles(files) {
    const formData = new FormData();

    // Validate files
    const validFiles = Array.from(files).filter((file) =>
      this.validateFile(file)
    );

    if (validFiles.length === 0) {
      this.showError("No valid files selected");
      return;
    }

    // Add files to form data
    validFiles.forEach((file) => {
      formData.append("files", file);
    });

    // Show progress
    this.showUploadProgress();

    try {
      const response = await fetch("/files/upload", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      this.handleUploadResponse(result);
    } catch (error) {
      console.error("Upload error:", error);
      this.showError("Upload failed: " + error.message);
    } finally {
      this.hideUploadProgress();
    }
  }

  validateFile(file) {
    // Check file type
    if (!this.supportedTypes.includes(file.type)) {
      this.showError(`Unsupported file type: ${file.type}`);
      return false;
    }

    // Check file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      this.showError(`File too large: ${file.name}`);
      return false;
    }

    return true;
  }

  showUploadProgress() {
    const progressBar = document.createElement("div");
    progressBar.className = "upload-progress";
    progressBar.innerHTML = `
            <div class="progress">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     style="width: 100%"></div>
            </div>
            <small>Processing files...</small>
        `;
    this.uploadArea.appendChild(progressBar);
  }
}
```

### 📄 chat-manager.js (Enhanced Document Preview)

**Purpose**: Advanced chat management with document preview capabilities  
**Location**: `/src/static/js/chat-manager.js`  
**Type**: JavaScript Class

### Overview

Enhanced chat manager that provides seamless document preview functionality with tabbed interface, automatic DOCX-to-PDF conversion, and real-time document viewing.

#### Key Document Preview Methods

##### Document Preview Creation

```javascript
async createFilePreviewContent(container, source, fileName) {
  // Creates clean, minimal design with tabbed interface
  container.innerHTML = `
    <div class="clean-source-container">
      <!-- Clean Header with file info and actions -->
      <div class="source-header">
        <div class="source-file-info">
          <h4>📄 ${fileName}</h4>
          ${source.metadata?.page ? `<div class="page-badge">Page ${source.metadata.page}</div>` : ""}
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

      <!-- Document Preview Tab (Active by default) -->
      <div id="document-preview" class="clean-tab-pane active">
        <div class="clean-loading">
          <div class="loading-spinner"></div>
          <p>Loading document preview...</p>
        </div>
      </div>
    </div>
  `;

  // Load document preview asynchronously
  this.loadDocumentPreview(fileName, source.metadata?.page);
}
```

##### Enhanced Document Viewer

```javascript
createDocumentViewer(fileName, previewData) {
  const fileType = previewData.file_type?.toLowerCase() || "unknown";

  // Handle Word documents that have been converted to PDF
  if ((fileType === "docx" || fileType === "doc") && previewData.converted_to_pdf) {
    return this.createConvertedWordViewer(fileName, previewData);
  }

  switch (fileType) {
    case "pdf":
      return this.createPdfViewer(fileName, previewData);
    // ... other file types
  }
}

createPdfViewer(fileName, previewData) {
  const pdfUrl = `/api/files/view/${fileName}`;

  return `
    <div class="document-viewer pdf-viewer">
      <div class="pdf-preview-options">
        <div class="preview-tabs">
          <button class="preview-tab" onclick="this.parentElement.parentElement.querySelector('.pdf-text-preview').style.display='block'; this.parentElement.parentElement.querySelector('.pdf-embed-preview').style.display='none';">
            📄 Text Extract
          </button>
          <button class="preview-tab active" onclick="this.parentElement.parentElement.querySelector('.pdf-text-preview').style.display='none'; this.parentElement.parentElement.querySelector('.pdf-embed-preview').style.display='block';">
            🔍 Document Preview
          </button>
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
          </iframe>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="pdf-view-actions">
        <button class="btn btn-sm btn-primary" onclick="window.open('${pdfUrl}', '_blank')">
          🔍 Open in New Tab
        </button>
        <button class="btn btn-sm btn-secondary" onclick="window.chatManager.downloadFile('${fileName}')">
          💾 Download
        </button>
      </div>
    </div>
  `;
}
```

#### Document Preview Features

- **Seamless DOCX Viewing**: Automatic conversion to PDF for consistent experience
- **Tabbed Interface**: Switch between text extract and visual document preview
- **Real-time Loading**: Asynchronous document loading with progress indicators
- **Multiple File Support**: PDF, DOCX, DOC, TXT with appropriate viewers
- **Page Navigation**: Support for multi-page documents
- **Download Options**: Direct download with proper file serving

### 📄 ai-config.js

**Purpose**: AI model configuration management  
**Location**: `/src/static/js/ai-config.js`  
**Type**: JavaScript Class

### Overview

Manages AI model selection, configuration settings, and user preferences with persistence.

#### Key Methods

##### AIConfig Class

```javascript
class AIConfig {
  constructor() {
    this.settings = {
      selectedModel: "gemini-1.5-flash",
      useRAG: true,
      temperature: 0.1,
      maxTokens: 8192,
      showSources: true,
    };

    this.loadSettings();
    this.setupEventListeners();
  }

  getSelectedModel() {
    return this.settings.selectedModel;
  }

  setSelectedModel(model) {
    this.settings.selectedModel = model;
    this.saveSettings();
    this.updateUI();
  }

  getUseRAG() {
    return this.settings.useRAG;
  }

  setUseRAG(useRAG) {
    this.settings.useRAG = useRAG;
    this.saveSettings();
  }

  loadSettings() {
    const saved = localStorage.getItem("aiConfig");
    if (saved) {
      this.settings = { ...this.settings, ...JSON.parse(saved) };
    }
    this.updateUI();
  }

  saveSettings() {
    localStorage.setItem("aiConfig", JSON.stringify(this.settings));
  }

  updateUI() {
    const modelSelect = document.getElementById("modelSelect");
    if (modelSelect) {
      modelSelect.value = this.settings.selectedModel;
    }

    const ragToggle = document.getElementById("ragToggle");
    if (ragToggle) {
      ragToggle.checked = this.settings.useRAG;
    }

    const sourcesToggle = document.getElementById("showSourcesToggle");
    if (sourcesToggle) {
      sourcesToggle.checked = this.settings.showSources;
    }
  }
}
```

---

## 🎨 Frontend Features

### User Experience

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Updates**: Dynamic content loading without page refresh
- **Smooth Animations**: CSS transitions and animations
- **Accessibility**: ARIA labels, keyboard navigation, screen reader support
- **Progressive Enhancement**: Core functionality works without JavaScript

### Performance Optimization

- **Lazy Loading**: Load content as needed
- **Debounced Input**: Prevent excessive API calls
- **Efficient DOM Updates**: Minimize reflow and repaint
- **Caching**: Store settings and session data locally
- **Compression**: Minified assets for production

### Interactive Features

- **Drag & Drop**: File upload with visual feedback
- **Keyboard Shortcuts**: Quick actions and navigation
- **Context Menus**: Right-click actions
- **Modal Dialogs**: Settings and configuration
- **Toast Notifications**: Status updates and alerts

### Error Handling

- **User-Friendly Messages**: Clear error communication
- **Graceful Degradation**: Fallback functionality
- **Retry Mechanisms**: Automatic retry for failed requests
- **Offline Support**: Cache for offline functionality

This comprehensive frontend system provides an intuitive, responsive, and feature-rich user interface for the RAG AI application with modern web standards and best practices.
