import requests
import json
import argparse
import time


def GetArgumentParser():
    """
    to parse the argument
    """
    parser = argparse.ArgumentParser(description="The scripts to post results .")

    parser.add_argument(
        "-p", "--log_path",
        type=str,
        default="summary_benchmark.log",
        help="log path."
    )

    parser.add_argument(
        "-b", "--branch",
        type=str,
        default="master",
        help="tensorflow branch."
    )

    parser.add_argument(
        "-t", "--time",
        type=str,
        default="",
        help="tensorflow test time."
    )

    return parser


def del_duplicate_line(log_l, key_wd, key_point):
    print(key_wd, "before len:", len(log_l))
    key_log = []
    for i, line in enumerate(log_l):
        if line.split(';')[key_point] == key_wd:
            key_log.append(line)
    print(key_wd, "after len:", len(key_log))
    return key_log


def sort_model_log(log, key_wd):
    intel_log = []
    private_log = []
    for line in log:
        if line.split(';')[-2].split('-')[0] == key_wd:
            intel_log.append(line)
        else:
            private_log.append(line)
#     print("intel model num:{}, private model num:{}".format(len(intel_log), len(private_log)))
    return intel_log, private_log


def post2hemis(post_dict):
    upload_data = json.dumps(post_dict)

    url = "http://heims.sh.intel.com/api/storedata/tensorflow"
    r = requests.post(url, upload_data)
#     print(upload_data)
#     print("return txt:", r.text)
#     print("return state:", r.status_code)


def main():
    args, extra_args = GetArgumentParser().parse_known_args()
    machine = {
        "cores": "56",
        "model": "AIPG CLX-8280"

    }
    rlt_json = {
        "date": time.strftime("%Y-%m-%d"),
        "device": "CLX",
        "category": "inf-dummy",
        'branch':args.branch,
        "environment":  machine,
    }

    res_dict = {}
    if args.log_path =="" or args.branch == "":
#         print("pls input the log you want to post!\n e.g: python post2hemis.py -p log_path -b branch")
        exit(0)
    else:
        print(args.log_path)
        log = open(args.log_path, 'r')
        raw_readers = log.read().splitlines()
#         print("123",type(raw_readers[0]), raw_readers[0].split(',')[0])

        if raw_readers[0].split(',')[0] == 'Model':
#             print("remove line 1")
            raw_readers.remove(raw_readers[0])

        for machine_tyep in ["CLX"]: #["SKX", "CLX"]:
            res_list = []
            model_list = []
            a, b, c, d, = 0, 0, 0, 0
            key_log = del_duplicate_line(raw_readers, machine_tyep, 2)
            print('1 ----------------------------------------------------')
            print(key_log)
            for src in ['training','inference']:  #['inference', 'training']:
                a +=1
                src_log = del_duplicate_line(key_log, src, 1)
                print('2 -------------------------------------------------')
                print(src_log)
                print("src log:", len(src_log))
                if len(src_log) == 0:
                    continue

                intel_model, private_model = sort_model_log(src_log, 'Intel')
                print('3 ------------------------------------------------')
                print(intel_model)
                print('4--------------------------------------------------')
                print(private_model)
                print("intel model len:{}, private model len:{}".format(len(intel_model), len(private_model)))
                model_conter = 0

                for model_type in [intel_model, private_model]:

                    if len(model_type) == 0:
                        continue
                    model_conter += 1
                    # print("!!!!!!!!!!!!!!!conter:", model_conter)

                    for line in model_type:
                        model_list.append(line.split(';')[0].lower())
                    model_list = list(set(model_list))
#                     print("model list:",model_list)
                    print('5----------------------------------------------')
                    print(model_list)
                    
                    for m in model_list:
                        value_list = []
                        b += 1
                        res_dict['key'] = m
                        res_dict['type'] = src
                        have_acc = 0
                        have_lat = 0
                        have_thpt= 0
                        latency_dict = {'config':'latency'}
                        thrpt_dict = {'config':'throughput'}
                        acc_dict = {'config':'accuracy'}
                        for line in model_type:
                            c += 1
                            if model_conter == 1:
                                res_dict['source'] = 'Intel-Models'
                            else:
                                res_dict['source'] = 'Private-Models'
                            if m == line.split(';')[0].lower():
                                if line.split(';')[4] == 'Latency':
                                    have_lat =1
                                    data_type = line.split(';')[3]
                                    bs = line.split(';')[5]
                                    value = 'None'
                                    if line.split(';')[6] != '':
                                        value = line.split(';')[6]
                                    latency_dict[data_type] = {'bs':bs, 'value':value}

                                elif line.split(';')[4] == 'Accuracy':
                                    have_acc = 1
                                    data_type = line.split(';')[3]
                                    bs = line.split(';')[5]
                                    value = 'None'
                                    if line.split(';')[6] != '':
                                        value = line.split(';')[6]
                                    acc_dict[data_type] = {'bs':bs, 'value':value}

                                else:
                                    have_thpt = 1
                                    data_type = line.split(';')[3]
                                    bs = line.split(';')[5]
                                    value = 'None'
                                    if line.split(';')[6] != '':
                                        value = line.split(';')[6]
                                    thrpt_dict[data_type] = {'bs':bs, 'value':value}
                        if have_lat:
                            value_list.append(latency_dict)
                        if have_acc:
                            value_list.append(acc_dict)
                        if have_thpt:
                            value_list.append(thrpt_dict)
                        res_dict['value'] = value_list
                        res_list.append(res_dict)
                        res_dict = {}
            # return

            if machine_tyep == "SKX":
                machine['model'] = "AIPG SKX_8180"
                rlt_json['device']= "SKX_8180"
            else:
                machine['model'] = "AIPG CLX_8280"
                rlt_json['device'] = "CLX_8280"
            rlt_json['results'] = res_list

            print(rlt_json)
            # post2hemis(rlt_json)


if __name__ == '__main__':
    main()
