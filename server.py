from bs4 import BeautifulSoup
import socket, threading, struct, requests, re, smtplib, time, schedule
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

l = threading.RLock()
users = dict()
subscribed = []
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

def send_email():
    sender_email = ""
    sender_password = "" # https://support.google.com/accounts/answer/185833?hl=en
    if(sender_email == '' or sender_password == ''):
        print("Can't send the emails because there sender email and password fields are empty")
    else:
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(sender_email, sender_password)
            content = latest()
            print("Preparing to send a daily email.\n")
            if subscribed:
                for receiver_email in subscribed:
                    try:
                        print("Sending email to " + receiver_email + " ... ")
                        msg = MIMEMultipart('alternative')
                        msg['Subject'] = "Daily Stock Report"
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        html = f"""
                        <html>
                        <body>
                        <p>{content}</p>
                        </body>
                        </html>
                        """
                        msg.attach(MIMEText(html, 'html'))
                        print("Done.\n")
                        server.sendmail(sender_email, receiver_email, msg.as_string())
                    except Exception as e:
                        print(f"Failed to send email to {receiver_email}: {e}/n")
        except Exception as e:
            print(f"Failed to connect to the SMTP server: {e}")
        finally:
            server.quit()

def latest():
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
    return msg

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
        table = page.find("tbody")
        if (re.compile(r'^RMDEN',re.IGNORECASE).match(data[2])):
            msg = "Denationalization bonds:\n"
            for row in table.find_all("tr")[0:]:
                msg += "\n"
                for colum in row:
                    text = str(colum.text).strip()
                    if len(text) == 0:
                        continue
                    msg += text + "\n"
        else:
            msg = "\nFinancial data(2020-2022) in denars:\n"
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
    msg += '\n'
    return msg
            
def ratios(data):
    url = "https://www.mse.mk/en/symbol/" + str(data[2])
    result = requests.get(url)
    page = BeautifulSoup(result.text, "html.parser")
    if page.find("div",{"id":"titleKonf2011"}):
        msg = "The company doesn't exist!"
    else:
        msg = "\nFinancial ratios(2020-2022) in denars:\n"
        if (re.compile(r'^RMDEN',re.IGNORECASE).match(data[2])):
            msg = "Government Bonds:\n"
            msg += "Starting from 08.01.2019, the continuous government bonds are listed on the Official Market of the Stock Exchange.\n"
        else:
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
            if email in users:
                msg = "taken"
                length = len(msg)
                msg = (struct.pack("!i", length)) + msg.encode("utf-8")
                s.sendall(msg)
            else:
                users[email] = Korisnik(email,data[2],s)
                msg = "registered"
                length = len(msg)
                msg = (struct.pack("!i", length)) + msg.encode("utf-8")
                s.sendall(msg)


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
            msg = ""
            msg = latest()
            length = len(msg)
            fullmsg = struct.pack("!i", length) + msg.encode("utf-8")
            users[data[1]].address.sendall(fullmsg)
            

        elif data[0] == 'specific':
            msg = ""
            msg += basic(data)
            if(msg != "The company doesn't exist!"):
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

        # Email Subscription
        elif data[0] == 'subscribe':
            if data[1] not in subscribed:
                subscribed.append(data[1])
                msg = "Successfully subscribed !"
            else:
                msg = "Successfully un-subscribed !"
                subscribed.remove(data[1])
            # print(subscribed)
            length = len(msg)
            fullmsg = struct.pack("!i", length) + msg.encode("utf-8")
            users[data[1]].address.sendall(fullmsg)

        else:
            msg = "Error wrong command"
            length = len(msg)
            fullmsg = (struct.pack("!i", length)) + msg.encode("utf-8")
            s.sendall(fullmsg)


def serveEmail():
    setTime = "14:02"
    schedule.every().monday.at(setTime).do(send_email)
    schedule.every().tuesday.at(setTime).do(send_email)
    schedule.every().wednesday.at(setTime).do(send_email)
    schedule.every().thursday.at(setTime).do(send_email)
    schedule.every().friday.at(setTime).do(send_email)
    while True:
        schedule.run_pending()
        time.sleep(1)

s.bind(('localhost', 1060))
s.listen(1)
threading.Thread(target=serveEmail,args=()).start()
while True:
    sc, sockname = s.accept()
    print(sockname)
    threading.Thread(target=serverClient,args=(sc,)).start()
