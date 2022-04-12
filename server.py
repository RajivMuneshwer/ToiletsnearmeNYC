import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response,flash, session, abort


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

DB_USER = "ram2277"
DB_PASSWORD = "6827"
DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"
DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"

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
  try:
    g.conn = engine.connect()
  except:
    print ("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def index():
  print (request.args)
  cursor = g.conn.execute("SELECT name FROM test")


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT name FROM U")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()
  context = dict(data = names)

  return render_template("index.html", **context)

@app.route('/another')
def another():
  return render_template("anotherfile.html")

@app.route('/user/<uid>')
def user(uid):
  query="SELECT * FROM U WHERE U.uid={}".format(uid)
  cursor = g.conn.execute(query)
  username=""
  is_verified=0
  non_verified=0
  startdate=""
  email=""
  for results in cursor:
    username=results['name']
    is_verified=results['verified']
    non_verified=results['non_verified']
    startdate=results['start_date']
    email=results['email_address']
  cursor.close()
  v="Non-Verified User"
  if is_verified==1:
    v="Verified User"
  if(username==""):
    return render_template("user.html",verified="User doesn't exist",date="Never")
  return render_template("user.html",Username=username,verified=v,date=startdate,email_address=email)

# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  print (name)
  cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
  g.conn.execute(text(cmd), name1 = name, name2 = name);
  return redirect('/')


@app.route('/home')
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
  else:
    flash('wrong password!')
  return redirect('/home')


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