import java

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

    def handle(self) -> Map:

        result = HashMap(self.arguments)

        trial_id = self.event_payload.get("SiteID")
        print("pppp event payload", trial_id)

        # badge = {
        #        "Badges": self.event_payload.get('Badges'),
        #        "transactionalGuid": self.event_payload.get('transactionalGuid')
        # }

        print("Fetching badges")
        sender_criterion = EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(
            self.node.info().getScAddress()).build()
        status_criterion = EqualitySearchFilter.builder().fieldName("trialStatus").value("SAVED").build()

        # vd_size=0
        vault_filter_trials = List.of(sender_criterion, status_criterion)
        vault_data_trials = self.vault.search('TRIALS', vault_filter_trials)
        vd_size = len(vault_data_trials)
        print("Care.Trials saved size: ", vd_size)

        # if vd_size>0:
        # badge_loc=vd_size-1
        # badge= vault_data_trials[badge_loc].get('Badges')
        # else:
        # badge = "https://i.ibb.co/pxX91Jv/Bronze-badge-Active.png"

        print("sender_node_address", self.sender_node_address)

        if vd_size >= 3:
            # badge = 'https://i.ibb.co/D1jCLDT/Silver.png'
            badge = 'https://i.ibb.co/Rh4t0wm/Silver-Active-small.png'

        else:
            # badge = "https://i.ibb.co/pxX91Jv/Bronze-badge-Active.png"
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

        # vd_size = len(vault_data_participants)
        # print("size", vd_size)
        # clicks = vd_size-1
        # print("clicks", clicks)

        # Badges criteria
        # if clicks < 20:
        #     badge = 'https://d1fgr2dke6q42b.cloudfront.net/uat/media/f116d56b-00a4-4091-932b-240e9cf64504/recruitment.png'
        # elif clicks >= 20:
        #    badge = 'https://d1fgr2dke6q42b.cloudfront.net/uat/media/f116d56b-00a4-4091-932b-240e9cf64504/clinical.png'

        # badge = 'https://i.ibb.co/vzLB4PC/Care-Trials-Badges-A-Bronze-2x.png'

        # data from trial admin (TRIALS)
        vault_filter_trials = List.of(EqualitySearchFilter.builder().fieldName("SiteID").value(trial_id).build())
        vault_data_trials = self.vault.search('TRIALS', vault_filter_trials)
        print("pppp vault_data_trials", vault_data_trials)

        #        trialSenderNodeAddress=self.event_payload.get("senderNodeAddress")
        #        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(trialSenderNodeAddress).build())
        #        data = self.vault.search('PARTICIPANT_ADMIN_TRIALS', vault_filter)
        #        for item in data:
        #            item.put("Badges", self.event_payload.get("Badges"))
        #            filterById = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(item.get('transactionalGuid')).build())
        #            updated = self.vault.update('PARTICIPANT_ADMIN_TRIALS', filterById, item, False)
        #            print("BADGES TRIAL", updated)

        import re

        if not vault_data_trials:
            print("vault_data_trials is empty")
        else:
            # Assuming vault_data_trials is a list of dictionaries
            # You may need to specify an index to access a particular dictionary
            # For now, let's assume you want the first dictionary in the list
            first_trial = vault_data_trials[0]
            distance_text = str(self.event_payload.get('Distance'))  # 5 miles away #calculated trial distance
            distance_numbers = re.findall(r'\d+', distance_text)
            if distance_numbers:
                user_distance_text = int(distance_numbers[0])  # 5
                user_distance_text = "Nearest location: " + str(user_distance_text) + " km away"

            else:
                user_distance_text = "Not Available"
            print("user_distance_text: ", user_distance_text)
            print("Age range from payload: ", self.event_payload.get('AgeRange'))
            print("Age range from admin trial: ", first_trial.get('AgeRange'))

            miles_text = str(
                self.event_payload.get('Miles_Text')) or "Anywhere"  # 500 miles away #Anywhere  #user max distance

            print("Miles text: ", miles_text)
            print("trials distance text: ", user_distance_text)

            # badge = self.event_payload.get('Badges') or 'https://i.ibb.co/pxX91Jv/Bronze-badge-Active.png'

            print("Badges: ", self.event_payload.get('Badges'))

            trial = {
                "senderNodeAddress": self.sender_node_address,
                "transactionalGuid": self.event_payload.get("transactionalGuid"),
                "SiteID": self.event_payload.get("SiteID"),
                "TrialID": self.event_payload.get('TrialID'),
                "LocationFacility": self.event_payload.get('LocationFacility'),

                "Miles": miles_text,
                "StudyType": self.event_payload.get('StudyType'),
                "Country": self.event_payload.get('Country'),
                "City": self.event_payload.get('City'),
                "LeadSponsorName": self.event_payload.get('LeadSponsorName'),
                "Age": self.event_payload.get('Age'),
                "Limitations": self.event_payload.get('Limitations'),
                "Conditions": self.event_payload.get('Conditions'),
                "AgeRange": self.event_payload.get('AgeRange'),
                # "Badges" : self.event_payload.get('Badges'),
                "Gender": self.event_payload.get('Gender'),
                "TrialName": self.event_payload.get('TrialName'),
                "BriefSummary" : self.event_payload.get('BriefSummary'),
                
                "Distance": self.event_payload.get('Distance'),
                "Site_UniqueCode": self.event_payload.get('Site_UniqueCode'),
                "AdminAddress": first_trial.get('AdminAddress'),  # Assuming we want AdminAddress from the first trial
                # "GenderAgeEthnicity_Text": str(self.event_payload.get('Gender')) + ", " + str(self.event_payload.get('Age')) + " years, " + str(self.event_payload.get('Ethnicity')),
                "GenderAgeEthnicity_Text": str(self.event_payload.get('Gender')) + ", " + str(
                    self.event_payload.get('Age')) + " years",
                "Distance_Text": str(user_distance_text),
                # "Location_Miles_Text": str(self.event_payload.get('City')) + ", " + str(self.event_payload.get('Country')) + "\nWilling to travel " + miles_text,
                "Location_Miles_Text": str(self.event_payload.get('City')) + ", " + "\nWilling to travel " + miles_text,

                # "Location_Text": str(self.event_payload.get('City')) + ", " + str(self.event_payload.get('Country')),
                "Location_Text": str(self.event_payload.get('City')),

                "Ethnicity": self.event_payload.get('Ethnicity'),
                "Eligible": self.event_payload.get('Eligible'),

                "GenderAgeCity": str(self.event_payload.get('Gender')) + ", " + str(
                    self.event_payload.get('Age')) + ", " + self.event_payload.get('City'),
                "TrialNameStatus": str(self.event_payload.get('TrialName')) + "-" + "Active",

                "AdditionalTrialInfo": first_trial.get('AdditionalTrialInfo'),
                "Inclusion": first_trial.get('Inclusion'),
                "Activity": first_trial.get('Activity'),
                "TrialDuration": first_trial.get('TrialDuration'),
                "Compensation": first_trial.get('Compensation'),
                "Exclusion": first_trial.get('Exclusion'),
                "Frequency": first_trial.get('Frequency'),
                "trialStatus": "NEW",
                "isSubscriptionActive": self.is_subscription_active(trial_id),
                # "allowCampaignPurchase": self.event_payload.get('allowCampaignPurchase'),

                # badges
                # "Badges": badge,
                "Badges": self.event_payload.get('Badges'),
                "recordBadges": self.event_payload.get('recordBadges'),
                "IDBadges": self.event_payload.get('IDBadges')
            }

            print(f"Care.Trial: {trial}")
            trial_filter = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(
                self.event_payload.get('transactionalGuid')).build())
            self.vault.update('PARTICIPANT_ADMIN_TRIALS', trial_filter, trial, True)

        return result

    def is_subscription_active(self, trial_id: str) -> bool:
        trial_id_criteria = EqualitySearchFilter.builder().fieldName("SiteID").value(trial_id).build()
        return len(self.vault.search('TRIAL_ADMIN_SUBSCRIPTION', List.of(trial_id_criteria))) > 0


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result
