#!/bin/bash

# Wait for RabbitMQ to start
until rabbitmqctl status; do
  echo "Waiting for RabbitMQ to start..."
  sleep 2
done

# Create queues
rabbitmqadmin declare queue name=business_queue durable=true
rabbitmqadmin declare queue name=domain_email_queue durable=true
rabbitmqadmin declare queue name=phone_queue durable=true
rabbitmqadmin declare queue name=serp_queue durable=true

# Create dead letter exchange and queues
rabbitmqadmin declare exchange name=dlx type=direct durable=true
rabbitmqadmin declare queue name=dead_letter_queue durable=true

# Set queue limits
rabbitmqctl set_policy queue-limits ".*" '{"max-length":100000}' --apply-to queues

# Enable plugins
rabbitmq-plugins enable rabbitmq_management
rabbitmq-plugins enable rabbitmq_prometheus