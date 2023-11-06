import datetime
import shutil
from flask import Flask, jsonify, render_template, send_from_directory, request, Response
from werkzeug.wsgi import FileWrapper
import os
import mimetypes
import json
import os
from glob import glob
import signal
from process import process, process_patient

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Global variable to store the data
data_dict = {}

# Load data at startup
def load_data():
    global data_dict
    for patient_folder in glob('data/*'):
        file = f'{patient_folder}/data.json'
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Store the file modification time along with the data
            data_dict[os.path.basename(patient_folder)] = {
                "data": data,
                "mod_time": datetime.datetime.fromtimestamp(os.path.getmtime(file)).strftime('%Y-%m-%d %H:%M:%S')
            }
          
# Update data when it changes
def update_data(patient_folder):
    global data_dict
    file = f'data/{patient_folder}/data.json'
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Store the file modification time along with the data
        data_dict[os.path.basename(patient_folder)] = {
            "data": data,
            "mod_time": datetime.datetime.fromtimestamp(os.path.getmtime(file)).strftime('%Y-%m-%d %H:%M:%S')
        }

@app.context_processor
def inject_enumerate():
    return dict(enumerate=enumerate, str=str)

@app.route('/')
def index():
    if not data_dict.values():
        load_data()
    return render_template('index.html')

@app.route('/scan')
def scab():
    return render_template('scan.html')

@app.route('/ocr', methods=['GET', 'POST'])
def ocr():
    tmp_dir_name = os.path.join(app.config['UPLOAD_FOLDER'], 'tmp')
    if request.method == 'POST':
        try:
            files = request.files.getlist('file[]')
            if os.path.exists(tmp_dir_name):
                shutil.rmtree(tmp_dir_name)
            pdf_dir = os.path.join(tmp_dir_name,'pdf')
            os.makedirs(pdf_dir)
            for file in files:
                filename = file.filename
                file.save(os.path.join(pdf_dir, filename))
            process_patient(tmp_dir_name)
        except Exception as e:
            print(e)
            return jsonify({'status': 'error', 'message': str(e)})
        return jsonify({'status': 'success'})
    if os.path.exists(os.path.join(tmp_dir_name,'data.json')):
        patient_data = json.load(open(os.path.join(tmp_dir_name,'data.json'), 'r', encoding='utf-8'))
        return render_template('ocr.html', data=patient_data)
    return render_template('ocr.html')

@app.route('/ocr_save', methods=['POST'])
def ocr_save():
    data = request.get_json()
    name = data.get('name')
    if name is not None and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 'tmp')):
        with open(os.path.join(app.config['UPLOAD_FOLDER'], 'tmp', 'data.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
        with open(os.path.join(app.config['UPLOAD_FOLDER'], 'tmp', 'data.json'), 'w', encoding='utf-8') as f:
            for i in range(len(data['info'])):
                data['info'][i]['path'] = os.path.join('/data',name,'png',os.path.basename(data['info'][i]['path']))
            for k in data['records']:
                v = data['records'][k]
                for i in range(len(v)):
                    data['records'][k][i][0] = os.path.join('/data',name,'png',os.path.basename(data['records'][k][i][0]))
            json.dump(data, f, ensure_ascii=False, indent=4)
        shutil.move(os.path.join(app.config['UPLOAD_FOLDER'], 'tmp'), os.path.join('data', name))
        update_data(name)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'})

@app.route('/ocr_cancel', methods=['POST'])
def ocr_cancel():
    if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 'tmp')):
        shutil.rmtree(os.path.join(app.config['UPLOAD_FOLDER'], 'tmp'))
    return jsonify({'status': 'success'})

@app.route('/ocr_delete', methods=['POST'])
def ocr_delete():
    data = request.get_json()
    name = data.get('name')
    if name and os.path.exists(os.path.join('data', name)):
        shutil.rmtree(os.path.join('data', name))
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'})

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/download/<string:patient_name>')
def download(patient_name):
    file_path = os.path.join('data', patient_name, 'data.fhir')
    wrapper = FileWrapper(open(file_path, 'rb'))
    response = Response(wrapper, direct_passthrough=True)
    response.headers['Content-Type'] = mimetypes.guess_type(file_path)[0]
    response.headers['Content-Disposition'] = 'attachment; filename='+patient_name + '.fhir'
    return response

@app.route('/search', methods=['POST'])
def search():
    results = []
    query = request.get_json()['query']
    if query:  # If the query is not empty
        for patient, patient_data in data_dict.items():
            for date, pages in patient_data["data"]['records'].items():
                for i, page in enumerate(pages):
                    if query in page[1]:
                        highlighted_text = page[1].replace(query, f'<mark>{query}</mark>')
                        results.append({
                            "patient": patient,
                            "record_date": date,
                            "page": i + 1,
                            "file_mod_date": patient_data["mod_time"],
                            "text": highlighted_text,
                        })
    else:  # If the query is empty
        for patient, patient_data in data_dict.items():
            results.append({
                "patient": patient,
                "record_date": None,
                "page": None,
                "file_mod_date": patient_data["mod_time"],
                "text": None,
            })
    results.sort(key=lambda x: (x['file_mod_date']), reverse=True)
    return jsonify(results)

@app.route('/patient/<string:patient_name>', methods=['GET', 'POST'])
def patient(patient_name):
    data = json.load(open('data/' + patient_name + '/data.json', 'r', encoding='utf-8'))
    return render_template('patient.html', data=data)

@app.route('/<path:filename>')
def send_image(filename):
    return send_from_directory('', filename)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    print("Shutting down gracefully...")
    os.kill(os.getpid(), signal.SIGINT)
    return 'Server shutting down...'

if __name__ == '__main__':
    load_data()
    app.run(debug=True)