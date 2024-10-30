from abc import ABC, abstractmethod

import java

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
NodeInfo = java.type("care.solve.node.core.model.NodeInfo")
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")
SearchQueryFilter = java.type("care.solve.node.core.model.query.SearchQueryFilter")

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
        print(f'==> [CustomPythonEventHandler#data]: {data}')
        guid = vault.update(criteria, data, insert_if_absent)
        print(f'==> [CustomPythonEventHandler#guid]: {guid}')
        return vault.getByGuid(guid)

    def search(self, collection: str, criteria: List) -> List:
        vault = self.context.getVaultStorage(collection)
        return vault.search(criteria)

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
        self.cdn = CDN(context)
        self.node = Node(context)

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):

    def find_saved_trials(self, site_id: str) -> List:

        criteria = List.of(EqualitySearchFilter.builder().fieldName("SiteID").value(site_id).build())
        vault_data = self.vault.search('TRIALS', criteria)
        print(f'Found {len(vault_data)} records in TRIALS with SiteID: '
              f'{site_id} and admin: {self.sender_node_address}')
        return vault_data

    def find_saved_campaigns(self, site_id: str) -> List:

        criteria = List.of(EqualitySearchFilter.builder().fieldName("SiteID").value(site_id).build())
        vault_data = self.vault.search('TRIAL_ADMIN_CAMPAIGN', criteria)
        print(f'Found {len(vault_data)} records in TRIAL_ADMIN_CAMPAIGN with SiteID: '
              f'{site_id} and admin: {self.sender_node_address}')
        return vault_data

    def update_saved_trials(self, site_id: str, stat_data: dict):
        existing_trials = self.find_saved_trials(site_id)
        for trial in existing_trials:
            trial.put("likes_count", stat_data['likes_count'])
            trial.put("leads_count", stat_data['leads_count'])
            trial.put("campaigns_count", stat_data['campaigns_count'])
            trial.put("campaigns_likes_count", stat_data['campaigns_likes_count'])
            trial.put("refers_count", stat_data['refers_count'])

            update_filter = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
                trial.get('transactionalGuid')).build())
            updated = self.vault.update('TRIALS', update_filter, trial, False)
            print(f'==> [updated trial]: {updated}')

    def calculate_statistics_for_campaigns(self, site_id: str):
        existing_campaigns = self.find_saved_campaigns(site_id)
        for campaign in existing_campaigns:
            campaign_id = campaign.get('transactionalGuid')
            campaign_likes = self.calculate_campaign_likes_count(site_id, campaign_id)
            campaign_refers = self.calculate_refers_count_by_campaign(site_id, campaign_id)
            campaign.put("statLikes", campaign_likes)
            campaign.put("statReferrals", campaign_refers)
            # campaign.put("statViews", stat_data['stat_views'])
            update_filter = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
                campaign_id).build())
            updated = self.vault.update('TRIAL_ADMIN_CAMPAIGN', update_filter, campaign, False)
            print(f'==> [updated campaign]: {updated}')

    def update_stats_data_in_cdn(self, stat_data: dict):
        stats_filter = SimpleQueryBuilder.eq('siteAdminScAddress', self.node.info().getScAddress())
        cdn_stats = self.cdn.find_all('site_admin_stats', stats_filter)

        cdn_stat_data = {
            'likesCount': stat_data['likes_count'],
            'leadsCount': stat_data['leads_count'],
            'campaignsCount': stat_data['campaigns_count'],
            'campaignsLikesCount': stat_data['campaigns_likes_count'],
            'refersCount': stat_data['refers_count'],
            'siteAdminScAddress': self.node.info().getScAddress(),
        }
        if len(cdn_stats) == 0:
            response = self.cdn.save('site_admin_stats', cdn_stat_data)
            print(f'[saved]: {cdn_stat_data} to site_admin_stats with id {response.getId()}')
        else:
            for cdn_stat in cdn_stats:
                self.cdn.update('site_admin_stats', cdn_stat.getId(), cdn_stat_data)
                print(f'[updated]: {cdn_stat} to site_admin_stats with id {cdn_stat.getId()}')

    def calculate_campaigns_likes_count(self, site_id: str) -> int:
        site_filter = SimpleQueryBuilder.eq('SiteID', site_id)
        platinum_filter = SimpleQueryBuilder.eq('CampaignType', 'Platinum')
        silver_filter = SimpleQueryBuilder.eq('CampaignType', 'Silver')
        gold_filter = SimpleQueryBuilder.eq('CampaignType', 'Gold')
        campaigns_type_filter = SimpleQueryBuilder.oor(platinum_filter, silver_filter, gold_filter)
        campaigns_filter = SimpleQueryBuilder.aand(site_filter, campaigns_type_filter)
        return self.cdn.count('trials_likes', campaigns_filter).getTotal()

    def calculate_campaign_likes_count(self, site_id: str, campaign_id) -> int:
        campaign_filter = SimpleQueryBuilder.eq('CampaignId', campaign_id)
        site_filter = SimpleQueryBuilder.eq('SiteID', site_id)
        campaigns_filter = SimpleQueryBuilder.aand(site_filter, campaign_filter)
        return self.cdn.count('trials_likes', campaigns_filter).getTotal()

    def calculate_refers_count(self, site_id: str) -> int:
        refers_filter = SimpleQueryBuilder.eq('SiteID', site_id)
        return self.cdn.count('trials_refers', refers_filter).getTotal()

    def calculate_refers_count_by_campaign(self, site_id: str, campaign_id: str) -> int:
        refers_filter = SimpleQueryBuilder.eq('SiteID', site_id)
        campaign_filter = SimpleQueryBuilder.eq('CampaignId', campaign_id)
        return self.cdn.count('trials_refers', SimpleQueryBuilder.aand(refers_filter, campaign_filter)).getTotal()

    def handle(self) -> Map:
        print("Custom event handler -> [e-h-n-statistic-count.py]")
        result = HashMap(self.arguments)

        site_id = self.event_payload.get("SiteID")
        print(f'Recalculate requests count for SiteID: {site_id}, sender: {self.sender_node_address}')

        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("SiteID").value(site_id).build())

        leads_count = self.vault.count('PARTICIPANT_ADMIN_TRIALS_SAVED', vault_filter)
        print(f'leads_count: {leads_count}')

        campaigns_count = self.vault.count('TRIAL_ADMIN_CAMPAIGN', vault_filter)
        print(f'campaigns_count: {campaigns_count}')

        likes_count = self.cdn.count('trials_likes', SimpleQueryBuilder.eq('SiteID', site_id)).getTotal()
        print(f'likes_count: {likes_count}')

        campaigns_likes_count = self.calculate_campaigns_likes_count(site_id)
        print(f'campaigns_likes_count: {campaigns_count}')

        refers_count = self.calculate_refers_count(site_id)
        print(f'refers_count: {refers_count}')

        stat_data = {
            'likes_count': likes_count,
            'leads_count': leads_count,
            'campaigns_count': campaigns_count,
            'campaigns_likes_count': campaigns_likes_count,
            'refers_count': refers_count
        }
        print(f"statistics: {stat_data}")

        self.update_saved_trials(site_id, stat_data)
        self.calculate_statistics_for_campaigns(site_id)
        self.update_stats_data_in_cdn(stat_data)

        print("result", result)
        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
