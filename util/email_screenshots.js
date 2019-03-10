const webdriver = require('selenium-webdriver');
const By = require('selenium-webdriver').By;
const until = require('selenium-webdriver').until;
const fs = require('fs');
const path = require('path');
const EMAILS_AMOUNT = 20;

const getScreenshotOfGivenEmail = (emailName, driver) => {
    return driver.get('file://' + path.join(__dirname, `../html_emails/${emailName}.html`))
        .then(() => driver.takeScreenshot())
        .then((data, err) => {
            if (err) {
                console.error(err);
                process.exit(-1);
            }
            fs.writeFileSync(`./${emailName}.png`, data, 'base64');
        })
};

const main = async () => {
    const driver = new webdriver.Builder().forBrowser('chrome').build();
    driver.manage().window().maximize();
    driver.manage().deleteAllCookies();

    for (let i = 1; i <= EMAILS_AMOUNT; i++)
        await getScreenshotOfGivenEmail(`letter${i}`, driver);

    driver.quit()
};

main();