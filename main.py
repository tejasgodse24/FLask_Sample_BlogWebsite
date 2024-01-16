
from flask import Flask, render_template, request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import  datetime
import json
from flask_mail import Mail,Message
import os
from werkzeug.utils import secure_filename
import math



with open('config.json','r') as c :
    params = json.load(c)["params"]

app = Flask(__name__)

app.secret_key = 'super-secret-key'

#mail parameters
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = params['gmail-user']
app.config['MAIL_PASSWORD'] = params['gmail-password']
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False


mail = Mail(app)

app.config['UPLOAD_FOLDER'] = params['upload_location']



local_server = True

if(local_server) :
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
'''
this is beforer json file
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/instrument'
'''

db = SQLAlchemy(app)

class Contacts(db.Model):
    '''srno, name, email, phone, message , date'''
    srno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(20), unique=False, nullable=False)
    phone = db.Column(db.String(12), unique=False, nullable=False)
    message = db.Column(db.String(120), unique=False, nullable=False)
    date = db.Column(db.String(12), unique=False,nullable=True)


class Posts(db.Model):
    srno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=False, nullable=False)
    slug = db.Column(db.String(25), unique=False, nullable=False)
    content = db.Column(db.String(120), unique=False, nullable=False)
    tagline = db.Column(db.String(120), unique=False, nullable=False)
    date = db.Column(db.String(12), unique=False,nullable=True)
    img = db.Column(db.String(25), unique=False, nullable=True)

# this is before paginationa
#
# @app.route("/")
# def home():
#     posts = Posts.query.filter_by().all()[0:params['no_of_posts']]
#     return render_template("index.html",params=params,posts=posts)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts) / int(params['no_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page - 1) * int(params['no_of_posts']):(page - 1) * int(params['no_of_posts']) + int(params['no_of_posts'])]
    if page == 1:
        prev = "#"
        next = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)

@app.route("/about")
def about():
    return render_template("about.html",params=params)



@app.route("/dashboard" ,methods=['GET','POST'])
def dashboard():

    if ('user' in session and session['user'] == params['admin_username']) :
        posts = Posts.query.all()
        return render_template('dashboard.html',params=params,posts=posts)

    if request.method == "POST" :
        username = request.form.get("uname")
        userpass = request.form.get("pass")
        if(username == params['admin_username'] and userpass == params['admin_password']):
            #set the session variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html',params=params,posts = posts)


    return render_template("login.html", params=params)



@app.route("/edit/<string:srno>" ,methods=['GET','POST'])
def edit(srno):
    if ('user' in session and session['user'] == params['admin_username']) :
        if request.method == "POST" :
            box_title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            date = datetime.now()
            img = request.form.get('img')

            if srno == '0':
                post = Posts(title=box_title,slug=slug,content=content,tagline=tagline,date=date, img=img)

                db.session.add(post)
                db.session.commit()

            else:
                post = Posts.query.filter_by(srno = srno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tagline
                post.date = date
                post.img = img;
                db.session.commit()
                return redirect('/edit/'+srno)
        post = Posts.query.filter_by(srno=srno).first()
        return render_template("edit.html",params=params,post=post,srno=srno)


@app.route("/uploader",methods=['GET','POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_username']):
        if request.method == "POST" :
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename) ))
            return "Uploaded Successfull..."




@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route("/delete/<string:srno>" ,methods=['GET','POST'])
def Delete(srno) :
    if ('user' in session and session['user'] == params['admin_username']):
        post = Posts.query.filter_by(srno = srno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect("/dashboard")


@app.route("/contact",methods=['GET','POST'])
def contact():
    if(request.method == 'POST') :
        '''add entry to data base'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone_no = request.form.get('phone')
        msg = request.form.get('message')

        entry = Contacts(name=name,email=email,phone=phone_no,date=datetime.now(),message=msg)
        db.session.add(entry)
        db.session.commit()
        e_msg = Message("new message from " + name,
            sender = email,
            recipients = [params['gmail-user']],
            body = msg + "\n" + phone_no)
        mail.send(e_msg)
    return render_template('contact.html', params=params)



@app.route("/showpost")
def showpost():
    posts = Posts.query.filter_by().all()
    return render_template("showpost.html",params=params, posts=posts)


@app.route("/post/<string:post_slug>",methods = ['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug = post_slug).first()

    return render_template("post.html",params=params,post=post)



app.run(debug=True, port=4000)
