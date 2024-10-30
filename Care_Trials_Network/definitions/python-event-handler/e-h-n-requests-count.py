from abc import ABC, abstractmethod

import java

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
        print(f'==> [CustomPythonEventHandler#data]: {data}')
        guid = vault.update(criteria, data, insert_if_absent)
        print(f'==> [CustomPythonEventHandler#guid]: {guid}')
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
            'You are matched with a trial!')

    def count_records(self, collection: str, trial_id: str) -> int:
        trial_id_criteria = EqualitySearchFilter.builder().fieldName("SiteID").value(trial_id).build()
        sender_filter = EqualitySearchFilter.builder().fieldName("adminNodeAddress").value(
            self.sender_node_address).build()
        records_filter = List.of(trial_id_criteria, sender_filter)
        vault_data = self.vault.search(collection, records_filter)
        count = len(vault_data)
        print(f'Found {count} records in {collection} with SiteID: {trial_id} and '
              f'adminNodeAddress: {self.sender_node_address}')
        return count

    def find_saved_trials(self, trial_id: str) -> List:
        trial_id_criteria = EqualitySearchFilter.builder().fieldName("SiteID").value(trial_id).build()
        sender_filter = EqualitySearchFilter.builder().fieldName("AdminAddress").value(
            self.sender_node_address).build()
        criteria = List.of(trial_id_criteria, sender_filter)
        vault_data = self.vault.search('PARTICIPANT_ADMIN_TRIALS_SAVED', criteria)
        print(f'Found {len(vault_data)} records in PARTICIPANT_ADMIN_TRIALS_SAVED with SiteID: '
              f'{trial_id} and admin: {self.sender_node_address}')
        return vault_data

    def update_saved_trial(self, trial: Map, stat_data: dict):
        trial.put("RecordID_size", stat_data['records_count'])
        trial.put("QA_size", stat_data['qa_count'])
        trial.put("appointments_size", stat_data['appointments_count'])
        trial.put("total_requests", stat_data['total_requests'])

        update_filter = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
            trial.get('transactionalGuid')).build())
        updated = self.vault.update('PARTICIPANT_ADMIN_TRIALS_SAVED', update_filter, trial, False)
        print(f'==> [updated trial]: {updated}')

    @staticmethod
    def readable(count: int) -> str:
        return str(count) if count > 0 else 'No'

    def handle(self) -> Map:
        print("Custom event handler -> [e-h-n-requests-count.py]")
        result = HashMap(self.arguments)

        trial_id = self.event_payload.get("SiteID")
        print(f'Recalculate requests count for SiteID: {trial_id}, sender: {self.sender_node_address}')

        records_count = self.count_records('PARTICIPANT_REQRECORDS', trial_id)
        qa_count = self.count_records('PARTICIPANT_QA', trial_id)
        appointments_count = self.count_records('PARTICIPANT_APPOINTMENT', trial_id)
        total_requests = records_count + qa_count + appointments_count
        print(f'Found {total_requests} records in total with SiteID: {trial_id} and admin: {self.sender_node_address}')

        stat_data = {
            'records_count': self.readable(records_count),
            'qa_count': self.readable(qa_count),
            'appointments_count': self.readable(appointments_count),
            'total_requests': self.readable(total_requests)
        }

        existing_trials = self.find_saved_trials(trial_id)
        for existing_trial in existing_trials:
            self.update_saved_trial(existing_trial, stat_data)

        print("result", result)
        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
