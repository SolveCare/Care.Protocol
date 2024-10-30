import java
import datetime

from datetime import datetime
from abc import ABC, abstractmethod

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
NodeInfo = java.type("care.solve.node.core.model.NodeInfo")
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")
NumericBoundsSearchFilter = java.type("care.solve.node.core.model.query.NumericBoundsSearchFilter")
SearchQueryFilter = java.type("care.solve.node.core.model.query.SearchQueryFilter")


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
        print("Custom event handler e-h-n-sa-submit-record.py.py")

        result = HashMap(self.arguments)

        # count saved trials
        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
            self.event_payload.get('transactionalGuid')).build())
        vault_data = self.vault.search('RECORD_DATA', vault_filter)

        print("SA vault_data", vault_data)
        current_time = datetime.now()
        current_date_string = current_time.strftime('%d-%m-%Y')

        data = {
            "transactionalGuid": self.event_payload.get('transactionalGuid'),
            # "verifiedTime": current_date_string,
            "recordStatus": "submitted",
            "timeMessage": "Submitted on: " + current_date_string
        }

        print("data", data)

        updated = self.vault.update('RECORD_DATA', vault_filter, data, False)

        self.context.initRecipientAddress(updated.get("senderNodeAddress"))
        result.putAll(self.event_payload)
        result.put("participantDetails", updated.get("participantDetails"))
        result.put("senderNodeAddress", updated.get("senderNodeAddress"))
        result.put("timeMessage", updated.get("timeMessage"))
        print("result", result)

        trials_vault_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.node.info().getScAddress()).build())
        trials_vault_data = self.vault.search('TRIALS', trials_vault_filter)

        ID_gold_url = 'https://i.ibb.co/Kw3RFKz/Gold-ID-small.png'
        ID_platinum_url = 'https://i.ibb.co/fxm2fYZ/Platinum-ID-small.png'

        Medical_gold_url = 'https://i.ibb.co/LPNrPGh/Gold-Records-small.png'
        Medical_platinum_url = 'https://i.ibb.co/7VMD3wQ/Platinumm-Records-small.png'

        print("rrrecordType", self.event_payload.get('recordType'))

        if trials_vault_data:
            if self.event_payload.get('recordType') == 'ID' and trials_vault_data[0].get("IDBadges") != ID_platinum_url:
                IDbadge = ID_gold_url
                for item in trials_vault_data:
                    item.put("IDBadges", IDbadge)
                    print("participant_badges", item)
                    filter_by_id = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
                        item.get('transactionalGuid')).build())
                    updated = self.vault.update('TRIALS', filter_by_id, item, False)
                    print("UPDATED TRIAL", updated)
            elif self.event_payload.get('recordType') == 'Medical' and trials_vault_data[0].get(
                    "recordBadges") != Medical_platinum_url:
                recordBadge = Medical_gold_url
                for item in trials_vault_data:
                    item.put("recordBadges", recordBadge)
                    print("participant_badges", item)
                    filter_by_id = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
                        item.get('transactionalGuid')).build())
                    updated = self.vault.update('TRIALS', filter_by_id, item, False)
                    print("UPDATED TRIAL", updated)
            # verified badges done
        vault_filter_badges = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.node.info().getScAddress()).build())
        vault_data_badges = self.vault.search('BADGES', vault_filter_badges)
        print(f'upload record badges: {vault_data_badges}')

        if vault_data_badges:
            print("ppp_vault_IDBadge_0", vault_data_badges[0].get("IDBadges"))
            print("ppp_vault_recodBadge_0", vault_data_badges[0].get("recordBadges"))
            print("type---", self.event_payload.get('recordType'))

            if self.event_payload.get('recordType') == 'ID' and vault_data_badges[0].get("IDBadges") != ID_platinum_url:
                badges = {
                    "IDBadges": ID_gold_url
                }
                self.vault.update('BADGES', vault_filter_badges, badges, False)

                print("ID-----")
            elif self.event_payload.get('recordType') == 'Medical' and vault_data_badges[0].get(
                    "recordBadges") != Medical_platinum_url:
                badges = {
                    "recordBadges": Medical_gold_url
                }
                self.vault.update('BADGES', vault_filter_badges, badges, False)
                print("Medical-----")

        # budget
        vault_filter = List.of(
            EqualitySearchFilter.builder().fieldName("SiteID").value(self.event_payload.get("SiteID")).build())
        print("senderNodeAddress vault_filter", vault_filter)

        vault_budget = self.vault.search('BUDGET', vault_filter)
        print("siteid vault_budget", vault_budget)

        amount_spent = 1000

        if vault_budget:
            for item in vault_budget:
                print("total_expenses ", item.getOrDefault('total_expenses', 0))
                print("remaining_budgett ", item.getOrDefault('remaining_budget', 0))

                data = {
                    "total_expenses": item.getOrDefault('total_expenses', 0) + amount_spent,
                    "remaining_budget": item.getOrDefault('remaining_budget', 0) - amount_spent,
                }
                print("data ", data)
                self.vault.update('BUDGET', vault_filter, data, False)
                print("UPDATED !")

        self.send_debit_notification()
        print("Deducted notification sent!")

        return result
    
    def send_debit_notification(self):
        self.context.getNotificationProvider().send(
            'Congratulations!',
            'Documents have been successfully submitted for review to the nurse. We’ve deducted 1000 SOLVE from your account as payment.'
        )
    def not_enough_solve_notification(self):
        self.context.getNotificationProvider().send(
            'You don’t have enough SOLVE to submit the records/ID.',
            'Please top up your SOLVE balance and try again.'
        )


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
