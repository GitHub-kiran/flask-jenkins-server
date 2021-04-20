from flask import Flask
import jenkins
from flask_cors import CORS, cross_origin
import json
from os import path
import pymongo
import time
import polling
import re
import math

app = Flask(__name__)
CORS(app, allow_headers=['Content-Type', 'Access-Control-Allow-Origin',
                         'Access-Control-Allow-Headers', 'Access-Control-Allow-Methods'])
endpoint = 'http://den01jpx.us.oracle.com:8080/';

server = jenkins.Jenkins(endpoint, username='ociui_user', password='ociui4@4')
# client = pymongo.MongoClient("localhost", 27017)
# db = client["jenkinsStoreDB"]

@app.route('/')
@cross_origin()
def welcome():
    return "welcome to jenkins mockup"


# @app.route('/save_jobname/')
# @cross_origin()
def save_job_name_list():
    jobs = server.get_jobs()
    # master_jobs = [{'sanity': []}, {'feature': []}, {'all': [{'job_name': 'All Suite', 'job_val': 'All Suite'}]}]
    master_jobs = [{'sanity': []}, {'feature': []}, {'all': []}]
    for i in range(len(jobs)):
        master_job = {}
        job_name = jobs[i]['name']
        last_build_number = server.get_job_info(job_name)['lastCompletedBuild']['number']
        build_info = server.get_build_info(job_name, last_build_number)
        git_branch_name = build_info['actions'][1]['lastBuiltRevision']['branch'][0]['name']
        if 'master' in git_branch_name:
            name = job_name.split('_')
            if len(name) >= 2:
                master_job['job_name'] = ' '.join(name)
                master_job['job_val'] = job_name
        if master_job:
            # if 'sanity' in job_name or 'Sanity' in job_name:
            if job_name.startswith('sanity') or job_name.startswith('Sanity'):
                master_jobs[0]['sanity'].append(master_job)
            else:
                master_jobs[1]['feature'].append(master_job)
    print(master_jobs)
    myfile = "job_name.json"

    with open(myfile, 'w') as outfile:
        json.dump(master_jobs, outfile)

    return "All job names are stored in DB"

@app.route('/sanity/', methods=['GET'])
@cross_origin()
def get_sanity_job_list():
    myfile = "job_name.json"
    if path.exists(myfile):
        with open(myfile) as f:
            job_name_map = json.load(f)
    else:
        save_job_name_list()
        with open(myfile) as f:
            job_name_map = json.load(f)

    print(job_name_map[0]['sanity'])
    return job_name_map[0]

    # job_name_col = db["job_name_list"]
    # return job_name_col.find_one()['master_jobs'][0]


@app.route('/feature/', methods=['GET'])
@cross_origin()
def get_feature_job_list():
    myfile = "job_name.json"
    if path.exists(myfile):
        with open(myfile) as f:
            job_name_map = json.load(f)
    else:
        save_job_name_list()
        with open(myfile) as f:
            job_name_map = json.load(f)

    return job_name_map[1]

    # job_name_col = db["job_name_list"]
    # return job_name_col.find_one()['master_jobs'][1]


@app.route('/all/', methods=['GET'])
@cross_origin()
def get_job_name_list():
    myfile = "job_name.json"
    if path.exists(myfile):
        with open(myfile) as f:
            job_name_map = json.load(f)
    else:
        save_job_name_list()
        with open(myfile) as f:
            job_name_map = json.load(f)

    return job_name_map[2]

    # job_name_col = db["job_name_list"]
    # return job_name_col.find_one()['master_jobs'][2]

@app.route('/<job_name>/', methods=['GET'])
@cross_origin()
def get_job_details(job_name="RC"):
    # --- add map of all the job names ---- #
    # job_name_dict = {
    #     "Paid Sanity1": "SanityPaidADW_19c",
    #     "Paid Sanity2": "SanityPaid2ATP_19c",
    #     "Free Sanity": "SanityFreeATP_19c",
    #     "LCM": "LCMOpeartionADW_19c",
    #     "Rename": "RenameTestADW_19c",
    #     "ADG": "ADGEnabledSanityADW_19c",
    #     "RC": "RefreshableCloneADW_19c",
    #     "Clone": "CloneADW_19c",
    #     "Backup": "CheckBackupAndRestoreSanityTest1",
    #     "AJD": "SanityAJD_19c",
    #     "Rean Only": "readOnlyTestATP_19c",
    #                  }
    job_detail_list = []

    # info = server.get_job_info(job_name_dict[job_name])
    info = server.get_job_info(job_name)
    # Loop over builds
    builds = info['builds']
    print(builds)
    time_flag = False
    for build in builds:
        job_dict_row = {}
        job_dict_row['build_no'] = build['number']
        print('build url is..............', build['url']);
        job_dict_row['build_url'] = build['url'] + 'testngreports/tests/'
        job_dict_row['report_url'] = build['url'].rsplit('/', 2)[0] + '/ws/ZippedReports/' + \
        build['url'].rsplit('/', 3)[1] + str(build['number']) + 'Report.zip'
        build_info = server.get_build_info(job_name, build['number'])
        # job_dict_row['avg_time'] = 1
        job_dict_row['avg_time'] = (build_info['duration'] / (1000 * 60 * 60)) % 24
        status = build_info['actions'][3]
        if 'failCount' not in status.keys():
            job_dict_row['dif'] = 0
            job_dict_row['skip'] = 0
            job_dict_row['suc'] = 0
            job_dict_row['test_count'] = 0
            job_dict_row['pct'] = 0
        else:
            job_dict_row['dif'] = status['failCount']
            job_dict_row['skip'] = status['skipCount']
            job_dict_row['suc'] = (status['totalCount'] - (status['failCount'] + status['skipCount']))
            job_dict_row['test_count'] = status['totalCount']
            suc_pct = int((int(job_dict_row['suc']) / int(job_dict_row['test_count']) * 100));
            job_dict_row['pct'] = 100 - suc_pct

        # ----------- TODO : need to update avg_time logic
        # if not time_flag and job_dict_row['test_count'] and ((job_dict_row['test_count'] == job_dict_row['suc']) or (
        #         job_dict_row['skip'] <= 3 and (
        #         job_dict_row['skip'] + job_dict_row['dif'] + job_dict_row['suc'] == job_dict_row['test_count']))):
        #     job_dict_row['avg_time'] = (build_info['duration'] / (1000 * 60 * 60)) % 24
        #     time_flag = True

        job_detail_list.append(job_dict_row)
    json_object = json.dumps(job_detail_list)
    print(json_object)
    return json_object


@app.route('/save_all/', methods=['GET'])
@cross_origin()
def save_all_job_details():
    # --- add map of all the job names ---- #

    if path.exists("job_name.json"):
        with open('job_name.json') as f:
            job_name_dict = json.load(f)

    job_name_dict = job_name_dict['master_jobs']

    all_jobs_info = []
    for i in range(1, len(job_name_dict)):
        job_name = job_name_dict[i]['job_val']
        job_dict_row = {'suiteName': '', 'builds': 0, 'dif': 0, 'suc': 0, 'skip': 0, 'test_count': 0, 'avg_time': 0, 'pct': 0}
        info = server.get_job_info(job_name)
        builds = info['builds']
        for build in builds:
            build_info = server.get_build_info(job_name, build['number'])
            job_dict_row['avg_time'] = (build_info['duration'] / (1000 * 60 * 60)) % 24
            status = build_info['actions'][3]
            if 'failCount' not in status.keys():
                pass
            else:
                job_dict_row['dif'] = int(job_dict_row['dif']) + int(status['failCount'])
                job_dict_row['skip'] = job_dict_row['skip'] + status['skipCount']
                job_dict_row['suc'] = job_dict_row['suc'] + (
                        status['totalCount'] - (status['failCount'] + status['skipCount']))
                job_dict_row['test_count'] = job_dict_row['test_count'] + status['totalCount']
            job_dict_row['suiteName'] = job_name
            job_dict_row['builds'] = job_dict_row['builds'] + 1
        suc_pct = int((int(job_dict_row['suc']) / int(job_dict_row['test_count']) * 100));
        job_dict_row['pct'] = 100 - suc_pct

        # append particular job info in a list
        all_jobs_info.append(job_dict_row)

    myfile = "data.json"

    with open(myfile, 'w') as outfile:
        json.dump(all_jobs_info, outfile)

    return "data dumped into a json file"


@app.route('/get_all/', methods=['GET'])
@cross_origin()
def get_all_job_details():
    if path.exists("data.json"):
        with open('data.json') as f:
            data = json.load(f)
    else:
        save_all_job_details()
        with open('data.json') as f:
            data = json.load(f)
    return {'jobs': data}


    # time.sleep(5)
    # all_job_data_col = db["all_job_data"]
    # time.sleep(5)
    # print(all_job_data_col.find()[0])
    # time.sleep(5)
    # return {'all_job_data': all_job_data_col.find()[0]['all_job_data']}
    # return "done"


# if __name__ == '__main__':
#     # app.run()
#     app.run(host='127.0.0.1', port=5000, debug=True)


# if 'master' in git_branch_name:
#     name = job_name.split('_')
#     if len(name) >= 2:
#         master_job['job_name'] = ' '.join(name)
#         master_job['job_val'] = job_name
# if master_job:
#     # if 'sanity' in job_name or 'Sanity' in job_name:
#     if job_name.startswith('sanity') or job_name.startswith('Sanity'):
#         master_jobs[0]['sanity'].append(master_job)
#     else:
#         master_jobs[1]['feature'].append(master_job)
#     master_jobs[2]['all'].append(master_job)
