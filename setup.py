"""
celery-unique adds argument-based unique constraints to Celery tasks.

Configuring unique constraints on Celery requires the following:
    - A modified Task base class for Celery (provided by this package)
    - A redis database connection (to pass to `@celery.task()`)
    - A simple (lambda) function that generates the "unique key" identifier for a task,
    based on the same arguments which are part of the task's signature.

Usage:
    - Step 1: Configure Celery
    ```
    # my_application/__init__.py
    #
    # Create and configure Celery app object, as usual
    from celery import Celery

    celery_app = Celery()

    # Add celery-unique capabilities to the original Celery Task class
    from celery_unique import unique_task_factory

    task_base_cls = celery_app.Task
    new_task_cls = unique_task_factory(task_base_cls)
    celery_app.Task = new_task_cls
    ```

    - Step 2: Configure your tasks to be unique
    ```
    # my_application/celery_tasks.py
    from . import celery_app
    from redis import Redis

    my_redis_client = Redis()

    # Configure a unique task by providing a key-generator and Redis connection
    # as `unique_key` and `redis_client` keyword arguments, respectively.
    @celery_app.task(unique_key=lambda a, b, c=0: '{} with {}'.format(a, c), redis_client=my_redis_client)
    def add_first_and_last(a, b, c=0):
        return a + c
    ```

    - Step 3: Run the tasks with a delay and see what happens
    ```
    import time
    from my_application.celery_tasks import add_first_and_last

    # Unique-handling will only take effect when the above functions are called
    # via `apply_async()` with an ETA or countdown...
    async_result_1 = add_first_and_last.apply_async(args=(1, 2, 3), countdown=100)
    async_result_2 = add_first_and_last.apply_async(args=(3, 2, 1), countdown=100)
    async_result_3 = add_first_and_last.apply_async(args=(1, 2), kwargs={'c': 3}, countdown=50)

    # Wait 100 seconds for all tasks to complete
    time.sleep(100)

    # Check and see the status of each task
    assert async_result_1.status == 'REVOKED'
    assert async_result_2.status == 'SUCCESS'
    assert async_result_3.status == 'SUCCESS'
    ```

In the above example, three Celery tasks were created.  However, in processing our third call,
the handling provided by celery-unique found that there was already a pending result for `add_first_and_last()`
with a unique key of "1 with 3" (generated by the lambda).  So what happened?  The first task was
automatically revoked, and the most recent task was then sent along to be handled by Celery.

This is especially useful for creating time-based tasks like emails.  If we create a task to re-engage users
via email 30 days after the last time we saw them, we could create a task with an ETA of 30 days from the
current time each time they visited.  If we didn't have celery-unique in this scenario and a user made
visits on Monday, Tuesday, and Wednesday, then they would get an email 30 days after Monday, 30 days after
Tuesday, and 30 days after Wednesday.  With celery-unique (and a proper task configuration, of course),
the only email sent would be 30 days after Wednesday.  Huzzah!
"""

from setuptools import setup


setup(
    name='celery-unique',
    url='https://github.com/sgrepo/celery-unique',
    author='Tyler Hendrickson, Shiftgig Inc',
    author_email='tyler@shiftgig.com',
    description='celery-unique adds argument-based unique constraints to Celery tasks',
    long_description=__doc__,
    py_modules=['celery_unique'],
    install_requires=[
        'celery',
        'redis',
    ],
    use_scm_version={
        'version_scheme': 'post-release',
    },
    setup_requires=['setuptools_scm'],
    test_suite='tests',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Object Brokering',
        'Topic :: Software Development :: Distributed Computing'
    ]
)
