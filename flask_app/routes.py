import asyncio
from flask import request
from flask_restx import Resource
from flask_restx._http import HTTPStatus
from microservice_utils.api_namespace import ApiNamespace
from flask_app.swagger_models import RequestModel,ResponseModel
from flask_app.services.create_order import CreateOrder
from flask_app.services.list_order import ListOrder
from microservice_utils.settings import logger
from flask_app.services.models import KafkaPayload

ns_mobile = ApiNamespace("mobile", "APIs related to mobile")
request_model = RequestModel(ns_mobile)
response_model = ResponseModel(ns_mobile)

ns_operator = ApiNamespace("operator", "APIs related to operator")
request_model = RequestModel(ns_operator)
response_model = ResponseModel(ns_operator)

ns_kafka = ApiNamespace("mimic_kafka", "APIs related to mimic kafka")
request_model = RequestModel(ns_kafka)
response_model = ResponseModel(ns_kafka)

# PATH: /orderservice/mobile/remote_start
@ns_mobile.route("remote_start/<string:mobile_id>")
class remote_start(Resource):
    #@ns_mobile.doc(security="Authorization")
    #@token_required
    @ns_mobile.expect(request_model.create_order_mobile(), validate=True)
    @ns_mobile.marshal_with(response_model.create_order(), skip_none=True)
    def post(self,mobile_id):
        #token = str(request.headers["Authorization"])
        #claims = decode_token(token)
        tenant_id = 'tenant_idA'

        data = request.json
        logger.info(f"Request data: {data}")

        create_order = CreateOrder()
        create_order.create_order_mobile_id(mobile_id=mobile_id,data=KafkaPayload(**data),tenant_id=tenant_id)

# PATH: /orderservice/mobile/make_reservation
@ns_mobile.route("make_reservation/<string:mobile_id>")
class make_reservation(Resource):
    #@ns_mobile.doc(security="Authorization")
    #@token_required
    @ns_mobile.expect(request_model.create_order_rfid_reservation(), validate=True)
    @ns_mobile.marshal_with(response_model.create_order(), skip_none=True)
    def post(self,mobile_id):
        #token = str(request.headers["Authorization"])
        #claims = decode_token(token)
        tenant_id = 'tenant_idA'

        data = request.json
        logger.info(f"Request data: {data}")

        create_order = CreateOrder()
        create_order.create_order_mobile_id(mobile_id=mobile_id,data=KafkaPayload(**data),tenant_id=tenant_id)

# PATH: /orderservice/mobile/order
@ns_mobile.route("order/<int:transaction_id>/", defaults={'keyword': None})
@ns_mobile.route("order/<int:transaction_id>/<string:keyword>")
class order_driver(Resource):
    #@ns_mobile.doc(security="Authorization")
    #@token_required
    @ns_mobile.marshal_with(response_model.list_order(), skip_none=True)
    def get(self,transaction_id,keyword):
        #token = str(request.headers["Authorization"])
        #claims = decode_token(token)
        logger.info(f"Transaction ID: {transaction_id}")
        tenant_id = 'tenant_idA'
        list_order = ListOrder()
        return list_order.list_order(tenant_id=tenant_id,transaction_id=transaction_id,keyword=keyword)



# PATH: /orderservice/operator/order
@ns_operator.route("order", defaults={'keyword': None})
@ns_operator.route("order/<string:keyword>")
class order_operator(Resource):
    #@ns_operator.doc(security="Authorization")
    #@token_required
    @ns_operator.marshal_with(response_model.list_order(), skip_none=True)
    def get(self,keyword):
        #token = str(request.headers["Authorization"])
        #claims = decode_token(token)
        tenant_id = 'tenant_idA'
        list_order = ListOrder()
        return list_order.list_order(tenant_id=tenant_id,transaction_id=None,keyword=keyword)

# PATH: /orderservice/operator/transaction_summary
@ns_operator.route("transaction_summary")
class transaction_summary(Resource):
    #@ns_operator.doc(security="Authorization")
    #@token_required
    @ns_operator.marshal_with(response_model.list_order(), skip_none=True)
    def get(self):
        #token = str(request.headers["Authorization"])
        #claims = decode_token(token)
        tenant_id = 'tenant_idA'
        list_order = ListOrder()
        return list_order.list_transaction_summary(tenant_id=tenant_id)

# PATH: /orderservice/operator/transaction_breakdown
@ns_operator.route("transaction_breakdown")
class transaction_breakdown(Resource):
    #@ns_operator.doc(security="Authorization")
    #@token_required
    @ns_operator.marshal_with(response_model.list_order(), skip_none=True)
    def get(self):
        #token = str(request.headers["Authorization"])
        #claims = decode_token(token)
        tenant_id = 'tenant_idA'
        list_order = ListOrder()
        return list_order.list_transaction_breakdown(tenant_id=tenant_id)



# PATH: /orderservice/kafka/authorize
@ns_kafka.route("authorize")
class authorize(Resource):
    #@ns_mobile.doc(security="Authorization")
    #@token_required
    @ns_kafka.expect(request_model.create_order_rfid_authorize(), validate=True)
    @ns_kafka.marshal_with(response_model.create_order(), skip_none=True)
    def post(self):
        #token = str(request.headers["Authorization"])
        #claims = decode_token(token)
        tenant_id = 'tenant_idA'

        data = request.json
        logger.info(f"Request data: {data}")

        create_order = CreateOrder()
        create_order.create_order_rfid(data=KafkaPayload(**data))