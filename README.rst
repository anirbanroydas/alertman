alertman
=========

An **Alerting** / **Notification** microservice written in Python using **asyncio** event loop which listens for alert events and sends notifications via **email**, **sms** etc.

Details
--------

:Author: Anirban Roy Das
:Email: anirban.nick@gmail.com

Features
---------

* microservice
* Asyncio event loop
* Alerting
* RabbitMq
* Email Notification

Overview
---------

* **Some Design Specific Note:**

  I have tried to structure the code using `Clean Architecture <https://8thlight.com/blog/uncle-bob/2012/08/13/the-clean-architecture.html>`_ proposed by 
  `Robert Martin <https://en.wikipedia.org/wiki/Robert_C._Martin>`_, famously known as **Uncle Bob**.

  **Clean Architecture** is some better or flavour of other known architectures like `Porst & Adapters <https://spin.atomicobject.com/2013/02/23/ports-adapters-software-architecture/>`_, 
  `The Onion Architecture <http://jeffreypalermo.com/blog/the-onion-architecture-part-1/>`_, etc.

  Clean architecture mainly focusses on following one principle strictly that is **Dependency Inversion**. Keeping all dependencies flow in a uni direction 
  makes it quite quite powerful. Infact, I have finally realized the value of proper **dependency injections** while implementing clean architecture.

  **NOTE :** This is not the best architecture for all usecases and of course a little more verbose and more boilerplate than some other design patterns, but it 
  does help you keep you codebase fully maintainable for the long run. You may not agree with Clean architecture's philosophy sometimes. But I am just using it to understand it more.


* **Service Details**

  This service is not a server based service. Instead of that it just listens for alert events 
  from a source (in this case, it is `RabbitMQ <https://www.rabbitmq.com/>`_, which for 
  everyone's sake could also be `Redis <https://redis.io/>`_, or `Kafka <https://kafka.apache.org/>`_
  or others.)

  Alertman starts a **worker** consumer **subsribed** to a configured **topic** of a particular 
  rabbitmq **exchange**. The exchange type is Topic exchange type.

  The worker consumer creates a predeficed queue and binds the queue to the configured 
  exchange via some **topic binding key**. Everytime the worker consumer is started it first tries
  to create the queue, but if the queue is already created and binded, it does not do it again.

  Now some other services, can be one, cab be hundred others would **send alert or notification** messages
  via this configured exchange. The services will send alerts to different topics or same topic depending
  on which topics the consumer (in this case the alertman service process) is subsribed to.

  The alertman worker will receive those messages and start processing them. Here the alertman service
  is capable of sending email notifications, sms notification or whatever you add the capabilities for.

  Now the service/worker will send all those emails, sms or whatever is required asynchronously and concurrently
  so that id doesn't have to wait for email or sms or either of them to complete. They would do it concurrently.

  Also, **you can start multiple alertman services/workers**, in which case all those workers will subsribe to the 
  same topic and the same queue bound to the same configured exchange. The only difference is when alerts come to 
  the queue, each worker will process those messages in workers queue fashion meaning, if there are 10 messages which
  come to the queue and there are 5 workers/alertman services running, then each of them will process some of those messages
  but not all. Thus more work could be done at the same time.

  Here the email sending is done using `aiosmtplib <https://github.com/cole/aiosmtplib>`_ which sends email via some 
  **smtp** server **asynchronously** using **asyncio** event loop.
  The service connects to rabbitmq using `aio-pika <aio-pika.readthedocs.io/>`_ client libary which is 
  an asycio based wrapper for the famous `pika <https://github.com/pika/pika>`_ library.

Technical Specs
----------------

:python 3.6: Python Language (Cpython)
:RabbitMQ: Used for listening in on events of alerts and process the events accordingly.
:aio-pika: Asyncio based asynchronous AMQP library which is a wrapper for the Pika library to talk to RabbitMQ.
:aiosmtplib: Asyncio based asynchronous smtp lib to send emails.
:pytest: Python testing library and test runner with awesome test discobery
:pytest-asyncio: Pytest plugin for asyncio lib, to test sanic apps using pytest library.
:Uber\'s Test-Double: Test Double library for python, a good alternative to the `mock <https://github.com/testing-cabal/mock>`_ library
:Docker: A containerization tool for better devops


Deployment
~~~~~~~~~~~

There are two ways to deploy:

* using `Virtualenv <https://virtualenv.pypa.io/en/stable/>`_
* using `Docker <https://www.docker.com/>`_


Prerequisite 
-------------

* **Required**

  Copy (not move) the ``env`` file in the root project directory to ``.env`` and add/edit 
  the configurations accordingly.

  This needs to be done because the server wants some pre configurations like ports, 
  hostnames, etc before it can start the service.

* **Optional**

  To safegurad secret and confidential data leakage via your git commits to public 
  github repo, check ``git-secrets``.

  This `git secrets <https://github.com/awslabs/git-secrets>`_ project helps in 
  preventing secrete leakage by mistake.


Using Virutalenv
-----------------

There is a ``deploy-virtualenv.sh`` script which does all the **heavylifting** and 
**automates** the entire creation of viratualenv, activating it, installing all 
dependencies from the requirements file and initalizing all environment variables 
required for the service and finally installs the service in the virtualenv.

Check the ``deploy-virtualenv.sh`` file for the actual way if you want to see the steps.
    ::    
    
        $ chmod +x deploy-viratualenv.sh
        $ ./deploy-virtualenv.sh


Using Docker
-------------

* **Step 1:**
    
  Install **docker** and **make** command if you don't have it already.

  * Install Docker
    
    Follow my another github project, where everything related to DevOps and scripts are 
    mentioned along with setting up a development environemt to use Docker is mentioned.

    * Project: https://github.com/anirbanroydas/DevOps

    * Go to setup directory and follow the setup instructions for your own platform, linux/macos

  * Install Make
    ::
            
        # (Mac Os)
        $ brew install automake

        # (Ubuntu)
        $ sudo apt-get update
        $ sudo apt-get install make

* **Step 2:**

  There is ``Makefile`` present in teh root project directory using actually hides
  away all the docker commands and other complex commands. So you don't have to actually 
  know the **Docker** commands to run the service via docker. **Make** commands will do the
  job for you.

  * Make sure the ``env`` file has been copied to ``.env`` and necessary configuration changes done.
  * There are only two values that need to be taken care of in the ``Makefile``

    * BRANCH: Change this to whatever branch you are in if making changes and creating the docker images again.
    * COMMIT = Change this to a 6 char hash of the commit value so that the new docker images can be tracked.

  * Run the command to start building new docker image and push it to docker hub.
        
    * There is a script called ``build_tag_push.sh`` which actually does all the job of building the image, tagging the image ans finally pushing it to the repository.
    * Make sure you are logged into to your docker hub acount. 
    * Currently the ``build_tag_push.sh`` scripts pushes the images to ``hub.docker.com/aroyd`` acount. Change the settings in that file if you need to send it to some other place.
    * The script tags the new built docker image with the branch, commit and datetime value.
    * To know more, you can read the ``Dockerfile`` to get idea about the image that gets built on runing this make command.

      ::
        
        $ make build-tag-push

* **Step 3:**

  Pull the image or run the image separately or you can run it along with other services, docker containers etc.
  To know about the check the sameple **dummy orders service** which makes use of this alertman servic.
    
  That service has a well defined ``docker-compose.yml`` file which explains the whole setup process to make the
  **alertman** service work/communicate with other services.

  Link to the dummy orders service is `dummy_orders <https://github.com/anirbanroydas/dummy_orders>`_.


Usage
-----

Check the above **Step 3** which will direct you to a plae on how to use it. There is not API as such but
to know what and how messages are read, for now just go through the code. Docs may be added later for detail description.

TODO
-----

* Add api related documentation
* Add sms notification implementation
* Add other notification implementations
* Save alert to some data store
