Call Center Analytics design will cover below four basics way of registering the complain and subsequently, we need to do sentiment analysis and analyse the KPIs.
a. Web method of call registering using text or voice supported by multiple languages
b. Chatbots complains from wen application frontend
c. Sentiment analysis of Bank of Baroda related messages from Twitter
The email will be sent out to support email id for highly dissatified complain. The same will be presented in real-time on Power BI dash board.

The Architect concept and flow diagram will be as below.
Flask application will be built and will be deployed on Azure with CI/CD pipeline using direct integration with GitHub.
The apps will allow user to register their comments either through text or voice or chatbots in multiple language or through twitter
Then the message will be sent through stream analytics for sentiment analysis on Jupiter notebook using python script.
At the same time data will be captured in Azure sql database.
The email will be sent out to the support email id for worst or highly dissatified comments or complains.
Then  power BI will be used to visualize the dashboard for KPI metric

Follow the BOB_Call_center_analytics_Solution_v1.0 for detail design description and design.
