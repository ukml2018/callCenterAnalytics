from datetime import datetime
import random
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import speech_recognition as spr
from googletrans import Translator
import googletrans as Trans
import os
import pandas as pd 
### mail package ##start 
import smtplib
import imghdr
from email.message import EmailMessage
import torch
import pyodbc
from model import NeuralNet
from nltk_utils import bag_of_words, tokenize
##import datetime
import time
import nltk
nltk.download('punkt')

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

with open('intents.json', 'r') as json_data:
    intents = json.load(json_data)

FILE = "data.pth"
data = torch.load(FILE)

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data['all_words']
tags = data['tags']
model_state = data["model_state"]

model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

bot_name = "Clara"

### addition of sentiment code ## may need t modularize ---asmita 

def connection():
    s = 'ht-sqlserver22.database.windows.net' 
    d = 'callCenterdb' 
    u = 'adminuser' #Your login
    p = 'Passw0rd!' #Your login password
    cstr = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+s+';DATABASE='+d+';UID='+u+';PWD='+ p
    conn = pyodbc.connect(cstr)
    return conn

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
            <h1 style="color:SlateGray;">Response entered from Chatbot</h1>"
            <h2 style="color:SlateGray;">User_id:""" +user_id+ """</h2>"
            <h3 style="color:SlateGray;">Customer Response:""" +text_msg+ """</h3>"
        </body>
    </html>
    """, subtype='html')


    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    
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
                ###update the cal_log_end 
                
                #date_str = pd.Timestamp.today().strftime('%Y-%m-%d')#YYYY-MM-DD HH24:MI:SS.FF
                #ts=time.time()
                ##date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                #date_str = datetime.utcnow()
                #date_str = pd.Timestamp.today().strftime('%Y-%m-%d %H:%M:%S')                
                #date_str=datetime. strptime(date_str, '%d/%m/%y %H:%M:%S')


                date_str=   time.strftime('%Y-%m-%d %H:%M:%S')           
                print(f"!!!!!!!!!!!!  after conversion , updating the call log end time {date_str}, {type(date_str)}")
                ##sql_3 = "update callSentiment  set call_log_end= "+date_str+  " where user_id  = "+ each['user_id']
                #cursor.execute(sql_3)
                cursor.execute("update dbo.callSentiment set  call_log_end=? ", date_str)
                

                ###   next , call the function for checking  sentiment value and customer satisfaction rating 
                check_sentiment_label , check_cust_rating=get_sentiment_label(str(compound_score['compound']))
                sql_3="update callSentiment set sentiment_value="+"'"+check_sentiment_label+"'"+", customer_statisfaction_rating="+"'"+check_cust_rating+"'"+"where user_id  = "+ each['user_id']
                print(f"printing sql for sentiment value  {sql_3}") 

                ### call the function , for sending emails when polarity_score --start 
                if float(compound_score['compound']) < 0.39:
                    send_email(each['user_id'],each['text_message'] )
                #####call of  sending emails when polaroty_score --end 
                  
                cursor.execute(sql_3)
                ### check the cursor for null transaction types   update them to generic 
                for  index ,  each   in sentiment_df[sentiment_df['transaction_type']=="" ].iterrows(): 
                    print(f"Updating the NULL transaction types as generic, for userid {each['user_id'] }  , type {type(each['user_id'] )}")
                    trx_type:str='generic'    
                    sql = "update callSentiment  set transaction_type= "+"'"+str(trx_type) +"'"+"where  user_id  = "+ each['user_id']     
                    cursor.execute(sql)  
            cursor.commit()

    return sentiment_df


### addition of sentiment code --asmita 

def get_response(msg):
    sentence = tokenize(msg)
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device)

    output = model(X)
    _, predicted = torch.max(output, dim=1)

    tag = tags[predicted.item()]
    #print(f"Printing the tag inside ethe training process {tag}")
    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]
    if prob.item() > 0.75:
        for intent in intents['intents']:
            if tag == intent["tag"]:
               ## print(f"printing the tag fro the chatbot  before inserting intosql server table:{tag} ")
                #print(f"random.choice(intent['responses']){random.choice(intent['responses'])} ")
                ##print(f"printing  tag!!!!  {intent['tag']}")
                if  intent["tag"]=="payments":
                    print(f"The message entered is  {msg}")
                    ##print(f"intent['patterns'] entered is :  {intent['patterns']}")
                    ### sentiment code start ##
                    ##insert the data into sql server 
                    conn = connection()
                    #print("Amit1.1")
                    cursor = conn.cursor()
                    cursor.execute("SELECT max(user_id) as user_id FROM dbo.callSentiment")
                    for row in cursor.fetchall():
                        user_id = row[0] + 1
                        print(user_id)
                    chck_time=time.strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute("INSERT INTO dbo.callSentiment(user_id,  languag, text_message,agent_id,is_twitter_not,call_log_start , call_log_end) VALUES (?, ?, ?, ?,?,?,?)", user_id,  'english', msg,'Clara','chat',chck_time ,chck_time)
                    conn.commit()
                    conn.close() 

                    print(f"Calling Sentiment analysis")
                    sentiment_df=capture_sentiment()
                    sentiment_df.reset_index(drop=True)
                    print(f" Printing the  retrieved  value in df mode :\n{sentiment_df[['user_id','text_message','transaction_type','languag']]}")
                    print(f"printing the type of index : {sentiment_df.index}")
            
                    ### sentiment code end ##
                return random.choice(intent['responses'])
                    
            
    
    return "I do not understand..Please rephrase and enter short sentences as much possible."


if __name__ == "__main__":
    list_check=[]
    print("Let's chat! (type 'quit' to exit)")
    while True:
        # sentence = "do you use credit cards?"
        sentence = input("You: ")
        if sentence == "quit":
            break

        resp = get_response(sentence)
        print(resp)
        
            
