import java
import time
import uuid
from datetime import datetime

from abc import ABC, abstractmethod

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
SearchRequest = java.type('care.solve.node.core.model.cdn.SearchRequest')
SearchResponse = java.type('care.solve.node.core.model.cdn.SearchResponse')
QueryCondition = java.type('care.solve.node.core.model.cdn.QueryCondition')
QueryConditions = java.type('care.solve.node.core.model.cdn.QueryConditions')
SimpleQueryBuilder = java.type('care.solve.node.core.model.cdn.SimpleQueryBuilder')

NodeInfo = java.type("care.solve.node.core.model.NodeInfo")
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")
NumericBoundsSearchFilter = java.type("care.solve.node.core.model.query.NumericBoundsSearchFilter")
SearchQueryFilter = java.type("care.solve.node.core.model.query.SearchQueryFilter")


class CDN:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context
        self.index = 'trials-with-geo'

    def findAll(self, parameters: SearchRequest) -> List:
        return self.context.getCareDataNodeProvider().findAll(self.index, parameters)

    def findFirst(self, parameters: SimpleQueryBuilder) -> SearchResponse:
        transaction_criteria = SimpleQueryBuilder.eq('_transaction_id',
                                                     self.context.getEvent().getPayload().get('transactionId'))
        return self.context.getCareDataNodeProvider().findFirst(self.index, SimpleQueryBuilder.aand(parameters,
                                                                                                    transaction_criteria))

    def raw_search(self, from_row, num_rows, search_request) -> List:
        return self.context.getCareDataNodeProvider().rawSearch(self.index, from_row, num_rows, search_request)

    def save(self, indices: str, data) -> SearchResponse:
        return self.context.getCareDataNodeProvider().save(indices, data)


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
        self.cdn = CDN(context)
        self.node = Node(context)
        self.context = context


@abstractmethod
def handle(self) -> Map:
    pass


class CustomPythonEventHandler(PythonEventHandler):

    def send_notification(self):
        self.context.getNotificationProvider().send(
            'Congratulations!',
            'Your records/ID have been approved.')

    def handle(self) -> Map:
        print("Custom event handler--verify badge.pyyy")

        result = HashMap(self.arguments)

        ID_bronze_url = 'https://i.ibb.co/0y0SXMt/Bronze-ID-small.png'
        ID_silver_url = 'https://i.ibb.co/QpnCNH9/Silver-ID-small.png'
        ID_gold_url = 'https://i.ibb.co/Kw3RFKz/Gold-ID-small.png'
        ID_platinum_url = 'https://i.ibb.co/fxm2fYZ/Platinum-ID-small.png'

        Medical_bronze_url = 'https://i.ibb.co/JRXBHJf/Bronze-medical-small.png'
        Medical_silver_url = 'https://i.ibb.co/whbrHDp/Silver-Records-small.png'
        Medical_gold_url = 'https://i.ibb.co/LPNrPGh/Gold-Records-small.png'
        Medical_platinum_url = 'https://i.ibb.co/7VMD3wQ/Platinumm-Records-small.png'

        vault_filter_badges = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.node.info().getScAddress()).build())
        vault_data_badges = self.vault.search('BADGES', vault_filter_badges)
        print(f'upload record badges: {vault_data_badges}')

        if vault_data_badges:
            print("ppp_vault_IDBadge_0", vault_data_badges[0].get("IDBadges"))
            print("ppp_vault_recodBadge_0", vault_data_badges[0].get("recordBadges"))
            print("type---", self.event_payload.get('recordType'))

            current_time = datetime.now()
            current_date_string = current_time.strftime('%Y-%m-%d')
            print("current_date_string---", current_date_string)


            if self.event_payload.get('recordType') == 'ID':
                badges = {
                    "IDBadges": ID_platinum_url
                }
                self.vault.update('BADGES', vault_filter_badges, badges, False)
                participant_activities_data = {
                    'SiteID': self.event_payload.get("SiteID") or "None",
                    'NCTId': self.event_payload.get("TrialID") or "None",
                    'WalletID': self.node.info().getScAddress(),
                    'Action': "Received badge-Platinum ID",
                    'ActionID': str(uuid.uuid1()),
                    'ActionRelatedData': "participant likes campaign",
                    'Date': current_date_string,
                }
                self.cdn.save('participant_activities', participant_activities_data)
                print("==> participant_activities_data:", participant_activities_data)

                print("ID-----")

            elif self.event_payload.get('recordType') == 'Medical':
                badges = {
                    "recordBadges": Medical_platinum_url
                }
                self.vault.update('BADGES', vault_filter_badges, badges, False)
                print("Medical-----")
                participant_activities_data = {
                    'SiteID': self.event_payload.get("SiteID") or "None",
                    'NCTId': self.event_payload.get("TrialID") or "None",
                    'WalletID': self.node.info().getScAddress(),
                    'Action': "Received badge-Platinum Record",
                    'ActionID': str(uuid.uuid1()),
                    'ActionRelatedData': "participant likes campaign",
                    'Date': current_date_string,
                }
                self.cdn.save('participant_activities', participant_activities_data)
                # self.save_participant_data(self,"Received badge-Platinum Record")

        self.send_notification()
        print("notification sent!")
        return result

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

    def save_participant_data(self, action):
        #        if self.__is_id_record():
        #            action = "Upload ID"
        #        elif self.__is_medical_record():
        #            action = "Upload Records"
        #        if self.__update_badge_record_if_required:
        #            action = "Received badge (Record-Silver)"
        #        elif self.__update_id_badge_required:
        #            action = "Received badge (ID-Silver)"
        participant_activities_data = {
            'SiteID': self.event_payload.get("SiteID") or "None",
            'NCTId': self.event_payload.get("TrialID") or "None",
            'WalletID': self.node.info().getScAddress(),
            'Action': action,
            'ActionID': str(uuid.uuid1()),
            'ActionRelatedData': "participant likes campaign",
            'Date': self.format_to_date_short(self.event_payload.get('createdAt')),
        }
        self.cdn.save('participant_activities', participant_activities_data)


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
