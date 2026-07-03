from flask import Flask, render_template, flash, request, redirect, session, url_for
from werkzeug.utils import secure_filename

import sqlite3 as sql
import os

from datetime import date
from datetime import datetime

import numpy as np
import tensorflow as tf
import cv2

app = Flask(__name__)
app.secret_key = "secret key"

loaded_model = tf.keras.models.load_model('model/model.h5', compile=False)

class_labels = ['cerebral', 'intracerebral', 'intracranial', 'no']

app.config['UPLOAD_FOLDER']="static/uploads"
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DATABASE = 'brainhemorrhage.db'

def get_db():
    conn = sql.connect(DATABASE)
    conn.row_factory = sql.Row
    return conn

def get_date():
    todaydate = date.today()    
    d1 = todaydate.strftime("%Y-%m-%d")    
    return d1

def get_time():
    currenttime = datetime.now()
    t1 = currenttime.strftime("%I:%M %p")  
    return t1

def model_predict(img_path):    
    test_img=cv2.imread(img_path)
    # Preprocess the image
    test_img= cv2.resize(test_img, (256, 256))
    test_input= test_img.reshape((1,256,256,3))
    pred= loaded_model.predict(test_input)
    prediction = np.argmax(pred, axis=1)
    return prediction

### Function Script End ###

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/actionlogin', methods=['GET', 'POST'])
def actionlogin():       
    if request.method == 'POST':  
        lid = request.form['lid']
        lpass = request.form['lpass']       
            
        conn = get_db()        
        cur=conn.cursor()
        cur.execute("select * from tbladmin where aemail=? and apass=?",(lid,lpass))
        data=cur.fetchone()            
        if data:                   
            session['adminloggedin'] = True   
            session["aid"]=data["aid"]
            session["aname"]=data["aname"]  
            session["aemail"]=data["aemail"]                
            return redirect(url_for('dashboard'))         
        else:
            flash('Incorrect E-Mail ID and Password','danger')
            return redirect(url_for("login"))   
                   
    return redirect(url_for("login"))

@app.route('/dashboard')
def dashboard():
    if 'adminloggedin' in session:
        admindata = {'aid':session['aid'],'aname':session['aname'],'aemail':session['aemail']} 
        return render_template('dashboard.html', **admindata)    
    return redirect(url_for("login"))

@app.route('/imagebaseanalysis')
def imagebaseanalysis():
    if 'adminloggedin' in session:
            admindata = {'aid':session['aid'],'aname':session['aname'],'aemail':session['aemail']} 
            return render_template('imagebaseanalysis.html', **admindata)       
    return redirect(url_for("login"))

@app.route('/actionemotion', methods=['GET', 'POST'])
def actionemotion():
    if 'adminloggedin' in session:
        if request.method == 'POST':
            sfile = request.files['file']

            filename = sfile.filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            sfile.save(save_path)

            # Make prediction
            preds = model_predict(save_path)
            print("preds value:",preds)

            for i in preds:
                pred1 = class_labels[i]
        
            result = pred1
            print("result value:",pred1)            

            admindata = {'aid':session['aid'],'aname':session['aname'],'aemail':session['aemail']} 
            return render_template('predictions.html', **admindata, results=result, save_paths=save_path)       
    return redirect(url_for("login"))


@app.route('/accuracy')
def accuracy():
    if 'adminloggedin' in session:
        admindata = {'aid':session['aid'],'aname':session['aname'],'aemail':session['aemail']} 
        return render_template('accuracy.html', **admindata)       
    return redirect(url_for("login"))    

@app.route('/logout')
def logout():   
   session.pop('adminloggedin', None)
   session.pop('aid', None)   
   session.pop('aname', None)  
   session.pop('eemail', None)  
   return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)
    