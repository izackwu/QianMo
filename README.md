<div align="center">
    <img src="./Website/static/img/icon1.png" alt="QianMo" width="30%">
</div>

# What's this?
QianMo, my final project of Course EE208. It's a search engine for some particular information of SJTU. 
It supports two types of search: HTML and face. For HTML search, with a query string, you can get some
related web pages; for face search, you upload a photo of somebody and get many other photos of this guy.

# How does it work?
The website is built with [web.py](https://github.com/webpy/webpy).

For HTML search, this project uses [ElasticSearch](https://github.com/elastic/elasticsearch) 
to index and retrieve web pages. Fisrt we extract information
such like title and content from HTML files and index it with ElasticSearch. Then with a query string, ElasticSearch
will handle (almost) everything for us.

For face search, basicly this project uses [OpenCV](https://github.com/opencv/opencv), 
[MTCNN and FaceNet](https://github.com/davidsandberg/facenet). More concretely, OpenCV is used to roughly filter out 
images that don't contain any face. After that, we use MTCNN to detect and crop faces from every single image and embed every face
into a 512-dimension vector with FaceNet. And for search, just compute the feature vector of the 
givin image and do the brute force search to find most similar faces of it. 

By the way, when handling image uploading, I use [Uppy](https://github.com/transloadit/uppy), which is really awesome.

# Where are the data from?
All data are collected from some websites of SJTU with a crawler.

# How does it look like?
There're some screenshots.

**HTML search**
![](./Report/image/html1.png)
![](./Report/image/html2.png)
![](./Report/image/html3.png)

**Face search**
![](./Report/image/face1.png)
![](./Report/image/face2.jpg)
![](./Report/image/face3.png)

# More details?
You can find more details in my project [report](./Report/content.pdf), which is in Chinese. 


