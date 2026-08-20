const form = document.getElementById("requestForm");
const productSelect = document.getElementById("product");
const requestTable = document.getElementById("requestTable");
const message = document.getElementById("requestMessage");


// -----------------------------------------
// LOAD PRODUCTS
// -----------------------------------------

async function loadProducts() {

    try {

        const response = await fetch(
            "/api/procurement/products"
        );

        const products = await response.json();

        productSelect.innerHTML = `
            <option value="">
                Select a product
            </option>
        `;

        products.forEach(product => {

            const option =
                document.createElement("option");

            option.value = product.id;

            option.textContent =
                `${product.name} (${product.category})`;

            productSelect.appendChild(option);

        });

    } catch (error) {

        console.error(
            "Failed to load products:",
            error
        );

        productSelect.innerHTML = `
            <option value="">
                Failed to load products
            </option>
        `;
    }
}


// -----------------------------------------
// LOAD REQUESTS
// -----------------------------------------

async function loadRequests() {

    try {

        const response = await fetch(
            "/api/procurement/requests"
        );

        const requests = await response.json();

        requestTable.innerHTML = "";

        requests.forEach(request => {

            const row =
                document.createElement("tr");

            let statusClass = "pending";

            if (
                request.status ===
                "SUPPLIER_SELECTION"
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
                    ₹${Number(
                        request.budget
                    ).toLocaleString("en-IN")}
                </td>

                <td>
                    <span class="status ${statusClass}">
                        ${request.status.replaceAll("_", " ")}
                    </span>
                </td>

            `;

            requestTable.appendChild(row);

        });

    } catch (error) {

        console.error(
            "Failed to load requests:",
            error
        );
    }
}


// -----------------------------------------
// CREATE REQUEST
// -----------------------------------------

form.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();

        message.textContent =
            "Creating purchase request...";

        message.className =
            "form-message";


        const requestData = {

            requested_by:
                Number(
                    document.getElementById(
                        "requester"
                    ).value
                ),

            product_id:
                Number(
                    productSelect.value
                ),

            quantity:
                Number(
                    document.getElementById(
                        "quantity"
                    ).value
                ),

            required_date:
                document.getElementById(
                    "requiredDate"
                ).value,

            budget:
                Number(
                    document.getElementById(
                        "budget"
                    ).value
                ),

            justification:
                document.getElementById(
                    "justification"
                ).value

        };


        try {

            const response = await fetch(
                "/api/procurement/requests",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            requestData
                        )
                }
            );


            const result =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    result.detail ||
                    "Failed to create request"
                );

            }


            message.textContent =
                `✓ ${result.request_code} created successfully.`;

            message.className =
                "form-message success";


            form.reset();

            await loadRequests();

        } catch (error) {

            message.textContent =
                `⚠ ${error.message}`;

            message.className =
                "form-message error";

        }

    }
);


// -----------------------------------------
// INITIALIZE
// -----------------------------------------

loadProducts();
loadRequests();