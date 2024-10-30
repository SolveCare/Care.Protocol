import java
from datetime import datetime

from abc import ABC, abstractmethod

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
NodeInfo = java.type("care.solve.node.core.model.NodeInfo")



EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")

class Vault:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context
    
    def search(self, collection: str, criteria: List) -> List:
        vault = self.context.getVaultStorage(collection)
        return vault.search(criteria)
    
    def update(self, collection: str, criteria: List, data: Map, insert_if_absent: bool) -> Map:
        vault = self.context.getVaultStorage(collection)
        print(f'==> [CustomPythonEventHandler#data]: {data}')
        guid = vault.update(criteria, data, insert_if_absent)
        print(f'==> [CustomPythonEventHandler#guid]: {guid}')
        return vault.getByGuid(guid)
    
class Node:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def info(self) -> NodeInfo:
        return self.context.getNodeInfo()


class PythonEventHandler(ABC):

    def __init__(self, context: HandlerExecutionContext):
        self.arguments = context.getArguments()
        self.context = context
        self.sender_node_address = context.getEvent().getFrom()
        self.vault = Vault(context)
        self.node = Node(context)


    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):
    def handle(self) -> Map:
        result = HashMap(self.arguments)

        request_filter = EqualitySearchFilter.builder().fieldName("physicianNodeAddress").value(
            self.node.info().getScAddress()).build()
        print("nodeAddress: ", self.node.info().getScAddress())

        vault_filter = List.of(request_filter)
        vault_data = self.vault.search('ENGAGEMENT', vault_filter)
        engagement_count = len(vault_data)

        for item in vault_data:
            item.put("engagementCount", str(engagement_count))
            print("item:", item)

            filter_by_guid = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
                item.get('transactionalGuid')).build())
            updated = self.vault.update('ENGAGEMENT', filter_by_guid, item, False)
            print("UPDATED ENGAGEMENT:", updated)

        self.context.getNotificationProvider().send(
            'Congratulations!',
            'You received an engagement request. Pay attention, you need to respond as soon as possible.')

        print("e-h-n-pi-get-eng-request-notif.py notification sent!")

        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
