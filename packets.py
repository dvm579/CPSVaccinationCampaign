import os
import pandas as pd
import requests
from datetime import date
import time
from PyPDF4 import PdfFileMerger
from printnodeapi import Gateway
import base64

offered_vax = [
        'DtaP',
        'Hepatitis B',
        'Haemophilus influenzae type B',
        'Meningococcal Disease',
        'Measles, Mumps, Rubella',
        'Pneumococcal Conjugate',
        'Tdap',
        'Varicella',
        'Poliomyelitis',
        'Human Papilloma',
        'Influenza',
        'COVID-19'
    ]
key = {
        'DTAP': 'DtaP',
        'DTP': 'DtaP',
        'HBV': 'Hepatitis B',
        'HIB': 'Haemophilus influenzae type B',
        'MEN': 'Meningococcal Disease',
        'MMR': 'Measles, Mumps, Rubella',
        "Measles Mumps Rubella": 'Measles, Mumps, Rubella',
        'PNE': 'Pneumococcal Conjugate',
        'Td': 'Tdap',
        'VAR': 'Varicella',
        'POL': 'Poliomyelitis',
        "Polio": 'Poliomyelitis',
        'HPV': 'Human Papilloma',
        'FLU': 'Influenza',
        'Covid-19': 'COVID-19'
}


def download_file_from_google_drive(id, destination):
    def get_confirm_token(resp):
        for key, value in resp.cookies.items():
            if key.startswith('download_warning'):
                return value

        return None

    def save_response_content(resp, dest_filepath):
        CHUNK_SIZE = 32768

        with open(dest_filepath, "wb") as f:
            for chunk in resp.iter_content(CHUNK_SIZE):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)

    URL = "https://docs.google.com/uc?export=download"

    session = requests.Session()

    response = session.get(URL, params={'id': id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {'id': id, 'confirm': token }
        response = session.get(URL, params=params, stream=True)

    save_response_content(response, destination)


def packets(combined_history_df, schoolname: str, eventdate: list[date], eventtimestr: str,
            downloadpdfs=False, printpdfs=False):
    # Create folder for event
    event_dir = schoolname.replace(" ", "") + '_' + eventdate[0].strftime("%Y%m%d")
    if not os.path.exists(os.path.join(os.getcwd(), 'output', 'packets', event_dir)):
        os.mkdir(os.path.join(os.getcwd(), 'output', 'packets', event_dir))

    # Parse CSV shot history data, get list of unique patients
    # Create FullName column & try 'dob' as duplicate search key
    combined_history_df = combined_history_df.loc[combined_history_df['combined_status'] != 'compliant']
    combined_history_df['FullName'] = combined_history_df['FirstName'] + ' ' + combined_history_df['LastName']
    combined_history_df = combined_history_df.set_index(['unique_id'])

    # Start looping over patient list
    count = 0
    for patient in combined_history_df.index.unique():
        count += 1
        shot_history_df = combined_history_df.loc[patient]
        consent_list = []
        try:
            for shot in shot_history_df.iterrows():
                vx = shot[1]['vaccine']
                try:
                    vx = key[vx]
                except KeyError:
                    pass
                if vx not in consent_list and vx in offered_vax:
                    consent_list.append(vx)
            full_name = shot_history_df['FullName'].unique()[0]
            dob = pd.to_datetime(shot_history_df['DOB'].unique()[0])
        except AttributeError:
            vx = shot_history_df['vaccine']
            try:
                vx = key[vx]
            except KeyError:
                pass
            if vx not in consent_list and vx in offered_vax:
                consent_list.append(vx)
            full_name = shot_history_df['FullName']
            dob = pd.to_datetime(shot_history_df['DOB'])

        if len(consent_list) == 0:
            continue

        template_url = 'https://script.google.com/macros/s/AKfycbwAjtttGw8m6koZuemvyo1RfbGqtcRNPTHt7zB56bBCSRzxhX_fiO' \
                       'jhC4A4mAbrC1hUaQ/exec'

        template_params = {
            'studentname': full_name,
            'schoolname': schoolname,
            'eventdate': eventdate,
            'eventtime': eventtimestr,
            'shotlist': consent_list,
            'dob': dob,
            'print': printpdfs
        }
        packet_id = requests.get(template_url, params=template_params).text

        if downloadpdfs:
            packet_doc = os.path.join('output', 'packets', event_dir, f"{full_name.replace(' ', '')}_CPSPacket.pdf")
            try:
                download_file_from_google_drive(packet_id, packet_doc)
            except:
                time.sleep(2.0)
                download_file_from_google_drive(packet_id, packet_doc)
            print(str(count) + ". " + packet_doc + ' Generated.')

            if printpdfs:
                printnode = Gateway(apikey='_axRw1YfsMn7VJjm7no1PvO4sxXd-RQrFZG98cttpew')
                with open(packet_doc, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()
                encoded_string = base64.b64encode(pdf_bytes).decode('ascii')
                printjob = printnode.PrintJob(printer=71634461, title=packet_doc.split('/')[-1], base64=encoded_string)
                print(printjob.id)
        else:
            print(str(count) + ". " + full_name +
                  ' Packet Generated: https://drive.google.com/file/d/' + packet_id + "/view")

    return event_dir


# if __name__ == '__main__':
#     import time as t
#     start_time = t.time()
#     fldr = packets(combined_history_df=,
#                    schoolname='CICS Longwood',
#                    eventdate=[date(2023, 5, 16)],
#                    eventtimestr="10:00 AM - 1:00 PM",
#                    printpdfs=True)
#     print("--- %s seconds ---" % (t.time() - start_time))
