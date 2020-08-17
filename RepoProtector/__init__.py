import base64
import logging
import os
import requests
import hmac
import hashlib
import jwt
import json
from datetime import datetime, timedelta, timezone

import azure.keyvault.secrets as azsecrets
import azure.keyvault.keys as azkeys
from azure.keyvault.keys.crypto import CryptographyClient
import azure.identity as azid
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    if not "webhook_secret" in os.environ:
        return func.HttpResponse("Function secret not configured!", status_code=500)
    else:
        secret = os.environ['webhook_secret'].encode()

    if not "X-Hub-Signature" in req.headers:
        return func.HttpResponse("No signature included.", status_code=400)
    else:
        hmac_gen = hmac.new(secret, req.get_body(), hashlib.sha1)
        digest = "sha1=" + hmac_gen.hexdigest()
        
        if not hmac.compare_digest(digest, req.headers['X-Hub-Signature']):
            func.HttpResponse("Bad signature.", status_code=400)

        req_body = req.get_json()
        #X-GitHub-Event: repository
        if req.headers['X-GitHub-Event'] == 'ping':
            zen = req_body['zen']
            logging.info(f"ping request: {zen}")
            return func.HttpResponse(zen)

        elif req.headers['X-GitHub-Event'] == 'repository':
            action = req_body['action']
            priv = bool(req_body['repository']['private'])
            #repo_name = req_body['repository']['name']
            repo_url = req_body['repository']['url']
            branch_protection_url = req_body['repository']['branches_url'].replace('{/branch}', '/master') + '/protection'
            issues_url = req_body['repository']['issues_url'].replace('{/number}', '')
            
            if action == 'created':
                t = get_github_auth_token()

                headers = {
                    "Authorization": "token " + t,
                    "Accept": "application/vnd.github.machine-man-preview+json",
                }

                # make repo public so we can protect it
                if priv:
                    r = requests.patch(repo_url, data=json.dumps({"private": False}), headers=headers)
                    logging.debug(r.json())

                protection_headers = {
                    "Authorization": "token " + t,
                    "Accept": "application/vnd.github.luke-cage-preview+json"
                }

                # protect branch
                r = requests.put(branch_protection_url, data=get_protection_payload(), headers=protection_headers)
                logging.debug(r.json())

                r = requests.post(issues_url, data=get_issue_payload(), headers=headers)
                logging.debug(r.json())

                return func.HttpResponse("Success.")
            else:
                return func.HttpResponse("Success.")

    return func.HttpResponse("Success!", status_code=200)

def get_github_auth_token():
    credential = azid.DefaultAzureCredential()

    header = {
        'Alg': 'RS256',
        'Kid': 'https://kv-ghapitest.vault.azure.net/keys/repoprotector/fa27e49e8ef74a54863c5497a6016a47',
        'Typ': 'JWT',
    }

    message = {
        'iss': os.environ['github_appID'],
        'iat': int(datetime.now(timezone.utc).timestamp()),
        'exp': int((datetime.now(timezone.utc) + timedelta(minutes=1)).timestamp()),
    }

    payload = base64.urlsafe_b64encode(json.dumps(header).encode()).decode() + "." + base64.urlsafe_b64encode(json.dumps(message).encode()).decode()
    digest = hashlib.sha256(payload.encode()).digest()

    cryptoClient = CryptographyClient('https://kv-ghapitest.vault.azure.net/keys/repoprotector/fa27e49e8ef74a54863c5497a6016a47', credential)
    result = cryptoClient.sign(azkeys.crypto.SignatureAlgorithm.rs256, digest)
    kv_jws = (base64.urlsafe_b64encode(json.dumps(header).encode()).decode() + "." + base64.urlsafe_b64encode(json.dumps(message).encode()).decode() + '.' + base64.urlsafe_b64encode(result.signature.decode('utf-8', 'ignore').encode()).decode())
    kv_jws.replace('==', '')

    client = azsecrets.SecretClient(vault_url=os.environ['key_vault_uri'], credential=credential)
    key = client.get_secret(os.environ['key_name'])

    message = {
        'iss': os.environ['github_appID'],
        'iat': (datetime.now(timezone.utc)),
        'exp': (datetime.now(timezone.utc) + timedelta(minutes=1)),
    }
    compact_jws = jwt.encode(message, key.value.replace("\\n", "\n").encode(), algorithm='RS256')

    headers = {
        "Authorization": "Bearer " + kv_jws.replace('==', ''),
        "Accept": "application/vnd.github.machine-man-preview+json",
    }

    r = requests.get('https://api.github.com/integration/installations', headers=headers)

    logging.debug(r.json())

    access_token_url = r.json()[0]['access_tokens_url']

    r = requests.post(access_token_url, headers=headers)

    logging.debug(r.json())

    return r.json()['token']

def get_protection_payload():
    return json.dumps({
        "required_status_checks": None,
        "restrictions": None,
        "enforce_admins": True,
        "required_pull_request_reviews": {
            "dismissal_restrictions": {},
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": True,
            "required_approving_review_count": 2
        }
    })

def get_issue_payload():
    return json.dumps({
        "title": "Repository protected!",
        "body": "2 pull request reviewers required (other than the owner)."
    })
