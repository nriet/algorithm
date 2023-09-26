#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time: 2022/12/29
# @Author: Shiys
# @File: KafkaProducerHandler.py

import json
from kafka import KafkaProducer
from kafka.errors import KafkaError


class KafkaProducerHandler:

    def __init__(self, config):
        self.host = config.get('host')
        self.port = config.get('port')
        self.topic = config.get('topic')
        self.producer = KafkaProducer(
            bootstrap_servers=['{kafka_host}:{kafka_port}'.format(kafka_host=self.host, kafka_port=self.port)],
            api_version=(0, 10)
        )

    def send_message(self, params):
        try:
            params_message = json.dumps(params)
            # producer = self.producer
            self.producer.send(self.topic, params_message.encode('utf-8'))
            self.producer.flush()
        except KafkaError as e:
            print(e)

    def close(self):
        self.producer.close()