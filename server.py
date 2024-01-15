from bs4 import BeautifulSoup
import socket, threading, struct, requests

l = threading.RLock()
users = dict()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

class Korisnik:
    def __init__(self,email,password,address):
        self.email, self.password, self.address = email, password, address


def recv_all(sock, length):
	data = b'' 
	while len(data) < length:
		more = sock.recv(length - len(data))
		data += more
	return data

def basic(data):
    url = "https://www.mse.mk/en/symbol/" + str(data[2])
    result = requests.get(url)
    page = BeautifulSoup(result.text, "html.parser")
    if page.find("div",{"id":"titleKonf2011"}):
        msg = "The company doesn't exist!"
    else:
        msg = "Issuer's basic data:\n"
        msg += "Name: " + page.find("div",{"class":"col-md-8 title"}).text + "\n"
                
        items = page.find("div",{"id":"izdavach"})
        for item in items.find_all("div",{"class":"row"})[2:7]:
            first = str(item.find("div",{"class":"col-md-4"}).text).strip()
            second = str(item.find("div",{"class":"col-md-8"}).text).strip()
            msg += first + ": " + second + "\n"
            
    return msg

def financial(data):
    url = "https://www.mse.mk/en/symbol/" + str(data[2])
    result = requests.get(url)
    page = BeautifulSoup(result.text, "html.parser")
    if page.find("div",{"id":"titleKonf2011"}):
        msg = "The company doesn't exist!"
    else:
        msg = "\nFinancial data(2020-2022) in denars:\n"
        table = page.find("tbody")
        for row in table.find_all("tr")[0:]:
            pom = 0
            msg += "\n"
            for colum in row:
                text = str(colum.text).strip()
                if len(text) == 0:
                    continue
                elif pom == 0:
                    msg += text + "\n"
                    pom += 1
                elif pom == 1:
                    msg += "In 2022: " + text +"\n"
                    pom += 1
                elif pom == 2:
                    msg += "In 2021: " + text + "\n"
                    pom += 1
                elif pom == 3:
                    msg += "In 2020: "+  text + "\n"
                    pom = 0
                        
    return msg
            
def ratios(data):
    url = "https://www.mse.mk/en/symbol/" + str(data[2])
    result = requests.get(url)
    page = BeautifulSoup(result.text, "html.parser")
    if page.find("div",{"id":"titleKonf2011"}):
        msg = "The company doesn't exist!"
    else:
        msg = "\nFinancial ratios(2020-2022) in denars:\n"
        table = page.find_all("tbody")[1]
        for row in table.find_all("tr")[0:]:
            pom = 0
            msg += "\n"
            for colum in row:
                text = str(colum.text).strip()
                if len(text) == 0:
                    continue
                elif pom == 0:
                    msg += text + "\n"
                    pom += 1
                elif pom == 1:
                    msg += "In 2022: " + text +"\n"
                    pom += 1
                elif pom == 2:
                    msg += "In 2021: " + text + "\n"
                    pom += 1
                elif pom == 3:
                    msg += "In 2020: "+  text + "\n"
                    pom = 0
    return msg            

def symbol(data):
    url = "https://www.mse.mk/en/symbol/" + str(data[2])
    result = requests.get(url)
    page = BeautifulSoup(result.text, "html.parser")
    if page.find("div",{"id":"titleKonf2011"}):
        msg = "The company doesn't exist!"
    else:
        msg = "\nSymbol data:\n"                
        items = page.find("div",{"id":"symbol-data"})
        for item in items.find_all("div",{"class":"row"})[:-1]:
            msg += str(item.text).strip() +"\n"
    
    return msg

def serverClient(s):
    while True:
        length = struct.unpack("!i", recv_all(s, 4))[0]
        data = (recv_all(s, length).decode("utf-8")).split("|")

        # Loggin and Register
        if data[0] == 'register':
            email = data[1]
            # l.acquire()
            #with l:
            if email in users:
                msg = "taken"
                length = len(msg)
                msg = (struct.pack("!i", length)) + msg.encode("utf-8")
                print(msg)
                s.sendall(msg)
            else:
                users[email] = Korisnik(email,data[2],s)
                msg = "registered"
                length = len(msg)
                msg = (struct.pack("!i", length)) + msg.encode("utf-8")
                s.sendall(msg)
            # l.release()


        elif data[0] == 'login':
            if data[1] in users:
                if data[2] == users[data[1]].password:
                    msg = "loggedin"
                    users[data[1]].address = s
                else:
                    msg = "error"
            else:
                msg = "error"
            
            length = len(msg)
            fullmsg = (struct.pack("!i", length)) + msg.encode("utf-8")
            s.sendall(fullmsg)

        # Scrapping commands
        # Get a list of the last traded shares
        elif data[0] == 'latest':
            url = "https://www.mse.mk/en/"
            msg = "Last Updated on: "
            result = requests.get(url)
            page = BeautifulSoup(result.text,"html.parser")
            sidebar = page.find("ul",{"class":"newsticker"})
            index = page.find("div",{"class": "index-title"})
            items = index.find_all("span")[3:]
            for item in items:
                msg += str(item.text).strip() + "\n"
            items = sidebar.find_all("li")
            for item in items:  
                msg += str(item.span.text).strip() + "\n"
            msg += "\nLink to the information: "+url+"\n"
            
            length = len(msg)
            fullmsg = struct.pack("!i", length) + msg.encode("utf-8")
            users[data[1]].address.sendall(fullmsg)
            

        elif data[0] == 'specific':
            msg = ""
            msg += basic(data)
            msg += financial(data)
            msg += ratios(data)
            msg += symbol(data)
            msg += "\nLink to the information: https://www.mse.mk/en/"+"\n"
            length = len(msg)
            fullmsg = struct.pack("!i", length) + msg.encode("utf-8")
            users[data[1]].address.sendall(fullmsg)

        # Basic issuers data
        elif data[0] == 'basic':
            msg = basic(data)
            msg += "\nLink to the information: https://www.mse.mk/en/"+"\n"
            length = len(msg)
            fullmsg = struct.pack("!i", length) + msg.encode("utf-8")
            users[data[1]].address.sendall(fullmsg)

        # Finnancial data
        elif data[0] == 'financial':
            msg = financial(data)
            msg += "\nLink to the information: https://www.mse.mk/en/"+"\n"
            length = len(msg)
            fullmsg = struct.pack("!i", length) + msg.encode("utf-8")
            users[data[1]].address.sendall(fullmsg)

        # Finnancial ratios data
        elif data[0] == 'ratios':
            msg = ratios(data)   
            msg += "\nLink to the information: https://www.mse.mk/en/"+"\n"         
            length = len(msg)
            fullmsg = struct.pack("!i", length) + msg.encode("utf-8")
            users[data[1]].address.sendall(fullmsg)

        # Symbol data
        elif data[0] == 'symbol':
            msg = symbol(data)
            msg += "\nLink to the information: https://www.mse.mk/en/"+"\n"
            length = len(msg)
            fullmsg = struct.pack("!i", length) + msg.encode("utf-8")
            users[data[1]].address.sendall(fullmsg)

        # Email Subscription - TODO

        else:
            msg = "Error wrong command"
            length = len(msg)
            fullmsg = (struct.pack("!i", length)) + msg.encode("utf-8")
            s.sendall(fullmsg)



s.bind(('localhost', 1060))
s.listen(1)
while True:
    sc, sockname = s.accept()
    print(sockname)
    threading.Thread(target=serverClient,args=(sc,)).start()
