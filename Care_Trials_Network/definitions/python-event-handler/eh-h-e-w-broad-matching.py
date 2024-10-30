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


class CDN:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def find_first(self, indices: str, parameters: SearchRequest) -> SearchResponse:
        return self.context.getCareDataNodeProvider().findFirst(indices, parameters)

    def raw_search(self, indices: str, from_row, num_rows, search_request) -> List:
        return self.context.getCareDataNodeProvider().rawSearch(indices, from_row, num_rows, search_request)

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
        self.cdn = CDN(context)
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
            EqualitySearchFilter.builder().fieldName("archived").value('false').build(),
            EqualitySearchFilter.builder().fieldName("trialStatus").value("NEW").build())

        existing_trials = self.vault.search('TRIALS_UNIQ', trial_filter)
        throw_next_event = False

        if len(existing_trials) == 1:
            existing_trial = existing_trials[0]
            result.put("transactionalGuid", existing_trial.get("transactionalGuid"))
            existing_trial_status = existing_trial.get('trialStatus')

            if existing_trial_status == 'NEW':
                throw_next_event = True
                existing_trial.put('trialStatus', 'SAVED')
                existing_trial.put('status', 'LIKED')
                self.vault.update('TRIALS_UNIQ', trial_filter, existing_trial, False)
                self.vault.update_all('TRIALS', trial_filter, Map.of("trialStatus", "SAVED"))

                cdn_record = HashMap(result)
                print("CDN Save to 'trials_likes':", cdn_record)
                cdn_record.putAll(self.event_payload)
                self.cdn.save('trials_likes', cdn_record)
                print(f"CDN Save to 'trials_likes': {cdn_record}")

        result.put('throwNextEvent', throw_next_event)
        result.putAll(self.event_payload)
        print("result", result)

        participant_activities_data = {
            'SiteID': self.event_payload.get("SiteID"),
            'NCTId': self.event_payload.get("TrialID"),
            'WalletID': self.node.info().getScAddress(),
            'Action': 'Like',
            'ActionID': str(uuid.uuid1()),
            'ActionRelatedData': "participant likes trial",
            'Date': self.format_to_date_short(self.event_payload.get('createdAt')),
        }
        self.cdn.save('participant_activities', participant_activities_data)
        print("participant_activities saved", participant_activities_data)
        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [eh-h-e-w-broad-matching.py]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
