from flask import Flask, request, jsonify
import requests
import traceback
import sys

app = Flask(__name__)

# URLs
image_analysis_url = "http://image-analysis-service:8080/frame"
section_url = "http://section-service:8080/persons"
face_recognition_url = "http://face-recognition-service:8080/frame"
alert_url = "http://alert-service:8080/alerts"

@app.route('/frame', methods=['POST'])
def frame_collector():
    try:
        image_data = request.get_data()
        headers = {"Content-Type": "application/octet-stream"}

        # 1. Send the image to the image_analysis service
        image_analysis_response = requests.post(image_analysis_url, headers=headers, data=image_data)
        response_json = image_analysis_response.json()
        
        if is_response_correct(response_json):
            # print successfully processed the data
            print(f"[collector service]: INFO: Response from image analysis: {response_json}")
            # 2. Transform data for the section service and send it
            section_data = transform_to_section_format(response_json)
            post_to_section(section_data)
            
            # 3. Send the same data to the face recognition service
            try:
                face_recognition_data = {
                    "timestamp": response_json["timestamp"],
                    "image": response_json.get("image", ""),  # Assuming image_analysis service provides base64 image string
                    "section": response_json["section"],
                    "event": response_json["event"],
                    # "destination": and "extra-info": are optional
                }
                post_to_face_recognition(face_recognition_data)
            except Exception as e:
                print(f"[collector service]: ERROR while posting to face recognition service: {str(e)}")

            return jsonify({"status": "success", "message": "Data processed successfully!"}), 200
        else:
            return jsonify({"status": "failure", "message": "Incorrect response from image analysis."}), 400

    except Exception as e:
        print(f"[collector service]: ERROR: {str(e)}")
        traceback.print_exc()
        return jsonify({"status": "failure", "message": str(e)}), 500

def is_response_correct(response_json):
    required_keys = ["persons", "timestamp", "section", "event"]
    return all(key in response_json for key in required_keys)

def transform_to_section_format(data):
    section_data = {
        "timestamp": data["timestamp"],
        "section": data["section"],
        "event": data["event"],
        "persons": data["persons"]
    }
    if "image" in data:
        section_data["image"] = data["image"]
    if "extra-info" in data:
        section_data["extra-info"] = data["extra-info"]
    return section_data

def post_to_section(data):
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(section_url, headers=headers, json=data)
        print(f"[collector service]: INFO: Response from section service: {response.status_code}")
    except Exception as e:
        print(f"[collector service]: ERROR while posting to section service: {str(e)}")

def post_to_face_recognition(data):
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(face_recognition_url, headers=headers, json=data)
        print(f"[collector service]: INFO: Response from face recognition service: {response.status_code}")
        
        # If response code is 200, post to alert service
        if response.status_code == 200:
            response_json = response.json()
            alert_data = transform_to_alert_format(response_json)
            post_to_alert(alert_data)

    except Exception as e:
        print(f"[collector service]: ERROR while posting to face recognition service: {str(e)}")

def transform_to_alert_format(data):
    alert_data = {
        "timestamp": data["timestamp"],
        "section": data["section"],
        "event": data["event"],
        "known-persons": data.get("known-persons", [])
    }
    if "image" in data:
        alert_data["image"] = data["image"]
    if "extra-info" in data:
        alert_data["extra-info"] = data["extra-info"]
    return alert_data

def post_to_alert(data):
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(alert_url, headers=headers, json=data)
        print(f"[collector service]: INFO: Response from alert service: {response.status_code}")
    except Exception as e:
        print(f"[collector service]: ERROR while posting to alert service: {str(e)}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
