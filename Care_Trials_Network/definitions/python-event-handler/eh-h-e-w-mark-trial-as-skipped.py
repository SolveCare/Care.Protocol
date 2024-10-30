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
            'Oops!',
            'Unfortunately, your criteria didn\'t match our requirement. Please keep swiping.')

    def handle(self) -> Map:
        print(f'==> [eh-h-e-w-mark-trial-as-skipped]: {self.arguments}')
        result = HashMap(self.arguments)

        trial_id = self.event_payload.get("TrialID")
        participant_address = self.event_payload.get("senderNodeAddress")
        print("1.participant addressss from event_payload:", participant_address)
        print("1.trial id from event_payload:", trial_id)

        trial_id_criterion = EqualitySearchFilter.builder().fieldName("TrialID").value(trial_id).build()
        participant_criterion = EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            participant_address).build()

        trial_filter = List.of(trial_id_criterion, participant_criterion)
        existing_trials = self.vault.search('TRIALS_UNIQ', trial_filter)
        print(f'==> [existing trials]: {existing_trials}')
        for existing_trial in existing_trials:
            existing_status = existing_trial.get("trialStatus")
            if existing_status != "BOUGHT":
                existing_trial.put("trialStatus", "SKIPPED")
                # self.send_notification()
                self.vault.update('TRIALS_UNIQ', trial_filter, existing_trial, False)

        print("result", result)
        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [eh-h-e-w-mark-trial-as-skipped]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
