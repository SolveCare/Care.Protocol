import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
import java

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
NodeInfo = java.type("care.solve.node.core.model.NodeInfo")
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

    def update_all(self, collection: str, criteria: List, data: Map) -> Map:
        vault = self.context.getVaultStorage(collection)
        print(f'==> [CustomPythonEventHandler#d]: {data}')
        guid = vault.update(criteria, data, False, False)
        print(f'==> [CustomPythonEventHandler#d]: {guid}')
        return vault.getByGuid(guid)

    def search(self, collection: str, criteria: List) -> List:
        vault = self.context.getVaultStorage(collection)
        return vault.search(criteria)


class Node:

    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def info(self) -> NodeInfo:
        return self.context.getNodeInfo()


class PythonEventHandler(ABC):

    def __init__(self, context: HandlerExecutionContext):
        self.arguments = context.getArguments()
        self.event_payload = context.getEvent().getPayload()
        self.vault = Vault(context)
        self.node = Node(context)

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):

    def find_last_questions_data(self) -> Map:
        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.node.info().getScAddress()).build())
        questions_data_list = self.vault.search('6_QUESTIONS', vault_filter)
        print(f'Found {len(questions_data_list)} records of 6_QUESTIONS')
        return questions_data_list[-1]

    @staticmethod
    def current_milli_time():
        return round(time.time() * 1000)

    @staticmethod
    def format_to_date(timestamp_ms: int) -> str:
        dt_object = datetime.fromtimestamp(timestamp_ms / 1000.0)
        return dt_object.isoformat()

    @staticmethod
    def format_to_date_short(timestamp_ms: int) -> str:
        dt_object = datetime.fromtimestamp(timestamp_ms / 1000.0)
        return dt_object.date().isoformat()

    def handle(self) -> Map:
        result = HashMap(self.arguments)

        trial_filter = List.of(
            EqualitySearchFilter.builder().fieldName("TrialID").value(self.event_payload.get("TrialID")).build(),
            EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
                self.event_payload.get("senderNodeAddress")).build())

        print("self.event_payload.get(TrialID)", self.event_payload.get("TrialID"))
        print("self.event_payload.get(senderNodeAddress)", self.event_payload.get("senderNodeAddress"))

        trials_vault_data = self.vault.search('PARTICIPANT_ADMIN_TRIALS', trial_filter)
        print("trials_vault_data unlike-next", trials_vault_data)

        for item in trials_vault_data:
            item.put("status", "UNLIKED")
            print("participant_like_status next", item)
            filter_by_id = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
                item.get('transactionalGuid')).build())
            updated = self.vault.update('PARTICIPANT_ADMIN_TRIALS', filter_by_id, item, False)
            print("participant_like_status updated PARTICIPANT_ADMIN_TRIALS", updated)
        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [eh-h-e-w-broad-unlike-next.py]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
