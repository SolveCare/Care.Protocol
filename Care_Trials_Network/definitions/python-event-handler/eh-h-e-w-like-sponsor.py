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
        print("LIKE result: ", result)

        self.context.getNotificationProvider().send(
            'Great news!',
            'You have liked a sponsor.')
 
        sponsor_filter = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(self.event_payload.get("transactionalGuid")).build())
        
        print("self.event_payload.get(Country)", self.event_payload.get("Country"))

        print("sponsor_filter", sponsor_filter)

        existing_sponsors = self.vault.search('SPONSORS', sponsor_filter)
        throw_next_event = False

        print("existing_sponsors", existing_sponsors)
        
        if len(existing_sponsors) == 1:
            existing_sponsor = existing_sponsors[0]
            result.put("transactionalGuid", existing_sponsor.get("transactionalGuid"))
            existing_trial_status = existing_sponsor.get('sponsorStatus')
            print("existing_trial_status", existing_trial_status)

            #if existing_trial_status == 'NEW':
            throw_next_event = True
            existing_sponsor.put('sponsorStatus', 'LIKED')
            result.put('sponsorStatus', 'LIKED')
            #existing_trial.put('status', 'LIKED')
            self.vault.update('SPONSORS', sponsor_filter, existing_sponsor, False)
            #self.vault.update_all('TRIALS', sponsor_filter, Map.of("sponsorStatus", "LIKED"))

            """ cdn_record = HashMap(result)
                print("CDN Save to 'trials_likes':", cdn_record)
                cdn_record.putAll(self.event_payload)
                self.cdn.save('trials_likes', cdn_record)
                print(f"CDN Save to 'trials_likes': {cdn_record}") """

        result.put('throwNextEvent', throw_next_event)
        result.putAll(self.event_payload)
        print("result", result)

        """  participant_activities_data = {
            'SiteID': self.event_payload.get("SiteID"),
            'NCTId': self.event_payload.get("TrialID"),
            'WalletID': self.node.info().getScAddress(),
            'Action': 'Like',
            'ActionID': str(uuid.uuid1()),
            'ActionRelatedData': "participant likes trial",
            'Date': self.format_to_date_short(self.event_payload.get('createdAt')),
        }
        self.cdn.save('participant_activities', participant_activities_data)
        print("participant_activities saved", participant_activities_data) """
        return result 


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [eh-h-e-w-LIKE-SPONSOR.py]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
