async function loadSuppliers() {

    try {

        const response = await fetch(
            "/api/procurement/suppliers"
        );

        const suppliers = await response.json();

        const table =
            document.getElementById("supplierTable");

        table.innerHTML = "";

        suppliers.forEach(supplier => {

            const row =
                document.createElement("tr");

            let statusClass = "pending";

            if (supplier.status === "APPROVED") {
                statusClass = "selection";
            }

            row.innerHTML = `

                <td>
                    <strong>
                        ${supplier.name}
                    </strong>
                </td>

                <td>
                    ${supplier.supplier_code}
                </td>

                <td>
                    ⭐ ${supplier.rating}
                </td>

                <td>
                    ${supplier.reliability_score}%
                </td>

                <td>
                    <span class="status ${statusClass}">
                        ${supplier.status}
                    </span>
                </td>

                <td>
                    ${supplier.contact_email}
                </td>

            `;

            table.appendChild(row);

        });


        // --------------------------------
        // SUMMARY
        // --------------------------------

        const total = suppliers.length;

        const approved =
            suppliers.filter(
                s => s.status === "APPROVED"
            ).length;

        const pending =
            suppliers.filter(
                s => s.status === "PENDING"
            ).length;

        const average =
            total > 0
                ? suppliers.reduce(
                    (sum, s) =>
                        sum + Number(s.rating),
                    0
                ) / total
                : 0;


        document.getElementById(
            "totalSuppliers"
        ).textContent = total;

        document.getElementById(
            "approvedSuppliers"
        ).textContent = approved;

        document.getElementById(
            "pendingSuppliers"
        ).textContent = pending;

        document.getElementById(
            "averageRating"
        ).textContent =
            average.toFixed(1) + " / 5";

    }

    catch (error) {

        console.error(
            "Failed to load suppliers:",
            error
        );

    }
}


loadSuppliers();