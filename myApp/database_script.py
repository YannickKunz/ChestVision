from website import db, create_app
from website.models import Patient, Appointment, Image, Finding
import json

app = create_app()
x = 0
with app.app_context():
    with open('./Documentation/patient_data.json') as f:
        data = json.load(f)
    # Assuming data is your JSON data
    for patient in data["Patients"]:
        new_patient = Patient(id=patient["PatientID"],
                              gender=patient["PatientGender"])
        db.session.add(new_patient)
        db.session.commit()

        #print(patient["PatientID"])
        #print(patient["PatientGender"])
        
        for appointment in patient["Appointments"]:
            for follow_up, image in appointment.items():
                # Include the 'group' attribute when creating a new Appointment
                new_appointment = Appointment(patient_id=new_patient.id, 
                                              follow_up_number=int(follow_up.split('#')[-1]),
                                              group=image[0]["Group"])  # Assuming all images in an appointment have the same group
                db.session.add(new_appointment)
                db.session.commit()

                #print("Appointment id")
                #print(new_appointment.id)
                #print(follow_up)
                #print(image[0]["Group"])

                new_image = Image(appointment_id=new_appointment.id,
                                    image_index=image[0]["ImageIndex"],
                                    patient_age=image[0]["PatientAge"],
                                    view_position=image[0]["ViewPosition"],
                                    original_image_width_height=image[0]["OriginalImageWidthHeight"],
                                    original_image_pixel_spacing=image[0]["OriginalImagePixelSpacing[x-y]"])
                db.session.add(new_image)
                db.session.commit()

                #print("Image id")
                #print(new_image.id)
                #print(image[0]["ImageIndex"])
                #print(image[0]["PatientAge"])
                #print(image[0]["ViewPosition"])
                #print(image[0]["OriginalImageWidthHeight"])
                #print(image[0]["OriginalImagePixelSpacing[x-y]"])

                for finding_label in image[0]["FindingLabels"]:
                    new_finding = Finding(image_id=new_image.id,
                                          finding_label=finding_label)
                    db.session.add(new_finding)
                    db.session.commit()

                    #print(finding_label)

        # Commit the changes for each patient
        print(f"Patient {x} has been added to the database.")
        x += 1
        db.session.commit()

print('Done!')
