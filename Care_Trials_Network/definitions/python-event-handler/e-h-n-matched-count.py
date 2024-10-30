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
        trial_id_criteria = EqualitySearchFilter.builder().fieldName("trialStatus").value("BOUGHT").build()
        sender_filter = EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.sender_node_address).build()
        records_filter = List.of(trial_id_criteria, sender_filter)
        vault_data = self.vault.search(collection, records_filter)
        count = len(vault_data)
        print(f'Found {count} records in {collection} with trial status: "BOUGHT" and '
              f'senderNodeAddress: {self.sender_node_address}')
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
        print("Custom event handler -> [e-h-n-matched-count.py]")
        result = HashMap(self.arguments)

        trial_id = self.event_payload.get("SiteID")
        sender_filter = EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(self.sender_node_address).build()
        parti_filter = EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(self.event_payload.get("senderNodeAddress")).build()
        
        print("sender_filter:", sender_filter)
        print("parti_filter", parti_filter)
        
        print("self.sender_node_address", self.sender_node_address)        
        print("self.event_payload.get(senderNodeAddress):", self.event_payload.get("senderNodeAddress"))
        
        skipped_criteria = EqualitySearchFilter.builder().fieldName("trialStatus").value("SKIPPED").build()        
        skipped_filter = List.of(skipped_criteria, parti_filter)
        skipped_data = self.vault.search('TRIALS_UNIQ', skipped_filter)
        skipped_count = len(skipped_data) 
        
        bought_criteria = EqualitySearchFilter.builder().fieldName("trialStatus").value("BOUGHT").build()        
        bought_filter = List.of(bought_criteria, parti_filter)
        bought_data = self.vault.search('TRIALS_UNIQ', bought_filter)
        bought_count = len(bought_data) 
        
        #bought_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(parti_filter).build())
        #bought_data = self.vault.search('PARTICIPANT_ADMIN_TRIALS_SAVED', bought_filter)
        #bought_count = len(bought_data) 
       
        noresponse_criteria = EqualitySearchFilter.builder().fieldName("trialStatus").value("SAVED").build() 
        liked_criteria = EqualitySearchFilter.builder().fieldName("status").value("LIKED").build()   
        noresponse_filter = List.of(noresponse_criteria, liked_criteria, parti_filter)
        noresponse_data = self.vault.search('TRIALS_UNIQ', noresponse_filter)
        noresponse_count = len(noresponse_data) 
       
        

        total_matched = bought_count
        total_notfit = skipped_count
        total_noresponse = noresponse_count
        print(f'total_matched {total_matched} for {parti_filter}')
        print(f'total_notfit {total_notfit} for {parti_filter}')
        print(f'total_noresponse {total_noresponse} for {parti_filter}')

        data = {
            'total_matched': str(total_matched),
            'total_notfit': str(total_notfit),
            'total_noresponse': str(total_noresponse),
            'senderNodeAddress': self.event_payload.get("senderNodeAddress")
        }
        print(f'total_matched data: {data}')

        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(self.event_payload.get("senderNodeAddress")).build())
        participant_trials = self.vault.search('PARTICIPANT_TRIALS', List.of(parti_filter))
        print(f'==> [participant_trials...matched]: {participant_trials}')
        
        if participant_trials:
            print(f'==> [participant_trials]: {participant_trials}')
            #participant_trial = participant_trials[0]
            #participant_trial.putAll(data)
            updated = self.vault.update('PARTICIPANT_TRIALS', List.of(parti_filter), data, False)
            print(f'==> [updated trial]: {updated}')
        else:
            self.vault.save('PARTICIPANT_TRIALS', data)
            print(f'==> [saved trial]: {data}')

        print("result", result)
        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
