from flask import Blueprint, Flask, render_template, request, flash, jsonify, url_for, send_file
from flask_login import login_required, current_user
from . import db
import json
import numpy as np
from keras.models import load_model
import cv2
from numpy import asarray
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from sqlalchemy.sql import func
from keras.preprocessing import image as keras_image
from werkzeug.utils import secure_filename
import tensorflow as tf

views = Blueprint('views', __name__)

all_labels = ['Atelectasis', 'Cardiomegaly', 'Consolidation', 'Edema', 'Effusion', 'Emphysema', 'Fibrosis',
              'Hernia', 'Infiltration', 'Mass', 'Nodule', 'Pleural_Thickening', 'Pneumonia', 'Pneumothorax']

from tensorflow.keras.preprocessing.image import ImageDataGenerator
IMG_SIZE = (128, 128)
core_idg = ImageDataGenerator(samplewise_center=True,
                              samplewise_std_normalization=True,
                              horizontal_flip = True,
                              vertical_flip = False,
                              height_shift_range= 0.05,
                              width_shift_range=0.1,
                              rotation_range=5,
                              shear_range = 0.1,
                              fill_mode = 'reflect',
                              zoom_range=0.15)

def preprocess_image(img):
    # Convert image to array
    img_array = keras_image.img_to_array(img)
    # Expand dimensions to fit the model input shape
    img_array_expanded_dims = np.expand_dims(img_array, axis=0)
    # Use the same ImageDataGenerator for preprocessing
    img_preprocessed = core_idg.standardize(img_array_expanded_dims)
    return img_preprocessed

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST': 
        pass
    return render_template("home.html", user=current_user)

from .models import Patient, Appointment, Image, Finding

@views.route('/delete-patient', methods=['POST'])
def delete_patient():
    patient = json.loads(request.data)
    patientId = patient['patientId']
    patient = Patient.query.get(patientId)
    if patient:
        db.session.delete(patient)
        db.session.commit()
    return jsonify({})

import PIL
from PIL import Image as PilImage
import io

@views.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        model = tf.keras.models.load_model('./models/modelx2.h5')
        uploaded_file = request.files['image']
        finding_label = ''

        if uploaded_file and uploaded_file.filename != '':
            image = PilImage.open(io.BytesIO(uploaded_file.read()))
            gray = image.convert('L')
            img = gray.resize(IMG_SIZE, PIL.Image.Resampling.LANCZOS)
            numpydata = np.array(img)
            input_image = preprocess_image(numpydata)
            
            prediction = model.predict(input_image)
            disease_probabilities = prediction[0]

            result_text = 'Diseases detected:'
            for disease, probability in zip(all_labels, disease_probabilities):
                if probability >= 0.3:  # Only include diseases with probability >= 30%
                    finding_label += disease + ', '
                    result_text += f'{disease}: {probability*100:.2f}% '

            finding_label = finding_label[:-2]  # Remove the last comma and space

            image_path = f"./website/static/assets/images/{uploaded_file.filename}"  # Use the uploaded file's filename

            if os.path.exists(image_path):
                print("Image already exists")
            else:
                print("Adding image to folder")
                image.save(image_path)
                print("Image saved")

                
            # Get details from form
            gender = request.form.get('gender')
            follow_up_number = int(request.form.get('follow_up_number'))
            group = request.form.get('group')
            age = request.form.get('age')
            view_position = request.form.get('view_position')
            original_image_width_height = request.form.get('original_image_width_height')
            original_image_pixel_spacing = request.form.get('original_image_pixel_spacing')

            # Check if follow_up_number is greater than 0
            if follow_up_number > 0:
                # If it is, get the existing patient
                patient_id = request.form.get('patient_id')
                patient = Patient.query.filter_by(gender=gender).first()
                if patient:
                    patient = Patient.query.get(patient_id)
                    appointment = Appointment(patient_id=patient.id,
                                              follow_up_number=follow_up_number,
                                              group=group)
                else:
                    # If patient does not exist, create a new patient
                    patient = Patient(gender=gender)
                    db.session.add(patient)
                    db.session.commit()
            else:
                # If follow_up_number is not greater than 0, create a new patient
                patient = Patient(gender=gender)
                db.session.add(patient)
                db.session.commit()

            # Create new appointment
            appointment = Appointment(patient_id=patient.id,
                                        follow_up_number=follow_up_number,
                                        group=group)
            db.session.add(appointment)
            db.session.commit()

            # Create new image
            image = Image(appointment_id=appointment.id,
                            image_index=uploaded_file.filename,
                            patient_age=age,
                            view_position=view_position,
                            original_image_width_height=original_image_width_height,
                            original_image_pixel_spacing=original_image_pixel_spacing)
            db.session.add(image)
            db.session.commit()

            # Create new finding
            finding = Finding(image_id=image.id,
                                finding_label=finding_label)
            db.session.add(finding)
            db.session.commit()
            
            myfile = uploaded_file.filename
            
            return render_template('predict.html', prediction_texts=[result_text], user=current_user, myfile=myfile)
        else:
            return render_template('predict.html', prediction_texts=['No files selected'], user=current_user)
    return render_template('predict.html', user=current_user)


@views.route('/predictions', methods=['GET','POST'])
@login_required
def predictions():
    if request.method == 'POST':
        model = tf.keras.models.load_model('./models/modelx2.h5')
        #model.load_weights('./models/xray_class_best_.weights.h5')
        uploaded_files = request.files.getlist('image')
        
        if uploaded_files:
            results = []
            fig, m_axs = plt.subplots(len(uploaded_files), 1, figsize = (32, len(uploaded_files)*24))
            
            for uploaded_file, c_ax in zip(uploaded_files, m_axs.flatten()):
                if uploaded_file.filename != '':
                    image = PilImage.open(io.BytesIO(uploaded_file.read()))
                    gray = image.convert('L')
                    img = gray.resize(IMG_SIZE, PIL.Image.Resampling.LANCZOS)
                    numpydata = np.array(img)
                    input_image = preprocess_image(numpydata)
                                
                    prediction = model.predict(input_image, verbose=0)
                    disease_probabilities = prediction[0]
                                
                    result_text = 'Diseases detected: '
                    booleanVal = False
                    for disease, probability in zip(all_labels, disease_probabilities):
                        if probability >= 0.3:  # Only include diseases with probability >= 30%
                            result_text += f'{disease}: {probability*100:.2f}% '
                            booleanVal = True

                    if not booleanVal:
                        result_text = 'No Findings'
                        
                    c_ax.imshow(img, cmap='bone')
                    pred_str = ['%s:%2.0f%%' % (disease[:4], probability*100) for disease, probability in zip(all_labels, disease_probabilities) if probability >= 0.3]
                    
                    if not pred_str:
                        pred_str = ['No Findings']

                    c_ax.set_title('PDx: '+', '.join(pred_str), color='blue', fontsize=100)
                    c_ax.axis('off')

                    print(result_text)
                    print(model.predict(input_image))
                    results.append(result_text)

            fig.savefig('website/static/assets/uploaded_images/predictions.png')
            print(results)
            print(disease_probabilities)
            
            return render_template('home.html', prediction_texts=results, user=current_user)
        else:
            return render_template('home.html', prediction_texts=['No files selected'], user=current_user)
    return render_template('home.html', user=current_user)
        


@views.route('/patients', methods=['GET', 'POST'])
@login_required
def patients():
    num_patients = db.session.query(func.count(Patient.id)).scalar()
    page = request.args.get('page', 1, type=int)
    patients = Patient.query.paginate(page=page, per_page=25)
    print(patients.items)
    return render_template('patients.html', user=current_user, patients=patients, num_patients=num_patients)

@views.route('/patients/<int:patient_id>')
@login_required
def patient_detail(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    print(f"Number of appointments: {len(patient.appointments.all())}")
    for appointment in patient.appointments:
        print(f"Number of images in appointment {appointment.id}: {len(appointment.images.all())}") 
    return render_template('patient_detail.html', patient=patient, user=current_user)

@views.route('/get_patient/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    patient = Patient.query.get(patient_id)
    if patient:
        return jsonify(patient.serialize())
    else:
        return jsonify({})
    
@views.route('/search_patients', methods=['GET'])
def search_patients():
    query = request.args.get('query')
    patients = Patient.query.filter(Patient.id.contains(query)).all()
    return jsonify([patient.serialize() for patient in patients])

