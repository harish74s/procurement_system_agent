async function loadPurchaseOrders() {

    try {

        const response = await fetch(
            "/api/procurement/purchase-orders"
        );

        const orders = await response.json();

        const table =
            document.getElementById("poTable");

        table.innerHTML = "";


        let totalValue = 0;

        let draftCount = 0;

        let activeCount = 0;


        orders.forEach(po => {

            totalValue +=
                Number(po.total_amount);


            if (po.status === "DRAFT") {
                draftCount++;
            }


            if (
                po.status === "APPROVED" ||
                po.status === "ORDERED"
            ) {
                activeCount++;
            }


            let statusClass = "pending";


            if (
                po.status === "APPROVED" ||
                po.status === "ORDERED"
            ) {

                statusClass =
                    "selection";

            }


            const row =
                document.createElement("tr");


            row.innerHTML = `

                <td>

                    <strong>
                        ${po.po_number}
                    </strong>

                </td>


                <td>
                    ${po.request_code}
                </td>


                <td>
                    ${po.supplier}
                </td>


                <td>
                    ${po.quantity}
                </td>


                <td>
                    ₹${Number(
                        po.total_amount
                    ).toLocaleString("en-IN")}
                </td>


                <td>
                    ${formatDate(po.order_date)}
                </td>


                <td>
                    ${formatDate(
                        po.expected_delivery
                    )}
                </td>


                <td>

                    <span
                        class="status ${statusClass}"
                    >
                        ${po.status.replaceAll("_", " ")}
                    </span>

                </td>

            `;


            table.appendChild(row);

        });


        document.getElementById(
            "totalPOs"
        ).textContent =
            orders.length;


        document.getElementById(
            "draftPOs"
        ).textContent =
            draftCount;


        document.getElementById(
            "activePOs"
        ).textContent =
            activeCount;


        document.getElementById(
            "totalPOValue"
        ).textContent =
            "₹" +
            totalValue.toLocaleString("en-IN");

    }

    catch (error) {

        console.error(
            "Failed to load purchase orders:",
            error
        );

    }

}


function formatDate(value) {

    if (!value) {
        return "-";
    }

    const date =
        new Date(value);

    return date.toLocaleDateString(
        "en-IN"
    );

}


loadPurchaseOrders();