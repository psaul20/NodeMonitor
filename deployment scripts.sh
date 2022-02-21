## Deploy node monitor
gcloud functions deploy node-monitor \
  --source https://source.developers.google.com/projects/nodemonitor/repos/github_psaul20_nodemonitor/moveable-aliases/master/paths/src/NodeMonitor \
  --memory 512MB \
  --runtime python39 \
  --env-vars-file=src/NodeMonitor/.env.yaml \
  --trigger-topic=time-trigger \
  --region=us-central1 \
  --ingress-settings=internal-only \
  --timeout=300s
## Deploy SMS Manager
gcloud functions deploy sms-manager \
  --entry-point sms_Manager \
  --source https://source.developers.google.com/projects/nodemonitor/repos/github_psaul20_nodemonitor/moveable-aliases/master/paths/src/SmsManager \
  --memory 256MB \
  --runtime python39 \
  --env-vars-file=src/SmsManager/.env.yaml \
  --trigger-topic=send-sms \
  --region=us-central1 \
  --ingress-settings=internal-only

## Deploy Crypto_Price_Checker
gcloud functions deploy crypto-price-checker \
  --entry-point crypto_Price_Checker \
  --source https://source.developers.google.com/projects/nodemonitor/repos/github_psaul20_nodemonitor/moveable-aliases/master/paths/src/CryptoPriceChecker \
  --memory 256MB \
  --runtime python39 \
  --env-vars-file=src/CryptoPriceChecker/.env.yaml \
  --trigger-http \
  --region=us-central1 \
  --ingress-settings=internal-only

## Create PubSub Topic
gcloud pubsub topics create price-check


