import os
import csv
import time

import lstm_qos

qos_test_list = [500*i for i in range(6, 18)]
success = 0
failure = 0
for qos_time in qos_test_list:
    print("qos time: " + str(qos_time))
    # Set the number of workers to 1
    os.system("rm distributed-lstm.jinja")
    os.system("cp ../distributed-lstm.jinja ./")
    start_time = time.time()
    lstm_qos.qos_guarantee(qos_time)
    end_time = time.time()
    # Delete job
    lstm_qos.delete_job()
    if end_time - start_time <= qos_time:
        print("success")
        success += 1
    else:
        print("failure")
        failure += 1
    with open("exp_result.csv", 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, dialect='excel')
        writer.writerow([qos_time, end_time - start_time])
    time.sleep(30)
print("success rate: " + str(success/(success + failure)))
