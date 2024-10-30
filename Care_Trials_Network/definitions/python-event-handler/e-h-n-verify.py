import java
import time
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

    def update_collection(self, collection_name, row, trial_filter) -> Map:

        current_time = datetime.now()
        current_date_string = current_time.strftime('%d-%m-%Y')

        row.put("participantLastName", self.event_payload.get('participantLastName'))
        row.put("participantFirstName", self.event_payload.get('participantFirstName'))
        row.put("reportType", self.event_payload.get('reportType'))
        row.put("reportTags", self.event_payload.get('reportTags'))
        row.put("ageOfRecord", self.event_payload.get('ageOfRecord'))
        row.put("recordDate", self.event_payload.get('recordDate'))
        row.put("comments", self.event_payload.get('comments'))
        row.put("recordStatus", "verified")
        row.put("isRejected", False)
        row.put("timeMessage", "Verified on: " + current_date_string)

        self.vault.update(collection_name, trial_filter, row, False)
        return row

    def handle(self) -> Map:
        print("Custom event handler--verify.pyyy")

        result = HashMap(self.arguments)

        # count saved trials
        # vault_filter = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(self.event_payload.get('transactionalGuid')).build())
        # vault_data = self.vault.search('RECORD_DATA', vault_filter)
        # vault_data_len= len(vault_data)
        # vault_data_size=vault_data_len-1
        transaction_criterion = EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
            self.event_payload.get("transactionalGuid")).build()
        vault_filter = List.of(transaction_criterion)
        vault_data = self.vault.search('RECORD_DATA', vault_filter)
        for data in vault_data:
            updated = self.update_collection('RECORD_DATA', data, vault_filter)
            print("data before cleanup", updated)
            self.context.initRecipientAddress(updated.get('senderNodeAddress'))
            updated.remove("_id")
            updated.remove("_revision")
            updated.remove("_modified")
            updated.remove("senderNodeAddress")
            updated.remove("sendToAdmin")
            updated.remove("recordAge")
            print("verifyyy data", updated)
            return updated

        # Add verified badges

        # sender_criterion = EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(self.node.info().getScAddress()).build()
        # status_criterion = EqualitySearchFilter.builder().fieldName("trialStatus").value("SAVED").build()
        # trials_vault_filter = List.of(sender_criterion, status_criterion)
        # trials_vault_data = self.vault.search('TRIALS', trials_vault_filter)

        # #parti_ans_vault_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(self.node.info().getScAddress()).build())
        # #parti_ans_vault_data = self.vault.search('td-PARTICIPANT_ANSWERS', parti_ans_vault_filter)

        trials_vault_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.node.info().getScAddress()).build())
        trials_vault_data = self.vault.search('TRIALS', trials_vault_filter)

        # print("VaultData", trials_vault_data)

        # Badges criteria

        # ID_bronze_url = 'https://i.ibb.co/stSV6pW/Bronze-3.png'
        # ID_silver_url = 'https://i.ibb.co/smhcfHv/Silver-ID.png'
        # ID_gold_url = 'https://i.ibb.co/Tk9LjqR/Gold-ID.png'
        # ID_platinum_url = 'https://i.ibb.co/H4WmjyK/Platinum-ID.png'

        # Medical_bronze_url = 'https://i.ibb.co/xDrnjVy/Bronze-2.png'
        # Medical_silver_url = 'https://i.ibb.co/bNJ6v9q/Silver-records.png'
        # Medical_gold_url = 'https://i.ibb.co/6Xj71BH/Gold-Records.png'
        # Medical_platinum_url = 'https://i.ibb.co/RNf4gMz/Platinum-medical.png'

        ID_bronze_url = 'https://i.ibb.co/0y0SXMt/Bronze-ID-small.png'
        ID_silver_url = 'https://i.ibb.co/QpnCNH9/Silver-ID-small.png'
        ID_gold_url = 'https://i.ibb.co/Kw3RFKz/Gold-ID-small.png'
        ID_platinum_url = 'https://i.ibb.co/fxm2fYZ/Platinum-ID-small.png'

        Medical_bronze_url = 'https://i.ibb.co/JRXBHJf/Bronze-medical-small.png'
        Medical_silver_url = 'https://i.ibb.co/whbrHDp/Silver-Records-small.png'
        Medical_gold_url = 'https://i.ibb.co/LPNrPGh/Gold-Records-small.png'
        Medical_platinum_url = 'https://i.ibb.co/7VMD3wQ/Platinumm-Records-small.png'

        if trials_vault_data:
            if self.event_payload.get('recordType') == 'ID':
                IDbadge = ID_platinum_url
                for item in trials_vault_data:
                    item.put("IDBadges", IDbadge)
                    print("participant_badges", item)
                    filter_by_id = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
                        item.get('transactionalGuid')).build())
                    updated = self.vault.update('TRIALS', filter_by_id, item, False)
                    print("UPDATED TRIAL", updated)



            elif self.event_payload.get('recordType') == 'Medical':
                recordBadge = Medical_platinum_url
                for item in trials_vault_data:
                    item.put("recordBadges", recordBadge)
                    print("participant_badges", item)
                    filter_by_id = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
                        item.get('transactionalGuid')).build())
                    updated = self.vault.update('TRIALS', filter_by_id, item, False)
                    print("UPDATED TRIAL", updated)

            # vault_filter_badges = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(self.node.info().getScAddress()).build())
            # vault_data_badges = self.vault.search('BADGES', vault_filter_badges)
            # print(f'upload record badges: {vault_data_badges}')

            # if vault_data_badges:
            #     print("ppp_vault_IDBadge_0",  vault_data_badges[0].get("IDBadges"))
            #     print("ppp_vault_recodBadge_0",  vault_data_badges[0].get("recordBadges"))
            #     print("type---",self.event_payload.get('recordType'))

            #     if self.event_payload.get('recordType') == 'ID':
            #         badges = {
            #             "IDBadges": ID_platinum_url
            #         }
            #         self.vault.update('BADGES', vault_filter_badges, badges, False)   
            #         print("ID-----")

            #     elif self.event_payload.get('recordType') == 'Medical':
            #         badges = {
            #             "recordBadges": Medical_platinum_url
            #         }
            #         self.vault.update('BADGES', vault_filter_badges, badges, False)   
            #         print("Medical-----")


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
