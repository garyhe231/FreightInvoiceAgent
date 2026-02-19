from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.shipment import Shipment
from app.models.invoice import Invoice
from app.models.port import Port
from app.models.client import Client
from app.schemas.shipment import ShipmentResponse, ShipmentDetail

router = APIRouter(prefix="/api/shipments", tags=["shipments"])


@router.get("", response_model=list[ShipmentResponse])
def list_shipments(
    status: Optional[str] = Query(None, description="Filter by shipment status"),
    has_invoice: Optional[bool] = Query(None, description="Filter by whether shipment has an invoice"),
    db: Session = Depends(get_db),
):
    query = db.query(Shipment)
    if status:
        query = query.filter(Shipment.status == status)
    if has_invoice is not None:
        invoiced_ids = db.query(Invoice.shipment_id).filter(Invoice.shipment_id.isnot(None)).subquery()
        if has_invoice:
            query = query.filter(Shipment.id.in_(invoiced_ids))
        else:
            query = query.filter(Shipment.id.notin_(invoiced_ids))
    return query.order_by(Shipment.created_at.desc()).all()


@router.get("/{shipment_id}", response_model=ShipmentDetail)
def get_shipment(shipment_id: int, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Look up port names
    origin_port_name = None
    destination_port_name = None
    if shipment.origin_port_id:
        origin_port = db.query(Port).filter(Port.id == shipment.origin_port_id).first()
        if origin_port:
            origin_port_name = origin_port.port_name
    if shipment.destination_port_id:
        dest_port = db.query(Port).filter(Port.id == shipment.destination_port_id).first()
        if dest_port:
            destination_port_name = dest_port.port_name

    # Look up client names
    shipper_name = None
    consignee_name = None
    if shipment.shipper_id:
        shipper = db.query(Client).filter(Client.id == shipment.shipper_id).first()
        if shipper:
            shipper_name = shipper.company_name
    if shipment.consignee_id:
        consignee = db.query(Client).filter(Client.id == shipment.consignee_id).first()
        if consignee:
            consignee_name = consignee.company_name

    # Check if invoice exists
    has_invoice = db.query(Invoice).filter(Invoice.shipment_id == shipment_id).first() is not None

    # Build response
    data = ShipmentDetail.model_validate(shipment)
    data.origin_port_name = origin_port_name
    data.destination_port_name = destination_port_name
    data.shipper_name = shipper_name
    data.consignee_name = consignee_name
    data.has_invoice = has_invoice
    return data
