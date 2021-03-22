from flask import Flask
import jenkins
from flask_cors import CORS, cross_origin
import json
import math
# import polling
# from waitress import serve


app = Flask(__name__)
# CORS(app)
CORS(app, allow_headers=['Content-Type', 'Access-Control-Allow-Origin',
                         'Access-Control-Allow-Headers', 'Access-Control-Allow-Methods'])
endpoint = 'http://den01jpx.us.oracle.com:8080/';

server = jenkins.Jenkins(endpoint, username='ociui_user', password='ociui4@4')

@app.route('/', methods=['GET'])
def getJobTest():
    # polling.poll(
    #     lambda: requests.get('http://google.com').status_code == 200,
    #     step=60,
    #     poll_forever=True
    # )
    # file_handle = polling.poll(
    #     lambda: open('/myfile.txt'),
    #     ignore_exceptions=(IOError,),
    #     timeout=3,
    #     step=0.1)
    #
    return "home"


@app.route('/<job_name>/', methods=['GET'])
@cross_origin()
def getJobDetails(job_name):
    # --- add map of all the job names ---- #
    job_name_dict = {
        "Paid LCM Sanity": "SanityPaidADW_19c",
        "Paid Feature Sanity": "SanityPaid2ATP_19c",
        "Free Sanity": "SanityFreeATP_19c",
        "LCM Suite": "LCMOpeartionADW_19c",
        "Rename Suite": "RenameTestADW_19c",
        "ADG Suite": "ADGEnabledSanityADW_19c",
        "RC": "RefreshableCloneADW_19c",
        "Clone Suite": "CloneADW_19c",
        "Backup Suite": "CheckBackupAndRestoreSanityTest1",
        "AJD Suite": "SanityAJD_19c",
        "Rean Only Restricted Suite": "readOnlyTestATP_19c",
                     }
    job_detail_list = []

    info = server.get_job_info(job_name_dict[job_name])
    # Loop over builds
    builds = info['builds']
    print(builds)
    for build in builds:
        job_dict_row = {}
        job_dict_row['build_no'] = build['number']
        job_dict_row['build_url'] = build['url'] + '/testngreports/tests/'
        job_dict_row['report_url'] = build['url'].rsplit('/', 2)[0] + '/ws/ZippedReports/' + build['url'].rsplit('/', 3)[1] + str(build['number']) + 'Report.zip'
        build_info = server.get_build_info(job_name_dict[job_name], build['number'])
        job_dict_row['avg_time'] = 1
        # job_dict_row['avg_time'] = math.floor((build_info['duration']/(1000*60*60)) % 24)
        status = build_info['actions'][3]
        if 'failCount' not in status.keys():
            job_dict_row['dif'] = 0
            job_dict_row['skip'] = 0
            job_dict_row['suc'] = 0
            job_dict_row['test_count'] = 0
            job_dict_row['pct'] = 0
        else :
            job_dict_row['dif'] = status['failCount']
            job_dict_row['skip'] = status['skipCount']
            job_dict_row['suc'] = (status['totalCount'] - (status['failCount'] + status['skipCount']))
            job_dict_row['test_count'] = status['totalCount']
            suc_pct = int((int(job_dict_row['suc']) / int(job_dict_row['test_count']) * 100));
            job_dict_row['pct'] = 100 - suc_pct
            # job_dict_row['pct'] = int((int(job_dict_row['dif']) / int(job_dict_row['test_count'] - job_dict_row['skip'])) * 100);
        job_detail_list.append(job_dict_row)
    json_object = json.dumps(job_detail_list)
    print(json_object)
    return json_object

if __name__ == '__main__':
    # app.run()
    app.run(host='127.0.0.1', port=5000, debug=True)
    # app.run(host='0.0.0.0', port=5000, debug=True)
    # app.run(host="0.0.0.0", port="33", debug=True)

