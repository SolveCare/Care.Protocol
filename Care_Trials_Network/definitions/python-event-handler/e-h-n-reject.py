import java
import datetime

from datetime import datetime
from abc import ABC, abstractmethod

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')

EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")
NumericBoundsSearchFilter = java.type("care.solve.node.core.model.query.NumericBoundsSearchFilter")
SearchQueryFilter = java.type("care.solve.node.core.model.query.SearchQueryFilter")


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
        self.sender_node_address = context.getEvent().getFrom()
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
            'You have rejected the record.')

    def update_collection(self, collection_name, row, trial_filter) -> Map:
        print("rejecttt row.put")

        current_time = datetime.now()
        current_date_string = current_time.strftime('%d-%m-%Y')

        row.put("participantLastName", self.event_payload.get('participantLastName') or "")
        row.put("participantFirstName", self.event_payload.get('participantFirstName') or "")
        row.put("reportType", "Required re-upload")
        row.put("reportTags", "Required re-upload")
        row.put("recordDate", "Required re-upload")

        row.put("ageOfRecord", self.event_payload.get('ageOfRecord') or "Required re-upload")
        row.put("comments", self.event_payload.get('comments') or "Required re-upload")
        row.put("recordStatus", "rejected")
        row.put("isRejected", True)
        row.put("timeMessage", "Rejected on: " + current_date_string)

        self.vault.update(collection_name, trial_filter, row, False)
        return row

    def handle(self) -> Map:
        print("Custom event handler-- reject.pyyy")

        result = HashMap(self.arguments)

        print("rejecttt")

        # count saved trials
        # vault_filter = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(self.event_payload.get('transactionalGuid')).build())
        # vault_data = self.vault.search('RECORD_DATA', vault_filter)
        # vault_data_len= len(vault_data)
        # vault_data_size=vault_data_len-1
        transaction_criterion = EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
            self.event_payload.get("transactionalGuid")).build()
        vault_filter = List.of(transaction_criterion)
        vault_data = self.vault.search('RECORD_DATA', vault_filter)
        for data in vault_data:
            updated = self.update_collection('RECORD_DATA', data, vault_filter)
            print("data before cleanup", updated)
            self.context.initRecipientAddress(updated.get('senderNodeAddress'))
            updated.remove("_id")
            updated.remove("_revision")
            updated.remove("_modified")
            updated.remove("senderNodeAddress")
            updated.remove("sendToAdmin")
            updated.remove("recordAge")
            # updated.remove("participantLastName")
            # updated.remove("participantFirstName")
            # updated.remove("reportType")
            # updated.remove("reportTags")
            # updated.remove("ageOfRecord")

            print("rejecttt data", updated)

            self.send_notification()
            print("Notification sent!")

            return updated

        # Add verified badges

        # Badges criteria

        # verified badges done


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
