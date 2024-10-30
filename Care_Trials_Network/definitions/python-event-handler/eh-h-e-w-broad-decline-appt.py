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


QueryCondition = java.type('care.solve.node.core.model.cdn.QueryCondition')
QueryConditions = java.type('care.solve.node.core.model.cdn.QueryConditions')
SimpleQueryBuilder = java.type('care.solve.node.core.model.cdn.SimpleQueryBuilder')
NodeInfo = java.type("care.solve.node.core.model.NodeInfo")
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")
NumericBoundsSearchFilter = java.type("care.solve.node.core.model.query.NumericBoundsSearchFilter")
SearchQueryFilter = java.type("care.solve.node.core.model.query.SearchQueryFilter")


    
    
    
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
    



class CustomPythonEventHandler(PythonEventHandler):

    def handle(self) -> Map:
        result = HashMap(self.arguments)
        
        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(self.event_payload.get('transactionalGuid')).build())
        vault_data = self.vault.search('PARTICIPANT_APPOINTMENT', vault_filter)
        print("tranactionalGuid", self.event_payload.get('transactionalGuid'))
        print("vault_data", vault_data)
                
        data = {
            "isApptStatus": False,
            "isApptStatusNot": True,
            "submittedAt" : "Declined on: " + datetime.now().strftime("%d/%m/%Y"),
            "statusIcon": "https://i.ibb.co/Ln0GPf6/Decline-Icon.png"

        }
        print("data ", data)
        
        updated = self.vault.update('PARTICIPANT_APPOINTMENT', vault_filter, data, False)
        print("PARTICIPANT_APPOINTMENT updated", updated)
        
        
        result.putAll(self.event_payload)


        print("appt declined notification sent to SA!")
        
        print("result", result)
        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result