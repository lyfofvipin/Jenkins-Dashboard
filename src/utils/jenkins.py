import requests, os
from .common import add_to_logs
from datetime import datetime
from .data import abc

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
        self.job_list = []
        self.success_jobs = {}
        self.fail_jobs = {}
        self.unstable_jobs = {}
        self.aborted_jobs = {}
        self.disabled_jobs = {}
        self.unknown_jobs = {}
        self.jobs_details = {}
        self.total_number_of_jobs = 0

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
        add_to_logs(str(self.job_list))
        self.total_number_of_jobs = len(self.job_list)
        for x in self.job_list:
            add_to_logs(f"Collecting details of {x}.")
            data = requests.get(
                x.rstrip("/") + self.api_suffix,
                auth = self.auth,
                verify=self.ssl_verification
            ).json()

            if data.get("buildable"):
                if data.get("lastCompletedBuild"):
                    add_to_logs(f"Collecting last build details of {data.get("fullDisplayName")}.")
                    last_build_data = requests.get(
                        data.get("lastCompletedBuild").get("url").strip("/") + self.api_suffix,
                        auth = self.auth,
                        verify=self.ssl_verification
                    ).json()
                    match last_build_data.get("result"):

                        case "UNSTABLE":
                            self.unstable_jobs[data.get("displayName")] = { 
                            "fullDisplayName": data.get("fullDisplayName"),
                            "score": data.get("healthReport")[0].get("score") if data.get("healthReport") else None,
                            "last_build_status": last_build_data.get("result") if data.get("lastCompletedBuild") else None,
                            "last_build_url": last_build_data.get("url") if data.get("lastCompletedBuild") else None,
                            "timestamp": last_build_data.get("timestamp") if data.get("lastCompletedBuild") else None,
                            "duration": last_build_data.get("duration") // 1000 if data.get("lastCompletedBuild") else None,
                        }

                        case "FAILURE":
                            self.fail_jobs[data.get("displayName")] = { 
                            "fullDisplayName": data.get("fullDisplayName"),
                            "score": data.get("healthReport")[0].get("score") if data.get("healthReport") else None,
                            "last_build_status": last_build_data.get("result") if data.get("lastCompletedBuild") else None,
                            "last_build_url": last_build_data.get("url") if data.get("lastCompletedBuild") else None,
                            "duration": last_build_data.get("duration") // 1000 if data.get("lastCompletedBuild") else None,
                            "timestamp": last_build_data.get("timestamp") if data.get("lastCompletedBuild") else None,
                        }
 
                        case "SUCCESS":
                            self.success_jobs[data.get("displayName")] = { 
                            "fullDisplayName": data.get("fullDisplayName"),
                            "score": data.get("healthReport")[0].get("score") if data.get("healthReport") else None,
                            "last_build_status": last_build_data.get("result") if data.get("lastCompletedBuild") else None,
                            "last_build_url": last_build_data.get("url") if data.get("lastCompletedBuild") else None,
                            "duration": last_build_data.get("duration") // 1000 if data.get("lastCompletedBuild") else None,
                            "timestamp": last_build_data.get("timestamp") if data.get("lastCompletedBuild") else None,
                        }

                        case "ABORTED":
                            self.aborted_jobs[data.get("displayName")] = { 
                            "fullDisplayName": data.get("fullDisplayName"),
                            "score": data.get("healthReport")[0].get("score") if data.get("healthReport") else None,
                            "last_build_status": last_build_data.get("result") if data.get("lastCompletedBuild") else None,
                            "last_build_url": last_build_data.get("url") if data.get("lastCompletedBuild") else None,
                            "duration": last_build_data.get("duration") // 1000 if data.get("lastCompletedBuild") else None,
                            "timestamp": last_build_data.get("timestamp") if data.get("lastCompletedBuild") else None,
                        }
                else:
                    self.unknown_jobs[data.get("displayName")] = { 
                        "fullDisplayName": data.get("fullDisplayName"),
                        "score": data.get("healthReport")[0].get("score") if data.get("healthReport") else None,
                        "last_build_url": x,
                    }
            else:
                self.disabled_jobs[data.get("displayName")] = { 
                    "fullDisplayName": data.get("fullDisplayName"),
                    "score": data.get("healthReport")[0].get("score") if data.get("healthReport") else None,
                    "last_build_url": x,
                }

    def prepare_dict_data(self):
        self.get_jobs_detail()
        self.jobs_details["total_number_of_jobs"] = \
            len(self.aborted_jobs) \
            + len(self.fail_jobs) \
            + len(self.success_jobs) \
            + len(self.unknown_jobs) \
            + len(self.unstable_jobs)
        self.jobs_details["success_jobs"] = self.success_jobs
        self.jobs_details["aborted_jobs"] = self.aborted_jobs
        self.jobs_details["unstable_jobs"] = self.unstable_jobs
        self.jobs_details["fail_jobs"] = self.fail_jobs
        self.jobs_details["unknown_jobs"] = self.unknown_jobs
        self.jobs_details["disabled_jobs"] = self.disabled_jobs
        # self.jobs_details = abc

        add_to_logs(str(self.jobs_details))

    def prepare_html_report(self):
        with open("src/templates/theme.html") as description_template:
            if not os.path.exists("reports"):
                os.mkdir("reports")
            with open("reports/index.html", "w") as description_file:
                for x in description_template.readlines():

                    if "**Jenkins Dashboard**" in x:
                        x = x.replace("**Jenkins Dashboard**", f"<a href=\"{self.server_url}\">Jenkins Dashboard</a>")

                    if "**dump_your_total_jobs_count_here**" in x:
                        x = x.replace("**dump_your_total_jobs_count_here**", str(self.jobs_details.get("total_number_of_jobs")) if str(self.jobs_details.get("total_number_of_jobs")) else "o")

                    if "**dump_your_passed_jobs_count_here**" in x:
                        x = x.replace("**dump_your_passed_jobs_count_here**", str(len(self.jobs_details.get("success_jobs")) if self.jobs_details.get("success_jobs") else "0"))
                    if "**dump_your_passed_jobs_count_percentage_here**" in x:
                        x = x.replace("**dump_your_passed_jobs_count_percentage_here**", str((len(self.jobs_details.get("success_jobs")) * 100) // self.jobs_details.get("total_number_of_jobs") if self.jobs_details.get("success_jobs") else "0"))

                    if "**dump_your_failed_jobs_count_here**" in x:
                        x = x.replace("**dump_your_failed_jobs_count_here**", str(len(self.jobs_details.get("fail_jobs")) if self.jobs_details.get("fail_jobs") else "0"))
                    if "**dump_your_failed_jobs_count_percentage_here**" in x:
                        x = x.replace("**dump_your_failed_jobs_count_percentage_here**", str((len(self.jobs_details.get("fail_jobs")) * 100) // self.jobs_details.get("total_number_of_jobs") if self.jobs_details.get("fail_jobs") else "0"))

                    if "**dump_your_unstable_jobs_count_here**" in x:
                        x = x.replace("**dump_your_unstable_jobs_count_here**", str(len(self.jobs_details.get("unstable_jobs")) if self.jobs_details.get("unstable_jobs") else "0"))
                    if "**dump_your_unstable_jobs_count_percentage_here**" in x:
                        x = x.replace("**dump_your_unstable_jobs_count_percentage_here**", str((len(self.jobs_details.get("unstable_jobs")) * 100) // self.jobs_details.get("total_number_of_jobs") if self.jobs_details.get("unstable_jobs") else "0"))

                    if "**dump_your_aborted_jobs_count_here**" in x:
                        x = x.replace("**dump_your_aborted_jobs_count_here**", str(len(self.jobs_details.get("aborted_jobs")) if self.jobs_details.get("aborted_jobs") else "0"))
                    if "**dump_your_aborted_jobs_count_percentage_here**" in x:
                        x = x.replace("**dump_your_aborted_jobs_count_percentage_here**", str((len(self.jobs_details.get("aborted_jobs")) * 100) // self.jobs_details.get("total_number_of_jobs") if self.jobs_details.get("aborted_jobs") else "0"))

                    if "**dump_your_disabled_jobs_count_here**" in x:
                        x = x.replace("**dump_your_disabled_jobs_count_here**", str(len(self.jobs_details.get("disabled_jobs")) if self.jobs_details.get("disabled_jobs") else "0"))
                    if "**dump_your_disabled_jobs_count_percentage_here**" in x:
                        x = x.replace("**dump_your_disabled_jobs_count_percentage_here**", str((len(self.jobs_details.get("disabled_jobs")) * 100) // self.jobs_details.get("total_number_of_jobs") if self.jobs_details.get("disabled_jobs") else "0"))

                    if "**dump_your_unknown_jobs_count_here**" in x:
                        x = x.replace("**dump_your_unknown_jobs_count_here**", str(len(self.jobs_details.get("unknown_jobs")) if self.jobs_details.get("unknown_jobs") else "0"))
                    if "**dump_your_unknown_jobs_count_percentage_here**" in x:
                        x = x.replace("**dump_your_unknown_jobs_count_percentage_here**", str((len(self.jobs_details.get("unknown_jobs")) * 100) // self.jobs_details.get("total_number_of_jobs") if self.jobs_details.get("unknown_jobs") else "0"))

                    if "**dump_your_all_failing_jobs_here**" in x:
                        if self.jobs_details.get("fail_jobs"):
                            with open("src/templates/for_standalone/add_failing_job.html") as failing_jobs:
                                failing_jobs_html_template = failing_jobs.read()
                            failing_jobs_html = ""

                            for y, z in self.jobs_details.get("fail_jobs").items():
                                dummy_template = failing_jobs_html_template
                                dummy_template = dummy_template.replace("**dump_your_job_name**", z.get("fullDisplayName"))
                                dummy_template = dummy_template.replace("**dump_your_job_url**", z.get("last_build_url"))
                                dummy_template = dummy_template.replace("**dump_your_job_timestamp_here**", datetime.fromtimestamp(z.get("timestamp")/1000).strftime('%A, %-d-%-m-%Y at %-I:%M %p'))
                                failing_jobs_html += dummy_template.replace("**dump_your_job_duration**", f"{z.get("duration")//60} Min")
                                x = x.replace("**dump_your_all_failing_jobs_here**", failing_jobs_html)
                            description_file.writelines(failing_jobs_html)
                            continue
                        else:
                            x = x.replace("**dump_your_all_failing_jobs_here**", "🚀🚀No Failing Jobs Found On The Jenkins.🚀🚀")

                    if "**dump_your_all_unstable_jobs_here**" in x:
                        if self.jobs_details.get("unstable_jobs"):
                            with open("src/templates/for_standalone/add_unstable_job.html") as failing_jobs:
                                failing_jobs_html_template = failing_jobs.read()
                            failing_jobs_html = ""

                            for y, z in self.jobs_details.get("unstable_jobs").items():
                                dummy_template = failing_jobs_html_template
                                dummy_template = dummy_template.replace("**dump_your_job_name**", z.get("fullDisplayName"))
                                dummy_template = dummy_template.replace("**dump_your_job_url**", z.get("last_build_url"))
                                dummy_template = dummy_template.replace("**dump_your_job_timestamp_here**", datetime.fromtimestamp(z.get("timestamp")/1000).strftime('%A, %-d-%-m-%Y at %-I:%M %p'))
                                failing_jobs_html += dummy_template.replace("**dump_your_job_duration**", f"{z.get("duration")//3600} Hr")
                                x = x.replace("**dump_your_all_unstable_jobs_here**", failing_jobs_html)
                            description_file.writelines(failing_jobs_html)
                            continue
                        else:
                            x = x.replace("**dump_your_all_unstable_jobs_here**", "🚀🚀No Unstable Jobs Found On The Jenkins.🚀🚀")

                    if "**dump_your_all_aborted_jobs_here**" in x:
                        if self.jobs_details.get("aborted_jobs"):
                            with open("src/templates/for_standalone/add_aborted_job.html") as failing_jobs:
                                failing_jobs_html_template = failing_jobs.read()
                            failing_jobs_html = ""

                            for y, z in self.jobs_details.get("aborted_jobs").items():
                                dummy_template = failing_jobs_html_template
                                dummy_template = dummy_template.replace("**dump_your_job_name**", z.get("fullDisplayName"))
                                dummy_template = dummy_template.replace("**dump_your_job_url**", z.get("last_build_url"))
                                dummy_template = dummy_template.replace("**dump_your_job_timestamp_here**", datetime.fromtimestamp(z.get("timestamp")/1000).strftime('%A, %-d-%-m-%Y at %-I:%M %p'))
                                failing_jobs_html += dummy_template.replace("**dump_your_job_duration**", f"{z.get("duration")//3600} Hr")
                                x = x.replace("**dump_your_all_aborted_jobs_here**", failing_jobs_html)
                            description_file.writelines(failing_jobs_html)
                            continue
                        else:
                            x = x.replace("**dump_your_all_aborted_jobs_here**", "🚀🚀No Aborted Jobs Found On The Jenkins.🚀🚀")

                    if "**dump_your_all_disabled_jobs_here**" in x:
                        if self.jobs_details.get("disabled_jobs"):
                            with open("src/templates/for_standalone/add_disabled_job.html") as failing_jobs:
                                failing_jobs_html_template = failing_jobs.read()
                            failing_jobs_html = ""

                            for y, z in self.jobs_details.get("disabled_jobs").items():
                                dummy_template = failing_jobs_html_template
                                dummy_template = dummy_template.replace("**dump_your_job_name**", z.get("fullDisplayName"))
                                failing_jobs_html += dummy_template.replace("**dump_your_job_url**", z.get("last_build_url"))
                                x = x.replace("**dump_your_all_disabled_jobs_here**", failing_jobs_html)
                            description_file.writelines(failing_jobs_html)
                            continue
                        else:
                            x = x.replace("**dump_your_all_disabled_jobs_here**", "🚀🚀No Disable Jobs Found On The Jenkins.🚀🚀")

                    if "**dump_your_all_unknown_jobs_here**" in x:
                        if self.jobs_details.get("unknown_jobs"):
                            with open("src/templates/for_standalone/add_unknown_job.html") as failing_jobs:
                                failing_jobs_html_template = failing_jobs.read()
                            failing_jobs_html = ""

                            for y, z in self.jobs_details.get("unknown_jobs").items():
                                dummy_template = failing_jobs_html_template
                                dummy_template = dummy_template.replace("**dump_your_job_name**", z.get("fullDisplayName"))
                                failing_jobs_html += dummy_template.replace("**dump_your_job_url**", z.get("last_build_url"))
                                x = x.replace("**dump_your_all_unknown_jobs_here**", failing_jobs_html)
                            description_file.writelines(failing_jobs_html)
                            continue
                        else:
                            x = x.replace("**dump_your_all_unknown_jobs_here**", "🚀🚀No Unknown Jobs Found On The Jenkins.🚀🚀")

                    if "**dump_your_all_success_jobs_here**" in x:
                        if self.jobs_details.get("success_jobs"):
                            with open("src/templates/for_standalone/add_success_job.html") as failing_jobs:
                                failing_jobs_html_template = failing_jobs.read()
                            failing_jobs_html = ""

                            for y, z in self.jobs_details.get("success_jobs").items():
                                dummy_template = failing_jobs_html_template
                                dummy_template = dummy_template.replace("**dump_your_job_name**", z.get("fullDisplayName"))
                                dummy_template = dummy_template.replace("**dump_your_job_url**", z.get("last_build_url"))
                                dummy_template = dummy_template.replace("**dump_your_job_timestamp_here**", datetime.fromtimestamp(z.get("timestamp")/1000).strftime('%A, %-d-%-m-%Y at %-I:%M %p'))
                                failing_jobs_html += dummy_template.replace("**dump_your_job_duration**", f"{z.get("duration")//3600} Hr")
                                x = x.replace("**dump_your_all_success_jobs_here**", failing_jobs_html)
                            description_file.writelines(failing_jobs_html)
                            continue
                        else:
                            x = x.replace("**dump_your_all_success_jobs_here**", "⛔⛔No Successful Jobs Found On The Jenkins.⛔⛔")

                    description_file.write( x )


    def prepare_description_report(self):
        with open("src/templates/description.html") as description_template:
            with open("description.html", "w") as description_file:
                for x in description_template.readlines():

                    if "**Jenkins Dashboard**" in x:
                        x = x.replace("**Jenkins Dashboard**", f"<a href=\"{self.server_url}\">Jenkins Dashboard</a>")

                    if "**dump_your_total_jobs_count_here**" in x:
                        x = x.replace("**dump_your_total_jobs_count_here**", str(self.jobs_details.get("total_number_of_jobs")) if str(self.jobs_details.get("total_number_of_jobs")) else "o")
                    if "**dump_your_passed_jobs_count_here**" in x:
                        x = x.replace("**dump_your_passed_jobs_count_here**", str(len(self.jobs_details.get("success_jobs")) if self.jobs_details.get("success_jobs") else "0"))
                    if "**dump_your_failed_jobs_count_here**" in x:
                        x = x.replace("**dump_your_failed_jobs_count_here**", str(len(self.jobs_details.get("fail_jobs")) if self.jobs_details.get("fail_jobs") else "0"))
                    if "**dump_your_unstable_jobs_count_here**" in x:
                        x = x.replace("**dump_your_unstable_jobs_count_here**", str(len(self.jobs_details.get("unstable_jobs")) if self.jobs_details.get("unstable_jobs") else "0"))
                    if "**dump_your_aborted_jobs_count_here**" in x:
                        x = x.replace("**dump_your_aborted_jobs_count_here**", str(len(self.jobs_details.get("aborted_jobs")) if self.jobs_details.get("aborted_jobs") else "0"))
                    if "**dump_your_disabled_jobs_count_here**" in x:
                        x = x.replace("**dump_your_disabled_jobs_count_here**", str(len(self.jobs_details.get("disabled_jobs")) if self.jobs_details.get("disabled_jobs") else "0"))
                    if "**dump_your_unknown_jobs_count_here**" in x:
                        x = x.replace("**dump_your_unknown_jobs_count_here**", str(len(self.jobs_details.get("unknown_jobs")) if self.jobs_details.get("unknown_jobs") else "0"))

                    if "**dump_your_all_failing_jobs_here**" in x:
                        if self.jobs_details.get("fail_jobs"):
                            with open("src/templates/for_description/add_failing_job.html") as failing_jobs:
                                failing_jobs_html_template = failing_jobs.read()
                            failing_jobs_html = ""
                            for y, z in self.jobs_details.get("fail_jobs").items():
                                dummy_template = failing_jobs_html_template
                                dummy_template = dummy_template.replace("**dump_job_name_1_here**", z.get("fullDisplayName"))
                                failing_jobs_html += dummy_template.replace("**dump_failures_1_here**", z.get("last_build_url"))
                                x = x.replace("**dump_your_all_failing_jobs_here**", failing_jobs_html)
                            description_file.writelines(failing_jobs_html)
                            continue
                        else:
                            x = x.replace("**dump_your_all_failing_jobs_here**", "🚀🚀No Failing Jobs Found On The Jenkins.🚀🚀")

                    if "**dump_your_all_unstable_jobs_here**" in x:
                        if self.jobs_details.get("unstable_jobs"):
                            with open("src/templates/for_description/add_unstable_job.html") as unstable_jobs:
                                unstable_jobs_html_template = unstable_jobs.read()
                            unstable_jobs_html = ""
                            for y, z in self.jobs_details.get("unstable_jobs").items():
                                dummy_template = unstable_jobs_html_template
                                dummy_template = dummy_template.replace("**dump_unstable_job_name_1_here**", z.get("fullDisplayName"))
                                unstable_jobs_html += dummy_template.replace("**dump_unstable_count_1_here**", z.get("last_build_url"))
                                x = x.replace("**dump_your_all_unstable_jobs_here**", unstable_jobs_html)
                            description_file.writelines(unstable_jobs_html)
                            continue
                        else:
                            x = x.replace("**dump_your_all_unstable_jobs_here**", "🚀🚀No Unstable Jobs Found On The Jenkins.🚀🚀")
                    
                    if "**dump_your_all_aborted_jobs_here**" in x:
                        if self.jobs_details.get("aborted_jobs"):
                            with open("src/templates/for_description/add_aborted_job.html") as aborted_jobs:
                                aborted_jobs_html_template = aborted_jobs.read()
                            aborted_jobs_html = ""
                            for y, z in self.jobs_details.get("aborted_jobs").items():
                                dummy_template = aborted_jobs_html_template
                                dummy_template = dummy_template.replace("**dump_aborted_job_name_1_here**", z.get("fullDisplayName"))
                                aborted_jobs_html += dummy_template.replace("**dump_aborted_count_1_here**", z.get("last_build_url"))
                                x = x.replace("**dump_your_all_aborted_jobs_here**", aborted_jobs_html)
                            description_file.writelines(aborted_jobs_html)
                            continue
                        else:
                            x = x.replace("**dump_your_all_aborted_jobs_here**", "🚀🚀No Aborted Jobs Found On The Jenkins.🚀🚀")
                    
                    if "**dump_your_all_disabled_jobs_here**" in x:
                        if self.jobs_details.get("disabled_jobs"):
                            with open("src/templates/for_description/add_disabled_job.html") as disabled_jobs:
                                disabled_jobs_html_template = disabled_jobs.read()
                            disabled_jobs_html = ""
                            for y, z in self.jobs_details.get("disabled_jobs").items():
                                dummy_template = disabled_jobs_html_template
                                dummy_template = dummy_template.replace("**dump_disabled_job_name_1_here**", z.get("fullDisplayName"))
                                disabled_jobs_html += dummy_template.replace("**dump_disabled_count_1_here**", z.get("last_build_url"))
                                x = x.replace("**dump_your_all_disabled_jobs_here**", disabled_jobs_html)
                            description_file.writelines(disabled_jobs_html)
                            continue
                        else:
                            x = x.replace("**dump_your_all_disabled_jobs_here**", "🚀🚀No Disable Jobs Found On The Jenkins.🚀🚀")

                    if "**dump_your_all_success_jobs_here**" in x:
                        if self.jobs_details.get("success_jobs"):
                            with open("src/templates/for_description/add_success_job.html") as success_jobs:
                                success_jobs_html_template = success_jobs.read()
                            success_jobs_html = ""
                            for y, z in self.jobs_details.get("success_jobs").items():
                                dummy_template = success_jobs_html_template
                                dummy_template = dummy_template.replace("**dump_success_job_name_1_here**", z.get("fullDisplayName"))
                                success_jobs_html += dummy_template.replace("**dump_success_count_1_here**", z.get("last_build_url"))
                                x = x.replace("**dump_your_all_success_jobs_here**", success_jobs_html)
                            description_file.writelines(success_jobs_html)
                            continue
                        else:
                            x = x.replace("**dump_your_all_success_jobs_here**", "⛔⛔No Successful Jobs Found On The Jenkins.⛔⛔")

                    if "**dump_your_all_unknown_jobs_here**" in x:
                        if self.jobs_details.get("unknown_jobs"):
                            with open("src/templates/for_description/add_unknown_job.html") as unknown_jobs:
                                unknown_jobs_html_template = unknown_jobs.read()
                            unknown_jobs_html = ""
                            for y, z in self.jobs_details.get("unknown_jobs").items():
                                dummy_template = unknown_jobs_html_template
                                dummy_template = dummy_template.replace("**dump_unknown_job_name_1_here**", z.get("fullDisplayName"))
                                unknown_jobs_html += dummy_template.replace("**dump_unknown_count_1_here**", z.get("last_build_url"))
                                x = x.replace("**dump_your_all_unknown_jobs_here**", unknown_jobs_html)
                            description_file.writelines(unknown_jobs_html)
                            continue
                        else:
                            x = x.replace("**dump_your_all_unknown_jobs_here**", "🚀🚀No Unknown Jobs Found On The Jenkins.🚀🚀")

                    description_file.write( x )
