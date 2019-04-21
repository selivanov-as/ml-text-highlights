const webdriver = require('selenium-webdriver');
const By = require('selenium-webdriver').By;
const until = require('selenium-webdriver').until;
const fs = require('fs');
const path = require('path');
const EMAILS_AMOUNT = 20;
const express = require('express')

const app = express();
app.get('/letter/:number', (req, res) => {
    res.sendFile(path.resolve(__dirname, `../html_emails/letter${req.params.number}.html`))
});

app.listen(3000);

const axios = "https://unpkg.com/axios/dist/axios.min.js";
const mark = "https://cdnjs.cloudflare.com/ajax/libs/mark.js/8.11.1/mark.min.js";
const loadScripts = `
function loadScript(scriptUrl) {
  var head =  document.getElementsByTagName('head')[0];
  var script = document.createElement('script');
  script.type = 'text/javascript';
  script.src = scriptUrl;
  head.appendChild(script);
}
loadScript('${axios}');
loadScript('${mark}');
`;
const highlight = `
    function loadScript(scriptUrl) {
	    return new Promise((resolve) => {
            var head =  document.getElementsByTagName('head')[0];
            var script = document.createElement('script');
            script.type = 'text/javascript';
            script.src = scriptUrl;
            script.addEventListener('load', function() {
                resolve(); 
            });
            
            head.appendChild(script);
	    })
    }

    function loadScripts() {
	    return Promise.all([loadScript('${axios}'), loadScript('${mark}')]);
    }
    
    var server_addr = 'http://127.0.0.1:5000/tf-idf';
    var rus_or_dig = /[а-яё0-9]/i;
    var ignored_tags = new Set(["SCRIPT", "STYLE"]);
    var endpoint_resolver_addr = "https://j3bjlwczt1.execute-api.eu-west-1.amazonaws.com/default/endpointResolver";
    var text_nodes = [];
    
    async function getEndpoint() {
        try {
            var response = await axios.get(endpoint_resolver_addr);
            server_addr = response.data;
            console.log(data)
            console.log(typeof data)
            console.log(server_addr)
            return axios.post(server_addr, data, {headers : {
                'Content-Type': 'application/json'}
            })
        } catch (e) {
            console.error(e);
        }
    }
    
    function dfs(node) {
        for (var child = node.firstChild; child; child=child.nextSibling) {
            if (child.nodeName === '#text') {
                text_nodes.push(child);
            }
            dfs(child);
        }
    }
    
    dfs(document.body);
    var texts = [];
    var good_nodes = [];
    for (node of text_nodes) {
        parent = node.parentNode;
        parent_tag = parent.nodeName;
        if (ignored_tags.has(parent_tag)) {
            continue;
        }
        var text = node.innerText || node.textContent;
        if (text.search(rus_or_dig) == -1) {
            continue;
        }
        good_nodes.push(node);
        texts.push({
            'text': text,
            'tag': parent_tag
        });
    }
    spans = [];
    var data = JSON.stringify({texts});
    
    return loadScripts()
        .then(() => getEndpoint())
        // .then(() =>
        //     axios.post(server_addr, data, {headers : {
        //         'Content-Type': 'application/json'}
        //     })
        .then(response => {
            spans = response.data;
            for (var i = 0; i < good_nodes.length; i++) {
                node = good_nodes[i];
                parent = node.parentNode;
                
                if (spans[i].length > 0) {
                    var last_node = node.nextSibling;
                    node = parent.removeChild(node);
                    var last_pos = 0;
                    for (span of spans[i]) {
                        if (span[0] > last_pos) {
                            text_node = document.createTextNode(
                                texts[i]['text'].slice(
                                    last_pos, span[0]
                                )
                            );
                            parent.insertBefore(text_node, last_node);
                        }
                        marked_node = document.createElement("mark");
                        marked_node.textContent = texts[i]['text'].slice(span[0], span[1]);
                        parent.insertBefore(marked_node, last_node);
                        last_pos = span[1];
                    }
                    
                    if (last_pos < texts[i]['text'].length) {
                        text_node = document.createTextNode(
                            texts[i]['text'].slice(
                                last_pos, texts[i]['text'].length
                            )
                        );
                        parent.insertBefore(text_node, last_node);
                    }
                }
            }
        });
`;

const wait = (ms) => {
    return new Promise((resolve, reject) => {
        setTimeout(resolve, ms)
    });
};

const getScreenshotOfGivenEmail = async (emailNumber, driver) => {
    try {
        await driver.get(`http://localhost:3000/letter/${emailNumber}`);
        await driver.executeScript(highlight);
        await wait(5000);
        const data = await driver.takeScreenshot();
        fs.writeFileSync(`./letter${emailNumber}.png`, data, 'base64');
    } catch (e) {
        // ignore script timeout error
        if (e.toString().indexOf('script timeout') === -1) {
            console.error(e)
        }
    }
};

const main = async () => {
    const driver = new webdriver.Builder().forBrowser('chrome').build();
    driver.manage().window().setRect({width: 720, height: 5000})
    driver.manage().deleteAllCookies();

    for (let i = 1; i <= EMAILS_AMOUNT; i++)
        await getScreenshotOfGivenEmail(i, driver);

    driver.quit()
};

main();