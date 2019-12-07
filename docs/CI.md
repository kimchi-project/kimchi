# How to setup Kimchi CI

Due to nested virtualization requirements, most of CI tools does not offer the minimum requirement to test kimchi. To solve this, we have an integration with [Google Cloud](https://cloud.google.com/), which create an instance and trigger the tests. 

# Create a service account in GCP

To run the tests, its necessary to create a service account with the following iam roles:

* `roles/iam.serviceAccountUser`
* `roles/compute.admin`

Here is a script to help
```
# create account
$ gcloud iam service-accounts create [SA-NAME] \
    --description "[SA-DESCRIPTION]" \
    --display-name "[SA-DISPLAY-NAME]"

# create the key to be store as a secret
$ gcloud iam service-accounts keys create ~/key.json \
  --iam-account [SA-NAME]@[PROJECT-ID].iam.gserviceaccount.com

# add iam roles
$ gcloud projects add-iam-policy-binding [PROJECT-ID] --member=serviceAccount:[SA-EMAIL] --role=roles/iam.serviceAccountUser

$ gcloud projects add-iam-policy-binding [PROJECT-ID] --member=serviceAccount:[SA-EMAIL] --role=roles/compute.admin   
```

# Setting up secrets

The code for the CI is already at our repo, you just need to set some Github Actions Secrets, the procedure is described here: https://help.github.com/en/actions/automating-your-workflow-with-github-actions/creating-and-using-encrypted-secrets#creating-encrypted-secrets

1) Create a secret named `GCP_PROJECT` with the project ID
2) Create a secret named `GCP_SA_EMAIL` with the service account email
3) Create a secret named `GCP_SA_KEY` with the service account json with base64: `cat my-key.json | base64`

# Testing the CI
Create a PR to see if the PR works