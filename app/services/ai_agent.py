import json
import os
from typing import Optional

from app.config import settings


def _get_claude_client():
    """Create and return an Anthropic client if the API key is configured.

    Returns None if the key is not set or the library is unavailable.
    """
    if not settings.CLAUDE_API_KEY:
        return None
    try:
        from anthropic import Anthropic
        return Anthropic(api_key=settings.CLAUDE_API_KEY)
    except ImportError:
        print("anthropic package not installed; falling back to deterministic logic")
        return None


def _call_claude(prompt: str, max_tokens: int = 1024) -> Optional[dict]:
    """Send a prompt to the Claude API and parse the JSON response.

    Returns the parsed dict, or None on any failure.
    """
    client = _get_claude_client()
    if client is None:
        return None

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(response.content[0].text)
    except Exception as e:
        print(f"Claude API error: {e}")
        return None


def ai_calculate_charges(
    shipment_data: dict,
    rate_cards: list,
    surcharges: list,
) -> Optional[dict]:
    """Use Claude to select the best rate card and calculate charges.

    If CLAUDE_API_KEY is not configured or the call fails, returns None so that
    the caller can fall back to deterministic calculation.
    """
    if not settings.CLAUDE_API_KEY:
        return None

    prompt = (
        "You are a freight billing expert. Given the following shipment data, "
        "available rate cards, and surcharges, select the best matching rate card "
        "and calculate the total charges.\n\n"
        "Return your answer as a JSON object with keys:\n"
        '  "selected_rate_card_id": int,\n'
        '  "line_items": [\n'
        '    {"charge_code": str, "description": str, "quantity": float, '
        '"unit_price": float, "line_total": float}\n'
        "  ],\n"
        '  "subtotal": float,\n'
        '  "reasoning": str\n\n'
        f"Shipment:\n{json.dumps(shipment_data, indent=2, default=str)}\n\n"
        f"Rate Cards:\n{json.dumps(rate_cards, indent=2, default=str)}\n\n"
        f"Surcharges:\n{json.dumps(surcharges, indent=2, default=str)}\n\n"
        "Respond ONLY with valid JSON, no additional text."
    )

    return _call_claude(prompt)


def ai_draft_email(context: dict) -> Optional[dict]:
    """Use Claude to draft a professional freight invoice email.

    If CLAUDE_API_KEY is not configured or the call fails, returns None so that
    the caller can fall back to the template-based email.

    Args:
        context: Dict containing invoice, client, and shipment details.

    Returns:
        Dict with 'subject' and 'body' keys, or None.
    """
    if not settings.CLAUDE_API_KEY:
        return None

    prompt = (
        "You are a professional billing assistant for a freight forwarding company "
        f"called {settings.COMPANY_NAME}. Draft a professional invoice email.\n\n"
        "Return your answer as a JSON object with keys:\n"
        '  "subject": str,\n'
        '  "body": str\n\n'
        f"Context:\n{json.dumps(context, indent=2, default=str)}\n\n"
        "The email should be professional, clear, and include payment instructions.\n"
        "Payment is by wire transfer to Bank of America, Account: XXXX-XXXX-1234.\n"
        "Respond ONLY with valid JSON, no additional text."
    )

    return _call_claude(prompt)


def ai_check_anomalies(invoices_data: list) -> list:
    """Review a set of invoices for anomalies.

    If CLAUDE_API_KEY is configured, uses Claude to identify unusual patterns.
    Otherwise, falls back to basic statistical checks (flags invoices where the
    total is more than 2x the average for the same route).

    Returns a list of dicts, each describing an anomaly:
        {"invoice_id": int, "invoice_number": str, "issue": str, "severity": str}
    """
    if settings.CLAUDE_API_KEY:
        prompt = (
            "You are a freight billing auditor. Review the following invoices for "
            "anomalies such as unusually high or low amounts, duplicate charges, "
            "or inconsistencies.\n\n"
            "Return your answer as a JSON array of objects with keys:\n"
            '  "invoice_id": int,\n'
            '  "invoice_number": str,\n'
            '  "issue": str,\n'
            '  "severity": str  (one of "low", "medium", "high")\n\n'
            f"Invoices:\n{json.dumps(invoices_data, indent=2, default=str)}\n\n"
            "If no anomalies are found, return an empty JSON array [].\n"
            "Respond ONLY with valid JSON, no additional text."
        )

        result = _call_claude(prompt)
        if result is not None:
            # Result should be a list; handle if wrapped in an object
            if isinstance(result, list):
                return result
            if isinstance(result, dict) and "anomalies" in result:
                return result["anomalies"]
            return []

    # --- Deterministic fallback: flag invoices > 2x the average for the same route ---
    anomalies: list[dict] = []

    # Group invoices by route (origin_port_id, destination_port_id)
    route_totals: dict[tuple, list[dict]] = {}
    for inv in invoices_data:
        route_key = (
            inv.get("origin_port_id"),
            inv.get("destination_port_id"),
        )
        route_totals.setdefault(route_key, []).append(inv)

    for route_key, invoices in route_totals.items():
        if len(invoices) < 2:
            continue

        amounts = [inv.get("total_amount", 0) for inv in invoices]
        avg_amount = sum(amounts) / len(amounts)

        if avg_amount <= 0:
            continue

        for inv in invoices:
            total = inv.get("total_amount", 0)
            if total > 2 * avg_amount:
                anomalies.append({
                    "invoice_id": inv.get("invoice_id"),
                    "invoice_number": inv.get("invoice_number", ""),
                    "issue": (
                        f"Total amount ${total:,.2f} is more than 2x the route "
                        f"average of ${avg_amount:,.2f}"
                    ),
                    "severity": "high",
                })

    return anomalies
