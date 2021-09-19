import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "KafkaLogs",
    version = "0.1.5",
    author = "mohammed yousuf uddin",
    author_email = "reach2yousuf@gmail.com",
    description = ("Kakfa logging made simple with python, make your log messages as kafka events out-of-the-box!"),
    license = "MIT",
    keywords = "kafka python logging",
    url = "http://example.com",
    packages=['KafkaLogs'],
    install_requires=[
          'python-decouple',
          'requests',
          'confluent-kafka'
      ],
    long_description=read('README'),
    long_description_content_type='text/markdown',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
)
