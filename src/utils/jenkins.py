import requests
from .common import add_to_logs

class JenkinsJobAnalyzer():

    
    def __init__(self, server_url: str, username=None, token=None, ssl_verification=True):
        """
        Verifies if a Jenkins server is running and accessible.

        Args:
            server_url (str): The base URL of the Jenkins server (e.g., "http://localhost:8080").
            username (str, optional): Jenkins username if authentication is required. Defaults to None.
            token (str, optional): Jenkins password or API token if authentication is required. Defaults to None.
            ssl_verification( str, bool, optional ): SSL cert path or set it to true of false for ssl verification
        """

        self.server_url = server_url.rstrip("/")
        self.username = username
        self.token = token
        self.api_suffix = "/api/json"
        self.auth = None
        self.ssl_verification = ssl_verification if ssl_verification else False
        self.jobs_details = {}
        self.job_list = []

        if username and token:
            self.auth = (username, token)

    def validate_jenkins_server(self):

        """
        Validate the given Jenkins Server URL is valid and the tool can access the Jenkins server API's
        """

        try:
            data = requests.get(
                self.server_url + self.api_suffix,
                auth = self.auth,
                verify=self.ssl_verification
            )
            add_to_logs(f"Connection to Jenkins Server {self.server_url} done.")
            return data.json()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Failed to connect with {self.server_url} you can try to access the jenkins from the host try `curl f{self.server_url + self.api_suffix}` and you will see some json.")

    def get_jobs_from_folder(self, folder_url):

        """
        This function's purpose is to recursively traverse Jenkins folders to find jobs within them.
        """

        data = requests.get(
            folder_url,
            auth = self.auth,
            verify=self.ssl_verification
        ).json().get("jobs")
        for x in data:
            if "WorkflowJob" in x.get("_class") or "FreeStyleProject" in x.get("_class"):
                self.job_list.append(x.get("url"))
                add_to_logs(f"Fetched job {x.get("url")}")
            if "Folder" in x.get("_class"):
                self.get_jobs_from_folder( x.get("url").rstrip("/") + self.api_suffix )

    def fetch_jobs(self):
        
        """
        Get Data from Jenkins Home Page
        Calls another method `self.validate_jenkins_server()`, which presumably makes an API call to the main Jenkins URL (e.g., `http://jenkins_url:8080/api/json`).
        """

        home_page_data = self.validate_jenkins_server().get("jobs")

        for x in home_page_data:
            if "WorkflowJob" in x.get("_class") or "FreeStyleProject" in x.get("_class"):
                self.job_list.append(x.get("url"))
                add_to_logs(f"Fetched job {x.get("url")}")
            if "Folder" in x.get("_class"):
                self.get_jobs_from_folder( x.get("url").rstrip("/") + self.api_suffix )

    def get_jobs_detail(self):

        """
            This method will fetch job details and create a dict out of it with all the info.
        """

        self.fetch_jobs()
        self.jobs_details["total_number_of_jobs"] = len(self.job_list)
        for x in self.job_list:
            last_build_data = {}
            data = requests.get(
                x.rstrip("/") + self.api_suffix,
                auth = self.auth,
                verify=self.ssl_verification
            ).json()
            if x.get("lastStableBuild"):
                last_build_data = requests.get(
                    x.get("lastStableBuild").get("url"),
                    auth = self.auth,
                    verify=self.ssl_verification
                ).json()

            self.jobs_details[x.get("displayName")] = { 
                "buildable": x.get("buildable"),
                "fullDisplayName": x.get("fullDisplayName"),
                "score": x.get("healthReport")[0].get("score") if x.get("healthReport") else None,
                "fullDisplayName": x.get("fullDisplayName"),
            }

    def prepare_dict_data(self):
        pass

    def prepare_html_report(self):
        pass

    def prepare_dashboard_report(self):
        pass

