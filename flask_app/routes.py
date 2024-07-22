import asyncio
import uuid
from flask import request
from flask_restx import Resource
from flask_restx._http import HTTPStatus
from flask_app.services.update_order import UpdateOrder
from microservice_utils.api_namespace import ApiNamespace
from flask_app.swagger_models import RequestModel,ResponseModel
from flask_app.services.create_order import CreateOrder
from flask_app.services.list_order import ListOrder
from microservice_utils.settings import logger
from flask_app.services.models import KafkaPayload, ListOrderModel
from microservice_utils.oneems_user_mgmt_decorator.auth import permission_required
from sqlalchemy_.ms_order_service.enum_types import ReturnActionStatus, RoleType

ns_mobile = ApiNamespace("mobile", "APIs related to mobile")
request_model = RequestModel(ns_mobile)
response_model = ResponseModel(ns_mobile)

ns_operator = ApiNamespace("operator", "APIs related to operator")
request_model = RequestModel(ns_operator)
response_model = ResponseModel(ns_operator)

ns_kafka = ApiNamespace("mimic_kafka", "APIs related to mimic kafka")
request_model = RequestModel(ns_kafka)
response_model = ResponseModel(ns_kafka)

claims = {
    "custom:tenant_id": 1,
    "custom:role": RoleType.OPERATOR.value,
    "email": "abc@domain.com"
}

# PATH: /orderservice/mobile/remote_start
@ns_mobile.route("remote_start/<string:mobile_id>")
class remote_start(Resource):
    #@ns_mobile.doc(security="Authorization")
    #@permission_required()
    @ns_mobile.expect(request_model.create_order_mobile(), validate=True)
    @ns_mobile.marshal_with(response_model.create_order(), skip_none=True)
    def post(self,mobile_id):
        
        #claims = decode_token(get_token())
        data = request.json
        data.get("meta").update({"request_id":str(uuid.uuid4())})
        data.get("data").update({"tenant_id":str(claims.get("custom:tenant_id"))})
        logger.info(f"Request data: {data}")

        create_order = CreateOrder()
        create_order.remote_start_payload(data=KafkaPayload(**data))

# PATH: /orderservice/mobile/make_reservation
@ns_mobile.route("make_reservation/<string:mobile_id>")
class make_reservation(Resource):
    #@ns_mobile.doc(security="Authorization")
    #@permission_required()
    @ns_mobile.expect(request_model.create_order_reservation(), validate=True)
    @ns_mobile.marshal_with(response_model.create_order(), skip_none=True)
    def post(self):
        
        #claims = decode_token(get_token())

        data = request.json
        data.get("meta").update({"request_id":str(uuid.uuid4())})
        data.get("data").update({"tenant_id":str(claims.get("custom:tenant_id"))})
        logger.info(f"Request data: {data}")

        create_order = CreateOrder()
        create_order.create_order(data=KafkaPayload(**data))

# PATH: /orderservice/mobile/stop_transaction
@ns_mobile.route("stop_transaction/<string:mobile_id>")
class stop_transaction(Resource):
    #@ns_mobile.doc(security="Authorization")
    #@permission_required()
    @ns_mobile.expect(request_model.create_order_stop_transaction(), validate=True)
    @ns_mobile.marshal_with(response_model.create_order(), skip_none=True)
    def post(self,mobile_id):
        
        #claims = decode_token(get_token())

        data = request.json
        data.get("meta").update({"request_id":str(uuid.uuid4())})
        data.get("data").update({"tenant_id":str(claims.get("custom:tenant_id"))})
        logger.info(f"Request data: {data}")

        update_order = UpdateOrder()
        update_order.update_order(data=KafkaPayload(**data),cancel_ind=None)

# PATH: /orderservice/mobile/order
@ns_mobile.route("order/list")
class order_driver(Resource):
    #@ns_mobile.doc(security="Authorization")
    #@permission_required()
    @ns_mobile.param('keyword')
    @ns_mobile.param('ev_driver_id')
    @ns_mobile.param('transaction_id')
    @ns_mobile.marshal_with(response_model.list_order(), skip_none=True)
    def get(self):
        #claims = decode_token(get_token())

        data={
            "keyword": request.args.get("keyword"),
            "ev_driver_id": request.args.get("ev_driver_id"),
            "transaction_id": request.args.get("transaction_id"),
            "tenant_id": str(claims.get("custom:tenant_id")),
            "role": claims.get("custom:role")
        }
        
        list_order = ListOrder()
        return list_order.list_order(data=ListOrderModel(**data))



# PATH: /orderservice/operator/transaction_summary
@ns_operator.route("transaction_summary")
class transaction_summary(Resource):
    #@ns_operator.doc(security="Authorization")
    #@permission_required()
    @ns_operator.marshal_with(response_model.list_order(), skip_none=True)
    def get(self):
        
        #claims = decode_token(get_token())
        list_order = ListOrder()
        return list_order.list_transaction_summary(tenant_id=str(claims.get("custom:tenant_id")))

# PATH: /orderservice/operator/transaction_breakdown
@ns_operator.route("transaction_breakdown")
class transaction_breakdown(Resource):
    #@ns_operator.doc(security="Authorization")
    #@permission_required()
    @ns_operator.marshal_with(response_model.list_order(), skip_none=True)
    def get(self):
        
        #claims = decode_token(get_token())
        list_order = ListOrder()
        return list_order.list_transaction_breakdown(tenant_id=str(claims.get("custom:tenant_id")))



# PATH: /orderservice/kafka/authorize
@ns_kafka.route("authorize")
class authorize(Resource):
    #@ns_kafka.doc(security="Authorization")
    #@permission_required()
    @ns_kafka.expect(request_model.create_order_authorize(), validate=True)
    @ns_kafka.marshal_with(response_model.create_order(), skip_none=True)
    def post(self):
        
        #claims = decode_token(get_token())
        data = request.json
        data.get("data").update({"tenant_id":str(claims.get("custom:tenant_id"))})
        data.get("meta").update({"request_id":str(uuid.uuid4())})
        logger.info(f"Request data: {data}")

        create_order = CreateOrder()
        return create_order.create_order(data=KafkaPayload(**data))

# PATH: /orderservice/mobile/remote_start
@ns_kafka.route("remote_start")
class remote_start(Resource):
    #@ns_kafka.doc(security="Authorization")
    #@permission_required()
    @ns_kafka.expect(request_model.create_order_remote_start(), validate=True)
    @ns_kafka.marshal_with(response_model.create_order(), skip_none=True)
    def post(self):
        
        #claims = decode_token(get_token())
        data = request.json
        data.get("meta").update({"request_id":str(uuid.uuid4())})
        data.get("data").update({"tenant_id":str(claims.get("custom:tenant_id"))})
        logger.info(f"Request data: {data}")

        create_order = CreateOrder()
        return create_order.remote_start_payload(data=KafkaPayload(**data))

# PATH: /orderservice/mobile/make_reservation
@ns_kafka.route("make_reservation")
class make_reservation(Resource):
    #@ns_mobile.doc(security="Authorization")
    #@permission_required()
    @ns_kafka.expect(request_model.create_order_reservation(), validate=True)
    @ns_kafka.marshal_with(response_model.create_order(), skip_none=True)
    def post(self):
        #claims = decode_token(get_token())

        data = request.json
        data.get("meta").update({"request_id":str(uuid.uuid4())})
        data.get("data").update({"tenant_id":str(claims.get("custom:tenant_id"))})
        logger.info(f"Request data: {data}")

        create_order = CreateOrder()
        create_order.create_order(data=KafkaPayload(**data))