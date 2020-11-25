import setuptools

setuptools.setup(
    packages=setuptools.find_packages(),
    name='drf_embedded_fields',
    url='https://github.com/Mendes11/drf_embedded_fields',
    version='0.1',
    description='Provides Fields/Serializers that can be embedded through querystring',
    long_description= 'file: README.md',
    author = 'Rafael Mendes Pacini Bachiega',
    author_email = 'rafaelmpb11@hotmail.com',
    classifiers =
    ['Intended Audience :: Developers',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3 :: Only',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8'],
    install_requires=[
        "Django>=2.2",
        "djangorestframework>=3.1"
    ],
)
