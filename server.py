import os
import csv 
import glob
import numpy as np
import sqlite3 as sql
from time import strftime
from skimage import feature, color
from skimage.data import imread
from scipy import misc, fftpack
from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
    url_for,
    redirect)


# query
INSERT = "INSERT INTO drats_data(filename, min, max, std, mean, blob_count, time) values (?, ?, ?, ?, ?, ?, ?)"

# server config 

DEV_MACHINE = 'X86_64'
PROD_MACHINE = 'armv7l'
PROD_MODE = False
DEBUG = True
UPLOAD_FOLDER = "static/"
DRATS_DB = "drats.db"

if os.uname()[-1] == PROD_MACHINE:
    from PIL import Image
    from picamera import PiCamera
    camera = PiCamera()
    PROD_MODE = True
    DEBUG = False

# scikit image reader
reader = misc.imread

# flask object
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db = sql.connect(DRATS_DB, check_same_thread=False)
cur = db.cursor()

def img2frq(image):
  img = imread(image, as_grey=True)
  fft = fftpack.fft2(img)
  fft_data = fft.argmax(axis=1).tolist()
  return fft_data


def blob_counter(img, min_sigma=2, max_sigma=8, treshold=0.0001, overlap=0.6):
   img = imread(img, as_grey=True)
   bw = img.mean(axis=2)
   blobs_dog = [(x[0],x[1],x[2]) for x in feature.blob_dog(-bw, min_sigma=2, max_sigma=8, threshold=0.0001, overlap=0.6)]
   blobs_dog = set(blobs_dog)
   return str(len(blobs_dog))


def count_blob(img):
   img = reader(img)
   bw = img.mean(axis=2)
   blobs_dog = [(x[0], x[1], x[2]) for x in feature.blob_dog(-bw, min_sigma=2, max_sigma=8, threshold=0.0001, overlap=0.6)]
   blobs_dog = set(blobs_dog)
   return str(len(blobs_dog))


def generate_filename():
    timestamps = strftime("%m%d%Y-%H%M%S") + '.jpg'
    return timestamps

def timestamps():
    timestamps = strftime("%m%d%Y-%H%M%S")
    return timestamps



# drats router 
@app.route("/", methods=["GET", "POST"])
def capture_image():

    # PRODUCTION ENVIRONMENT
    if PROD_MODE == True:
        if request.method == "POST":
            filename = generate_filename()
            camera.resolution = (500, 500)
            filepath = "static/"+filename
            camera.capture(filepath)
            num_blob = count_blob(filepath)
            fft_data = img2frq(filepath)
            time = timestamps()
            minx, maxx, std, mean = float(min(fft_data)), float(max(fft_data)), float(np.std(fft_data)), float(np.mean(fft_data))
            #minx, maxx, std, mean = float(fft_data.min()), float(fft_data.max()), float(fft_data.std()), float(fft_data.mean())
            data = [filename, minx, maxx, std, mean, num_blob, time]
            cur.execute(INSERT, data)
            db.commit()
            return render_template('drats.html', filename=image.filename, num_blob=num_blob, 
                                    fft_data=fft_data, minx=minx, maxx=maxx, std=std, mean=mean)
        return render_template("drats.html")


    # DEVELOPMENT ENVIRONMENT
    if PROD_MODE == False:
        if request.method == "POST":
            image = request.files['file']
            if image:
               image.save(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
               filepath = "static/"+image.filename
               num_blob = count_blob(filepath)
               fft_data = img2frq(filepath)
               time = timestamps()
               minx, maxx, std, mean = float(min(fft_data)), float(max(fft_data)), float(np.std(fft_data)), float(np.mean(fft_data))
               #minx, maxx, std, mean = np.min(fft_data), np.max(fft_data), np.std(fft_data), np.mean(fft_data)
               data = [image.filename, minx, maxx, std, mean, num_blob, time]
               cur.execute(INSERT, data)
               db.commit()
               return render_template('dev.html', filename=image.filename, num_blob=num_blob, 
					fft_data=fft_data, minx=minx, maxx=maxx, std=std, mean=mean)
        return render_template("dev.html")


@app.route('/show')
def plot():
   files = cur.execute('SELECT * FROM drats_data')
   return render_template("show.html", files=files)


@app.route('/images')
def show_images():
   images = glob.glob('static/*.png')
   return render_template('images.html', images=images)


@app.route('/csv-file')
def show_csvs():
   files = glob.glob('static/*.csv')
   return render_template('csv.html', files=files)
   

@app.route('/csv', methods=['POST'])
def generate_csv():

   if request.method == "POST":
      cur_time = timestamps()
      filepath = 'static/'+cur_time+'.csv'
      with open(filepath, 'a+') as f:
         writer = csv.writer(f)
         writer.writerow(('id_data', 'filename', 'min', 'max', 'std', 'mean', 'blob_count', 'time'))
         data = cur.execute('SELECT * FROM drats_data')
         for item in data:
             writer.writerow(item)      
      return redirect(url_for('show_csvs'))
   


if __name__ == '__main__':
    app.run('0.0.0.0', port=8000, debug=DEBUG)

