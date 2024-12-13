#!/bin/bash

# Wait for RabbitMQ to start
until rabbitmqctl status; do
  echo "Waiting for RabbitMQ to start..."
  sleep 1
done

# Create user and set permissions
rabbitmqctl add_user ${RABBITMQ_USER} ${RABBITMQ_PASS}
rabbitmqctl set_user_tags ${RABBITMQ_USER} administrator
rabbitmqctl set_permissions -p / ${RABBITMQ_USER} ".*" ".*" ".*"

# Declare queues
rabbitmqadmin declare queue name=business_queue durable=true
rabbitmqadmin declare queue name=domain_email_queue durable=true
rabbitmqadmin declare queue name=phone_queue durable=true
rabbitmqadmin declare queue name=serp_queue durable=true
rabbitmqadmin declare queue name=leak_check_queue durable=true

# Add Shodan-related queues
rabbitmqadmin declare queue name=shodan_search_queue durable=true
rabbitmqadmin declare queue name=shodan_host_queue durable=true

# Declare exchanges
rabbitmqadmin declare exchange name=shodan_exchange type=direct durable=true

# Bind queues to exchange
rabbitmqadmin declare binding source=shodan_exchange destination=shodan_search_queue routing_key=search
rabbitmqadmin declare binding source=shodan_exchange destination=shodan_host_queue routing_key=host

# Set up dead letter exchanges and queues
rabbitmqadmin declare exchange name=dead_letter_exchange type=direct durable=true
rabbitmqadmin declare queue name=dead_letter_queue durable=true
rabbitmqadmin declare binding source=dead_letter_exchange destination=dead_letter_queue routing_key=dead_letter

# Set queue limits
rabbitmqctl set_policy queue-limits ".*" '{"max-length":100000}' --apply-to queues

# Enable plugins
rabbitmq-plugins enable rabbitmq_management
rabbitmq-plugins enable rabbitmq_prometheus