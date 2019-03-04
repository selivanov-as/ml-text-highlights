# ML text highlights / Выделение смысла из текста

* Цель
	* Ускорить взаимодействие с письмами пользователя
* Техническая цель
	* Плагин, выделяющий важное в тексте
* Успех
	* Появится плагин в Chromium в marketplace, со 100 пользователями, который умеет выделять важдное в тексте письма с хорошей метрикой качества (PR/AC/Recall/?) за 1 с (300мс) к 25.04.2019 и соблюдением GDPR
* Метрики
	* latency
	* PR/AC/Recall/?
	* Рейтинг в marketplace
	* Количество пользователей


## Задачи
#### Plugin
1. Сделать UI
2. Внедрить предсказатель/решающую функцию
3. Уметь готовить данные для решающей функции
#### Pipeline ML
1. Почитать статьи
2. Собрать данные
3. Обучиться на данных
4. Измериться на данных
5. Создать решающую функцию

## Wikipedia Corpus
Скачиваем последний дамп с русской википедией (занимает ~60 минут в зависимости от скорости интернета)
`wget http://dumps.wikimedia.org/ruwiki/latest/ruwiki-latest-pages-articles.xml.bz2`

Вычленяем и сохраняем все токены из корпуса в текстовый файл (занимает 3-5 часов)
https://gist.github.com/bulgakovk/4d81cdfb12bc0edab8f0f1fa0c578bc4

Лемматизация и обучение моделей с 27 страницы:
http://www.machinelearning.ru/wiki/images/7/7e/Mel_lain_msu_nlp_sem_5.pdf

## Count PR/AC/Recall and F1 Score
* Скрипт для подсчета метрик качества и размеченные данные находятся в `/server`

* `samples_raw.py` содержит размеченные тексты. Символ `@` перед словом, означает, 
что данное слово должно быть выделено как важное

* Чтобы запустить подсчет метрик необходимо выполнить команду `python script.py`,
находясь в `/server`.

*  Метод, используемый для подсчета метрик может быть изменен в 4-й строке:
`METHOD = tf_idf_normalized` с `tf_idf_normalized` на любой другой метод, 
возвращающий тот же самый список слов, обернутых в объект с булевым
свойством `highlight`
## Configuring AWS Lambda
* Login or register new account on [AWS console](https://aws.amazon.com/ru/lambda/) page.  
* Create new or open existing function to edit [here.](https://eu-west-1.console.aws.amazon.com/lambda/home?region=eu-west-1#/functions)
* When your Lambda function is ready, you have to add so called `trigger` that could be able to make requests to your function. 
Choose `API Gateway` from list in `Designer` menu. 
* Finish configuring in `API Gateway` menu below and save your HTTP Endpoint. 
* Now your Lambda function is successfully configured.

## How to deploy source codes to AWS Lambda function
* You need to have AWS credentials in `~/.aws/credentials`
file with following content:
```
[default] ; default profile
aws_access_key_id = <...>
aws_secret_access_key = <...>
```

This information could be found [here.](https://console.aws.amazon.com/iam/home#/security_credentials)

* Configure these params in `gulpfile.js` (lines 43-52):
Don't forget to change name and insert correct Lambda ID
```
const params = {
    name: "<Your function name>",
    role: "arn:aws:iam::<Lamda ID>:role/service-role/defaultRole",
    runtime: "python3.7"
};

const options = {
    profile: "default",
    region: "eu-west-1"
};
```

* Install `gulp` globally with `npm i gulp -g` command (you need to have `npm` installed on your machine)

* Install all required node modules locally with `npm i` command  

* Enter `gulp` command and wait until your sources will be deployed to AWS Lambda ()