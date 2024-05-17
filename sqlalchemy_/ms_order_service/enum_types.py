import enum

class OrderStatus(enum.Enum):
    CREATED = 'Created'
    AUTHORIZED = 'Authorized'
    AUTHORIZEDFAILED = 'AuthorizationFailed'
    CHARGING = 'Charging'
    RESERVING = 'Reserving'
    CANCELLED = 'Cancelled'
    COMPLETED = 'Completed'

class DriverStatus(enum.Enum):
    ACCEPTED = 'Accepted'
    BLOCKED = 'Blocked'
    EXPIRED = 'Expired'
    INVALID = 'Invalid'
    CONCURRENT = 'ConcurrentTx'

class ReturnActionStatus(enum.Enum):
    CREATED = 'created'
    COMPLETED = 'completed'
    FAILED = 'failed'

class ReturnStatus(enum.Enum):
    SUCCESS = 'success'
    ERROR = 'error'

class ProducerTypes(enum.Enum):
    EVSE_AS_SERVICE = "EVSE as a Service"
    OCPP_AS_SERVICE = "OCPP as a Service"
    CSMS_AS_SERVICE = "CSMS as a Service"
    ORDER_SERVICE = "Order Service"


class TriggerMethod(enum.Enum):
    AUTHORIZE = 'authorize'
    START_TRANSACTION = 'start_transaction'
    REMOTE_START = 'remote_start'
    MAKE_RESERVATION = 'make_reservation'
