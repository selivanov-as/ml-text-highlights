const server_addr = 'http://127.0.0.1:5000/cfg';
const rus_or_dig = /[а-яё0-9]/i;
const ignored_tags = new Set(["SCRIPT", "STYLE"]);

var text_nodes = [];
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
	texts.push(text);
}

spans = [];
spans = axios.post(server_addr, texts).then(
	function (response) {
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
							texts[i].slice(
								last_pos, span[0]
							)
						);
						parent.insertBefore(text_node, last_node);
					}
					marked_node = document.createElement("mark");
					marked_node.textContent = texts[i].slice(span[0], span[1]);
					parent.insertBefore(marked_node, last_node);
					last_pos = span[1];
				}
				
				if (last_pos < texts[i].length) {
					text_node = document.createTextNode(
						texts[i].slice(
							last_pos, texts[i].length
						)
					);
					parent.insertBefore(text_node, last_node);
				}
			}
		}
	}
);
