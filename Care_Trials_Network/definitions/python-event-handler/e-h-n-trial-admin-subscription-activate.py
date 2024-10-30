from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import uuid

import java

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
NodeInfo = java.type("care.solve.node.core.model.NodeInfo")
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")

SearchRequest = java.type('care.solve.node.core.model.cdn.SearchRequest')
SearchResponse = java.type('care.solve.node.core.model.cdn.SearchResponse')
CountResponse = java.type('care.solve.node.core.model.cdn.CountResponse')
SimpleQueryBuilder = java.type('care.solve.node.core.model.cdn.SimpleQueryBuilder')


class CDN:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def find_first(self, indices: str, parameters: SearchRequest) -> SearchResponse:
        return self.context.getCareDataNodeProvider().findFirst(indices, parameters)

    def count(self, indices: str, parameters: SearchRequest) -> CountResponse:
        return self.context.getCareDataNodeProvider().count(indices, parameters)

    def find_all(self, indices: str, parameters: SearchRequest) -> List:
        return self.context.getCareDataNodeProvider().findAll(indices, parameters)

    def raw_search(self, indices, from_row, num_rows, search_request) -> List:
        return self.context.getCareDataNodeProvider().rawSearch(indices, from_row, num_rows, search_request)

    def raw_count(self, indices, search_request) -> CountResponse:
        return self.context.getCareDataNodeProvider().rawCount(indices, search_request)

    def save(self, indices: str, data) -> SearchResponse:
        return self.context.getCareDataNodeProvider().save(indices, data)

    def update(self, indices: str, identifier: str, data) -> SearchResponse:
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
        self.event_payload = context.getEvent().getPayload()
        self.vault = Vault(context)
        self.cdn = CDN(context)
        self.node = Node(context)

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):

    @staticmethod
    def format_to_date_short(timestamp_ms: int) -> str:
        dt_object = datetime.fromtimestamp(timestamp_ms / 1000.0)
        return dt_object.date().isoformat()

    @staticmethod
    def plus_year(timestamp_ms: int) -> int:
        dt_object = datetime.fromtimestamp(timestamp_ms / 1000.0)
        one_year_later = dt_object + timedelta(days=365)
        return int(one_year_later.timestamp() * 1000)

    def activate_subscription(self) -> Map:
        print(f'==> [trial-admin-subscription-activate]: arguments: {self.arguments}')

        subscription_id = self.event_payload.get('transactionalGuid')
        id_criteria = EqualitySearchFilter.builder().fieldName("transactionalGuid").value(subscription_id).build()
        site_id = self.event_payload.get('SiteID')
        site_id_criteria = EqualitySearchFilter.builder().fieldName("SiteID").value(site_id).build()
        subscription_filter = List.of(id_criteria, site_id_criteria)
        subscription = self.vault.search('TRIAL_ADMIN_SUBSCRIPTION', subscription_filter)[0]
        print(f'==> [trial-admin-subscription-activate]: For {site_id} found subscription: {subscription}')

        expire_at = self.plus_year(subscription.get('createdAt'))

        subscription.put('paidByNodeAddress', self.event_payload.get('paidByNodeAddress'))
        subscription.put('totalSolveCost', self.event_payload.get('totalSolveCost'))
        subscription.put('paymentStatus', self.event_payload.get('paymentStatus'))
        subscription.put('status', 'Active')
        subscription.put('isSubscriptionActive', True)
        subscription.put('expireAt', expire_at)
        subscription.put('expireAtText', self.format_to_date_short(expire_at))

        updated = self.vault.update('TRIAL_ADMIN_SUBSCRIPTION', subscription_filter, subscription, False)
        print(f'==> [trial-admin-subscription-activate]: Updated subscription: {updated}')

        sites = self.vault.search('TRIALS', List.of(site_id_criteria))
        for trial in sites:
            trial.put("isSubscriptionActive", True)
            trial.put("isSubscriptionNotActive", False)
            guid_criteria = (EqualitySearchFilter.builder()
                             .fieldName("transactionalGuid")
                             .value(trial.get('transactionalGuid')).build())
            self.vault.update('TRIALS', List.of(guid_criteria), trial, False)

        subscription_activities_data = {
            'SiteID': self.event_payload.get('SiteID'),
            'NCTId': self.event_payload.get('TrialID'),
            'SubscriptionType': 'Subscription',
            'StartDate': self.format_to_date_short(subscription.get('createdAt')),
            'EndDate': self.format_to_date_short(expire_at),
            'Amount': self.event_payload.get('totalSolveCost'),
            'SubscriptionID': subscription_id,
            'OwnerNodeScAddress': self.node.info().getScAddress()
        }

        self.cdn.save('subscription_activities', subscription_activities_data)
        print(f"CDN Save to 'subscription_activities': {subscription_activities_data}")
        print("subscription_activities saved", subscription_activities_data)

        return updated

    def update_leads(self, subscription: Map):
        trial_id = subscription.get("SiteID")
        trial_id_criterion = EqualitySearchFilter.builder().fieldName("SiteID").value(trial_id).build()
        existing_trials = self.vault.search('PARTICIPANT_ADMIN_TRIALS', List.of(trial_id_criterion))
        print(f'==> [trial-admin-subscription-activate]: Found {len(existing_trials)} leads with {trial_id}')
        for existing_trial in existing_trials:
            existing_trial.put("isSubscriptionActive", True)
            existing_trial_id = existing_trial.get('transactionalGuid')
            id_criteria = EqualitySearchFilter.builder().fieldName("transactionalGuid").value(existing_trial_id).build()
            self.vault.update('PARTICIPANT_ADMIN_TRIALS', List.of(id_criteria), existing_trial, False)
            print(f'==> [trial-admin-subscription-activate]: Updated lead {existing_trial_id}')

    def handle(self) -> Map:
        result = HashMap(self.arguments)
        subscription = self.activate_subscription()
        self.update_leads(subscription)
        print("result", result)
        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [eh-h-e-w-mark-lead-as-bought]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
