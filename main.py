import sys
import json
from algosdk.v2client import *
from algosdk import account
from algosdk.future import transaction
from configparser import ConfigParser
parser = ConfigParser()

parser.read('config.cfg')

def network_client():
    try:
        algod_address = parser.get('ALGOD_test_params', 'algod_address')
        algod_token = parser.get('ALGOD_test_params', 'algod_token')
        headers = {
        "X-API-Key": algod_token,
        }
        algod_client = algod.AlgodClient(algod_token, algod_address, headers)
        return algod_client
    except Exception as e:
        raise Exception(e)

def wait_for_confirmation(client, txid):
    """
    Utility function to wait until the transaction is
    confirmed before proceeding.
    """
    last_round = client.status().get('last-round')
    txinfo = client.pending_transaction_info(txid)
    while not (txinfo.get('confirmed-round') and txinfo.get('confirmed-round') > 0):
        last_round += 1
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(txid)
    # print("Transaction {} confirmed in round {}.".format(txid, txinfo.get('confirmed-round')))
    return txinfo

# Creating Algorand Standard Asset
def Create_ASA_TXN(total,assetname,unitname,decimals,url,freezeState):
    try:
        algod_client = network_client()
        private_key = parser.get('ALGOD_test_params', 'private_key')
        address = account.address_from_private_key(private_key)
        params = algod_client.suggested_params()
        gh, first_valid_round, last_valid_round = params.gh, params.first, params.last
        fee = 1000
        sp = transaction.SuggestedParams(fee, first_valid_round,last_valid_round,gh)
        # get last block info
        block_info = algod_client.block_info(sp.first)
        # print("Block", sp.first, "info:", json.dumps(block_info, indent=2), "\n")    
        txn,err = transaction.AssetConfigTxn(address, sp, total=total, manager=address,
                    reserve=address, freeze=address, clawback=address,
                    unit_name=unitname, asset_name=assetname, url=url,decimals=decimals,
                    default_frozen=freezeState),None
        signed = txn.sign(private_key)
        txid = algod_client.send_transaction(signed)
        wait_for_confirmation(algod_client,txid)
        ptx = algod_client.pending_transaction_info(txid)
        assetid = ptx["asset-index"]
        return txid, err, assetid
    except Exception as e:
        txid, err = e, e
        assetid = None
        return txid, err, assetid

def main():
    try:
        assetname = parser.get("XET_params","assetName")
        unitname = parser.get("XET_params","unitName")
        total = parser.get("XET_params","total_supply")
        fractions = parser.get("XET_params","decimals")
        url = parser.get("XET_params","url")
        freezestate = parser.get("XET_params","freezeState")
        total,fractions = int(total), int(fractions)
        txid,err,assetid = Create_ASA_TXN(total=total, assetname=assetname, unitname=unitname, decimals=fractions, url=url, freezeState=freezestate)
        data = {}
        data["txid"],data["asset_id"] = txid,assetid

        # Writing Values into the persistent file
        data = json.dumps(data,indent=4)
        with open("asset_details.json", "w") as outfile:
            outfile.write(data)

        if err :
            content = {"Message":str(err)}
            print(content)
        print("Transaction ID: " + str(txid) + "\n")
        print("Asset Id: "+ str(assetid) + "\n")

    except Exception as e:
        print(e)

# Main Function 
main()