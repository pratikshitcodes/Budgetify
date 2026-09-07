// ─────────────────────────────────────────────────────────────────────────────
// Budgetify AI Chatbot
// ─────────────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {

    // ── Inject Chatbot UI ────────────────────────────────────────────────────

    const widget = document.createElement("div");

    widget.className = "chat-widget";

    widget.innerHTML = `
        <div class="chat-panel" id="chatPanel">

            <div class="chat-header">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <i class="ti ti-robot"></i>
                    Budgetify AI
                </div>

                <button class="chat-close" id="chatCloseBtn">
                    <i class="ti ti-x"></i>
                </button>
            </div>

            <div class="chat-body" id="chatBody">
                <div class="chat-msg ai">
                    Hello! I'm your Budgetify AI assistant.
                    How can I help you with your finances today?
                </div>
            </div>

            <div class="chat-footer">

                <input
                    type="text"
                    class="chat-input"
                    id="chatInput"
                    placeholder="Ask about your budget..."
                >

                <button class="chat-send" id="chatSendBtn">
                    <i class="ti ti-send"></i>
                </button>

            </div>

        </div>

        <button class="chat-toggle" id="chatToggleBtn">
            <i class="ti ti-message-chatbot"></i>
        </button>
    `;

    document.body.appendChild(widget);


    // ── DOM References ───────────────────────────────────────────────────────

    const toggleBtn = document.getElementById("chatToggleBtn");
    const closeBtn = document.getElementById("chatCloseBtn");
    const panel = document.getElementById("chatPanel");
    const input = document.getElementById("chatInput");
    const sendBtn = document.getElementById("chatSendBtn");
    const body = document.getElementById("chatBody");


    // ── Chat History ─────────────────────────────────────────────────────────

    let chatHistory = [];


    // ── Open / Close Chat ────────────────────────────────────────────────────

    toggleBtn.addEventListener("click", () => {
        panel.classList.toggle("open");
    });

    closeBtn.addEventListener("click", () => {
        panel.classList.remove("open");
    });


    // ── Lightweight Markdown Renderer ───────────────────────────────────────

    function renderMarkdown(text) {

        if (!text) return "";

        // Escape HTML first to prevent HTML injection
        let html = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Headers
        html = html.replace(/^### (.+)$/gm, "<h4>$1</h4>");
        html = html.replace(/^## (.+)$/gm, "<h3>$1</h3>");
        html = html.replace(/^# (.+)$/gm, "<h2>$1</h2>");

        // Bold + italic
        html = html.replace(
            /\*\*\*(.+?)\*\*\*/g,
            "<strong><em>$1</em></strong>"
        );

        // Bold
        html = html.replace(
            /\*\*(.+?)\*\*/g,
            "<strong>$1</strong>"
        );

        // Italic
        html = html.replace(
            /\*(.+?)\*/g,
            "<em>$1</em>"
        );

        // Inline code
        html = html.replace(
            /`([^`]+)`/g,
            "<code>$1</code>"
        );

        // Bullet lists
        html = html.replace(
            /^[*-] (.+)$/gm,
            "<li>$1</li>"
        );

        // Wrap consecutive <li> elements
        html = html.replace(
            /((?:<li>.*?<\/li>\s*)+)/gs,
            "<ul>$1</ul>"
        );

        // Numbered lists
        html = html.replace(
            /^\d+\. (.+)$/gm,
            "<li>$1</li>"
        );

        // New lines
        html = html.replace(
            /\n/g,
            "<br>"
        );

        return html;
    }


    // ── Add Message ──────────────────────────────────────────────────────────

    function appendMessage(role, content) {

        const div = document.createElement("div");

        div.className = `chat-msg ${role}`;

        div.innerHTML = renderMarkdown(content);

        body.appendChild(div);

        body.scrollTop = body.scrollHeight;

        return div;
    }


    // ── Report Download Buttons ──────────────────────────────────────────────

    function appendReports(reportMeta) {

        if (!reportMeta || !reportMeta.pdf_url) {
            return;
        }

        const div = document.createElement("div");

        div.className = "report-downloads";


        // PDF button
        const pdfBtn = document.createElement("a");

        pdfBtn.className = "pdf-btn";

        pdfBtn.href = "#";

        pdfBtn.innerHTML = `
            <i class="ti ti-file-type-pdf"></i>
            Download PDF
        `;

        pdfBtn.addEventListener("click", (e) => {

            e.preventDefault();

            downloadFile(
                reportMeta.pdf_url,
                "report.pdf"
            );

        });


        // CSV button
        const csvBtn = document.createElement("a");

        csvBtn.className = "csv-btn";

        csvBtn.href = "#";

        csvBtn.innerHTML = `
            <i class="ti ti-file-type-csv"></i>
            Download CSV
        `;

        csvBtn.addEventListener("click", (e) => {

            e.preventDefault();

            if (reportMeta.csv_url) {

                downloadFile(
                    reportMeta.csv_url,
                    "report.csv"
                );

            }

        });


        div.appendChild(pdfBtn);

        if (reportMeta.csv_url) {
            div.appendChild(csvBtn);
        }

        body.appendChild(div);

        body.scrollTop = body.scrollHeight;
    }


    // ── Download File ────────────────────────────────────────────────────────

    async function downloadFile(url, defaultName) {

        try {

            const response = await apiFetch(url);

            if (!response.ok) {
                throw new Error("Download failed");
            }

            const blob = await response.blob();

            const blobUrl = window.URL.createObjectURL(blob);

            const contentDisposition =
                response.headers.get("Content-Disposition");

            let filename = defaultName;

            if (
                contentDisposition &&
                contentDisposition.includes("filename=")
            ) {

                filename =
                    contentDisposition
                        .split("filename=")[1]
                        .replace(/"/g, "")
                        .trim();
            }


            const a = document.createElement("a");

            a.style.display = "none";

            a.href = blobUrl;

            a.download = filename;

            document.body.appendChild(a);

            a.click();

            a.remove();

            window.URL.revokeObjectURL(blobUrl);

        } catch (err) {

            console.error("File download error:", err);

            alert("Failed to download file.");

        }
    }


    // ── Send Message With SSE Streaming ──────────────────────────────────────

    async function sendMessage() {

        const text = input.value.trim();

        if (!text) {
            return;
        }


        // Display user's message
        appendMessage("user", text);

        input.value = "";

        input.disabled = true;

        sendBtn.disabled = true;


        // Thinking indicator
        const statusBubble =
            appendMessage("system", "Thinking…");


        // AI response bubble
        const aiBubble =
            document.createElement("div");

        aiBubble.className = "chat-msg ai";

        aiBubble.style.display = "none";

        body.appendChild(aiBubble);


        let rawText = "";

        let reportMeta = null;


        try {

            // Get JWT token
            const token =
                localStorage.getItem("access_token");


            if (!token) {

                statusBubble.remove();

                aiBubble.remove();

                appendMessage(
                    "system",
                    "Please log in again to use Budgetify AI."
                );

                return;
            }


            // API URL
            const apiBase =
                window.API_BASE_URL ||
                "http://localhost:8000";


            // Send request
            const response = await fetch(
                `${apiBase}/chat/stream`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },

                    body: JSON.stringify({
                        message: text,
                        history: chatHistory
                    })
                }
            );


            // Handle HTTP errors
            if (!response.ok) {

                const errorText =
                    await response.text();

                console.error(
                    "Chat API error:",
                    response.status,
                    errorText
                );

                statusBubble.remove();

                aiBubble.remove();

                appendMessage(
                    "system",
                    "Failed to get a response from the AI server."
                );

                return;
            }


            // Check streaming support
            if (!response.body) {

                throw new Error(
                    "Streaming is not supported by this response."
                );
            }


            // ── Read SSE Stream ──────────────────────────────────────────────

            const reader =
                response.body.getReader();

            const decoder =
                new TextDecoder();

            let buffer = "";


            while (true) {

                const {
                    done,
                    value
                } = await reader.read();


                if (done) {
                    break;
                }


                buffer += decoder.decode(
                    value,
                    {
                        stream: true
                    }
                );


                // Split SSE messages
                const lines =
                    buffer.split("\n");


                // Keep incomplete line
                buffer =
                    lines.pop() || "";


                for (const line of lines) {

                    const trimmedLine =
                        line.trim();


                    // Ignore empty lines
                    if (!trimmedLine) {
                        continue;
                    }


                    // Ignore non-data SSE lines
                    if (!trimmedLine.startsWith("data:")) {
                        continue;
                    }


                    const jsonString =
                        trimmedLine.slice(5).trim();


                    if (!jsonString) {
                        continue;
                    }


                    let event;


                    try {

                        event =
                            JSON.parse(jsonString);

                    } catch (error) {

                        console.warn(
                            "Invalid SSE JSON:",
                            jsonString
                        );

                        continue;
                    }


                    // ── Status Event ────────────────────────────────────────

                    if (event.type === "status") {

                        statusBubble.innerHTML =
                            renderMarkdown(
                                event.content || "Thinking…"
                            );

                    }


                    // ── Token Event ─────────────────────────────────────────

                    else if (event.type === "token") {

                        // First token received
                        if (
                            aiBubble.style.display === "none"
                        ) {

                            statusBubble.remove();

                            aiBubble.style.display = "";

                        }


                        rawText +=
                            event.content || "";


                        aiBubble.innerHTML =
                            renderMarkdown(rawText);


                        body.scrollTop =
                            body.scrollHeight;
                    }


                    // ── Report Event ────────────────────────────────────────

                    else if (event.type === "report") {

                        reportMeta =
                            event.content;

                    }


                    // ── Comparison Event ────────────────────────────────────

                    else if (event.type === "comparison") {

                        // Comparison information is already
                        // included in the streamed response.

                        console.log(
                            "Comparison:",
                            event.content
                        );
                    }


                    // ── Done Event ──────────────────────────────────────────

                    else if (event.type === "done") {

                        // Save conversation
                        chatHistory.push({
                            role: "user",
                            content: text
                        });

                        chatHistory.push({
                            role: "assistant",
                            content: rawText
                        });


                        // Show report buttons
                        if (reportMeta) {

                            appendReports(
                                reportMeta
                            );
                        }


                        // Refresh dashboard if
                        // expense/budget was modified
                        const lower =
                            rawText.toLowerCase();


                        if (
                            lower.includes("added") ||
                            lower.includes("deleted") ||
                            lower.includes("updated")
                        ) {

                            if (
                                typeof loadExpenses ===
                                "function"
                            ) {
                                loadExpenses();
                            }


                            if (
                                typeof loadDashboard ===
                                "function"
                            ) {
                                loadDashboard();
                            }
                        }
                    }
                }
            }


            if (
                aiBubble.style.display === "none"
            ) {

                statusBubble.remove();

                aiBubble.remove();

                appendMessage(
                    "system",
                    "No response received from AI."
                );
            }

        } catch (error) {

            console.error(
                "Chatbot error:",
                error
            );


            // Remove temporary bubbles
            statusBubble.remove();

            aiBubble.remove();


            appendMessage(
                "system",
                "Error connecting to AI server."
            );

        } finally {

            input.disabled = false;

            sendBtn.disabled = false;

            input.focus();
        }
    }


    // ── Event Listeners ──────────────────────────────────────────────────────

    sendBtn.addEventListener(
        "click",
        sendMessage
    );


    input.addEventListener(
        "keydown",
        (event) => {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                sendMessage();
            }
        }
    );

});