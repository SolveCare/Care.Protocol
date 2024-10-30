import time
import uuid

from abc import ABC, abstractmethod
from datetime import datetime

import java

from abc import ABC, abstractmethod
from datetime import datetime

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")

SearchRequest = java.type('care.solve.node.core.model.cdn.SearchRequest')
SearchResponse = java.type('care.solve.node.core.model.cdn.SearchResponse')
CountResponse = java.type('care.solve.node.core.model.cdn.CountResponse')
SimpleQueryBuilder = java.type('care.solve.node.core.model.cdn.SimpleQueryBuilder')


class CDN:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def find_first(self, indices: str, parameters: SearchRequest) -> SearchResponse:
        return self.context.getCareDataNodeProvider().findFirst(indices, parameters)

    def raw_search(self, indices: str, from_row, num_rows, search_request) -> List:
        return self.context.getCareDataNodeProvider().rawSearch(indices, from_row, num_rows, search_request)

    def save(self, indices: str, data) -> SearchResponse:
        return self.context.getCareDataNodeProvider().save(indices, data)

    def count(self, indices: str, parameters: SearchRequest) -> CountResponse:
        return self.context.getCareDataNodeProvider().count(indices, parameters)


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
        self.cdn = CDN(context)

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
        # return dt_object.strftime("%m/%d/%Y")
        return dt_object.isoformat()

    @staticmethod
    def formatted_date_short() -> str:
        dt_object = datetime.fromtimestamp(time.time())
        return dt_object.date().isoformat()

    @staticmethod
    def format_to_date_short(timestamp_ms: int) -> str:
        dt_object = datetime.fromtimestamp(timestamp_ms / 1000.0)
        # return dt_object.strftime("%m/%d/%Y")
        return dt_object.date().isoformat()

    def __no_participant_activity_saved(self, site_id: str, wallet_id: str) -> int:
        action_filter = SimpleQueryBuilder.eq('Action', 'View')
        wallet_id_filter = SimpleQueryBuilder.eq('WalletID', wallet_id)
        site_id_filter = SimpleQueryBuilder.eq('SiteID', site_id)
        activities_filter = SimpleQueryBuilder.aand(action_filter, wallet_id_filter, site_id_filter)
        return self.cdn.count('participant_activities', activities_filter).getTotal() == 0

    def __save_participant_activity(self):
        site_id = self.event_payload.get('SiteID')
        wallet_id = self.event_payload.get('senderNodeAddress')
        if self.__no_participant_activity_saved(site_id, wallet_id):
            participant_activities_data = {
                'SiteID': site_id,
                'NCTId': self.event_payload.get("TrialID"),
                'WalletID': wallet_id,
                'Action': 'View',
                'ActionID': str(uuid.uuid1()),
                'ActionRelatedData': 'admin view lead',
                'Date': self.formatted_date_short(),
            }
            self.cdn.save('participant_activities', participant_activities_data)
            print("participant_activities saved", participant_activities_data)

    def handle(self) -> Map:
        print(f'==> [eh-h-e-w-mark-lead-as-bought-1]: {self.arguments}')
        result = HashMap(self.arguments)

        trial_id = self.event_payload.get("SiteID")
        participant_address = self.event_payload.get("senderNodeAddress")
        trial_id_criterion = EqualitySearchFilter.builder().fieldName("SiteID").value(trial_id).build()
        participant_criterion = EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            participant_address).build()
        trial_filter = List.of(trial_id_criterion, participant_criterion)
        print(f'==> [eh-h-e-w-mark-lead-as-bought-2]: {trial_id}')
        print(f'==> [eh-h-e-w-mark-lead-as-bought-2]: {participant_address}')
        existing_trials = self.vault.search('PARTICIPANT_ADMIN_TRIALS', trial_filter)
        print(f'==> [eh-h-e-w-mark-lead-as-bought-3]: {existing_trials}')
        for existing_trial in existing_trials:
            existing_trial.putAll(self.event_payload)
            existing_trial.put("RecordID_size", "0")
            existing_trial.put("QA_size", "0")
            existing_trial.put("appointments_size", "0")
            existing_trial.put("total_requests", "0")
            existing_trial.put("trialStatus", "BOUGHT")
            updated = self.vault.update('PARTICIPANT_ADMIN_TRIALS', trial_filter, existing_trial, False)
            existing_trial.remove("isSubscriptionActive")
            self.vault.update('PARTICIPANT_ADMIN_TRIALS_SAVED', trial_filter, existing_trial, True)
            result.put("transactionalGuid", updated.get("transactionalGuid"))
            print(f'==> [updated trial]: {updated}')

        self.__save_participant_activity()

        result.putAll(self.event_payload)
        print("result", result)
        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [eh-h-e-w-mark-lead-as-bought]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
