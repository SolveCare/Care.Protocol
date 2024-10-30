import java

from abc import ABC, abstractmethod

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
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

    def remove(self, collection: str, guid: str):
        vault = self.context.getVaultStorage(collection)
        vault.delete(guid)


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

    def handle(self) -> Map:
        result = HashMap(self.arguments)

        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
            self.event_payload.get("senderNodeAddress")).build())
        vault_data = self.vault.search('RECORD', vault_filter)

        if self.event_payload.get("sendToAdmin") == "True":
            result.put("transactionalGuid", vault_data.get("transactionalGuid"))
            # result.put('throwNextEvent', throw_next_event)
            result.putAll(self.event_payload)

        print("result", result)
        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result


# def send_join_bonus_notification(self: HandlerExecutionContext):
#     self.getNotificationProvider().send(
#         'Congratulations!',
#         'You will receive 100 SOLVE tokens within 72 hours for joining Care.Trials network')


# def send_referral_bonus_notification(self: HandlerExecutionContext):
#     self.getNotificationProvider().send(
#         'Congratulations!',
#         'You will receive 20 SOLVE tokens within 72 hours for joining Care.Trials network using a referral code')


def send_trials_found_notification(self: HandlerExecutionContext, count):
    self.getNotificationProvider().send(
        'Great news!',
        f'There are {count} trials found matching your search criteria. You can start swiping trials now.')


def send_trials_not_found_notification(self: HandlerExecutionContext):
    self.getNotificationProvider().send(
        'No matches this time',
        'It is recommended to increase the distance radius of your search.')
