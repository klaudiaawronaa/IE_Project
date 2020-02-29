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


class User(Resource):

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
        if auth.username() == 'admin':
            cr.execute('SELECT * FROM users;')
        else:
            cr.execute('SELECT * FROM users WHERE username = "%s"' % auth.username())
        res = cr.fetchall()
        return res, 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username')
        parser.add_argument('password')
        parser.add_argument('email')
        args = parser.parse_args()
        cr.execute('SELECT * FROM users WHERE username = "%s" OR email = "%s";' % (args['username'], args['email']))

        if cr.fetchall():
            return "User with username '%s' or e-mail '%s' already exists!" % (args['username'], args['email']), 409
        if args['username'] is (None or '') or args['password'] is (None or ''):
            return 'Username and/or password cannot be empty', 400

        args['password'] = self.hash_password(args['password'])  # hash plain text pass
        cr.execute("INSERT INTO users (username, password, email) VALUES ('%s', '%s', '%s');"
                   % (str(args['username']), str(args['password']), str(args['email'])))
        dB.commit()  # commit changes to remote database

        return 'User created successfully', 201

    @auth.login_required
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id')
        parser.add_argument('username')
        parser.add_argument('password')
        parser.add_argument('email')
        args = parser.parse_args()

        if auth.username() == 'admin':
            #  search based on User.ID
            if args['password'] is (None or '') or args['email'] is (None or '') or args['username'] is (None or ''):
                return "Any information about user can not be empty", 400
            args['password'] = self.hash_password(args['password'])
            cr.execute('SELECT * from users where id = %s ;' % (args['id']))

            if len(cr.fetchall()) == 0:
                return "User with given ID does not exist.", 404

            cr.execute('SELECT * FROM users WHERE username = "%s" AND id = %s ;' % (args['username'], args['id']))
            if len(cr.fetchall()) == 0:
                cr.execute('SELECT * FROM users WHERE username = "%s" ;' % (args['username']))
                if len(cr.fetchall()) != 0:
                    return "User with given username already exists.", 404
            cr.execute('SELECT * FROM users WHERE email = "%s" AND id = %s ;' % (args['email'], args['id']))
            if len(cr.fetchall()) == 0:
                cr.execute('SELECT * FROM users WHERE email = "%s" ;' % (args['email']))
                if len(cr.fetchall()) != 0:
                    return "User with given email already exists.", 409

            cr.execute('UPDATE users '
                        'SET '
                       'username = "%s", '
                       'password = "%s", '
                       'email = "%s" '
                        'WHERE id = %s;' %
                        (str(args['username']),str(args['password']), str(args['email']), args['id']))

        else:
            #  search based on User.username
            if args['password'] is (None or '') or args['email'] is (None or '') or args['username'] is (None or ''):
                return "Any information about user can not be empty", 400
            args['password'] = self.hash_password(args['password'])

            if auth.username() != args['username']:
                return "User with given username already exists.", 409

            cr.execute('SELECT * FROM users WHERE email = "%s";' % (args['email']))
            if len(cr.fetchall()) != 0:
                cr.execute('SELECT * FROM users WHERE email = "%s" AND username = "%s" ;'
                           % (args['email'], args['username']))
                if len(cr.fetchall()) == 0:
                    return "User with given email already exists.", 409

            cr.execute('UPDATE users '
                       'SET '
                       'username = "%s", '
                       'password = "%s", '
                       'email = "%s" '
                       'WHERE id = %s;' %
                       (str(args['username']),str(args['password']), str(args['email']), args['id']))

        dB.commit()
        return "User updated successfully", 200

    @auth.login_required
    def delete(self):
        #  by User.ID
        parser = reqparse.RequestParser()
        parser.add_argument('id')
        args = parser.parse_args()
        if auth.username() == 'admin':
            cr.execute('SELECT * from users where id = %s' % args['id'])
            if len(cr.fetchall()) == 0:
                return "User with given ID does not exist.", 404

            cr.execute('DELETE FROM users WHERE id = %s' % args['id'])
            dB.commit()
            return "User deleted successfully", 204
        else:
            return "Unauthorized Access", 401
