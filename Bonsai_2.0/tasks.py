# tasks.py

from celery_app import celery

@celery.task
def add_together(a, b):
    return a + b
