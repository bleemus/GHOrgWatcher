# GHOrgWatcher

An API that enables a GitHub App (via webhook) to watch for creation of repositories in an GitHub Organization.  The API also will protect the master branch of that repository, and pose an issue in the repository that it has been protected.

# Installation

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
1. Create Azure Key Vault
    1. Navigate to https://portal.azure.com
    1. Select *Create a Resource* in the upper left of the first page
    1. Search for *key vault*
    1. Click *Create*
    1. Choose the *Resource Group* that was previously utilized to deploy the function above
    1. Enter a *Key vault name* (e.g. kv-githubdemo)

        **Note:** All key vaults must be uniquely named, if taken, a different name must be chosen.
    1. Choose *Review + create*
1. Import key from GitHub
    1. Choose the Key vault created above, or search for it at the top of the portal
    1. Select *Keys*
    1. Select *Generate/import*
    1. Use the following options:
        1. *Options -> Import*
        1. Use the *File Upload* options to choose the .pem file created above.
        1. Enter a Name for the key (e.g. *githubdemokey*)
        1. Select *Create*
    1. Make note of the following values for application settings below:
        1. Azure Key Value DNS Name (key_vault_uri): `https://kv-githubdemo.valut.azure.net/`
        1. Key name (key_name): `githubdemokey`
        1. Current version of key (key_version): `fa27e49e8ef74a5412345677a6016a47`

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
* Values from the created Azure Key Vault above:
    * key_vault_uri
    * key_name
    * key_version
* The GitHub App ID from the installed App will be placed in the following setting (available under Organization > Installed GitHub Apps > Configure > App Settings):
    * github_appID
* Finally, the webhook secret in the GitHub app will be stored in this setting:
    * webhook_secret

For this to run successfully locally, place all of these settings in the *local.settings.json* file in the local copy of the Azure function on the development machine.

Example *local.settings.json*:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_CLIENT_ID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "AZURE_CLIENT_SECRET": "generates_client_secret",
    "AZURE_TENANT_ID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "key_vault_uri": "https://kv-githubdemo.vault.azure.net/",
    "key_name": "repoprotector",
    "key_version": "fa27e49e8ef74a5412345677a6016a47",
    "github_appID": 12345,
    "webhook_secret": "___SECRET_WEBHOOK_VALUE___"
  }
}
```

# Using the App

Once the application is fully configured, it will trigger upon creation of a repository in the organization.  This repository must be seeded with a master branch.

Upon creation, the GitHub App will fire the webhook to connect to the Azure Function App to validate the request, and then utilize the identity of the GitHub app to do the following steps:
1. Make the repository public, if created as a private repository.  This is to enable branch protection policies, only available for free with public repositories.
1. Set the number of approvers necessary for a pull request to the master branch to 2.
1. Creates an issue in the repository that the bot has configured that branch.
