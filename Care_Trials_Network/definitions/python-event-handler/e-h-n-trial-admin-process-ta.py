import java
import uuid

from abc import ABC, abstractmethod

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
SearchRequest = java.type('care.solve.node.core.model.cdn.SearchRequest')
CountResponse = java.type('care.solve.node.core.model.cdn.CountResponse')
SearchResponse = java.type('care.solve.node.core.model.cdn.SearchResponse')
SimpleQueryBuilder = java.type('care.solve.node.core.model.cdn.SimpleQueryBuilder')
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")


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

    def count(self, indices: str, parameters: SearchRequest) -> CountResponse:
        return self.context.getCareDataNodeProvider().count(indices, parameters)


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

    def count(self, collection: str, criteria: List) -> int:
        vault = self.context.getVaultStorage(collection)
        return vault.count(criteria)


class PythonEventHandler(ABC):

    def __init__(self, context: HandlerExecutionContext):
        self.arguments = context.getArguments()
        self.sender_node_address = context.getEvent().getFrom()
        self.event_payload = context.getEvent().getPayload()
        self.vault = Vault(context)
        self.cdn = CDN(context)
        self.context = context

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):

    def send_notification(self):
        self.context.getNotificationProvider().send(
            'Congratulations!',
            'Your trial admin code has been activated successfully.')

    def find_site_in_cdn(self, unique_code: str) -> List:
        query = {
            "query": {
                "bool": {
                    "must": [{"query_string": {"query": f"(UniqueCode:{unique_code})"}}]
                }
            }
        }

        print("CDN Query:", query)
        return self.cdn.raw_search(0, 100, query)

    def is_site_active(self, trial_id: str, site_id: str) -> bool:
        criteria = SimpleQueryBuilder.aand(
            SimpleQueryBuilder.eq('TrialID', trial_id),
            SimpleQueryBuilder.eq('SiteID', site_id))
        return self.cdn.count('site_admin_assignments', criteria).getTotal() > 0

    def save_trial(self, cdn_sites: List):
        row = cdn_sites[0].getData()

        age_text = str(int(row.get('MinimumAgeNumber'))) + "-" + str(int(row.get('MaximumAgeNumber'))) + " years, "
        gender_text = row.get('Gender')

        if gender_text == "All":
            gender_text = gender_text + " genders"

        trial = {
            "TrialID": row.get('NCTId'),

            "archived": 'false',
            "StudyType": row.get('StudyType'),
            "Country": row.get('LocationCountry'),
            "City": row.get('LocationCity'),
            "LeadSponsorName": row.get('LeadSponsorName'),
            "AgeRange": age_text,
            "Gender": row.get('Gender'),
            "LocationFacility": row.get('LocationFacility'),

            "TrialName": row.get('BriefTitle'),
            "BriefSummary" : row.get('BriefSummary'),        
            "UniqueCode": row.get('UniqueCode'),
            "AdminAddress": self.sender_node_address,
            "Eligible": age_text + gender_text,
            # "Location_Text": row.get('LocationCity') + ", " + row.get('LocationCountry'),
            "Location_Text": row.get('LocationCity'),

            "transactionalGuid": str(uuid.uuid1()),
            "trialStatus": "NEW",
            "isSubscriptionActive": False,
            "isSubscriptionNotActive": True,
            # "allowCampaignPurchase" : True
            "likes_count": 0,
            "total_sites": 0,
            "active_sites": 0,
            "campaigns_likes_count": 0
        }

        print(f'Saving Care.Trial {row.get("NCTId")} by unique code: {row.get("UniqueCode")}')
        self.vault.save('TRIALS_TA_SH', trial)

    def save_site(self, row: Map):

        trial_id = row.get('NCTId')
        site_id = row.get('SiteID')
        is_active = self.is_site_active(trial_id, site_id)

        age_text = str(int(row.get('MinimumAgeNumber'))) + "-" + str(int(row.get('MaximumAgeNumber'))) + " years, "
        gender_text = row.get('Gender')

        if gender_text == "All":
            gender_text = gender_text + " genders"

        trial = {
            "TrialID": trial_id,
            "SiteID": site_id,

            "archived": 'false',
            "StudyType": row.get('StudyType'),
            "Country": row.get('LocationCountry'),
            "City": row.get('LocationCity'),
            "LeadSponsorName": row.get('LeadSponsorName'),
            "AgeRange": age_text,
            "Gender": row.get('Gender'),
            "LocationFacility": row.get('LocationFacility'),

            "TrialName": row.get('BriefTitle'),
            "BriefSummary" : row.get('BriefSummary'),        
            
            "UniqueCode": row.get('UniqueCode'),
            "AdminAddress": self.sender_node_address,
            "Eligible": age_text + gender_text,
            # "Location_Text": row.get('LocationCity') + ", " + row.get('LocationCountry'),
            "Location_Text": row.get('LocationCity'),

            "transactionalGuid": str(uuid.uuid1()),
            "trialStatus": "NEW",
            "isSubscriptionActive": False,
            "isSubscriptionNotActive": True,
            # "allowCampaignPurchase" : True
            "isSiteNotActive": not is_active,
            "isSiteActive": is_active,
            "likes_count": 0,
            "campaigns_count": 0,
            "campaigns_likes_count": 0
        }

        print(f'Saving Care.Site {trial_id}:{site_id} by unique code: {row.get("UniqueCode")}')
        self.vault.save('TRIALS_TA', trial)

    def handle(self) -> Map:
        result = HashMap(self.arguments)

        if self.event_payload:
            admin_address = self.sender_node_address
            code = self.event_payload.get("UniqueCode")

            admin_criterion = EqualitySearchFilter.builder().fieldName("AdminAddress").value(admin_address).build()
            code_criterion = EqualitySearchFilter.builder().fieldName("UniqueCode").value(code).build()

            vault_filter_trials = List.of(admin_criterion, code_criterion)
            vault_data_trials = self.vault.count('TRIALS_TA_SH', vault_filter_trials)

            if vault_data_trials > 0:
                print(f'Trial with code: {code} already exists. Skip it.')
                return result

            cdn_sites = self.find_site_in_cdn(code)

            if len(cdn_sites) == 0:
                print(f'No sites found with UniqueCode: {code}. Skip it.')
                return result

            self.save_trial(cdn_sites)

            for row in cdn_sites:
                self.save_site(row.getData())

            self.send_notification()
            print("Notification sent!")

        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
