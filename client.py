import sys, socket, threading, struct

def recv_all(sock, length):
    data = b''
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError('socket closed %d bytes into a %d-byte message' % (len(data), length))
        data += more
    return data

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

if len(sys.argv) > 3:
    s.connect(("localhost", 1060))
    email = sys.argv[1]
    password = sys.argv[2]
    if sys.argv[3].lower() == 'r':
        msg = "register|" + email + "|" + password
    elif sys.argv[3].lower() == 'l':
        msg = "login|" + email + "|" + password
    else:
        print("Invalid option! Use 'r' or 'l' for registering or login in respectively")
        sys.exit(-1)
    length = len(msg)
    fullmsg = (struct.pack("!i", length)) + msg.encode("utf-8")
    s.sendall(fullmsg)
    length = struct.unpack("!i", recv_all(s, 4))[0]
    reply = recv_all(s, length).decode()
    if reply == "error":
        print("Wrong email or password")
        sys.exit(-1)
    elif reply == "taken":
        print("There already exists a user with that email")
        sys.exit(-1)           
    elif reply == "loggedin":
        print("Succesfully logged in")
    elif reply == "registed":
        print("Succesfully registered")
    try:
        flag = True
        while flag:
            what = input('What is next? \t\no - Logout\t\nl - Get the latest traded stocks \t\ns - Get a specific stock(all the options bellow combined into one)\t\nb - Get the issuer\'s data of a specific stock\t\nf - Get the financial data of a specific stock\t\nr - Get the financial ratios of a specific stock\t\nsy- Get the symbol data of a specific stock\t\nsub - Subscribe/Unsubscribe to the daily stock report\n\n') 
            if(what == "l"):
                msg = "latest|"+email
            elif(what == "s"):
                msg = input("Enter the digit symbol for the stock:\t")
                msg = "specific|"+email+"|"+msg.upper()
            elif(what == 'o'):
                flag = False
                continue
            elif(what == "b"):
                msg = input("Enter the digit symbol for the stock:\t")
                msg = "basic|"+email+"|"+msg.upper()
            elif(what == "f"):
                msg = input("Enter the digit symbol for the stock:\t")
                msg = "financial|"+email+"|"+msg.upper()
            elif(what == "r"):
                msg = input("Enter the digit symbol for the stock:\t")
                msg = "ratios|"+email+"|"+msg.upper()
            elif(what == "sy"):
                msg = input("Enter the digit symbol for the stock:\t")
                msg = "symbol|"+email+"|"+msg.upper()
            elif(what == "sub"):
                msg = "subscribe|"+email
            else:
                print("Invalid command try again")
                continue
            length = len(msg)
            fullmsg = (struct.pack("!i", length)) + msg.encode("utf-8")
            s.sendall(fullmsg)
            length = struct.unpack("!i", recv_all(s, 4))[0]
            data = recv_all(s, length)
            data = (data.decode("utf-8"))
            print (data+"\n")
    except:
        print("Error")
    finally:
        print("Exiting the program")
        sys.exit(0)
else:
    print("Usage: " + sys.argv[0] + " email password type\n Type can be l(loggin) or r(register)")