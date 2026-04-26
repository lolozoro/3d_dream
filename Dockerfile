#使用python基础镜像
FROM python:3.12-slim
#创建在镜像/容器内代码的地址
WORKDIR workspace 
#将物理电脑这个文件夹内的所有代码复制到镜像的workspace内
COPY . .  
#安装代码运行所需环境 
RUN pip3 install -r ./brainmap_3d/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install opencv-python-headless -i https://pypi.tuna.tsinghua.edu.cn/simple
#yolo系列会报一个有关so的错误，下载这个即可
#创建命令
CMD ["/bin/bash"]