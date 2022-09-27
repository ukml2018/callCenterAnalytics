import requests
import os
import json
import pyodbc
import time

#addition of extra packages -27th sep
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import speech_recognition as spr
from googletrans import Translator
import googletrans as Trans
### mail package ##start 
from email.message import EmailMessage
# Import modules
import smtplib, ssl
## email.mime subclasses
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
## The pandas library is only for generating the current date, which is not necessary for sending emails
import pandas as pd


###update sentiment logic fr twitter data -27th sep --start
def send_email(user_id,text_msg):     
    EMAIL_ADDRESS = 'bobcomplain@gmail.com'#os.environ.get('EMAIL_USER')
    EMAIL_PASSWORD = 'kkkcaxjcvxlaulqb'##os.environ.get('EMAIL_PASS')

    contacts = ['bobcomplain@gmail.com']

    msg = EmailMessage()
    msg['Subject'] = 'Escalation Email-Customer dissatisfaction'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = 'bobcomplain@gmail.com'

    msg.set_content('This is a plain text email')

    msg.add_alternative("""\
    <!DOCTYPE html>
    <html>
        <body>
            <h1 style="color:SlateGray;">User_id:""" +user_id+ """</h1>"
            <h2 style="color:SlateGray;">Customer Response:""" +text_msg+ """</h2>"
        </body>
    </html>
    """, subtype='html')


    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

def connection():
    s = 'ht-sqlserver22.database.windows.net' 
    d = 'callCenterdb' 
    u = 'adminuser' #Your login
    p = 'Passw0rd!' #Your login password
    cstr = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+s+';DATABASE='+d+';UID='+u+';PWD='+ p
    conn = pyodbc.connect(cstr)
    return conn
    
## function to get the compound polarity score 
def get_polarity_score (text):
    compound_score=0
    analyser = SentimentIntensityAnalyzer()
    compound_score=analyser.polarity_scores(text)
    return compound_score

def get_sentiment_label(score):
    sentiment_label :str=""
    customer_rating :str=""
    score = float(score)
    if score <=0:
        sentiment_label="Worst"
        customer_rating="Not At All Satisfactory"
    elif  0< score < 0.4:
        sentiment_label="Below Average"
        customer_rating="Not finding usage"
    elif   0.4< score < 0.5:  
        sentiment_label="Average"
        customer_rating="Needs huge improvisation"
    elif   0.5< score < 0.75: 
        sentiment_label="Good"
        customer_rating="Satisfied"   
    elif   0.75< score < 0.9:  
        sentiment_label="Very Good"
        customer_rating="Highly Satisfied"
    else:
        sentiment_label="Excellent"
        customer_rating="Outstanding Satisfaction"      
    return (sentiment_label,customer_rating)

## function to   update sentiment in db table 
def  capture_sentiment():
    #### capture all the encoded  language codes , for various other languages
    

    compound_score=0
    sentiment_df=pd.DataFrame(columns=['user_id','text_message','sentiment_value','polarity_score','transaction_type','languag'])
    server = 'ht-sqlserver22.database.windows.net'
    database = 'callCenterdb'
    username = 'adminuser'
    password = 'Passw0rd!'   
    driver= '{ODBC Driver 17 for SQL Server}'
    check_trx:str=""
    with pyodbc.connect('DRIVER='+driver+';SERVER=tcp:'+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id , text_message  , languag from callSentiment where sentiment_value is NULL; ")
            row = cursor.fetchone()
            while row:
                print (str(row[0]) + " " + str(row[1]))
                #print(f"type of str {type(str(row[1]))}")
                
                ##check if the "credit" or debit or loan , are present in text message 
                if str(row[1].lower()).find("credit")!=-1:
                    check_trx="credit"
                elif str(row[1].lower()).find("debit")!=-1:  
                    check_trx="debit"  
                elif  str(row[1].lower()).find("loan")!=-1:   
                    check_trx="loan" 
                else:
                    #print("Trx tyoe not credit , debit or lon") 
                    check_trx=""   

                sentiment_df=sentiment_df.append({'user_id':str(row[0]),'text_message':str(row[1]),'transaction_type':check_trx, 'languag':str(row[2])} , ignore_index=True)
                row = cursor.fetchone()           
             
         
            ###open the closed cursor now , for updation 
            cursor = conn.cursor()
            ##from_lang=""
            ### first filter  out the records having non english 
            # Creating Recogniser() class object
            for  index ,  each   in sentiment_df[sentiment_df['languag']!='english' ].iterrows():
                print(f"????????????????????? , printing language of each row  {each['languag']}")
                print(f"printing the  non english text entered {str(each['text_message'])}")
                translator = Translator()
                language_dict:dict = Trans.LANGUAGES
                print(f"printing the language   {each['languag']}")  
                print(f"#########################")
                from_lang =''   
                for k, v in language_dict.items():
                    ###print(f"printing  key {k} , value , {v}")                    
                    if each['languag']==v :
                        from_lang=k
                        print(f"printing  key {k} , value , {v}")
                        break
                
                to_lang = 'en'
                print(f"printing the source_language  {from_lang}")

                print("#############################")
                text_to_translate = translator.translate(str(each['text_message']),
                                                     src= from_lang,
                                                     dest= to_lang)
                # Storing the translated text in text
                # variable
                print(f" printing here : {text_to_translate.text}")
                print("printing the non english text into english ",str(each['text_message']) )  
                sql_0 = " update callSentiment  set text_message= "+"'"+text_to_translate.text+"'"+  " where user_id  = "+ each['user_id']                                   
                print(f"printing sql for language {sql_0}")      
                cursor.execute(sql_0) 
           

            ##first filter  out the dataframe  , only consisting of  not null trx type 
            for  index ,  each   in sentiment_df[sentiment_df['transaction_type']!=""].iterrows():
                #print(f"printing th user_id : {each['user_id']}  and  text_message :{each['text_message']} and trx_type {each['transaction_type']}")
                ###convert the transactio type to string 
                trxtype:str ="'"+str(each['transaction_type'])+"'"
                #print("trx type ",trxtype)
                #trxtype="loan"
                sql_1 = " update callSentiment  set transaction_type= "+str(trxtype)+  " where user_id  = "+ each['user_id']
                print(f"printing sql for trx type {sql_1}")      
                cursor.execute(sql_1)          
            #### call the loop for putting sentiment score and customer rating 
            for index , each in sentiment_df[sentiment_df['polarity_score']!=""].iterrows():

                ##call the function to recheck the polarity_score 
                print(f"printing the sentiment value  just as it is   {str(each['text_message'])}")
                compound_score=get_polarity_score(str(each['text_message']))
                print(f"the compund score is : {str(compound_score['compound'])} , type {type(compound_score)}")
                sql_2 = " update callSentiment  set polarity_score= "+"'"+str(compound_score['compound'])+"'"+  " where user_id  = "+ each['user_id']
                print(f"printing sql for polarity_score {sql_2}")      
                cursor.execute(sql_2)
                ###   next , call the function for checking  sentiment value and customer satisfaction rating 
                check_sentiment_label , check_cust_rating=get_sentiment_label(str(compound_score['compound']))
                sql_3="update callSentiment set sentiment_value="+"'"+check_sentiment_label+"'"+", customer_statisfaction_rating="+"'"+check_cust_rating+"'"+"where user_id  = "+ each['user_id']
                print(f"printing sql for sentiment value  {sql_3}")  
                cursor.execute(sql_3)

                ### call the function , for sending emails when polarity_score --start 
                if float(compound_score['compound']) < 0.39:
                    send_email(each['user_id'],each['text_message'] )
                #####call of  sending emails when polaroty_score --end 
                
                chck_time=time.strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("update dbo.callSentiment set  call_log_end=? ", chck_time)
            
            ### check the cursor for null transaction types   update them to generic 
            for  index ,  each   in sentiment_df[sentiment_df['transaction_type']=="" ].iterrows(): 
                print(f"Updating the NULL transaction types as generic, for userid {each['user_id'] }  , type {type(each['user_id'] )}")
                trx_type:str='generic'    
                sql = "update callSentiment  set transaction_type= "+"'"+str(trx_type) +"'"+"where  user_id  = "+ each['user_id']     
                cursor.execute(sql)  

            ##finally commit , aftre all the db transactions are over 
            cursor.commit()

    return sentiment_df

###update sentiment logic fr twitter data -27th sep --start

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
            if i > 2:
                ##added update sentiment functions:27th sep
                print(f"Calling Sentiment analysis")
                sentiment_df=capture_sentiment()
                break
            


def main():
    rules = get_rules()
    delete = delete_all_rules(rules)
    set = set_rules(delete)
    get_stream(set)

    


if __name__ == "__main__":
    main()
    