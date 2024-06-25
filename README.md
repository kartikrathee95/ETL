# Calendar-Export

# DEPLOY BACKEND

1. Commit files except with .js extension, to integrations repo in a new branch.
2. sudo docker build -t c:latest --build-arg YOUR_ENV=integrationservice .
3. aws ecr get-login-password --region us-east-1 | sudo docker login --username AWS --password-stdin 602037364990.dkr.ecr.us-east-1.amazonaws.com
4. sudo docker tag c:latest 602037364990.dkr.ecr.us-east-1.amazonaws.com/onenote:latest
5. sudo docker push 602037364990.dkr.ecr.us-east-1.amazonaws.com/onenote:latest
6. aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 602037364990.dkr.ecr.us-east-1.amazonaws.com
7. docker pull 602037364990.dkr.ecr.us-east-1.amazonaws.com/onenote:latest
8. docker run -p 8003:8000 --restart always -e ENV_FOR_DYNACONF=testing 602037364990.dkr.ecr.us-east-1.amazonaws.com/onenote:latest

# INTEGRATE FRONTEND

1.setup local.app.com on the machine
2. add FrotendAPIs.js in web/js/render/calendar/API folder
3. Import the apis in MenuMain.js
4. Edit MenuMain.js with MenuMain.js in this repository
5. Take PR and deploy on local.testing.com


