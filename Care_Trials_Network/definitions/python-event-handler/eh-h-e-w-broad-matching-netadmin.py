import uuid

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

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):

    def handle(self) -> Map:
        result = HashMap(self.arguments)
        trial_filter = List.of(
            EqualitySearchFilter.builder().fieldName("SiteID").value(self.event_payload.get("SiteID")).build())
        existing_trials = self.vault.search('TRIALS', trial_filter)
        throw_next_event = False
        if len(existing_trials) == 1:
            existing_trial = existing_trials[0]
            result.put("transactionalGuid", existing_trial.get("transactionalGuid"))
            existing_trial_status = existing_trial.get('trialStatus')
            if existing_trial_status == 'NEW':
                throw_next_event = True
        else:
            result.put("transactionalGuid", str(uuid.uuid1()))
        result.put('throwNextEvent', throw_next_event)
        result.putAll(self.event_payload)
        print("result", result)
        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [e-w-broad-matching-netadmin]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
