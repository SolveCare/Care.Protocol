import java
import uuid

from abc import ABC, abstractmethod

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
SearchRequest = java.type('care.solve.node.core.model.cdn.SearchRequest')
SearchResponse = java.type('care.solve.node.core.model.cdn.SearchResponse')
SimpleQueryBuilder = java.type('care.solve.node.core.model.cdn.SimpleQueryBuilder')
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")
NodeInfo = java.type("care.solve.node.core.model.NodeInfo")


class CDN:

    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def find_all(self, indices: str, parameters: SearchRequest) -> List:
        return self.context.getCareDataNodeProvider().findAll(indices, parameters)

    def save(self, indices: str, data) -> SearchResponse:
        return self.context.getCareDataNodeProvider().save(indices, data)

    def raw_search(self, indices: str, page_num, page_size, search_request) -> List:
        return self.context.getCareDataNodeProvider().rawSearch(indices, page_num, page_size, search_request)

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

    def send_notification(self):
        self.context.getNotificationProvider().send(
            'Congratulations!',
            'Your site admin code has been activated successfully.')

    def handle(self) -> Map:
        result = HashMap(self.arguments)
        print("e-h-n-trial admin process-> activating trial")

        if self.event_payload:
            admin_address = self.sender_node_address
            code = self.event_payload.get("Site_UniqueCode")

            admin_criterion = EqualitySearchFilter.builder().fieldName("AdminAddress").value(admin_address).build()
            code_criterion = EqualitySearchFilter.builder().fieldName("Site_UniqueCode").value(code).build()

            vault_filter_trials = List.of(admin_criterion, code_criterion)
            vault_data_trials = self.vault.search('TRIALS', vault_filter_trials)

            code_exists = len(vault_data_trials) > 0

            site_data_list = self.cdn.find_all('trials-with-geo', SimpleQueryBuilder.eq('Site_UniqueCode', code))
            print("site_data_list ", site_data_list)
            if len(site_data_list) == 0:
                print(f'no site data by code, {code}')
                return result

            site_assignments = self.cdn.find_all('site_admin_assignments', SimpleQueryBuilder.eq('SiteID', code))
            print("site_data_list ", site_data_list)

            # if unique code entered by admin = unique code in cdn
            if not code_exists and len(site_assignments) == 0:

                for row in site_data_list:
                    age_text = str(int(row.getData().get('MinimumAgeNumber'))) + "-" + str(
                        int(row.getData().get('MaximumAgeNumber'))) + " years, "
                    gender_text = row.getData().get('Gender')

                    if gender_text == "All":
                        gender_text = gender_text + " genders"

                    latitude = None
                    longitude = None
                    trial_loc = row.getData().get('Location')
                    if trial_loc:
                        latitude = float(trial_loc.get('lat') or "1")
                        longitude = float(trial_loc.get('lon') or "1")
                    print("site admin Latitude:", latitude, type(latitude))
                    print("site admin Longitude:", longitude, type(longitude))

                    trial = {
                        "SiteID": row.getData().get('SiteID'),
                        "TrialID": row.getData().get('NCTId'),

                        "archived": 'false',
                        # "Miles": row.getData().get('Miles'),
                        "StudyType": row.getData().get('StudyType'),
                        "Country": row.getData().get('LocationCountry'),
                        "City": row.getData().get('LocationCity'),
                        "LeadSponsorName": row.getData().get('LeadSponsorName'),
                        # "Age": row.getData().get('MinimumAgeNumber'),
                        "AgeRange": age_text,
                        "Gender": row.getData().get('Gender'),
                        "LocationFacility": row.getData().get('LocationFacility'),
                        "Latitude": latitude,
                        "Longitude": longitude,

                        "TrialName": row.getData().get('BriefTitle'),
                        "BriefSummary" : row.getData().get('BriefSummary'),        

                        # "Distance": row.getData().get('Distance'),
                        "Site_UniqueCode": row.getData().get('Site_UniqueCode'),
                        "AdminAddress": admin_address,
                        "Eligible": age_text + gender_text,
                        # "Location_Text": row.getData().get('LocationCity') + ", " + row.getData().get('LocationCountry'),
                        "Location_Text": row.getData().get('LocationCity'),

                        "transactionalGuid": str(uuid.uuid1()),
                        "trialStatus": "NEW",
                        "isSubscriptionActive": False,
                        "isSubscriptionNotActive": True,
                        # "allowCampaignPurchase" : True
                        "isSiteNotActive": False,
                        "isSiteActive": True,
                        "likes_count": 0,
                        "leads_count": 0,
                        "campaigns_count": 0,
                        "campaigns_likes_count": 0,
                        
                        "InclusionCriteria": row.getData().get('InclusionCriteria'),
                        "ExclusionCriteria": row.getData().get('ExclusionCriteria')

                    }

                    print(f'Care.Trial with unique code: {trial}')
                    self.vault.save('TRIALS', trial)

                    cdn_data = {
                        "TrialID": trial["TrialID"],
                        "SiteID": trial["SiteID"],
                        "TrialName": trial["TrialName"],
                        "siteAdminScAddress": self.sender_node_address
                        # "SiteName" : trial["LocationFacility"],
                        # "SiteAddress" : trial["Location_Text"],
                        # "Contact" : trial["Contact"],

                    }
                    self.cdn.save('site_admin_assignments', cdn_data)

                    update_data = Map.of('SiteWalletID', self.node.info().getScAddress())
                    self.cdn.update('trials-with-geo', row.getId(), update_data)

                    self.send_notification()
                    print("Notification sent!")

        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
