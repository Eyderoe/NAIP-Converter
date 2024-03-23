# PDF extract
生成标准文件
## 建议配置
Python 3.8
## 数据库编码部分
数据库_1_PDF提取：\
将pdf文件转换为ZXXX_procedure.txt\
仅提取，不做任何修改，上下划线以文本的形式记录。\

数据库_2_标准化编码：\
将ZXXX_procedure.txt转换为ZXXX_encode.txt\
标准编码，保留和规范有效信息。\

数据库_3_数据库编码.py：\
将ZXXX_encode.txt转换为ZXXX_db.txt\
最终的格式。\
分离多跑道程序，拼接各种(过渡 复飞 等待)程序。进一步编码。\

数据库_4_过渡重构.py：\
部分进近程序存在名称与起始点不一致情况。\
对这部分程序进行修改