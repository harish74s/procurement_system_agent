import json
import requests

from database import get_db_connection


# ==================================================
# TOOL 1 — GET PURCHASE REQUEST
# ==================================================

def get_purchase_request(request_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            pr.id,
            pr.request_code,
            pr.quantity,
            pr.required_date,
            pr.budget,
            pr.justification,
            pr.status,
            p.name AS product,
            p.category,
            u.name AS requested_by,
            u.department
        FROM purchase_requests pr
        JOIN products p
            ON pr.product_id = p.id
        JOIN users u
            ON pr.requested_by = u.id
        WHERE pr.id = %s
    """, (request_id,))

    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result


# ==================================================
# TOOL 2 — CHECK INVENTORY
# ==================================================

def check_inventory(product_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            quantity_available,
            reorder_level,
            warehouse
        FROM inventory
        WHERE product_id = %s
    """, (product_id,))

    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result


# ==================================================
# TOOL 3 — GET SUPPLIER QUOTES
# ==================================================

def get_supplier_quotes(request_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            sq.quote_code,
            s.id AS supplier_id,
            s.name AS supplier,
            s.rating,
            s.reliability_score,
            s.status AS supplier_status,
            sq.unit_price,
            sq.quantity,
            sq.total_amount,
            sq.delivery_days,
            sq.warranty_months,
            sq.status AS quote_status
        FROM supplier_quotes sq
        JOIN suppliers s
            ON sq.supplier_id = s.id
        WHERE sq.purchase_request_id = %s
        ORDER BY sq.total_amount ASC
    """, (request_id,))

    results = cursor.fetchall()

    cursor.close()
    connection.close()

    return results


# ==================================================
# TOOL 4 — GET PROCUREMENT POLICIES
# ==================================================

def get_procurement_policies():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            policy_name,
            description,
            threshold_amount,
            approval_required
        FROM procurement_policies
        WHERE active = TRUE
    """)

    results = cursor.fetchall()

    cursor.close()
    connection.close()

    return results


# ==================================================
# BUILD PROCUREMENT CONTEXT
# ==================================================

def collect_procurement_context(request_id):

    request = get_purchase_request(request_id)

    if not request:
        return None

    # product_id is not selected above, so get it separately
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT product_id
        FROM purchase_requests
        WHERE id = %s
    """, (request_id,))

    product_data = cursor.fetchone()

    cursor.close()
    connection.close()

    product_id = product_data["product_id"]

    inventory = check_inventory(product_id)

    quotes = get_supplier_quotes(request_id)

    policies = get_procurement_policies()

    return {
        "purchase_request": request,
        "inventory": inventory,
        "supplier_quotes": quotes,
        "procurement_policies": policies
    }


# ==================================================
# SEND DATA TO LOCAL LLM
# ==================================================

def ask_local_llm(context):

    prompt = f"""
You are an Enterprise Procurement AI Agent.

Your job is to analyze a purchase request and recommend
the most appropriate procurement action.

You have access to:

1. Purchase request
2. Inventory information
3. Supplier quotations
4. Supplier ratings and reliability
5. Procurement policies

Do NOT simply select the cheapest supplier.

Consider:

- Required delivery date
- Supplier delivery time
- Total cost
- Budget
- Warranty
- Supplier reliability
- Supplier approval status
- Inventory availability
- Procurement policies

Return your answer as valid JSON with exactly these fields:

{{
    "decision": "BUY_FROM_SUPPLIER / USE_EXISTING_INVENTORY / NEED_APPROVAL / NEED_MORE_QUOTES",
    "recommended_supplier": "supplier name or null",
    "confidence": "HIGH / MEDIUM / LOW",
    "reasoning": "clear explanation",
    "risks": ["risk 1", "risk 2"],
    "next_action": "what procurement should do next"
}}

Procurement data:

{json.dumps(context, indent=2, default=str)}
"""

    # LM Studio OpenAI-compatible local endpoint
    url = "http://127.0.0.1:1234/v1/chat/completions"

    payload = {
        "model": "local-model",
        "messages": [
            {
                "role": "system",
                "content": "You are an enterprise procurement specialist."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2
    }

    response = requests.post(
        url,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    result = response.json()

    content = result["choices"][0]["message"]["content"]

    return content


# ==================================================
# MAIN AGENT
# ==================================================

def analyze_purchase_request(request_id):

    context = collect_procurement_context(request_id)

    if not context:
        return {
            "error": "Purchase request not found"
        }

    try:

        llm_response = ask_local_llm(context)

        # Remove markdown JSON fences if model adds them
        cleaned = llm_response.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        recommendation = json.loads(cleaned)

    except Exception as e:

        recommendation = {
            "decision": "NEED_HUMAN_REVIEW",
            "recommended_supplier": None,
            "confidence": "LOW",
            "reasoning": f"AI analysis could not be completed: {str(e)}",
            "risks": [
                "AI service unavailable"
            ],
            "next_action": "Procurement manager should review the request manually."
        }

    return {
        "request_id": request_id,
        "context": context,
        "recommendation": recommendation
    }