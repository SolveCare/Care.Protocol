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

SearchRequest = java.type('care.solve.node.core.model.cdn.SearchRequest')
SimpleQueryBuilder = java.type('care.solve.node.core.model.cdn.SimpleQueryBuilder')


class CDN:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def find_all(self, indices: str, parameters: SearchRequest) -> List:
        return self.context.getCareDataNodeProvider().findAll(indices, parameters)


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
        self.sender_node_address = context.getEvent().getFrom()
        self.event_payload = context.getEvent().getPayload()
        self.vault = Vault(context)
        self.node = Node(context)
        self.cdn = CDN(context)
        self.context = context


@abstractmethod
def handle(self) -> Map:
    pass


class CustomPythonEventHandler(PythonEventHandler):

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

        print("self.event_payload.get(TrialID)", self.event_payload.get("TrialID"))
        print("self.event_payload.get(senderNodeAddress)", self.event_payload.get("senderNodeAddress"))

        wallet_id_filter = SimpleQueryBuilder.eq('WalletID', self.event_payload.get("senderNodeAddress"))
        nct_id_filter = SimpleQueryBuilder.eq('SiteID', self.event_payload.get("SiteID"))
        action_id_filter = SimpleQueryBuilder.eq('Action', 'Re-like')
        activities_filter = SimpleQueryBuilder.aand(wallet_id_filter, nct_id_filter, action_id_filter)
 
        participant_activities = self.cdn.find_all('participant_activities', activities_filter)
        print(f'Found {len(participant_activities)} records in participant_activities')

        for activity in participant_activities:
            data = activity.getData()
            print(f"SiteID: {data.get('SiteID')}, WalletID: {data.get('WalletID')}, Action: {data.get('Action')}, Date: {data.get('Date')}")

        current_date = datetime.now().date().isoformat()
        print(f'Current date: {current_date}')

        relike_today = [activity for activity in participant_activities if activity.getData().get('Date') == current_date]
        print("relike_today: ", len(relike_today))

        site_id_filter = List.of(EqualitySearchFilter.builder().fieldName("SiteID").value(self.event_payload.get('SiteID')).build())
        trial_data = self.vault.search('TRIALS', site_id_filter)
        print("trial_data: ", trial_data)

        if len(relike_today) == 1 and trial_data:
            self.send_relike_notification()
            print("relike notification sent to admin!")

        print("eh-h-e-w-broad-relike-next.py end")
        return result

    def send_relike_notification(self):
        self.context.getNotificationProvider().send(
            'Heads up!',
            'Participant has shown renewed interest in your trial by liking it again. Take a moment to review their profile!'
        )


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [eh-h-e-w-broad-relike-next.py]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
