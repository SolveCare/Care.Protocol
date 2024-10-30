import time
from abc import ABC, abstractmethod
from datetime import datetime

import java

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
NodeInfo = java.type("care.solve.node.core.model.NodeInfo")
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")
SearchResponse = java.type('care.solve.node.core.model.cdn.SearchResponse')
SearchRequest = java.type('care.solve.node.core.model.cdn.SearchRequest')
SimpleQueryBuilder = java.type('care.solve.node.core.model.cdn.SimpleQueryBuilder')


class CDN:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def find_first(self, indices: str, parameters: SearchRequest) -> SearchResponse:
        return self.context.getCareDataNodeProvider().findFirst(indices, parameters)

    def raw_search(self, indices: str, from_row, num_rows, search_request) -> List:
        return self.context.getCareDataNodeProvider().rawSearch(indices, from_row, num_rows, search_request)

    def save(self, indices: str, data) -> SearchResponse:
        return self.context.getCareDataNodeProvider().save(indices, data)


class Vault:

    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def save(self, collection: str, data: Map) -> Map:
        vault = self.context.getVaultStorage(collection)
        guid = vault.save(data)
        return vault.getByGuid(guid)

    def update(self, collection: str, criteria: List, data: Map, insert_if_absent: bool) -> Map:
        vault = self.context.getVaultStorage(collection)
        print(f'==> [CustomPythonEventHandler#pre_update] {collection}, criteria: {criteria}, data: {data}')
        guid = vault.update(criteria, data, insert_if_absent)
        print(f'==> [CustomPythonEventHandler#post_update] {collection}: guid:{guid}')
        return vault.getByGuid(guid)

    def search(self, collection: str, criteria: List) -> List:
        vault = self.context.getVaultStorage(collection)
        return vault.search(criteria)

    def remove(self, collection: str, guid: str):
        vault = self.context.getVaultStorage(collection)
        vault.delete(guid)


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

    def find_campaign(self) -> Map:
        campaign_id = self.event_payload.get('transactionalGuid')
        filter_by_id = List.of(EqualitySearchFilter.builder().fieldName('transactionalGuid').value(campaign_id).build())
        saved_campaign_data = self.vault.search('TRIAL_ADMIN_CAMPAIGN', filter_by_id)
        print(f'Search TRIAL_ADMIN_CAMPAIGN with id: {campaign_id}, value: {saved_campaign_data}')
        campaign = saved_campaign_data[0]

        start_time = campaign.get('createdAt')
        end_time = start_time + 7 * 24 * 60 * 60 * 1000  # now() + 7 days in milliseconds

        campaign.put('startTime', start_time)
        campaign.put('startDate', self.format_to_date(start_time))
        campaign.put('startDateText', self.format_to_date_short(start_time))
        campaign.put('endTime', end_time)
        campaign.put('endDate', self.format_to_date(end_time))
        campaign.put('endDateText', self.format_to_date_short(end_time))
        campaign.put('paidByNodeAddress', self.event_payload.get('paidByNodeAddress'))
        campaign.put('totalSolveCost', self.event_payload.get('totalSolveCost'))
        campaign.put('paymentStatus', self.event_payload.get('paymentStatus'))
        campaign.put('status', 'Active')
        campaign.put('statViews', 0)
        campaign.put('statLikes', 0)
        campaign.put('statReferrals', 0)

        # campaign.put('allowCampaignPurchase', False)
        desired_distance = campaign.get('desiredDistance')
        if desired_distance:
            desired_distance = desired_distance
        else:
            campaign_type = campaign.get('campaignType')
            if campaign_type == 'Platinum':
                desired_distance = '500'
            elif campaign_type == 'Gold':
                desired_distance = '250'
            else:
                desired_distance = '100'
        campaign.put('desiredDistance', desired_distance)

        print(f'Update TRIAL_ADMIN_CAMPAIGN with id: {campaign_id}, with value: {campaign}')
        return self.vault.update('TRIAL_ADMIN_CAMPAIGN', filter_by_id, campaign, False)

    def update_trial_status(self, campaign: Map) -> Map:
        trial_id = campaign.get('SiteID')
        filter_by_id = List.of(EqualitySearchFilter.builder().fieldName('SiteID').value(trial_id).build())

        start_time = campaign.get('createdAt')
        end_time = start_time + 7 * 24 * 60 * 60 * 1000  # now() + 7 days in milliseconds

        trial_data = self.vault.search('TRIALS', filter_by_id)
        print(f'Search TRIALS with SiteID: {trial_id}, value: {trial_data}')

        trial = trial_data[0]
        trial.put('trialStatus', 'CAMPAIGN')
        trial.put('CampaignId', campaign.get('transactionalGuid'))
        trial.put('CampaignType', campaign.get('campaignType'))
        trial.put('AdminAddress', self.node.info().getScAddress())
        trial.put('CampaignStartTime', start_time)
        trial.put('CampaignStartDate', self.format_to_date(start_time))
        trial.put('CampaignEndTime', end_time)
        trial.put('CampaignEndDate', self.format_to_date(end_time))

        self.vault.update('TRIALS', filter_by_id, trial, False)
        print(f'Updated TRIALS with SiteID: {trial_id}, with value: {trial}')

    def save_campaign_to_cdn(self, campaign: Map):
        trial_id = campaign.get('SiteID')
        trial_data = self.cdn.find_first('trials-with-geo', SimpleQueryBuilder.eq('SiteID', trial_id))

        trial = HashMap(trial_data.getData())

        print(f"CDN Search 'trials-with-geo' with SiteID: {trial_id}, value: {trial_data}")

        trial.remove('_transaction_id')
        trial.remove('_meta_data')
        trial.remove('audit')
        trial.remove('SiteWalletID')

        start_time = campaign.get('createdAt')
        end_time = start_time + 7 * 24 * 60 * 60 * 1000  # now() + 7 days in milliseconds

        desired_distance = campaign.get('desiredDistance')
        if desired_distance:
            desired_distance = int(float(desired_distance))
        else:
            desired_distance = 100

        free_service = campaign.get('freeService')
        if free_service:
            free_service = [value.strip() for value in free_service.split(',')]
        else:
            free_service = []

        trial.put('CampaignId', campaign.get('transactionalGuid'))
        trial.put('CampaignType', campaign.get('campaignType'))
        trial.put('CampaignDistance', desired_distance)
        trial.put('CampaignFreeServices', free_service)
        trial.put('OwnerNodeScAddress', self.node.info().getScAddress())
        trial.put('StartTime', start_time)
        trial.put('EndTime', end_time)
        self.cdn.save('trials-campaign', trial)
        print(f"CDN Save to 'trials-campaign': {trial}")

        campaign_activities_data = {
            'SiteID': campaign.get('SiteID'),
            'NCTId': campaign.get('TrialID'),
            'CampaignType': campaign.get('campaignType'),
            'StartDate': self.format_to_date_short(start_time),
            'EndDate': self.format_to_date_short(end_time),
            'Amount': campaign.get('totalSolveCost'),
            'CampaignID': campaign.get('transactionalGuid'),
            'OwnerNodeScAddress': self.node.info().getScAddress(),
        }
        self.cdn.save('campaign_activities', campaign_activities_data)
        print(f"CDN Save to 'campaign_activities': {campaign_activities_data}")

    def handle(self) -> Map:
        result = HashMap(self.arguments)
        campaign = self.find_campaign()
        self.save_campaign_to_cdn(campaign)
        self.update_trial_status(campaign)
        print('Execution done')
        return result


def execute(context: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {context}')
    result = CustomPythonEventHandler(context).handle()
    return result
