# install OS requirements 
1. make sure you are using python version 3.10
2. if you are on windows or mac make sure to install PostgreSQL
3. if you are on ubuntu make sure to install the below packages (required for psycopg2 package)
```
sudo apt-get update 
sudo apt-get install libpq-dev 
sudo apt-get install python3-dev
sudo apt-get install gcc 
```

# setup

```
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

# env file

1. create a .env file under the root directory of the project 
2. please check sample.env file to get an example file with all the neccesary env variables we have

# run

```
python manage.py runserver
```

# setting up stuff

1. go to http://127.0.0.1:8000/admin (user/pw admin/admin)
2. login as superuser
3. create a new user under the `AUTHENTICATION AND AUTHORIZATION` section.
4. create a `LiteratureReview`... which requires
   - a client
     - that requires an address
     - and a logo image
   - a device
     - that requires a manufacturer
   - and an intake
5. create a `NCBIDatabase` with this information

- name = `PubMed Central` (COPY THIS EXACTLY)
- entrez_enum = `pmc` (COPY THIS EXACTLY)
- url = https://www.ncbi.nlm.nih.gov/pmc/

6.  go to http://127.0.0.1:8000/literature_reviews/1 and log in as the user from (3) above

# doing the review

1.  go to "Search Terms" under the Protocol menu on the left hand side.
2.  Under Search Dash -- all search results files will be uploaded
3.  ed can do his work under "SEARCH RESULTS" from here on out
4.  under "CLINICAL LITERATURE APPRAISAL", an entry will appear for each Included article.

# How to deploy to heroku?

1.  Deploy master branch

- `git push heroku master`
  2- Deploy your own branch
- `git push heroku <branch-name>:master`

# How to run command inside heroku?

1.  Go inside heroku app

- `heroku run bash`

2.  Move to backend folder

- `cd backend`

3.  Run your command

- eg run migration command `python manage.py migrate`

   <!-- Run celery -->

celery -A backend worker -l INFO -P threads

# You are having an issue with loading css files? try the below solution
make sure DEBUG=True when you are developing locally (in development mode).

## ENV File Management - Heroku
Heroku stores and manages ENVs in their web interface. If you want to update an ENV, you need to:
1. login to Heroku
2. go to the right application 
3. go to settings -> Variables
4. Update the variables you'd like. 


## Ansible/Docker ENVs
When we are deploying via ansible-playbook (and thus building docker images/containers on our digital ocean server)
ENVs are set in an ansible-vault. This is just a way to encrypt the db files so we can share them on git.

When deploying with docker, docker looks for the .env file in the project root to use. 
This ENV file is built from our ansible-playbook process automatically. Here's how it works.
The ansible-playbook script looks at the 'vault' file, and pulls the values to create the .env file.
This happens everytie you run the deployment script. 

### Editing ENVs with the ansible vault
The vault is just an encrypted text file that ansible knows how to open. 
To edit a vault file, use the 'ansible-vault' command. 

```commandline
ansible-vault edit deployment-infra/[vault name.yml] 
```
- You will need a password to decrypt (Ethan maintains these on Notion)
- make sure you prefix any var name with 'vault_'  like vault_AWS_ACCESS_KEY_ID. this is important to the deployment process

### Adding a New ENV with the ansible vault
If you are ADDING an env, make sure that it's also referenced in the relevant playbook.

1. Open the vault and add in your variable. 

```commandline
ansible-vault ansible-vault edit deployment-infra/[the vault name.yml] 
```

2. make sure you prefix your variable with 'vault_'  like vault_AWS_KEY_ID

3. save the vault (like yo uwould with a vim text editor)

4. Find the create env step in the deploy script, and add your new ENV in line.
Note they have to be prefixed with vault_  for some reason (in the database too)

4.1 Open up the deployment script
```commandline
vim deployment-infra/deploy-staging.yml  ### for the staging env script
```

4.2 Navigate to the lines under vars->env_vars. it should look like this 
```commandline
    - name: Create .env file
      template:
        src: "env.j2"
        dest: "{{ project_deployed_path }}/.envtest"
        mode: '0600'
      vars:
        env_vars:
          ENV: "{{ vault_ENV }}"
          [yournew ENV]: ""{{ vault_[yournew_ENV] }}"" #### your line can go here
```
5. Save the deployment script file (deploy-staging.yml in this case), and you are good to run it! 


## Docker Stuff 
We are now deploying a few new things.
1. Both worker AND web processes are deployed via docker-compose.yml 
2. We are using ansible to manage deployment for each of the (soon to be created) remote servers.

You can run docker locally to make sure things are working very easily.
```commandline
docker compose up  ## from project root
```

### Viewing Logs from Docker
First find the container you want
```commandline
docker ps
```
Then you can tail the logs of it to debug
```
docker logs -f <container-id>
```

### SSH into docker container
```commandline
docker ps (to get teh container id you want) 
docker exec -it [container_id] /bin/bash
```


## Gooogle Chrome and ChromeDriver
The worker scripts use chrome to run headless scrapers. If deploying via ansible directly, you will need to have the 
compaptible chromedriver versions locally so they are copied over.
They are stored here: https://www.notion.so/citemedical/Deployment-CI-CD-Infrastructure-1230d4fa511c8081934de9dffe9a2458?pvs=4#15f0d4fa511c8016aa17f2ab3f7a963c 

Other versions links and compatibility can be found her:
*Chromedriver chrome compatibility*
https://googlechromelabs.github.io/chrome-for-testing/#stable

 



## Ansible Deployment

We are deploying the staging environment via ansible now.
The vault password file is for securely storing all of the envs 

### Managing ENVs with Ansible Vault
The ansible vault stores all of our encrypted environment variables -- we will create a vault for each environment
type,  demo, staging, production.

When the deployment script executes, it pulls the right values from the vault and creates a .env file (that the containers)
will use when they execute. 

```commandline
ansible-vault edit demo-vault.yml

```
The above command just edits the demo vault file that's encrypted.
It's just a basic ENV file, but encrypted so thats why you open it with ansible-vault edit  command to decrypt.


### Chrome and Chromedriver Requirments for Deployment
Moving off of heroku, we need to manage chrome installation ourselves. 
The build script epects these to be located under .chrome/ folder from root project directory.
get a copy from Ethan (also linked on Notion) to make sure the versions are compatible.

[Notion Link](https://www.notion.so/citemedical/Deployment-CI-CD-Infrastructure-1230d4fa511c8081934de9dffe9a2458?pvs=4#15f0d4fa511c8016aa17f2ab3f7a963c)

Need to upgrade chrome and find the right versions of chrome/chromium that are compatible?
[Go to this link](https://googlechromelabs.github.io/chrome-for-testing/#stable)


Unzip the .chrome directory in the same directory as manage.py (project root folder)

You <b>need<b> this to exist on your local environment for the deployment to work,
because our deployment script is copying your local files -> the remote server.

### ENV Vault Password File
You'll notice that some of the deployment commands have the flag
```commandline
--vault-password-file ~/.vault_pass.txt
```
This is just a plain text file stored on your local machine somewehre that contains the password for the vaults.
You do NOT need to use this (you could type it in each time if you wanted). 

### How to perform a full deploy with an ansible script
Run this from the project's root directory. Make sure you have your vault PW file locally as well.
```commandline

ansible-playbook  -i deployment-infra/inventory.yml deployment-infra/deploy-staging.yml --vault-password-file ~/.vault_pass.txt

```

### Quick  Deploy (push code only)
The main deployment scripts do a complete rebuild of the project. If you just want to update  some 
code quickly (that doesn't require new packages, ENVs etc.) then you can run the 'quick' version.
This will sync the files over, and run the migrations only (then restart web + celery services)

```commandline
ansible-playbook  -i deployment-infra/inventory.yml deployment-infra/quick-deploy-staging.yml --vault-password-file ~/.vault_pass.txt

```

### deployment scripts available:
- deploy-staging.yml | staging1.citemed.io
- quick-deploy-staging.yml | staging1.citemed.io
- 

### Automated Tests
To run all tests:
- `python manage.py test`

To run a specific test (all tests lives under lit_reviews/tests):
- `python manage.py test <app_name>.<test file name>` example: `python manage.py test lit_reviews.tests.test_scrapers`

### Add registered users to active campaing
run below command
`python manage.py add_registered_users_to_activecampaign`
