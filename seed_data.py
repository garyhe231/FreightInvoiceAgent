#!/usr/bin/env python3
"""
Comprehensive data seeding script for the Freight Invoice Automation app.
Seeds all tables with realistic freight forwarding data.

Usage:
    python3 seed_data.py
"""

import sys
sys.path.insert(0, '.')

import random
import math
from datetime import date, datetime, timedelta

random.seed(42)

from app.database import engine, SessionLocal, Base
from app.models.client import Client
from app.models.port import Port
from app.models.rate_card import RateCard
from app.models.surcharge import Surcharge
from app.models.shipment import Shipment
from app.models.invoice import Invoice
from app.models.invoice_line import InvoiceLine
from app.models.payment import Payment
from app.models.email_log import EmailLog


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def reset_database():
    """Drop all tables and recreate them."""
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Recreating all tables...")
    # Ensure every model is registered on Base.metadata
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    print("Database reset complete.\n")


# ---------------------------------------------------------------------------
# 1. Ports
# ---------------------------------------------------------------------------

def seed_ports(db):
    print("Seeding ports...")
    port_data = [
        ("CNSHA", "Shanghai",     "China",       "Asia"),
        ("CNNGB", "Ningbo",       "China",       "Asia"),
        ("CNYTN", "Yantian",      "China",       "Asia"),
        ("HKHKG", "Hong Kong",    "Hong Kong",   "Asia"),
        ("SGSIN", "Singapore",    "Singapore",   "Asia"),
        ("JPYOK", "Yokohama",     "Japan",       "Asia"),
        ("KRPUS", "Busan",        "South Korea", "Asia"),
        ("USLAX", "Los Angeles",  "USA",         "Americas"),
        ("USNYC", "New York",     "USA",         "Americas"),
        ("NLRTM", "Rotterdam",    "Netherlands", "Europe"),
        ("DEHAM", "Hamburg",      "Germany",     "Europe"),
        ("GBFXT", "Felixstowe",   "UK",          "Europe"),
    ]
    ports = []
    for code, name, country, region in port_data:
        p = Port(port_code=code, port_name=name, country=country, region=region)
        db.add(p)
        ports.append(p)
    db.flush()
    print(f"  -> {len(ports)} ports created.")
    return {p.port_code: p for p in ports}


# ---------------------------------------------------------------------------
# 2. Clients
# ---------------------------------------------------------------------------

def seed_clients(db):
    print("Seeding clients...")
    client_data = [
        # Asian shippers (exporters)
        {
            "company_name": "Shenzhen Bright Electronics Co., Ltd.",
            "client_type": "shipper",
            "contact_name": "Li Wei",
            "email": "li.wei@brightelectronics.cn",
            "phone": "+86-755-8832-1100",
            "address": "88 Nanshan Technology Park, Nanshan District",
            "city": "Shenzhen",
            "country": "China",
            "payment_terms_days": 30,
        },
        {
            "company_name": "Shanghai Global Trading Corp.",
            "client_type": "shipper",
            "contact_name": "Zhang Ming",
            "email": "z.ming@shanghaigtc.com",
            "phone": "+86-21-6188-3300",
            "address": "1500 Lujiazui Ring Road, Pudong New Area",
            "city": "Shanghai",
            "country": "China",
            "payment_terms_days": 30,
        },
        {
            "company_name": "Ningbo Pacific Textiles Ltd.",
            "client_type": "shipper",
            "contact_name": "Chen Xiaoli",
            "email": "chen.xl@nbpactex.com",
            "phone": "+86-574-8706-5500",
            "address": "28 Beilun Port Industrial Zone",
            "city": "Ningbo",
            "country": "China",
            "payment_terms_days": 30,
        },
        {
            "company_name": "Hong Kong Dragon Logistics",
            "client_type": "shipper",
            "contact_name": "David Chan",
            "email": "d.chan@dragonlogistics.hk",
            "phone": "+852-2815-7700",
            "address": "Unit 1205, Tower A, Harbour Centre, 25 Harbour Road",
            "city": "Hong Kong",
            "country": "Hong Kong",
            "payment_terms_days": 30,
        },
        {
            "company_name": "Guangzhou Fortune Plastics Co.",
            "client_type": "shipper",
            "contact_name": "Wang Fang",
            "email": "w.fang@fortuneplastics.cn",
            "phone": "+86-20-3862-0088",
            "address": "168 Huangpu East Road, Tianhe District",
            "city": "Guangzhou",
            "country": "China",
            "payment_terms_days": 30,
        },
        # US / EU consignees (importers)
        {
            "company_name": "Pacific West Trading Inc.",
            "client_type": "consignee",
            "contact_name": "Michael Torres",
            "email": "m.torres@pacwesttrading.com",
            "phone": "+1-310-555-0142",
            "address": "2500 E. Pacific Coast Hwy, Suite 400",
            "city": "Los Angeles",
            "country": "USA",
            "payment_terms_days": 30,
        },
        {
            "company_name": "Atlantic Import Solutions LLC",
            "client_type": "consignee",
            "contact_name": "Sarah Johnson",
            "email": "s.johnson@atlanticimports.com",
            "phone": "+1-212-555-0198",
            "address": "350 Fifth Avenue, 21st Floor",
            "city": "New York",
            "country": "USA",
            "payment_terms_days": 30,
        },
        {
            "company_name": "EuroTrade GmbH",
            "client_type": "consignee",
            "contact_name": "Klaus Mueller",
            "email": "k.mueller@eurotrade.de",
            "phone": "+49-40-5551-2200",
            "address": "Ballindamm 40",
            "city": "Hamburg",
            "country": "Germany",
            "payment_terms_days": 60,
        },
        {
            "company_name": "British Imports Ltd.",
            "client_type": "consignee",
            "contact_name": "James Whitfield",
            "email": "j.whitfield@britishimports.co.uk",
            "phone": "+44-20-7946-0321",
            "address": "14 Canary Wharf, Docklands",
            "city": "London",
            "country": "UK",
            "payment_terms_days": 60,
        },
        {
            "company_name": "Rotterdam Distribution BV",
            "client_type": "consignee",
            "contact_name": "Jan de Vries",
            "email": "j.devries@rotterdamdist.nl",
            "phone": "+31-10-555-4488",
            "address": "Europaweg 200, Maasvlakte",
            "city": "Rotterdam",
            "country": "Netherlands",
            "payment_terms_days": 45,
        },
    ]
    shippers = []
    consignees = []
    for cd in client_data:
        c = Client(**cd)
        db.add(c)
        if cd["client_type"] == "shipper":
            shippers.append(c)
        else:
            consignees.append(c)
    db.flush()
    print(f"  -> {len(shippers)} shippers + {len(consignees)} consignees = {len(shippers)+len(consignees)} clients created.")
    return shippers, consignees


# ---------------------------------------------------------------------------
# 3. Rate Cards
# ---------------------------------------------------------------------------

def seed_rate_cards(db, ports):
    print("Seeding rate cards...")
    eff = date(2026, 1, 1)
    carriers = ["COSCO", "Evergreen", "Maersk", "MSC", "ONE"]

    # Helper: create one rate card row
    def rc(origin_code, dest_code, ctype, rate, carrier):
        return RateCard(
            origin_port_id=ports[origin_code].id,
            destination_port_id=ports[dest_code].id,
            container_type=ctype,
            base_ocean_freight=rate,
            effective_from=eff,
            effective_to=None,
            carrier_name=carrier,
            is_active=True,
        )

    cards = []

    # Shanghai/Ningbo/Yantian -> LA
    for origin in ["CNSHA", "CNNGB", "CNYTN"]:
        carrier = random.choice(carriers)
        cards.append(rc(origin, "USLAX", "20GP", 1800, carrier))
        cards.append(rc(origin, "USLAX", "40GP", 2800, carrier))
        cards.append(rc(origin, "USLAX", "40HC", 3100, carrier))
        cards.append(rc(origin, "USLAX", "LCL",  55,   carrier))

    # Shanghai/Ningbo -> NYC
    for origin in ["CNSHA", "CNNGB"]:
        carrier = random.choice(carriers)
        cards.append(rc(origin, "USNYC", "20GP", 2200, carrier))
        cards.append(rc(origin, "USNYC", "40GP", 3400, carrier))
        cards.append(rc(origin, "USNYC", "40HC", 3700, carrier))
        cards.append(rc(origin, "USNYC", "LCL",  65,   carrier))

    # Shanghai -> Rotterdam/Hamburg
    for dest in ["NLRTM", "DEHAM"]:
        carrier = random.choice(carriers)
        cards.append(rc("CNSHA", dest, "20GP", 1600, carrier))
        cards.append(rc("CNSHA", dest, "40GP", 2500, carrier))
        cards.append(rc("CNSHA", dest, "40HC", 2800, carrier))
        cards.append(rc("CNSHA", dest, "LCL",  50,   carrier))

    # Hong Kong -> LA
    carrier = random.choice(carriers)
    cards.append(rc("HKHKG", "USLAX", "20GP", 1900, carrier))
    cards.append(rc("HKHKG", "USLAX", "40GP", 2900, carrier))
    cards.append(rc("HKHKG", "USLAX", "40HC", 3200, carrier))

    # We now have a good set; trim to exactly 20 if needed or keep all
    # (the routes above generate: 3*4 + 2*4 + 2*4 + 3 = 12+8+8+3 = 31)
    # Take the first 20 to match the spec
    cards = cards[:20]

    for c in cards:
        db.add(c)
    db.flush()
    print(f"  -> {len(cards)} rate cards created.")
    return cards


# ---------------------------------------------------------------------------
# 4. Surcharges
# ---------------------------------------------------------------------------

def seed_surcharges(db, ports):
    print("Seeding surcharges...")
    us_ports = [ports["USLAX"].id, ports["USNYC"].id]
    eu_ports = [ports["NLRTM"].id, ports["DEHAM"].id, ports["GBFXT"].id]

    surcharge_defs = [
        ("BAF",        "Bunker Adjustment Factor",         "per_container", 350,  None,            "FCL",  None),
        ("CAF",        "Currency Adjustment Factor",        "percentage",    3,    "ocean_freight", "all",  None),
        ("THC_ORIGIN", "Terminal Handling - Origin",        "per_container", 180,  None,            "FCL",  None),
        ("THC_DEST",   "Terminal Handling - Destination",   "per_container", 250,  None,            "FCL",  None),
        ("DOC_FEE",    "Documentation Fee",                 "fixed",         75,   None,            "all",  None),
        ("BL_FEE",     "Bill of Lading Fee",                "fixed",         50,   None,            "all",  None),
        ("SEAL_FEE",   "Container Seal Fee",                "per_container", 15,   None,            "FCL",  None),
        ("AMS_FEE",    "AMS Filing Fee",                    "fixed",         35,   None,            "all",  "US"),
        ("ISPS",       "ISPS Security Charge",              "per_container", 12,   None,            "FCL",  None),
        ("ENS_FEE",    "ENS Filing Fee",                    "fixed",         30,   None,            "all",  "EU"),
        ("CFS_ORIGIN", "CFS Charge Origin",                 "per_cbm",       15,   None,            "LCL",  None),
        ("CFS_DEST",   "CFS Charge Destination",            "per_cbm",       18,   None,            "LCL",  None),
        ("PSS",        "Peak Season Surcharge",             "per_container", 200,  None,            "FCL",  None),
        ("LCL_MIN",    "LCL Minimum Charge",                "fixed",         120,  None,            "LCL",  None),
        ("HANDLING",   "Freight Handling Fee",               "fixed",         45,   None,            "all",  None),
    ]

    surcharges = []
    for code, name, calc, amt, pct_of, applies, dest_region in surcharge_defs:
        if dest_region == "US":
            # Create one surcharge row per US port
            for pid in us_ports:
                s = Surcharge(
                    charge_code=code,
                    charge_name=name,
                    calculation_type=calc,
                    amount=amt,
                    percentage_of=pct_of,
                    applies_to=applies,
                    origin_port_id=None,
                    destination_port_id=pid,
                    is_active=True,
                )
                db.add(s)
                surcharges.append(s)
        elif dest_region == "EU":
            for pid in eu_ports:
                s = Surcharge(
                    charge_code=code,
                    charge_name=name,
                    calculation_type=calc,
                    amount=amt,
                    percentage_of=pct_of,
                    applies_to=applies,
                    origin_port_id=None,
                    destination_port_id=pid,
                    is_active=True,
                )
                db.add(s)
                surcharges.append(s)
        else:
            s = Surcharge(
                charge_code=code,
                charge_name=name,
                calculation_type=calc,
                amount=amt,
                percentage_of=pct_of,
                applies_to=applies,
                origin_port_id=None,
                destination_port_id=None,
                is_active=True,
            )
            db.add(s)
            surcharges.append(s)

    db.flush()
    # Report only the 15 unique charge codes
    unique_codes = set(s.charge_code for s in surcharges)
    print(f"  -> {len(surcharges)} surcharge rows ({len(unique_codes)} unique charge codes) created.")
    return surcharges


# ---------------------------------------------------------------------------
# 5. Shipments
# ---------------------------------------------------------------------------

def seed_shipments(db, ports, shippers, consignees):
    print("Seeding shipments...")

    # --- container type distribution ---
    # 60 shipments: 24 x 40GP, 15 x 40HC, 12 x 20GP, 9 x LCL
    container_pool = (
        ["40GP"] * 24 + ["40HC"] * 15 + ["20GP"] * 12 + ["LCL"] * 9
    )
    random.shuffle(container_pool)

    # --- Asian origin ports ---
    asia_origin_codes = ["CNSHA", "CNNGB", "CNYTN", "HKHKG"]
    # --- US/EU destination ports ---
    west_dest_codes = ["USLAX", "USNYC", "NLRTM", "DEHAM", "GBFXT"]

    # --- vessel names ---
    vessel_names = [
        "COSCO Shipping Aries", "Ever Golden", "Maersk Emerald",
        "MSC Isabella", "ONE Competence", "COSCO Shipping Taurus",
        "Ever Gentle", "Maersk Seletar", "MSC Gulsun", "ONE Continuity",
        "COSCO Shipping Virgo", "Ever Grade", "Maersk Enshi",
        "MSC Ambra", "ONE Commitment",
    ]

    commodities = [
        "Consumer electronics and accessories",
        "Cotton textiles and garments",
        "Flat-pack furniture and fittings",
        "Automotive spare parts",
        "Plastic injection-molded products",
        "Industrial machinery components",
        "LED lighting fixtures",
        "Ceramic tiles and sanitary ware",
        "Stainless steel kitchenware",
        "Rubber and silicone products",
        "Household appliances",
        "Sports equipment and accessories",
        "Toys and children's products",
        "Computer hardware and peripherals",
        "Polyester fabric rolls",
    ]

    carrier_prefixes = {
        "COSCO": "COSU",
        "Evergreen": "EGLV",
        "Maersk": "MAEU",
        "MSC": "MSCU",
        "ONE": "ONEY",
    }

    # Statuses per index: 0-19 delivered, 20-34 arrived, 35-49 shipped, 50-59 booked
    def status_for(idx):
        if idx < 20:
            return "delivered"
        elif idx < 35:
            return "arrived"
        elif idx < 50:
            return "shipped"
        else:
            return "booked"

    # Spread ETD across Dec 2025 - Feb 2026
    base_date = date(2025, 12, 1)  # earliest ETD
    shipments = []

    for i in range(60):
        ctype = container_pool[i]
        origin_code = random.choice(asia_origin_codes)
        dest_code = random.choice(west_dest_codes)
        shipper = random.choice(shippers)
        consignee_choice = random.choice(consignees)

        # Match destination port region to consignee where reasonable
        dest_region = ports[dest_code].region
        if dest_region == "Americas":
            consignee_choice = random.choice(
                [c for c in consignees if c.country == "USA"]
            )
        else:
            consignee_choice = random.choice(
                [c for c in consignees if c.country in ("Germany", "UK", "Netherlands")]
            )

        # ETD spread: roughly 1.5 days apart to cover ~90 days
        etd = base_date + timedelta(days=int(i * 1.5) + random.randint(0, 2))
        # Transit time depends on route
        if dest_region == "Americas":
            transit = random.randint(14, 22)
        else:
            transit = random.randint(25, 35)
        eta = etd + timedelta(days=transit)

        container_count = 1
        cbm = None
        weight_kg = None
        if ctype == "LCL":
            container_count = 1
            cbm = round(random.uniform(2, 15), 1)
            weight_kg = round(cbm * random.uniform(150, 400), 0)
        else:
            container_count = random.randint(1, 3)
            # Approximate weight per container
            weight_kg = round(container_count * random.uniform(12000, 24000), 0)

        vessel = random.choice(vessel_names)
        voyage = f"V{random.choice(['E', 'W', 'N', 'S'])}{random.randint(100,999)}"

        # Carrier prefix for B/L
        carrier_key = vessel.split()[0]  # first word: COSCO, Ever, Maersk, MSC, ONE
        bl_prefix = "COSU"
        if "Ever" in vessel:
            bl_prefix = "EGLV"
        elif "Maersk" in vessel:
            bl_prefix = "MAEU"
        elif "MSC" in vessel:
            bl_prefix = "MSCU"
        elif "ONE" in vessel:
            bl_prefix = "ONEY"

        bl_number = None
        if i < 50:
            bl_number = f"{bl_prefix}26{random.randint(10000, 99999)}"

        bill_to = "shipper" if random.random() < 0.6 else "consignee"

        shipment = Shipment(
            booking_number=f"BK-2026-{i+1:04d}",
            shipper_id=shipper.id,
            consignee_id=consignee_choice.id,
            origin_port_id=ports[origin_code].id,
            destination_port_id=ports[dest_code].id,
            container_type=ctype,
            container_count=container_count,
            cbm=cbm,
            weight_kg=weight_kg,
            commodity_description=random.choice(commodities),
            vessel_name=vessel,
            voyage_number=voyage,
            etd=etd,
            eta=eta,
            bl_number=bl_number,
            status=status_for(i),
            bill_to=bill_to,
        )
        db.add(shipment)
        shipments.append(shipment)

    db.flush()
    print(f"  -> {len(shipments)} shipments created.")
    return shipments


# ---------------------------------------------------------------------------
# 6. Invoices, Invoice Lines, Payments, Email Logs
# ---------------------------------------------------------------------------

def _ocean_freight_rate(ctype, origin_code, dest_code):
    """Return a realistic ocean freight rate based on route and container type."""
    # Lookup table mirroring our rate cards
    rates = {
        # (origin, dest, ctype) -> rate
    }
    # Shanghai/Ningbo/Yantian -> LA
    for o in ["CNSHA", "CNNGB", "CNYTN"]:
        rates[(o, "USLAX", "20GP")] = 1800
        rates[(o, "USLAX", "40GP")] = 2800
        rates[(o, "USLAX", "40HC")] = 3100
        rates[(o, "USLAX", "LCL")]  = 55
    # Shanghai/Ningbo -> NYC
    for o in ["CNSHA", "CNNGB"]:
        rates[(o, "USNYC", "20GP")] = 2200
        rates[(o, "USNYC", "40GP")] = 3400
        rates[(o, "USNYC", "40HC")] = 3700
        rates[(o, "USNYC", "LCL")]  = 65
    # Shanghai -> RTM/HAM
    for d in ["NLRTM", "DEHAM"]:
        rates[("CNSHA", d, "20GP")] = 1600
        rates[("CNSHA", d, "40GP")] = 2500
        rates[("CNSHA", d, "40HC")] = 2800
        rates[("CNSHA", d, "LCL")]  = 50
    # HK -> LA
    rates[("HKHKG", "USLAX", "20GP")] = 1900
    rates[("HKHKG", "USLAX", "40GP")] = 2900
    rates[("HKHKG", "USLAX", "40HC")] = 3200

    key = (origin_code, dest_code, ctype)
    if key in rates:
        return rates[key]
    # Fallback: approximate rates for routes not explicitly listed
    fallback = {"20GP": 2000, "40GP": 3000, "40HC": 3300, "LCL": 58}
    return fallback.get(ctype, 2500)


def seed_invoices_and_lines(db, shipments, ports, shippers, consignees):
    """Create 40 invoices (for shipments 0..39) with line items."""
    print("Seeding invoices and invoice lines...")

    # Build quick lookup for port codes
    port_id_to_code = {p.id: code for code, p in ports.items()}

    invoices = []
    all_lines = []

    for idx in range(40):
        ship = shipments[idx]
        origin_code = port_id_to_code[ship.origin_port_id]
        dest_code = port_id_to_code[ship.destination_port_id]
        dest_region = ports[dest_code].region

        # Determine billed client
        if ship.bill_to == "consignee":
            client_id = ship.consignee_id
        else:
            client_id = ship.shipper_id

        # Find client's payment terms
        billed_client = (
            db.query(Client).filter(Client.id == client_id).first()
        )
        payment_terms = billed_client.payment_terms_days if billed_client else 30

        issue_date = ship.etd + timedelta(days=random.randint(1, 4))
        due_date = issue_date + timedelta(days=payment_terms)

        # --- Build line items ---
        lines = []
        line_order = 0
        ctype = ship.container_type
        cnt = ship.container_count
        cbm = ship.cbm or 0

        rate = _ocean_freight_rate(ctype, origin_code, dest_code)

        if ctype == "LCL":
            # Ocean Freight
            ocean_total = round(rate * cbm, 2)
            line_order += 1
            lines.append(dict(
                charge_code="OCEAN",
                description=f"Ocean Freight ({origin_code} -> {dest_code}, {cbm} CBM)",
                quantity=cbm,
                unit_price=rate,
                line_total=ocean_total,
                line_order=line_order,
            ))
            # CFS Origin
            line_order += 1
            cfs_o = round(15 * cbm, 2)
            lines.append(dict(
                charge_code="CFS_ORIGIN",
                description="CFS Charge Origin",
                quantity=cbm,
                unit_price=15,
                line_total=cfs_o,
                line_order=line_order,
            ))
            # CFS Destination
            line_order += 1
            cfs_d = round(18 * cbm, 2)
            lines.append(dict(
                charge_code="CFS_DEST",
                description="CFS Charge Destination",
                quantity=cbm,
                unit_price=18,
                line_total=cfs_d,
                line_order=line_order,
            ))
            # Doc Fee
            line_order += 1
            lines.append(dict(
                charge_code="DOC_FEE",
                description="Documentation Fee",
                quantity=1,
                unit_price=75,
                line_total=75,
                line_order=line_order,
            ))
            # B/L Fee
            line_order += 1
            lines.append(dict(
                charge_code="BL_FEE",
                description="Bill of Lading Fee",
                quantity=1,
                unit_price=50,
                line_total=50,
                line_order=line_order,
            ))
            # AMS / ENS
            if dest_region == "Americas":
                line_order += 1
                lines.append(dict(
                    charge_code="AMS_FEE",
                    description="AMS Filing Fee",
                    quantity=1,
                    unit_price=35,
                    line_total=35,
                    line_order=line_order,
                ))
            elif dest_region == "Europe":
                line_order += 1
                lines.append(dict(
                    charge_code="ENS_FEE",
                    description="ENS Filing Fee",
                    quantity=1,
                    unit_price=30,
                    line_total=30,
                    line_order=line_order,
                ))
            # Handling
            line_order += 1
            lines.append(dict(
                charge_code="HANDLING",
                description="Freight Handling Fee",
                quantity=1,
                unit_price=45,
                line_total=45,
                line_order=line_order,
            ))
            # LCL Minimum (only if ocean freight < 120)
            if ocean_total < 120:
                line_order += 1
                lines.append(dict(
                    charge_code="LCL_MIN",
                    description="LCL Minimum Charge",
                    quantity=1,
                    unit_price=120,
                    line_total=120,
                    line_order=line_order,
                ))
        else:
            # FCL invoice
            # Ocean Freight
            ocean_total = round(rate * cnt, 2)
            line_order += 1
            lines.append(dict(
                charge_code="OCEAN",
                description=f"Ocean Freight ({origin_code} -> {dest_code}, {cnt}x{ctype})",
                quantity=cnt,
                unit_price=rate,
                line_total=ocean_total,
                line_order=line_order,
            ))
            # BAF
            line_order += 1
            lines.append(dict(
                charge_code="BAF",
                description="Bunker Adjustment Factor",
                quantity=cnt,
                unit_price=350,
                line_total=round(350 * cnt, 2),
                line_order=line_order,
            ))
            # THC Origin
            line_order += 1
            lines.append(dict(
                charge_code="THC_ORIGIN",
                description="Terminal Handling - Origin",
                quantity=cnt,
                unit_price=180,
                line_total=round(180 * cnt, 2),
                line_order=line_order,
            ))
            # THC Dest
            line_order += 1
            lines.append(dict(
                charge_code="THC_DEST",
                description="Terminal Handling - Destination",
                quantity=cnt,
                unit_price=250,
                line_total=round(250 * cnt, 2),
                line_order=line_order,
            ))
            # Doc Fee
            line_order += 1
            lines.append(dict(
                charge_code="DOC_FEE",
                description="Documentation Fee",
                quantity=1,
                unit_price=75,
                line_total=75,
                line_order=line_order,
            ))
            # B/L Fee
            line_order += 1
            lines.append(dict(
                charge_code="BL_FEE",
                description="Bill of Lading Fee",
                quantity=1,
                unit_price=50,
                line_total=50,
                line_order=line_order,
            ))
            # Seal Fee
            line_order += 1
            lines.append(dict(
                charge_code="SEAL_FEE",
                description="Container Seal Fee",
                quantity=cnt,
                unit_price=15,
                line_total=round(15 * cnt, 2),
                line_order=line_order,
            ))
            # ISPS
            line_order += 1
            lines.append(dict(
                charge_code="ISPS",
                description="ISPS Security Charge",
                quantity=cnt,
                unit_price=12,
                line_total=round(12 * cnt, 2),
                line_order=line_order,
            ))
            # AMS or ENS
            if dest_region == "Americas":
                line_order += 1
                lines.append(dict(
                    charge_code="AMS_FEE",
                    description="AMS Filing Fee",
                    quantity=1,
                    unit_price=35,
                    line_total=35,
                    line_order=line_order,
                ))
            elif dest_region == "Europe":
                line_order += 1
                lines.append(dict(
                    charge_code="ENS_FEE",
                    description="ENS Filing Fee",
                    quantity=1,
                    unit_price=30,
                    line_total=30,
                    line_order=line_order,
                ))
            # Handling
            line_order += 1
            lines.append(dict(
                charge_code="HANDLING",
                description="Freight Handling Fee",
                quantity=1,
                unit_price=45,
                line_total=45,
                line_order=line_order,
            ))

        # --- Compute totals ---
        subtotal = round(sum(l["line_total"] for l in lines), 2)
        tax_amount = 0.0
        total_amount = round(subtotal + tax_amount, 2)

        # --- Invoice status ---
        if idx < 10:
            status = "paid"
            amount_paid = total_amount
            balance_due = 0.0
        elif idx < 18:
            status = "partial"
            pct = random.uniform(0.50, 0.70)
            amount_paid = round(total_amount * pct, 2)
            balance_due = round(total_amount - amount_paid, 2)
        elif idx < 30:
            status = "sent"
            amount_paid = 0.0
            balance_due = total_amount
        else:
            status = "draft"
            amount_paid = 0.0
            balance_due = total_amount

        sent_at = None
        if status == "sent":
            sent_at = datetime.combine(issue_date + timedelta(days=random.randint(0, 2)), datetime.min.time())

        inv = Invoice(
            invoice_number=f"INV-2026-{idx+1:04d}",
            shipment_id=ship.id,
            client_id=client_id,
            issue_date=issue_date,
            due_date=due_date,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            amount_paid=amount_paid,
            balance_due=balance_due,
            status=status,
            notes=None,
            pdf_path=None,
            sent_at=sent_at,
        )
        db.add(inv)
        db.flush()  # get inv.id

        # Create invoice line objects
        for ld in lines:
            il = InvoiceLine(
                invoice_id=inv.id,
                line_order=ld["line_order"],
                charge_code=ld["charge_code"],
                description=ld["description"],
                quantity=ld["quantity"],
                unit_price=ld["unit_price"],
                line_total=ld["line_total"],
            )
            db.add(il)
            all_lines.append(il)

        invoices.append(inv)

    db.flush()
    print(f"  -> {len(invoices)} invoices created.")
    print(f"  -> {len(all_lines)} invoice lines created.")
    return invoices


# ---------------------------------------------------------------------------
# 7. Payments
# ---------------------------------------------------------------------------

def seed_payments(db, invoices):
    print("Seeding payments...")
    payments = []

    for idx, inv in enumerate(invoices):
        if inv.status == "paid":
            # Full payment, dates in Jan-Feb 2026
            pay_date = inv.issue_date + timedelta(days=random.randint(5, 30))
            ref = f"WT-2026-{random.randint(100000, 999999)}"
            p = Payment(
                invoice_id=inv.id,
                payment_date=pay_date,
                amount=inv.total_amount,
                payment_method="wire_transfer",
                reference_number=ref,
                notes=f"Full payment for {inv.invoice_number}",
            )
            db.add(p)
            payments.append(p)

        elif inv.status == "partial":
            pay_date = inv.issue_date + timedelta(days=random.randint(10, 25))
            ref = f"WT-2026-{random.randint(100000, 999999)}"
            p = Payment(
                invoice_id=inv.id,
                payment_date=pay_date,
                amount=inv.amount_paid,
                payment_method="wire_transfer",
                reference_number=ref,
                notes=f"Partial payment for {inv.invoice_number}",
            )
            db.add(p)
            payments.append(p)

    db.flush()
    print(f"  -> {len(payments)} payments created.")
    return payments


# ---------------------------------------------------------------------------
# 8. Email Logs
# ---------------------------------------------------------------------------

def seed_email_logs(db, invoices):
    print("Seeding email logs...")
    logs = []

    # Only for "sent" invoices (indices 18-29, i.e. invoices 19-30)
    for idx in range(18, 30):
        inv = invoices[idx]
        client = db.query(Client).filter(Client.id == inv.client_id).first()
        client_name = client.company_name if client else "Valued Customer"
        client_email = client.email if client else "unknown@example.com"

        log = EmailLog(
            invoice_id=inv.id,
            recipient_email=client_email,
            subject=f"Invoice {inv.invoice_number} \u2014 Pacific Freight Solutions",
            body=(
                f"Dear {client_name},\n\n"
                f"Please find attached invoice {inv.invoice_number} "
                f"for shipment {inv.invoice_number.replace('INV', 'BK')}.\n\n"
                f"Amount Due: ${inv.total_amount:,.2f}\n"
                f"Due Date: {inv.due_date.strftime('%B %d, %Y')}\n\n"
                f"Please remit payment at your earliest convenience.\n\n"
                f"Regards,\n"
                f"Pacific Freight Solutions Inc.\n"
                f"billing@pacificfreight.com"
            ),
            email_type="invoice",
            status="simulated",
        )
        db.add(log)
        logs.append(log)

    db.flush()
    print(f"  -> {len(logs)} email log entries created.")
    return logs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  Freight Invoice Agent -- Data Seeder")
    print("=" * 60)
    print()

    reset_database()

    db = SessionLocal()
    try:
        # 1. Ports
        ports = seed_ports(db)
        print()

        # 2. Clients
        shippers, consignees = seed_clients(db)
        print()

        # 3. Rate Cards
        rate_cards = seed_rate_cards(db, ports)
        print()

        # 4. Surcharges
        surcharges = seed_surcharges(db, ports)
        print()

        # 5. Shipments
        shipments = seed_shipments(db, ports, shippers, consignees)
        print()

        # 6. Invoices + Lines
        invoices = seed_invoices_and_lines(db, shipments, ports, shippers, consignees)
        print()

        # 7. Payments
        payments = seed_payments(db, invoices)
        print()

        # 8. Email Logs
        email_logs = seed_email_logs(db, invoices)
        print()

        db.commit()

        # ----- Summary -----
        print("=" * 60)
        print("  SEED COMPLETE -- Summary")
        print("=" * 60)
        counts = {
            "Ports":          db.query(Port).count(),
            "Clients":        db.query(Client).count(),
            "Rate Cards":     db.query(RateCard).count(),
            "Surcharges":     db.query(Surcharge).count(),
            "Shipments":      db.query(Shipment).count(),
            "Invoices":       db.query(Invoice).count(),
            "Invoice Lines":  db.query(InvoiceLine).count(),
            "Payments":       db.query(Payment).count(),
            "Email Logs":     db.query(EmailLog).count(),
        }
        for table, count in counts.items():
            print(f"  {table:<20s} {count:>5d}")
        print("=" * 60)
        print()

    except Exception as e:
        db.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
