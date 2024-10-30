import java

from abc import ABC, abstractmethod
from datetime import datetime

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
NodeInfo = java.type("care.solve.node.core.model.NodeInfo")
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")
List = java.type('java.util.List')


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
        self.node = Node(context)
        self.context = context

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):

    def handle(self) -> Map:
        result = HashMap(self.arguments)
        result.putAll(self.event_payload)

        
        participantNodeAddress = self.event_payload.get('senderNodeAddress')
        adminNodeAddress = self.event_payload.get('adminNodeAddress')
        
        print(f'==> [participantNodeAddress]: {participantNodeAddress}')
        print(f'==> [adminNodeAddress]: {adminNodeAddress}')
        print(f'==> [self.node.info().getScAddress()]: {self.node.info().getScAddress()}')
        
        
        leadNodeAddress = self.event_payload.get('leadNodeAddress')
        print(f'==> [leadNodeAddress]: {leadNodeAddress}')

        lead_filter = List.of(EqualitySearchFilter.builder().fieldName("leadNodeAddress").value(leadNodeAddress).build())
        appt_filter = List.of(EqualitySearchFilter.builder().fieldName("apptInfo").value(self.event_payload.get('apptInfo')).build())
        
        vault_filter = List.of(
            EqualitySearchFilter.builder().fieldName("SiteID").value(self.event_payload.get('SiteID')).build(),
            EqualitySearchFilter.builder().fieldName("apptInfo").value(self.event_payload.get('apptInfo')).build(),
            EqualitySearchFilter.builder().fieldName("apptPurpose").value(self.event_payload.get('apptPurpose')).build())
       
        vault_data = self.vault.search('TRIAL_ADMIN_APPOINTMENT', vault_filter)
        print("apptInfo", self.event_payload.get('apptInfo'))
        print("vault_data", vault_data)
                
        data = {
            "isApptStatus": False,
            "isApptStatusNot": True,
            "submittedAt" : "Accepted on: " + datetime.now().strftime("%d/%m/%Y"),
            "statusIcon": "https://i.ibb.co/jWWybCB/Status.png"
        }
        print("data ", data)
        
        updated = self.vault.update('TRIAL_ADMIN_APPOINTMENT', vault_filter, data, False)
        print("TRIAL_ADMIN_APPOINTMENT updated", updated)

        result.putAll(self.event_payload)
        print("result accept appt", result)

        
        if adminNodeAddress == self.node.info().getScAddress():
            self.context.getNotificationProvider().send(
                'Great news!',
                'The lead has accepted your appointment request.')

            print("appt accepted notification received by SA!")

        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
