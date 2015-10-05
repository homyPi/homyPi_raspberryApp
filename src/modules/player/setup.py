from setuptools import find_packages, setup
setup(name='HApi_player',
      version='0.1',
      description='Client for HApi',
      url='',
      author='Youenn PENNARUN',
      author_email='youenn.pennarun@gmail.com',
      license='MIT',
      packages=find_packages(exclude=['tests', 'tests.*']),
      zip_safe=False,
      include_package_data=True,
      install_requires=['pika'])