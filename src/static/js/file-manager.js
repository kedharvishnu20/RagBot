class FileManager {
  constructor() {
    this.uploadedFiles = [];
    this.maxFileSize = 10 * 1024 * 1024; // 10MB limit
    this.allowedTypes = [
      "text/plain",
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "application/msword",
      "text/csv",
      "application/json",
    ];
  }

  /**
   * Upload files to the server
   * @param {FileList} files - Files to upload
   * @returns {Promise<Object>} Upload result
   */
  async uploadFiles(files) {
    try {
      if (!files || files.length === 0) {
        throw new Error("No files selected");
      }

      // Validate files
      for (let file of files) {
        this.validateFile(file);
      }

      const formData = new FormData();
      for (let file of files) {
        formData.append("files", file);
      }
      const response = await fetch("/api/files/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Upload failed");
      }

      const result = await response.json();

      // Add uploaded files to our tracking
      this.uploadedFiles.push(...result.files);

      return result;
    } catch (error) {
      console.error("File upload error:", error);
      throw error;
    }
  }

  /**
   * Validate a single file
   * @param {File} file - File to validate
   */
  validateFile(file) {
    // Check file size
    if (file.size > this.maxFileSize) {
      throw new Error(
        `File "${file.name}" is too large. Maximum size is ${
          this.maxFileSize / (1024 * 1024)
        }MB`
      );
    }

    // Check file type
    if (!this.allowedTypes.includes(file.type) && !this.isTextFile(file)) {
      throw new Error(
        `File type "${file.type}" is not supported for file "${file.name}"`
      );
    }
  }

  /**
   * Check if file is a text file based on extension
   * @param {File} file - File to check
   * @returns {boolean} True if text file
   */
  isTextFile(file) {
    const textExtensions = [
      ".txt",
      ".md",
      ".py",
      ".js",
      ".html",
      ".css",
      ".json",
      ".xml",
      ".csv",
    ];
    const fileName = file.name.toLowerCase();
    return textExtensions.some((ext) => fileName.endsWith(ext));
  }

  /**
   * Get list of uploaded files
   * @returns {Array} List of uploaded files
   */
  getUploadedFiles() {
    return this.uploadedFiles;
  }

  /**
   * Clear uploaded files list
   */
  clearUploadedFiles() {
    this.uploadedFiles = [];
  }

  /**
   * Delete a file from the server
   * @param {string} filename - Name of file to delete
   * @returns {Promise<Object>} Delete result
   */
  async deleteFile(filename) {
    try {
      const response = await fetch(
        `/api/files/delete/${encodeURIComponent(filename)}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Delete failed");
      }

      // Remove from our tracking
      this.uploadedFiles = this.uploadedFiles.filter(
        (file) => file.filename !== filename
      );

      return await response.json();
    } catch (error) {
      console.error("File delete error:", error);
      throw error;
    }
  }

  /**
   * Get file upload progress (placeholder for future enhancement)
   * @param {File} file - File being uploaded
   * @returns {Promise<number>} Progress percentage
   */
  async getUploadProgress(file) {
    // This could be enhanced with actual progress tracking
    return 100;
  }

  /**
   * Format file size for display
   * @param {number} bytes - File size in bytes
   * @returns {string} Formatted file size
   */
  formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes";

    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }

  /**
   * Rebuild the vector index from all uploaded files
   * @returns {Promise<Object>} Rebuild result
   */
  async rebuildIndex() {
    try {
      console.log("🔄 Starting vector index rebuild...");
      const response = await fetch("/api/files/rebuild_index", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Index rebuild failed");
      }

      const result = await response.json();
      console.log("✅ Vector index rebuild completed:", result);

      // Show success notification
      this.showNotification("Vector index rebuilt successfully!", "success");

      return result;
    } catch (error) {
      console.error("❌ Vector index rebuild error:", error);
      this.showNotification(`Index rebuild failed: ${error.message}`, "error");
      throw error;
    }
  }

  /**
   * Show a notification to the user
   * @param {string} message - Notification message
   * @param {string} type - Notification type (success, error, info)
   */
  showNotification(message, type = "info") {
    // Create notification element if it doesn't exist
    let notification = document.getElementById("file-notification");
    if (!notification) {
      notification = document.createElement("div");
      notification.id = "file-notification";
      notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 4px;
        color: white;
        font-weight: bold;
        z-index: 1000;
        max-width: 300px;
        word-wrap: break-word;
      `;
      document.body.appendChild(notification);
    }

    // Set notification style based on type
    const styles = {
      success: "background-color: #28a745;",
      error: "background-color: #dc3545;",
      info: "background-color: #17a2b8;",
    };

    notification.style.cssText += styles[type] || styles.info;
    notification.textContent = message;
    notification.style.display = "block";

    // Auto-hide notification after 3 seconds
    setTimeout(() => {
      if (notification) {
        notification.style.display = "none";
      }
    }, 3000);
  }

  /**
   * Clear the vector database
   * @returns {Promise<Object>} Clear result
   */
  async clearVectorDb() {
    try {
      console.log("🗑️ Starting vector database clear...");

      const confirmed = confirm(
        "Are you sure you want to clear the vector database? This will remove all indexed content."
      );
      if (!confirmed) {
        console.log("❌ Vector database clear cancelled by user");
        return;
      }
      const response = await fetch("/api/files/clear_vector_db", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Clear vector database failed");
      }

      const result = await response.json();
      console.log("✅ Vector database cleared successfully:", result);

      // Show success notification
      this.showNotification("Vector database cleared successfully!", "success"); // Clear uploaded files list since vector db is now empty
      this.clearUploadedFiles();

      return result;
    } catch (error) {
      console.error("❌ Vector database clear error:", error);
      this.showNotification(`Clear failed: ${error.message}`, "error");
      throw error;
    }
  }
  /**
   * Fetch list of uploaded files from server
   * @returns {Promise<Array>} List of files
   */
  async fetchFileList() {
    try {
      const response = await fetch("/api/files/uploaded", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch files: ${response.statusText}`);
      }

      const result = await response.json();
      return result.files || [];
    } catch (error) {
      console.error("❌ Failed to fetch file list:", error);
      throw error;
    }
  }

  /**
   * Get file extension from filename
   * @param {string} filename
   * @returns {string} File extension
   */
  getFileExtension(filename) {
    return filename.toLowerCase().split(".").pop() || "";
  }

  /**
   * Get file icon based on extension
   * @param {string} extension
   * @returns {string} Icon character
   */
  getFileIcon(extension) {
    const iconMap = {
      pdf: "📄",
      txt: "📝",
      doc: "📘",
      docx: "📘",
      jpg: "🖼️",
      jpeg: "🖼️",
      png: "🖼️",
      csv: "📊",
      json: "📋",
    };
    return iconMap[extension] || "📄";
  }

  /**
   * Format file size for display
   * @param {number} size Size in bytes
   * @returns {string} Formatted size
   */
  formatFileSize(size) {
    if (size < 1024) return size + " B";
    if (size < 1024 * 1024) return (size / 1024).toFixed(1) + " KB";
    return (size / (1024 * 1024)).toFixed(1) + " MB";
  }
  /**
   * Get file name from full path
   * @param {string} filePath
   * @returns {string} File name
   */
  getFileName(filePath) {
    return filePath.split(/[\\/]/).pop() || filePath;
  }
}

/**
 * File Browser Manager - handles the sidebar file browser functionality
 */
class FileBrowser {
  constructor(fileManager) {
    this.fileManager = fileManager;
    this.files = [];
    this.filteredFiles = [];
    this.selectedFile = null;

    this.initializeElements();
    this.bindEvents();
    this.loadFiles();
  }

  /**
   * Initialize DOM elements
   */
  initializeElements() {
    this.fileListContainer = document.getElementById("file-list");
    this.fileSearchInput = document.getElementById("file-search");

    if (!this.fileListContainer || !this.fileSearchInput) {
      console.error("File browser elements not found in DOM");
      return;
    }
  }

  /**
   * Bind event listeners
   */
  bindEvents() {
    if (this.fileSearchInput) {
      this.fileSearchInput.addEventListener("input", (e) => {
        this.filterFiles(e.target.value);
      });
    }
  }

  /**
   * Load files from server and populate the list
   */
  async loadFiles() {
    try {
      this.showLoading();
      this.files = await this.fileManager.fetchFileList();
      this.filteredFiles = [...this.files];
      this.renderFileList();
    } catch (error) {
      console.error("Failed to load files:", error);
      this.showError("Failed to load files");
    }
  }

  /**
   * Filter files based on search query
   * @param {string} query Search query
   */
  filterFiles(query) {
    if (!query.trim()) {
      this.filteredFiles = [...this.files];
    } else {
      const searchTerm = query.toLowerCase();
      this.filteredFiles = this.files.filter((filePath) => {
        const fileName = this.fileManager.getFileName(filePath);
        return fileName.toLowerCase().includes(searchTerm);
      });
    }
    this.renderFileList();
  }
  /**
   * Render the file list in the sidebar
   */
  renderFileList() {
    if (!this.fileListContainer) return;

    if (this.filteredFiles.length === 0) {
      this.showEmptyState();
      return;
    }

    const fileItemsHtml = this.filteredFiles
      .map((filePath) => {
        const fileName = this.fileManager.getFileName(filePath);
        const extension = this.fileManager.getFileExtension(fileName);
        const icon = this.fileManager.getFileIcon(extension);
        const isActive = this.selectedFile === filePath;

        return `
        <div class="file-item ${
          isActive ? "active" : ""
        }" data-file-path="${filePath}">
          <span class="file-icon ${extension}">${icon}</span>
          <span class="file-name" title="${fileName}">${fileName}</span>
          <span class="file-meta">.${extension}</span>
          <button class="file-delete-btn" data-file-path="${filePath}" title="Delete ${fileName}">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="3,6 5,6 21,6"></polyline>
              <path d="m19,6v14a2,2 0 0,1 -2,2H7a2,2 0 0,1 -2,-2V6m3,0V4a2,2 0 0,1 2,-2h4a2,2 0 0,1 2,2v2"></path>
              <line x1="10" y1="11" x2="10" y2="17"></line>
              <line x1="14" y1="11" x2="14" y2="17"></line>
            </svg>
          </button>
        </div>
      `;
      })
      .join("");

    this.fileListContainer.innerHTML = fileItemsHtml;
    this.bindFileItemEvents();
  }
  /**
   * Bind click events to file items
   */
  bindFileItemEvents() {
    const fileItems = this.fileListContainer.querySelectorAll(".file-item");
    fileItems.forEach((item) => {
      // File item click handler
      item.addEventListener("click", (e) => {
        // Don't trigger file selection if delete button was clicked
        if (e.target.closest(".file-delete-btn")) {
          return;
        }
        const filePath = e.currentTarget.dataset.filePath;
        this.selectFile(filePath);
      });
    });

    // Delete button click handlers
    const deleteButtons =
      this.fileListContainer.querySelectorAll(".file-delete-btn");
    deleteButtons.forEach((button) => {
      button.addEventListener("click", (e) => {
        e.stopPropagation(); // Prevent file selection
        const filePath = e.currentTarget.dataset.filePath;
        const fileName = this.fileManager.getFileName(filePath);
        this.deleteFile(filePath, fileName);
      });
    });
  }

  /**
   * Select a file and update UI
   * @param {string} filePath Path of the selected file
   */
  selectFile(filePath) {
    // Remove active class from all items
    const fileItems = this.fileListContainer.querySelectorAll(".file-item");
    fileItems.forEach((item) => item.classList.remove("active"));

    // Add active class to selected item
    const selectedItem = this.fileListContainer.querySelector(
      `[data-file-path="${filePath}"]`
    );
    if (selectedItem) {
      selectedItem.classList.add("active");
    }

    this.selectedFile = filePath;

    // Emit custom event for other components to listen to
    const event = new CustomEvent("fileSelected", {
      detail: { filePath, fileName: this.fileManager.getFileName(filePath) },
    });
    document.dispatchEvent(event);

    console.log("📁 File selected:", this.fileManager.getFileName(filePath));
  }

  /**
   * Show loading state
   */
  showLoading() {
    if (this.fileListContainer) {
      this.fileListContainer.innerHTML = `
        <div class="file-list-loading">
          <div class="typing-dots">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
          </div>
          Loading files...
        </div>
      `;
    }
  }

  /**
   * Show empty state
   */
  showEmptyState() {
    if (this.fileListContainer) {
      this.fileListContainer.innerHTML = `
        <div class="file-list-empty">
          No files found
        </div>
      `;
    }
  }

  /**
   * Show error state
   * @param {string} message Error message
   */
  showError(message) {
    if (this.fileListContainer) {
      this.fileListContainer.innerHTML = `
        <div class="file-list-empty" style="color: #ff6b6b;">
          ⚠️ ${message}
        </div>
      `;
    }
  }

  /**
   * Refresh the file list
   */
  async refresh() {
    await this.loadFiles();
  }
  /**
   * Clear selection
   */
  clearSelection() {
    this.selectedFile = null;
    const fileItems = this.fileListContainer.querySelectorAll(".file-item");
    fileItems.forEach((item) => item.classList.remove("active"));
  }

  /**
   * Delete a file with confirmation
   * @param {string} filePath Path of the file to delete
   * @param {string} fileName Name of the file to delete
   */
  async deleteFile(filePath, fileName) {
    // Show confirmation dialog
    const confirmed = confirm(
      `Are you sure you want to delete "${fileName}"?\n\nThis action cannot be undone.`
    );

    if (!confirmed) {
      return;
    }

    try {
      // Show loading state on the delete button
      const deleteButton = this.fileListContainer.querySelector(
        `[data-file-path="${filePath}"] .file-delete-btn`
      );
      if (deleteButton) {
        deleteButton.style.opacity = "0.5";
        deleteButton.style.pointerEvents = "none";
      }

      // Call delete API
      const response = await fetch(
        `/api/files/delete/${encodeURIComponent(fileName)}`,
        {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to delete file");
      }

      const result = await response.json();

      // Show success message
      this.showNotification(
        `✅ File "${fileName}" deleted successfully`,
        "success"
      );

      // Clear selection if deleted file was selected
      if (this.selectedFile === filePath) {
        this.clearSelection();
      }

      // Refresh file list
      await this.loadFiles();

      console.log("🗑️ File deleted successfully:", fileName);
    } catch (error) {
      console.error("❌ Failed to delete file:", error);
      this.showNotification(
        `❌ Failed to delete "${fileName}": ${error.message}`,
        "error"
      );

      // Restore delete button state
      const deleteButton = this.fileListContainer.querySelector(
        `[data-file-path="${filePath}"] .file-delete-btn`
      );
      if (deleteButton) {
        deleteButton.style.opacity = "";
        deleteButton.style.pointerEvents = "";
      }
    }
  }

  /**
   * Show notification message
   * @param {string} message Notification message
   * @param {string} type Notification type ('success', 'error', 'info')
   */
  showNotification(message, type = "info") {
    // Create notification element
    const notification = document.createElement("div");
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    // Style the notification
    Object.assign(notification.style, {
      position: "fixed",
      top: "20px",
      right: "20px",
      padding: "12px 16px",
      borderRadius: "6px",
      color: "white",
      fontWeight: "500",
      zIndex: "10000",
      maxWidth: "300px",
      fontSize: "14px",
      boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
      transform: "translateX(100%)",
      transition: "transform 0.3s ease-in-out",
    });

    // Set background color based on type
    const colors = {
      success: "#10b981",
      error: "#ef4444",
      info: "#3b82f6",
    };
    notification.style.backgroundColor = colors[type] || colors.info;

    // Add to DOM
    document.body.appendChild(notification);

    // Animate in
    setTimeout(() => {
      notification.style.transform = "translateX(0)";
    }, 100);

    // Remove after delay
    setTimeout(() => {
      notification.style.transform = "translateX(100%)";
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    }, 3000);
  }
}
