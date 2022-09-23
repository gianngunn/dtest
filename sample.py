import pymongo
from pymongo import MongoClient
from flask import Flask, request, Response, jsonify
from datetime import _Time, datetime
import json
import re
import random

client = MongoClient('mongodb://docker:mongopw@localhost:49153')

db = client['DSAirlines']
User = db['Users']
Flight = db['Flights']
Booking = db['Bookings']

app = Flask(__name__)
logedin = 0
logedinUser = None

if User.count_documents({'role':'admin'}) == 0:
    User.insert_one({'name':'admin', 'password':'admin', 'email':'admin@admin.com', 'role':'admin', 'changedPass': 'no'})

@app.route('/register', methods=['POST'])
def register():

    data = None

    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500)

    if data == None:
        return Response("bad request", status=500)

    if not 'email' in data or not 'username' in data or not 'name' in data or not 'lastname' in data or not 'password' in data or not 'passpordNumber' in data:
        return Response("Information incompleted", status=500)

    if User.count_documents({'email': data['email']}) == 0:
        if User.count_documents({'username': data['username']}) == 0:
            if User.count_documents({'passpordNumber': data['passpordNumber']}) == 0:
                if len('password') < 8:
                    return Response("password needs to be 8 length and bigger, try again", status=200)
                if any(i.isdigit() for i in 'password') == False:
                    return Response("password must contain a number", status=200) 
                """
                thelei kai gia akribos 1 arimtho?
                alpha,string=0,"Geeks1234"
                for i in string:
                    if (i.isalpha()):
                        alpha+=1
                print("Number of Digit is", len(string)-alpha)
                print("Number of Alphabets is", alpha)

                elenxos gia diabatirio
                regex = "/^[A-Z]{2}\d{7}$/"
                p = re.complie(regex)
                if (string == ''):
                    return False
                m = re.match(p, 'passportNumber')
                if m is None:
                    return False
                """
                user = {
                    'email': data['email'],
                    'username': data['username'],
                    'name': data['name'],
                    'lastname': data['lastname'],
                    'password': data['password'],
                    'passpordNumber': data['passpordNumber'],
                    'role': "Απλός Χρήστης",
                    'activeUser': "yes",
                    'activationNumber': None
                }
                User.insert_one(user)
                return Response("User successfully registered!!", status=201)
            else:
               return Response("passpordNumber is used, try another one", status=200) 
        else:
            return Response("username is used, try another one", status=200)
    else:
        return Response("email is used, try another one", status=200)

@app.route('/login', methods=['POST'])
def login():
    global logedin, logedinUser
    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500)

    if data == None:
        return Response("bad request", status=500)
    
    if not 'email' in data and not 'username' in data or not 'password' in data:
        return Response("Information incompleted", status=500)

    if 'email' in data:
        user = User.find_one({'email': data['email']})
    else:
        user = User.find_one({'username': data['username']})

    if not user:
        logedinUser = None
        logedin = 0
        return Response("you must register first in order to log in, if you are admin use email only", status=404)
    
    if user['activeUser'] == 'no':
        return Response('your account is not active. activete it first, go to /accountActivation', status=404)

    if user['password'] == data['password']:
        logedinUser = user
        logedin = 1
        if user['role'] == 'admin':
            if user['changedPass'] == 'no':
                return Response("go to /changepassA to change your password", status=200)
            else:
                return Response('welcome admin!!',status=200)
        return Response("User successfully loged in!!", status=202)
    else:
        logedinUser = None
        logedin = 0
        return Response("Wrong password, try again!!", status=401)

@app.route('/getFlight/<string:location>/<string:destination>/<date:dateDe>', methods=['GET'])
def getFlight(location, destination, dateDe):
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)
    if location == None:
        return Response("Bad request", status=400)
    if destination == None:
        return Response("Bad request", status=400)
    if dateDe == None:
        return Response("Bad request", status=400)

    flights = Flight.find({'departure': location, 'destination': destination, 'deTime': dateDe})

    x = []
    for g in flights:
        if g['availability'] > 0:
            x.append(g)
    if x == []:
        return Response("no flights", status=404)
    return jsonify(x) 
    #to jsonify mporei na min xreiazetai    

@app.route('/ticketBooking/<string:UNF>/<string:name>/<string:passportNumber>/<string:creditcard>', methods=['POST'])
def ticketBooking(UFN, name, passportNumber, creditcard):
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)
    if UFN == None:
        return Response("Bad request", status=400)
    if name == None:
        return Response("Bad request", status=400)
    if passportNumber == None:
        return Response("Bad request", status=400)
    if creditcard == None:
        return Response("Bad request", status=400)

    if len(creditcard) != 16:
        return Response("creditcard must be of size 16", status=404)

    flight = Flight.find_one({'uniqueFN': UFN})
    
    if flight['availability'] == 0:
        return Response('flight is full', status=404)
    idb=datetime.now().strftime('%Y%m%d%H%M%S')
    booking = {
        'bookingID': idb # ebala auto edw giati mporei na uparxei problima me tin emfanisi tou _id opote opote einai na ginei emfanisi na ginete to _id = none alla ama ginei auto tha prepei na allajoun ta upoloipa '_id' me 'bookingID'
        'departure': flight['location'], 
        'destination': flight['destination'],
        'bookingCreatedAt': datetime.now(),
        'user': logedinUser['email'],
        'userPassport': passportNumber,
        'bookingCost': flight['cost'],
        'creditcardUsed': creditcard
    }
    Booking.insert_one(booking)

    flight['availability'] = flight['availability'] - 1
    #?mporei na thelei jsonify
    return Response(booking, status=201)

@app.route('/getBooking/<string:bookingID>', methods=['GET'])
def getBooking(bookingID):
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)
    if bookingID == None:
        return Response("Bad request", status=400)
    
    booking = Booking.find_one({'_id': bookingID, 'user': logedinUser['email']}) #*
    if booking != None:
        return jsonify(booking)
    else:
        return Response('no booking with that ID', status=404)

@app.route('/deleteBooking/<string:bookingID>', methods=['DELETE'])
def deleteBooking(bookingID):
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)
    
    booking = Booking.find_one({'_id': bookingID, 'user': logedinUser['email']}) #*

    if booking != None:
        x = Booking.find_one({'_id': bookingID}) #*

        Booking.delete_one({'_id': bookingID}) #*
        return Response('Booking deleted! the money will be returned to card number: ',x['credidcardUsed'], status=200) #?
    else:
        return Response('no booking with that ID', status=404)

@app.route('/getAllBookings/<string:order>', methods=['GET'])
def getAllBookings(order):
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)
    if order == 'asc':
        bookings = Booking.find({'user': logedinUser['_id']}).sort(
            'bookingCreatedAt', pymongo.ASCENDING)
        x = []
        for g in bookings:
            #g['_id'] = None
            #g['user'] = logedinUser['username']
            x.append(g)

        if x == []:
            return Response("no bookings", status=404)
        return jsonify(x)
    if order == 'des':
        bookings = Booking.find({'user': logedinUser['_id']}).sort(
            'bookingCreatedAt', pymongo.DESCENDING)
        x = []
        for g in bookings:
            #g['_id'] = None
            #g['user'] = logedinUser['username']
            x.append(g)

        if x == []:
            return Response("no bookings", status=404)
        return jsonify(x)

@app.route('/getCheapestAndMostExpensiveBooking', methods=['GET'])
def getCheapestOrMostExpensiveBooking():
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)

    
    bookings = Booking.find({'user': logedinUser['_id']}).sort(
        'bookingCost', pymongo.ASCENDING)
    x = []
    for g in bookings:
        #g['_id'] = None
        #g['user'] = logedinUser['username']
        x.append(g)

    if x == []:
        return Response("no bookings", status=404)

    for j in x:
        if x[0]['bookingCost'] == j['bookingCost']:
            if x[0]['bookingCreatedAt'] < j['bookingCreatedAt']:
                x[0] = j
    
    bookings = Booking.find({'user': logedinUser['_id']}).sort(
        'bookingCost', pymongo.DESCENDING)
    k = []
    for g in bookings:
        #g['_id'] = None
        #g['user'] = logedinUser['username']
        k.append(g)

    if k == []:
        return Response("no bookings", status=404)
    for j in k:
        if k[0]['bookingCost'] == j['bookingCost']:
            if k[0]['bookingCreatedAt'] < j['bookingCreatedAt']:
                k[0] = j
    
    # x,k==[] mporei na ginei if bookings == None -> return...
    #theloume elegxo gia otan eiai 1 booking?
    """
    if x[0] == k[0]:
        return Response("you have only 1 booking", x[0])
    
    """
    return x[0],k[0]

@app.route('/getBookingsBasedOnDest/<string:dest>', methods=['GET'])
def getBookingsBasedOnDest(dest):
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)

    if dest == None:
        return Response("fill the destination!!", status=404)

    allbookings = Booking.find({'user': logedinUser['email'], 'destination': dest})

    if allbookings == None:
        return Response("you dont have bookings for this destination!!", status=404)

    return allbookings

@app.route('/deactivateAccount', methods=['PATCH'])
def deactivateAccount():
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)
    
    #User.update_one({'email':logedinUser['email']}, {'$set': {'activeUser': "no"}})

    n = random.randint(100000000000,999999999999)

    users = User.find({'activeUser': "no"})
    """j = 0
    for g in users:
        if n == users['activationNumber']:
            if n == 999999999999:
                n = n - 1 
            else:
                n = n + 1

                 OR

                while users.count_documents({'activationNumber': n}) != 0:
                    if n == 999999999999:
                        n = 100000000000 
                    else:
                        n = n + 1
                        #this is better i think

                """
    User.update_one({'email':logedinUser['email']}, {'$set': {'activeUser': "no", 'activationNumber: n'}})

    return Response("you acc has been deactivated this is your reset code " ,n, status=200)
@app.route('/accountActivation', methods=['PATCH'])
def accountActivation():
     data = None

    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=400)

    if data == None:
        return Response("bad request", status=400)

     if not 'activationNumber' in data or not 'passportNumber' in data:
        return Response('information incomplite', status= 400)
    
    user = User.find_one({'passportNumber': data['passportNumber']})

    if user == None:
        return Response("No user!!", status=404)

    if user['activeUser'] == "no":
        if user['activationNumber'] == data['activationNumber']:
            User.update_one({'email':data['emai']},{
                '$set': {'activeUser': "yes", 'activationNumber': None}
            })
            return Response("account activated", status=200)
        else:
            return Response("wrong activation number", status=404)
    else:
        return Response("your account is active", status=200)

@app.route('/newAdmin', methods=['POST'])
def newAdmin():
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)
    if logedinUser['role'] == 'admin':
        data = None

        try:
            data = json.loads(request.data)
        except Exception as e:
            return Response("bad json content", status=400,)

        if data == None:
            return Response("bad request", status=400)

        if User.count_documents({'email': data['email']}) == 0:

            admin = {
                'name': data['name'],
                'email': data['email'],
                'password': data['password'],
                'role': 'admin',
                'changedPass': 'no'
            }
            User.insert_one(admin)
            return Response("Admin successfully registered!!", status=201)

        else:
            return Response("email is used, try another one", status=200)
    else:
        return Response('This is for admins only!!', status=405)

@app.route('/createNewFlight', methods=['POST'])
def createNewFlight():
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)
    if logedinUser['role'] == 'admin':
        data = None

        try:
            data = json.loads(request.data)
        except Exception as e:
            return Response("bad json content", status=400,)

        if data == None:
            return Response("bad request", status=400)
        
        if not 'departure' in data or not 'destination' in data or not 'cost' in data or not 'flightDuration' in data or not 'date' in data:
            return Response("Information incompleted", status=500)

        Dep = data['departure'][0]
        Des = data['destination'][0]
        Year = data['date'].strftime("%Y")[2:3]
        M = data['date'].strftime("%m")
        Day = data['date'].strftime("%d")
        Time = data['date'].strftime("%H")

        UFN = Dep+Des+Year+M+Day+Time

        if Flight.count_documents({'uniqueFN': UFN}) == 0:
            flight = {
                'DateAndTime': data['date'],
                'departure': data['departure'],
                'destination': data['destination'],
                'cost': data['cost'],
                'flightDuration': data['flightDuration'],
                'uniqueFN': UFN,
                'availability': 220
            }
            Flight.insert_one(flight)
            return Response('Flight created!', status=200)
        else:
            return Response('this flight existes', status=404)


        
            
    else:
        return Response('This is for admins only!!', status=405)    


@app.route('/changepassA', methods=['PATCH'])
def changepassA():
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)
    data = None

    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=400)

    if data == None:
        return Response("bad request", status=400)
    
    if 'password' not in data:
        return Response('wrong data', status= 400)
    
    if logedinUser['role'] == 'admin':
        User.update_one({'email': logedinUser['email']}, {
                        '$set': {'password': data['password'], 'changedPass': 'yes'}})
        return Response('Pass changed!!', status=200)
    else:
        return Response('go back', status=405)