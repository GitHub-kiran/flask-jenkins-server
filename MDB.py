import jenkins
import pymongo
import pdb

endpoint = 'http://den01jpx.us.oracle.com:8080/';
server = jenkins.Jenkins(endpoint, username='ociui_user', password='ociui4@4')
client = pymongo.MongoClient("localhost", 27017)
db = client["jenkinsStoreDB"]


def save_job_name_list():
    jobs = server.get_jobs()
    # master_jobs = [{'sanity': []}, {'feature': []}, {'all': [{'job_name': 'All Suite', 'job_val': 'All Suite'}]}]
    master_jobs = [{'sanity': []}, {'feature': []}, {'all': []}]
    for i in range(len(jobs)):
        master_job = {}
        job_name = jobs[i]['name']
        print(job_name)
        try:
            last_build_number = server.get_job_info(job_name)['lastCompletedBuild']['number']
        except:
            continue
        build_info = server.get_build_info(job_name, last_build_number)
        git_branch_name = build_info['actions'][1]['lastBuiltRevision']['branch'][0]['name']
        if 'master' in git_branch_name or 'MasterClone' in git_branch_name:
            name = job_name.split('_')
            if len(name) >= 3:
                master_job['job_name'] = ' '.join(name)
                master_job['job_val'] = job_name
        if master_job:
            # if 'sanity' in job_name or 'Sanity' in job_name:
            if job_name.startswith('Sanity') or job_name.startswith('sanity'):
                master_jobs[0]['sanity'].append(master_job)
            else:
                master_jobs[1]['feature'].append(master_job)

    # store all job name list into a DB
    job_name_col = db["job_name_list"]
    job_name_col.insert_one({'master_jobs': master_jobs})
    # job_name_col.insert_one({'master_jobs': master_jobs})


def save_all_job_details():
    # read job name list from db
    job_name_col = db["job_name_list"]
    job_name_dict = job_name_col.find_one()['master_jobs']

    # merge all job names into a single db
    job_name_list = job_name_dict[0]['sanity'] + job_name_dict[1]['feature']

    # iterate over the job details and save all job data in a DB
    all_jobs_info = []
    for i in range(len(job_name_list)):
        job_name = job_name_list[i]['job_val']
        job_dict_row = {'suiteName': '', 'builds': 0, 'dif': 0, 'suc': 0, 'skip': 0, 'test_count': 0, 'avg_time': 0,
                        'pct': 0}
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

        all_job_data_col = db["all_job_data"]
    all_job_data_col.insert_one({'all_job_data': all_jobs_info})
    # all_job_data_col.insert_one({'all_job_data': all_jobs_info})


# save all job name list into a DB
save_job_name_list()

# save all jobs data into a DB
save_all_job_details()
