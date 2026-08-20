from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db_connection
from services.procurement_agent import analyze_purchase_request
router = APIRouter(
    prefix="/api/procurement",
    tags=["Procurement"]
)


# --------------------------------------------------
# 1. PURCHASE REQUESTS
# --------------------------------------------------

@router.get("/requests")
def get_purchase_requests():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            pr.id,
            pr.request_code,
            u.name AS requested_by,
            p.name AS product,
            p.category,
            pr.quantity,
            pr.required_date,
            pr.budget,
            pr.status,
            pr.created_at
        FROM purchase_requests pr
        JOIN users u ON pr.requested_by = u.id
        JOIN products p ON pr.product_id = p.id
        ORDER BY pr.created_at DESC
    """

    cursor.execute(query)
    requests = cursor.fetchall()

    cursor.close()
    connection.close()

    return requests


# --------------------------------------------------
# 2. SUPPLIERS
# --------------------------------------------------

@router.get("/suppliers")
def get_suppliers():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            id,
            supplier_code,
            name,
            contact_email,
            phone,
            rating,
            reliability_score,
            status
        FROM suppliers
        ORDER BY rating DESC
    """

    cursor.execute(query)
    suppliers = cursor.fetchall()

    cursor.close()
    connection.close()

    return suppliers


# --------------------------------------------------
# 3. INVENTORY
# --------------------------------------------------

@router.get("/inventory")
def get_inventory():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            i.id,
            p.product_code,
            p.name AS product,
            p.category,
            i.quantity_available,
            i.reorder_level,
            i.warehouse,
            CASE
                WHEN i.quantity_available <= i.reorder_level
                THEN 'LOW STOCK'
                ELSE 'AVAILABLE'
            END AS stock_status
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        ORDER BY i.quantity_available ASC
    """

    cursor.execute(query)
    inventory = cursor.fetchall()

    cursor.close()
    connection.close()

    return inventory


# --------------------------------------------------
# 4. SUPPLIER QUOTATIONS
# --------------------------------------------------

@router.get("/quotes")
def get_supplier_quotes():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            sq.id,
            sq.quote_code,
            pr.id AS purchase_request_id,
            s.name AS supplier,
            pr.request_code,
            p.name AS product,
            sq.quantity,
            sq.unit_price,
            sq.total_amount,
            sq.delivery_days,
            sq.warranty_months,
            sq.status
        FROM supplier_quotes sq
        JOIN suppliers s
            ON sq.supplier_id = s.id
        JOIN purchase_requests pr
            ON sq.purchase_request_id = pr.id
        JOIN products p
            ON pr.product_id = p.id
        ORDER BY sq.total_amount ASC
    """

    cursor.execute(query)
    quotes = cursor.fetchall()

    cursor.close()
    connection.close()

    return quotes


# --------------------------------------------------
# 5. DASHBOARD STATISTICS
# --------------------------------------------------

@router.get("/dashboard/stats")
def get_dashboard_stats():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    stats = {}

    # Total purchase requests
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM purchase_requests
    """)
    stats["total_requests"] = cursor.fetchone()["total"]

    # Pending requests
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM purchase_requests
        WHERE status IN ('PENDING', 'PENDING_APPROVAL')
    """)
    stats["pending_requests"] = cursor.fetchone()["total"]

    # Active purchase orders
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM purchase_orders
        WHERE status NOT IN ('CANCELLED', 'RECEIVED')
    """)
    stats["active_purchase_orders"] = cursor.fetchone()["total"]

    # Total invoices
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM invoices
    """)
    stats["total_invoices"] = cursor.fetchone()["total"]

    # Open exceptions
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM exceptions
        WHERE status IN ('OPEN', 'UNDER_REVIEW')
    """)
    stats["open_exceptions"] = cursor.fetchone()["total"]

    # Total procurement budget
    cursor.execute("""
        SELECT COALESCE(SUM(budget), 0) AS total
        FROM purchase_requests
    """)
    stats["total_budget"] = float(cursor.fetchone()["total"])

    cursor.close()
    connection.close()

    return stats

# --------------------------------------------------
# 6. GET PRODUCTS
# --------------------------------------------------

@router.get("/products")
def get_products():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            id,
            product_code,
            name,
            category,
            description,
            unit
        FROM products
        ORDER BY name
    """

    cursor.execute(query)
    products = cursor.fetchall()

    cursor.close()
    connection.close()

    return products


# --------------------------------------------------
# 7. CREATE PURCHASE REQUEST
# --------------------------------------------------

class PurchaseRequestCreate(BaseModel):

    requested_by: int
    product_id: int
    quantity: int
    required_date: str
    budget: float
    justification: str


@router.post("/requests")
def create_purchase_request(request: PurchaseRequestCreate):

    # Validate quantity
    if request.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )

    # Validate budget
    if request.budget <= 0:
        raise HTTPException(
            status_code=400,
            detail="Budget must be greater than zero"
        )

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # ------------------------------------------
        # Check requester
        # ------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE id = %s
            """,
            (request.requested_by,)
        )

        user = cursor.fetchone()

        if not user:

            raise HTTPException(
                status_code=404,
                detail="Requester not found"
            )


        # ------------------------------------------
        # Check product
        # ------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM products
            WHERE id = %s
            """,
            (request.product_id,)
        )

        product = cursor.fetchone()

        if not product:

            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )


        # ------------------------------------------
        # Generate request code
        # ------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM purchase_requests
            """
        )

        count = cursor.fetchone()["total"] + 1

        request_code = f"PR-{1000 + count}"


        # ------------------------------------------
        # Insert request
        # ------------------------------------------

        cursor.execute(
            """
            INSERT INTO purchase_requests
            (
                request_code,
                requested_by,
                product_id,
                quantity,
                required_date,
                budget,
                justification,
                status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'PENDING'
            )
            """,
            (
                request_code,
                request.requested_by,
                request.product_id,
                request.quantity,
                request.required_date,
                request.budget,
                request.justification
            )
        )

        connection.commit()

        new_id = cursor.lastrowid


        return {
            "message": "Purchase request created successfully",
            "request_id": new_id,
            "request_code": request_code,
            "status": "PENDING"
        }

    except HTTPException:
        connection.rollback()
        raise

    except Exception as e:
        connection.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to create purchase request: {str(e)}"
        )

    finally:

        cursor.close()
        connection.close()

@router.post("/requests/{request_id}/analyze")
def analyze_request(request_id: int):

    result = analyze_purchase_request(request_id)

    if "error" in result:
        raise HTTPException(
            status_code=404,
            detail=result["error"]
        )

    return result

@router.post("/requests/{request_id}/generate-quotes")
def generate_quotes(request_id: int):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get purchase request
    cursor.execute("""
        SELECT
            pr.id,
            pr.quantity,
            pr.product_id,
            p.name AS product
        FROM purchase_requests pr
        JOIN products p
            ON pr.product_id = p.id
        WHERE pr.id = %s
    """, (request_id,))

    request = cursor.fetchone()

    if not request:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Purchase request not found"
        )

    # Check whether quotes already exist
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM supplier_quotes
        WHERE purchase_request_id = %s
    """, (request_id,))

    existing = cursor.fetchone()["total"]

    if existing > 0:

        cursor.close()
        connection.close()

        return {
            "message": "Quotations already exist",
            "quotes_created": 0
        }

    # Get approved suppliers
    cursor.execute("""
        SELECT
            id,
            name,
            rating,
            reliability_score
        FROM suppliers
        WHERE status = 'APPROVED'
        ORDER BY reliability_score DESC
        LIMIT 3
    """)

    suppliers = cursor.fetchall()

    if len(suppliers) < 3:

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=400,
            detail="At least 3 approved suppliers are required"
        )

    # -----------------------------------------
    # Determine a realistic base price
    # -----------------------------------------

    cursor.execute("""
        SELECT unit_price
        FROM supplier_quotes sq
        JOIN purchase_requests pr
            ON sq.purchase_request_id = pr.id
        WHERE pr.product_id = %s
        ORDER BY sq.id DESC
        LIMIT 1
    """, (request["product_id"],))

    historical = cursor.fetchone()

    if historical:

        base_price = float(
            historical["unit_price"]
        )

    else:

        # Synthetic fallback prices for products
        product_name = request["product"].lower()

        if "laptop" in product_name:
            base_price = 72000

        elif "monitor" in product_name:
            base_price = 13000

        elif "server" in product_name:
            base_price = 180000

        else:
            base_price = 25000

    # -----------------------------------------
    # Synthetic supplier quotations
    # -----------------------------------------

    supplier_configs = [
        {
            "price_multiplier": 0.965,
            "delivery_days": 7,
            "warranty": 36
        },
        {
            "price_multiplier": 0.930,
            "delivery_days": 14,
            "warranty": 24
        },
        {
            "price_multiplier": 1.000,
            "delivery_days": 5,
            "warranty": 36
        }
    ]

    created_quotes = []

    for index, supplier in enumerate(suppliers):

        config = supplier_configs[index]

        unit_price = round(
            base_price *
            config["price_multiplier"],
            2
        )

        total_amount = round(
            unit_price *
            request["quantity"],
            2
        )

        quote_code = (
            f"QT-{request_id}{index + 1:02d}"
        )

        cursor.execute("""
            INSERT INTO supplier_quotes
            (
                purchase_request_id,
                supplier_id,
                quote_code,
                quantity,
                unit_price,
                total_amount,
                delivery_days,
                warranty_months,
                status
            )
            VALUES
            (
                %s, %s, %s, %s, %s,
                %s, %s, %s, 'RECEIVED'
            )
        """, (
            request_id,
            supplier["id"],
            quote_code,
            request["quantity"],
            unit_price,
            total_amount,
            config["delivery_days"],
            config["warranty"]
        ))

        created_quotes.append({
            "quote_code": quote_code,
            "supplier": supplier["name"],
            "unit_price": unit_price,
            "total_amount": total_amount,
            "delivery_days": config["delivery_days"],
            "warranty_months": config["warranty"]
        })

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Supplier quotations generated successfully",
        "request_id": request_id,
        "request_code": f"PR-{1000 + request_id}",
        "quotes_created": len(created_quotes),
        "quotes": created_quotes
    }

from datetime import date, timedelta


@router.post("/quotes/{quote_id}/create-po")
def create_purchase_order(quote_id: int):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # -----------------------------------------
    # Get quotation
    # -----------------------------------------

    cursor.execute("""
        SELECT
            sq.id,
            sq.purchase_request_id,
            sq.supplier_id,
            sq.quantity,
            sq.unit_price,
            sq.total_amount,
            sq.delivery_days,
            sq.status,
            pr.request_code,
            pr.required_date,
            s.name AS supplier
        FROM supplier_quotes sq
        JOIN purchase_requests pr
            ON sq.purchase_request_id = pr.id
        JOIN suppliers s
            ON sq.supplier_id = s.id
        WHERE sq.id = %s
    """, (quote_id,))

    quote = cursor.fetchone()

    if not quote:

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Quotation not found"
        )

    # -----------------------------------------
    # Check supplier approval
    # -----------------------------------------

    cursor.execute("""
        SELECT status
        FROM suppliers
        WHERE id = %s
    """, (quote["supplier_id"],))

    supplier = cursor.fetchone()

    if not supplier or supplier["status"] != "APPROVED":

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=400,
            detail="Purchase order can only be created for an approved supplier"
        )

    # -----------------------------------------
    # Check if PO already exists
    # -----------------------------------------

    cursor.execute("""
        SELECT
            id,
            po_number,
            status
        FROM purchase_orders
        WHERE purchase_request_id = %s
    """, (quote["purchase_request_id"],))

    existing_po = cursor.fetchone()

    if existing_po:

        cursor.close()
        connection.close()

        return {
            "message": "Purchase order already exists",
            "po_id": existing_po["id"],
            "po_number": existing_po["po_number"],
            "status": existing_po["status"]
        }

    # -----------------------------------------
    # Generate PO number
    # -----------------------------------------

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM purchase_orders
    """)

    count = cursor.fetchone()["total"] + 1

    po_number = f"PO-{1000 + count}"

    # -----------------------------------------
    # Dates
    # -----------------------------------------

    order_date = date.today()

    expected_delivery = (
        order_date +
        timedelta(days=int(quote["delivery_days"]))
    )

    # -----------------------------------------
    # Create PO
    # -----------------------------------------

    cursor.execute("""
        INSERT INTO purchase_orders
        (
            po_number,
            purchase_request_id,
            supplier_id,
            quantity,
            unit_price,
            total_amount,
            order_date,
            expected_delivery,
            status
        )
        VALUES
        (
            %s, %s, %s, %s, %s,
            %s, %s, %s, 'DRAFT'
        )
    """, (
        po_number,
        quote["purchase_request_id"],
        quote["supplier_id"],
        quote["quantity"],
        quote["unit_price"],
        quote["total_amount"],
        order_date,
        expected_delivery
    ))

    po_id = cursor.lastrowid

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Purchase order created successfully",
        "po_id": po_id,
        "po_number": po_number,
        "supplier": quote["supplier"],
        "total_amount": float(quote["total_amount"]),
        "expected_delivery": str(expected_delivery),
        "status": "DRAFT"
    }

@router.get("/purchase-orders")
def get_purchase_orders():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            po.id,
            po.po_number,
            po.purchase_request_id,
            pr.request_code,
            s.name AS supplier,
            po.quantity,
            po.unit_price,
            po.total_amount,
            po.order_date,
            po.expected_delivery,
            po.status
        FROM purchase_orders po

        JOIN purchase_requests pr
            ON po.purchase_request_id = pr.id

        JOIN suppliers s
            ON po.supplier_id = s.id

        ORDER BY po.id DESC
    """)

    orders = cursor.fetchall()

    cursor.close()
    connection.close()

    return orders