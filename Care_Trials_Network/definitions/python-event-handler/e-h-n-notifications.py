import java

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
        self.vault = Vault(context)
        self.node = Node(context)

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):

    def handle(self) -> Map:
        result = HashMap(self.arguments)

        # count saved trials
        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.node.info().getScAddress()).build())
        vault_data = self.vault.search('PARTICIPANT_ADMIN_TRIALS_SAVED', vault_filter)
        vault_data_len = len(vault_data)
        vault_data_size = vault_data_len - 1

        sender_criterion = EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.node.info().getScAddress()).build()
        status_criterion = EqualitySearchFilter.builder().fieldName("trialStatus").value("SAVED").build()

        vault_filter_participants_interested = List.of(sender_criterion, status_criterion)
        vault_data_participants_interested = self.vault.search('TRIALS', vault_filter_participants_interested)
        vault_data_participants_interested_len = len(vault_data_participants_interested)
        vault_data_participants_interested_size = vault_data_participants_interested_len - 1

        liked = f"You liked {vault_data_participants_interested_size} Trials \nKeep Swiping"
        matched = f"You Matched with {vault_data_size} Trials"

        data = {
            # "TimeString":time_string,
            "Liked": liked,
            "Matched": matched
        }

        # print("Care.Trial: ", trial)
        self.vault.save('NOTIFICATIONS', data)

        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result