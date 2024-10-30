from abc import ABC, abstractmethod
import java
import time
import uuid
from datetime import datetime

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
NodeInfo = java.type("care.solve.node.core.model.NodeInfo")
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")

SearchRequest = java.type('care.solve.node.core.model.cdn.SearchRequest')
SearchResponse = java.type('care.solve.node.core.model.cdn.SearchResponse')

QueryCondition = java.type('care.solve.node.core.model.cdn.QueryCondition')
QueryConditions = java.type('care.solve.node.core.model.cdn.QueryConditions')
SimpleQueryBuilder = java.type('care.solve.node.core.model.cdn.SimpleQueryBuilder')
CountResponse = java.type('care.solve.node.core.model.cdn.CountResponse')


class CDN:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def find_first(self, indices: str, parameters: SearchRequest) -> SearchResponse:
        return self.context.getCareDataNodeProvider().findFirst(indices, parameters)

    def raw_search(self, indices: str, from_row, num_rows, search_request) -> List:
        return self.context.getCareDataNodeProvider().rawSearch(indices, from_row, num_rows, search_request)

    def save(self, indices: str, data) -> SearchResponse:
        return self.context.getCareDataNodeProvider().save(indices, data)

    def count(self, indices: str, parameters: SearchRequest) -> CountResponse:
        return self.context.getCareDataNodeProvider().count(indices, parameters)

    def raw_count(self, indices, search_request) -> CountResponse:
        return self.context.getCareDataNodeProvider().rawCount(indices, search_request)


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
        self.event_payload = context.getEvent().getPayload()
        self.cdn = CDN(context)
        self.vault = Vault(context)
        self.node = Node(context)
        self.context = context

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):

    def handle(self) -> Map:
        result = HashMap(self.arguments)
        self.like_trial_notification()
        likes_criteria = SimpleQueryBuilder.eq('senderNodeAddress', self.node.info().getScAddress())
        print("likes_criteria senderNodeAddress", self.node.info().getScAddress())
        likes_count = self.cdn.count('trials_likes', likes_criteria).getTotal()
        print(f'likes_count for badges: {likes_count}')

        if likes_count >= 3:
            badge = 'https://i.ibb.co/Rh4t0wm/Silver-Active-small.png'
            print(f'updated likes badges: {badge}')

            badges = {
                "Badges": badge
            }
            if likes_count == 4:
                self.badge_notification()

            vault_filter_badges = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
                self.node.info().getScAddress()).build())
            self.vault.update('BADGES', vault_filter_badges, badges, False)
            participant_activities_data = {
                'SiteID': self.event_payload.get("SiteID"),
                'NCTId': self.event_payload.get("TrialID"),
                'WalletID': self.node.info().getScAddress(),
                'Action': "Received badge-Silver Active",
                'ActionID': str(uuid.uuid1()),
                'ActionRelatedData': "participant likes campaign",
                'Date': self.format_to_date_short(self.event_payload.get('createdAt')),
            }
            self.cdn.save('participant_activities', participant_activities_data)
            # self.save_participant_data(self,"Received badge-Silver Active")

        return result

    @staticmethod
    def current_milli_time():
        return round(time.time() * 1000)

    @staticmethod
    def format_to_date(timestamp_ms: int) -> str:
        dt_object = datetime.fromtimestamp(timestamp_ms / 1000.0)
        return dt_object.isoformat()

    @staticmethod
    def format_to_date_short(timestamp_ms: int) -> str:
        dt_object = datetime.fromtimestamp(timestamp_ms / 1000.0)
        return dt_object.date().isoformat()

    def save_participant_data(self, action):
        #        if self.__is_id_record():
        #            action = "Upload ID"
        #        elif self.__is_medical_record():
        #            action = "Upload Records"
        #        if self.__update_badge_record_if_required:
        #            action = "Received badge (Record-Silver)"
        #        elif self.__update_id_badge_required:
        #            action = "Received badge (ID-Silver)"
        participant_activities_data = {
            'SiteID': self.event_payload.get("SiteID"),
            'NCTId': self.event_payload.get("TrialID"),
            'WalletID': self.node.info().getScAddress(),
            'Action': action,
            'ActionID': str(uuid.uuid1()),
            'ActionRelatedData': "participant likes campaign",
            'Date': self.format_to_date_short(self.event_payload.get('createdAt')),
        }
        self.cdn.save('participant_activities', participant_activities_data)

    def like_trial_notification(self):
        self.context.getNotificationProvider().send(
            'Great news!',
            'You liked the trial.'
        )

    def badge_notification(self):
        self.context.getNotificationProvider().send(
            'Congratulations!',
            'You have received a Silver “Active” badge.'
        )


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [eh-h-e-w-broad-matching.py]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
