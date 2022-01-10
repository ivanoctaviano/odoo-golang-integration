
# Odoo Golang Integration

## Installation

Build image golang service by execute Dockerfile inside folder interceptor-service

```bash
  cd interceptor_service
  docker build -t interceptor-service .
```

![App Screenshot](https://github.com/ivanoctaviano/odoo-golang-integration/blob/master/docs/build-image-go.png)

Excute docker-compose file for container db, odoo, and golang service

```bash
  docker-compose up -d
```


## Documentation

Use this command to check if all services are running well

```bash
  docker ps
```

If all service are running well, it will give output like this

![App Screenshot](https://github.com/ivanoctaviano/odoo-golang-integration/blob/master/docs/check-service.png)

We can access the service using web browser :

- Odoo Service : *localhost:8071* (Login *user: admin, pass: admin*)
![App Screenshot](https://github.com/ivanoctaviano/odoo-golang-integration/blob/master/docs/odoo-service.png)
- Interceptor Service : *localhost:8000*
![App Screenshot](https://github.com/ivanoctaviano/odoo-golang-integration/blob/master/docs/interceptor-service.png)

This project handles 3 http methods (POST, PUT, GET) with the full documentation can be checked in file openapi.yml. We can configure static token for Interceptor Service in Odoo by access Menu Settings -> Technical -> System Parameters -> Search "static_token" (default "ABC")
![App Screenshot](https://github.com/ivanoctaviano/odoo-golang-integration/blob/master/docs/static-token.png)
Here is the example of sending API request to Interceptor Service using Postman (create order in Odoo Service)
![App Screenshot](https://github.com/ivanoctaviano/odoo-golang-integration/blob/master/docs/postman.png)
The result of this request can be checked in Odoo by access Menu Sales -> Search order based on field *Source Document*
![App Screenshot](https://github.com/ivanoctaviano/odoo-golang-integration/blob/master/docs/sale-order.png)
After generate order, Odoo Service will trigger event handling to Webhook. We can check the result of this Webhook in log Interceptor Service using this command :
```bash
  docker logs -f --tail 100 interceptor-service
``` 
and the output will be like this 
![App Screenshot](https://github.com/ivanoctaviano/odoo-golang-integration/blob/master/docs/webhook.png)

## Authors

Ivan Octaviano (ivanoctaviano25@gmail.com)