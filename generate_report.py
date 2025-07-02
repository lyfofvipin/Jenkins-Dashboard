from src.utils.jenkins import JenkinsJobAnalyzer
import os

if os.environ.get("JENKINS_SERVER_URL"):
    server_url = os.environ.get("JENKINS_SERVER_URL")
elif os.environ.get("JENKINS_HOME"):
    server_url = os.environ.get("JENKINS_HOME")
else:
    server_url = "http://localhost:8080"

if os.environ.get("USERNAME") and os.environ.get("TOKEN"):
    username = os.environ.get("USERNAME")
    token = os.environ.get("TOKEN")
else:
    username = None
    token = None

if os.environ.get("SSL_VERIFICATION"):
    ssl_verification = os.environ.get("SSL_VERIFICATION")
else:
    ssl_verification = False

server_url = "https://jenkins-csb-rhcertqe-master.dno.corp.redhat.com"
abcd = JenkinsJobAnalyzer(server_url=server_url, ssl_verification=ssl_verification, username=username, token=token)
abcd.prepare_dict_data()
abcd.prepare_description_report()
abcd.prepare_html_report()
