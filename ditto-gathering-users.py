import requests, json
import csv

from decimal import Decimal
from web3 import Web3   
from time import sleep, time
from eth_utils import address
from datetime import datetime
import time
import math

HTTP_PROVIDER_URL = "https://bsc-dataseed.binance.org/"
STAKING_CONTRACT = "0x27Da7Bc5CcB7c31baaeEA8a04CC8Bf0085017208"
with open('src/abis/DittoStaking.json') as f:
  STAKING_CONTRACT_ABI = json.load(f)

w3 = Web3(Web3.HTTPProvider(HTTP_PROVIDER_URL))
staking_contract = w3.eth.contract(STAKING_CONTRACT, abi=STAKING_CONTRACT_ABI)

TOTAL_REWARDS = 250 * 1e18

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
userStakingShareSeconds = {}
now = time.time()

print("Collecting user totals...")

# Get totalStakingShareSeconds
for staker in address_obj:
  staking_address = address.to_checksum_address(staker["reference"]["address"])

  if staking_address in userStakingShareSeconds:
    continue  # Skip duplicates
  
  (stakingShares, stakingShareSeconds, lastAccountingTimestamp) = staking_contract.functions.userTotals(staking_address).call()

  stakingShareSeconds = stakingShareSeconds + (now - lastAccountingTimestamp) * stakingShares

  userStakingShareSeconds[staking_address] = stakingShareSeconds
  totalStakingShareSeconds = stakingShareSeconds + totalStakingShareSeconds

print("= totalStakingShareSeconds:{}\n= Number of users: {}\n".format(totalStakingShareSeconds, len(userStakingShareSeconds)))

# Generate Ditto Claim list and Balance 
with open('ditto_list_claim.csv', 'w', encoding='utf8') as file:
  writer = csv.writer(file)
  writer.writerow = [("address", "amount")]

  for address,stakingShareSeconds in userStakingShareSeconds.items():

    if (stakingShareSeconds > 0):
      claim_amount = math.floor(TOTAL_REWARDS * stakingShareSeconds / totalStakingShareSeconds)

      amount_fmt = "%d" % claim_amount

      print("{},{}".format(address,amount_fmt))
      writer.writerows = (address, amount_fmt)
