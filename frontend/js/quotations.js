let allQuotes = [];

const generateQuotesButton =
    document.getElementById(
        "generateQuotesButton"
    );

async function loadAllRequests() {

    try {

        const response = await fetch(
            "/api/procurement/requests"
        );

        const requests =
            await response.json();

        const selector =
            document.getElementById(
                "requestSelector"
            );

        selector.innerHTML = `
            <option value="">
                Select a purchase request
            </option>
        `;

        requests.forEach(request => {

            const option =
                document.createElement("option");

            option.value =
                request.request_code;

            option.textContent =
                `${request.request_code} — ${request.product}`;

            selector.appendChild(option);

        });

    }
    catch (error) {

        console.error(
            "Failed to load requests:",
            error
        );

    }
}
// ==========================================
// LOAD QUOTATIONS
// ==========================================
async function generateQuotes() {

    const requestCode =
        document.getElementById(
            "requestSelector"
        ).value;

    if (!requestCode) {

        alert(
            "Please select a purchase request first."
        );

        return;
    }

    const quote =
        allQuotes.find(
            q => q.request_code === requestCode
        );

    /*
        If quotations already exist,
        don't generate duplicates.
    */

    if (quote) {

        alert(
            `${requestCode} already has quotations.`
        );

        return;
    }

    /*
        Get request ID from the request code.
        Example:
        PR-1005 → 5
    */

    const requestId =
        Number(
            requestCode.replace("PR-", "")
        ) - 1000;

    generateQuotesButton.disabled = true;

    generateQuotesButton.textContent =
        "Generating...";

    try {

        const response = await fetch(
            `/api/procurement/requests/${requestId}/generate-quotes`,
            {
                method: "POST"
            }
        );

        const result =
            await response.json();

        if (!response.ok) {

            throw new Error(
                result.detail ||
                "Failed to generate quotations"
            );

        }

        alert(
            `✓ ${result.quotes_created} supplier quotations generated for ${requestCode}`
        );

        await loadQuotations();

        document.getElementById(
            "requestSelector"
        ).value = requestCode;

    }
    catch (error) {

        console.error(error);

        alert(
            `⚠ ${error.message}`
        );

    }
    finally {

        generateQuotesButton.disabled = false;

        generateQuotesButton.textContent =
            "📑 Generate Supplier Quotes";

    }
}
async function loadQuotations() {

    try {

        const response = await fetch(
            "/api/procurement/quotes"
        );

        allQuotes = await response.json();

        const table =
            document.getElementById("quoteTable");

        table.innerHTML = "";


        allQuotes.forEach(quote => {

            const row =
                document.createElement("tr");

            let statusClass = "pending";

            if (quote.status === "SELECTED") {
                statusClass = "selection";
            }


            row.innerHTML = `

                <td>
                    <strong>
                        ${quote.quote_code}
                    </strong>
                </td>

                <td>
                    ${quote.request_code}
                </td>

                <td>
                    ${quote.supplier}
                </td>

                <td>
                    ${quote.product}
                </td>

                <td>
                    ₹${Number(
                        quote.unit_price
                    ).toLocaleString("en-IN")}
                </td>

                <td>
                    ₹${Number(
                        quote.total_amount
                    ).toLocaleString("en-IN")}
                </td>

                <td>
                    ${quote.delivery_days} days
                </td>

                <td>
                    ${quote.warranty_months} months
                </td>

                <td>

                    <span class="status ${statusClass}">
                        ${quote.status.replaceAll("_", " ")}
                    </span>

                </td>

                <td>

                    <button
                        class="ai-small-button"
                        onclick="selectRequest('${quote.request_code}')"
                    >
                        🤖 Analyze
                    </button>

                </td>

            `;

            table.appendChild(row);

        });


        loadSummary();

        loadRequestSelector();

    }

    catch (error) {

        console.error(
            "Failed to load quotations:",
            error
        );

    }

}


// ==========================================
// SUMMARY
// ==========================================

function loadSummary() {

    const totalQuotes =
        allQuotes.length;


    const uniqueRequests =
        new Set(
            allQuotes.map(
                quote => quote.request_code
            )
        ).size;


    const lowest =
        allQuotes.length > 0
            ? Math.min(
                ...allQuotes.map(
                    quote =>
                        Number(
                            quote.total_amount
                        )
                )
            )
            : 0;


    const averageDelivery =
        allQuotes.length > 0
            ? allQuotes.reduce(
                (sum, quote) =>
                    sum +
                    Number(
                        quote.delivery_days
                    ),
                0
            ) / allQuotes.length
            : 0;


    document.getElementById(
        "totalQuotes"
    ).textContent = totalQuotes;


    document.getElementById(
        "requestsWithQuotes"
    ).textContent = uniqueRequests;


    document.getElementById(
        "lowestQuote"
    ).textContent =
        lowest > 0
            ? "₹" +
              lowest.toLocaleString("en-IN")
            : "-";


    document.getElementById(
        "averageDelivery"
    ).textContent =
        averageDelivery.toFixed(1) +
        " days";

}


// ==========================================
// REQUEST SELECTOR
// ==========================================

function loadRequestSelector() {

    const selector =
        document.getElementById(
            "requestSelector"
        );

    const requests =
        [...new Set(
            allQuotes.map(
                quote => quote.request_code
            )
        )];

    selector.innerHTML = `
        <option value="">
            Select a purchase request
        </option>
    `;

    requests.forEach(requestCode => {

        const option =
            document.createElement("option");

        option.value = requestCode;

        option.textContent =
            requestCode;

        selector.appendChild(option);

    });

}


// ==========================================
// SELECT REQUEST FROM TABLE
// ==========================================

function selectRequest(requestCode) {

    const selector =
        document.getElementById(
            "requestSelector"
        );

    selector.value = requestCode;

    analyzeRequest(requestCode);

}


// ==========================================
// ANALYZE REQUEST
// ==========================================

async function analyzeRequest(requestCode) {

    if (!requestCode) {

        alert(
            "Please select a purchase request."
        );

        return;

    }


    const quote =
        allQuotes.find(
            q => q.request_code === requestCode
        );


    if (!quote) {

        alert(
            "No quotation found for this request."
        );

        return;

    }


    const resultContainer =
        document.getElementById(
            "aiResult"
        );

    const button =
        document.getElementById(
            "analyzeButton"
        );


    button.disabled = true;

    button.textContent =
        "🤖 AI Analyzing...";


    resultContainer.innerHTML = `

        <div class="insight">

            <strong>
                AI is analyzing ${requestCode}...
            </strong>

            <p style="margin-top:8px;">
                Checking inventory, supplier quotes,
                budget, reliability and procurement policies.
            </p>

        </div>

    `;


    try {

        const response = await fetch(
            `/api/procurement/requests/${quoteRequestId(
                requestCode
            )}/analyze`,
            {
                method: "POST"
            }
        );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "AI analysis failed"
            );

        }


        displayAIResult(
            data.recommendation
        );


    }

    catch (error) {

        console.error(error);

        resultContainer.innerHTML = `

         <div class="ai-loading">

        <div class="ai-spinner"></div>

        <h3 style="margin-top:15px;">
            AI is analyzing the request...
        </h3>

        <p style="margin-top:8px;color:#6b7280;">
            Evaluating suppliers, pricing, delivery,
            warranty, inventory and procurement policies.
        </p>

        </div>

     `;

    }


    finally {

        button.disabled = false;

        button.textContent =
            "🤖 Analyze with AI";

    }

}


// ==========================================
// GET REQUEST ID
// ==========================================

function quoteRequestId(requestCode) {

    const quote =
        allQuotes.find(
            q => q.request_code === requestCode
        );

    if (!quote) {
        return null;
    }

    return quote.purchase_request_id;
}


// ==========================================
// DISPLAY AI RESULT
// ==========================================

function displayAIResult(recommendation) {

    const container =
        document.getElementById(
            "aiResult"
        );


    const risks =
        recommendation.risks || [];


    let risksHTML = "";

    if (risks.length === 0) {

        risksHTML =
            "<p>✓ No major risks identified.</p>";

    } else {

        risksHTML = `
            <ul>
                ${risks.map(
                    risk =>
                        `<li>⚠ ${risk}</li>`
                ).join("")}
            </ul>
        `;

    }


    container.innerHTML = `

        <div class="ai-recommendation">

            <div class="recommendation-header">

                <div>

                    <span class="recommendation-label">
                        RECOMMENDED SUPPLIER
                    </span>

                    <h2>
                        ${recommendation.recommended_supplier || "None"}
                    </h2>

                </div>

                <span class="confidence">
                    ${recommendation.confidence}
                </span>

            </div>


            <div class="recommendation-grid">

                <div>
                    <span>Decision</span>
                    <strong>
                        ${recommendation.decision.replaceAll("_", " ")}
                    </strong>
                </div>


                <div>
                    <span>Next Action</span>
                    <strong>
                        ${recommendation.next_action}
                    </strong>
                </div>

            </div>


            <div class="recommendation-section">

                <h3>AI Reasoning</h3>

                <p>
                    ${recommendation.reasoning}
                </p>

            </div>


            <div class="recommendation-section">

                <h3>Risks</h3>

                ${risksHTML}

            </div>
            <div class="po-action">

    <button
        class="po-button"
        onclick="createPurchaseOrder()"
    >
        📦 Create Purchase Order
    </button>

</div>

        </div>

    `;

}


// ==========================================
// BUTTON
// ==========================================
generateQuotesButton.addEventListener(
    "click",
    generateQuotes
);
document
    .getElementById("analyzeButton")
    .addEventListener(
        "click",
        () => {

            const requestCode =
                document.getElementById(
                    "requestSelector"
                ).value;

            analyzeRequest(
                requestCode
            );

        }
    );
async function createPurchaseOrder() {

    const requestCode =
        document.getElementById(
            "requestSelector"
        ).value;

    if (!requestCode) {

        alert(
            "Please select a purchase request first."
        );

        return;
    }

    const quote =
        allQuotes.find(
            q => q.request_code === requestCode
        );

    if (!quote) {

        alert(
            "No quotation found for this request."
        );

        return;
    }

    try {

        const response = await fetch(
            `/api/procurement/quotes/${quote.id}/create-po`,
            {
                method: "POST"
            }
        );

        const result =
            await response.json();

        if (!response.ok) {

            throw new Error(
                result.detail ||
                "Failed to create purchase order"
            );

        }

        alert(
            `✓ ${result.po_number} created successfully`
        );

        console.log(
            "Purchase Order:",
            result
        );

    }

    catch (error) {

        console.error(error);

        alert(
            `⚠ ${error.message}`
        );

    }

}

// ==========================================
// INITIALIZE
// ==========================================

loadQuotations();
loadAllRequests();