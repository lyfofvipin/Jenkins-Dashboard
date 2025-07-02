import os
from datetime import datetime, timedelta

def add_to_logs(logs, file_name="common_logs", display=True):
    
    """
    Function to dump all the logs in a file and on the console
    """

    if not os.path.exists("logs"):
        os.mkdir("logs")
    with open(os.path.join("logs", file_name+".txt"), "a") as file:
        for x in logs.splitlines():
            if display: print(x)
            file.write(x+"\n")

def convert_sec_to_hr_min_sec(sec: int):
    if not sec: return f"Haven't Completed Yet"
    hr = sec // 3600
    min = (sec % 3600) // 60
    sec = ((sec % 3600) // 60) % 60
    return f"{hr}Hr {min}Min {sec} sec"


def dump_data_of_separate_entity_to_html( base_template_path: str, data: dict, new_file_name: str, status_template_html: str, string_to_replace_in_template: str, data_key_to_fetch: str, jobs_count_string: str, jobs_percentage_string: str, add_duration_and_timestamp: bool = True):

    data_collector = ""
    with open(base_template_path) as base_template:
        base_template_content = base_template.read()
        base_template_content = base_template_content.replace("**Jenkins Dashboard**", "<a href=\"index.html\">Jenkins Dashboard</a>")
        base_template_content = base_template_content.replace(jobs_count_string, str(len(data.get(data_key_to_fetch)) if data.get(data_key_to_fetch) else "0"))
        base_template_content = base_template_content.replace(jobs_percentage_string, str((len(data.get(data_key_to_fetch)) * 100) // data.get("total_number_of_jobs") if data.get(data_key_to_fetch) else "0"))
        data_collector = ""
        for y, z in data.get(data_key_to_fetch).items():
            dummy_template = status_template_html
            dummy_template = dummy_template.replace("**dump_your_job_name**", z.get("fullDisplayName"))
            dummy_template = dummy_template.replace("**dump_your_job_url**", z.get("last_build_url"))
            if add_duration_and_timestamp:
                dummy_template = dummy_template.replace("**dump_your_job_timestamp_here**", datetime.fromtimestamp(z.get("timestamp")/1000).strftime('%A, %-d-%-m-%Y at %-I:%M %p'))
                data_collector += dummy_template.replace("**dump_your_job_duration**", convert_sec_to_hr_min_sec(z.get("duration") if z.get("duration") else 0))
            else:
                data_collector += dummy_template
        base_template_content = base_template_content.replace(string_to_replace_in_template, data_collector)
    with open(new_file_name, "w") as all_failed_jobs_template:
        all_failed_jobs_template.writelines(base_template_content)

def validate_if_job_running_more_then_a_day(timestamp: str):
    return datetime.now() - datetime.fromtimestamp(timestamp/1000) >= timedelta(days=1)
