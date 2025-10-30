# storage_dynamodb.py
import logging
import boto3
from boto3.dynamodb.types import TypeSerializer
from models import WidgetRequest, to_flat_widget_dict

class DynamoWidgetStore:
    """
    Saves widgets to a DynamoDB table with *flattened* attributes.
    Every field (including otherAttributes) becomes a top-level attribute.
    """

    def __init__(self, table_name: str):
        self.ddb = boto3.client("dynamodb")
        self.table = table_name
        self.serializer = TypeSerializer()
        self.log = logging.getLogger(self.__class__.__name__)

    def put_widget(self, req: WidgetRequest) -> str:
        item_py = to_flat_widget_dict(req)  # plain Python dict
        # Convert to DynamoDB AttributeValue format
        item_av = self.serializer.serialize(item_py)["M"]

        try:
            self.ddb.put_item(TableName=self.table, Item=item_av)
            self.log.info(f"Stored widget {item_py['widgetId']} in DynamoDB table {self.table}")
            return item_py["widgetId"]
        except Exception as e:
            self.log.error(f"Failed to store widget in DynamoDB: {e}")
            raise
