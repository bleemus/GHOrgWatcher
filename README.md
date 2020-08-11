# GHOrgWatcher

An API that enables a GitHub App (via webhook) to watch for creation of repositories in an GitHub Organization.  The API also will protect the master branch of that repository, and pose an issue in the repository that it has been protected.

# Installation

## API

This API is programmed in Python and is built for deployment to an Azure Function.

The main setup for the Azure Function is available [on Microsoft Docs](https://docs.microsoft.com/en-us/azure/azure-functions/functions-create-first-function-vs-code?pivots=programming-language-python) for setup in Visual Studio Code.

Once the above steps are followed, clone this repository and deploy to the newly created app using the instructions from the previous documentation.

To obtain the URL for the deployed service, navigate to the function and select **Get Function Url**

### App Configuration 

This application requires the following app settings to exist and be properly configured.  See [Microsoft Docs](https://docs.microsoft.com/en-us/azure/azure-functions/functions-how-to-use-azure-function-app-settings#settings) on how to set these key/value pairs

* Documentation on creating an Azure Key Vault and setting up the service principal is available on [Microsoft Docs](https://docs.microsoft.com/en-us/azure/key-vault/secrets/quick-create-python#create-a-resource-group-and-key-vault).  The clientId, clientSecret, and tenantId will be required in the following settings:
    * AZURE_CLIENT_ID
    * AZURE_CLIENT_SECRET
    * AZURE_TENANT_ID
* The key vault URL will go in the following setting:
    * key_vault_uri
* The name of the secret that will hold the private key information from the GitHub App will be placed in the following setting:
    * key_name
* The GitHub App ID from the installed App will be placed in the following setting (available under Organization > Installed GitHub Apps > Configure > App Settings):
    * github_appID
* Finally, the webhook secret in the GitHub app will be stored in this setting:
    * webhook_secret

## GitHub App

This API is meant to be deployed as a webhook endpoint to a GitHub app.

1. [Create a GitHub organization](https://docs.github.com/en/github/setting-up-and-managing-organizations-and-teams/creating-a-new-organization-from-scratch)
1. Select **Settings** for the new Organization
1. Select **GitHub Apps** under *Developer settings*
1. Select **New GitHub App**
1. Name the App
1. Under *Webhook*
    1. Verify the **Active** flag is checked
    1. Paste in the Function URL from API step above
1. Enable the following permissions:
    1. *Administration*: Read & Write
    1. *Contents*: Read & Write
    1. *Issues*: Read & Write
    1. *Metadata*: Read-only
1. Under *Subscribe to events*:
    1. Check *Repository*
1. Select **Save Changes**

Once the application is installed, a private key must be generated and added to the Azure Key Vault:

1. Organization > Installed GitHub Apps > Configure > App Settings
1. At the bottom of this screen, select **Generate a private key**
    1. A save dialog will spawn, save off the .pem file locally.
1. Copy the text from the .pem file
1. Open the secret made in the Azure Key Vault steps above
1. Select **New Version**
1. Place the private key value text into the **Value** input box and click **Create**

# Using the App

Once the application is fully configured, it will trigger upon creation of a repository in the organization.  This repository must be seeded with a master branch.

Upon creation, the GitHub App will fire the webhook to connect to the Azure Function App to validate the request, and then utilize the identity of the GitHub app to do the following steps:
1. Make the repository public, if created as a private repository.  This is to enable branch protection policies, only available for free with public repositories.
1. Set the number of approvers necessary for a pull request to the master branch to 2.
1. Creates an issue in the repository that the bot has configured that branch.
