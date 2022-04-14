import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response,flash, session, abort
from datetime import date, datetime
from werkzeug.utils import secure_filename

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

DB_USER = "ram2277"
DB_PASSWORD = "6827"
DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"
DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"

engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print ("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    raise

@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
  except Exception as e:
    pass

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

  if( username == None ):

    return render_template("user.html",verified="User doesn't exist",date="Never")
  query="SELECT * FROM Visit WHERE Visit.uid={} ORDER BY time".format(uid)
  cursor=g.conn.execute(query)
  visits=[]
  for result in cursor:
    visits.append(result)
  cursor.close()
  query="SELECT * FROM Tips WHERE Tips.uid={}".format(uid)
  cursor=g.conn.execute(query)
  tips=[]
  for result in cursor:
    tips.append(result)
  cursor.close()
  query="SELECT * FROM Review WHERE Review.uid={} ORDER BY time".format(uid)
  cursor=g.conn.execute(query)
  reviews=[]
  for result in cursor:
    reviews.append(result)
  cursor.close()
  return render_template("user.html",Username=username,verified=v,date=startdate,email_address=email,visitsrecord=visits,tiprecord=tips,reviewrecord=reviews)

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

  cmd = 'SELECT uid, password  FROM U WHERE name = (:n1)';

  cursor = g.conn.execute(text(cmd), n1 = username_prime);

  password = []

  uid = []

  for result in cursor:

    uid.append(result['uid'])  # can also be accessed using result[0]

    password.append(result['password'])

  cursor.close()

  if password_prime == str(password[0]) :

    session['logged_in'] = True

    session['uid'] = uid[0]

  else:
    flash('wrong password!')

  return redirect('/')



@app.route('/restroom/<rid>/create_tips')
def create_tips(rid, methods = ['GET','POST']):

  return render_template("tips.html", rid =rid)

@app.route('/restroom/<rid>/create_review')
def create_review(rid, methods = ['GET', 'POST']):
  return render_template("review.html", rid =rid)


@app.route('/add_tips/<rid>',  methods=['POST'])
def add_tips(rid):

  label = request.form['label_box']

  desc = request.form['tips_desc'] 

  uid = session['uid']

  cmd = 'INSERT INTO Tips VALUES (:u, :r, DEFAULT, :l, :d)';

  g.conn.execute(text(cmd), u = uid, r = rid, l = label, d = desc);

  return redirect('/restroom/'+rid)

@app.route('/add_review/<rid>', methods=  ['POST'])
def add_review(rid):

  stars = request.form['rating']

  desc = request.form['review_desc']

  uid = session['uid']

  x = datetime.now()

  time = x.strftime("%x")

  uploaded_file = request.files['file']

  print(uploaded_file)
  
  if uploaded_file.filename != '':

        filename = secure_filename(uploaded_file.filename)
        
        uploaded_file.save(os.path.join('static/images', filename))
        
        cmd = 'INSERT INTO  Review VALUES (:r, :u, :d, :s, :p, :t)';
        
        g.conn.execute(text(cmd), u = uid, r = rid, d = desc, s = stars, t = time, p = filename);
  else:
    
    cmd = 'INSERT INTO  Review VALUES (:r, :u, :d, :s, NULL, :t)';
    
    g.conn.execute(text(cmd), u = uid, r = rid, d = desc, s = stars, t = time);
  return redirect('/restroom/'+rid )









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
