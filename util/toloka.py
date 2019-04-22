import argparse
import datetime
import json
import sys
from itertools import zip_longest

import numpy as np
import pandas as pd
import requests

cache = {}

def get_args():
    parser = argparse.ArgumentParser(description='Process some integers.',
                                     usage='<command> <OAuth_token> <Pool_ID>')
    parser.add_argument(
        'OAuth_token', type=str,
        help='OAuth token could be found here: '
             'https://toloka.yandex.ru/requester/profile/integration')
    parser.add_argument(
        'Pool_ID',
        help='Pool ID. Could be found in URL when you\'re on pool page')
    parser.add_argument(
        '-s', '--pair-statistic',
        help='Print statistics for tasks',
        action='store_true')
    parser.add_argument(
        '-c', '--check',
        help='Check users for consistency and honeypot '
             'performance and store results in dataframe',
        action='store_true')
    parser.add_argument(
        '-e', '--send-evals',
        help='Send approvals as delayed evaluation',
        action='store_true')
    parser.add_argument(
        '-b', '--send-blocks',
        help='Check users for consistency and honeypot performance, '
             'store results in dataframe '
             'and block inconsistent and honeypotted users via toloka API',
        action='store_true')
    parser.add_argument(
        '-p', '--path',
        type=str,
        help='dataframe saving path, default is ../toloka_results/pool_{Pool_ID}_results.csv'
    )

    return parser.parse_args()


def make_request(args):
    response = requests.get(
        f'https://toloka.yandex.ru/api/v1/assignments?pool_id={args.Pool_ID}&limit=10000',
        headers={'Authorization': f'OAuth {args.OAuth_token}'})
    if response.status_code != 200:
        print(f'Got {response.status_code} code')
        exit(1)

    return json.loads(response.text)


def get_pair_statistic(args):
    body = cache.get('body', None) or make_request(args)
    cache['body'] = body
    statistics = dict()
    for item in body['items']:
        for i, task in enumerate(item['tasks']):
            if 'solutions' not in item:
                continue

            left_image_array = task['input_values']['image_left'].split('/')
            right_image_array = task['input_values']['image_right'].split('/')
            left_name, right_name = f'{left_image_array.pop(-1)}[{left_image_array.pop(-1)}]', \
                                    f'{right_image_array.pop(-1)}[{right_image_array.pop(-1)}]'

            current_left_statistic = {}
            if left_name not in statistics:
                current_left_statistic = {'shown': 1, 'chosen': 0}
            else:
                current_left_statistic = statistics[left_name]
                current_left_statistic['shown'] += 1

            current_right_statistic = {}
            if right_name not in statistics:
                current_right_statistic = {'shown': 1, 'chosen': 0}
            else:
                current_right_statistic = statistics[right_name]
                current_right_statistic['shown'] += 1

            if item['solutions'][i]['output_values']['result']:
                current_left_statistic['chosen'] += 1
            else:
                current_right_statistic['chosen'] += 1

            statistics[left_name] = current_left_statistic
            statistics[right_name] = current_right_statistic

            print(statistics)


def make_df(args):
    if 'df' in cache:
        return
    if 'body' not in cache:
        cache['body'] = make_request(args)
    body = cache['body']
    if not body['items']:
        print('empty response!')
        exit(1)
    for item in body['items']:
        common = {k: v for k, v in item.items()
                  if not isinstance(v, (list, dict))}
        common.update({f'{k}__{inner_k}': inner_v
                       for k, v in item.items()
                       if isinstance(v, dict)
                       for inner_k, inner_v in v.items()})
        tasks, solutions = item['tasks'], item.get('solutions', [])
        for task, solution in zip_longest(tasks, solutions):
            cur_vals = {k: v for k, v in task.items()
                        if not isinstance(v, (list, dict))}
            cur_vals.update({k: v for k, v in task['input_values'].items()})
            if 'known_solutions' in task:
                cur_vals['golden'] = task['known_solutions'][0]['output_values']['result']
            else:
                cur_vals['golden'] = np.nan
            cur_vals['task_id'] = task['id']
            del cur_vals['id']
            for opt_key in ['overlap', 'submitted', 'expired',
                            'public_comment', 'accepted']:
                cur_vals[opt_key] = cur_vals.get(opt_key, np.nan)
            cur_vals['solution'] = solution['output_values']['result'] if solution else np.nan
            cur_vals.update(common)

            if 'df' not in cache:
                cache['df'] = pd.DataFrame(columns=cur_vals.keys())
            df = cache['df']
            if set(df.columns) != cur_vals.keys():
                print(
                    set(df.columns) - cur_vals.keys(),
                    cur_vals.keys() - set(df.columns),
                    cur_vals, file=sys.stderr
            )

            df.loc[len(df), :] = cur_vals

    df = cache['df']
    df['alg_left'] = df.apply(lambda x: x['image_left'].split('/')[-2], axis=1)
    df['alg_right'] = df.apply(lambda x: x['image_right'].split('/')[-2],
                               axis=1)
    df['algs'] = df.apply(
        lambda x: '__'.join(sorted([x['alg_left'], x['alg_right']])), axis=1)

    def get_task(line):
        _, task_l = line.image_left.rsplit('/', maxsplit=1)
        _, task_r = line.image_right.rsplit('/', maxsplit=1)
        assert task_l == task_r
        return task_l

    df['task'] = df.apply(get_task, axis=1)

    def get_chosen_alg(line):
        if line.solution is np.nan:
            return np.nan
        elif line.solution == 'left':
            return line.alg_left
        elif line.solution == 'right':
            return line.alg_right
        else:
            assert False

    df['chosen_alg'] = df.apply(get_chosen_alg, axis=1)


def save_dataframe(args):
    if 'df' not in cache:
        make_df(args)
    df = cache['df']
    path = args.path or f'../toloka_results/pool_{args.Pool_ID}_results.csv'
    df.to_csv(path)


def send_evaluations(args):
    if 'df' not in cache:
        make_df(args)
    df = cache['df']
    for iid in df.groupby('id')['id'].max():
        message = {
          "status": "ACCEPTED",
          "public_comment": "Принято!"
        }
        body = json.dumps(message)
        response = requests.patch(
            f'https://toloka.yandex.ru/api/v1/assignments/{iid}',
            data=body,
            headers={'Authorization': f'OAuth {args.OAuth_token}',
                     'Content-Type': 'application/json'})
        if (response.status_code != 200
                and json.loads(
                    response._content
                )['code'] != 'INAPPROPRIATE_STATUS'):
            print('unsuccessful patch request:',
                  response.__dict__, sep='\n')
            exit(1)


def check_answers(args,
                  min_consistency_checks_showed=1, min_inconsistent_share=0.4,
                  min_honeypot_showed=3, min_honeypot_wrong_share=0.4):
    if 'df' not in cache:
        make_df(args)
    df = cache['df']
    user_algs_task_aggregation = df[df.golden.isna()].groupby(
        by=['user_id', 'algs', 'task']
    )['chosen_alg'].agg({'n_showed': 'count', 'different_answers': 'nunique'})
    user_algs_task_aggregation['item_ids'] = df[df.golden.isna()].groupby(
        by=['user_id', 'algs', 'task']
    )['id'].agg(lambda x: list(x))
    user_algs_task_aggregation = user_algs_task_aggregation[
        user_algs_task_aggregation.n_showed > 1]
    user_algs_task_aggregation['consistent'] = user_algs_task_aggregation[
                                              'different_answers'] == 1

    # inconsistent = user_algs_task_aggregation[
    #     user_algs_task_aggregation.consistent != True]
    # inconsistent_item_ids = set(iid
    #                             for line in inconsistent['item_ids']
    #                             for iid in line)

    user_aggregation = user_algs_task_aggregation.groupby(by='user_id')[
        'consistent'].agg(['count', 'sum'])  # n_task_checked, n_tasks_passed
    # share_of_tasks_failed:
    user_aggregation['inconsistent_share'] = (
            1 - user_aggregation['sum'] / user_aggregation['count'])
    inconsistent_users = set(
        user_aggregation[
            (user_aggregation['inconsistent_share'] > min_inconsistent_share)
            & (user_aggregation['count'] >= min_consistency_checks_showed)
        ].index)
    df['by_inconsistency_blocked_user'] = df.user_id.apply(
        lambda uid: uid in inconsistent_users)

    df['honeypotted'] = (df.chosen_alg == 'random')
    honeypot_user_aggregation = df[~df.golden.isna()].groupby('user_id')[
        'honeypotted'].agg({'n_showed': 'count', 'n_wrong': 'sum'})
    honeypot_user_aggregation[
        'wrong_share'
    ] = honeypot_user_aggregation.n_wrong / honeypot_user_aggregation.n_showed

    honeypotted_users = set(
        honeypot_user_aggregation[
            (honeypot_user_aggregation.wrong_share > min_honeypot_wrong_share)
            & (honeypot_user_aggregation.n_showed >= min_honeypot_showed)
        ].index)
    df['by_honeypot_blocked_user'] = df.user_id.apply(
        lambda uid: uid in honeypotted_users)

    if args.send_blocks:
        blockdays = 60
        for uid in inconsistent_users:
            message = {
                "scope": "PROJECT",
                "user_id": uid,
                "project_id": "20359",
                "private_comment": "Непоследовательность",
                "will_expire": (
                        datetime.datetime.now() + datetime.timedelta(blockdays)
                ).strftime("%Y-%m-%dT%H:%M:%S")
            }
            body = json.dumps(message)
            response = requests.put(
                'https://toloka.yandex.ru/api/v1/user-restrictions',
                data=body,
                headers={'Authorization': f'OAuth {args.OAuth_token}',
                         'Content-Type': 'application/json'})
            if response.status_code not in [200, 201]:
                print('unsuccessful put request:',
                      response.__dict__, sep='\n')
                exit(1)

        for uid in honeypotted_users - inconsistent_users:
            message = {
                "scope": "PROJECT",
                "user_id": uid,
                "project_id": "20359",
                "private_comment": "ханипот (постобработка)",
                "will_expire": (
                        datetime.datetime.now() + datetime.timedelta(blockdays)
                ).strftime("%Y-%m-%dT%H:%M:%S")
            }
            body = json.dumps(message)
            response = requests.put(
                'https://toloka.yandex.ru/api/v1/user-restrictions',
                data=body,
                headers={'Authorization': f'OAuth {args.OAuth_token}',
                         'Content-Type': 'application/json'})
            if response.status_code != 200:
                print('unsuccessful put request:',
                      response.__dict__, sep='\n')
                exit(1)


def main():
    args = get_args()

    if args.pair_statistic:
        get_pair_statistic(args)
    if args.check or args.send_blocks:
        check_answers(args)
    save_dataframe(args)
    if args.send_evals:
        send_evaluations(args)


if __name__ == '__main__':
    main()
