from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from datetime import date, timedelta
from typing import Optional

from app.models.shipment import Shipment
from app.models.invoice import Invoice
from app.models.invoice_line import InvoiceLine
from app.models.rate_card import RateCard
from app.models.surcharge import Surcharge
from app.models.client import Client
from app.models.port import Port


# Container types considered FCL
FCL_TYPES = {"20GP", "40GP", "40HC"}

# Minimum ocean freight threshold for LCL_MIN surcharge
LCL_MIN_THRESHOLD = 120.0


def get_next_invoice_number(db: Session) -> str:
    """Generate the next sequential invoice number in format INV-2026-XXXX."""
    max_invoice_number = (
        db.query(sql_func.max(Invoice.invoice_number))
        .filter(Invoice.invoice_number.like("INV-2026-%"))
        .scalar()
    )

    if max_invoice_number is None:
        return "INV-2026-0001"

    # Parse the sequence number from the last segment
    try:
        sequence = int(max_invoice_number.split("-")[-1])
    except (ValueError, IndexError):
        sequence = 0

    next_sequence = sequence + 1
    return f"INV-2026-{next_sequence:04d}"


def find_rate_card(
    db: Session,
    origin_port_id: int,
    dest_port_id: int,
    container_type: str,
) -> Optional[RateCard]:
    """Find the best matching active rate card for the given route and container type.

    First tries an exact origin+destination match. If none is found, falls back
    to a region-based match (any origin in the same region to the same destination).
    In either case the most recently effective rate card is returned.
    """
    # Exact origin + destination match
    exact_match = (
        db.query(RateCard)
        .filter(
            RateCard.origin_port_id == origin_port_id,
            RateCard.destination_port_id == dest_port_id,
            RateCard.container_type == container_type,
            RateCard.is_active == True,  # noqa: E712
        )
        .order_by(RateCard.effective_from.desc())
        .first()
    )

    if exact_match is not None:
        return exact_match

    # Region-based fallback: find the origin port's region, then look for any
    # rate card whose origin port is in the same region heading to the same dest.
    origin_port = db.query(Port).filter(Port.id == origin_port_id).first()
    if origin_port is None:
        return None

    region_ports = (
        db.query(Port.id)
        .filter(Port.region == origin_port.region)
        .all()
    )
    region_port_ids = [p.id for p in region_ports]

    region_match = (
        db.query(RateCard)
        .filter(
            RateCard.origin_port_id.in_(region_port_ids),
            RateCard.destination_port_id == dest_port_id,
            RateCard.container_type == container_type,
            RateCard.is_active == True,  # noqa: E712
        )
        .order_by(RateCard.effective_from.desc())
        .first()
    )

    if region_match is not None:
        return region_match

    # Further fallback: also relax the destination to same region
    dest_port = db.query(Port).filter(Port.id == dest_port_id).first()
    if dest_port is None:
        return None

    dest_region_ports = (
        db.query(Port.id)
        .filter(Port.region == dest_port.region)
        .all()
    )
    dest_region_port_ids = [p.id for p in dest_region_ports]

    broad_match = (
        db.query(RateCard)
        .filter(
            RateCard.origin_port_id.in_(region_port_ids),
            RateCard.destination_port_id.in_(dest_region_port_ids),
            RateCard.container_type == container_type,
            RateCard.is_active == True,  # noqa: E712
        )
        .order_by(RateCard.effective_from.desc())
        .first()
    )

    return broad_match


def get_applicable_surcharges(
    db: Session,
    origin_port_id: int,
    dest_port_id: int,
    container_type: str,
) -> list[Surcharge]:
    """Return all active surcharges applicable to the given route and container type."""
    # Determine the category for the container type
    if container_type in FCL_TYPES:
        category = "FCL"
    else:
        category = "LCL"

    all_active = (
        db.query(Surcharge)
        .filter(Surcharge.is_active == True)  # noqa: E712
        .all()
    )

    applicable: list[Surcharge] = []
    for s in all_active:
        # Check applies_to matches container category
        if s.applies_to not in (category, "all"):
            continue

        # Check port filters
        if s.origin_port_id is not None and s.origin_port_id != origin_port_id:
            continue
        if s.destination_port_id is not None and s.destination_port_id != dest_port_id:
            continue

        applicable.append(s)

    return applicable


def calculate_line_items(
    shipment: Shipment,
    rate_card: RateCard,
    surcharges: list[Surcharge],
) -> list[dict]:
    """Calculate all invoice line items for a shipment.

    Returns a list of dicts, each with keys:
        charge_code, description, quantity, unit_price, line_total
    Sorted with Ocean Freight first, then remaining surcharges alphabetically.
    """
    lines: list[dict] = []
    is_lcl = shipment.container_type == "LCL"

    # --- Ocean Freight ---
    if is_lcl:
        cbm = max(shipment.cbm or 0, 1.0)
        ocean_freight_total = rate_card.base_ocean_freight * cbm
        lines.append({
            "charge_code": "OFR",
            "description": "Ocean Freight",
            "quantity": cbm,
            "unit_price": rate_card.base_ocean_freight,
            "line_total": round(ocean_freight_total, 2),
        })
    else:
        count = shipment.container_count or 1
        ocean_freight_total = rate_card.base_ocean_freight * count
        lines.append({
            "charge_code": "OFR",
            "description": "Ocean Freight",
            "quantity": float(count),
            "unit_price": rate_card.base_ocean_freight,
            "line_total": round(ocean_freight_total, 2),
        })

    # --- Surcharges ---
    surcharge_lines: list[dict] = []

    for s in surcharges:
        if s.calculation_type == "per_container" and not is_lcl:
            count = shipment.container_count or 1
            surcharge_lines.append({
                "charge_code": s.charge_code,
                "description": s.charge_name,
                "quantity": float(count),
                "unit_price": s.amount,
                "line_total": round(s.amount * count, 2),
            })

        elif s.calculation_type == "per_cbm" and is_lcl:
            cbm = max(shipment.cbm or 0, 1.0)
            surcharge_lines.append({
                "charge_code": s.charge_code,
                "description": s.charge_name,
                "quantity": cbm,
                "unit_price": s.amount,
                "line_total": round(s.amount * cbm, 2),
            })

        elif s.calculation_type == "fixed":
            # LCL_MIN: only add if ocean freight is below threshold
            if s.charge_code == "LCL_MIN" and is_lcl:
                if ocean_freight_total >= LCL_MIN_THRESHOLD:
                    continue
            surcharge_lines.append({
                "charge_code": s.charge_code,
                "description": s.charge_name,
                "quantity": 1.0,
                "unit_price": s.amount,
                "line_total": round(s.amount, 2),
            })

        elif s.calculation_type == "percentage":
            pct_amount = (s.amount / 100.0) * ocean_freight_total
            surcharge_lines.append({
                "charge_code": s.charge_code,
                "description": s.charge_name,
                "quantity": 1.0,
                "unit_price": round(pct_amount, 2),
                "line_total": round(pct_amount, 2),
            })

    # Sort surcharges alphabetically by charge_code
    surcharge_lines.sort(key=lambda x: x["charge_code"])

    return lines + surcharge_lines


def generate_invoice(db: Session, shipment_id: int) -> Invoice:
    """Generate a new invoice for a shipment.

    Raises ValueError if the shipment is not found or already has an invoice.
    """
    # 1. Load shipment
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if shipment is None:
        raise ValueError(f"Shipment with id {shipment_id} not found")

    existing_invoice = (
        db.query(Invoice)
        .filter(Invoice.shipment_id == shipment_id)
        .first()
    )
    if existing_invoice is not None:
        raise ValueError(
            f"Shipment {shipment_id} already has invoice {existing_invoice.invoice_number}"
        )

    # 2. Determine bill-to client
    if shipment.bill_to == "consignee":
        client = db.query(Client).filter(Client.id == shipment.consignee_id).first()
    else:
        client = db.query(Client).filter(Client.id == shipment.shipper_id).first()

    if client is None:
        raise ValueError("Bill-to client not found for shipment")

    # 3. Find rate card
    rate_card = find_rate_card(
        db,
        shipment.origin_port_id,
        shipment.destination_port_id,
        shipment.container_type,
    )
    if rate_card is None:
        raise ValueError(
            f"No rate card found for route "
            f"(origin={shipment.origin_port_id}, dest={shipment.destination_port_id}) "
            f"and container type {shipment.container_type}"
        )

    # 4. Get applicable surcharges
    surcharges = get_applicable_surcharges(
        db,
        shipment.origin_port_id,
        shipment.destination_port_id,
        shipment.container_type,
    )

    # 5. Calculate line items
    line_items = calculate_line_items(shipment, rate_card, surcharges)

    # 6. Create Invoice record
    subtotal = sum(item["line_total"] for item in line_items)
    tax_amount = 0.0
    total_amount = subtotal + tax_amount

    today = date.today()
    payment_terms = client.payment_terms_days or 30

    invoice = Invoice(
        invoice_number=get_next_invoice_number(db),
        shipment_id=shipment_id,
        client_id=client.id,
        issue_date=today,
        due_date=today + timedelta(days=payment_terms),
        subtotal=round(subtotal, 2),
        tax_amount=round(tax_amount, 2),
        total_amount=round(total_amount, 2),
        amount_paid=0.0,
        balance_due=round(total_amount, 2),
        status="draft",
    )
    db.add(invoice)
    db.flush()  # Populate invoice.id before creating lines

    # 7. Create InvoiceLine records
    for idx, item in enumerate(line_items, start=1):
        line = InvoiceLine(
            invoice_id=invoice.id,
            line_order=idx,
            charge_code=item["charge_code"],
            description=item["description"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            line_total=item["line_total"],
        )
        db.add(line)

    # 8. Commit and return
    db.commit()
    db.refresh(invoice)
    return invoice
