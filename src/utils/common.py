import os

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
