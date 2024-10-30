import math
import re
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime

import java
from datetime import datetime
import os
import pandas as pd
import secrets
import requests
import re
import nltk
from nltk.corpus import wordnet

nltk.download('wordnet')



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
    
    def current_data() -> str:
        current_date = datetime.now()
        return current_date.strftime('%Y_%m_%d')

    def extract_diseases(self, text: str) -> str:
        diseases = set()
        for word in text.split():
            synonyms = set()
            for synset in wordnet.synsets(word):
                for lemma in synset.lemmas():
                    synonyms.add(lemma.name())
            diseases.add(word)
            diseases.update(synonyms)
        return ", ".join(diseases)

    def extract_age(self, age_string: str):
        parts = age_string.split()
        if len(parts) == 1:
            try:
                return int(parts[0])
            except ValueError:
                return None
        num, unit = parts
        try:
            num = int(num)
        except ValueError:
            return None
        if unit.lower() in ['year', 'years']:
            return num
        elif unit.lower() in ['month', 'months']:
            return round(num / 12, 2)
        elif unit.lower() in ['week', 'weeks']:
            return round(num / 52, 2)
        elif unit.lower() in ['day', 'days']:
            return round(num / 365, 2)
        else:
            match = re.search(r'\d+', age_string)
            if match:
                return int(match.group())
            return None

    def extract_criteria(self, criteria_text: str) -> (str, str):
        inclusion_criteria = []
        exclusion_criteria = []
        criteria_list = criteria_text.split('*')
        for criteria in criteria_list:
            criteria = criteria.strip()
            if criteria.startswith("Inclusion Criteria:"):
                inclusion_criteria.extend(criteria.replace("Inclusion Criteria:", "").strip().split('\n'))
            elif criteria.startswith("Exclusion Criteria:"):
                exclusion_criteria.extend(criteria.replace("Exclusion Criteria:", "").strip().split('\n'))
        return "\n".join(inclusion_criteria), "\n".join(exclusion_criteria)

    def extract_conditions(self, trial_data: dict) -> str:
        conditions = trial_data.get("conditionsModule", {}).get("conditions", [])
        return ", ".join(conditions)

    def extract_study_type(self, trial_data: dict) -> str:
        try:
            return trial_data["designModule"]["studyType"]
        except KeyError:
            return "Unknown"

    def extract_start_date(self, trial_data: dict) -> str:
        start_date = trial_data["statusModule"].get("startDateStruct", {}).get("date", "null")
        if start_date == "null":
            return None
        return start_date

    def extract_end_date(self, trial_data: dict) -> str:
        return trial_data["statusModule"].get("completionDateStruct", {}).get("date", "null")

    def extract_gender(self, trial_eligibility: dict) -> str:
        if trial_eligibility:
            return trial_eligibility.get("sex", "Unknown")
        else:
            return "Unknown"

    def extract_site_address(self, site_data: dict) -> str:
        location_country = site_data.get("country", "Unknown")
        location_city = site_data.get("city", "Unknown")
        location_zip = site_data.get("zip", "Unknown")
        location_facility = site_data.get("facility", "Unknown")
        location_parts = [location_facility, location_city, location_country, location_zip]
        filtered_location_parts = [part for part in location_parts if part != "Unknown"]
        if not filtered_location_parts:
            site_address = "Unknown"
        else:
            site_address = ", ".join(filtered_location_parts)
        return site_address

    def extract_geo_data(self, site_data: dict) -> (str, str):
        if "geoPoint" in site_data:
            lat = site_data["geoPoint"].get("lat")
            lon = site_data["geoPoint"].get("lon")
        else:
            lat = None
            lon = None
        return lat, lon

    def extract_healthy_volunteers(self, trial_eligibility: dict) -> str:
        if trial_eligibility.get('healthyVolunteers'):
            return "yes"
        return "no"

    def extract_recruitment_status(self, trial_data: dict, site_data: dict) -> str:
        if 'status' in site_data and site_data['status']:
            return site_data['status']
        return trial_data["statusModule"]["overallStatus"]

    def load_trials(self) -> [dict]:
        base_url = "https://clinicaltrials.gov/api/v2/studies"
        active_statuses = ['NOT_YET_RECRUITING', 'RECRUITING', 'AVAILABLE', 'ENROLLING_BY_INVITATION']

        params = {
        "format": "json",
        "filter.overallStatus": '|'.join(active_statuses),
        "pageSize": 1000
        }
        
        next_page_token = None
        while True:
            if next_page_token:
                params["pageToken"] = next_page_token
            else:
                params.pop("pageToken", None)
            try:
                page_response = requests.get(base_url, params=params)
                page_response.raise_for_status()
                page_data = page_response.json()  # Ensure to call json() method to get JSON data

                if "studies" in page_data and page_data["studies"]:
                    yield from page_data["studies"]
                    print(f"Successfully loaded {len(page_data['studies'])} active Care.Trials")

                if "nextPageToken" in page_data:
                    next_page_token = page_data["nextPageToken"]
                else:
                    break

            except requests.exceptions.HTTPError as e:
                print(f"HTTP error occurred while fetching data with nextPageToken: {next_page_token}: {e}")
            except requests.exceptions.JSONDecodeError as e:
                print(f"Error decoding JSON response with nextPageToken: {next_page_token}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred with nextPageToken: {next_page_token}: {e}")



    def to_site_data(self, trial_data: dict, site_data: dict, index: int) -> dict:
        active_statuses = ['NOT_YET_RECRUITING', 'RECRUITING', 'AVAILABLE', 'ENROLLING_BY_INVITATION']
        recruitment_status = self.extract_recruitment_status(trial_data, site_data)
        if recruitment_status not in active_statuses:
            return {}

        trial_info = trial_data["identificationModule"]
        nct_id = trial_info["nctId"]
        unique_code = secrets.token_hex(5)

        trial_eligibility = trial_data.get("eligibilityModule", {})
        max_age = trial_eligibility.get("maximumAge", "100")
        min_age = trial_eligibility.get("minimumAge", "0")

        inclusion_criteria, exclusion_criteria = self.extract_criteria(trial_eligibility.get("eligibilityCriteria", ""))

        lat, lon = self.extract_geo_data(site_data)

        trials = {
            "NCTId": nct_id,
            "SiteID": f"SA{nct_id}_{index}",
            "BriefTitle": trial_info["briefTitle"],
            "OfficialTitle": trial_info.get("officialTitle", "Unknown"),
            "OrgFullName": trial_info["organization"]["fullName"],
            "OverallStatus": trial_data["statusModule"]["overallStatus"],
            "Condition": self.extract_conditions(trial_data),
            "Gender": self.extract_gender(trial_eligibility),
            "MaximumAge": max_age,
            "MinimumAge": min_age,
            "MaximumAgeNumber": self.extract_age(max_age),
            "MinimumAgeNumber": self.extract_age(min_age),
            "HealthyVolunteers": self.extract_healthy_volunteers(trial_eligibility),
            "StudyType": self.extract_study_type(trial_data),
            "LeadSponsorName": trial_data["sponsorCollaboratorsModule"]["leadSponsor"]["name"],
            "StartDate": self.extract_start_date(trial_data),
            "EndDate": self.extract_end_date(trial_data),
            "LocationCountry": site_data.get("country", "Unknown"),
            "LocationCity": site_data.get("city", "Unknown"),
            "LocationZip": site_data.get("zip", "Unknown"),
            "LocationFacility": site_data.get("facility", "Unknown"),
            "FDAAA801Violation": "Not Available",
            "Latitude": lat,
            "Longitude": lon,
            "RecruitmentStatus": recruitment_status,
            "UniqueCode": unique_code,
            "Site_UniqueCode": f"{unique_code}_{index}",
            "BriefSummary": trial_data.get("descriptionModule", {}).get("briefSummary", "Unknown"),
            "InclusionCriteria": inclusion_criteria,
            "ExclusionCriteria": exclusion_criteria,
            "Contact": ", ".join([contact.get("name", "Unknown") for contact in site_data.get("contacts", [])]),
            "SiteName": site_data.get("facility", "Unknown"),
            "SiteAddress": self.extract_site_address(site_data),
            "Rank": "",
            "ContactInfo": "",
            "SiteWalletID": ""
        }

        return trials

    def trial_to_sites(self, trial_data: dict) -> [dict]:
        trial_sites = []
        protocol_section = trial_data["protocolSection"]
        if "contactsLocationsModule" in protocol_section and "locations" in protocol_section["contactsLocationsModule"]:
            for index, location in enumerate(protocol_section["contactsLocationsModule"]["locations"], start=1):
                site_data = self.to_site_data(protocol_section, location, index)
                if site_data:
                    trial_sites.append(site_data)
        return trial_sites
        

        
    def handle(self) -> Map:
        print("Custom event handler-- sync_cdn.pyyy")
        nct_ids = set()
        query = {
            "query": {
                "match_all": {}
                }
        }
        cdn_data = self.cdn.raw_search('trials-with-geo', 0, 100, query)
        if 'NCTId' in cdn_data.columns:
            nct_ids.update(cdn_data['NCTId'].unique())
        existing_nct_ids = nct_ids
        
        all_sites = []

        for study in self.load_trials():
            all_sites.extend(self.trial_to_sites(study))

        df = pd.DataFrame(all_sites)
        df = df[df['StartDate'].notnull()]
        df = df[~df['NCTId'].isin(existing_nct_ids)]

        if not df.empty:
            self.cdn.save('trials-with-geo', df) 

        print(f"Successfully uploaded new active Care.Sites")
        print("sync_cdn")
        

def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
        