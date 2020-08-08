import logging
import os
import hmac
import hashlib
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.  Released wtih GitHub Actions! :)')

    if not "signature" in os.environ:
        return func.HttpResponse("Function secret not configured!", status_code=500)
    else:
        secret = os.environ['signature'].encode()

    if not "X-Hub-Signature" in req.headers:
        return func.HttpResponse("No signature included.", status_code=400)
    else:
        hmac_gen = hmac.new(secret, req.get_body(), hashlib.sha1)
        digest = "sha1=" + hmac_gen.hexdigest()
        
        if not hmac.compare_digest(digest, req.headers['X-Hub-Signature']):
            func.HttpResponse("Bad signature.", status_code=400)

        req_body = req.get_json()
        
        if req_body.get('action') == 'created':
            logging.info('Repository created...')
            return func.HttpResponse("Success.")

        elif req_body.get('zen') is not None:
            zen = req_body['zen']
            logging.info(f"ping request: {zen}")
            return func.HttpResponse(zen)

