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
        sender_criterion = EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.node.info().getScAddress()).build()
        status_criterion = EqualitySearchFilter.builder().fieldName("trialStatus").value("SAVED").build()

        vault_filter = List.of(sender_criterion, status_criterion)

        vault_data = self.vault.search('TRIALS', vault_filter)
        print("VaultData", vault_data)

        vd_size = len(vault_data)
        print("vd_size: ", vd_size)
        clicks = vd_size - 1
        print("clicks: ", clicks)

        # Badges criteria
        if clicks >= 3:
            # badge = 'https://i.ibb.co/D1jCLDT/Silver.png'
            badge = 'https://i.ibb.co/Rh4t0wm/Silver-Active-small.png'

        else:
            # badge = 'https://i.ibb.co/pxX91Jv/Bronze-badge-Active.png'
            badge = 'https://i.ibb.co/d6VdwVh/Bronze-active-small.png'

        for item in vault_data:
            item.put("Badges", badge)
            print("participant_badges", item)
            filter_by_id = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
                item.get('transactionalGuid')).build())
            updated = self.vault.update('TRIALS', filter_by_id, item, False)
            print("UPDATED TRIAL", updated)

            # print("Care.Trial: ", trial)
            # self.vault.save('TRIALS', trial)

        result.put("Badges", badge)
        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
