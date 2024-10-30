import java
import math
import re

from abc import ABC, abstractmethod

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
NodeInfo = java.type("care.solve.node.core.model.NodeInfo")
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")


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
        self.node = Node(context)

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

    @staticmethod
    def __gender_age_ethnicity_text(payload):
        gender = payload.get('Gender')
        if gender is not None and gender == "Rather not say":
            return f"{payload.get('Age')} years"
            # return f"{payload.get('Age')} years, {payload.get('Ethnicity')}"
        else:
            return f"{gender}, {payload.get('Age')} years"
            # return f"{gender}, {payload.get('Age')} years, {payload.get('Ethnicity')}"

    @staticmethod
    def __distance_text(payload):
        distance_text = str(payload.get('Distance'))  # 5 miles away #calculated trial distance
        distance_numbers = re.findall(r'\d+', distance_text)
        if distance_numbers:
            user_distance_text = int(distance_numbers[0])  # 5
            user_distance_text = "Nearest location: " + str(user_distance_text) + " km away"
        else:
            user_distance_text = "Not Available"
        print("user_distance_text: ", user_distance_text)
        return user_distance_text

    def __extract_distance(self, site_data) -> int:

        guid = self.event_payload.get("transactionalGuid")

        user_latitude = self.event_payload.get('userLocationLatitude')
        user_longitude = float(self.event_payload.get('userLocationLongitude'))

        site_latitude = site_data.get("Latitude")
        site_longitude = site_data.get("Longitude")

        if site_latitude and site_longitude and user_latitude and user_longitude:
            distance = self.__calculate_distance(user_latitude, user_longitude,
                                                 float(site_latitude), float(site_longitude))

            print(f"Calculated distance for Lead {guid}: {distance}km")
            return distance
        else:
            print(f"Couldn't calculate distance for Lead {guid} as it without 'Location'")
            return -1

    def __is_matches(self, site_data) -> bool:

        guid = self.event_payload.get("transactionalGuid")
        miles = self.event_payload.get("Miles")

        if miles == 'Anywhere':
            print(f"Lead {guid} matches participant has anywhere max distance")
            return True

        participant_max_distance = int(float(miles))
        if participant_max_distance >= 20000:
            print(f"Lead {guid} matches participant has more than 20000km max distance")
            return True

        distance = self.__extract_distance(site_data)
        if distance <= participant_max_distance:
            print(f"Lead {guid} matches as calculated {distance}km distance is less than "
                  f"participant max {participant_max_distance}km distance")
            return True
        else:
            print(f"Lead {guid} not matches as calculated {distance}km distance is greater than "
                  f"participant max {participant_max_distance}km distance")
            return False

    def __calculate_badges(self):
        print("Fetching badges")
        sender_criterion = EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.node.info().getScAddress()).build()
        status_criterion = EqualitySearchFilter.builder().fieldName("trialStatus").value("SAVED").build()

        vault_filter_trials = List.of(sender_criterion, status_criterion)
        vault_data_trials = self.vault.search('TRIALS', vault_filter_trials)
        vd_size = len(vault_data_trials)
        print("Care.Trials saved size: ", vd_size)

        print("sender_node_address", self.sender_node_address)

        if vd_size >= 3:
            badge = 'https://i.ibb.co/Rh4t0wm/Silver-Active-small.png'
        else:
            badge = 'https://i.ibb.co/d6VdwVh/Bronze-active-small.png'

        print("Badge fetched: ", badge)
        badges_filter = List.of(
            EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(self.sender_node_address).build())
        badges_data = self.vault.search('PARTICIPANT_ADMIN_TRIALS', badges_filter)
        for item in badges_data:
            filter_by_id = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
                item.get('transactionalGuid')).build())
            item.put('Badges', badge)
            badges_updated = self.vault.update('PARTICIPANT_ADMIN_TRIALS', filter_by_id, item, False)
            print("BADGES TRIAL", badges_updated)

    def __save_lead_entity(self, site_data):
        # Assuming vault_data_trials is a list of dictionaries
        # You may need to specify an index to access a particular dictionary
        # For now, let's assume you want the first dictionary in the list
        print("Age range from payload: ", self.event_payload.get('AgeRange'))
        print("Age range from admin trial: ", site_data.get('AgeRange'))

        # 500 miles away #Anywhere  #user max distance
        miles_text = str(self.event_payload.get('Miles_Text')) or "Anywhere"

        print("Miles text: ", miles_text)
        print("Badges: ", self.event_payload.get('Badges'))

        location_miles_text = f"{site_data.get('City')}\nWilling to travel {miles_text}"

        trial_id = self.event_payload.get("TrialID")
        trial = {
            "senderNodeAddress": self.sender_node_address,
            "transactionalGuid": self.event_payload.get("transactionalGuid"),
            "SiteID": site_data.get("SiteID"),
            "TrialID": trial_id,
            "LocationFacility": site_data.get('LocationFacility'),

            "Miles": miles_text,
            "StudyType": self.event_payload.get('StudyType'),
            "Country": site_data.get('Country'),
            "City": site_data.get('City'),
            "LeadSponsorName": site_data.get('LeadSponsorName'),
            "Age": self.event_payload.get('Age'),
            "Limitations": self.event_payload.get('Limitations'),
            "Conditions": self.event_payload.get('Conditions'),
            "AgeRange": self.event_payload.get('AgeRange'),
            "Gender": self.event_payload.get('Gender'),
            "TrialName": self.event_payload.get('TrialName'),
            "BriefSummary" : self.event_payload.get('BriefSummary'),

            "Distance": self.event_payload.get('Distance'),
            "Site_UniqueCode": site_data.get('Site_UniqueCode'),
            "AdminAddress": self.node.info().getScAddress(),
            "GenderAgeEthnicity_Text": self.__gender_age_ethnicity_text(self.event_payload),
            "Distance_Text": self.__distance_text(self.event_payload),
            "Location_Miles_Text": location_miles_text,
            # "Location_Text": f"{site_data.get('City')}, {site_data.get('Country')}",
            "Location_Text": f"{site_data.get('City')}",
            "Ethnicity": self.event_payload.get('Ethnicity'),
            "Eligible": self.event_payload.get('Eligible'),
            # "GenderAgeCity": f"{site_data.get('Gender')}, {site_data.get('Age')}, {site_data.get('City')}",
            "GenderAgeCity": f"{self.event_payload.get('Gender')}, {self.event_payload.get('Age')}, {site_data.get('City')}",

            "TrialNameStatus": f"{site_data.get('TrialName')}-Active",
            "AdditionalTrialInfo": site_data.get('AdditionalTrialInfo'),
            "Inclusion": site_data.get('Inclusion'),
            "Activity": site_data.get('Activity'),
            "TrialDuration": site_data.get('TrialDuration'),
            "Compensation": site_data.get('Compensation'),
            "Exclusion": site_data.get('Exclusion'),
            "Frequency": site_data.get('Frequency'),
            "trialStatus": "NEW",
            "isSubscriptionActive": self.is_subscription_active(trial_id),

            # badges
            "Badges": self.event_payload.get('Badges'),
            "recordBadges": self.event_payload.get('recordBadges'),
            "IDBadges": self.event_payload.get('IDBadges'),
            
            "eligibleStatus": "Pending"
        }

        print(f"Care.Trial: {trial}")
        trial_filter = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
            self.event_payload.get('transactionalGuid')).build())
        self.vault.update('PARTICIPANT_ADMIN_TRIALS', trial_filter, trial, True)

    def handle(self) -> Map:

        result = HashMap(self.arguments)

        trial_id = self.event_payload.get("TrialID")
        guid = self.event_payload.get("transactionalGuid")
        print("TrialID: ", trial_id)

        self.__calculate_badges()

        site_filter = List.of(
            EqualitySearchFilter.builder().fieldName("AdminAddress").value(self.node.info().getScAddress()).build(),
            EqualitySearchFilter.builder().fieldName("TrialID").value(trial_id).build())
        site_data_list = self.vault.search('TRIALS', site_filter)
        print("site_data_list: ", site_data_list)

        if len(site_data_list) == 0:
            print(f'No found activated sites with TrialID: {trial_id} for lead {guid}')
            return result

        site_data = site_data_list[0]

        if self.__is_matches(site_data):
            self.__save_lead_entity(site_data)

        return result

    def is_subscription_active(self, trial_id: str) -> bool:
        trial_id_criteria = EqualitySearchFilter.builder().fieldName("SiteID").value(trial_id).build()
        return len(self.vault.search('TRIAL_ADMIN_SUBSCRIPTION', List.of(trial_id_criteria))) > 0


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
