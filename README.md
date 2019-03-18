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


## Подготовка работающей модели к загрузке на AWS Lambda
### Настройка окружения
* Необходимо создать файл `credentials` (без расширения) в директории `~/.aws`
со следующим содержимым:
    ```
    [default] ; default profile
    aws_access_key_id = <...>
    aws_secret_access_key = <...>
    ```
    Ключи можно найти в нашем чате или создать новые [тут.](https://console.aws.amazon.com/iam/home#/security_credentials)
* Необходимо установить [node.js](https://nodejs.org/en/)
* Необходимо установить `gulp` с глобальным флагом при помощи команды `npm i gulp -g`
* Необходимо установить локальным зависимости командой `npm i`, находясь в текущей директории.
* Необходимо установить Docker (https://www.docker.com/products/docker-desktop)

### Подготовка исходников
Можно ориентироваться на то, как выглядит проект в [этой ветке](https://github.com/selivanov-as/ml-text-highlights/tree/deployment/tf-idf),
то есть: скомпилированные зависимости под AWS, "чистый" репозиторий без других файлов, отдельная ветка.
Обработчик, который будет вызывать Lambda при тригерах: `"main.handler"`. 
Это значит, что вызывается функция `handler` lambda_src/main.py. 
Это поведение можно менять в настройках функции в `gulpfile`, если в этом есть необходимость.
Пошаговое руководство выглядит так:
* Вынести исходный код из своих моделей в main.py файл в функцию `handler`. Работа этой функции
должна заключаться в принятии входных параметров из объекта запроса, обработки информации
при помощи модели и возврата ответа. Следует обратить внимание, что функция параметры
из поля `texts`, т.е. плагин должен упаковывать список нод в массив, который и будет 
содержаться внутри поля `texts`. Например, корректным **запросом** будет такой запрос:
(_Content-Type: application/json_)
```
{
  "texts": [
    {
      "text": "Здравствуйте, Kirill Bulgakov,",
      "tag": "P"
    },
    {
      "text": "\n    Мы обратили внимание, что Вы еще не активировали Вашу Предоплаченную Дебетовую Карту Payoneer MasterCard® и хотели\n    бы\n    убедиться в том, что Вы получили ее. Если Вы еще не получили Вашу карту, пожалуйста, посетите Центр Поддержки для\n    получения дополнительной информации.\n    Если Вы уже получили Вашу карту, Вы можете войти в Ваш аккаунт Payoneer, активировать ее и начать получать выплаты.\n",
      "tag": "P"
    },
    {
      "text": "Для получения дополнительной информации относительно доставки карт, пожалуйста, прочитайте эту статью в блоге\n    Payoneer.\n    Спасибо,\n    Коллектив Payoneer\n",
      "tag": "P"
    }
  ]
}
```
* Все функции и другие файлы, используемые в модели, должны быть также перенесены в lambda_src, 
так как именно эта директория затем будет упаковываться в архив.
* Необходимо удостовериться, что `./venv` создан и в нем на данный момент не находятся никакие
установленные зависимости (т.к. они могут быть скомпилированы в окружении, которое не совпадает 
с тем, в котором код исполняется на Lambda), а в requirements находится актуальный список зависимостей.
Желательно лишние зависимости удалять, чтобы не превысить лимиты на объем загружаемого контейнера.
* Компилируем зависимости под окружение AWS:
`docker run -it -v $PWD:/var/task lambci/lambda:build-python3.6 bash`

`source ./venv/bin/activate`

`pip install -r requirements.txt`

* Теперь модель полностью готова к деплою на AWS Lambda. venv с зависимостями
предлагается заливать прямо в репозиторий, чтобы не приходилось компилировать их
заново.

### Настройка параметров AWS Lambda функции
* Параметры Lambda функции настраиваются в `gulpfile.js` (линии 43-52):
Если использовать **имя уже существующей функции**, ее перезапишет исходниками новой, 
поэтому следует быть аккуратным.
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