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
        # vault_data = self.vault.search('BUDGET', vault_filter)
        # print("vault_data",vault_data)

        budget= self.event_payload.get('Budget')
        print("budget",budget)

        print("SiteIDDDD",self.event_payload.get("SiteID"))

        
        vault_filter = List.of(EqualitySearchFilter.builder().fieldName("SiteID").value(self.event_payload.get("SiteID")).build())
        print("siteidddd vault_filter",vault_filter)

        # subscription_spent=0
        # campaigns_spent=0
        # leads_spent=0
        
        # vault_data_subscription = self.vault.search('TRIAL_ADMIN_SUBSCRIPTION', vault_filter)
        # for rows in vault_data_subscription:
        #     total_solve_cost = rows.get('totalSolveCost')
        #     if total_solve_cost is not None and isinstance(total_solve_cost, (int, float)):
        #         subscription_spent += int(total_solve_cost)
        # print("subscription_spent",subscription_spent)


        # vault_data_campaigns = self.vault.search('TRIAL_ADMIN_CAMPAIGN', vault_filter)
        # for rows in vault_data_campaigns:
        #     total_solve_cost = rows.get('totalSolveCost')
        #     if total_solve_cost is not None and isinstance(total_solve_cost, (int, float)):
        #         campaigns_spent += int(total_solve_cost)   
        # print("campaigns_spent",campaigns_spent)
            
            
        # vault_data_leads = self.vault.search('PARTICIPANT_ADMIN_TRIALS_SAVED', vault_filter)
        # for rows in vault_data_leads:
        #     total_solve_cost = rows.get('totalSolveCost')
        #     if total_solve_cost is not None and isinstance(total_solve_cost, (int, float)):
        #         leads_spent += int(total_solve_cost)  
        # print("leads_spent",leads_spent)
       
        vault_budget = self.vault.search('BUDGET', vault_filter)     
        #total_expenses = vault_budget[0].get('total_expenses') or 0  
        from datetime import datetime

        current_datetime = datetime.now()
        current_date = current_datetime.date()
        formatted_date = current_date.strftime("%d-%m-%Y")
        updated_date = formatted_date
        print("updated_date",updated_date)

        if vault_budget:
            print("inside if ")            
            total_expenses = vault_budget[0].getOrDefault('total_expenses', 0)
            remaining_budget = vault_budget[0].getOrDefault('remaining_budget', 0)            
            previous_budget = vault_budget[0].getOrDefault('Budget', 0) 
            print("previous_budget ",previous_budget)
            new_requested_amount =self.event_payload.get('requested_amount')    
            print("new_requested_amount ",new_requested_amount)            
            budget= previous_budget+new_requested_amount
            remaining_budget = budget-total_expenses
            print("total budget ",budget)            
            print("total_expenses ",total_expenses)
            print("remaining_budge ",remaining_budget)
            
            data = {
                #"transactionalGuid": self.event_payload.get('transactionalGuid'),
                #"TrialID": self.event_payload.get('TrialID'),
                #"SiteID": self.event_payload.get('SiteID'),
                "Budget": budget,
                #"total_expenses": total_expenses,
                "remaining_budget": remaining_budget,
                "Comments": self.event_payload.get('Comments'),
                "updated_date" : updated_date              
            }
 
            print("data",data)
            self.vault.update('BUDGET', vault_filter, data, False)   

    #     else:
    #         print("inside else ")                        
    #         total_expenses = 0
    #         budget = self.event_payload.get('Budget')  
    #         print("false ",total_expenses)
                    
    #     budget = self.event_payload.get('Budget')            
    #     print("total_expenses, budget",total_expenses, budget)

    #     remaining_budget = budget-total_expenses
        


       
    #    # vault_filterbyId = List.of(EqualitySearchFilter.builder().fieldName("recordStatus").value('pending').build())
    #     data = {
    #             #"transactionalGuid": self.event_payload.get('transactionalGuid'),
    #             #"TrialID": self.event_payload.get('TrialID'),
    #             "SiteID": self.event_payload.get('SiteID'),
    #             "Budget": self.event_payload.get('Budget'),
    #             "total_expenses": total_expenses,
    #             "remaining_budget": remaining_budget,
    #             "Comments": self.event_payload.get('Comments'),
    #             "updated_date" : updated_date              
    #         }
 
    #     print("data",data)
    #     #self.vault.save('TWO', data)
    #     self.vault.update('BUDGET', vault_filter, data, False)   
        result.putAll(self.event_payload)
        print("result", result)

        return result


def execute(self: HandlerExecutionContext) -> Map:
    print(f'==> [CustomPythonEventHandler]: {self}')
    result = CustomPythonEventHandler(self).handle()
    return result