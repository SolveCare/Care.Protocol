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


class PythonEventHandler(ABC):

    def __init__(self, context: HandlerExecutionContext):
        self.arguments = context.getArguments()
        self.event_payload = context.getEvent().getPayload()
        self.vault = Vault(context)

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):

    def update_collection(self, collection_name, row, trial_filter):
        row.put("StudyType", self.event_payload.get('StudyType'))
        row.put("AgeRange", self.event_payload.get('AgeRange'))
        row.put("Gender", self.event_payload.get('Gender'))
        row.put("City", self.event_payload.get('City'))
        row.put("Compensation", self.event_payload.get('Compensation'))
        row.put("TrialDuration", self.event_payload.get('TrialDuration'))
        row.put("Activity", self.event_payload.get('Activity'))
        row.put("Frequency", self.event_payload.get('Frequency'))
        self.vault.update(collection_name, trial_filter, row, False)

    def handle(self) -> Map:
        result = HashMap(self.arguments)

        trial_id = self.event_payload.get("TrialID")
        participant_address = self.event_payload.get("senderNodeAddress")
        trial_id_criterion = EqualitySearchFilter.builder().fieldName("TrialID").value(trial_id).build()
        participant_criterion = EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            participant_address).build()
        trial_filter = List.of(trial_id_criterion, participant_criterion)
        trials = self.vault.search('TRIALS', trial_filter)
        for existing_trial in trials:
            self.update_collection('TRIALS', existing_trial, trial_filter)

        print("result", result)
        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
