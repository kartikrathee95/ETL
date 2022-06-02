# Sentieo-Calendar-Export

***DEPLOY BACKEND STEPS ***
1. sudo docker build -t c:latest --build-arg YOUR_ENV=integrationservice .
2. aws ecr get-login-password --region us-east-1 | sudo docker login --username AWS --password-stdin 602037364990.dkr.ecr.us-east-1.amazonaws.com
3. sudo docker tag c:latest 602037364990.dkr.ecr.us-east-1.amazonaws.com/sentieoonenote:latest
4. sudo docker push 602037364990.dkr.ecr.us-east-1.amazonaws.com/sentieoonenote:latest
5. aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 602037364990.dkr.ecr.us-east-1.amazonaws.com
6. docker pull 602037364990.dkr.ecr.us-east-1.amazonaws.com/sentieoonenote:latest
7. docker run -p 8003:8000 --restart always -e ENV_FOR_DYNACONF=testing 602037364990.dkr.ecr.us-east-1.amazonaws.com/sentieoonenote:latest

# *** INTEGRATE FRONTEND
1.setup local.sentieo.com on the machine
2. add FrotendAPIs.js in sentieoweb/js/render/calendar/API folder
3. Import the apis in MenuMain.js
4. Edit MenuMain.js with MenuMain.js in this repository
5. Take PR and deploy on testing.sentieo.com


