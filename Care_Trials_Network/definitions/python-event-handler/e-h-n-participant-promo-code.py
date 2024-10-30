import java
import datetime

from datetime import datetime
from abc import ABC, abstractmethod

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
SearchRequest = java.type('care.solve.node.core.model.cdn.SearchRequest')
SearchResponse = java.type('care.solve.node.core.model.cdn.SearchResponse')
QueryCondition = java.type('care.solve.node.core.model.cdn.QueryCondition')
QueryConditions = java.type('care.solve.node.core.model.cdn.QueryConditions')
SimpleQueryBuilder = java.type('care.solve.node.core.model.cdn.SimpleQueryBuilder')
NodeInfo = java.type("care.solve.node.core.model.NodeInfo")
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")
NumericBoundsSearchFilter = java.type("care.solve.node.core.model.query.NumericBoundsSearchFilter")
SearchQueryFilter = java.type("care.solve.node.core.model.query.SearchQueryFilter")


class CDN:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context
        self.index = 'trials-with-geo'

    def find_all(self, indices: str, parameters: SearchRequest) -> List:
        return self.context.getCareDataNodeProvider().findAll(indices, parameters)

    def find_first(self, parameters: SimpleQueryBuilder) -> SearchResponse:
        transaction_criteria = SimpleQueryBuilder.eq('_transaction_id',
                                                     self.context.getEvent().getPayload().get('transactionId'))
        return self.context.getCareDataNodeProvider().findFirst(self.index, SimpleQueryBuilder.aand(parameters,
                                                                                                    transaction_criteria))

    def raw_search(self, from_row, num_rows, search_request) -> List:
        return self.context.getCareDataNodeProvider().rawSearch(self.index, from_row, num_rows, search_request)

    def update(self, indices: str, identifier: str, data: Map) -> SearchResponse:
        return self.context.getCareDataNodeProvider().update(indices, identifier, data)


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
        self.cdn = CDN(context)
        self.node = Node(context)
        self.context = context

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):

    def handle(self) -> Map:
        print("Custom event handler e-h-n-participant-promo-code-submit-record.py")

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
            "recordStatus": "submitted",
            "timeMessage": "Submitted on: " + current_date_string
        }

        print("data", data)

        promo_code = self.event_payload.get('PromoCode')
        record = self.event_payload.get('folderReference')
        record_type = self.event_payload.get('recordType')

        print('record', record)
        print('recordType', record_type)
        print('PromoCode', promo_code)

        promo_details = self.cdn.find_all('promo_activities', SimpleQueryBuilder.eq('Code', promo_code))
        print('promo_details', promo_details)
        print('len(promo_details)', len(promo_details))

        if promo_details:
            promo = 1
            total_solve = promo_details[0].getData().get('TotalAmount')
            available_solve = promo_details[0].getData().get('AvailableAmount')
            status = promo_details[0].getData().get('Status')
            print('promo_solve', total_solve)
            print('available_solve', available_solve)
        else:
            promo = 0
            self.wrong_promo_notification()

        if promo_details:
            if status == "IN_USE":
                print("Promo code is already in use")
                self.used_promo_notification()                
                balance = 0

            elif total_solve <= available_solve:
                print("Enough SOLVE available")
                balance_solve = available_solve - total_solve
                print("balance_solve", balance_solve)
                self.enough_solve_notification()
                balance = 1
                for row in promo_details:
                    update_data = Map.of('Status', 'IN_USE')
                    self.cdn.update('promo_activities', row.getId(), update_data)

            elif total_solve > available_solve:
                print("Enough SOLVE not available")
                self.not_enough_solve_notification()
                balance = 0

        if promo and balance:
            print("promo and balance")
            updated = self.vault.update('RECORD_DATA', vault_filter, data, False)

            self.context.initRecipientAddress(updated.get("senderNodeAddress"))
            result.putAll(self.event_payload)
            print("resultttt",result)
            result.put("participantDetails", updated.get("participantDetails"))
            result.put("senderNodeAddress", updated.get("senderNodeAddress"))
            result.put("timeMessage", updated.get("timeMessage"))
            result.put("reviewPayWith", "promocode")
            #result.put("PromoCode", "promocode")


            print("result", result)

            # Add submit badges

            trials_vault_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
                self.node.info().getScAddress()).build())
            trials_vault_data = self.vault.search('TRIALS', trials_vault_filter)

            # Badges criteria
            id_gold_url = 'https://i.ibb.co/Kw3RFKz/Gold-ID-small.png'
            id_platinum_url = 'https://i.ibb.co/fxm2fYZ/Platinum-ID-small.png'

            medical_gold_url = 'https://i.ibb.co/LPNrPGh/Gold-Records-small.png'
            medical_platinum_url = 'https://i.ibb.co/7VMD3wQ/Platinumm-Records-small.png'

            print("rrrecordType", self.event_payload.get('recordType'))

            if trials_vault_data:
                if self.event_payload.get('recordType') == 'ID' and trials_vault_data[0].get(
                        "IDBadges") != id_platinum_url:
                    id_badge = id_gold_url
                    for item in trials_vault_data:
                        item.put("IDBadges", id_badge)
                        print("participant_badges", item)
                        filter_by_id = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
                            item.get('transactionalGuid')).build())
                        updated = self.vault.update('TRIALS', filter_by_id, item, False)
                        print("UPDATED TRIAL", updated)

                elif self.event_payload.get('recordType') == 'Medical' and trials_vault_data[0].get(
                        "recordBadges") != medical_platinum_url:
                    record_badge = medical_gold_url
                    for item in trials_vault_data:
                        item.put("recordBadges", record_badge)
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

                if self.event_payload.get('recordType') == 'ID' and vault_data_badges[0].get(
                        "IDBadges") != id_platinum_url:
                    badges = {
                        "IDBadges": id_gold_url
                    }
                    self.vault.update('BADGES', vault_filter_badges, badges, False)

                    print("ID-----")

                elif self.event_payload.get('recordType') == 'Medical' and vault_data_badges[0].get(
                        "recordBadges") != medical_platinum_url:
                    badges = {
                        "recordBadges": medical_gold_url
                    }
                    self.vault.update('BADGES', vault_filter_badges, badges, False)
                    print("Medical-----")

        return result

    def not_enough_solve_notification(self):
        self.context.getNotificationProvider().send(
            'You don’t have enough SOLVE to submit the records/ID.',
            'Please top up your SOLVE balance and try again.'
        )

    def enough_solve_notification(self):
        self.context.getNotificationProvider().send(
            'Congratulations!',
            'You have successfully submitted the records/ID to the nurse.'
        )

    def wrong_promo_notification(self):
        self.context.getNotificationProvider().send(
            'Oops!',
            'It appears the code you entered is invalid, and as a result, your records were not submitted successfully. Please double-check the code and try submitting again.'
        )
    def used_promo_notification(self):
        self.context.getNotificationProvider().send(
            'Oops!',
            'It appears the code you entered is already used, and as a result, your records were not submitted successfully. Please use a different code and try submitting again.'
        )    


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
