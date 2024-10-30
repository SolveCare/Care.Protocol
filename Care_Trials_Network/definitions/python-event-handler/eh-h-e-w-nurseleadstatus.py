import time

import java
import uuid
from abc import ABC, abstractmethod
from datetime import datetime

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")
SimpleQueryBuilder = java.type('care.solve.node.core.model.cdn.SimpleQueryBuilder')

class CDN:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def find_first(self, indices: str, parameters: SearchRequest) -> SearchResponse:
        return self.context.getCareDataNodeProvider().findFirst(indices, parameters)

    def find_all(self, indices: str, parameters: SearchRequest) -> List:
        return self.context.getCareDataNodeProvider().findAll(indices, parameters)

    def raw_search(self, indices, from_row, num_rows, search_request) -> List:
        return self.context.getCareDataNodeProvider().rawSearch(indices, from_row, num_rows, search_request)

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
        self.cdn = CDN(context)



@abstractmethod
def handle(self) -> Map:
    pass


class CustomPythonEventHandler(PythonEventHandler):

    def handle(self) -> Map:
        print(f'==> [eh-h-e-w-nurse-lead]: {self.arguments}')
        result = HashMap(self.arguments)

        #site_id = self.event_payload.get("SiteID")
        participant_address = self.event_payload.get("senderNodeAddress")

        
        code = self.event_payload.get("Site_UniqueCode")
        
        site_data_list = self.cdn.find_all('trials-with-geo', SimpleQueryBuilder.eq('Site_UniqueCode', code))
        print("site_data_list ", site_data_list)

        if len(site_data_list) == 0:
            return result

        site_data = site_data_list[0].getData()
        trial_id = site_data.get('NCTId')
        site_id = site_data.get('SiteID')
            
            
        print("1.participant addressss from event_payload:", participant_address)
        print("1.site_id from event_payload:", site_id)    
        
        site_id_criterion = EqualitySearchFilter.builder().fieldName("SiteID").value(site_id).build()
        participant_criterion = EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            participant_address).build()
        trial_filter = List.of(site_id_criterion, participant_criterion)
        existing_trials = self.vault.search('TRIALS_SAVED', trial_filter)
        print(f'==> [existing trials]: {existing_trials}')
        for existing_trial in existing_trials:
            existing_status = existing_trial.get("eligibleStatus")
            print("existing_status", existing_status)
            existing_trial.put("eligibleStatus", existing_status)
            self.vault.update('PARTICIPANT_ADMIN_TRIALS', trial_filter, existing_trial, False)
        


        print("result", result)
        #self.send_match_notification()
        #print("match notification sent!")
        return result

    def send_match_notification(self):
        self.context.getNotificationProvider().send(
            'Congratulations!',
            'You are matched with a trial!'
        )


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [eh-h-e-w-nurse-lead]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
