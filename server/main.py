from flask import Flask, jsonify, request
# import json
import asyncio

from clusteing import *
from preps import *
from grouping import *
from ner import *

app = Flask(__name__)


@app.route('/api/data')
def get_data():
    data = {'key': 'value'}
    return str(data)


@app.route('/txts', methods=['POST'])
def get_data1():
    data = request.json
    res = []
    for d in data:
        res.append(preprocess(d))
    return jsonify(res)


@app.route('/clustering', methods=['POST'])
def cluster():
    data = request.json
    res = []
    for d in data['txts']:
        res.append(preprocess(d))
    if data['algorithm'] == 'kmeans':
        res = kmeans(res, data['clusterCount'])
    else:
        res = optics(res)
    return jsonify(res)


@app.route('/tag', methods=['POST'])
def tag():
    data = request.json
    txt = ''
    resp = {}
    if 'texts' in data:
        txt = [preprocess(data['texts'])]
    resp = tagify(data, 0.2, txt)
    res = {
        "ner_tags": create_tags(data['texts']),
        "tags": [keyword for keyword, score in resp.items()]
    }
    return jsonify(res)


@app.route('/api/links', methods=['POST'])
def get_links_info():
    links = request.json
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def process_links():
        tasks = [get_link_info(link) for link in links]
        results = await asyncio.gather(*tasks)
        return {link: result for link, result in zip(links, results)}

    link_info = loop.run_until_complete(process_links())
    loop.close()

    return jsonify(link_info)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
