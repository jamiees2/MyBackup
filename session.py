import os
import requests
session = requests.session()
session.auth = (os.environ["MYSCHOOL_USER"], os.environ["MYSCHOOL_PASS"])
