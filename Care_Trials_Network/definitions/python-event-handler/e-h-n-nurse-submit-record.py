import java
import datetime

from datetime import datetime
from abc import ABC, abstractmethod

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")


class Vault:

    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def save(self, collection: str, data: Map) -> Map:
        vault = self.context.getVaultStorage(collection)
        guid = vault.save(data)
        return vault.getByGuid(guid)

    def update(self, collection: str, criteria: List, data: Map, insert_if_absent: bool) -> Map:
        vault = self.context.getVaultStorage(collection)
        print(f'==> [CustomPythonEventHandler#d]: {data}')
        guid = vault.update(criteria, data, insert_if_absent)
        print(f'==> [CustomPythonEventHandler#d]: {guid}')
        return vault.getByGuid(guid)

    def search(self, collection: str, criteria: List) -> List:
        vault = self.context.getVaultStorage(collection)
        return vault.search(criteria)


class PythonEventHandler(ABC):

    def __init__(self, context: HandlerExecutionContext):
        self.arguments = context.getArguments()
        self.event_payload = context.getEvent().getPayload()
        self.vault = Vault(context)
        self.context = context

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):

    def send_notification(self):
        self.context.getNotificationProvider().send(
            'Congratulations!',
            'You have received a new record for review.')

    def handle(self) -> Map:
        print("Custom event handler e-h-n-nurse-submit-record.py")

        result = HashMap(self.arguments)

        # count saved trials
        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
            self.event_payload.get('transactionalGuid')).build())
        vault_data = self.vault.search('RECORD_DATA', vault_filter)

        print("==>Nurse vault_data: ", vault_data)
        current_time = datetime.now()
        current_date_string = current_time.strftime('%d-%m-%Y')

        data = {
            "participantDetails": self.event_payload.get('participantDetails'),
            "recordType": self.event_payload.get('recordType'),
            "folderReference": self.event_payload.get('folderReference'),
            "sendToAdmin": self.event_payload.get('sendToAdmin'),
            "recordAge": self.event_payload.get('recordAge'),
            "transactionalGuid": self.event_payload.get('transactionalGuid'),
            "recordStatus": "submitted",
            "timeMessage": "Submitted on: " + current_date_string,
            "senderNodeAddress": self.event_payload.get("senderNodeAddress")
        }

        print("==>Nurse data:", data)
        self.vault.save('RECORD_DATA', data)
        result.putAll(self.event_payload)

        print("e-h-n-nurse-submit-record.py result", result)

        self.send_notification()
        print("Notification sent!")

        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
