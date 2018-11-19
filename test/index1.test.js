const {walkDOM, highlightFunc, onClick} = require('../plugin/Highlight.js');
const body = "";//need to have DOM object

const nodes = [];
const collectNodes = node => {
    nodes.push(node);
};

test('adds 1 + 2 to equal 3', _ => {
    walkDOM(body, collectNodes);
    expect(nodes.length).toBeGreaterThan(0);
});