# vim:set et ts=4 sw=4:

import json
import logging

import requests

# logging
logger = logging.getLogger('grouper')
logger.setLevel(logging.DEBUG)

base_uri = 'https://calgroups.berkeley.edu/gws/servicesRest/json/v2_2_100'

def auth(user, password):
    return requests.auth.HTTPBasicAuth(user, password)

def create_stem(auth, stem, name):
    '''Create a new grouper stem.'''
    # https://github.com/Internet2/grouper/blob/master/grouper-ws/grouper-ws/doc/samples/stemSave/WsSampleStemSaveRestLite_json.txt
    logger.info('creating {}'.format(stem))
    data = {
        "WsRestStemSaveLiteRequest": {
            "description":name,
            "displayExtension":name,
            "stemName":stem
        }
    }
    r = requests.post(f'{base_uri}/stems/{stem}',
        data=json.dumps(data), auth=auth, headers={'Content-type':'text/x-json'}
    )
    out = r.json()
    if 'WsRestResultProblem' in out:
        msg = out['WsRestResultProblem']['resultMetadata']['resultMessage']
        raise Exception(msg)
    if 'WsStemSaveLiteResult' in out:
        code = out['WsStemSaveLiteResult']['resultMetadata']['resultCode']
        if code not in ['SUCCESS_INSERTED', 'SUCCESS_NO_CHANGES_NEEDED']:
            msg = out['WsStemSaveLiteResult']['resultMetadata']['resultMessage']
            raise Exception(f'{code}: {msg}')
    return out

def create_group(auth, group, name):
    '''Create a new grouper group.'''
    # https://github.com/Internet2/grouper/blob/master/grouper-ws/grouper-ws/doc/samples/groupSave/WsSampleGroupSaveRestLite_json.txt
    logger.info('creating {}'.format(group))
    data = {
        "WsRestGroupSaveLiteRequest": {
            "description":name,
            "displayExtension":name,
            "groupName":group
        }
    }
    r = requests.post(f'{base_uri}/groups/{group}',
        data=json.dumps(data), auth=auth, headers={'Content-type':'text/x-json'}
    )
    out = r.json()
    if 'WsRestResultProblem' in out:
        msg = out['WsRestResultProblem']['resultMetadata']['resultMessage']
        meta = out['WsRestResultProblem']['resultMetadata']
        print(f'Error creating group: {group} {data}')
        raise Exception(meta)
    if 'WsGroupSaveLiteResult' in out:
        code = out['WsGroupSaveLiteResult']['resultMetadata']['resultCode']
        if code not in ['SUCCESS_INSERTED', 'SUCCESS_NO_CHANGES_NEEDED']:
            msg = out['WsGroupSaveLiteResult']['resultMetadata']['resultMessage']
            print(f'Error creating group: {group} {data}')
            raise Exception(f'{code}: {msg}')
    return out

def replace_users(auth, group, users):
    '''Replace the members of the grouper group {group} with {users}.'''
    logger.info('transferring to {}'.format(group))
    # https://github.com/Internet2/grouper/blob/master/grouper-ws/grouper-ws/doc/samples/addMember/WsSampleAddMemberRest_json.txt
    data = {
        "WsRestAddMemberRequest": {
            "replaceAllExisting":"T",
            "subjectLookups":[]
        }
    }
    for user in users:
        data['WsRestAddMemberRequest']['subjectLookups'].append(
            {"subjectId":user}
        )
    r = requests.put(f'{base_uri}/groups/{group}/members',
        data=json.dumps(data), auth=auth, headers={'Content-type':'text/x-json'}
    )
    out = r.json()
    if 'WsRestResultProblem' in out:
        msg = out['WsRestResultProblem']['resultMetadata']['resultMessage']
        meta = out['WsRestResultProblem']['resultMetadata']
        raise Exception(meta)
