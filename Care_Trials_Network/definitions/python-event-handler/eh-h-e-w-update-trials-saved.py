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


class PythonEventHandler(ABC):

    def __init__(self, context: HandlerExecutionContext):
        self.arguments = context.getArguments()
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
            'You have successfully shared the site information with the lead.')

    def handle(self) -> Map:
        result = HashMap(self.arguments)
        trial_id = self.event_payload.get("SiteID")
        participant_address = self.event_payload.get("senderNodeAddress")
        trial_id_criterion = EqualitySearchFilter.builder().fieldName("SiteID").value(trial_id).build()
        participant_criterion = EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            participant_address).build()
        trial_filter = List.of(trial_id_criterion, participant_criterion)
        existing_trials = self.vault.search('PARTICIPANT_ADMIN_TRIALS', trial_filter)
        for existing_trial in existing_trials:
            existing_trial.putAll(self.event_payload)
            updated = self.vault.update('PARTICIPANT_ADMIN_TRIALS_SAVED', trial_filter, existing_trial, False)
            result.put("transactionalGuid", updated.get("transactionalGuid"))
            print(f'==> [updated trial]: {updated}')

        result.putAll(self.event_payload)

        self.send_notification()
        print("Notification sent!")

        print("result", result)
        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [eh-h-e-w-update-trials-saved]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
