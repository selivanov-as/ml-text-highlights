import argparse
import requests
import json


# Returns a namespace:
#
# Namespace(
# OAuth_token=<>,
# Pool_ID=<>,
# command=<>
# )
def get_args():
    parser = argparse.ArgumentParser(description='Process some integers.', usage='<command> <OAuth_token> <Pool_ID>')
    parser.add_argument('command', type=str,
                        help='Which command to perform', choices=['consistency', 'pair-statistic'])
    parser.add_argument('OAuth_token', type=str,
                        help='OAuth token could be found here: https://toloka.yandex.ru/requester/profile/integration')
    parser.add_argument('Pool_ID',
                        help='Pool ID. Could be found in URL when you\'re on pool page')

    return parser.parse_args()


def get_pair_statistic(args):
    response = requests.get(f'https://toloka.yandex.ru/api/v1/assignments?pool_id={args.Pool_ID}&limit=100',
                            headers={'Authorization': f'OAuth {args.OAuth_token}'})
    if response.status_code != 200:
        print(f'Got {response.status_code} code')
        return

    body = json.loads(response.text)
    statistics = dict()
    for item in body['items']:
        for i, task in enumerate(item['tasks']):
            if 'solutions' not in item:
                continue

            left_image_array, right_image_array = task['input_values']['image_left'].split('/'), task['input_values'][
                'image_left'].split('/')
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


def check_consistency(args):
    return


def main():
    args = get_args()

    if args.command == 'pair-statistic':
        return get_pair_statistic(args)
    if args.command == 'consistency':
        return check_consistency(args)


main()
