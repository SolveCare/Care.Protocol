import java
import math

from abc import ABC, abstractmethod

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")

SearchRequest = java.type('care.solve.node.core.model.cdn.SearchRequest')
SearchResponse = java.type('care.solve.node.core.model.cdn.SearchResponse')
SimpleQueryBuilder = java.type('care.solve.node.core.model.cdn.SimpleQueryBuilder')


class CDN:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def find_first(self, indices: str, parameters: SearchRequest) -> SearchResponse:
        return self.context.getCareDataNodeProvider().findFirst(indices, parameters)

    def find_all(self, indices: str, parameters: SearchRequest) -> List:
        return self.context.getCareDataNodeProvider().findAll(indices, parameters)

    def raw_search(self, indices, from_row, num_rows, search_request) -> List:
        return self.context.getCareDataNodeProvider().rawSearch(indices, from_row, num_rows, search_request)


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

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):

    @staticmethod
    def __calculate_distance(user_latitude, user_longitude, site_latitude, site_longitude):
        # find the distance between site and participant
        distance_km = 6371 * 2 * math.asin(
            math.sqrt(math.sin(math.radians((site_latitude - user_latitude) / 2)) ** 2 + math.cos(
                math.radians(user_latitude)) * math.cos(math.radians(site_latitude)) * math.sin(
                math.radians((site_longitude - user_longitude) / 2)) ** 2))
        return int(distance_km)

    def __extract_distance(self, site_data, lead_data) -> int:
        guid = lead_data.get('transactionalGuid')
        user_latitude = lead_data.get('userLocationLatitude')
        user_longitude = lead_data.get('userLocationLongitude')
        site_loc = site_data.get('Location')
        if site_loc and user_latitude and user_longitude:
            site_latitude = float(site_loc.get('lat'))
            site_longitude = float(site_loc.get('lon'))
            distance = self.__calculate_distance(user_latitude, user_longitude, site_latitude, site_longitude)

            print(f"Calculated distance for 'trials_likes' {guid}: {distance}km")
            return distance
        else:
            print(f"Couldn't calculate distance for 'trials_likes' {guid} as it without 'Location'")
            return -1

    def __is_matches(self, site_data, lead_data) -> bool:

        guid = lead_data.get('transactionalGuid')
        miles = lead_data.get("Miles")

        if miles == 'Anywhere':
            print(f"'trials_likes' {guid} matches participant has anywhere max distance")
            return True

        participant_max_distance = int(float(miles))
        if participant_max_distance >= 20000:
            print(f"'trials_likes' {guid} matches participant has more than 20000km max distance")
            return True

        distance = self.__extract_distance(site_data, lead_data)
        if distance <= participant_max_distance:
            print(f"'trials_likes' {guid} matches as calculated {distance}km distance is less than "
                  f"participant max {participant_max_distance}km distance")
            return True
        else:
            print(f"'trials_likes' {guid} not matches as calculated {distance}km distance is greater than "
                  f"participant max {participant_max_distance}km distance")
            return False

    def __build_lead_entity(self, site_data, lead_data) -> dict:
        gender = lead_data.get('Gender')
        age = lead_data.get('Age')
        city = lead_data.get('City')
        gender_age_city = f"{gender}, {age}, {city}"
        if gender is not None and gender == "Rather not say":
            gender_age_ethnicity_text = f"{age} years"
        else:
            gender_age_ethnicity_text = f"{gender}, {age} years"
        # gender_age_ethnicity_text = f"{gender}, {age} years, {lead_data.get('Ethnicity')}"
        location_miles_text = f"{city}\nWilling to travel {lead_data.get('Miles_Text')}"
        # location_miles_text = f"{city}, {lead_data.get('Country')}\nWilling to travel {lead_data.get('Miles_Text')}"

        return {
            "SiteID": site_data.get('SiteID'),
            "TrialID": lead_data.get('TrialID'),
            "archived": 'false',
            "StudyType": lead_data.get('StudyType'),
            "Country": lead_data.get('Country'),
            "City": city,
            "LeadSponsorName": lead_data.get('LeadSponsorName'),
            "AgeRange": lead_data.get('AgeRange'),
            "Gender": gender,
            "LocationFacility": site_data.get('LocationFacility'),
            "TrialName": lead_data.get('TrialName'),
            "BriefSummary" : lead_data.get('BriefSummary'),        
            "Site_UniqueCode": self.event_payload.get("Site_UniqueCode"),
            "AdminAddress": self.sender_node_address,
            "Eligible": lead_data.get('Eligible'),
            "Location_Text": lead_data.get('Location_Text'),
            "transactionalGuid": lead_data.get('transactionalGuid'),
            "trialStatus": "NEW",
            "isSubscriptionActive": False,
            # enrich with runtime data
            "createdAt": lead_data.get('createdAt'),
            "senderNodeAddress": lead_data.get('senderNodeAddress'),

            # Badges
            "Badges": lead_data.get('Badges'),
            "recordBadges": lead_data.get('recordBadges'),
            "IDBadges": lead_data.get('IDBadges'),

            "Age": age,
            "Conditions": lead_data.get('Conditions'),
            "Distance": lead_data.get('Distance'),
            "Distance_Text": lead_data.get('Distance'),
            "Ethnicity": lead_data.get('Ethnicity'),
            "GenderAgeCity": gender_age_city,
            "GenderAgeEthnicity_Text": gender_age_ethnicity_text,
            "Limitations": lead_data.get('Limitations'),
            "Location_Miles_Text": location_miles_text,
            "Miles": lead_data.get('Miles_Text'),
            "TrialNameStatus": lead_data.get('TrialName') + " -Active",
            
            "eligibleStatus": "Pending",
            
            "InclusionCriteria": site_data.get('InclusionCriteria'),
            "ExclusionCriteria": site_data.get('ExclusionCriteria')
        }
        

    def __is_exists(self, transactional_guid: str) -> bool:
        criteria = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
            transactional_guid).build())
        return self.vault.count('PARTICIPANT_ADMIN_TRIALS', criteria) > 0

    def import_lead(self, site_data, lead: SearchResponse) -> bool:
        lead_data = lead.getData()
        guid = lead_data.get('transactionalGuid')

        if guid is not None and not self.__is_exists(guid) and self.__is_matches(site_data, lead_data):
            lead_entity = self.__build_lead_entity(site_data, lead_data)
            print(f'Saving to PARTICIPANT_ADMIN_TRIALS: {lead_entity}')
            self.vault.save('PARTICIPANT_ADMIN_TRIALS', lead_entity)
            eligibilityStatusUpdate = self.update_eligibility_status(site_data, lead_data)
            print(f'==> [eligibilityStatusUpdate]: {eligibilityStatusUpdate}')
            
            return True
        return False

    def import_leads(self, site_data: Map, leads_data: List) -> int:
        count = 0
        for lead in leads_data:
            if self.import_lead(site_data, lead):
                count += 1
        return count
    
    def update_eligibility_status(self, site_data, lead_data):
        site_id = site_data.get('SiteID')
        participant_address = lead_data.get('senderNodeAddress')
        print("1.participant addressss from event_payload:", participant_address)
        print("1.site_id from event_payload:", site_id)
        
        site_id_criterion = EqualitySearchFilter.builder().fieldName("SiteID").value(site_id).build()
        participant_criterion = EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            participant_address).build()
        trial_filter = List.of(site_id_criterion, participant_criterion)
        existing_trials = self.vault.search('TRIALS_SAVED', trial_filter)
        print(f'==> [existing trials]: {existing_trials}')
        for existing_trial in existing_trials:
            existing_status = existing_trial.get("eligibleStatus")
            print("existing_status", existing_status)
            existing_trial.put("eligibleStatus", existing_status)
            self.vault.update('PARTICIPANT_ADMIN_TRIALS', trial_filter, existing_trial, False)

    def handle(self) -> Map:
        result = HashMap(self.arguments)

        if self.event_payload:
            print('----Lead Process----')
            print('Event Payload: ', self.event_payload)
            print('Args: ', result)
            code = self.event_payload.get("Site_UniqueCode")
            print('Code: ', code)

            site_data_list = self.cdn.find_all('trials-with-geo', SimpleQueryBuilder.eq('Site_UniqueCode', code))
            print("site_data_list ", site_data_list)

            if len(site_data_list) == 0:
                return result

            site_data = site_data_list[0].getData()
            trial_id = site_data.get('NCTId')
            site_id = site_data.get('SiteID')
            print(f"trials-with-geo trial_id: {trial_id} and site_id: {site_id}")

            query = {"query": {"bool": {
                "must": [{"match": {"TrialID": trial_id}}]
            }}}

            total_leads = 0
            page_num = 0
            page_size = 100
            leads_data = self.cdn.raw_search('trials_likes', page_num, page_size, query)

            while len(leads_data) > 0:
                imported = self.import_leads(site_data, leads_data)
                total_leads = total_leads + imported
                page_num += 1
                leads_data = self.cdn.raw_search('trials_likes', page_num, page_size, query)

            print(f'Total leads imported: {total_leads}')

        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
