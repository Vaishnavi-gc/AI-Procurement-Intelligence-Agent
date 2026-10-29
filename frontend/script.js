const API_URL = "http://localhost:8000/api/query";

let conversationHistory = [];
function useExample(button) {

    const questionInput =
        document.getElementById("question");

    questionInput.value =
        button.innerText;

    questionInput.focus();
}


async function askQuestion() {

    const input =
        document.getElementById("question");

    const button =
        document.getElementById("askButton");

    const question =
        input.value.trim();


    if (!question) {
        return;
    }


    // Remove welcome screen

    const welcome =
        document.querySelector(".welcome");

    if (welcome) {
        welcome.remove();
    }


    // Add user message

    addUserMessage(question);


    // Clear input

    input.value = "";


    // Disable button

    button.disabled = true;

    button.innerText = "Thinking...";


    // Add loading message

    const loadingId =
        addAIMessage(
            "Analyzing your question..."
        );


    try {

        /*
         * Send question to FastAPI
         *
         * FastAPI expects:
         *
         * POST /api/query?question=...
         */

        const history = JSON.stringify(
           conversationHistory.slice(-5)
        );

        const response = await fetch(
         `${API_URL}?question=${encodeURIComponent(question)}&history=${encodeURIComponent(history)}`,
         {
           method: "POST"
         }
      );


        const data =
            await response.json();


        // Remove loading message

        removeMessage(loadingId);


        // Handle HTTP errors

        if (!response.ok) {

            addAIMessage(
                data.detail ||
                "Something went wrong."
            );

            return;
        }


        // Handle blocked SQL

        if (data.blocked) {

            addAIMessage(
                "⚠️ Query blocked: " +
                data.message
            );

            return;
        }


        // Display successful result

        displayResult(data);
        conversationHistory.push({
             question: question,
             answer: data.answer || "",
             results: JSON.stringify(
              data.rows || []
          )
    });

    } catch (error) {

        removeMessage(loadingId);


        addAIMessage(
            "Unable to connect to the AI server."
        );


        console.error(
            "API Error:",
            error
        );

    } finally {

        // Re-enable button

        button.disabled = false;

        button.innerText = "Ask";
    }
}


/* =========================================
   USER MESSAGE
========================================= */

function addUserMessage(text) {

    const chat =
        document.getElementById("chat");


    const message =
        document.createElement("div");


    message.className =
        "message user-message";


    message.innerHTML =
        `
        <strong>You</strong>
        <br>
        ${escapeHtml(text)}
        `;


    chat.appendChild(message);


    scrollToBottom();
}


/* =========================================
   AI MESSAGE
========================================= */

function addAIMessage(text) {

    const chat =
        document.getElementById("chat");


    const message =
        document.createElement("div");


    message.className =
        "message ai-message";


    message.innerHTML =
        `
        <strong>AI</strong>
        <br>
        ${escapeHtml(text)}
        `;


    const id =
        "message-" + Date.now();


    message.id = id;


    chat.appendChild(message);


    scrollToBottom();


    return id;
}


/* =========================================
   REMOVE MESSAGE
========================================= */

function removeMessage(id) {

    const message =
        document.getElementById(id);


    if (message) {

        message.remove();
    }
}


/* =========================================
   DISPLAY AI RESULT
========================================= */

function displayResult(data) {

    const chat =
        document.getElementById("chat");


    const message =
        document.createElement("div");


    message.className =
        "message ai-message";


    /*
     * AI answer
     */

    let html = `
        <strong>AI</strong>

        <p style="margin-top:10px;">
            ${formatAIAnswer(data.answer || "I couldn't generate an answer for this request. ")}
        </p>
    `;


    /*
     * Generated SQL
     */

    if (data.generated_sql) {

        html += `
            <details style="margin-top:15px;">

                <summary>
                    View generated SQL
                </summary>

                <div class="sql-box">
                    ${escapeHtml(data.generated_sql)}
                </div>

            </details>
        `;
    }


    /*
     * Database results
     */

    if (
        data.rows &&
        data.rows.length > 0
    ) {

        html += `
            <details style="margin-top:15px;">

                <summary>
                    View database results
                </summary>

                ${createTable(
                    data.columns,
                    data.rows
                )}

            </details>
        `;
    }


    /*
     * No results
     */

    if (
        data.rows &&
        data.rows.length === 0
    ) {

        html += `
            <p style="margin-top:15px; color:#6b7280;">
                No matching records were found.
            </p>
        `;
    }


    message.innerHTML =
        html;


    chat.appendChild(message);


    scrollToBottom();
}


/* =========================================
   CREATE RESULT TABLE
========================================= */

function createTable(
    columns,
    rows
) {

    let html =
        `
        <table class="result-table">

            <thead>

                <tr>
        `;


    /*
     * Table headers
     */

    columns.forEach(column => {

        html +=
            `
            <th>
                ${escapeHtml(String(column))}
            </th>
            `;
    });


    html +=
        `
                </tr>

            </thead>

            <tbody>
        `;


    /*
     * Table rows
     */

    rows.forEach(row => {

        html += "<tr>";


        columns.forEach(column => {

            let value =
                row[column];


            if (
                value === null ||
                value === undefined
            ) {

                value = "";
            }


            html +=
                `
                <td>
                    ${escapeHtml(String(value))}
                </td>
                `;
        });


        html += "</tr>";
    });


    html +=
        `
            </tbody>

        </table>
        `;


    return html;
}

function formatAIAnswer(text) {

    // First escape HTML for security
    let formatted = escapeHtml(text);

    // Convert **text** → <strong>text</strong>
    formatted = formatted.replace(
        /\*\*(.*?)\*\*/g,
        "<strong>$1</strong>"
    );

    // Convert bullet points
    formatted = formatted.replace(
        /^[-•]\s+(.*)$/gm,
        "<li>$1</li>"
    );

    // Wrap consecutive <li> elements
    formatted = formatted.replace(
        /(<li>.*?<\/li>(?:\s*<li>.*?<\/li>)*)/gs,
        "<ul>$1</ul>"
    );

    // Preserve line breaks
    formatted = formatted.replace(
        /\n/g,
        "<br>"
    );

    return formatted;
}
/* =========================================
   ESCAPE HTML
========================================= */

function escapeHtml(value) {

    return String(value)
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );
}


/* =========================================
   SCROLL CHAT TO BOTTOM
========================================= */

function scrollToBottom() {

    const chat =
        document.getElementById("chat");


    chat.scrollTop =
        chat.scrollHeight;
}


/* =========================================
   ENTER KEY SUPPORT
========================================= */

document
    .getElementById("question")
    .addEventListener(
        "keydown",
        function(event) {

            /*
             * Enter = send
             *
             * Shift + Enter = new line
             */

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                askQuestion();
            }
        }
    );