from abc import ABC, abstractmethod

import java

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
NodeInfo = java.type("care.solve.node.core.model.NodeInfo")
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")
NumericBoundsSearchFilter = java.type("care.solve.node.core.model.query.NumericBoundsSearchFilter")
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

    def find_saved_trials(self) -> List:
        print(f'============> find_saved_trials')

        vault_data = self.vault.search('TRIALS_TA_SH', List.of())
        print("============> vault_data: ", vault_data)
        print(f'Found {len(vault_data)} records in TRIALS_TA_SH for admin: {self.sender_node_address}')
        return vault_data

    def find_saved_sites(self, trial_id: str) -> List:
        print(f'============> find_saved_sites for trial_id: {trial_id}')

        criteria = List.of(EqualitySearchFilter.builder().fieldName("TrialID").value(trial_id).build())
        vault_data = self.vault.search('TRIALS_TA', criteria)
        print("============> vault_data: ", vault_data)
        print(f'Found {len(vault_data)} records in TRIALS_TA with TrialID: '
              f'{trial_id} and admin: {self.sender_node_address}')
        return vault_data

    def update_saved_trial(self, trial: Map, stat_data: dict):
        trial.put("likes_count", stat_data['likes_count'])
        trial.put("total_sites", stat_data['total_sites'])
        trial.put("active_sites", stat_data['active_sites'])
        trial.put("campaigns_likes_count", stat_data['campaigns_likes_count'])

        update_filter = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
            trial.get('transactionalGuid')).build())
        updated = self.vault.update('TRIALS_TA_SH', update_filter, trial, False)
        print(f'[Trial:{trial.get("TrialID")}] ==> [updated]: {updated}')

    def update_saved_site(self, site: Map, stat_data: dict):
        site.put("likes_count", stat_data['likes_count'])
        site.put("campaigns_count", stat_data['campaigns_count'])
        site.put("campaigns_likes_count", stat_data['campaigns_likes_count'])

        update_filter = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
            site.get('transactionalGuid')).build())
        updated = self.vault.update('TRIALS_TA', update_filter, site, False)
        print(f'[Site:{site.get("SiteID")}] ==>  [updated]: {updated}')

    def update_stats_data_in_cdn(self, trial_id: str, site_id: str, trial_stat_data: dict, site_stat_data: dict):
        admin_filter = SimpleQueryBuilder.eq('trialAdminScAddress', self.node.info().getScAddress())
        trial_filter = SimpleQueryBuilder.eq('TrialID', trial_id)
        cdn_stats = self.cdn.find_all('trial_admin_stats', SimpleQueryBuilder.aand(trial_filter, admin_filter))

        cdn_stat_data = {
            'TrialID': trial_id,
            'SiteID': site_id,
            'trialLikesCount': trial_stat_data['likes_count'],
            'trialTotalSites': trial_stat_data['total_sites'],
            'trialActiveSites': trial_stat_data['active_sites'],
            'trialCampaignsLikesCount': trial_stat_data['campaigns_likes_count'],
            'siteLikesCount': site_stat_data['likes_count'],
            'siteCampaignsCount': site_stat_data['campaigns_count'],
            'siteCampaignsLikesCount': site_stat_data['campaigns_likes_count'],
            'trialAdminScAddress': self.node.info().getScAddress(),
        }
        if len(cdn_stats) == 0:
            response = self.cdn.save('trial_admin_stats', cdn_stat_data)
            print(f'[saved]: {cdn_stat_data} to trial_admin_stats with id {response.getId()}')
        else:
            for cdn_stat in cdn_stats:
                self.cdn.update('trial_admin_stats', cdn_stat.getId(), cdn_stat_data)
                print(f'[updated]: {cdn_stat} to trial_admin_stats with id {cdn_stat.getId()}')

    def calculate_active_sites(self, trial_id: str) -> int:
        active_sites_filter = List.of(
            EqualitySearchFilter.builder().fieldName("isSiteActive").value(True).build(),
            EqualitySearchFilter.builder().fieldName("TrialID").value(trial_id).build())
        return self.vault.count('TRIALS_TA', active_sites_filter)

    def calculate_campaigns_likes_count(self, trial_id: str) -> int:
        trial_filter = SimpleQueryBuilder.eq('TrialID', trial_id)
        platinum_filter = SimpleQueryBuilder.eq('CampaignType', 'Platinum')
        silver_filter = SimpleQueryBuilder.eq('CampaignType', 'Silver')
        gold_filter = SimpleQueryBuilder.eq('CampaignType', 'Gold')
        campaigns_type_filter = SimpleQueryBuilder.oor(platinum_filter, silver_filter, gold_filter)
        campaigns_filter = SimpleQueryBuilder.aand(trial_filter, campaigns_type_filter)
        return self.cdn.count('trials_likes', campaigns_filter).getTotal()

    def calculate_likes_for_site(self, trial_id: str, site_id: str) -> int:
        criteria = SimpleQueryBuilder.aand(
            SimpleQueryBuilder.eq('TrialID', trial_id),
            SimpleQueryBuilder.eq('SiteID', site_id))
        return self.cdn.count('trials_likes', criteria).getTotal()

    def calculate_campaigns_for_site(self, trial_id: str, site_id: str) -> int:
        criteria = SimpleQueryBuilder.aand(
            SimpleQueryBuilder.eq('NCTId', trial_id),
            SimpleQueryBuilder.eq('SiteID', site_id))
        return self.cdn.count('trials-campaign', criteria).getTotal()

    def calculate_campaigns_likes_for_site(self, trial_id: str, site_id: str) -> int:
        trial_filter = SimpleQueryBuilder.eq('TrialID', trial_id)
        site_filter = SimpleQueryBuilder.eq('SiteID', site_id)
        platinum_filter = SimpleQueryBuilder.eq('CampaignType', 'Platinum')
        silver_filter = SimpleQueryBuilder.eq('CampaignType', 'Silver')
        gold_filter = SimpleQueryBuilder.eq('CampaignType', 'Gold')
        campaigns_type_filter = SimpleQueryBuilder.oor(platinum_filter, silver_filter, gold_filter)
        campaigns_filter = SimpleQueryBuilder.aand(trial_filter, site_filter, campaigns_type_filter)
        return self.cdn.count('trials_likes', campaigns_filter).getTotal()

    def update_stats_data_for_sites(self, trial_id: str, trial_stat_data: dict):
        sites = self.find_saved_sites(trial_id)
        for site in sites:
            site_id = site.get('SiteID')

            likes_count = self.calculate_likes_for_site(trial_id, site_id)
            print(f'[Site:{site_id}] -> likes_count: {likes_count}')

            campaigns_count = self.calculate_campaigns_for_site(trial_id, site_id)
            print(f'[Site:{site_id}] -> campaigns_count: {campaigns_count}')

            campaigns_likes_count = self.calculate_campaigns_likes_for_site(trial_id, site_id)
            print(f'[Site:{site_id}] -> campaigns_likes_count: {campaigns_likes_count}')

            site_stat_data = {
                'likes_count': likes_count,
                'campaigns_count': campaigns_count,
                'campaigns_likes_count': campaigns_likes_count
            }
            self.update_saved_site(site, site_stat_data)

            self.update_stats_data_in_cdn(trial_id, site_id, trial_stat_data, site_stat_data)

    def update_stats_data(self, existing_trial: Map):
        trial_id = existing_trial.get('TrialID')

        likes_count = self.cdn.count('trials_likes', SimpleQueryBuilder.eq('TrialID', trial_id)).getTotal()
        print(f'[Trial:{trial_id}] -> likes_count: {likes_count}')

        total_sites = self.cdn.count('trials-with-geo', SimpleQueryBuilder.eq('NCTId', trial_id)).getTotal()
        print(f'[Trial:{trial_id}] -> total_sites: {total_sites}')

        active_sites = self.calculate_active_sites(trial_id)
        print(f'[Trial:{trial_id}] -> active_sites: {active_sites}')

        campaigns_likes_count = self.calculate_campaigns_likes_count(trial_id)
        print(f'[Trial:{trial_id}] -> campaigns_likes_count: {campaigns_likes_count}')

        trial_stat_data = {
            'likes_count': likes_count,
            'total_sites': total_sites,
            'active_sites': active_sites,
            'campaigns_likes_count': campaigns_likes_count
        }
        print(f'[Trial:{trial_id}] -> statistics: {trial_stat_data}')

        self.update_saved_trial(existing_trial, trial_stat_data)
        self.update_stats_data_for_sites(trial_id, trial_stat_data)

    def handle(self) -> Map:
        print("Custom event handler -> [e-h-n-statistic-count-for-ta.py]")
        result = HashMap(self.arguments)

        existing_trials = self.find_saved_trials()
        print(f'existing_trials:', existing_trials)

        if len(existing_trials) == 0:
            print(f"No existing trials found, skip it.")
            return result

        for existing_trial in existing_trials:
            self.update_stats_data(existing_trial)

        print("result", result)
        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
