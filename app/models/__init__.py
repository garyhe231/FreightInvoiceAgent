# Import all models so Base.metadata.create_all() picks them up
from app.models.client import Client  # noqa: F401
from app.models.port import Port  # noqa: F401
from app.models.rate_card import RateCard  # noqa: F401
from app.models.surcharge import Surcharge  # noqa: F401
from app.models.shipment import Shipment  # noqa: F401
from app.models.invoice import Invoice  # noqa: F401
from app.models.invoice_line import InvoiceLine  # noqa: F401
from app.models.payment import Payment  # noqa: F401
from app.models.email_log import EmailLog  # noqa: F401
from app.models.agent_log import AgentLog  # noqa: F401
