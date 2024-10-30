import java
import time

from abc import ABC, abstractmethod

HandlerExecutionContext = java.type('care.solve.node.core.context.HandlerExecutionContext')
HashMap = java.type('java.util.HashMap')
Map = java.type('java.util.Map')
List = java.type('java.util.List')
SearchRequest = java.type('care.solve.node.core.model.cdn.SearchRequest')
SearchResponse = java.type('care.solve.node.core.model.cdn.SearchResponse')
QueryCondition = java.type('care.solve.node.core.model.cdn.QueryCondition')
QueryConditions = java.type('care.solve.node.core.model.cdn.QueryConditions')
SimpleQueryBuilder = java.type('care.solve.node.core.model.cdn.SimpleQueryBuilder')
WalletProfile = java.type('care.solve.node.core.model.mainnetnode.WalletProfile')
PhoneProfile = java.type('care.solve.node.core.model.mainnetnode.PhoneProfile')
ContactProfile = java.type('care.solve.node.core.model.mainnetnode.ContactProfile')
ProfileType = java.type('care.solve.node.core.model.mainnetnode.ProfileType')
ProfileAttribute = java.type('care.solve.node.core.model.mainnetnode.ProfileAttribute')
NodeInfo = java.type("care.solve.node.core.model.NodeInfo")
EqualitySearchFilter = java.type("care.solve.node.core.model.query.EqualitySearchFilter")
NumericBoundsSearchFilter = java.type("care.solve.node.core.model.query.NumericBoundsSearchFilter")
SearchQueryFilter = java.type("care.solve.node.core.model.query.SearchQueryFilter")


class CDN:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context
        self.index = 'trials-with-geo'

    def findAll(self, parameters: SearchRequest) -> List:
        return self.context.getCareDataNodeProvider().findAll(self.index, parameters)

    def findFirst(self, parameters: SimpleQueryBuilder) -> SearchResponse:
        transaction_criteria = SimpleQueryBuilder.eq('_transaction_id',
                                                     self.context.getEvent().getPayload().get('transactionId'))
        return self.context.getCareDataNodeProvider().findFirst(self.index, SimpleQueryBuilder.aand(parameters,
                                                                                                    transaction_criteria))

    def raw_search(self, from_row, num_rows, search_request) -> List:
        return self.context.getCareDataNodeProvider().rawSearch(self.index, from_row, num_rows, search_request)


class Wallet:
    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def getWalletProfile(self) -> WalletProfile:
        return self.context.getMainNetNodeProvider().getMainNetProfile(ProfileType.WALLET)

    def getPhoneProfile(self) -> PhoneProfile:
        return self.context.getMainNetNodeProvider().getMainNetProfile(ProfileType.PHONE)

    def getContactProfile(self) -> ContactProfile:
        return self.context.getMainNetNodeProvider().getMainNetProfile(ProfileType.CONTACT)

    def updateWalletProfile(self, data: Map, attributeMapping: Map) -> Map:
        self.context.getMainNetNodeProvider().updateWalletProfile(data, attributeMapping)
        return data

    def updatePhoneProfile(self, data: Map, attributeMapping: Map) -> Map:
        self.context.getMainNetNodeProvider().updatePhoneProfile(data, attributeMapping)
        return data

    def updateContactProfile(self, data: Map, attributeMapping: Map) -> Map:
        self.context.getMainNetNodeProvider().updateContactProfile(data, attributeMapping)
        return data


class Vault:

    def __init__(self, context: HandlerExecutionContext):
        self.context = context

    def save(self, collection: str, data: Map) -> Map:
        vault = self.context.getVaultStorage(collection)
        guid = vault.save(data)
        return vault.getByGuid(guid)

    def update(self, collection: str, criteria: List, data: Map, insertIfAbsent: bool) -> Map:
        vault = self.context.getVaultStorage(collection)
        print(f'==> [CustomPythonEventHandler#d]: {data}')
        guid = vault.update(criteria, data, insertIfAbsent)
        print(f'==> [CustomPythonEventHandler#d]: {guid}')
        return vault.getByGuid(guid)

    def search(self, collection: str, filter: List) -> List:
        vault = self.context.getVaultStorage(collection)
        return vault.search(filter)


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
        self.wallet = Wallet(context)
        self.node = Node(context)

    @abstractmethod
    def handle(self) -> Map:
        pass


class CustomPythonEventHandler(PythonEventHandler):
    def handle(self) -> Map:
        print("Custom event handler budddgettt")
        
        result = HashMap(self.arguments)

        #count saved trials
        #vault_filter = List.of(EqualitySearchFilter.builder().fieldName("transactionalGuid").value(self.event_payload.get('transactionalGuid')).build())
        #vault_data = self.vault.search('RECORD_DATA', vault_filter)
        #vault_data_len= len(vault_data)
        #vault_data_size=vault_data_len-1
        # transaction_criterion = EqualitySearchFilter.builder().fieldName("transactionalGuid").value(self.event_payload.get("transactionalGuid")).build()
        # participant_criterion = EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(self.event_payload.get("senderNodeAddress")).build()
        # vault_filter = List.of(transaction_criterion, participant_criterion)
            # subscription_data = self.vault.search('TRIAL_ADMIN_SUBSCRIPTION', vault_filter)
            # print("subscription_data",subscription_data)        
            
        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("senderNodeAddress").value(self.node.info().getScAddress()).build())
        print("vault_filter",vault_filter)
        print("senderNodeAddressss",self.event_payload.get("senderNodeAddress"))
        
        subscription_cost = 0
        silver_cost = 0
        gold_cost= 0
        platinum_cost = 0
        

        # if (self.event_payload.get("campaignType")is not None):
        #     transaction_type = self.event_payload.get("campaignType")
        #     subscription_cost = self.event_payload.get("totalSolveCost")
            
        #     print("transaction_type",transaction_type)
        #     print("transaction_cost",transaction_cost)

        # elif (self.event_payload.get("trialSubscriptionStatus")is not None):
        #     transaction_type = "Annual Subscription"
        #     transaction_cost = self.event_payload.get("totalSolveCost")
        #     print("transaction_type",transaction_type)
        #     print("transaction_cost",transaction_cost)

        # if (self.event_payload.get("campaignType")is not None):
        #     campaignType = self.event_payload.get("campaignType")
        #     if campaignType is 'Silver':
        #         silver_cost = self.event_payload.get("totalSolveCost")
        #     elif campaignType is 'Gold':
        #         gold_cost = self.event_payload.get("totalSolveCost")
        #     elif campaignType is 'Platinum':        
        #         platinum_cost = self.event_payload.get("totalSolveCost")
        
        #     print("campaignType",campaignType)
        #     print("silver_cost",silver_cost)
        #     print("gold_cost",gold_cost)
        #     print("platinum_cost",platinum_cost)



        
        silver_cost = 10000
        print("silver_cost",silver_cost)
      


       
       # vault_filterbyId = List.of(EqualitySearchFilter.builder().fieldName("recordStatus").value('pending').build())
        data = {
                "transactionalGuid": self.event_payload.get('transactionalGuid'),
                "senderNodeAddress": self.event_payload.get('senderNodeAddress'),
                "silver_cost": silver_cost,
                # "silver_cost": silver_cost,
                # "gold_cost": gold_cost,
                # "platinum_cost": platinum_cost
            }
 
        print("data",data)
        #self.vault.save('TWO', data)
        self.vault.update('TRANSACTION_HISTORY', vault_filter, data, False)   
        #self.vault.save('TRANSACTION_HISTORY', data)
        result.putAll(self.event_payload)
        print("result", result)

        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result