from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientResponse

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=list[ClientResponse])
def list_clients(
    type: Optional[str] = Query(None, description="Filter by client_type, e.g. 'shipper' or 'consignee'"),
    db: Session = Depends(get_db),
):
    query = db.query(Client)
    if type:
        query = query.filter(Client.client_type == type)
    return query.order_by(Client.company_name).all()


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.post("", response_model=ClientResponse, status_code=201)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    client = Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(client_id: int, payload: ClientCreate, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    for key, value in payload.model_dump().items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return client
