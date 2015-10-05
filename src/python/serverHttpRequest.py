import requests

class ServerHttpRequest:
    token = None
    validity = None
    url = None
    username = None
    password = None
    def __init__(self, url, username, password):
        self.url = url
        if (self.url[len(self.url)-1] != "/"):
            self.url = self.url + "/"
        self.username = username
        self.password = password
        self.getToken()

    def getToken(self):
        r = requests.post(self.url + "api/users/login",
                      json={"username": self.username, "password": self.password})
        print(r.text)
        response = r.json()
        self.token = response["token"];
        #self.validity = response["expire_date"]

    def get(self, url):
        print("get ", url)
        headers={"Authorization": "Bearer " + self.token}
        r = requests.get(self.url + url, headers=headers)
        r.raise_for_status()
        return r.json()

    def post(self, url, data={}):
        headers={"Authorization": "Bearer " + self.token}
        r = requests.post(self.url + url, headers=headers, json=data)
        return r.json()
    def put(self, url, data={}):
        headers={"Authorization": "Bearer " + self.token}
        r = requests.put(self.url + url, headers=headers, json=data)
        return r.json()
    def delete(self, url):
        headers={"Authorization": "Bearer " + self.token}
        r = requests.delete(self.url + url, headers=headers)
        return r.json()




