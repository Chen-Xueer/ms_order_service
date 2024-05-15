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