import mysql.connector
from flask import Flask
from flask_httpauth import HTTPBasicAuth
from flask_restful import Api, Resource, reqparse

from resource.User import User
from resource.Food import Food
from resource.Consumption import Consumption


app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()
dB = mysql.connector.connect(user='root', password='admin',
                             database='myDB', host='localhost')  # connect to data storage
cr = dB.cursor(buffered=True)  # obtain storage cursor


# cr.execute("select name, fat, sugar from food;")
# myresult = cr.fetchall()`
# for x in myresult:
#    print(x)


api.add_resource(User, "/users")
api.add_resource(Food, "/food")
api.add_resource(Consumption, "/consumptions")
#  api.add_resource(User, "/user/<string:name>")
#  **********************************************
app.run(debug=True)
