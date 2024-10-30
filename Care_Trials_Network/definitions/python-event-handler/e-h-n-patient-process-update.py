import math
import re
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime

import java

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
NodeInfo = java.type("care.solve.node.core.model.NodeInfo")
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")
Pagination = java.type('care.solve.node.core.model.query.Pagination')
Sorting = java.type('care.solve.node.core.model.query.Sorting')

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
        print(f'==> [CustomPythonEventHandler#d]: {data}')
        guid = vault.update(criteria, data, insert_if_absent)
        print(f'==> [CustomPythonEventHandler#d]: {guid}')
        return vault.getByGuid(guid)

    def search(self, collection: str, criteria: List) -> List:
        vault = self.context.getVaultStorage(collection)
        return vault.search(criteria)

    def search_pageable(self, collection: str, criteria: List, pagination: Pagination) -> List:
        vault = self.context.getVaultStorage(collection)
        return vault.search(criteria, pagination)

    def remove(self, collection: str, guid: str):
        vault = self.context.getVaultStorage(collection)
        vault.delete(guid)

    def remove_by_criteria(self, collection: str, criteria: List) -> int:
        vault = self.context.getVaultStorage(collection)
        return vault.delete(criteria)

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

    @staticmethod
    def calculate_max_distance(questions_data: Map) -> int:
        miles = questions_data.get('Miles') or "1000 km"
        numbers = re.findall(r'\d+', miles)
        if numbers:
            return int(numbers[0])
        elif miles.lower().startswith('local'):
            return 50
        else:
            return 20000

    @staticmethod
    def extract_age(questions_data: Map) -> int:
        return questions_data.get('Age') or 20

    @staticmethod
    def extract_age_text(row_data) -> str:
        return f"{int(row_data.get('MinimumAgeNumber'))}-{int(row_data.get('MaximumAgeNumber'))} years"

    @staticmethod
    def extract_gender(questions_data: Map) -> str:
        return questions_data.get('Gender') or "All"

    @staticmethod
    def extract_gender_text(row_data) -> str:
        gender_text = row_data.get('Gender')
        if gender_text == "All":
            gender_text = gender_text + " genders"
        return gender_text

    @staticmethod
    def extract_distance(row_data, questions_data: Map) -> int:
        user_latitude = questions_data.get('userLocationLatitude')
        user_longitude = questions_data.get('userLocationLongitude')
        trial_loc = row_data.get('Location')
        if trial_loc and user_latitude and user_longitude:
            trial_lat = float(trial_loc.get('lat'))
            trial_lon = float(trial_loc.get('lon'))
            distance_km = 6371 * 2 * math.asin(math.sqrt(
                math.sin(math.radians((trial_lat - user_latitude) / 2)) ** 2 + math.cos(
                    math.radians(user_latitude)) * math.cos(math.radians(trial_lat)) * math.sin(
                    math.radians((trial_lon - user_longitude) / 2)) ** 2))
            # distance_mi = distance_km * 0.621371
            # distance = int(distance_mi)
            distance = int(distance_km)

            print(f"Calculated distance for Care.Trial {row_data.get('SiteID')}: {distance}km")
            return distance
        else:
            print(f"Couldn't calculate distance for Care.Trial {row_data.get('SiteID')} as it without 'Location'")
            return -1

    @staticmethod
    def build_distance_text(distance: int) -> str:
        if distance > 0:
            return "Nearest location: " + str(distance) + " km away"
        elif distance == 0:
            return "Nearest location: less than 1 km away"
        else:
            return "Not Available"

    @staticmethod
    def count_matched_conditions(document, questions_data) -> int:
        trial_conditions = [condition.strip() for condition in
                            re.split(r'[|,]', document.getOrDefault("Condition", "").lower().strip("[]"))]
        query_conditions = [condition.strip() for condition in
                            questions_data.getOrDefault('Conditions', "").lower().split(",")]
        return sum(any(query_condition in trial_condition for trial_condition in trial_conditions)
                   for query_condition in query_conditions)

    @staticmethod
    def determine_matching_group(row_data) -> int:
        score = row_data.getScore()
        if score >= 10000:
            return int(score / 10000)
        elif score >= 5000:
            return 0
        else:
            return -1

    def find_questions_data(self) -> List:
        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.node.info().getScAddress()).build())
        pagination = Pagination.of(0, 2, Sorting.desc('createdAt'))
        questions_data_list = self.vault.search_pageable('6_QUESTIONS', vault_filter, pagination)
        print(f'Found {len(questions_data_list)} records of 6_QUESTIONS')

        return questions_data_list

    def clean_up_old_results(self, collection: str):
        clean_up_filter = List.of(
            EqualitySearchFilter.builder().fieldName("trialStatus").value("NEW").build(),
            EqualitySearchFilter.builder().fieldName("shared").value(True).inverted(True).build())

        removed = self.vault.remove_by_criteria(collection, clean_up_filter)
        print(f'Removed {removed} documents from {collection}')

    def save_site(self, row: SearchResponse, questions_data: Map) -> bool:
        row_data = row.getData()
        site_id = row_data.get('SiteID')
        print(f'Found site with SiteID: {site_id}, Location: {row_data.get("Location")}')

        vault_filter_trials = List.of(EqualitySearchFilter.builder().fieldName("SiteID").value(site_id).build())
        vault_data_trials = self.vault.count('TRIALS', vault_filter_trials)

        if vault_data_trials > 0:
            print(f'Skip Care.Site with SiteID:{site_id} as it already present in TRIALS collection')
            return False

        age_text = self.extract_age_text(row_data)
        distance = self.extract_distance(row_data, questions_data)

        trial = {

            # enrich with data from search response
            "SiteID": site_id,
            "TrialID": row_data.get('NCTId'),
            "LocationFacility": row_data.get('LocationFacility'),

            "StudyType": row_data.get('StudyType'),
            "Country": row_data.get('LocationCountry'),
            "City": row_data.get('LocationCity'),
            "LeadSponsorName": row_data.get('LeadSponsorName'),
            "AgeRange": age_text,
            "TrialName": row_data.get('BriefTitle'),
            "BriefSummary" : row_data.get('BriefSummary'),
            "Eligible": f"{age_text}, {self.extract_gender_text(row_data)}",
            "Location_Text": f"{row_data.get('LocationCity')}",
            "Site_UniqueCode": row_data.get('Site_UniqueCode'),
            "Distance": self.build_distance_text(distance),

            # enrich with data from 6_QUESTIONS
            "Miles": str(self.calculate_max_distance(questions_data)),
            "Miles_Text": questions_data.get('Miles'),
            "Age": self.extract_age(questions_data),
            "Gender": self.extract_gender(questions_data),
            "Conditions": questions_data.get('Conditions') or "None",
            "Limitations": questions_data.get('Limitations'),
            "Ethnicity": questions_data.get('Ethnicity'),

            # enrich with static data
            "archived": 'false',
            "trialStatus": "NEW",
            "shared": False,

            # enrich with runtime data
            "createdAt": self.current_milli_time(),
            "senderNodeAddress": self.node.info().getScAddress(),
            "transactionalGuid": str(uuid.uuid1()),

            # update badges
            "Badges": 'https://i.ibb.co/d6VdwVh/Bronze-active-small.png',
            "recordBadges": 'https://i.ibb.co/JRXBHJf/Bronze-medical-small.png',
            "IDBadges": 'https://i.ibb.co/0y0SXMt/Bronze-ID-small.png'

        }

        if row_data.get('CampaignType'):
            campaign_max_distance = row_data.get('CampaignDistance')

            if campaign_max_distance < distance:
                print(
                    f'Skipping Care.Trial campaign {site_id} - {distance}km exceeds max range {campaign_max_distance}')
                return False

            trial['CampaignId'] = row_data.get('CampaignId')
            trial['CampaignType'] = row_data.get('CampaignType')
            trial['CampaignStartTime'] = row_data.get('StartTime')
            trial['CampaignStartDate'] = self.format_to_date(row_data.get('StartTime'))
            trial['CampaignEndTime'] = row_data.get('EndTime')
            trial['CampaignEndDate'] = self.format_to_date(row_data.get('EndTime'))
            trial['AdminAddress'] = row_data.get('OwnerNodeScAddress')
            if row_data.get('CampaignFreeServices'):
                trial['CampaignFreeServices'] = row_data.get('CampaignFreeServices')

            print(f"Mark Care.Trial {row_data.get('SiteID')} as {row_data.get('CampaignType')} campaign")

        print("Saving Care.Site: ", trial)
        self.vault.save('TRIALS', trial)
        return self.save_trial(row, questions_data)

    def save_trial(self, row: SearchResponse, questions_data: Map) -> bool:
        row_data = row.getData()
        nct_id = row_data.get('NCTId')
        print(f'Found trial with TrialID: {nct_id}, Location: {row_data.get("Location")}')

        vault_filter_trials = List.of(EqualitySearchFilter.builder().fieldName("TrialID").value(nct_id).build())
        vault_data_trials = self.vault.count('TRIALS_UNIQ', vault_filter_trials)

        if vault_data_trials > 0:
            print(f'Skip Care.Trial with TrialID:{nct_id} as it already present in TRIALS collection')
            return False

        age_text = self.extract_age_text(row_data)
        distance = self.extract_distance(row_data, questions_data)

        matched = self.determine_matching_group(row)
        print(f'Total matched conditions: {matched}')
        if matched > 1:
            match = "Great Match"
            match_text = "This trial matches most of your health conditions"
            match_icon = "https://i.ibb.co/71LJX9N/great-match.png"
        elif matched == 1:
            match = "Good Match"
            match_text = "This trial matches one of your health conditions"
            match_icon = "https://i.ibb.co/X4TNnZp/good-match.png"
        elif matched == 0:
            match = "Interesting Match"
            match_text = "You may be interested in this trial as a healthy volunteer"
            match_icon = "https://i.ibb.co/x3sr94M/Microsoft-Teams-image-23.png"            
        else:
            match = "Smart Match"
            match_text = "Connects you with clinical trials tailored to your specific age, gender, and location."
            match_icon = "https://i.ibb.co/x3sr94M/Microsoft-Teams-image-23.png"

        print(f'match: ', match, match_text)

        trial = {

            # enrich with data from search response
            "SiteID": row_data.get('SiteID'),
            "TrialID": nct_id,
            "LocationFacility": row_data.get('LocationFacility'),

            "StudyType": row_data.get('StudyType'),
            "Country": row_data.get('LocationCountry'),
            "City": row_data.get('LocationCity'),
            "LeadSponsorName": row_data.get('LeadSponsorName'),
            "AgeRange": age_text,
            "TrialName": row_data.get('BriefTitle'),
            "BriefSummary" : row_data.get('BriefSummary'),
            "Eligible": f"{age_text}, {self.extract_gender_text(row_data)}",
            "Location_Text": f"{row_data.get('LocationCity')}",
            "Site_UniqueCode": row_data.get('Site_UniqueCode'),
            "Distance": self.build_distance_text(distance),

            # enrich with data from 6_QUESTIONS
            "Miles": str(self.calculate_max_distance(questions_data)),
            "Miles_Text": questions_data.get('Miles'),
            "Age": self.extract_age(questions_data),
            "Gender": self.extract_gender(questions_data),
            "Conditions": questions_data.get('Conditions') or "None",
            "Limitations": questions_data.get('Limitations'),
            "Ethnicity": questions_data.get('Ethnicity'),

            "userLocationLatitude": questions_data.get('userLocationLatitude'),
            "userLocationLongitude": questions_data.get('userLocationLongitude'),

            # enrich with static data
            "archived": 'false',
            "trialStatus": "NEW",
            "shared": False,

            # enrich with runtime data
            "createdAt": self.current_milli_time(),
            "senderNodeAddress": self.node.info().getScAddress(),
            "transactionalGuid": str(uuid.uuid1()),

            # badges
            "Badges": 'https://i.ibb.co/d6VdwVh/Bronze-active-small.png',
            "recordBadges": 'https://i.ibb.co/JRXBHJf/Bronze-medical-small.png',
            "IDBadges": 'https://i.ibb.co/0y0SXMt/Bronze-ID-small.png',

            "match": match,
            "match_text": match_text,
            "match_icon": match_icon
        }

        if row_data.get('CampaignType'):
            campaign_max_distance = row_data.get('CampaignDistance')

            if campaign_max_distance < distance:
                print(f'Skipping Care.Trial campaign {nct_id} - {distance}km exceeds max range {campaign_max_distance}')
                return False

            trial['CampaignId'] = row_data.get('CampaignId')
            trial['CampaignType'] = row_data.get('CampaignType')
            trial['CampaignStartTime'] = row_data.get('StartTime')
            trial['CampaignStartDate'] = self.format_to_date(row_data.get('StartTime'))
            trial['CampaignEndTime'] = row_data.get('EndTime')
            trial['CampaignEndDate'] = self.format_to_date(row_data.get('EndTime'))
            trial['AdminAddress'] = row_data.get('OwnerNodeScAddress')
            if row_data.get('CampaignFreeServices'):
                trial['CampaignFreeServices'] = row_data.get('CampaignFreeServices')

            print(f"Mark Care.Trial {row_data.get('SiteID')} as {row_data.get('CampaignType')} campaign")

        print("Saving Care.Trial: ", trial)
        self.vault.save('TRIALS_UNIQ', trial)

        return True

    def build_campaign_query(self, questions_data: Map, campaign_type: str, max_distance: int) -> dict:
        # Initialize the Elasticsearch query
        now_ts = self.current_milli_time()
        query = {
            "query": {"bool": {"must": [
                {"query_string": {"query": f"(CampaignType:{campaign_type})"}},
                {"range": {"StartTime": {"lte": now_ts}}},
                {"range": {"EndTime": {"gte": now_ts}}}
            ]}},
            "sort": []
        }

        user_latitude = questions_data.get('userLocationLatitude')
        user_longitude = questions_data.get('userLocationLongitude')
        # Check if user_latitude and user_longitude are not None (for the distance condition)
        if user_latitude and user_longitude:
            # Add the geo_distance filter to search within a certain distance
            query["query"]["bool"]["must"].append({
                "geo_distance": {
                    "distance": f"{max_distance}km",
                    "Location": {"lat": user_latitude, "lon": user_longitude}
                }
            })
            query['sort'].append({
                "_geo_distance": {
                    "Location": {"lat": user_latitude, "lon": user_longitude},
                    "order": "asc"
                }
            })
        print(f'Search criteria {query}')

        return query

    def build_sites_query(self, questions_data: Map) -> dict:

        conditions_match_weight = 10000
        volunteers_match_weight = 5000

        location_match_weight = 1000
        location_decay = 0.5
        location_scale_factor = 0.5

        gender = self.extract_gender(questions_data)
        age = self.extract_age(questions_data)
        raw_conditions = questions_data.get('Conditions')
        user_latitude = questions_data.get('userLocationLatitude')
        user_longitude = questions_data.get('userLocationLongitude')

        main_query = [
            {"range": {"MinimumAgeNumber": {"lte": age}}},
            {"range": {"MaximumAgeNumber": {"gte": age}}}
        ]
        function_score = []

        if gender and gender != 'Rather not say':
            main_query.append({"query_string": {"query": f"(Gender:{gender} or Gender:All)"}})

        if user_latitude and user_longitude:
            max_distance = self.calculate_max_distance(questions_data)
            main_query.append({"geo_distance": {
                "distance": f"{max_distance}km",
                "Location": {"lat": user_latitude, "lon": user_longitude}
            }})
            function_score.append({"linear": {
                "Location": {
                    "origin": {"lat": user_latitude, "lon": user_longitude},
                    "scale": f"{max_distance * location_scale_factor}km",
                    "offset": f"10km",
                    "decay": location_decay
                }},
                "weight": location_match_weight
            })

        if raw_conditions and raw_conditions != 'None':
            conditions = [condition.strip() for condition in raw_conditions.split(",")]
            if len(conditions) > 0:

                for condition in conditions:
                    function_score.append({"filter": {
                        "bool": {"must": [
                            {"query_string": {"query": "HealthyVolunteers:(no OR null)"}},
                            {"match_phrase": {"Condition": condition}}]}},
                        "weight": conditions_match_weight})

                conditions_match_query = [{"match_phrase": {"Condition": condition}} for condition in conditions]

                conditions_query = {
                    "bool": {"must": [
                        {"query_string": {"query": "HealthyVolunteers:(no OR null)"}},
                        {"bool": {"should": conditions_match_query}}]}}

                volunteers_query = {
                    "bool": {"must": [
                        {"query_string": {"query": "HealthyVolunteers:yes"}},
                        {"bool": {"must_not": conditions_match_query}}]}}

                function_score.append({"filter": volunteers_query, "weight": volunteers_match_weight})

                main_query.append({"bool": {"should": [
                    conditions_query,
                    volunteers_query
                ]}})

        query = {
            "query": {"function_score": {
                "query": {"bool": {
                    "must": main_query}},
                "functions": function_score,
                "score_mode": "sum",
                "boost_mode": "sum"}},
            "sort": [],
            "track_scores": True,
            "collapse": {"field": "NCTId.keyword"}
        }

        print(f'Search criteria {query}')
        return query

    def handle(self) -> Map:

        max_trials = 500

        result = HashMap(self.arguments)
        # List of all records from 6_QUESTIONS vault collection
        questions_data_list = self.find_questions_data()
        # Latest record from 6_QUESTIONS vault collection
        if len(questions_data_list) < 1:
            return result

        questions_data = questions_data_list[0]

        # clean-up old data
        self.clean_up_old_results('TRIALS')
        self.clean_up_old_results('TRIALS_UNIQ')

        campaign_indices = 'trials-campaign'
        trials_indices = 'trials-with-geo'
        saved_trials = 0

        saved_trials += self.search_and_save_campaigns(
            campaign_indices, 'Platinum', 500, questions_data, saved_trials, max_trials)

        saved_trials += self.search_and_save_campaigns(
            campaign_indices, 'Gold', 250, questions_data, saved_trials, max_trials)

        saved_trials += self.search_and_save_campaigns(
            campaign_indices, 'Silver', 100, questions_data, saved_trials, max_trials)

        saved_trials += self.search_and_save_trials(
            trials_indices, questions_data, saved_trials, max_trials)

        print(f'Successfully found and saved {saved_trials} Care.Trials and Campaigns')

        print('Execution done')
        return result

    def search_and_save_campaigns(self, campaign_indices: str, campaign_type: str, max_distance: int,
                                  questions_data: Map, saved_trials: int, max_trials: int) -> int:
        query = self.build_campaign_query(questions_data, campaign_type, max_distance)
        campaigns = self.search_and_save(campaign_indices, query, saved_trials, max_trials, questions_data)
        print(f'Found and saved {campaigns} {campaign_type} campaigns')
        return campaigns

    def search_and_save_trials(self, trials_indices: str, questions_data: Map,
                               saved_trials: int, max_trials: int) -> int:
        query = self.build_sites_query(questions_data)
        trials = self.search_and_save(trials_indices, query, saved_trials, max_trials, questions_data)
        print(f'Found and saved {trials} Care.Trials')
        return trials

    def search_and_save(self, indices: str, query: dict,
                        saved_trials: int, max_trials: int, questions_data: Map) -> int:
        if saved_trials >= max_trials:
            print(f'Care.Trails limit of {max_trials} reached. Skip search.')
            return 0

        from_row = 0
        page_number = 0

        print(f'CDN from_row: {from_row}, num_rows: 100, query: {query}')
        cdn_data = self.cdn.raw_search(indices, page_number, 100, query)
        total_count = saved_trials
        saved_count = 0

        while total_count < max_trials and len(cdn_data) > 0:
            print(f'CDN response: {cdn_data}')
            for row in cdn_data:
                if total_count < max_trials:
                    if self.save_site(row, questions_data):
                        total_count += 1
                        saved_count += 1

            if total_count < max_trials:
                page_number += 1
                print(f'CDN page_number: {page_number}, num_rows: 100, query: {query}')
                cdn_data = self.cdn.raw_search(indices, page_number, 100, query)

        print(f'Successfully saved {saved_count} Care.Trials')
        return saved_count


def execute(context: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {context}')
    result = CustomPythonEventHandler(context).handle()
    return result
