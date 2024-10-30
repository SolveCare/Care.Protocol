import time

import java

from abc import ABC, abstractmethod
from datetime import datetime

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')

NodeInfo = java.type("care.solve.node.core.model.NodeInfo")
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")
NumericBoundsSearchFilter = java.type("care.solve.node.core.model.query.NumericBoundsSearchFilter")
SearchQueryFilter = java.type("care.solve.node.core.model.query.SearchQueryFilter")
Pagination = java.type('care.solve.node.core.model.query.Pagination')
Sorting = java.type('care.solve.node.core.model.query.Sorting')


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

    def update_by_query(self, collection: str, criteria: List, data: Map) -> int:
        vault = self.context.getVaultStorage(collection)
        return vault.update(criteria, data, False, False)

    def search(self, collection: str, criteria: List) -> List:
        vault = self.context.getVaultStorage(collection)
        return vault.search(criteria)

    def search_pageable(self, collection: str, criteria: List, pagination: Pagination) -> List:
        vault = self.context.getVaultStorage(collection)
        return vault.search(criteria, pagination)

    def count(self, collection: str, criteria: List) -> int:
        vault = self.context.getVaultStorage(collection)
        return vault.count(criteria)


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

        self.id_silver_url = 'https://i.ibb.co/QpnCNH9/Silver-ID-small.png'
        self.id_gold_url = 'https://i.ibb.co/Kw3RFKz/Gold-ID-small.png'
        self.id_platinum_url = 'https://i.ibb.co/fxm2fYZ/Platinum-ID-small.png'

        self.medical_silver_url = 'https://i.ibb.co/whbrHDp/Silver-Records-small.png'
        self.medical_gold_url = 'https://i.ibb.co/LPNrPGh/Gold-Records-small.png'
        self.medical_platinum_url = 'https://i.ibb.co/7VMD3wQ/Platinumm-Records-small.png'

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):

    @staticmethod
    def current_milli_time():
        return round(time.time() * 1000)

    def __date_string(self):
        created_at = self.event_payload.get('createdAt')
        if created_at is None:
            created_at = self.current_milli_time()

        if len(str(created_at)) > 10:
            created_at /= 1000

        print("[e-h-n-time-p-to-n.py] created_at: ", created_at)
        date_time = datetime.fromtimestamp(created_at)
        return date_time.strftime('%d-%m-%Y')

    def __is_id_record(self):
        return self.event_payload.get('recordType') == 'ID'

    def __is_medical_record(self):
        return self.event_payload.get('recordType') == 'Medical'

    def __update_id_badge_required(self, value):
        return value != self.id_gold_url and value != self.id_platinum_url

    def __update_medical_badge_required(self, value):
        return value != self.medical_gold_url and value != self.medical_platinum_url

    def __find_questions_data(self) -> List:
        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.node.info().getScAddress()).build())
        pagination = Pagination.of(0, 1, Sorting.desc('createdAt'))
        questions_data_list = self.vault.search_pageable('6_QUESTIONS', vault_filter, pagination)
        print(f'[e-h-n-time-p-to-n.py] Found {len(questions_data_list)} records of 6_QUESTIONS')
        return questions_data_list

    def __find_badges(self) -> List:
        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.node.info().getScAddress()).build())
        pagination = Pagination.of(0, 1)
        badges_list = self.vault.search_pageable('BADGES', vault_filter, pagination)
        print(f'[e-h-n-time-p-to-n.py] Found {len(badges_list)} records of BADGES')
        return badges_list

    def __update_badge_records(self, update_data):
        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.node.info().getScAddress()).build())
        print(f'[e-h-n-time-p-to-n.py] Update BADGES with data: {update_data}')
        updated = self.vault.update_by_query('BADGES', vault_filter, update_data)
        print(f'[e-h-n-time-p-to-n.py] Successfully updated {updated} BADGES')

    def __update_badge_record_if_required(self, badge):
        if self.__is_id_record() and self.__update_id_badge_required(badge.get("IDBadges")):
            update_data = {
                "IDBadges": self.id_silver_url
            }
            self.gold_records_badge_notification()
            self.__update_badge_records(update_data)
        elif self.__is_medical_record() and self.__update_medical_badge_required(badge.get("recordBadges")):
            update_data = {
                "recordBadges": self.medical_silver_url
            }
            self.gold_ID_badge_notification()

            self.__update_badge_records(update_data)

    def __find_trials(self) -> List:
        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.node.info().getScAddress()).build())
        pagination = Pagination.of(0, 1)
        trials_list = self.vault.search_pageable('TRIALS', vault_filter, pagination)
        print(f'[e-h-n-time-p-to-n.py] Found {len(trials_list)} records of TRIALS')
        return trials_list

    def __update_trials(self, update_data):
        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.node.info().getScAddress()).build())
        print(f'[e-h-n-time-p-to-n.py] Update TRIALS with data: {update_data}')
        updated = self.vault.update_by_query('TRIALS', vault_filter, update_data)
        print(f'[e-h-n-time-p-to-n.py] Successfully updated {updated} TRIALS')

    def __update_trials_if_required(self, trial_data):

        if self.__is_id_record() and self.__update_id_badge_required(trial_data.get("IDBadges")):
            update_data = {
                "IDBadges": self.id_silver_url
            }
            self.__update_trials(update_data)
        elif self.__is_medical_record() and self.__update_medical_badge_required(trial_data.get("recordBadges")):
            update_data = {
                "recordBadges": self.medical_silver_url
            }
            self.__update_trials(update_data)

    def __participants_details(self):
        participants_data_list = self.__find_questions_data()
        if len(participants_data_list) > 0:
            participants_data = participants_data_list[0]
            participants_gender = participants_data.get('Gender')
            participants_age = str(participants_data.get('Age')) + " Years"
            participants_details = participants_gender + ", " + participants_age
            print("[e-h-n-time-p-to-n.py] participants_details: ", participants_details)
            return participants_details
        else:
            print("[e-h-n-time-p-to-n.py] No question data found, so participants_details wil be empty")
            return " "

    def __save_records_data(self):
        participants_details = self.__participants_details()
        date_string = self.__date_string()
        data = {
            "time": str(date_string),
            "senderNodeAddress": self.node.info().getScAddress(),
            "recordStatus": "submitted",
            "isRejected": False,
            "timeMessage": "Record submitted on: " + str(date_string),
            "participantDetails": participants_details,
            "folderReference": self.event_payload.get('folderReference'),
            "recordType": self.event_payload.get('recordType'),
            "sendToAdmin": self.event_payload.getOrDefault('sendToAdmin', 'false'),

            "reportTags": "Pending verification",
            "reportType": "Pending verification",
            "recordDate": "Pending verification",
            "comments": "Pending verification",
            "ageOfRecord": "Pending verification"
        }

        print("[e-h-n-time-p-to-n.py] Saving RECORD_DATA: ", data)
        return self.vault.save('RECORD_DATA', data)

    def handle(self) -> Map:
        print("[e-h-n-time-p-to-n.py] Start execution")

        record_data = self.__save_records_data()

        trials_list = self.__find_trials()
        if len(trials_list) > 0:
            self.__update_trials_if_required(trials_list[0])

        badges_list = self.__find_badges()
        if len(badges_list) > 0:
            self.__update_badge_record_if_required(badges_list[0])

        record_data.remove("_id")
        record_data.remove("_revision")
        record_data.remove("_modified")

        print("[e-h-n-time-p-to-n.py] Execution done")
        self.submit_to_nurse_notification()
        return record_data

    def submit_to_nurse_notification(self):
        self.context.getNotificationProvider().send(
            'Congratulations!',
            'You have successfully submitted the records/ID to the nurse.'
        )

    def gold_records_badge_notification(self):
        self.context.getNotificationProvider().send(
            'Congratulations!',
            'You have received a Gold “Records” badge.'
        )

    def gold_ID_badge_notification(self):
        self.context.getNotificationProvider().send(
            'Congratulations!',
            'You have received a Gold “ID” badge.'
        )


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
