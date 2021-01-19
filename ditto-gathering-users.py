import requests, json
import csv

from decimal import Decimal
from web3 import Web3   
from time import sleep, time
from eth_utils import address
from datetime import datetime

HTTP_PROVIDER_URL = "https://bsc-dataseed.binance.org/"
STAKING_CONTRACT = "0x27Da7Bc5CcB7c31baaeEA8a04CC8Bf0085017208"
with open('src/abis/DittoStaking.json') as f:
  STAKING_CONTRACT_ABI = json.load(f)

w3 = Web3(Web3.HTTPProvider(HTTP_PROVIDER_URL))
staking_contract = w3.eth.contract(STAKING_CONTRACT, abi=STAKING_CONTRACT_ABI)

def run_query(query):  # A simple function to use requests.post to make the API call.
    request = requests.post('https://graphql.bitquery.io/',
                            json={'query': query})
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception('Query failed and return code is {}.      {}'.format(request.status_code,
                        query))



# The GraphQL Ditto Staking
query = """
query {
    ethereum(network: bsc) {
      arguments(smartContractAddress: 
        {is: "0x27Da7Bc5CcB7c31baaeEA8a04CC8Bf0085017208"},
        smartContractEvent: {is: "Staked"}, 
        options: {desc: "block.height", limit: 2000}) {
        block {
          height
        }
        reference {
          address
        }
      }
    }
  }
"""

result = run_query(query) 
address_obj = result["data"]["ethereum"]["arguments"]
totalStakingShareSeconds = 0

# Get totalStakingShareSeconds
for staker in address_obj:
  staking_address = address.to_checksum_address(staker["reference"]["address"])  
  userTotals = staking_contract.functions.userTotals(staking_address).call()
  if (userTotals[1] > 0):
    totalStakingShareSeconds = userTotals[1] + totalStakingShareSeconds

# print('Total Events Staking: {}'.format(len(address_obj)))
# print('Total Time Staking: {}'.format(datetime.datetime(totalStakingShareSeconds)))

# Generate Ditto Claim list and Balance 
with open('ditto_list_claim.csv', 'w', encoding='utf8') as file:
  writer = csv.writer(file)
  writer.writerow = [("address", "amount")]
  for staker_address in address_obj:
    staking_address = address.to_checksum_address(staker_address["reference"]["address"])  
    userTotals = staking_contract.functions.userTotals(staking_address).call()
    if (userTotals[1] > 0):
      claim_balance = userTotals[1]/totalStakingShareSeconds
      writer.writerows = (staking_address, claim_balance)