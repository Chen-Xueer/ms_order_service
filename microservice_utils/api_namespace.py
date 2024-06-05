from typing import Any, Optional
from flask_restx import fields, Namespace
from pydantic import BaseModel


def get_defs(properties, schema):
    if "$ref" in properties:
        refs = str(properties["$ref"]).replace("#/$defs/", "")
        return schema["$defs"][refs]

    elif "type" in properties:
        return properties

    raise Exception("Not implemented")


class ApiNamespace(Namespace):

    def prop_to_model(self, properties, schema):
        if "type" in properties or "$ref" in properties:
            return self.prop_ref(properties, schema)

        elif "anyOf" in properties:
            schema_type = []
            schema_example = []
            for anyof in properties["anyOf"]:
                anyof_defs = get_defs(anyof, schema)
                prop_type = anyof_defs["type"]

                schema_type.append(prop_type)

                if prop_type == "string":
                    if "enum" in anyof:
                        schema_example.append(
                            "/".join([e for e in anyof["enum"]])
                        )
                    else:
                        schema_example.append("")

                elif prop_type == "integer":
                    schema_example.append(0)

                elif prop_type == "number":
                    schema_example.append(0.0)

                elif prop_type == "boolean":
                    schema_example.append(True)

                elif prop_type == "array":
                    schema_example.append([])

                elif prop_type == "object":
                    schema_example.append({})

            class AnyOf(fields.Raw):
                __schema_type__ = schema_type
                __schema_example__ = schema_example

            return AnyOf()

        raise Exception("Not implemented")

    def prop_ref(self, properties, schema):
        defs = get_defs(properties, schema)

        ptype = defs["type"]

        if ptype == "string":
            enum = None
            example = ""
            if "enum" in defs:
                enum = list(defs["enum"])
                example = "/".join([e for e in enum])

            return fields.String(required=True, enum=enum, example=example)

        elif ptype == "integer":
            example = 0
            return fields.Integer(required=True, example=example)

        elif ptype == "number":
            example = 0.0
            return fields.Integer(required=True, example=example)

        elif ptype == "boolean":
            example = True
            return fields.Boolean(required=True, example=example)

        elif ptype == "array":
            return fields.List(
                self.prop_to_model(defs["items"], schema), required=True
            )

        elif ptype == "object":

            model = {}
            for name, properties in defs["properties"].items():
                model[name] = self.prop_to_model(properties, defs)

            api_model = self.model(schema["title"] + defs["title"], model)

            return fields.Nested(api_model, required=True)

        raise Exception("Not implemented")

    def api_fields(
        self,
        pydantic_model: type[BaseModel],
        model_name: Optional[str] = None,
        example: dict[str, Any] = {},
    ):

        schema = pydantic_model.model_json_schema()

        model = {}
        for name, properties in schema["properties"].items():
            prop_model = self.prop_to_model(properties, schema)

            prop_model.example = example.get(name, prop_model.example)

            model[name] = prop_model

        api_model = self.model((model_name or schema["title"]), model)

        return api_model
