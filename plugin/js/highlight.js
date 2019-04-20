var server_addr = 'http://127.0.0.1:5000/tf-idf';
var rus_or_dig = /[а-яё0-9]/i;
var ignored_tags = new Set(["SCRIPT", "STYLE"]);
var endpoint_resolver_addr = "https://5bs06gpnr4.execute-api.eu-west-1.amazonaws.com/default/endpointResolver";

async function getEndpoint() {
    try {
        const response = await axios.get(endpoint_resolver_addr);

        return response.data;
    } catch (e) {
        console.error(e);
    }
}

function dfs (node, text_nodes) {
    for (let child = node.firstChild; child; child = child.nextSibling) {
        if (child.nodeName === '#text') {
            text_nodes.push(child);
        }
        dfs(child, text_nodes);
    }
}

function parseTextNodes () {
    const [text_nodes, texts, good_nodes] = [ [], [], [] ];
    dfs(document.body, text_nodes);

    for (node of text_nodes) {
        parent = node.parentNode;
        parent_tag = parent.nodeName;
        if (ignored_tags.has(parent_tag)) continue;

        const text = node.innerText || node.textContent;
        if (text.search(rus_or_dig) === -1) continue;
        good_nodes.push(node);
        texts.push({
            'text': text,
            'tag': parent_tag
        });
    }

    return { texts, text_nodes, good_nodes }
}

function parseResponseAndHighlight (spans, { texts, good_nodes }) {
    for (let i = 0; i < good_nodes.length; i++) {
        let node = good_nodes[i];
        let parent = node.parentNode;

        if (spans[i].length > 0) {
            const last_node = node.nextSibling;
            node = parent.removeChild(node);
            let last_pos = 0;

            for (const span of spans[i]) {
                if (span[0] > last_pos) {
                    const text_node = document.createTextNode(
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

async function main () {
    const endpoint = await getEndpoint();
    const { texts, text_nodes, good_nodes } = parseTextNodes();

    const response = await axios.post(endpoint,
        JSON.stringify({ texts }),
        { headers: { 'Content-Type': 'application/json' } }
    );

    parseResponseAndHighlight(response.data, { texts, good_nodes, text_nodes });
}

main().catch(error => {
    // ToDo: send error message to host here
    console.log(error);
});