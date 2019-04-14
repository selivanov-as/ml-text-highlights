const request = require('request-promise');
const yargs = require('yargs');

const getArgs = () => {
    const options = {
        'OAuth-token': {
            type: 'string',
            description: 'OAuth token could be found here: https://toloka.yandex.ru/requester/profile/integration',
            demandOption: true,
            alias: 't'
        },
        pool: {
            description: 'Pool ID. Could be found in URL when you\'re on pool page',
            type: 'string',
            demandOption: true,
            alias: 'p'
        }
    };

    return yargs
        .usage('Usage: $0 <command> [options]')
        .wrap(yargs.terminalWidth())
        .command('consistency [options]', 'Check consistency of answers for each user')
        .command('pair-statistic [options]', 'Get statistic for each pair', {
            'OAuth-token': options['OAuth-token'],
            pool: options.pool
        })
        .demandCommand(1, 'You need at least one command before moving on')
        .help('help').alias('help', 'h')
        .argv
};

const checkConsistency = () => {

};

const getPairStatistic = async (args) => {
    const response = await request({
        uri: `https://toloka.yandex.ru/api/v1/assignments?pool_id=${args.p}&limit=100`,
        method: 'GET',
        headers: {
            Authorization: `OAuth ${args.t}`
        },
        json: true
    });

    const statistics = new Map();
    response.items.forEach(item =>
        item.tasks.forEach((task, i) => {
            if (!item.solutions) return;

            const [leftImageArray, rightImageArray] = [task.input_values.image_left.split('/'), task.input_values.image_left.split('/')];
            const [leftName, rightName] = [`${leftImageArray.pop()}[${leftImageArray.pop()}]`, `${rightImageArray.pop()}[${rightImageArray.pop()}]`];

            let currentLeftStatistic = statistics.get(leftName);
            if (!currentLeftStatistic) currentLeftStatistic = {shown: 1, chosen: 0};
            else currentLeftStatistic.shown++;

            let currentRightStatistic = statistics.get(rightName);
            if (!currentRightStatistic) currentRightStatistic = {shown: 1, chosen: 0};
            else currentRightStatistic.shown++;

            item.solutions[i].output_values.result === 'left'
                ? currentLeftStatistic.chosen++
                : currentRightStatistic.chosen++;

            statistics.set(leftName, currentLeftStatistic);
            statistics.set(rightName, currentRightStatistic);
        })
    );

    console.table(statistics);
};

const main = async () => {
    const args = getArgs();
    const commandName = args._[0];

    switch (commandName) {
        case 'consistency':
            return checkConsistency(args);
        case 'pair-statistic':
            return getPairStatistic(args);
    }
};

main().catch(console.error);