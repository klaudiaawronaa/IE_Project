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


class Food(Resource):

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

    def get(self):
        cr.execute('SELECT * FROM food')
        res = cr.fetchall()
        return res, 200

    @auth.login_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('calories')
        parser.add_argument('carbs')
        parser.add_argument('fat')
        parser.add_argument('fiber')
        parser.add_argument('name')
        parser.add_argument('protein')
        parser.add_argument('saturated_fat')
        parser.add_argument('sodium')
        parser.add_argument('sugar')
        args = parser.parse_args()

        if args['calories'] is (None or '') or args['carbs'] is (None or '') or args['fat'] is (None or '') \
                or args['fiber'] is (None or '') or args['name'] is (None or '') or args['protein'] is (None or '') \
                or args['saturated_fat'] is (None or '') or args['sodium'] is (None or '') or args['sugar'] is (
                None or ''):
            return 'Any information about food cannot be empty', 400

        if auth.username() == 'admin':
            cr.execute("SELECT * from food WHERE name = '%s'" % str(args['name']))
            if len(cr.fetchall()) != 0:
                return "Product with given name already exists.", 409

            cr.execute("INSERT INTO food (calories, carbs, fat, fiber, name, protein, saturated_fat, sodium, sugar)"
                       " VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')"
                       % (args['calories'], args['carbs'], args['fat'],
                          args['fiber'], str(args['name']), args['protein'],
                          args['saturated_fat'], args['sodium'], args['sugar']))

            dB.commit()
            return 'Food created successfully', 201
        else:
            return "Unauthorized Access", 401

    @auth.login_required
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('calories')
        parser.add_argument('carbs')
        parser.add_argument('fat')
        parser.add_argument('fiber')
        parser.add_argument('name')
        parser.add_argument('protein')
        parser.add_argument('saturated_fat')
        parser.add_argument('sodium')
        parser.add_argument('sugar')
        args = parser.parse_args()

        if args['calories'] is (None or '') or args['carbs'] is (None or '') or args['fat'] is (None or '') \
                or args['fiber'] is (None or '') or str(args['name']) is (None or '') or args['protein'] is (None or '')\
                or args['saturated_fat'] is (None or '') or args['sodium'] is (None or '') or args['sugar'] is (None or ''):
            return 'Any information about food cannot be empty', 400

        if auth.username() == 'admin':
            #  search based on food.name
            cr.execute('SELECT * from food where name = "%s"' % str(args['name']))
            if len(cr.fetchall()) == 0:
                return "Food with given name does not exist.", 404

            cr.execute('UPDATE food '
                       'SET '
                       'calories = %s, '
                       'carbs = %s, '
                       'fat = %s, '
                       'fiber = %s, '
                       'protein = %s, '
                       'saturated_fat = %s, '
                       'sodium = %s, '
                       'sugar = %s '
                       'WHERE name = "%s";' %
                       (args['calories'], args['carbs'], args['fat'], args['fiber'], args['protein'],
                        args['saturated_fat'], args['sodium'], args['sugar'], str(args['name'])))

            dB.commit()
            return "Food updated successfully", 200
        else:
            return "Unauthorized Access", 401

    @auth.login_required
    def delete(self):
        #  by food.name
        parser = reqparse.RequestParser()
        parser.add_argument('name')
        args = parser.parse_args()
        if auth.username() == 'admin':
            cr.execute('SELECT * from food where name = "%s"' % str(args['name']))
            if len(cr.fetchall()) == 0:
                return "Food with given name does not exist.", 404

            cr.execute('DELETE FROM food WHERE name = "%s"' % str(args['name']))
            dB.commit()
            return "Food deleted successfully", 204
        else:
            return "Unauthorized Access", 401