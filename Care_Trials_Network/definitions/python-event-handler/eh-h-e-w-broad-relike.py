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
SearchResponse = java.type('care.solve.node.core.model.cdn.SearchResponse')
SimpleQueryBuilder = java.type('care.solve.node.core.model.cdn.SimpleQueryBuilder')


class CDN:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def find_first(self, indices: str, parameters: SearchRequest) -> SearchResponse:
        return self.context.getCareDataNodeProvider().findFirst(indices, parameters)

    def find_all(self, indices: str, parameters: SearchRequest) -> List:
        return self.context.getCareDataNodeProvider().findAll(indices, parameters)

    def raw_search(self, indices: str, from_row, num_rows, search_request) -> List:
        return self.context.getCareDataNodeProvider().rawSearch(indices, from_row, num_rows, search_request)

    def save(self, indices: str, data) -> SearchResponse:
        return self.context.getCareDataNodeProvider().save(indices, data)

    def update(self, indices: str, identifier: str, data: Map) -> SearchResponse:
        return self.context.getCareDataNodeProvider().update(indices, identifier, data)


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
        self.cdn = CDN(context)
        self.vault = Vault(context)
        self.node = Node(context)
        self.context = context


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

        trial_filter = SimpleQueryBuilder.aand(
            SimpleQueryBuilder.eq('TrialID', self.event_payload.get("TrialID")),
            SimpleQueryBuilder.eq('senderNodeAddress', self.node.info().getScAddress()))

        existing_trials = self.cdn.find_all('trials_likes', trial_filter)

        for row in existing_trials:
            update_data = Map.of('status', 'RELIKED')
            self.cdn.update('trials_likes', row.getId(), update_data)

        existing_trial = self.cdn.find_first('trials_likes', trial_filter)
        print("existing_trialLL", existing_trial)

        current_time = datetime.now()
        current_date = current_time.strftime('%Y-%m-%d')
        print("current_date_string--", current_date)

        #        if existing_trials:
        #            for row in existing_trials:
        #                print("existing_likes_row", row)
        #                row.remove("_id")
        #                row.remove("_revision")
        #                row.remove("_modified")
        #                row.remove("participantTrialID")
        #                row.remove("trialStatus")
        #                row.remove("UniqueCode")
        #                row.put("likeStatus", "RELIKED")
        #                result.putAll(row)
        #                print("result row", result)
        #                #self.cdn.save('trials_likes', row)
        #                update_data = Map.of('likeStatus', "RELIKED")
        #                self.cdn.update('trials_likes', row.getId(), update_data)

        participant_activities_data = {
            'SiteID': self.event_payload.get("SiteID"),
            'NCTId': self.event_payload.get("TrialID"),
            'WalletID': self.node.info().getScAddress(),
            'Action': 'Re-like',
            'ActionID': str(uuid.uuid1()),
            'ActionRelatedData': "participant likes campaign",
            'Date': current_date,
        }
        self.cdn.save('participant_activities', participant_activities_data)
        print("participant_activities", participant_activities_data)

        result.putAll(self.event_payload)
        print("result relike", result)
        self.send_relike_notification()
        print("relike notification sent to admin!")
        return result

    def send_relike_notification(self):
        self.context.getNotificationProvider().send(
            'Heads up!',
            'You\'ve liked this trial again. We\'ve sent a reminder to the admin to check out your interest.'
        )


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [eh-h-e-w-broad-relike.py]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
