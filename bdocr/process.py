from collections import OrderedDict
import json
import os
from datetime import datetime
from glob import glob
import fitz  # this is pymupdf
import os
from ocr import ocr
import re

def fill_in_fhir(data):
    p = OrderedDict({
        "resourceType" : "Patient",
        "id" : "",
        "text" : {
            "status" : "generated"
        },
        "identifier" : [{
            "use" : "usual",
            "type" : {
            "coding" : [{
                "system" : "http://terminology.hl7.org/CodeSystem/v2-0203",
                "code" : "MR"
            }]
            },
            "system" : "urn:oid:1.2.36.146.595.217.0.1",
            "value" : "1000",
            "period" : {
            "start" : "2001-05-06"
            },
            "assigner" : {
            "display" : "Acme Healthcare"
            }
        }],
        "active" : True,
        "name" : [{
            "use" : "official",
            "family" : "",
            "given" : [""]
        }],
        "telecom" : [{
            "use" : "home"
        },
        {
            "system" : "phone",
            "value" : "",
            "use" : "work",
            "rank" : 1
        }],
        "gender" : "",
        "birthDate" : "",
        "_birthDate" : {
            "extension" : [{
            "url" : "http://hl7.org/fhir/StructureDefinition/patient-birthTime",
            "valueDateTime" : ""
            }]
        },
        "deceasedBoolean" : False,
        "address" : [{
            "use" : "home",
            "type" : "both",
            "text" : "",
            "line" : [""],
            "city" : "",
            "district" : "",
            "state" : "",
            "postalCode" : "",
            "period" : {
            "start" : ""
            }
        }],
        "contact" : [{
            "relationship" : [{
            "coding" : [{
                "system" : "http://terminology.hl7.org/CodeSystem/v2-0131",
                "code" : "N"
            }]
            }],
            "name" : {
            "family" : "",
            "given" : [""]
            },
            "telecom" : [{
            "system" : "phone",
            "value" : ""
            }],
            "address" : {
            "use" : "home",
            "type" : "both",
            "line" : [""],
            "city" : "",
            "district" : "",
            "state" : "",
            "postalCode" : "",
            "period" : {
                "start" : ""
            }
            },
            "gender" : "",
            "period" : {
            "start" : ""
            }
        }],
        "managingOrganization" : {
            "reference" : ""
        }
        }
)
    # Extract info from data
    info = data['info']

    # Fill in the patient data
    p['id'] = info[0]['data'][1]['URN']
    p['name'][0]['family'] = info[0]['data'][1]['Family Name']
    p['name'][0]['given'] = info[0]['data'][1]['Given Names'].split()
    p['address'][0]['line'] = [info[0]['data'][1]['Address']]
    p['birthDate'] = info[0]['data'][1]['Date of Birth']
    p['gender'] = info[0]['data'][1]['Sex'].lower()

    return p


def pdf_to_images(pdf_path, output_folder):
    # Ensure output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Open the PDF file
    doc = fitz.open(pdf_path)

    for i in range(len(doc)):
        # Read each page of the PDF
        page = doc.load_page(i)

        # Render the page to a pixmap (an image)
        pix = page.get_pixmap()

        # Save the image to the output folder
        pix.save(os.path.join(output_folder, f'{os.path.basename(pdf_path)}_{i}.png'))


def process_images(patient_dir):
    patient_data = OrderedDict({
        'info': [
        {
            'path': '', 
            'data': [
                {'Date': '', 'Time': ''
                },
                {'URN': '', 'Family Name': '', 'Given Names': '', 'Address': '', 'Date of Birth': '', 'Sex':''
                },
                {'Admission date': '', 'Date referred to GRLS': '', 'SNAP date': '', 'Admitting Unit': '', 'Ward:': '', 'SNAP category': ''
                },
                {'INFECTIOUS PRECAUTIONS': ''
                },
                {'BEHAVIOUR ISSUES': '', 'HIGH VISUAL BAY': '', 'SIGNIFICANT PSYCHOSOCIAL ISSUES': ''
                },
                {'DIAGNOSIS': ''
                },
                {'PAST MEDICAL HISTORY': ''
                },
                {'SOCIAL SITUATION':''
                },
                {'HOME ENVIRONMENT': ''
                },
                {'PRE ADMISSION FUNCTIONAL STATUS': {'Mobility / TF / balance': '', 'Cognition': '', 'Self cares': '', 'Vision / Hearing': '',
                        "IADL's": '', 'Medications': '', 'Working': '', 'Continence': '', 'Driving': ''
                    }
                },
                {'CURRENT FUNCTIONAL STATUS (FIM)': {
                    'Motor': {'Eating': '', 'Grooming': '', 'Bathing': '', 'Dressing (upper body)': '', 'Dressing (lower body)': '', 'Toileting': ''}, 
                    'Cognition': {'Comprehension': '', 'Expression': '', 'Social interaction': '', 'Bowel management': '', 'Bladder management': '', 'Transfers - bed/chair/wchair': '', 'Transfers-tolet': '', 'Transfer. shower/bath': '', 'Mobilty': '', 'Stairs:': '', 'Motor FIM total score=': '', 'Problem solving': '', 'Memory': '', 'Cognition FIM total score': ''}
                    }
                },
                {'PICC/IVC': '', 'NaTPEG': '', '02': '', 'Wt-': '', 'Wound/PI': '', '0 & P': ''
                }
            ]
        },
        {
            'path': '', 
            'data': [
                {'Date': '', 'Time': ''
                },
                {
                    'URN': '', 'Family Name': '', 'Given Names': '', 'Address': '', 'Date of Birth': '', 'Sex': ''
                },
                {'Admission summary': ''
                },
                {'Potential multidisciplinary goals to be achieved during sub-acute admission': ''
                },
                {'Follow-up appointments required during sub-acute admission': ''
                },
                {'Outcome of GRLS Assessment': {'Details of assessment discussed with': '', 'MDT': '', 'Patient': '', 'Famiy': '', 'Further GRLS Consultant / Registrar and / or Coordinator review required': '', 'Patient to be referred for sub-acute care at': '', 'Referral closed-Reason': ''
                    }
                },
                {'Name': '', 'Signature': '', 'Contact number': '', 'Date': ''
                }
            ]
        }
        ], 
        'records': {}
    })
    for image_path in glob(os.path.join(patient_dir, 'png/*.png')):
        json_path = image_path.rsplit('.', 1)[0] + '.json'
        if not os.path.exists(json_path):
            ocr(image_path)
        with open(json_path,'r', encoding='utf-8') as f:
            data = json.load(f)
        footer = data['tables_result'][0]['footer']

        page_number = None
        if len(footer) != 0:
            matches = re.findall(r'Page\s*(\d+)\s*of\s*(\d+)', footer[0]['words'])
            if len(matches) != 0:
                page_number = int(matches[0][0])
        
        # Iterate over the tables_result
        for table in data['tables_result']:
            # Iterate over the body
            for cell in table['body']:
                # Iterate over the contents
                if 'NOTES' in cell['words'].upper():
                    page_number = None

        # Note Page
        if page_number is None:
            texts = ''
            start_to_add = False
            # Iterate over the tables_result
            for table in data['tables_result']:
                # Iterate over the body
                for cell in table['body']:
                    if start_to_add:
                        texts += cell['words'] + '\n'
                    if not start_to_add:
                        if 'TIME' in cell['words']:
                            start_to_add = True
            while '\n\n' in texts:
                texts = texts.replace('\n\n', '\n')
            # Iterate over the tables_result
            for table in data['tables_result']:
                # Iterate over the body
                for cell in table['body']:
                    # Iterate over the contents
                    for content in cell['contents']:
                        match = re.match(r'(\d{1,2}).(\d{1,2}).(\d{1,2})', content["word"])
                        if match:
                            day, month, year = map(int, match.groups())
                            try:
                                datetime(year, month, day)  # This will raise an exception if the date is not valid
                                date = f'{day}/{month}/{year}'
                                # print('Date:',date)
                                if date not in patient_data['records']:
                                    patient_data['records'][date] = []
                                patient_data['records'][date].append(['/'+image_path.replace('\\', '/'), texts])
                            except ValueError:
                                # print(f'{year}-{month}-{day} is not a valid date')
                                pass
        else:
            patient_data['info'][page_number-1]['path'] = '/'+image_path.replace('\\', '/')
            def process_block(parent_k, block):
                keys = list(block.keys())
                key_len = len(keys)
                rdata = {}
                for i, k in enumerate(keys):
                    v = block[k]
                    if type(v) == dict:
                        rdata[k]=process_block(k, v)
                    else:
                        next_k = keys[i + 1] if i + 1 < key_len else ''
                        # Iterate over the tables_result
                        value = ''
                        found_words = ''
                        for table in data['tables_result']:
                            # Iterate over the body
                            for cell in table['body']:
                                words = cell['words']
                                if words == '':
                                    continue
                                if k in words:
                                    found_words = words
                                    if k in [
                                        'SOCIAL SITUATION', 
                                        'HOME ENVIRONMENT', 
                                        'INFECTIOUS PRECAUTIONS',
                                        'Working',
                                        'Driving',
                                        'MDT',
                                        'Famiy',
                                        'Sex',
                                    ]:
                                        checked = []
                                        for i, content in enumerate(cell['contents']):
                                            if content['word'] == '√' and i+1 < len(cell['contents']):
                                                if cell['contents'][i+1]['word'] in ['Other:', 'No'] and i+2 < len(cell['contents']):
                                                    checked.append(cell['contents'][i+1]['word'] + cell['contents'][i+2]['word'])
                                                else:
                                                    checked.append(cell['contents'][i+1]['word'])
                                        value = ', '.join(checked)
                                    elif 'DATE' in k.upper():
                                        for content in cell['contents']:
                                            pattern = r"(\d{2})[\/|lI1](\d{2})[\/|lI1](\d{2})"

                                            matches = re.findall(pattern, content['word'])

                                            for match in matches:
                                                day, month, year = map(int, match)
                                                try:
                                                    datetime(year, month, day)  # This will raise an exception if the date is not valid
                                                    value = '/'.join(match)
                                                    print('Date:', value)
                                                    break
                                                except ValueError:
                                                    # print(f'{year}-{month}-{day} is not a valid date')
                                                    pass
                                        if value == '':
                                            matchs = re.findall(f'{re.escape(k)}(.*){re.escape(next_k)}', words, flags=re.DOTALL)
                                            if len(matchs) != 0:
                                                value = matchs[0]
                                            value = value.strip('\n').strip(':')
                                    elif k == 'Time':
                                        # 提取16\n00格式时间
                                        matchs = re.findall(f'{re.escape(k)}.*(\d\d).*(\d\d)', words, flags=re.DOTALL)
                                        if len(matchs) != 0:
                                            value = ':'.join(matchs[0])
                                    elif k in ['URN']:
                                        matchs = re.findall(f'{re.escape(k)}\D*(\d*)', words, flags=re.DOTALL)
                                        if len(matchs) != 0:
                                            value = matchs[0]
                                    elif k in ['Toileting']:
                                        matchs = re.findall(f'{re.escape(k)}(.*)Cognition', words, flags=re.DOTALL)
                                        if len(matchs) != 0:
                                            value = matchs[0]
                                    elif value == '':
                                        matchs = re.findall(f'{re.escape(k)}(.*){re.escape(next_k)}', words, flags=re.DOTALL)
                                        if len(matchs) != 0:
                                            value = matchs[0]
                                        elif k not in [
                                            'Name',
                                            'Date',
                                            'Address'
                                        ]:
                                            matchs = re.findall(f'{re.escape(k)}(.*)', words, flags=re.DOTALL)
                                            if len(matchs) != 0:
                                                value = matchs[0]
                                        value = value.strip('\n').strip(':')
                                        # if page_number==1 and value == '' and k not in [
                                        #     'SNAP category',
                                        #     'SIGNIFICANT PSYCHOSOCIAL ISSUES',
                                        # ]:
                                            # print('----------------------------------------------------------------\nKey:', k, '\nNext:', next_k)
                                            # print('Value:', value)
                                            # print('Found:', found_words)
                                            # exit()
                        rdata[k]=value.strip('\n').replace('\n',', ')
                return rdata
            for i in range(len(patient_data['info'][page_number-1]['data'])):
                block = patient_data['info'][page_number-1]['data'][i]
                patient_data['info'][page_number-1]['data'][i] = process_block(None,block)
    return patient_data


def process_patient(patient_dir):
    patient_json_path = os.path.join(patient_dir, 'data.json')
    # if os.path.exists(patient_json_path):
    #     return json.load(open(patient_json_path, 'r', encoding='utf-8'))
    pdfs = glob(os.path.join(patient_dir, 'pdf/*.pdf'))
    png_dir = os.path.join(patient_dir, 'png')
    if not os.path.exists(png_dir):
        os.mkdir(png_dir)
        for pdf in pdfs:
            print('processing:', pdf)
            pdf_to_images(pdf, png_dir)
    patient_data = process_images(patient_dir)
    fhir_data = fill_in_fhir(patient_data)
    with open(patient_json_path, 'w', encoding='utf-8') as f:
        json.dump(patient_data, f, ensure_ascii=False, indent=4)
    with open(patient_json_path.replace('.json','.fhir'), 'w', encoding='utf-8') as f:
        json.dump(fhir_data, f, ensure_ascii=False, indent=2)
    return patient_data

def process():
    for patient_dir in glob('data/*'):
        patient_json_path = os.path.join(patient_dir, 'data.json')
        # if not os.path.exists(patient_json_path):
        process_patient(patient_dir)

if __name__ == '__main__':
    process()