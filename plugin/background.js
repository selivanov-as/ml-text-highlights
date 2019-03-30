const highlight = `
    var server_addr = 'http://127.0.0.1:5000/tf-idf';
    var ignored_tags = new Set(["SCRIPT", "STYLE"]);
    var endpoint_resolver_addr = "https://5bs06gpnr4.execute-api.eu-west-1.amazonaws.com/default/endpointResolver";

    var text_nodes = [];
    
    async function getEndpoint() {
        try {
            var response = await axios.get(endpoint_resolver_addr);
            server_addr = response.data;
        } catch (e) {
            console.error(e);
        }
    }
    
    async function dfs(node) {
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
        good_nodes.push(node);
        texts.push({
            'text': text,
            'tag': parent_tag
        });
    }

    spans = [];
    var data = JSON.stringify({texts});
    getEndpoint().then(_ =>
        axios.post(server_addr, data, {headers : {
            'Content-Type': 'application/json'}
        }).then(response => {
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
            }
        )
    );
`;

chrome.browserAction.onClicked.addListener(function (tab) {
    console.log("Click event");
    chrome.tabs.executeScript({code: highlight}, (res) => console.log); //ToDo: Reuse code from Hightlight.js
});
