from setuptools import setup, find_packages


setup(
    name='django-db-parti',
    version='0.3.0',
    packages=find_packages(),
    url='https://github.com/maxtepkeev/django-db-parti',
    license=open('LICENSE').read(),
    author='Max Tepkeev',
    author_email='tepkeev@gmail.com',
    description='Fully automatic database table partitioning for Django',
    long_description=open('README.rst').read() + '\n\n' +
                     open('CHANGELOG.rst').read(),
    keywords='django,partition,database,table',
    install_requires=['Django >= 1.5'],
    zip_safe=False,
    classifiers=[
        'Framework :: Django',
        'Development Status :: 4 - Beta',
        'Topic :: Internet',
        'Topic :: Database',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
)
