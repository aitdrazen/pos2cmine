<!--
Peter.Kutschera@ait.ac.at
2019-08-28
-->

# DRIVER+ PoS to CMINE Exporter

Author: Peter Kutschera, Peter.Kutschera@ait.ac.at

The exporter is a python script that copies solutions from PoS to CMINE.

The steps caried out are:
1. Login in CMINE
2. Get own CMINE user id.  
  This id will "own" the exported solutions from PoS and MUST NOT be used for something else!
3. Get the actual name of the TRL field from CMINE  
  This name is different on each production / sandbox instance
4. Get list of solutions already available in CMINE owned by this user id
5. For all solutions in PoS that are allowed to share with CMINE:
  * if already in CMINE: Compare timestamps to decide if update is needed
  * Create or update solution in CMINE if needed
6. For all solutions in CMINE owned by user id:
  * delete soution in CMINE if no longer in the list of solutions from PoS

__Login in PoS__: There is no need to login into PoS. If this changes the exporter need to be updated depending of login mechanism used.

## Mapping

The problem is that there are a lot of field in CMINE that are not available from PoS (in the moment).

| CMINE | PoS | Comment |
|-------|-----|---------|
| high_level_pitch | title | |
| product | summary | "Blank" if not available |
| company_name | provider | "DRIVER+" if not available |
| company_website | base_url + group_uri | Link to solution PoS |
| user_id |  | the id of the user with the same email as the admin doing the import |
| business_stage | "unknown" | A mandatory field in CMINE; should be innovation_stage but content does not match list of allowed values in CMINE |
| locations | "Giefinggasse 4, Vienna, AT" | This field is not updated by the exporter |
| cover_picture | base_url + illustration_uri | |
| logo | "https://s3-eu-west-1.amazonaws.com/kit-eu-preprod/assets/networks/550/picture/-original.jpg?1567692929"| |
| video_html | (video_url) | not available in the moment as ignored by CMINE |
| _2e743dbd_Technology_Readiness_Level__TRL_ | trl |  E.g.   "TRL 9 - Actual system proven in operational environment" |

The CMINE name of TLR is different on sandbox and production system so the name is guessed from the available CMINE customizable attributes.

## Setup

1. Install an actual python 3 version.
  The exporter might run using python2 also but this is not tested!

  See  https://www.python.org/ for installation instructions if needed.
  The following assumes python3 is your default python version.
  Else commands needs to be changed to use python 3.
2. Install required modules either globaly (`pip install requests python-dotenv iso8601 python-dateutil`)
  or locally, e.g. using pipenv.
  ```shell-dump
  cd directory_with_pos2cmine.py
  pip install pipenv
  pipenv --three install requests python-dotenv iso8601 python-dateutil
  ```
3. running automatically every week

  * First create a file `.env` in the directory also containing `pos2cmine.py`
    with the following content (Replace with the correct usernane,...)
    as described below in "Run the Exporter"
	```
    #  DRIVER+ PoS
    pos_url = https://pos.driver-project.eu
    #  CMINE productiv
    cmine_url = https://www.cmine.eu
	cmine_email = someone@some.domain
	cmine_password = ****
	cmine_owner = cmine-helpdesk@projectdriver.eu
	cmine_client_id = ************************************************************
	cmine_client_secret = ************************************************************
	```

  * Add this to yout crontab (With correct paths!)
    This will run the syncronisation every monday 5 minutes past 9 am.
	```
	9 5 * * mon (cd /home/peter/_work/DRIVERplus/pos2cmine; flock -xn ./pos2cmine.lock /home/peter/.local/bin/pipenv run ./pos2cmine.py) > ./pos2cmine.log 2>&1
	```
  



## Run the Exporter

```shell-dump
pipenv run ./pos2cmine.py -h
```

There are a lot of parameters required. They can also provided as enviroment variables or as `.env` file. The content would something like this:
```env
#  DRIVER+ PoS developement system
pos_url = https://pos.driver-project.eu
# CMINE Sandbox
cmine_url = https://www.cmine.eu
# email, password: an administrator to login und use CMINE REST
cmine_email = admistrator_email_address
cmine_password = administrator_password
# owner: User owning the PoS solutions. And ONLY then, other solutions owned bys owner will be deleted.
cmine_owner = cmine-helpdesk@projectdriver.eu
cmine_client_id = UID from  https://www.cmine.eu/backoffice/networks/436/external_integrations
cmine_client_secret = Secret from  https://www.cmine.eu/backoffice/networks/436/external_integrations
```


<!--

## Relevant Documentation and Links

### PoS

Denis has implemented a simple REST GET export function for the trials and solutions. Some examples:
*	https://pos-dev.driver-project.eu/group_export?_format=json&type=solution&search=crowd returns the solutions with “crowd” in name or description
*	https://pos-dev.driver-project.eu/group_export?_format=json&type=solution&offset=10returns next 10 solutions in a pager
*	https://pos-dev.driver-project.eu/group_export?_format=json&type=solution&changed=-2%20months returns the solutions with descriptions changed in the last 2 months.
*	https://pos-dev.driver-project.eu/group_export?_format=json&type=solutio... returns the german translations of the solutions.
UPDATE: same functions are available on pos too.



PoS https://pos.driver-project.eu

PoS developement https://pos-dev.driver-project.eu

### CMINE

REST Api Docu at https://hivebrite.com/documentation/api/admin#ventures

CMINE api https://www.cmine.eu/api
CMINE Sandbox API https://cmine-sandbox.preprod.hivebrite.com/api

CMINE https://www.cmine.eu/
CMINE API https://arttic-driver.hivebrite.com/api


JSON-Files with swagger-descriptions of the API:  
```
Case PRODUCTION
1/ to access the authentication documentation :
https://arttic-driver.hivebrite.com/api/oauth/swagger_doc.json
2/ to access the whole API documentation :
https://arttic-driver.hivebrite.com/api/swagger_doc.json

Case PREPROD
1/ to access the authentication documentation :
https://cmine-sandbox.preprod.hivebrite.com/api/oauth/swagger_doc.json
2/ to access the whole API documentation :
https://cmine-sandbox.preprod.hivebrite.com/api/swagger_doc.json
```

To get the oauth token:
```
POST /oauth/token
with params
- grant_type: password
- scope: admin
- admin_email: EMAIL_OF_THE_ADMINISTRATOR_THAT_WILL_BE_LOGGED_IN
- password: PASSWORD_OF_THE_ADMINISTRATOR_THAT_WILL_BE_LOGGED_IN
- client_id: UID for the API Access
- client_secret: Secret of the API Access
```

You'll get an access token upon success.

Use this token inside a `Authorization: Bearer _the_access_token` header.

-->
