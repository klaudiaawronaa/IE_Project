import json
from tokenize import String
import mysql.connector
from flask import Flask
from flask_httpauth import HTTPBasicAuth
from flask_restful import Api, Resource, reqparse
from passlib.apps import custom_app_context as pwd_context

app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()
dB = mysql.connector.connect(user='root', password='admin',
                             database='myDB', host='localhost')  # connect to data storage
cr = dB.cursor(buffered=True)  # obtain storage cursor


class Consumption(Resource):

    @staticmethod
    def hash_password(password):
        return pwd_context.hash(password)

    @auth.verify_password
    def authenticate(username, password):
        cr.execute('SELECT password from users WHERE username = "' + username + '";')
        stored_hash = cr.fetchall()

        if not stored_hash:
            return False
        if pwd_context.verify(password, stored_hash[0][0]):
            return True
        else:
            return False

    @auth.login_required
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('date')
        args = parser.parse_args()

        if auth.username() == 'admin':
            cr.execute('SELECT * FROM consumptions;')
            res = json.dumps(cr.fetchall(), indent=1, sort_keys=True, default=str)
            res = res.replace('\n', '')

        else:
            cr.execute('SELECT id FROM users WHERE username = "%s"' % auth.username())
            user_id = cr.fetchall()
            if args['date'] is (None or ''):
                return 'Date cannot be empty', 400

            cr.execute('SELECT food.name,food.calories,food.carbs,food.fat,food.fiber,'
                       'food.protein,food.saturated_fat,food.sodium,food.sugar,consumptions.amount FROM consumptions '
                       'INNER JOIN food ON consumptions.food_id = food.id AND consumptions.user_id = %s '
                       'WHERE consumptions.date LIKE "%s %%"' % (user_id[0][0], str(args['date'])))
            res = cr.fetchall()

            cr.execute('SELECT SUM(food.calories * consumptions.amount) '
                       'FROM consumptions '
                       'INNER JOIN food ON consumptions.food_id = food.id AND consumptions.user_id = %s '
                       'WHERE consumptions.date LIKE "%s %%"' % (user_id[0][0], str(args['date'])))
            res += cr.fetchall()
        return res, 200

    @auth.login_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name')
        parser.add_argument('amount')
        args = parser.parse_args()

        if args['name'] is (None or '') or args['amount'] is (None or ''):
            return 'Name and/or amount cannot be empty', 400
        cr.execute('SELECT * FROM food WHERE name = "%s"' % args['name'])
        if len(cr.fetchall()) == 0:
            return "Food with given name does not exist.", 404

        cr.execute('SELECT id FROM users WHERE username = "%s"' % auth.username())
        user_id = cr.fetchall()
        cr.execute('INSERT INTO consumptions SELECT id,%s,%s,CURRENT_TIMESTAMP from food where name = "%s"' %
                   (user_id[0][0], args['amount'], str(args['name'])))

        dB.commit()
        return "Product added to food list.", 200

    @auth.login_required
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name')
        parser.add_argument('amount')
        args = parser.parse_args()

        if args['name'] is (None or '') or args['amount'] is (None or ''):
            return 'Name and/or amount cannot be empty', 400

        cr.execute('SELECT * from food where name = "%s"' % str(args['name']))
        if len(cr.fetchall()) == 0:
            return "Food with given name does not exist.", 404

        cr.execute('SELECT id FROM food WHERE name = "%s"' % str(args['name']))
        food_id = cr.fetchall()
        cr.execute('SELECT id FROM users WHERE username = "%s"' % auth.username())
        user_id = cr.fetchall()

        cr.execute('UPDATE consumptions '
                   'SET '
                   'amount = "%s" '
                   'WHERE food_id = %s AND user_id = %s;' %
                   (args['amount'], food_id[0][0], user_id[0][0]))

        dB.commit()
        return "Product updated successfully", 200

    @auth.login_required
    def delete(self):

        parser = reqparse.RequestParser()
        parser.add_argument('name')
        args = parser.parse_args()

        if args['name'] is (None or ''):
            return 'Name cannot be empty', 400

        cr.execute('SELECT * from food where name = "%s"' % str(args['name']))
        if len(cr.fetchall()) == 0:
            return "Food with given name does not exist.", 404

        cr.execute('SELECT id FROM food WHERE name = "%s"' % str(args['name']))
        food_id = cr.fetchall()
        cr.execute('SELECT id FROM users WHERE username = "%s"' % auth.username())
        user_id = cr.fetchall()

        cr.execute('DELETE FROM consumptions WHERE food_id = "%s" AND user_id = "%s" AND DATE(date) = CURRENT_DATE'
                   % (food_id[0][0], user_id[0][0]))
        dB.commit()

        return "Consumption deleted successfully", 204
