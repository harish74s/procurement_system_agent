const API_URL = "";


// -----------------------------------------
// LOAD DASHBOARD STATISTICS
// -----------------------------------------

async function loadStats() {

    try {

        const response = await fetch(
            `${API_URL}/api/procurement/dashboard/stats`
        );

        const data = await response.json();

        document.getElementById("totalRequests").textContent =
            data.total_requests;

        document.getElementById("pendingRequests").textContent =
            data.pending_requests;

        document.getElementById("activePOs").textContent =
            data.active_purchase_orders;

        document.getElementById("openExceptions").textContent =
            data.open_exceptions;

    }

    catch (error) {

        console.error(
            "Failed to load dashboard statistics:",
            error
        );

    }
}


// -----------------------------------------
// LOAD PURCHASE REQUESTS
// -----------------------------------------

async function loadRequests() {

    try {

        const response = await fetch(
            `${API_URL}/api/procurement/requests`
        );

        const requests = await response.json();

        const table =
            document.getElementById("requestsTable");

        table.innerHTML = "";

        requests.forEach(request => {

            const row = document.createElement("tr");

            let statusClass = "pending";

            if (
                request.status === "SUPPLIER_SELECTION"
            ) {
                statusClass = "selection";
            }

            row.innerHTML = `

                <td>
                    <strong>
                        ${request.request_code}
                    </strong>
                </td>

                <td>
                    ${request.requested_by}
                </td>

                <td>
                    ${request.product}
                </td>

                <td>
                    ${request.quantity}
                </td>

                <td>
                    ₹${Number(request.budget).toLocaleString("en-IN")}
                </td>

                <td>

                    <span class="status ${statusClass}">
                        ${request.status.replaceAll("_", " ")}
                    </span>

                </td>
            `;

            table.appendChild(row);

        });

    }

    catch (error) {

        console.error(
            "Failed to load purchase requests:",
            error
        );

    }
}


// -----------------------------------------
// LOAD AI INSIGHTS
// -----------------------------------------

async function loadInsights() {

    const container =
        document.getElementById("aiInsights");

    try {

        const response = await fetch(
            `${API_URL}/api/procurement/inventory`
        );

        const inventory = await response.json();

        const lowStock =
            inventory.filter(
                item => item.stock_status === "LOW STOCK"
            );

        if (lowStock.length === 0) {

            container.innerHTML = `
                <div class="insight">
                    ✓ Inventory levels are currently healthy.
                </div>
            `;

            return;
        }

        container.innerHTML = "";

        lowStock.forEach(item => {

            const div =
                document.createElement("div");

            div.className = "insight";

            div.innerHTML = `
                ⚠ <strong>${item.product}</strong>
                has low inventory.
                Available: ${item.quantity_available}
                | Reorder level: ${item.reorder_level}
            `;

            container.appendChild(div);

        });

    }

    catch (error) {

        console.error(
            "Failed to load insights:",
            error
        );

    }
}


// -----------------------------------------
// INITIALIZE DASHBOARD
// -----------------------------------------

loadStats();
loadRequests();
loadInsights();