import os

inputFolder=r"F:\temp"
rawFiles=os.listdir(inputFolder)
newFiles=[i.replace("_processed",'') for i in rawFiles]
for i in range(len(newFiles)):
    os.rename(os.path.join(inputFolder,rawFiles[i]),os.path.join(inputFolder,newFiles[i]))