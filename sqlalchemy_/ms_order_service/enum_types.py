import enum

class RoleType(enum.Enum):
    ADMIN = 'Admin'
    SUPERADMIN = 'SuperAdmin'
    MEMBER = 'Member'
    HOMEOWNER = 'HomeOwner'
    DRIVER = 'Driver'
    OPERATOR = 'Operator'

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
    CHARGER_MGMT = 'oneems_charger_management'
    CSMS_AS_SERVICE = "CSMS as a Service"
    ORDER_SERVICE = "Order Service"

class DriverStatus(enum.Enum):
    ACCEPTED = 'Accepted'
    BLOCKED = 'Blocked'
    EXPIRED = 'Expired'
    INVALID = 'Invalid'
    CONCURRENT = 'ConcurrentTx'

class OrderStatus(enum.Enum):
    CREATED = 'Created'
    AUTHORIZED = 'Authorized'
    AUTHORIZEDFAILED = 'AuthorizationFailed'
    PREPARECHARGING = 'PendingToStartCharging'
    CHARGING = 'Charging'
    RESERVING = 'Reserving'
    CANCELLED = 'Cancelled'
    COMPLETED = 'Completed'

class TriggerMethod(enum.Enum):
    AUTHORIZE = 'Authorize'
    START_TRANSACTION = 'StartTransaction'
    REMOTE_START = 'RemoteStartTransaction'
    MAKE_RESERVATION = 'ReserveNow'
    STOP_TRANSACTION = 'RemoteStopTransaction'
    CANCEL_ORDER = 'CancelOrder'

class StopTransactionReason(enum.Enum):
    emergency_stop = "EmergencyStop"
    ev_disconnected = "EVDisconnected"
    hard_reset = "HardReset"
    local = "Local"
    other = "Other"
    power_loss = "PowerLoss"
    reboot = "Reboot"
    remote = "Remote"
    soft_reset = "SoftReset"
    unlock_command = "UnlockCommand"
    de_authorized = "DeAuthorized"