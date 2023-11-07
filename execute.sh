source venv/bin/activate; nohup python3 lyra-bot.py &

curl -X POST http://188.166.93.193:9988/discourse_webhook -H "Content-Type: application/json" -H "X-Discourse-Event-Signature: sha256=$(echo -n '{"topic":{"title":"Example Topic","slug":"example-topic","id":123,"category_id":8}}' | openssl dgst -sha256 -hmac "my_simulated_discourse_secret" | sed 's/^.* //')" -d '{"topic":{"title":"Update for ongoing Lyra protocol incentives","slug":"example-topic","id":123,"category_id":8}}'
