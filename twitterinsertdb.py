import requests
import os
import json
import pyodbc
import time

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
#bearer_token = os.environ.get("BEARER_TOKEN")
bearer_token = 'AAAAAAAAAAAAAAAAAAAAAL9mhQEAAAAAV01l5q2n1sn8BnDRQsWLAek0s0U%3DStHFfgeHRWr3ZVdRIgCLPQQEoL4VBcFhMxOLPgbh2ATe5cW5XI'

def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FilteredStreamPython"
    return r

def connection():
    s = 'ht-sqlserver22.database.windows.net' 
    d = 'callCenterdb' 
    u = 'adminuser' #Your login
    p = 'Passw0rd!' #Your login password
    cstr = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+s+';DATABASE='+d+';UID='+u+';PWD='+ p
    conn = pyodbc.connect(cstr)
    return conn


def get_rules():
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))
    return response.json()


def delete_all_rules(rules):
    if rules is None or "data" not in rules:
        return None

    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot delete rules (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    print(json.dumps(response.json()))


def set_rules(delete):
    # You can adjust the rules if needed
    sample_rules = [
        {
         "value": "@bankofbaroda", "tag": "CreditCard",
         "value": "@bankofbaroda", "tag": "Account",
         "value": "@bankofbaroda", "tag": "SavingAccount",
         "value": "@bankofbaroda", "tag": "debitcard",
         "value": "@bankofbaroda", "tag": "faurd",
        }
    ]
    payload = {"add": sample_rules}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            "Cannot add rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))


def get_stream(set):
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream", auth=bearer_oauth, stream=True,
    )
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(
            "Cannot get stream (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )

    i =0
    for response_line in response.iter_lines():
        if response_line:
            json_response = json.loads(response_line)
            #print(json.dumps(json_response, indent=4, sort_keys=True))
            conn = connection()
            cursor = conn.cursor()
            cursor.execute("SELECT max(user_id) as user_id FROM dbo.callSentiment")
            for row in cursor.fetchall():
                user_id = row[0] + 1
            print(user_id)
            start_time = time.strftime('%Y-%m-%d %H:%M:%S')
            Sentiment_data = json_response["data"]['text']
            print(json_response["data"]['text'])
            cursor.execute("INSERT INTO dbo.callSentiment(user_id, text_message, agent_id, is_twitter_not, languag, call_log_start) VALUES (?, ?, ?, ?,? ,?)", user_id, Sentiment_data,'Clara' ,'twitter', 'english', start_time)
            conn.commit()
            conn.close()
            i = i + 1
            if i > 10:
                break
            


def main():
    rules = get_rules()
    delete = delete_all_rules(rules)
    set = set_rules(delete)
    get_stream(set)


if __name__ == "__main__":
    main()