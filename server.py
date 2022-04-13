

"""
Columbia W4111 Intro to databases
Example webserver
To run locally
    python server.py
Go to http://localhost:8111 in your browser
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response,flash, session, abort


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)



# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "ram2277"
DB_PASSWORD = "6827"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request
  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print ("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():

  name = request.form['name']

  cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';

  g.conn.execute(text(cmd), name1 = name, name2 = name);
  
  return redirect('/')


@app.route('/')
def home():

  if not session.get('logged_in'):

    return render_template('login.html')

  else:

    return "Hello Boss!"



@app.route('/login', methods = ['POST'])
def login():

  password_prime = request.form['password']

  username_prime = request.form['username']

  cmd = 'SELECT uid FROM U WHERE name = (:n1)';

  cursor = g.conn.execute(text(cmd), n1 = username_prime);

  password = []

  for result in cursor:

    password.append(result['uid'])  # can also be accessed using result[0]

  cursor.close()

  if password_prime == str(password[0]) :

    session['logged_in'] = True

    session['uid'] = password_prime

  else:
    flash('wrong password!')

  return redirect('/')



@app.route('/restroom/<rid>/create_tips')
def create_tips(rid, methods = ['GET','POST']):

  return render_template("tips.html", rid =rid)



@app.route('/add_tips/<rid>',  methods=['POST'])
def add_tips(rid):

  label = request.form['label_box']

  desc = request.form['tips_desc'] 

  uid = session['uid']

  cmd = 'INSERT INTO Tips VALUES (:u, :r, DEFAULT, :l, :d)';

  g.conn.execute(text(cmd), u = uid, r = rid, l = label, d = desc);

  return redirect('/restroom/'+rid)






@app.route('/restroom/<rid>')
def restroom(rid):

  cmd = 'SELECT U.name, T.label, T.description FROM Tips as T JOIN U ON T.uid = U.uid WHERE T.rid = (:r1)';

  cursor = g.conn.execute(text(cmd), r1 = rid);

  tips_dic = {'names_tips':[], 'labels_tips':[],'desc_tips':[]}

  for result in cursor:

    tips_dic['names_tips'].append(result['name'])

    if result['label'] != 'None':
      tips_dic['labels_tips'].append(result['label'])
    else:
      tips_dic['labels_tips'].append(None)

    tips_dic['desc_tips'].append(result['description'])

  cursor.close()

  cmd = 'SELECT U.name, R.review, R.stars, R.photos FROM Review as R JOIN U ON R.uid = U.uid WHERE R.rid = (:r2)';

  cursor = g.conn.execute(text(cmd), r2 = rid);

  review_dic = {'names_review':[],'review_review' : [], 'stars_review' : [], 'photos_review' : []}

  star_jpg = ['*', '**', '***', '****', '*****']



  for result in cursor:

    review_dic['names_review'].append(result['name'])

    review_dic['review_review'].append(result['review'])

    review_dic['stars_review'].append(star_jpg[int(result['stars']) - 1 ])

    review_dic['photos_review'].append(str(result['photos']))

  
  cmd = 'SELECT P.name, P.address, R.open, R.close FROM Restroom as R JOIN Places as P ON R.pid = P.pid WHERE R.rid = (:r3)'

  cursor = g.conn.execute(text(cmd), r3 = rid)

  location = {'name':null, 'address':null, 'open':null, 'close':null}

  for result in cursor:

    location['name'] = result['name']

    location['address'] = result['address']

    location['open'] = result['open']

    location['close'] = result['close']

  print(tips_dic)

  return render_template("restroom.html", loc = location, tips = tips_dic, len_tips = len(tips_dic['names_tips']),
  review = review_dic, len_review = len(review_dic['names_review']), rid = rid)





if __name__ == "__main__":

  app.secret_key = os.urandom(12)

  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using
        python server.py
    Show the help text using
        python server.py --help
    """

    HOST, PORT = host, port
    print ("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()