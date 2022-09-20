import pymongo
from pymongo import MongoClient
from flask import Flask, request, Response, jsonify
from datetime import datetime
import json
import re

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
                    'role': 'Απλός Χρήστης'
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

    booking = {
        'flightInfo': flight,
        'bookingCreatedAt': datetime.now(),
        'user': logedinUser['email']
    }
    booking.insert_one(booking)

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
    
    booking = Booking.find_one({'_id': bookingID, 'user': logedinUser['email']})
    if booking != None:
        return jsonify(booking)
    else:
        return Response('no booking with that ID', status=404)